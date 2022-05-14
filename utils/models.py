from typing import Any

from tortoise import fields
from tortoise.models import Model


class BaseModel(Model):
    @classmethod
    async def update(cls, field_name: str, id: int, value: Any) -> bool:
        """Updates a database field with the given value. Returns True if the value is not 0."""
        await cls.update_or_create({field_name: value}, id=id)
        return value != 0

    class Meta:
        abstract = True


class TagModel(BaseModel):
    name = fields.TextField()
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    author_id = fields.IntField()
    guild_id = fields.IntField()
    content = fields.TextField()
    uses = fields.IntField()

    def __str__(self):
        return self.content


class GuildModel(BaseModel):
    id = fields.IntField(pk=True)
    automod = fields.BooleanField(default=False)
    mod_log = fields.IntField(default=0)
    server_log = fields.IntField(default=0)
    suggestions = fields.IntField(default=0)


class WarnModel(BaseModel):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    mod_id = fields.IntField()
    target_id = fields.IntField()
    guild_id = fields.IntField()
    reason = fields.TextField()
