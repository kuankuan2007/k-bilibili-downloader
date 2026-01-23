from typing import *
import re
import json
from lib.util import types, getLogger, optionalChain, errorLogInfo


def get(html: str, cookie: str) -> list[types.VideoPart]:
    logger = getLogger("AnalyzingPageWindowPlayinfo")
    try:
        logger.info("start parse page")
        flag = False
        for i, maper in [
            (
                re.compile(r"window.__playinfo__=(.*?)</script>", re.S),
                lambda x: x["data"],
            ),
            (
                re.compile(
                    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                    re.S,
                ),
                lambda x: [
                    i["state"]["data"]["result"]["video_info"]
                    for i in x["props"]["pageProps"]["dehydratedState"]["queries"]
                    if optionalChain(i, "state", "data", "result", "video_info")
                ][0],
            ),
        ]:
            try:
                palyInfo = maper(json.loads(re.findall(i, html)[0]))
            except Exception:
                continue
            else:
                flag = True
                break

        if not flag:
            logger.warning("Can't find playinfo in page")
            raise Exception("Can't find playinfo in page")
        return [
            types.VideoPart(
                title=optionalChain(
                    re.findall(r"<title.*>(.*)</title>", html), 0, default="Unknown"
                ),
                playinfo=lambda: palyInfo,
            )
        ]
    except Exception as e:
        logger.warning(f"Can't parse page with error {errorLogInfo(e)}, return")
    return []
