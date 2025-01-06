from lib.util import session
import re
import lib.util as util
import lib.util.types as types
from . import playUrl


def get(video: str, cookie: str):
    logger = util.getLogger("AnalyzingEpApi")
    try:

        epID = (re.findall(r"ep([1-9][0-9]*)", video, re.I) or [None])[0]

        if epID is None:
            logger.info("No ep id found")
            raise ValueError("No ep id found")

        epData = session.get(
            "https://api.bilibili.com/pgc/view/web/ep/list",
            params={"ep_id": epID},
            headers=util.getHeader(cookie),
        ).json()["result"]

        res = types.VideoPartResults(title="root", li=[])
        res.li.append(
            types.VideoPartResults(
                title=util.optionalChain(epData, "title", default="Season"),
                li=[
                    types.VideoPart(
                        title=i["title"],
                        playinfo=util.toCallback(
                            playUrl.get,
                            cookie=cookie,
                            avid=i["aid"],
                            bvid=i["bvid"],
                            cid=i["cid"],
                        ),
                    )
                    for i in util.optionalChain(epData, "episodes", default=[])
                ],
            )
        )
        sectionPart = types.VideoPartResults(title="section", li=[])
        res.li.append(sectionPart)

        for i in util.optionalChain(epData, "section", default=[]):
            now = types.VideoPartResults(title=i["title"], li=[])
            sectionPart.li.append(now)
            for j in util.optionalChain(epData, "episodes", default=[]):
                now.li.append(
                    types.VideoPart(
                        title=j["title"],
                        playinfo=util.toCallback(
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
        logger.warning(f"Can't get page list with error {util.errorLogInfo(e)}")
        return None
