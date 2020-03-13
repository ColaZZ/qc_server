#!/usr/bin/python3
# -*- coding: utf-8 -*-

from peewee import *

from apps.found_handler import FoundHandler
from apps.found_handler_v2 import RedisHandler
from lib.routes import route
from lib.utils import login_required
from lib.gernerate_colors import *
from apps.models.user import User, User_Level, User_Mall, User_Coins, User_Tools

from tornado import gen
from tornado.concurrent import run_on_executor
from tornado.concurrent import futures

from apps.models.config import Config
from apps.models.config import Game_Config
from lib.utils import random_robot


@route('/test_robot')
class TestRobotHandler(RedisHandler):
    def get(self):
        print(random_robot(Config.robot_config, "34,23"))


@route('/test.py')
class TestHandler(RedisHandler):

    @gen.coroutine
    async def get(self):
        user_mall = await self.application.objects.get(User_Mall, uuid="b953c357-6fea-4418-b03e-15d62dd59f32")
        data = {
            "id": user_mall.action_id,
            "action_name": user_mall.action_name,
            "action_status": user_mall.status
        }

        # game_config = await self.application.objects.execute(
        #     Game_Config.select(Game_Config.level, Game_Config.target_score, Game_Config.color_num) \
        #         .where(Game_Config.level.in_([2, 2]))
        # )
        # print(len(game_config))
        # # for gc in game_config:
        # #     print(gc.level, gc.target_score, gc.color_num)
        
        self.write_json(data)


@route('/test_main')
class TestMainHandler(RedisHandler):
    # @login_required

    async def get(self):
        # username = self.get_current_user()
        # print('start...')
        # print(username)
        open_id = "o3veQ4nZRtFABP3bVxlDwYMRnTF0"
        existed_user = await self.application.objects.get(User, open_id=open_id)
        user_uuid = existed_user.uuid
        login_time = existed_user.login_time.strftime('%Y-%m-%d')
        existed_user_level = await self.application.objects.get(User_Level, uuid=user_uuid)
        level = existed_user_level.level
        current_score = existed_user_level.current_score
        restart = existed_user_level.restart
        game_config = await self.application.objects.get(Game_Config, level=level)
        target_score = game_config.target_score
        color_num = game_config.color_num
        direct = game_config.direct

        user_coins = await self.application.objects.get(User_Coins, uuid=user_uuid)
        coins = user_coins.coins

        tools_result = await self.application.objects.execute(
            User_Tools.select(User_Tools.tool_id, User_Tools.count).where(User_Tools.uuid == user_uuid)
        )
        tools = {}
        for res in tools_result:
            tool_id = res.tool_id
            count = res.count
            tools[tool_id] = count

        verified = 0

        self.save_user_info_session(
            user_uuid=user_uuid,
            openid=open_id,
            level=level,
            current_score=current_score,
            target_score=target_score,
            color_num=color_num,
            verified=verified,
            tools=str(tools),
            coins=coins,
            direct=direct
        )
        data = {
            "user_uuid": user_uuid,
            "login_time": login_time,
            "level": level,
            "current_score": current_score,
            "restart": restart,
            "target_score": target_score,
            "color_num": color_num,
            "direct": direct

        }
        self.write_json(data)
        await self.finish()



@route('/test_login')
class TestLoginHandler(FoundHandler):
    async def get(self):
        score = self.redis_spare.zscore("world_rank", "zlinxx")
        print(score, type(score))


@route('/test_insert')
class TestInsertHandler(FoundHandler):
    async def get(self):
        cur = self.cur
        try:
            sql = "insert into user_level (uuid, `level`, next_level, current_score) values(%s, %s, %s, %s)"
            cur.execute(sql, ['test_uuid', 22, 23, 456])
            cur.connection.commit()
        except Exception as e:
            print(e)

@route('/verify_test')
class PersonalInfoTestHandler(RedisHandler):
    async def post(self):
        tool_id = int(self.get_argument("tool_id", "") or 0)
        count = int(self.get_argument("count", "") or 0)
        uuid = "3695cdd6-132f-4c80-bdc4-f4ce6c45e8e4"

        # print(chardet.detect(str.encode(name)))
        user_info_session_key = "sx_info:" + uuid

        user_tool = await self.application.objects.get(User_Tools, uuid=uuid, tool_id=tool_id)
        user_tool.count += count
        await self.application.objects.update(user_tool)
        print("ad_tools", user_info_session_key)
        redis_tools = eval(self.redis_spare.hget(user_info_session_key, "tools"))
        redis_tools[tool_id] = user_tool.count
        self.redis_spare.hset(user_info_session_key, "tools", str(redis_tools))
        tool_count = user_tool.count
        print(tool_id, tool_count)

        self.write_json(msg="success")
