#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pymysql
import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from settings import *

conn = pymysql.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    passwd=MYSQL_PWD,
    db=MYSQL_DB,
    user=MYSQL_USER,
    charset='utf8'
)
cur = conn.cursor(cursor=pymysql.cursors.DictCursor)


def execute_scripts_from_file(filename):
    fd = open(filename, 'r', encoding='utf-8')
    sql_file = fd.read()
    fd.close()
    sql_commands = sql_file.split(';')

    for command in sql_commands:
        try:

            cur.execute(command)
        except Exception as e:
            print(command)
            print(e)
    print('sql执行完成')


if __name__ == "__main__":
    # 测试用例
    # executeScriptsFromFile("../game_test.sql")
    execute_scripts_from_file("./game.sql")
