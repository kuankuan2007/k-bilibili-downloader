from typing import *
from lib.util import session
import re
import lib.util as util
import lib.types as types
from . import playUrl


def get(video: str, cookie: str):
    logger = util.getLogger("AnalyzingBvOrAvApi")
    try:
        info = {
            "aid": (re.findall(r"av([1-9][0-9]*)", video, re.I) or [None])[0],
            "bvid": (re.findall(r"BV[0-9a-zA-Z]{10}", video, re.I) or [None])[0],
        }
        if not info["aid"] and not info["bvid"]:
            logger.info("No av or bv found")
            return []
        pagelist = session.get(
            "https://api.bilibili.com/x/player/pagelist",
            params=info,
            headers=util.getHeader(cookie),
        ).json()["data"]
        assert pagelist and type(pagelist) == list, "Can't get page list"
        logger.info(f"Got {len(pagelist)} pages")
        return [
            types.VideoPart(
                title=i["part"],
                playinfo=util.toCallback(
                    playUrl.get, cookie=cookie, avid=info["aid"], bvid=info["bvid"], cid=i["cid"]
                ),
            )
            for i in pagelist
        ]
    except Exception as e:
        logger.warning(f"Can't get page list with error {util.errorLogInfo(e)}")
        return []
