from apps.found_handler_v2 import RedisHandler
from lib.routes import route
from apps.models.config import Config


@route('/config/tool')
class ConfigToolHandler(RedisHandler):
    async def get(self):
        data = Config.tool_config
        self.write_json(data)


@route('/config/sign')
class ConfigSignHandler(RedisHandler):
    async def get(self):
        data = {
            "sign_config": Config.sign_config,
            "sign_award_config": Config.sign_award_config
        }
        self.write_json(data)


@route('/config/source')
class ConfigSourceHandler(RedisHandler):
    async def get(self):
        data = Config.source_config
        self.write_json(data)


@route('/config/challenge')
class ConfigChallengeHandler(RedisHandler):
    async def get(self):
        data = Config.challenge_config
        self.write_json(data)


