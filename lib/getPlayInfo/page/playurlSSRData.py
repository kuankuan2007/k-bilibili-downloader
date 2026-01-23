from typing import *
import re
import json
import lib.util as util
from lib.util import session, playUrl, types, getLogger, toCallback

pattern = re.compile(r"^(\s*)const playurlSSRData\s*=\s*{\s*$", re.S)


def get(html: str, cookie: str) -> list[types.VideoPart]:
    logger = getLogger("AnalyzingPlayurlSSRData")
    lines=html.splitlines()
    try:
        logger.info("start parse page")
        for index,line in enumerate(lines):
            res=pattern.match(line)
            if res:
                logger.info(f"find playurlSSRData at line {index}")
                break
        else:
            logger.info("Can't find playurlSSRData")
            raise Exception("Can't find playurlSSRData")
        print(index,line)
    except Exception as e:
        logger.error(f"parse page error:{e}")
    return []