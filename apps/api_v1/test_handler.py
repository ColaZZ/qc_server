#!/usr/bin/python3
# -*- coding: utf-8 -*-

from apps.found_handler import FoundHandler
from lib.routes import route
from lib.utils import login_required

from apps.models.config import Config


@route('/test')
class TestHandler(FoundHandler):
    async def get(self):
        # value = self.redis.get("test_key").decode("utf-8")
        # print(type(value))
        data = Config.default_config
        self.write_json(data)


@route('/test_main')
class TestMainHandler(FoundHandler):
    # @login_required
    async def get(self):
        # username = self.get_current_user()
        # print('start...')
        # print(username)
        # open_id = "121212"
        data = {}
        self.write_json(data)



@route('/test_login')
class TestLoginHandler(FoundHandler):
    async def get(self):
        self.session["user_name"] = self.get_argument("name")
        self.session["test"] = "test login xxx"
        self.session.save()
        self.write_json("你的session已经存储")


@route('/test_insert')
class TestInsertHandler(FoundHandler):
    async def get(self):
        cur = self.cur
        try:
            sql = "insert into user_level (uuid, `level`, next_level, current_score) values(%s, %s, %s, %s)"
            cur.execute(sql, ['test_uuid', 22, 23, 456])
            cur.connection.commit()
        except Exception as e:
            print(e)
