import redis
from tornado.web import RequestHandler

from lib.constant import SESSION_REDIS_EXPIRES


class RedisHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    @property
    def redis(self):
        return self.application.redis

    @property
    def redis_spare(self):
        return self.application.redis_spare

    def write_json(self, data=None, status=0, msg="", need_format=True):
        if data is None:
            data = {}
        if need_format:
            response = {
                "status": status,
                "message": msg,
                "data": data
            }
        else:
            response = data

        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.set_header("Access-Control-Allow-Origin", "*")     # 允许跨域请求
        self.set_header("Sever", "test")
        self.write(response)


    # sx:open_id 缓存
    def save_user_session(self, user_uuid, open_id, session_key):
        user_session_value = {
            'uuid': user_uuid,
            'session_key': session_key
        }
        user_session_key = 'sx:' + open_id
        with self.redis_spare.pipeline(transaction=False) as pipe:
            pipe.hmset(user_session_key, user_session_value)
            pipe.expire(user_session_key, SESSION_REDIS_EXPIRES)
            pipe.execute()

    def get_session(self, open_id):
        user_session_key = 'sx:' + open_id
        with self.redis_spare.pipeline(transaction=False) as pipe:
            pipe.hgetall(user_session_key)
            data = pipe.execute()
        return data

    # sx_info:uuid 缓存
    def save_user_info_session(self, user_uuid, openid, level, current_score, target_score, color_num, verified, tools, coins, direct, history_score):
        user_info_session_value = {
            "openid": openid,
            "level": level,
            "current_score": current_score,
            "target_score": target_score,
            "color_num": color_num,
            "verified": verified,
            "tools": tools,
            "coins": coins,
            "direct": direct,
            "history_score": history_score
        }
        user_info_session_key = "sx_info:" + user_uuid
        # print(user_info_session_value)
        with self.redis_spare.pipeline(transaction=False) as pipe:
            pipe.hmset(user_info_session_key, user_info_session_value)
            pipe.expire(user_info_session_key, SESSION_REDIS_EXPIRES)
            pipe.execute()

    def get_user_info_session(self, uuid):
        user_key = "sx_info:" + uuid
        return self.redis_spare.hgetall(user_key)
