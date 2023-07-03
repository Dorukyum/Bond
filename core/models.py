from discord import Guild, TextChannel
from tortoise import fields
from tortoise.models import Model

__all__ = ("GuildModel", "TagModel", "WarnModel")


class GuildModel(Model):
    id = fields.IntField(pk=True)
    automod = fields.BooleanField(default=False)
    mod_log = fields.IntField(default=0)
    server_log = fields.IntField(default=0)
    suggestions = fields.IntField(default=0)
    repo = fields.CharField(50, null=True)

    @classmethod
    async def get_text_channel(
        cls, guild: Guild, field_name: str
    ) -> TextChannel | None:
        """Return the text channel from a guild set to the given field."""
        guild_data, _ = await cls.get_or_create(id=guild.id)
        if channel_id := getattr(guild_data, field_name):
            channel = guild.get_channel(channel_id)
            return channel if isinstance(channel, TextChannel) else None

    class Meta:
        table = "guilds"


class TagModel(Model):
    name = fields.TextField()
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    author_id = fields.IntField()
    guild_id = fields.IntField()
    content = fields.TextField()
    uses = fields.IntField()

    def __str__(self):
        return self.content

    class Meta:
        table = "tags"


class WarnModel(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    mod_id = fields.IntField()
    target_id = fields.IntField()
    guild_id = fields.IntField()
    reason = fields.TextField()

    class Meta:
        table = "warns"
