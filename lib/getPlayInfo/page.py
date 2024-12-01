from typing import *
import requests
import re
import json
import lib.util as util


def get(video: str, cookie: str):
    logger = util.getLogger("AnalyzingPage")
    url = util.getPageUrl(video)
    headers = util.getHeader(cookie, url)
    try:
        logger.info(f"request page url: {url}, headers: {headers}")
        response = requests.get(url, headers=headers, timeout=util.timeout)
        logger.info(f"response status code: {response.status_code}")
        assert response.status_code // 100 == 2
        html = response.text
    except Exception as e:
        logger.warning(f"Can't get page response with error {util.errorLogInfo(e)}")
        util.messagebox.showerror(
            "错误",
            f"请求错误，无法获取页面信息\n{util.errorLogInfo(e)}",
        )
        return
    try:
        logger.info("start parse page")
        flag = False
        with open("a.html", "w", encoding="utf-8") as f:
            f.write(html)
        for i, maper in [
            (
                re.compile(r"window.__playinfo__=(.*?)</script>", re.S),
                lambda x: x["data"],
            ),
            (
                re.compile(
                    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                    re.S,
                ),
                lambda x: [
                    i["state"]["data"]["result"]["video_info"]
                    for i in x["props"]["pageProps"]["dehydratedState"]["queries"]
                    if util.optionalChain(i, "state", "data", "result", "video_info")
                ][0],
            ),
        ]:
            try:
                palyInfo = maper(json.loads(re.findall(i, html)[0]))
            except Exception:
                continue
            else:
                flag = True
                break

        if not flag:
            logger.warning("Can't find playinfo in page")
            raise Exception("Can't find playinfo in page")
        return [
            {
                "title": util.optionalChain(
                    re.findall(r"<title.*>(.*)</title>", html), 0, default="Unknown"
                ),
                "playinfo": lambda: palyInfo,
            }
        ]
    except Exception as e:
        logger.warning(f"Can't parse page with error {util.errorLogInfo(e)}, return")
        util.messagebox.showerror("错误", "解析错误，无法获取视频信息")
        return
