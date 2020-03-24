#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import datetime

from peewee import *
import jwt


from apps.found_handler_v2 import RedisHandler
from lib.routes import route
# from lib.utils import login_required
from lib.utils import to_str, random_robot
from lib.authenticated_async import authenticated_async
from apps.models.user import User_Level, User, User_Sign, User_Coins, User_Loto, User_Tools
from apps.models.config import Game_Config, Config
from lib.gernerate_colors import random_color_array
from lib.loto import loto
from lib.constant import SECRET_KEY, SESSION_REDIS_EXPIRES


# 世界排名
@route("/rank")
class RankHandler(RedisHandler):
    # @authenticated_async
    async def get(self):
        data = []
        # result = []
        result = self.redis_spare.zrevrange("world_rank", 0, 99, withscores=True)
        if result:
            for key, value in result:

                name = to_str(key)
                if name != "visitor访客":
                    score = int(value)
                    rank = result.index((key, value)) + 1
                    avatar = to_str(self.redis_spare.hget("user_avatar", name))
                    data.append({
                        "rank": rank,
                        "name": name,
                        "score": score,
                        "avatarUrl": avatar
                    })
                else:
                    pass
        else:
            # 缓存失效的情况
            # 前100名排名
            # result = self.application.objects.execute(
            #     User_Level.select(User_Level.uuid, User_Level.current_score, fn.rank())\
            #     .order_by(User_Level.current_score)
            # )
            result = await self.application.objects.execute(
                User_Level.select(User.name, User.avatar, User_Level.uuid, User_Level.current_score, User_Level.history_score).join(
                    User, JOIN.LEFT_OUTER, on=(User.uuid == User_Level.uuid)
                ).order_by(-User_Level.current_score)
            )

            for rk in result:
                print(rk)
                name = rk.uuid.name
                score = rk.current_score
                history_score = rk.history_score
                if name and (score or history_score):
                    avatar = rk.uuid.avatar
                    score = rk.current_score if rk.current_score > rk.history_score else rk.history_score
                    data.append({
                        "name": name,
                        "score": score,
                        "avatarUrl": avatar
                    })
                    # 排好的名次push入redis缓存
                    self.redis_spare.zadd("world_rank", {name: score})

                    self.redis_spare.hset("user_avatar", name, avatar)
                else:
                    pass

            # TODO 改成mysql直接输出排名
            for d in data:
                rank = data.index(d)
                d["rank"] = rank + 1

        self.write_json(data)
        # to do 分布式


@route("/restart")
class RestartHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        print(uuid)
        # 1. 删缓存
        user_info_session_key = "sx_info:" + uuid
        # open_id = self.redis_spare.hget(user_info_session_key, "open_id")
        name = self.redis_spare.hget(user_info_session_key, "name")
        tools = self.redis_spare.hget(user_info_session_key, "tools")
        print(type(tools))
        # verified = self.redis_spare.hget(user_info_session_key, "verified")
        # coins = self.redis_spare.hget(user_info_session_key, "coins")
        # print(self.redis_spare.hgetall(user_info_session_key))
        # print(coins)
        # self.redis_spare.delete(user_info_session_key)

        # 2. 更新数据库
        user_level = await self.application.objects.get(User_Level, uuid=uuid)
        user_level.level = 1
        user_level.next_level = 2
        current_score = int(user_level.current_score)
        user_level.current_score = 0
        user_level.restart = 1
        history_score = user_level.history_score
        await self.application.objects.update(user_level)
        try:
            game_config = await self.application.objects.get(Game_Config, level=1)
            next_target_score = game_config.target_score
            next_color_num = game_config.color_num
            nn_next_game_config = await self.application.objects.get(Game_Config, level=2)
            nnext_target_score = nn_next_game_config.target_score
        except Game_Config.DoesNotExist as e:
            return self.write_json(status=-2, msg="请重新刷新配置")

        # set缓存

        value = {
            "level": user_level.level,
            "current_score": user_level.current_score,
            "target_score": next_target_score,
            "color_num": next_color_num,
            "restart": 1
        }
        self.redis_spare.hmset(user_info_session_key, value)

        # 存入排行榜 20200213 删掉
        # if name:
        #     # name = "visitor访客"
        #     self.redis_spare.zadd("world_rank", {name: 0})
        color_array, random_list = random_color_array(1, int(next_color_num))

        payload = {
            "uuid": uuid,
            "exp": datetime.datetime.utcnow()
        }
        tuuid = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        random_dict = {}
        for rl in random_list:
            random_dict[rl] = 0

        for ca in color_array:
            for c in ca:
                random_dict[c] += 1

        # 超越好友
        user_robot_key = "robot:" + uuid
        restart_times = int(self.redis_spare.hget(user_robot_key, "restart") or 0) + 1
        robot_user_dict, robot_last = random_robot(Config.robot_config, "", current_score, nnext_target_score, restart=restart_times)
        robot_user_dict["restart"] = restart_times
        self.redis_spare.hmset(user_robot_key, robot_user_dict)
        robot_user = {
            "robot_name": robot_user_dict.get("name", 0),
            "robot_avatar": robot_user_dict.get("avatar", ""),
            "robot_score": robot_user_dict.get("score", "")
        }

        data = {
            "level": 1,
            "target_score": next_target_score,
            # "next_color_num": next_color_num,
            "current_score": 0,
            "color_array": color_array,
            "tools": eval(tools),
            "uuid": to_str(tuuid),
            "random_dict": random_dict,
            "history_score": history_score,
            "robot": robot_user

        }
        self.write_json(data)


