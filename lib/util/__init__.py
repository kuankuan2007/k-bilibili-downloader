import typing as t
import logging
import re
import pathlib
import sys
import os
import tempfile
import time
from lib.util.argparser import config
import subprocess
import tkinter as tk
import traceback
from lib.util.request import session

rootWindow = tk.Tk()

from lib.ui import dialog





logMap = {
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


def toCallback(func: t.Callable, *args, **kwargs) -> t.Callable:
    """
    Converts a function to a callback format.

    Args:
        func (Callable): The function to be converted.
        *args: Positional arguments to be passed to the function.
        **kwargs: Keyword arguments to be passed to the function.

    Returns:
        Callable: A callback function that calls the original function with the provided arguments.
    """
    return lambda *args_callback, **kwargs_callback: func(
        *args, *args_callback, **kwargs, **kwargs_callback
    )


def getLogger(name: str):
    return logging.getLogger(name)


def optionalChain(d: dict | list, *keys: t.Any, default: t.Any = None) -> t.Any:
    """
    Chains together a series of keys in a dictionary to retrieve a value.

    Args:
        d (dict): The dictionary to search.
        *keys (str): The keys to chain together.
        default (Any, optional): The default value to return if the key chain is invalid. Defaults to None.

    Returns:
        Any: The value associated with the key chain, or the default value if the key chain is invalid.
    """
    for key in keys:
        if key in d:
            d = d[key]
        else:
            return default
    return d


def getHeader(cookie: str | None = None, referer: str | None = None, **kwargs) -> dict:
    return {
        "Referer": referer,
        "Cookie": cookie,
        "Accept": "*/*",
        "Accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Sec-Ch-Ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        **kwargs,
    }


def getPageUrl(vid: str):
    if re.match(
        r"^(((ht|f)tps?):\/\/)?([^!@#$%^&*?.\s-]([^!@#$%^&*?.\s]{0,63}[^!@#$%^&*?.\s])?\.)+[a-z]{2,6}\/?",
        vid,
    ):
        return vid
    if re.match(
        re.compile("av[1-9][0-9]*", re.I),
        vid,
    ) or re.match("(?:B|b)(?:v|V)[0-9a-zA-Z]{10}", vid):
        return f"https://www.bilibili.com/video/{vid}?spm_id_from=player_end_recommend_autoplay"
    elif re.match(
        re.compile("(?:ep|ss)[1-9][0-9]*", re.I),
        vid,
    ):
        return f"https://www.bilibili.com/bangumi/play/{vid}"
    elif re.match(
        re.compile("md[1-9][0-9]*", re.I),
        vid,
    ):
        return f"https://www.bilibili.com/bangumi/media/{vid}"
    rootLogger.warning(f"Unknown video id: {vid}")
    raise ValueError("unknown video id")


if getattr(sys, "frozen", None):
    dataBasePath = pathlib.Path(sys._MEIPASS)  # type: ignore
else:
    dataBasePath = pathlib.Path(os.getcwd()).joinpath("data")


def dataPath(filename: str | pathlib.Path):
    if isinstance(filename, str):
        filename = pathlib.Path(filename)
    return dataBasePath.joinpath(filename)


def errorLogInfo(e: BaseException, showTraceback: bool = False):

    return (
        e.tip if isinstance(e, TipableException) else f"{e.__class__.__name__}:{str(e)}"
    ) + (
        f"\n{'\n'.join(traceback.format_exception(None, e, e.__traceback__))}"
        if showTraceback
        else ""
    )


def testFfmpeg(path: str):
    try:
        subprocess.call(
            [path, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        return False
    return True


class TipableException(Exception):
    tip: str

    def __init__(self, message: str, tipForUser: str):
        super().__init__(message)
        self.tip = tipForUser


tempRoot = pathlib.Path(tempfile.gettempdir()).joinpath(
    f"k-bilibili-download-{time.time()}"
)
if not tempRoot.exists():
    os.mkdir(tempRoot)

fileLogHandler = logging.FileHandler(
    filename=str(tempRoot.joinpath("log.txt")),
    mode="w",
    encoding="utf-8",
)
fmter = logging.Formatter(
    fmt="[%(asctime)s] [%(name)s] [t-%(thread)d] [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

consoleLogHandler = logging.StreamHandler()

rootLogger = logging.getLogger()

rootLogger.addHandler(fileLogHandler)
rootLogger.addHandler(consoleLogHandler)
rootLogger.setLevel(logging.DEBUG)

fileLogHandler.setLevel(logMap[config.log_level])
fileLogHandler.setFormatter(fmter)
consoleLogHandler.setLevel(logMap[config.log_level])
consoleLogHandler.setFormatter(fmter)


__all__ = [
    "toCallback",
    "dialog",
    "getLogger",
    "optionalChain",
    "getHeader",
    "getPageUrl",
    "dataPath",
    "testFfmpeg",
    "session",
]
