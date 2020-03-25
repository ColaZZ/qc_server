#!/usr/bin/python3

from apps.found_handler_v2 import RedisHandler
from lib.routes import route
# from lib.constant import USER_SESSION_KEY
from lib.gernerate_colors import random_color_array
from apps.models.config import Config
from lib.authenticated_async import authenticated_async
from apps.models.user import User_Level
from apps.models.config import Game_Config
from lib.utils import random_robot


# 下一关
@route("/next_level")
class LevelHandler(RedisHandler):
    @authenticated_async
    async def get(self):
        level = int(self.get_argument("level", "") or 0)
        score = int(self.get_argument("score", "") or 0)

        if not score or not level:
            return self.write_json(status=-1, msg="请稍后重试")
        uuid = self.current_user.uuid

        # 先删缓存再更新数据库
        # 1. 删除缓存
        user_info_session_key = "sx_info:" + uuid
        # open_id = self.redis_spare.hget(user_info_session_key, "open_id")
        # name = self.redis_spare.hget(user_info_session_key, "name")
        # verified = self.redis_spare.hget(user_info_session_key, "verified")
        # tools = self.redis_spare.hget(user_info_session_key, "tools")
        # coins = self.redis_spare.hget(user_info_session_key, "coins")
        # print(coins)
        # self.redis_spare.delete(user_info_session_key)
        name = self.redis_spare.hget(user_info_session_key, "name")

        # TODO 后端判断分数是否达标
        # v1 从redis缓存中获取target_score
        target_score = int(self.redis_spare.hget(user_info_session_key, "target_score"))
        if score < target_score:
            return self.write_json(status=-2, msg="分数未达到,请重试")

        # 2. 更新数据库
        next_level = level + 1

        # game_config = await self.application.objects.get(Game_Config, level=next_level)
        # game_config = Game_Config.select(Game_Config.level, Game_Config.target_score, Game_Config.color_num)\
        #     .where(Game_Config.level.in_(level, next_level))
        game_config = await self.application.objects.execute(
            Game_Config.select(Game_Config.level, Game_Config.target_score, Game_Config.color_num, Game_Config.direct) \
                .where(Game_Config.level.in_([level, next_level]))
        )

        next_target_score = next_color_num = direct = nnext_target_score = 0
        if len(game_config) == 1:
            # 已到达最大关卡
            next_level = next_level1 = level
            for gc in game_config:
                next_target_score = gc.target_score
                next_color_num = gc.color_num
                direct = gc.direct
                nnext_target_score = next_target_score

        elif len(game_config) == 2:
            # 未达到最大关卡
            next_level1 = next_level + 1
            for gc in game_config:
                if next_level == gc.level:
                    next_target_score = gc.target_score
                    next_color_num = gc.color_num
                    direct = gc.direct
                    nn_next_game_config = await self.application.objects.get(Game_Config, level=next_level1 + 1)
                    nnext_target_score = nn_next_game_config.target_score
        else:
            next_level1 = 1
        user_level = await self.application.objects.get(User_Level, uuid=uuid)
        user_level.level = next_level
        user_level.next_level = next_level1
        user_level.current_score = score
        restart = user_level.restart
        history_score_m = user_level.history_score
        if history_score_m < score:
            user_level.history_score = score
            history_score = score
        else:
            history_score = history_score_m
        await self.application.objects.update(user_level)

        # set 缓存
        # self.save_user_info_session(
        #     user_uuid=uuid,
        #     openid=open_id,
        #     level=level,
        #     current_score=score,
        #     target_score=next_target_score,
        #     color_num=next_color_num,
        #     verified=verified,
        #     tools=tools,
        #     coins=coins
        # )
        value = {
            "level": next_level,
            "current_score": score,
            "target_score": next_target_score,
            "color_num": next_color_num,
            "direct": direct,
            "history_score": history_score
        }
        self.redis_spare.hmset(user_info_session_key, value)

        # 存入排行榜
        if name and history_score_m < score:
            self.redis_spare.zadd("world_rank", {name: score})

        #
        random_dict = {}
        # if int(next_level) % 10 == 0:
        #     default_config = Config.default_config
        #     color_array = default_config.get(next_level, [])
        #     for ca in color_array:
        #         for c in ca:
        #             if c not in random_dict:
        #                 random_dict[c] = 1
        #             else:
        #                 random_dict[c] += 1
        # else:
        color_array, random_list = random_color_array(int(level), int(next_color_num))

        for rl in random_list:
            random_dict[rl] = 0

        for ca in color_array:
            for c in ca:
                random_dict[c] += 1

        # 超越好友
        user_robot_key = "robot:" + uuid
        robot_user_dict = self.redis_spare.hgetall(user_robot_key)
        robot_score = int(robot_user_dict.get("score", 0))
        robot_list = robot_user_dict.get("robot_list", "")
        if score > robot_score:
            robot_user_dict, robot_list = random_robot(Config.robot_config, robot_list, next_target_score, nnext_target_score)
            robot_user_dict["robot_list"] = robot_list
            self.redis_spare.hmset(user_robot_key, robot_user_dict)

        robot_user = {
            "robot_name": robot_user_dict.get("name", 0),
            "robot_avatar": robot_user_dict.get("avatar", ""),
            "robot_score": robot_user_dict.get("score", "")
        }
        data = {
            "next_level": next_level,
            "next_target_score": next_target_score,
            "next_color_num": next_color_num,
            "score": score,
            "color_array": color_array,
            "random_dict": random_dict,
            "direct": direct,
            "history_score": history_score,
            "robot": robot_user
        }
        self.write_json(data)




