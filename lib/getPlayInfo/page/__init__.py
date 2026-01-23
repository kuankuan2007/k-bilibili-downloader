from . import initialState, playurlSSRData, windowPlayinfo

from lib.util import getPage, types, getLogger

li = [initialState, playurlSSRData, windowPlayinfo]


def get(video: str, cookie: str) -> list[types.VideoPart]:
    html = getPage.get(video, cookie)
    logger = getLogger("AnalyzingHTML")

    for i in li:
        try:
            res = i.get(html, cookie)
            if res and len(res) > 0:
                logger.info(f"get video parts from {i.__name__}")
                return res
        except Exception as e:
            logger.error(e)
            continue
    raise Exception("Can't find video parts from all methods by html")
