
from lib import util

res = util.session.get(
    "https://api.bilibili.com/pgc/view/web/ep/list?ep_id=742228",
    headers=util.getHeader(
        """buvid4=6DD896D7-CA92-7327-A9FC-7DD7E3BE2A7427402-022123002-e9CMmr5ancbgIJz1JLYvRA%3D%3D; DedeUserID=662698080; DedeUserID__ckMd5=7783e3885aa270e3; buvid_fp_plain=undefined; enable_web_push=DISABLE; PVID=1; _uuid=54479210F-CE95-2272-26A5-488F8E1AF87898376infoc; buvid3=A1ED7419-6413-5E6C-ABE1-047EFAA6C9D539788infoc; b_nut=1713339439; FEED_LIVE_VERSION=V_WATCHLATER_PIP_WINDOW3; header_theme_version=CLOSE; rpdid=|(ku|kYJJk~k0J'u~uR~lRJkk; fingerprint=7b48c978fd2b5b9eb7f025c320cc6e6b; buvid_fp=7b48c978fd2b5b9eb7f025c320cc6e6b; CURRENT_QUALITY=32; home_feed_column=5; browser_resolution=2552-1322; SESSDATA=8f0b6a1c%2C1749668795%2Cfa0f5%2Ac2CjDhhJMDhCYUYBLr-T4TRjVzuiGnBimLR4Bw2-iHJImWjiBOApbYLhnVkGdPS7aHp4oSVnhpNlcwVGFDelExVGtMQUVGUHlQS1hQa2xnb1VTVFhFUUZHSGhOZTU5V3JJQjZCREdnbWlFRnBLd29oMTBhdlpKTjdkZnhaUnZ4U1cwMXpHbFhpSzRnIIEC; bili_jct=97a9a4b2f10647902ab64d9031957123; bsource_origin=bing_ogv; bsource=bing_ogv; sid=6dbm7mgo; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzQ1MTg3MTcsImlhdCI6MTczNDI1OTQ1NywicGx0IjotMX0.ivZgYmaZ8eDYEAP-X9ur1IoDIu_6KdYC536E98L8oVM; bili_ticket_expires=1734518657; CURRENT_FNVAL=4048; bp_t_offset_662698080=1011169682415157248; b_lsid=E2296227_193CACD0639"""
    ),
)

print(res)
