#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
服务器静态配置项数据
"""

import logging
import platform
from os.path import join, dirname

from dotenv import load_dotenv, find_dotenv
import os
import re
from lib.utils import str_to_bool

load_dotenv(find_dotenv())

APPS = re.split(",", os.getenv("APPS"))  #需要启动的app
API_PORT = os.getenv("API_PORT")
DEBUG = str_to_bool(os.getenv("DEBUG"))

if not DEBUG:
    #*************生产环境配置*************
    DEBUG = os.getenv("DEBUG")
    LOGGING_LEVEL = logging.INFO

    # reids服务器
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_DB = os.getenv("REDIS_DB")
    REDIS_DB_SPARE = os.getenv("REDIS_DB_SPARE")

    # mysql服务器
    MYSQL_HOST = os.getenv("MYSQL_HOST")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
    MYSQL_DB = os.getenv("MYSQL_DB")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PWD = os.getenv("MYSQL_PWD")

    # session配置
    SESSION_TIMEOUT = os.getenv("SESSION_TIMEOUT")
    SESSION_REDIS_HOST = os.getenv("SESSION_REDIS_HOST")
    SESSION_REDIS_PORT = os.getenv("SESSION_REDIS_PORT")
    SESSION_REDIS_DB = os.getenv("SESSION_REDIS_DB")

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
    MYSQL_DB = "hlxxx_p"
    MYSQL_USER = "root"
    MYSQL_PWD = "123456"

    # session配置
    SESSION_TIMEOUT = 600
    SESSION_REDIS_HOST = "127.0.0.1"
    SESSION_REDIS_PORT = "6379"
    SESSION_REDIS_DB = 1


