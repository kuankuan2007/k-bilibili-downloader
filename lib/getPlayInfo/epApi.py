from typing import *
from lib.util import session
import re
from lib.util import playUrl, types, getHeader, toCallback, optionalChain, getLogger,errorLogInfo


def get(video: str, cookie: str):
    logger = getLogger("AnalyzingEpApi")
    try:

        epID = (re.findall(r"ep([1-9][0-9]*)", video, re.I) or [None])[0]

        if epID is None:
            logger.info("No ep id found")
            return []

        epData = session.get(
            "https://api.bilibili.com/pgc/view/web/ep/list",
            params={"ep_id": epID},
            headers=getHeader(cookie),
        ).json()["result"]

        res = [
            types.VideoPart(
                title=i["title"],
                playinfo=toCallback(
                    playUrl.get,
                    cookie=cookie,
                    avid=i["aid"],
                    bvid=i["bvid"],
                    cid=i["cid"],
                ),
            )
            for i in optionalChain(epData, "episodes", default=[])
        ]
        for i in optionalChain(epData, "section", default=[]):
            for j in optionalChain(epData, "episodes", default=[]):
                res.append(
                    types.VideoPart(
                        title=i["title"] + " - " + j["title"],
                        playinfo=toCallback(
                            playUrl.get,
                            cookie=cookie,
                            avid=j["aid"],
                            bvid=j["bvid"],
                            cid=j["cid"],
                        ),
                    )
                )

        return res

    except Exception as e:
        logger.warning(f"Can't get page list with error {errorLogInfo(e)}")
        return []
