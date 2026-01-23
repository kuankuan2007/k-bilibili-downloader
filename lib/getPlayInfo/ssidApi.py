from typing import *
from lib.util import session
import re
from lib.util import (
    playUrl,
    types,
    getHeader,
    toCallback,
    optionalChain,
    getLogger,
    errorLogInfo,
    getPageUrl,
)


def get(video: str, cookie: str):
    logger = getLogger("AnalyzingEpApi")
    try:

        ssid = (re.findall(r"ss([1-9][0-9]*)", video, re.I) or [None])[0]

        if ssid is None:
            logger.info("No ssid found")
            return []
        return getFromSsid(str(ssid), cookie)
    except Exception as e:
        logger.warning(f"Can't get page list with error {errorLogInfo(e)}")
        return []


def getFromSsid(ssid: str, cookie: str):
    res = session.get(
        "https://api.bilibili.com/pgc/web/season/section",
        params={
            "season_id": ssid,
        },
        headers=getHeader(
            cookie,
            getPageUrl(f"ss{ssid}"),
            Accept="application/json, text/plain, */*",
        ),
    )
    res.raise_for_status()
    data = res.json()["result"]
    res = [
        types.VideoPart(
            title=f"{data['main_section']['title']} - "
            + (i["long_title"] or i["title"]),
            playinfo=toCallback(
                playUrl.get,
                avid=i["aid"],
                cid=i["cid"],
                cookie=cookie,
            ),
        )
        for i in optionalChain(data, "main_section", "episodes", default=[])
    ]
    for i in optionalChain(data, "section", default=[]):
        for j in optionalChain(i, "episodes", default=[]):
            res.append(
                types.VideoPart(
                    title=f"{i['title']} - " + (j["long_title"] or j["title"]),
                    playinfo=toCallback(
                        playUrl.get,
                        avid=j["aid"],
                        cid=j["cid"],
                        cookie=cookie,
                    ),
                )
            )
    return res
