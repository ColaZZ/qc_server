#!/usr/bin/python3
# -*- coding: utf-8 -*-

import tornado.web


class route(object):
    _routes = []

    def __init__(self, uri, name=None):
        self._uri = uri
        self.name = name

    def __call__(self, _handler):
        """gets called when our class decorate"""
        name = self.name and self.name or _handler.__name__
        self._routes.append(tornado.web.url(self._uri, _handler, name=name))
        return _handler

    @classmethod
    def get_routes(cls):
        cls._routes.append(tornado.web.URLSpec(r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "/static"}))
        return cls._routes


def route_redirect(from_, to, name=None):
    route._routes.append(tornado.web.url(from_, tornado.web.RedirectHandler, dict(url=to), name=name))