from bot import db
from peewee import *
from datetime import datetime


class Trigger(Model):
    trigger_name = CharField()
    chat_id = IntegerField()
    trigger_type = CharField()
    trigger_value = TextField()

    class Meta:
        primary_key = CompositeKey('trigger_name', 'chat_id')
        database = db


class TimeTrigger(Model):
    chat_id = IntegerField()
    time = CharField()
    trigger_type = CharField()
    trigger_value = TextField()

    class Meta:
        primary_key = CompositeKey('chat_id', 'time')
        database = db


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


class Report(Model):
    text = CharField()
    nickname = CharField()
    date = DateTimeField()
    chat_id = IntegerField()

    class Meta:
        primary_key = CompositeKey('nickname', 'date')
        database = db


class Token(Model):
    chat_id = IntegerField(primary_key=True)
    token = CharField()

    class Meta:
        database = db


class Request(Model):
    chat_id = IntegerField(primary_key=True)
    req_id = CharField(null=True)
    action = CharField()
    operation = CharField(null=True)

    class Meta:
        database = db


class UserData(Model):
    chat_id = IntegerField()
    type = CharField()
    data = TextField()

    class Meta:
        database = db
        primary_key = CompositeKey('chat_id', 'type')


class GoldRules(Model):
    chat_id = IntegerField(primary_key=True)
    rules = TextField()
    auto = BooleanField(default=True)

    class Meta:
        database = db


class WtbLogs(Model):
    chat_id = IntegerField(primary_key=True)
    quantity = IntegerField()
    price = IntegerField()
    item = CharField()
    status = CharField(null=True)
    date = DateTimeField(default=datetime.now)

    class Meta:
        database = db


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
