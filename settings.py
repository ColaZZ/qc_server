#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
服务器静态配置项数据
"""

import logging
import platform

PRD_SERVER = ["iZj6c28175n4uyqeuxks6zZ"]
APPS = ('api_v1',)  #需要启动的app
API_PORT = 8080

if platform.node() in PRD_SERVER:
    #*************生产环境配置*************
    DEBUG = False
    LOGGING_LEVEL = logging.ERROR

    # reids服务器
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_DB_SPARE = 2

    # mysql服务器
    MYSQL_HOST = "127.0.0.1"
    MYSQL_PORT = ""
    MYSQL_DB = "game"
    MYSQL_USER = "root"
    MYSQL_PWD = "d52695122b70f465"

    # session配置
    SESSION_TIMEOUT = 600
    SESSION_REDIS_HOST = "127.0.0.1"
    SESSION_REDIS_PORT = "6379"
    SESSION_REDIS_DB = 1

else:
    #*************开发/测试环境配置*************
    DEBUG = True
    LOGGING_LEVEL = logging.INFO

    # reids服务器
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = "6379"
    REDIS_DB = 0
    REDIS_DB_SPARE = 2

    # mysql服务器
    MYSQL_HOST = "127.0.0.1"
    MYSQL_PORT = 3306
    MYSQL_DB = "game"
    MYSQL_USER = "root"
    MYSQL_PWD = "123456"

    # session配置
    SESSION_TIMEOUT = 600
    SESSION_REDIS_HOST = "127.0.0.1"
    SESSION_REDIS_PORT = "6379"
    SESSION_REDIS_DB = 1


