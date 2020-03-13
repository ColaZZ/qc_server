import functools
import jwt

from lib.constant import SECRET_KEY, JWT_EXPIRE
from apps.models.user import User


# 登陆态装饰器
def authenticated_async(method):
    @functools.wraps(method)
    async def wrapper(self, *args, **kwargs):
        tuuid = self.request.headers.get("uuid", None)
        # print(tuuid)
        if tuuid:
            try:
                tuuid = tuuid.encode("utf-8")
                try:
                    send_data = jwt.decode(tuuid, SECRET_KEY, leeway=JWT_EXPIRE, options={"verify_exp": True})
                    user_uuid = send_data.get("uuid")
                    # 从数据库中获取到user并赋值给_current_user
                    try:
                        user = await self.application.objects.get(User, uuid=user_uuid)
                        self._current_user = user

                        # 关键
                        await method(self, *args, **kwargs)
                    except User.DoesNotExist as e:
                        # print(33333)
                        self.set_status(401)
                except Exception as e:
                    print(e)
                    # print(444444)
                    self.set_status(401)
            except jwt.ExpiredSignature as e:
                print(e)
                # print(555555)
                self.set_status(401)
        else:
            self.set_status(401)
    return wrapper


def encode_tuuid(tuuid):
    tuuid = tuuid.encode("utf-8")
    send_data = jwt.decode(tuuid, SECRET_KEY, leeway=JWT_EXPIRE, options={"verify_exp": True})
    user_uuid = send_data.get("uuid")
    return user_uuid