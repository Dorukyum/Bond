from tortoise import fields
from tortoise.models import Model


class TagModel(Model):
    name = fields.TextField()
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    author_id = fields.IntField()
    guild_id = fields.IntField()
    content = fields.TextField()
    uses = fields.IntField()

    def __str__(self):
        return self.content


class GuildModel(Model):
    id = fields.IntField(pk=True)
    automod = fields.BooleanField(default=False)
    mod_log = fields.IntField(default=0)


class WarnModel(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    mod_id = fields.IntField()
    target_id = fields.IntField()
    guild_id = fields.IntField()
    reason = fields.TextField()
