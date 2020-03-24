#!/usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.web
import pymysql
import time

from settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PWD, MYSQL_DB
# from string import lower
import json
from lib import session
from lib.constant import SESSION_REDIS_EXPIRES
from lib.utils import to_str


class FoundHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, *args, **kwargs):
        super(FoundHandler, self).__init__(application, request, **kwargs)
        self.session = session.Session(self.application.session_manager, self)

    @property
    def redis(self):
        return self.application.redis

    @property
    def redis_spare(self):
        return self.application.redis_spare

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

    # def get_current_user(self):
    #     # print("session", self.session)
    #     return self.session.get("user_name")

    # 保存用户信息    open_id:{"user_id": xxx, "name": ssss}
    def save_user_info(self, open_id=None, user_uuid=None):
        cur = self.cur
        try:
            sql = "insert into user (open_id, uuid) value(%s, %s) on DUPLICATE KEY UPDATE open_id=%s "
            result = cur.execute(sql, [open_id, user_uuid, open_id])
            cur.connection.commit()
            if result:
                save = "sucess"
            else:
                save = "already"
        except Exception as e:
            save = "False"
            print(e)
        # print(save)
        return save

    def save_user_session(self, user_uuid, openid, session_key):
        user_session_value = {
            'uuid': user_uuid,
            'session_key': session_key
        }
        user_session_key = 'sx:' + openid
        with self.redis_spare.pipeline(transaction=False) as pipe:
            pipe.hmset(user_session_key, user_session_value)
            pipe.expire(user_session_key, SESSION_REDIS_EXPIRES)
            pipe.execute()

    def get_current_uuid(self, uuid):
        # print("session", self.session)
        user_info_session_key = "sx_info:" + uuid
        open_id = to_str(self.redis_spare.hget(user_info_session_key, "openid"))
        if open_id is None:
            return False
        user_session_key = 'sx:' + open_id
        session_key = self.redis_spare.hget(user_session_key, "session_key")
        return session_key

    # def get_uuid(self, user_session_key):
    #     return self.redis_spare.hget(user_session_key, "uuid")
    #
    # def get_level(self, user_session_key):
    #     return

    def get_session(self, user_session_key):
        return self.redis_spare.hgetall(user_session_key)

    def save_user_info_session(self, user_uuid, openid, level, current_score, target_score, color_num):
        user_info_session_value = {
            "openid": openid,
            "level": level,
            "current_score": current_score,
            "target_score": target_score,
            "color_num": color_num
        }
        user_info_session_key = "sx_info:" + user_uuid
        # print(user_info_session_value)
        with self.redis_spare.pipeline(transaction=False) as pipe:
            pipe.hmset(user_info_session_key, user_info_session_value)
            pipe.expire(user_uuid, SESSION_REDIS_EXPIRES)
            pipe.execute()

    def get_user_info_session(self, uuid):
        user_key = "sx_info:" + uuid
        return self.redis_spare.hgetall(user_key)

    # # 记录登陆时间,ip
    # def set_login_info(self):
    #     sql = "inset into admin_user (openid, login_time"