# 签到界面
@route("/signBoard")
class SignBoardHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        day_time = int(time.mktime(datetime.date.today().timetuple()))
        user_info_session = self.get_user_info_session(uuid)
        if user_info_session:
            continuous_sign_days = user_info_session.get("continuous_sign_days", 0)
            lastest_sign_date = user_info_session.get("lastest_sign_date", "")
        else:
            user_sign = await self.application.objects.get(User_Sign, uuid=uuid)
            lastest_sign_date = user_sign.lastest_sign_date.strftime('%Y-%m-%d')
            continuous_sign_days = user_sign.continuous_sign_days
            user_info_session_key = "sx_info:" + uuid
            self.redis_spare.hset(user_info_session_key, "lastest_sign_date", lastest_sign_date)
            self.redis_spare.hset(user_info_session_key, "continuous_sign_days", continuous_sign_days)

        timeArray = time.strptime(lastest_sign_date, "%Y-%m-%d")
        lastest_sign_timestamp = int(time.mktime(timeArray))

        # 连续签到几天
        if lastest_sign_timestamp >= day_time - 3600 * 24:
            continuous_sign_days = continuous_sign_days
        else:
            continuous_sign_days = 0
        data = {
            "days": int(continuous_sign_days)
        }
        self.write_json(data)


