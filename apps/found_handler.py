#!/usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.web
import pymysql
from settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PWD, MYSQL_DB
# from string import lower
import json
from lib import session


class FoundHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, *args, **kwargs):
        super(FoundHandler, self).__init__(application, request, **kwargs)
        self.session = session.Session(self.application.session_manager, self)

    @property
    def redis(self):
        return self.application.redis

    @property
    def cur(self):
        mysql_conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PWD,
            db=MYSQL_DB,
            port=MYSQL_PORT,
            use_unicode=True,
            charset='utf8'
        )   #msyql数据库连接
        return mysql_conn.cursor(cursor=pymysql.cursors.DictCursor)

    def write_json(self, data=None, status=0, msg="", need_format=True):
        if data is None:
            data = {}
        if need_format:
            response = {
                "status": status,
                "message": msg,
                "data": data
            }
        else:
            response = data

        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.set_header("Access-Control-Allow-Origin", "*")     # 允许跨域请求
        self.set_header("Sever", "test")
        self.write(response)

    def compute_etag(self):
        return None

    def get_current_user(self):
        print("session", self.session)
        return self.session.get("user_name")
