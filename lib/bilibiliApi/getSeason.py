import re
import json
from lib import util
import lib.util.types as types
from . import getPage
from . import playUrl
from lib.util import session
import typing as t


def get(video: str, cookie: str):
    logger = util.getLogger("AnalyzingPageSeasonInfo")
    html = getPage.get(video, cookie)

    def findSeasonId(d: t.Any) -> int | None:
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
        ressult = types.VideoPartResults(title="root", li=[])
        mainPart = types.VideoPartResults(
            title=util.optionalChain(
                data, "main_section", "title", default="Main Section"
            ),
            li=[
                types.VideoPart(
                    title=f"{data['main_section']['title']} - "
                    + (i["long_title"] or i["title"]),
                    playinfo=util.toCallback(
                        playUrl.get,
                        avid=i["aid"],
                        cid=i["cid"],
                        cookie=cookie,
                    ),
                )
                for i in util.optionalChain(
                    data, "main_section", "episodes", default=[]
                )
            ],
        )
        ressult.li.append(mainPart)
        sectionPart = types.VideoPartResults(title="Other", li=[])
        for i in util.optionalChain(data, "section", default=[]):
            now = types.VideoPartResults(
                title=util.optionalChain(i, "title", default="Section"), li=[]
            )
            sectionPart.li.append(now)
            for j in util.optionalChain(i, "episodes", default=[]):
                now.li.append(
                    types.VideoPart(
                        title=(j["long_title"] or j["title"]),
                        playinfo=util.toCallback(
                            playUrl.get,
                            avid=j["aid"],
                            cid=j["cid"],
                            cookie=cookie,
                        ),
                    )
                )
        return ressult
    except Exception:
        return None