# 签到按钮
@route("/sign")
class SignHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        day_time = int(time.mktime(datetime.date.today().timetuple()))
        # 双倍开关
        double = int(self.get_argument("double", "") or 0)
        extra = int(self.get_argument("extra", "") or 0)

        if extra and double:
            return self.write_json(status=-3, msg="签到失误,请稍后再试2")

        try:
            user_sign = await self.application.objects.get(User_Sign, uuid=uuid)

            if str(user_sign.lastest_sign_date) == time.strftime("%Y-%m-%d", time.localtime()) and user_sign.extra:
                return self.write_json(status=-4, msg="今日已签到4")

            if str(user_sign.lastest_sign_date) == time.strftime("%Y-%m-%d", time.localtime()) and double:
                return self.write_json(status=-5, msg="签到失误,请稍后再试2")

            if str(user_sign.lastest_sign_date) == time.strftime("%Y-%m-%d", time.localtime()) and not extra:
                return self.write_json(status=-6, msg="签到失误,请稍后再试6")



            continuous_sign_days = user_sign.continuous_sign_days
            lastest_sign_date = user_sign.lastest_sign_date.strftime('%Y-%m-%d')
            timeArray = time.strptime(lastest_sign_date, "%Y-%m-%d")
            lastest_sign_timestamp = int(time.mktime(timeArray))

            if not extra:
                if lastest_sign_timestamp == day_time - 24 * 3600:
                    if continuous_sign_days == 7:
                        continuous_sign_days = 1
                    else:
                        continuous_sign_days = (continuous_sign_days + 1) % 8
                elif lastest_sign_timestamp == day_time:
                    continuous_sign_days = continuous_sign_days
                else:
                    continuous_sign_days = 1

            # reward_id = Config.sign_config.get(continuous_sign_days)
            # reward_dict = Config.sign_award_config.get(reward_id)

            user_sign.lastest_sign_date = time.strftime("%Y-%m-%d", time.localtime())
            user_sign.continuous_sign_days = continuous_sign_days

            user_coins = await self.application.objects.get(User_Coins, uuid=uuid)
            reward_coins = 10 * int(continuous_sign_days)
            user_coins.coins += reward_coins * 2 if double else reward_coins
            if double or extra:
                user_sign.extra = 1

            try:
                await self.application.objects.update(user_sign)
                await self.application.objects.update(user_coins)
                user_info_session_key = "sx_info:" + uuid
                self.redis_spare.hset(user_info_session_key, "lastest_sign_date", user_sign.lastest_sign_date)
                self.redis_spare.hset(user_info_session_key, "continuous_sign_days", continuous_sign_days)
                self.redis_spare.hset(user_info_session_key, "coins", user_coins.coins)
                self.redis_spare.hset(user_info_session_key, "extra", user_sign.extra)
                data = {
                    "days": continuous_sign_days,
                    "today_sign_status": 1,
                    "coins": user_coins.coins
                }
                self.write_json(data)
            except Exception as e:
                self.write_json(status=-2, msg="签到失误,请稍后再试")
        except User_Sign.DoesNotExist as e:
            self.write_json(status=-1, msg="无签到记录")


@route("/get_coins")
class GetCoinsHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        count = int(self.get_argument("count", "") or 0)

        uuid = self.current_user.uuid
        try:
            user_coins = await self.application.objects.get(User_Coins, uuid=uuid)
            user_coins.coins += count
            await self.application.objects.update(user_coins)

            user_info_session_key = "sx_info:" + uuid
            self.redis_spare.hset(user_info_session_key, "coins", user_coins.coins)

            data = {
                "coins": user_coins.coins
            }
            self.write_json(data)

        except User_Coins.DoesNotExist as e:
            self.write_json(status=-1, msg="请稍后再试")


@route("/loto")
class LotoHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid

        try:
            per_list = []
            user_loto = await self.application.objects.get(User_Loto, uuid=uuid)
            if user_loto.number <= 0:
                return self.write_json(status=-2, msg="抽奖次数不足")

            user_loto.number -= 1
            loto_config = Config.loto_config
            id_list = list(loto_config.keys())
            for _, v in loto_config.items():
                per_list.append(v.get("per", 0) / 100)
            id = loto(id_list, per_list)
            tool_id = loto_config.get(id, {}).get('tool_id', 0)
            num = loto_config.get(id, {}).get('num', 0)

            if not tool_id or not num:
                self.write_json(status=-2, msg="请重新刷新配置")

            user_info_session_key = "sx_info:" + uuid
            user_coins = await self.application.objects.get(User_Coins, uuid=uuid)
            redis_tools = eval(self.redis_spare.hget(user_info_session_key, "tools"))
            if tool_id == 1001:
                # coins
                user_coins.coins += num
                await self.application.objects.update(user_coins)

                self.redis_spare.hset(user_info_session_key, "coins", user_coins.coins)

            else:
                # tools
                user_tool = await self.application.objects.get(User_Tools, uuid=uuid, tool_id=tool_id)
                user_tool.count += num
                await self.application.objects.update(user_tool)
                redis_tools[tool_id] = user_tool.count
                self.redis_spare.hset(user_info_session_key, "tools", str(redis_tools))
            await self.application.objects.update(user_loto)
            data = {
                "reward_id": id, 
                "tool_id": tool_id,
                "count": num,
                "loto_num": user_loto.number,
                "coins": user_coins.coins,
                "tools": redis_tools
            }
            self.write_json(status=1, msg="抽奖成功", data=data)

        except User_Loto.DoesNotExist as e:
            self.write_json(status=-1, msg="请稍后再试")


















