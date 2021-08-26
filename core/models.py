from core.base import db
from peewee import *


class WorldTop(Model):
    emodji = CharField()
    name = CharField()
    points = IntegerField()
    date = DateTimeField()
    gold = IntegerField(null=True)
    action = CharField(null=True)
    digits = IntegerField(null=True)

    class Meta:
        database = db
        primary_key = CompositeKey('emodji', 'name', 'date')
