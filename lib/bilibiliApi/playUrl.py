from lib.util import session
from lib import util


def get(
    cookie: str,
    avid: str | None = None,
    bvid: str | None = None,
    cid: str | None = None,
) -> dict:
    logger = util.getLogger("getPlayInfo")
    try:
        return session.get(
            "https://api.bilibili.com/x/player/wbi/playurl",
            params={
                "avid": avid,
                "bvid": bvid,
                "cid": cid,
                "fnval": "4048",
            },
            headers=util.getHeader(cookie),
        ).json()["data"]
    except Exception as e:
        logger.error(e)
        util.dialog.showerror(
            "错误",
            f"请求错误，无法获取播放信息\n{util.errorLogInfo(e)}",
        )
        raise
