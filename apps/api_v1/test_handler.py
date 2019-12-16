#!/usr/bin/python3
# -*- coding: utf-8 -*-

from apps.found_handler import FoundHandler
from lib.routes import route
from lib.utils import login_required


@route('/test')
class TestHandler(FoundHandler):
    def get(self):
        value = self.redis.get("test_key").decode("utf-8")
        # print(type(value))
        data = "test redis data is {}".format(value)
        self.write_json(data)


@route('/test_main')
class TestMainHandler(FoundHandler):
    # @login_required
    def get(self):
        # username = self.get_current_user()
        # print('start...')
        # print(username)
        # open_id = "121212"
        data = {}
        self.write_json(data)



@route('/test_login')
class TestLoginHandler(FoundHandler):
    def get(self):
        self.session["user_name"] = self.get_argument("name")
        self.session["test"] = "test login xxx"
        self.session.save()
        self.write_json("你的session已经存储")
