#!/usr/bin/python3

import json
import uuid
import datetime
import time
# import chardet
import json

import jwt

from apps.found_handler_v2 import RedisHandler
from lib.routes import route
from lib.utils import to_str, get_user_info, random_robot
from lib.authenticated_async import authenticated_async, encode_tuuid
from lib.gernerate_colors import random_color_array
# from apps.models.config import Config
from lib.constant import USER_SESSION_KEY, COLOR_NUM_CONST, TARGET_SCORE_CONST, SECRET_KEY, APPID
from apps.models.user import User, User_Level, User_Coins, User_Tools, User_Sign, User_Mall, User_Loto, User_Challenge
from apps.models.config import Game_Config, Config
from lib.WXBizDataCrypt import WXBizDataCrypt


@route('/login')
class LoginHandler(RedisHandler):
    async def post(self):
        req_data = json.loads(to_str(self.request.body))
        js_code = req_data.get("code", "")
        sceneId = req_data.get("sceneId", "")
        query = req_data.get("query", "")
        encryptedData = req_data.get("encryptedData", "")
        iv = req_data.get("iv", "")

        if type(sceneId) not in [str, int]:
            env_code = 0
        else:
            env_code = int(sceneId)

        from_id = ""
        if query:
            from_keys = list(query.keys())
            if from_keys:
                from_id = from_keys[0]
                from_id = encode_tuuid(from_id)

        # js_code = self.get_argument("code", "")
        # env_code = int(self.get_argument("sceneId", "") or 0)
        # from_id = str(self.get_argument("from_id", "") or 0)

        # 三个参数缺一不可
        if not js_code:
            return self.write_json(status=-1, msg="上报code有误，请核对")

        # 1.获取用户信息
        # print("js_code", js_code)
        user_info = get_user_info(js_code)
        # user_info = {"openid": "sss", "session_key": "aaa"}
        # print("user_info", user_info)
        open_id = user_info.get("openid", "")

        if not open_id:
            return self.write_json(status=-2, msg="上报code有误，请核对")

        # 2.获取session_key
        session_key = user_info.get("session_key", "")
        # user_session_key = USER_SESSION_KEY + open_id
        user_session = self.get_session(open_id)

        if encryptedData and iv:
            pc = WXBizDataCrypt(APPID, session_key)
            WX_data = pc.decrypt(encryptedData, iv)
            unionId = WX_data.get("unionId", "")
        else:
            unionId = ""

        today = time.strftime("%Y-%m-%d", time.localtime())
        day_time = int(time.mktime(datetime.date.today().timetuple()))
        # 3. 登陆时未找到缓存
        if user_session == [{}] or not user_session:
            user_uuid = str(uuid.uuid4())
            # 3.1 用户是否注册过
            try:
                # 3.1.1 注册过,缓存过期
                existed_user = await self.application.objects.get(User, open_id=open_id)
                user_uuid = existed_user.uuid
                login_time = existed_user.login_time.strftime('%Y-%m-%d')
                name = existed_user.name
                existed_user_level = await self.application.objects.get(User_Level, uuid=user_uuid)
                level = existed_user_level.level
                current_score = existed_user_level.current_score
                restart = existed_user_level.restart
                history_score = existed_user_level.history_score
                game_config = await self.application.objects.get(Game_Config, level=level)
                target_score = game_config.target_score
                color_num = game_config.color_num
                direct = game_config.direct

                user_coins = await self.application.objects.get(User_Coins, uuid=user_uuid)
                coins = user_coins.coins
                verified = 1 if name else 0

                tools_result = await self.application.objects.execute(
                    User_Tools.select(User_Tools.tool_id, User_Tools.count).where(User_Tools.uuid==user_uuid)
                )
                tools = {}
                for res in tools_result:
                    tool_id = res.tool_id
                    count = res.count
                    tools[tool_id] = count

                # 最后登录
                user_sign = await self.application.objects.get(User_Sign, uuid=user_uuid)
                lastest_sign_date = user_sign.lastest_sign_date.strftime('%Y-%m-%d')
                continuous_sign_days = user_sign.continuous_sign_days
                timeArray = time.strptime(lastest_sign_date, "%Y-%m-%d")
                lastest_sign_timestamp = int(time.mktime(timeArray))
                extra = int(user_sign.extra)
                if lastest_sign_timestamp < day_time - 3600 * 24:
                    continuous_sign_days = 0
                if lastest_sign_timestamp == day_time - 3600 * 24 and int(continuous_sign_days) == 7:
                    continuous_sign_days = 0

                today_sign_status = 0

                if lastest_sign_date == today:
                    # signboard = 0
                    today_sign_status = 1

                if lastest_sign_date != today and extra:
                    today_sign_status = 0
                    user_sign.extra = 0
                    await self.application.objects.update(user_sign)
                    extra = 0


                signboard = 0
                try:
                    user_loto = await self.application.objects.get(User_Loto, uuid=user_uuid)
                    loto_num = user_loto.number
                except User_Loto.DoesNotExist as e:
                    user_loto = await self.application.objects.create(User_Loto, uuid=user_uuid, number=3)
                    loto_num = 3

                # loto_num = user_loto.number
                if lastest_sign_date < today:
                    signboard = 1

                if login_time < today:
                    existed_user.login_time = today
                    await self.application.objects.update(existed_user)
                    # loto
                    user_loto.number = loto_num = 3
                    await self.application.objects.update(user_loto)

                    for i in range(1, 6):
                        user_mall = await self.application.objects.get(User_Mall, uuid=user_uuid, action_id=i)
                        # if i == 1:
                        user_mall.daily_status = 0
                        if user_mall.status == 2:
                            user_mall.status = 0
                            await self.application.objects.update(user_mall)

                lotoboard = 1 if loto_num else 0

                if int(env_code) == 1089:
                    # 收藏渠道4
                    try:
                        user_mall = await self.application.objects.get(User_Mall, uuid=user_uuid, action_id=4)
                        if not user_mall.status:
                            user_mall.status = 1
                            await self.application.objects.update(user_mall)
                    except User_Mall.DoesNotExist as e:
                        pass

                elif int(env_code) == 1131:
                    # 浮窗渠道5
                    try:
                        user_mall = await self.application.objects.get(User_Mall, uuid=user_uuid, action_id=5)
                        if not user_mall.status:
                            user_mall.status = 1
                            await self.application.objects.update(user_mall)
                    except User_Mall.DoesNotExist as e:
                        pass
                new_user = 0

                # 闯关模式
                try:
                    user_challenge = await self.application.objects.get(User_Challenge, uuid=user_uuid)
                    challenge_info = user_challenge.challenge_info
                    challenge_info_json = json.dumps(to_str(challenge_info))
                except User_Challenge.DoesNotExist as e:
                    challenge_info = {"1": 0}
                    challenge_info_json = json.dumps(challenge_info)
                    await self.application.objects.create(User_Challenge, uuid=user_uuid,
                                                          challenge_info=challenge_info_json)


            # 3.1.2 未注册过
            # TODO 新用户初始化
            except User.DoesNotExist as e:

                login_time = today
                await self.application.objects.create(User, open_id=open_id, uuid=user_uuid, login_time=login_time)
                user_level = await self.application.objects.create(User_Level, uuid=user_uuid, level=1,
                                                                   next_level=2, current_score=0, history_score=0)
                current_score = 0
                history_score = 0
                game_config = await self.application.objects.get(Game_Config, level=1)
                level = game_config.level
                target_score = game_config.target_score
                color_num = game_config.color_num
                direct = game_config.direct

                tools = {}
                tool_source = []
                tool_config = Config.tool_config.keys()
                for key in tool_config:
                    tools[key] = 0
                    tool_source.append(
                        {"uuid": user_uuid, "tool_id": key, "count": 0}
                    )
                await self.application.objects.execute(
                    User_Tools.insert_many(tool_source)
                )

                coins = 0
                restart = 0

                # 生成签到表
                await self.application.objects.create(User_Sign, uuid=user_uuid,
                                                      lastest_sign_date="1900-01-01", continuous_sign_days=0, extra=0)
                # 生成mall表
                data_source = [
                    {"uuid": user_uuid, "action_id": 1, "action_name": "视频广告", "status": 0, "daily_status": 0},
                    {"uuid": user_uuid, "action_id": 2, "action_name": "邀请好友", "status": 0, "daily_status": 0},
                    {"uuid": user_uuid, "action_id": 3, "action_name": "客服会话", "status": 0, "daily_status": 0},
                    {"uuid": user_uuid, "action_id": 4, "action_name": "收藏", "status": 0, "daily_status": 0},
                    {"uuid": user_uuid, "action_id": 5, "action_name": "浮窗", "status": 0, "daily_status": 0},
                ]
                # field = (User_Mall.uuid, User_Mall.action_id, User_Mall.action_name, User_Mall.status)
                await self.application.objects.execute(
                    User_Mall.insert_many(data_source)
                )

                await self.application.objects.create(User_Coins, uuid=user_uuid, coins=0)
                await self.application.objects.create(User_Loto, uuid=user_uuid)

                loto_num = 3
                lotoboard = 1
                signboard = 1
                continuous_sign_days = 0
                today_sign_status = 0
                lastest_sign_date = "1900-01-01"
                extra = 0
                verified = 0
                new_user = 1

                # # 是否邀请而来
                if from_id:
                    try:
                        user_mall = await self.application.objects.get(User_Mall, uuid=from_id, action_id=2)
                        if user_mall.status == 0:
                            user_mall.status = 1
                            await self.application.objects.update(user_mall)
                    except User_Mall.DoesNotExist as e:
                        pass

                # 初始化闯关模式
                challenge_info = {"1": 0}
                challenge_info_json = json.dumps(challenge_info)
                await self.application.objects.create(User_Challenge, uuid=user_uuid, challenge_info=challenge_info_json)


            # 3.1.3 保存缓存
            self.save_user_session(user_uuid, open_id, session_key)
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
                direct=direct,
                history_score=history_score
            )
            user_info_session_key = "sx_info:" + user_uuid
            self.redis_spare.hset(user_info_session_key, "lastest_sign_date", lastest_sign_date)
            self.redis_spare.hset(user_info_session_key, "continuous_sign_days", continuous_sign_days)
            self.redis_spare.hset(user_info_session_key, "login_time", login_time)
            self.redis_spare.hset(user_info_session_key, "restart", restart)
            self.redis_spare.hset(user_info_session_key, "loto_num", loto_num)
            self.redis_spare.hset(user_info_session_key, "extra", extra)
            self.redis_spare.hset(user_info_session_key, "challenge_info", challenge_info_json)
        else:
            user_session = user_session[0]

            user_uuid = user_session.get("uuid", "")
            user_info_session = self.get_user_info_session(user_uuid)
            level = user_info_session.get("level", 1)
            current_score = user_info_session.get("current_score", 0)
            target_score = user_info_session.get("target_score", TARGET_SCORE_CONST)
            color_num = user_info_session.get("color_num", COLOR_NUM_CONST)
            name = user_info_session.get("name", "")
            continuous_sign_days = user_info_session.get("continuous_sign_days", 0)
            lastest_sign_date = user_info_session.get("lastest_sign_date", "")
            coins = user_info_session.get("coins", 0)
            login_time = user_info_session.get("login_time", "")
            tools = eval(user_info_session.get("tools", "{}"))
            restart = int(user_info_session.get('restart', 0))
            direct = user_info_session.get('direct', 0)
            extra = int(user_info_session.get('extra', 0))
            history_score = int(user_info_session.get("history_score", 0))
            # challenge_info = eval(user_info_session.get("challenge_info", {}))




            if not history_score:
                user_level = await self.application.objects.get(User_Level, uuid=user_uuid)
                history_score = user_level.history_score
                if history_score:
                    user_info_session_key = "sx_info:" + user_uuid
                    self.redis_spare.hset(user_info_session_key, "history_score", history_score)


            timeArray = time.strptime(lastest_sign_date, "%Y-%m-%d")
            lastest_sign_timestamp = int(time.mktime(timeArray))
            if lastest_sign_timestamp == day_time - 3600 * 24 and int(continuous_sign_days) == 7:
                continuous_sign_days = 0

            if int(env_code) == 1089:
                # 收藏渠道4
                try:
                    user_mall = await self.application.objects.get(User_Mall, uuid=user_uuid, action_id=4)

                    if not user_mall.status:
                        user_mall.status = 1
                        await self.application.objects.update(user_mall)
                except User_Mall.DoesNotExist as e:
                    pass

            elif int(env_code) == 1131:
                # 浮窗渠道5
                try:
                    user_mall = self.application.objects.get(User_Mall, uuid=user_uuid, action_id=5)
                    if user_mall.status != 1:
                        user_mall.status = 1
                        await self.application.objects.update(user_mall)
                except User_Mall.DoesNotExist as e:
                    pass
            verified = 1 if name else 0
            new_user = 0

            user_info_session_key = "sx_info:" + user_uuid

            today_sign_status = 0
            signboard = 0
            if lastest_sign_date != today:
                signboard = 1
                today_sign_status = 0

            if lastest_sign_date == today:
                signboard = 0
                today_sign_status = 1
            if lastest_sign_date != today and extra:
                user_sign = await self.application.objects.get(User_Sign, uuid=user_uuid)
                user_sign.extra = 0
                await self.application.objects.update(user_sign)
                self.redis_spare.hset(user_info_session_key, "extra", 0)
                extra = 0


            try:
                user_loto = await self.application.objects.get(User_Loto, uuid=user_uuid)
                loto_num = user_loto.number
            except User_Loto.DoesNotExist as e:
                user_loto = await self.application.objects.create(User_Loto, uuid=user_uuid, number=3)
                loto_num = 3

            # signboard = 0
            # if lastest_sign_date < today:
            #     signboard = 1


            if login_time < today:
                existed_user = await self.application.objects.get(User, uuid=user_uuid)
                existed_user.login_time = today
                await self.application.objects.update(existed_user)
                self.redis_spare.hset(user_info_session_key, "login_time", today)

                user_loto.number = loto_num = 3
                await self.application.objects.update(user_loto)
                self.redis_spare.hset(user_info_session_key, "loto_num", loto_num)

                for i in range(1, 6):
                    user_mall = await self.application.objects.get(User_Mall, uuid=user_uuid, action_id=i)
                    # if i == 1:
                    user_mall.daily_status = 0
                    if user_mall.status == 2:
                        user_mall.status = 0
                        await self.application.objects.update(user_mall)

            lotoboard = 1 if loto_num else 0

        # 微信小程序不能设置cookie，把用户信息存在了headers中
        self.set_header("Authorization", user_uuid)

        # 超越好友
        user_robot_key = "robot:" + user_uuid
        robot_user_dict = self.redis_spare.hgetall(user_robot_key)

        if not robot_user_dict:
            next_game_config = await self.application.objects.get(Game_Config, level=int(level) + 1)
            next_target_score = next_game_config.target_score if next_game_config.target_score else target_score
            robot_user_dict, robot_last = random_robot(Config.robot_config, "", int(target_score), int(next_target_score))
            print(robot_user_dict, robot_last)
            # self.redis_spare.hset(user_info_session_key, str(robot_user))
            robot_user_dict["robot_list"] = robot_last
            robot_user_dict["restart"] = 0
            if "id" in robot_user_dict:
                robot_user_dict.pop("id")
            self.redis_spare.hmset(user_robot_key, robot_user_dict)

        robot_user = {
            "robot_name": robot_user_dict.get("name", 0),
            "robot_avatar": robot_user_dict.get("avatar", ""),
            "robot_score": robot_user_dict.get("score", "")
        }

        # 生成color地图
        random_dict = {}

        # if int(level) == 1 or int(level) % 10 == 0:
        #     default_config = Config.default_config
        #     color_array = default_config.get(int(level), [])
        #     for ca in color_array:
        #         for c in ca:
        #             if c not in random_dict:
        #                 random_dict[c] = 1
        #             else:
        #                 random_dict[c] += 1
        # else:
        color_array, random_list = random_color_array(int(level), int(color_num))

        for rl in random_list:
            random_dict[rl] = 0

        for ca in color_array:
            for c in ca:
                random_dict[c] += 1

        payload = {
            "uuid": user_uuid,
            "exp": datetime.datetime.utcnow()
        }
        tuuid = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        double = 1 if lastest_sign_date != today else 0
        extra_sign = 0 if extra else 1

        data = {"uuid": to_str(tuuid),
                "openid": open_id,
                "level": level,
                "current_score": current_score,
                "target_score": target_score,
                "color_num": color_num,
                "direct": direct,               # 是否可以看视频通关
                "color_array": color_array,
                "verified": verified,
                "continuous_sign_days": continuous_sign_days,
                "today_sign_status": today_sign_status,
                "signboard": signboard,          # 1显示,0不显示
                "coins": coins,
                "tools": tools,
                "restart": restart,
                "random_dict": random_dict,
                "loto_num": loto_num,
                "lotoboard": lotoboard,
                "double_sign": double,
                "extra_sign": extra_sign,
                "history_score": history_score,
                "robot": robot_user,
                "new_user": new_user,                   # 是否为新用户
                "unionid": unionId,                     # unionid
                }
        self.write_json(data, msg="success")


