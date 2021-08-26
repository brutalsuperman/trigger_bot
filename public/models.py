from core.base import db
from peewee import *
from playhouse.postgres_ext import *


class Prices(Model):
    name = CharField(primary_key=True)
    prices = ArrayField(IntegerField)
    code = CharField(null=True)

    class Meta:
        database = db
