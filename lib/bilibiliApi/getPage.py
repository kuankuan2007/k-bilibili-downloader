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
        raise util.TipableException(
            "Request Error", f"无法获取页面信息: {util.errorLogInfo(e)}"
        )

    cache[url] = html
    return html
