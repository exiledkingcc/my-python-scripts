#!/usr/bin/env python3

import sys
import logging


FORMAT = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"

NOTSET = logging.NOTSET
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


class Logger:
    def __init__(self, name=None):
        self._logger = logging.getLogger(name)

    def _msg(self, *args):
        msg = " {}" * len(args)
        return msg[1:].format(*args)

    def d(self, *args):
        self._logger.debug(self._msg(*args))

    def i(self, *args):
        self._logger.info(self._msg(*args))

    def w(self, *args):
        self._logger.warning(self._msg(*args))

    def e(self, *args):
        self._logger.error(self._msg(*args))

    def c(self, *args):
        self._logger.critical(self._msg(*args))


class Formatter(logging.Formatter):
    COLORS = {
        DEBUG: "\x1b[37m",
        INFO: "\x1b[32m",
        WARNING: "\x1b[33m",
        ERROR: "\x1b[31m",
        CRITICAL: "\x1b[35m",
        "default": "\x1b[0m"
    }

    def __int__(self, fmt=None):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):
        result = logging.Formatter.format(self, record)
        nocolor = Formatter.COLORS["default"]
        color = Formatter.COLORS.get(record.levelno, nocolor)
        return color + result + nocolor


def init(**kwargs):
    stream = kwargs.pop("stream", sys.stderr)
    fmt = kwargs.pop("format", FORMAT)
    level = kwargs.pop("level", DEBUG)

    if len(kwargs) > 0:
        k, _ = kwargs.popitem()
        raise TypeError("invalid keyword argument '{}'".format(k))

    handler = logging.StreamHandler(stream)
    formatter = Formatter(fmt)
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)
    logging.root.setLevel(level)


if __name__ == '__main__':
    init()
    log = Logger(__name__)
    log.d("debug")
    log.i("info")
    log.w("warning")
    log.e("error")
    log.c("critical")
