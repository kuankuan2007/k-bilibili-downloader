from typing import *
from lib.util import session
import lib.util as util

cache = {}


def get(video: str, cookie: str) -> str:
    logger = util.getLogger("download page")
    url = util.getPageUrl(video)
    headers = util.getHeader(cookie, url)
    if url in cache:
        logger.info(f"get page from cache: {url}")
        return cache[url]
    try:
        logger.info(f"request page url: {url}, headers: {headers}")
        response = session.get(url, headers=headers)
        logger.info(f"response status code: {response.status_code}")
        assert response.status_code // 100 == 2
        html = response.text
    except Exception as e:
        logger.warning(f"Can't get page response with error {util.errorLogInfo(e)}")
        util.dialog.showerror(
            "错误",
            f"请求错误，无法获取页面信息\n{util.errorLogInfo(e)}",
        )
        return

    cache[url] = html
    return html
