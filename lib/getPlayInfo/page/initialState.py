import re
import json
from lib.util import types, getLogger
from lib.getPlayInfo.ssidApi import getFromSsid

def get(html: str, cookie: str) -> list[types.VideoPart]:
    logger = getLogger("AnalyzingPageInitialState")
    

    def findSeasonId(d: dict | list) -> int | None:
        record=set[int]()
        queue = [d]
        while queue:
            d = queue.pop(0)
            if id(d) in record:
                continue
            record.add(id(d))
            if isinstance(d, dict):
                for i in d:
                    if i == "season_id" and type(d[i]) == int:
                        return d[i]
                    elif type(d[i]) == dict or type(d[i]) == list:
                        queue.append(d[i])
            elif isinstance(d, list):
                for i in d:
                    if type(i) == dict or type(i) == list:
                        queue.append(i)
        return None
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
