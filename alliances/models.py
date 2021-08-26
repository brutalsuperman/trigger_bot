from core.base import db
from peewee import *


class Spot(Model):
    name = CharField()
    code = CharField()
    spot_type = CharField()
    chat_id = IntegerField()

    class Meta:
        primary_key = CompositeKey('code', 'chat_id')
        database = db


class Alliances(Model):
    name = CharField()
    alliance = CharField()
    type = CharField()
    date = DateTimeField()

    class Meta:
        primary_key = CompositeKey('name')
        database = db
