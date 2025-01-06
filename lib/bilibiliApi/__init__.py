from . import avOrBvApi, epApi, getSeason, pageRawPlayinfo
from lib import util
from lib.util import types
import typing as t


li = [avOrBvApi, epApi, getSeason, pageRawPlayinfo]


def analyzeUrl(video: str, cookie: str):
    logger = util.getLogger("Analyze new video")

    logger.info(f"video: {video}, cookie: {cookie}")

    if not (video and cookie):
        logger.info("Incomplete information, return")
        raise util.TipableException("Incomplete information", "请填写完整信息")
    results: types.VideoPartResults
    for i in li:
        res: types.VideoPartResults | None = i.get(video, cookie)
        if res is None:
            logger.info("Play list not found")
            continue
        results = res
        break
    if not results:
        raise util.TipableException("Play list not found", "未找到可下载的视频")
    return results
