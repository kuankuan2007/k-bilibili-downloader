import requests as _requests
import requests.adapters as _adapters
from lib.util import config

session = _requests.Session()


class _GlobalHttpAdapter(_adapters.HTTPAdapter):

    def send(
        self,
        request,
        stream=False,
        timeout=None,
        verify=True,
        cert=None,
        proxies=None,
    ):
        return super().send(
            request, stream, timeout or (config.timeout, None), verify, cert, proxies
        )


globalHttpAdapter = _GlobalHttpAdapter(max_retries=3)


def _resErrorHook(res: _requests.Response, *_args, **_kwargs):
    try:
        res.raise_for_status()
    except Exception as e:
        raise Exception(f"Request Error: {res.status_code}") from e


session.hooks["response"] = [_resErrorHook]


session.mount("http://", globalHttpAdapter)
session.mount("https://", globalHttpAdapter)
