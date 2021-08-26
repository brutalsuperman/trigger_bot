from core.config import DB_NAME, DB_PASSWORD, DB_USER
from peewee import *

db = PostgresqlDatabase(DB_NAME, user=DB_USER, password=DB_PASSWORD, autorollback=True)
