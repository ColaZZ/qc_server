#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
API接口服务器主进程
"""
import os
import sys
import site
import logging

from tornado.options import parse_command_line
import tornado.httpserver
import tornado.ioloop
import tornado.web
from peewee_async import Manager

import redis
from settings import *
from lib.routes import route
import lib.session as session
from lib.utils import generate_cookie_secret, generate_session_secret

from lib.import_default_config import *
from models.models import database

ROOT = os.path.abspath(os.path.dirname(__file__))
path = lambda *a: os.path.join(*a)
site.addsitedir(path('vendor'))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = route.get_routes()
        redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)  # redis缓存连接池
        redis_spare_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_SPARE, decode_responses=True)  # redis缓存连接池
        self.redis = redis.StrictRedis(connection_pool=redis_pool, decode_responses=True)
        self.redis_spare = redis.StrictRedis(connection_pool=redis_spare_pool, decode_responses=True)

        app_settings = dict(
            debug=DEBUG,
            autoescape=None,
            gzip=True,
            static_path=os.path.join(ROOT, "static"),
            # 缓存相关
            session_timeout=SESSION_TIMEOUT,
            cookie_secret=generate_cookie_secret(),
            session_secret=generate_session_secret(),
            store_options={
                'redis_host': SESSION_REDIS_HOST,
                'redis_port': SESSION_REDIS_PORT,
                'redis_pass': "",
                'redis_db': SESSION_REDIS_DB,
            }
        )
        tornado.web.Application.__init__(self, handlers, **app_settings)
        self.session_manager = session.SessionManager(app_settings["session_secret"], app_settings["store_options"],
                                                      app_settings["session_timeout"])


for app_name in APPS:
    __import__("apps.%s" % app_name, fromlist=["handlers"])


def main():
    parse_command_line()
    logging.getLogger().setLevel(LOGGING_LEVEL)
    application = Application()

    # add peewee_async
    objects = Manager(database)
    # 开启异步
    database.set_allow_sync(False)
    application.objects = objects

    http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
    api_port = API_PORT if len(sys.argv) == 1 else int(sys.argv[1])

    http_server.bind(api_port)
    http_server.start()

    # 加载默认参数
    import_default_config()
    import_sign_config()
    import_sign_award_config()
    import_tool_config()
    import_loto_config()
    import_robot_config()
    import_challenge_config()

    print("API Server start on port %s" % api_port)

    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        logging.info("API Server stoped")
        sys.exit(0)


if __name__ == "__main__":
    main()
