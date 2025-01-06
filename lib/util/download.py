import autoDownload
import threading
import asyncio
import typing as t
from lib import util
from lib.util import types


class DownloadManagerTread(threading.Thread):
    loop: asyncio.AbstractEventLoop
    __waitingList: t.List[
        t.Tuple[autoDownload.download.TaskResult, types.DownloadTaskCallback]
    ]

    def __init__(self):
        super().__init__(name="DownloadManager", daemon=True)
        self.loop = asyncio.get_event_loop()

    def waitAsync(
        self,
        taskResult: autoDownload.download.TaskResult,
        cb: types.DownloadTaskCallback,
    ):
        self.__waitingList.append((taskResult, cb))

    def request(
        self,
        task: types.DownloadTask,
    ):
        self.waitAsync(
            autoDownload.rawRequest(
                autoDownload.TaskConfig(
                    task.url,
                    task.file,
                    headers=util.getHeader(task.cookie, task.referer),
                )
            ),
            task.cb,
        )

    async def eventHandler(self):
        while True:
            await asyncio.sleep(1)
            for i in self.__waitingList.copy():
                if i[0].event.is_set():
                    self.__waitingList.remove(i)
                    i[1](i[0].ok, i[0].err)

    def run(self):
        self.loop.run_forever()

    async def submitRequests(
        self,
        aGen: t.AsyncGenerator[types.DownloadTask],
    ):
        async for i in aGen:
            self.request(i)


_dmTread = DownloadManagerTread()
_dmTread.start()


def submit(tasks: t.AsyncGenerator[types.DownloadTask]):
    _r = _dmTread.submitRequests(tasks)