@route('/verify')
class PersonalInfoHandler(RedisHandler):
    @authenticated_async
    async def post(self):
        name = self.get_argument("name", "")
        avatar = self.get_argument("avatar", "")
        # print(chardet.detect(str.encode(name)))

        # req_data = to_str(self.request.body).split("&")
        # name = req_data.get("name", "")
        # avatar = req_data.get("avatar", "")
        # print("name", name, type(name))

        if not name and not avatar:
            return self.write_json(status=-1, msg="参数错误")

        uuid = self.current_user.uuid
        user = await self.application.objects.get(User, uuid=uuid)
        user.name = name
        user.avatar = avatar
        await self.application.objects.update(user)

        user_info_session_key = "sx_info:" + uuid
        self.redis_spare.hset(user_info_session_key, "name", name)
        self.redis_spare.hset("user_avatar", name, avatar)

        self.write_json(msg="success")


@route('/unionId')
class UnionIdHandler(RedisHandler):
    @authenticated_async
    async def post(self):
        encryptedData = self.get_argument("encryptedData", "")
        iv = self.get_argument("iv", "")
        uuid = self.current_user.uuid
        user_info_session_key = "sx_info:" + uuid
        union_id = to_str(self.redis_spare.hget(user_info_session_key, "union_id"))
        if not union_id:
            if encryptedData and iv:
                open_id = to_str(self.redis_spare.hget(user_info_session_key, "openid"))
                session_dict = self.get_session(open_id)
                session_key = session_dict[0].get("session_key", "")
                print("session_key", session_key)
                pc = WXBizDataCrypt(APPID, session_key)
                WX_data = pc.decrypt(encryptedData, iv)
                union_id = WX_data.get("unionId", "")
                self.redis_spare.hset(user_info_session_key, "uniond_id", union_id)
            else:
                return self.write_json(status=-1, msg="上报信息有误，请核对")
        data = {"unionId": union_id}
        self.write_json(data)













