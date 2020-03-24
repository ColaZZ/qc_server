import os

import peewee_async
from peewee import *

from settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PWD

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

database = peewee_async.MySQLDatabase(
    'hlxxx_p', host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PWD
)

print("database:", 'hlxxx_p', MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PWD)

class BaseModel(Model):

    class Meta:
        database = database

