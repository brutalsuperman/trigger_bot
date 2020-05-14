from bot import db
from peewee import *


class Trigger(Model):
    trigger_name = CharField()
    chat_id = IntegerField()
    trigger_type = CharField()
    trigger_value = CharField()

    class Meta:
        primary_key = CompositeKey('trigger_name', 'chat_id')
        database = db


class TimeTrigger(Model):
    chat_id = IntegerField()
    time = CharField()
    trigger_type = CharField()
    trigger_value = CharField()

    class Meta:
        primary_key = CompositeKey('chat_id', 'time')
        database = db
