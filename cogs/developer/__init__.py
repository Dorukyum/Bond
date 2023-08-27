import re
import textwrap
from io import BytesIO
from typing import Type, overload

import discord
from discord.ext.pages import Paginator
from discord.utils import as_chunks

from core import Cog, GuildModel

from .rtfm import OVERRIDES, TARGETS, SphinxObjectFileReader, create_buttons, finder

__all__ = ("setup",)

GITHUB_RE = re.compile(
    r"https://github\.com/(?P<repo>[a-zA-Z0-9-]+/[\w.-]+)/blob/"
    r"(?P<path>[^#>]+)(\?[^#>]+)?(#L(?P<start_line>\d+)(([-~:]|(\.\.))L(?P<end_line>\d+))?)"
)

GITHUB_GIST_RE = re.compile(
    r"https://gist\.github\.com/([a-zA-Z0-9-]+)/(?P<gist_id>[a-zA-Z0-9]+)/*"
    r"(?P<revision>[a-zA-Z0-9]*)/*#file-(?P<file_path>[^#>]+?)(\?[^#>]+)?"
    r"(-L(?P<start_line>\d+)([-~:]L(?P<end_line>\d+))?)"
)

PULL_HASH_REGEX = re.compile(
    r"(?:(?P<org>(?:[A-Za-z]|\d|-)+)\/)?(?P<repo>(?:[A-Za-z]|\d|-|_|\.)+)?(?:##)(?P<index>[0-9]+)"
)


async def rtfm_autocomplete(ctx: discord.AutocompleteContext):
    assert isinstance(ctx.cog, Developer)
    results = await ctx.cog.get_rtfm_results(ctx.options["documentation"], ctx.value)
    return [key for key, _ in results] if results else []


