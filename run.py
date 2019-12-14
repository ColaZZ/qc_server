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

import redis
from settings import *
from lib import session
from lib.routes import route
from lib.utils import generate_cookie_secret, generate_session_secret

ROOT = os.path.abspath(os.path.dirname(__file__))
path = lambda *a: os.path.join(*a)
site.addsitedir(path('vendor'))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = route.get_routes()
        # print(handlers)
        redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)    # redis缓存连接池
        self.redis = redis.Redis(connection_pool=redis_pool)

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
    http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
    api_port = API_PORT if len(sys.argv) == 1 else int(sys.argv[1])

    http_server.bind(api_port)
    http_server.start()

    print("API Server start on port %s" % api_port)

    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.info("API Server stoped")
        sys.exit(0)


if __name__ == "__main__":
    main()
