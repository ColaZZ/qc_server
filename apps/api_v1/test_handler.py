#!/usr/bin/python3
# -*- coding: utf-8 -*-

import platform

from apps.found_handler import FoundHandler
from lib.routes import route

@route('/test')
class TestHandler(FoundHandler):
    def get(self):
        value = self.redis.get("test_key").decode("utf-8")
        # print(type(value))
        data = "test redis data is {}".format(value)
        self.write_json(data)