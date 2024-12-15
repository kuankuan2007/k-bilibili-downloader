from typing import *
import re
import json
import lib.util as util
import lib.types as types
from . import getPage
from . import playUrl
from lib.util import session


def get(video: str, cookie: str) -> list[types.VideoPart]:
    logger = util.getLogger("AnalyzingPageSeasonInfo")
    html = getPage.get(video, cookie)

    def findSeasonId(d: dict | list) -> int | None:
        for i in d if isinstance(d, dict) else range(len(d)):
            if i == "season_id" and type(d[i]) == int:
                return d[i]
            elif type(d[i]) == dict or type(d[i]) == list:
                r = findSeasonId(d[i])
                if r:
                    return r

    try:
        logger.info("start parse page")
        seasonId: int | None = None
        for i in [
            re.compile(r"window.__INITIAL_STATE__\s*=\s*(\{.*?\});", re.S),
        ]:
            try:
                seasonId = findSeasonId(json.loads(re.findall(i, html)[0]))
                assert seasonId
            except Exception as e:
                print(e)
                continue
            else:
                break

        if not seasonId:
            logger.info("Can't find season_id")
            raise Exception("Can't find season_id")
        res = session.get(
            "https://api.bilibili.com/pgc/web/season/section",
            params={
                "season_id": seasonId,
            },
            headers=util.getHeader(
                cookie,
                util.getPageUrl(video),
                Accept="application/json, text/plain, */*",
            ),
        )
        res.raise_for_status()
        data = res.json()["result"]
        res = [
            types.VideoPart(
                title=f"{data['main_section']['title']} - " + (i["long_title"] or i["title"]),
                playinfo=util.toCallback(
                    playUrl.get,
                    avid=i["aid"],
                    cid=i["cid"],
                    cookie=cookie,
                ),
            )
            for i in util.optionalChain(data, "main_section", "episodes", default=[])
        ]
        for i in util.optionalChain(data, "section", default=[]):
            for j in util.optionalChain(i, "episodes", default=[]):
                res.append(
                    types.VideoPart(
                        title=f"{i['title']} - " + (j["long_title"] or j["title"]),
                        playinfo=util.toCallback(
                            playUrl.get,
                            avid=j["aid"],
                            cid=j["cid"],
                            cookie=cookie,
                        ),
                    )
                )
        return res
    except Exception:
        return []
