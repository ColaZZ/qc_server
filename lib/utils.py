#!/usr/bin/python3
# -*- coding: utf-8 -*-


def login_required(f):
    def _wrapper(self, *args, **kwargs):
        print(self.get_current_user)
        logged = self.get_current_user()
        if logged is None:
            # 无session，返回登录 etc
            self.write('no login')
            self.finish()
        else:
            ret = f(self, *args, **kwargs)
    return _wrapper()
