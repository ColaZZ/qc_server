#!/usr/bin/python3

import os
import sys
import inspect

import pymysql
import openpyxl

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


# 导入关卡配置表
def import_game_config():
    path = r"/home/web/tornado_server/game_config/game_config.xlsx"
    # path = r"/mnt/d/tornado_server/game_config/game_config.xlsx"
    # path = r"/Users/zlinxx/tornado_server/game_config/game_config.xlsx"
    workbook = openpyxl.load_workbook(path)
    sheet = workbook['Sheet1']

    rows, config = [], []
    for row in sheet.rows:
        rows.append(row)

    for row in rows[1:]:
        value = [v.value for v in row[::-1]]
        value = tuple(value)
        config.append(value)

    sql = "update game_config set `direct`=%s, `color_num`=%s, `target_score`=%s where `level`=%s"
    try:
        cur.executemany(sql, config)
        cur.connection.commit()

    except:
        conn.rollback()
    conn.close()


if __name__ == "__main__":
    import_game_config()
