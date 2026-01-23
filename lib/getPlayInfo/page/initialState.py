from typing import *
import re
import json
import lib.util as util
from lib.util import session, playUrl, types, getLogger, toCallback
from lib.getPlayInfo.ssidApi import getFromSsid

def get(html: str, cookie: str) -> list[types.VideoPart]:
    logger = getLogger("AnalyzingPageInitialState")

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
        return getFromSsid(str(seasonId), cookie)
    except Exception:
        return []
