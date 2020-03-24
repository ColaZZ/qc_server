#!/usr/bin/python3

import json

from apps.found_handler_v2 import RedisHandler
from lib.routes import route
from lib.authenticated_async import authenticated_async

from apps.models.user import User_Challenge
from apps.models.config import Config


# 1.闯关入口
@route('/challenge')
class ChallengeHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        user_info_session_key = "sx_info:" + uuid

        challenge_info = self.redis_spare.hget(user_info_session_key, "challenge_info")
        challenge_info_dict = json.loads(challenge_info)
        chan_dict = {}
        temp = "0"
        if type(challenge_info_dict) != dict:
            challenge_info_dict = eval(challenge_info_dict)

        for id, star in challenge_info_dict.items():
            chan_dict[id] = {
                "id": id,
                "star": star
            }
            if int(id) > int(temp):
                temp = id
        chan_dict["current_level"] = temp
        self.write_json(chan_dict)


# 2.进入关卡,获取关卡信息
@route('/challenge_info')
class ChallengeInfoHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        uuid = self.current_user.uuid
        level = int(self.get_argument("level", "") or 0)

        if not level:
            return self.write_json(status=-1, msg="请稍后重试")

        data = Config.challenge_config
        condition = data.get(level)
        condition["level"] = level
        self.write_json(condition)


# 3.挑战结束保存结果
@route('/challenge_next')
class ChallengeNextHandler(RedisHandler):
    @authenticated_async
    async def post(self):
        uuid = self.current_user.uuid
        level = str(self.get_argument("level", "") or 0)
        star = int(self.get_argument("star", "") or 0)
        # print(level, type(level))
        # print(star, type(star))
        if not level or not star:
            return self.write_json(status=-1, msg="请稍后重试")
        user_info_session_key = "sx_info:" + uuid
        user_challenge = await self.application.objects.get(User_Challenge, uuid=uuid)
        challenge_info = eval(user_challenge.challenge_info)
        challenge_info[level] = star
        if int(level) < 120:
            next_level = int(level) + 1
            if challenge_info.get(str(next_level), 0) == 0:
                challenge_info[next_level] = 0
        else:
            next_level = level

        config = Config.challenge_config
        condition = config.get(next_level)

        user_challenge.challenge_info = json.dumps(challenge_info)
        await self.application.objects.update(user_challenge)

        challenge_info_json = json.dumps(challenge_info)
        self.redis_spare.hset(user_info_session_key, "challenge_info", challenge_info_json)

        # test = await self.application.objects.get(User_Challenge, uuid=uuid)
        data = {
            "next_level": next_level,
            "condition": condition
        }
        self.write_json(data)