class Delete(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member) -> None:
        super().__init__()
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        assert interaction.channel
        if (
            self.user.bot
            or self.user == interaction.user
            or (
                isinstance(interaction.user, discord.Member)
                and not isinstance(interaction.channel, discord.PartialMessageable)
                and interaction.channel.permissions_for(
                    interaction.user
                ).manage_messages
            )
        ):
            return True
        await interaction.response.send_message(
            "You need to either be the user who requested this snippet or have "
            "`Manage Messages` permissions in this channel to delete it.",
            ephemeral=True,
        )
        return False

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red)
    async def delete(self, _, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        if interaction.message:
            await interaction.delete_original_response()
        self.stop()


class Developer(Cog):
    """Commands related to developer utilities."""

    def __init__(self, bot):
        super().__init__(bot)
        self.pattern_handlers = [
            (GITHUB_RE, self.fetch_snippet),
            (GITHUB_GIST_RE, self.fetch_gist_snippet),
        ]
        self.rtfm_cache: dict[str, dict] = {}
        self.bot.loop.create_task(self.build_docs())

    @overload
    async def _fetch(self, url: str, response_type: Type[str]) -> str:
        ...

    @overload
    async def _fetch(self, url: str, response_type: Type[list]) -> list:
        ...

    @overload
    async def _fetch(self, url: str, response_type: Type[dict]) -> dict:
        ...

    async def _fetch(self, url: str, response_type):
        """Makes an HTTP request to GitHub using aiohttp."""
        async with self.bot.http_session.get(
            url,
            raise_for_status=True,
            headers={"Accept": "application/vnd.github.v3.raw"},
        ) as response:
            if response_type is str:
                return await response.text()
            return await response.json()

    def find_reference(self, path: str, refs: list) -> tuple:
        """Loops through all branches and tags to find the required reference."""
        # Base case: there is no slash in the branch name
        ref, file_path = path.split("/", 1)
        # In case there are slashes in the branch name, loop through all branches and tags
        for possible_ref in refs:
            if path.startswith(possible_ref["name"] + "/"):
                ref = possible_ref["name"]
                file_path = path[len(ref) + 1 :]
                break
        return ref, file_path

    async def fetch_snippet(
        self, repo: str, path: str, start_line: str, end_line: str
    ) -> tuple[str, ...] | None:
        """Fetches a snippet from a GitHub repo."""
        branches = await self._fetch(
            f"https://api.github.com/repos/{repo}/branches",
            list,
        )
        tags = await self._fetch(f"https://api.github.com/repos/{repo}/tags", list)
        refs = branches + tags
        ref, file_path = self.find_reference(path, refs)

        file_contents = await self._fetch(
            f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={ref}",
            str,
        )
        return self.snippet_to_codeblock(file_contents, file_path, start_line, end_line)

    async def fetch_gist_snippet(
        self,
        gist_id: str,
        revision: str,
        file_path: str,
        start_line: str,
        end_line: str,
    ) -> tuple[str, ...] | None:
        """Fetches a snippet from a GitHub gist."""
        gist_json = await self._fetch(
            f"https://api.github.com/gists/{gist_id}{f'/{revision}' if len(revision) > 0 else ''}",
            dict,
        )

        for gist_file in gist_json["files"]:
            if file_path == gist_file.lower().replace(".", "-"):
                file_contents = await self._fetch(
                    gist_json["files"][gist_file]["raw_url"],
                    str,
                )
                return self.snippet_to_codeblock(
                    file_contents, gist_file, start_line, end_line
                )

    def snippet_to_codeblock(
        self, file_contents: str, file_path: str, start_line: str, end_line: str
    ) -> tuple[str, ...] | None:
        """
        Given the entire file contents and target lines, creates a code block.
        First, we split the file contents into a list of lines and then keep and join only the required
        ones together.
        We then dedent the lines to look nice, and replace all ` characters with `\u200b to prevent
        markdown injection.
        Finally, we surround the code with ``` characters.
        """
        if end_line is None:
            start = end = int(start_line)
        else:
            start = int(start_line)
            end = int(end_line)

        split_file_contents = file_contents.splitlines()

        if start > end:
            start, end = end, start
        if start > len(split_file_contents) or end < 1:
            return
        start = max(1, start)
        end = min(len(split_file_contents), end)

        # Gets the code lines, dedents them, and inserts zero-width spaces to prevent Markdown injection
        code = (
            textwrap.dedent("\n".join(split_file_contents[start - 1 : end]))
            .rstrip()
            .replace("`", "`\u200b")
        )

        # Extracts the code language and checks whether it's a "valid" language
        language = (
            file_path.split("/")[-1]
            .split(".")[-1]
            .replace("-", "")
            .replace("+", "")
            .replace("_", "")
        )
        language = language if language.isalnum() else "txt"

        if start == end:
            title = f"`{file_path}` line {start}\n"
        else:
            title = f"`{file_path}` lines {start} to {end}\n"
        return title, code, language

    async def parse_snippets(self, content: str) -> tuple[str, ...] | None:
        """Parses message content and return code snippet information."""
        for pattern, handler in self.pattern_handlers:
            if snippet := pattern.search(content):
                return await handler(**snippet.groupdict())

    @discord.message_command(name="Fetch Code Snippet")
    async def gitlink(self, ctx: discord.ApplicationContext, message: discord.Message):
        """Fetch and display a code snippet from a GitHub permalink."""
        assert isinstance(ctx.author, discord.Member) and isinstance(
            ctx.channel, discord.TextChannel
        )
        if (
            ctx.author != message.author
            and not ctx.channel.permissions_for(ctx.author).manage_messages
        ):
            return await ctx.respond(
                "You need to either be the user who sent this message or have "
                "`Manage Messages` permissions in this channel to request a snippet.",
                ephemeral=True,
            )

        snippet = await self.parse_snippets(message.content)
        if not snippet:
            return await ctx.respond(
                "There were no GitHub snippet links found in this message.",
                ephemeral=True,
            )
        if not snippet[1]:
            return await ctx.respond("The snippet is empty.", ephemeral=True)
        if len(content := f"{snippet[0]}```{snippet[2]}\n{snippet[1]}```") <= 2000:
            return await ctx.respond(content, view=Delete(ctx.author))
        await ctx.respond(
            snippet[0],
            file=discord.File(
                BytesIO(snippet[1].encode("utf-8")),
                f"output.{snippet[2]}",
            ),
            view=Delete(ctx.author),
        )

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(manage_guild=True)
    @discord.option(
        "repo",
        description="The GitHub repository in format `owner/repository-name`.",
    )
    async def repository(self, ctx: discord.ApplicationContext, repo: str):
        """Set the default GitHub repository to use for pr and issue linking (`##123`)"""
        if len(repo.split("/")) != 2:
            return await ctx.respond(
                f"The GitHub repository should be in the following format: "
                "owner/repository-name",
                ephemeral=True,
            )
        if len(repo) > 50:
            return await ctx.respond(
                "The name of the repository can't be longer than 50 letters."
            )
        await GuildModel.update_or_create(id=ctx.guild_id, defaults={"repo": repo})
        await ctx.respond(
            f"The default GitHub repository for pr and issue linking is now `{repo}`."
        )

    async def build_docs(self) -> None:
        await self.bot.wait_until_ready()
        for target in TARGETS:
            self.bot.loop.create_task(self.build_documentation((target)))

    async def build_documentation(self, target: str) -> None:
        url = TARGETS[target]
        req = await self.bot.http_session.get(
            OVERRIDES.get(target, url + "/objects.inv")
        )
        if req.status != 200:
            raise discord.ApplicationCommandError(
                f"Failed to build RTFM cache for {target}"
            )
        self.rtfm_cache[target] = SphinxObjectFileReader(
            await req.read()
        ).parse_object_inv(url)

    async def get_rtfm_results(self, target: str, query: str) -> list:
        if not (cached := self.rtfm_cache.get(target)):
            return []
        results = await finder(
            query,
            list(cached.items()),
            key=lambda x: x[0],
        )
        return results

    @discord.command()
    @discord.option(
        "query", description="The search query.", autocomplete=rtfm_autocomplete
    )
    @discord.option(
        "documentation",
        description="The documentation to search through.",
        choices=[*TARGETS.keys()],
        default="pycord"
    )
    async def rtfm(
        self,
        ctx: discord.ApplicationContext,
        documentation: str,
        query: str,
    ):
        """Search through a specific documentation."""
        if not (results := await self.get_rtfm_results(documentation, query)):
            return await ctx.respond("Couldn't find any results")

        if len(results) <= 15:
            embed = discord.Embed(
                title=f"Searched in {documentation}",
                description="\n".join([f"[`{key}`]({url})" for key, url in results]),
                color=discord.Color.blurple(),
            )
            return await ctx.respond(embed=embed)

        chunks = as_chunks(iter(results), 15)
        embeds = [
            discord.Embed(
                title=f"Searched in {documentation}",
                description="\n".join([f"[`{key}`]({url})" for key, url in chunk]),
                color=discord.Color.blurple(),
            )
            for chunk in chunks
        ]
        paginator = Paginator(
            embeds,  # type: ignore # embeds is compatible
            custom_buttons=create_buttons(),
            use_default_buttons=False,
        )
        await paginator.respond(ctx.interaction)

    @Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not (
            not message.author.bot
            and message.guild
            and (data := await GuildModel.get_or_none(id=message.guild.id))
            and data.repo
        ):
            return

        links = [
            f"https://github.com/{org or data.repo.split('/')[0]}/{repo or data.repo.split('/')[1]}/pull/{index}"
            for org, repo, index in {*PULL_HASH_REGEX.findall(message.content)[:10]}
        ]
        if len(links) > 2:
            links = [f"<{link}>" for link in links]
        if links:
            await message.reply("\n".join(links))


def setup(bot):
    bot.add_cog(Developer(bot))
