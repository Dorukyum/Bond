from tortoise import fields
from tortoise.models import Model


class Tag(Model):
    name = fields.TextField()
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    author_id = fields.IntField()
    guild_id = fields.IntField()
    content = fields.TextField()
    uses = fields.IntField()

    def __str__(self):
        return self.content
