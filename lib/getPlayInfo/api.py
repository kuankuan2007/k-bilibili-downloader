from typing import *
import requests
import re
import lib.util as util


def getPlayInfo(video: dict, cookie: str):
    return requests.get(
        "https://api.bilibili.com/x/player/wbi/playurl",
        params={
            "avid": video["aid"],
            "bvid": video["bvid"],
            "cid": video["cid"],
            "fnval": "4048",
        },
        headers=util.getHeader(cookie),
    ).json()["data"]


def get(video: str, cookie: str):
    logger = util.getLogger("AnalyzingBvOrAvApi")
    try:
        info = {
            "aid": (re.findall(r"av([1-9][0-9]*)", video, re.I) or [None])[0],
            "bvid": (re.findall(r"BV[0-9a-zA-Z]{10}", video, re.I) or [None])[0],
        }
        if not info["aid"] and not info["bvid"]:
            logger.warning("No av or bv found")
            return []
        pagelist = requests.get(
            "https://api.bilibili.com/x/player/pagelist",
            params=info,
            headers=util.getHeader(cookie),
        ).json()["data"]
        assert pagelist and type(pagelist) == list, "Can't get page list"
        logger.info(f"Got {len(pagelist)} pages")
        return [
            {
                "title": i["part"],
                "playinfo": util.toCallback(
                    getPlayInfo, {**info, "cid": i["cid"]}, cookie
                ),
            }
            for i in pagelist
        ]
    except Exception as e:
        logger.warning(f"Can't get page list with error {util.errorLogInfo(e)}")
        return []

