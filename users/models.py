from datetime import datetime

from core.base import db
from peewee import *


class Users(Model):
    castle = CharField()
    guild = CharField()
    name = CharField()
    cw_id = CharField(null=True)
    telegram_id = CharField(null=True)
    where = CharField()
    level = IntegerField(default=0)
    last_seen = DateTimeField()

    class Meta:
        database = db
        primary_key = CompositeKey('guild', 'name')


class Duels(Model):
    date = DateTimeField()
    winner_castle = CharField(null=False)
    winner_guild = CharField(null=True)
    winner_name = CharField()
    winner_level = IntegerField()
    winner_id = CharField()
    loser_castle = CharField(null=False)
    loser_guild = CharField(null=True)
    loser_name = CharField()
    loser_level = IntegerField()
    loser_id = CharField()

    class Meta:
        database = db
        primary_key = CompositeKey('date', 'winner_id')


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


class Report(Model):
    text = CharField()
    nickname = CharField()
    date = DateTimeField()
    chat_id = IntegerField()

    class Meta:
        primary_key = CompositeKey('nickname', 'date')
        database = db


class Guilds(Model):
    castle = CharField()
    name = CharField(primary_key=True)
    last_seen = DateTimeField()
    where = CharField()

    class Meta:
        database = db


class UserSettings(Model):
    cw_id = CharField(null=True)
    telegram_id = CharField(primary_key=True)
    sell_notification = BooleanField(default=False)
    auto_spend_notification = BooleanField(default=True)

    class Meta:
        database = db


class GuildsGlory(Model):
    name = CharField(null=False, unique=True)
    castle = CharField(null=True)
    glory_before = IntegerField(null=True)
    glory_after = IntegerField(null=True)
    set_by = IntegerField()

    class Meta:
        database = db
