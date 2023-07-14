# Directly taken and modified from TechStruck/TechStruck-Bot
# https://github.com/TechStruck/TechStruck-Bot/blob/271e900f084101f2fa9910e9348c8d49ea396842/bot/utils/fuzzy.py
# This code is under the Mozilla Public License 2.0

import re
from difflib import SequenceMatcher
from heapq import nlargest


def ratio(a, b):
    m = SequenceMatcher(None, a, b)
    return int(round(100 * m.ratio()))


def quick_ratio(a, b):
    m = SequenceMatcher(None, a, b)
    return int(round(100 * m.quick_ratio()))


def partial_ratio(a, b):
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    m = SequenceMatcher(None, short, long)

    blocks = m.get_matching_blocks()

    scores = []
    for i, j, _ in blocks:
        start = max(j - i, 0)
        end = start + len(short)
        o = SequenceMatcher(None, short, long[start:end])
        r = o.ratio()

        if 100 * r > 99:
            return 100
        scores.append(r)

    return int(round(100 * max(scores)))


_word_regex = re.compile(r"\W", re.IGNORECASE)


def _sort_tokens(a):
    a = _word_regex.sub(" ", a).lower().strip()
    return " ".join(sorted(a.split()))


def token_sort_ratio(a, b):
    a = _sort_tokens(a)
    b = _sort_tokens(b)
    return ratio(a, b)


def quick_token_sort_ratio(a, b):
    a = _sort_tokens(a)
    b = _sort_tokens(b)
    return quick_ratio(a, b)


def partial_token_sort_ratio(a, b):
    a = _sort_tokens(a)
    b = _sort_tokens(b)
    return partial_ratio(a, b)


def _extraction_generator(query, choices, scorer=quick_ratio, score_cutoff=0):
    try:
        for key, value in choices.items():
            score = scorer(query, key)
            if score >= score_cutoff:
                yield (key, score, value)
    except AttributeError:
        for choice in choices:
            score = scorer(query, choice)
            if score >= score_cutoff:
                yield (choice, score)


def extract(
    query, choices, *, scorer=quick_ratio, score_cutoff=0, limit: int | None = 10
):
    it = _extraction_generator(query, choices, scorer, score_cutoff)
    key = lambda t: t[1]
    if limit is not None:
        return nlargest(limit, it, key=key)
    return sorted(it, key=key, reverse=True)


def extract_one(query, choices, *, scorer=quick_ratio, score_cutoff=0):
    it = _extraction_generator(query, choices, scorer, score_cutoff)
    key = lambda t: t[1]
    try:
        return max(it, key=key)
    except:
        # iterator could return nothing
        return None


def extract_or_exact(query, choices, *, limit=None, scorer=quick_ratio, score_cutoff=0):
    matches = extract(
        query, choices, scorer=scorer, score_cutoff=score_cutoff, limit=limit
    )
    if len(matches) == 0:
        return []

    if len(matches) == 1:
        return matches

    top = matches[0][1]
    second = matches[1][1]

    # check if the top one is exact or more than 30% more correct than the top
    if top == 100 or top > (second + 30):
        return [matches[0]]

    return matches


def extract_matches(query, choices, *, scorer=quick_ratio, score_cutoff=0):
    matches = extract(query, choices, scorer=scorer, score_cutoff=score_cutoff)
    if len(matches) == 0:
        return []

    top_score = matches[0][1]
    to_return = []
    index = 0
    while True:
        try:
            match = matches[index]
        except IndexError:
            break
        else:
            index += 1

        if match[1] != top_score:
            break

        to_return.append(match)
    return to_return


async def finder(text, collection, *, key=None):
    suggestions = []
    text = str(text)
    pat = ".*?".join(map(re.escape, text))
    regex = re.compile(pat, flags=re.IGNORECASE)
    for item in collection:
        to_search = key(item) if key else item
        r = regex.search(to_search)
        if r:
            suggestions.append((len(r.group()), r.start(), item))

    def sort_key(tup):
        if key:
            return tup[0], tup[1], key(tup[2])
        return tup

    return [z for _, _, z in sorted(suggestions, key=sort_key)]


async def find(text, collection, *, key=None) -> list | None:
    try:
        return await finder(text, collection, key=key)
    except IndexError:
        return None
