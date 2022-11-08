import re
import textwrap
from typing import Type, Union, overload

import discord
from aiohttp import ClientResponseError
from tortoise.exceptions import ConfigurationError

from core import Cog, GuildModel

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
    r"(?:(?P<org>(?:[A-Za-z]|\d|-)+)/)?(?P<repo>(?:[A-Za-z]|\d|-)+)?(?:##)(?P<index>[0-9]+)"
)


class Delete(discord.ui.View):
    """Delete View for git-codeblock"""

    def __init__(self, user: Union[discord.User, discord.Member]) -> None:
        super().__init__()
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if (
            self.user.bot
            or self.user == interaction.user
            or (
                isinstance(interaction.user, discord.Member)
                and interaction.user.guild_permissions.manage_messages
            )
        ):
            return True
        await interaction.response.send_message(
            "`Manage Messages` permission required to delete this.",
            ephemeral=True,
        )
        return False

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red)
    async def delete(self, _, interaction: discord.Interaction) -> None:
        if interaction.message:
            await interaction.message.delete()
        self.stop()


class Developer(Cog):
    """Commands related to developer utilities."""

    def __init__(self, bot):
        super().__init__(bot)
        self.pattern_handlers = [
            (GITHUB_RE, self.fetch_snippet),
            (GITHUB_GIST_RE, self.fetch_gist_snippet),
        ]

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
        """Makes HTTP requests using aiohttp."""
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
    ) -> str:
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
    ) -> str:
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
        return ""

    def snippet_to_codeblock(
        self, file_contents: str, file_path: str, start_line: str, end_line: str
    ) -> str:
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
            return ""
        start = max(1, start)
        end = min(len(split_file_contents), end)

        # Gets the code lines, dedents them, and inserts zero-width spaces to prevent Markdown injection
        required = "\n".join(split_file_contents[start - 1 : end])
        required = textwrap.dedent(required).rstrip().replace("`", "`\u200b")

        # Extracts the code language and checks whether it's a "valid" language
        language = file_path.split("/")[-1].split(".")[-1]
        trimmed_language = language.replace("-", "").replace("+", "").replace("_", "")
        is_valid_language = trimmed_language.isalnum()
        if not is_valid_language:
            language = ""

        if start == end:
            ret = f"`{file_path}` line {start}\n"
        else:
            ret = f"`{file_path}` lines {start} to {end}\n"

        if len(required) != 0:
            return f"{ret}```{language}\n{required}```"
        # Returns an empty codeblock if the snippet is empty
        return f"{ret}``` ```"

    async def parse_snippets(self, content: str) -> str:
        """Parse message content and return a string with a code block for each URL found."""
        all_snippets = []

        for pattern, handler in self.pattern_handlers:
            for match in pattern.finditer(content):
                try:
                    snippet = await handler(**match.groupdict())
                    all_snippets.append((match.start(), snippet))
                except ClientResponseError as error:
                    error_message = error.message
                    print(error_message)

        # Sorts the list of snippets by their match index
        return "\n".join(map(lambda x: x[1], sorted(all_snippets)))

    @discord.slash_command()
    @discord.guild_only()
    @discord.default_permissions(manage_guild=True)
    @discord.option(
        "status",
        description="Turn GitHub snippet linking on or off.",
        choices=["On", "Off"],
    )
    async def gitlink(self, ctx: discord.ApplicationContext, status: str):
        """Toggle GitHub snippet linking for this server."""
        guild, _ = await GuildModel.get_or_create(id=ctx.guild_id)
        as_bool = status == "On"
        if guild.gitlink == as_bool:
            return await ctx.respond(f"GitLink is already {status.lower()}.")

        await guild.update_from_dict({"gitlink": as_bool}).save()
        await ctx.respond(f"GitLink is now {status.lower()}.")

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

    @Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        try:
            if not (
                not message.author.bot
                and message.guild
                and (data := await GuildModel.get_or_none(id=message.guild.id))
            ):
                return
        except ConfigurationError:
            return

        if data.gitlink:
            message_to_send = await self.parse_snippets(message.content)
            if 0 < len(message_to_send) <= 1990:
                # TODO: Text Pagination
                await message.channel.send(message_to_send, view=Delete(message.author))

        if data.repo is not None:
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
