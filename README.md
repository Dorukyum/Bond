<div align="center">
	<h1>Toolkit 🛠️</h1>
	<img alt="Discord" src="https://img.shields.io/discord/789829818547175446?label=Discord&style=for-the-badge&logo=discord&color=5865F2&logoColor=white">
	<img alt="GitHub contributors" src="https://img.shields.io/github/contributors/Dorukyum/Toolkit?style=for-the-badge">
	<img alt="Lines of code" src="https://img.shields.io/tokei/lines/github/Dorukyum/Toolkit?style=for-the-badge">
	<h3>Gain full control over your Discord server.</h3>
</div>

Toolkit is a Discord bot created to make server management as easy as possible.
It's built with UI components and application commands to be user-friendly.

## Commands
### ⚡ Moderation
- `/massban`: Ban multiple members at once
- `/warn`: Warn members
- `/delwarn`: Delete a warning
- `/warns`: View warnings given to a specific member
- `/slowmode`: Set channel slowmode delay
- `/lock`: Lock a channel instantly
- `/unlock`: Unlock a locked channel
- `/purge all`: Delete a specific amount of messages
- `/purge member`: Delete messages only from a specific member
- `/purge bots`: Delete messages only from bots
- `/purge containing`: Delete messages only containing a specific substring
- `View Account Age`: Simply check the age of an account (user command)

### 🗒️ Logs
- `/logs set`: Set the logs channel for a logging category
- `/logs disable`: Disable logs for a logging category
- Moderation logs (ban, kick, timeout)
- Server logs (channel updates, role updates)

### 🤖 Automoderation
- `/automod`: Enable or disable automoderation
- Timeout new accounts on join
- Ban or timeout when too many mentions are sent

### ✅ Dropdown Roles
- `/dropdown_roles setup`: Setup a dropdown menu for choosing roles.

### 🏷️ Tags
- `/tag create`: Create a tag
- `/tag view`: View the content of a tag
- `/tag raw`: View the raw content of a tag (escapes markdown)
- `/tag edit`: Edit a tag
- `/tag list`: View a list of tags
- `/tag search`: Search tags
- `/tag claim`: Claim a tag whose owner left the server
- `/tag info`: View information about a tag
- `/tag delete`: Delete a tag

### 📈 Statistics / Information
- `/serverinfo`: View statistics / information about the server
- `/userinfo`: View information about a user

### 📊 Polls
- `/poll`: Start a poll
- `/poll_yesno`: Start a poll with two options: yes or no

### 📢 Suggestions
- `/suggestions set`: Set the channel for member suggestions
- `/suggestions disable`: Disable member suggestions
- `/suggest`: Make a suggestion

### 💻 Developer Utilities
- `/gitlink`: Enable or disable linking code snippets
- Fetch GitHub repository and gist URLs with line numbers
- `/repository`: Set the default GitHub repository to use for pr and issue linking
- Triggered with "##123" (123 being the issue / pr number)

### 😁 Emojis
- `/emoji add`: Add a custom emoji to the server
- `/emoji delete`: Delete a custom server emoji

### 🚀 Fun
- `/8ball ask`: Ask something to the magic 8 ball
- `/8ball yes_or_no`: Respond with either yes or no
- `/how_many`: Learn how many members have the specified substring in their name

### ➕ Other
- `/timestamp`: View the current timestamp
- `/afk`: Set your AFK status to respond to pings
- `/ping`: View the bot's websocket latency

## How to Contribute
1. Fork this GitHub repository
2. Make changes
3. Create a pull request

## Reporting Bugs and Making Suggestions
Feel free to [create an issue](https://github.com/Dorukyum/Toolkit/issues/new) or [contact me on Discord](https://discord.gg/8JsMVhBP4W).
