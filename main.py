import tkinter as tk
from tkinter import messagebox, filedialog, ttk

import threading
from typing import *
import io
import autoDownload.console
import pyperclip
import pathlib
import time
import subprocess
from PIL import Image, ImageTk
import autoDownload

prog = autoDownload.console.DownloadProgress()
prog.start()
import lib.util.argparser as argParser

if __name__ == "__main__":
    argParser.parse()

import lib.getPlayInfo as getPlayInfo
import lib.util as util
import lib.util.types as types


rootLogger = util.getLogger("root")

rootLogger.info("base dir: %s", util.dataBasePath)

rootWindow = util.rootWindow


def _download(
    url: str,
    header: Dict[str, str],
    saveFile: pathlib.Path,
    succeed: Callable[[], None],
    fail: Callable[[], None],
    progress: ttk.Progressbar,
):
    logger = util.getLogger("_download")

    logger.info("start downloading %s", url)

    try:
        res = autoDownload.rawRequest(
            autoDownload.TaskConfig(
                url=url,
                headers=header,
                file=saveFile,
            )
        )
        prog.traceTask(res.task)
        res.task.progress.addListener(
            lambda p: (progress.configure(maximum=p.total, value=p.now), prog.refresh())
        )
        res.event.wait()
        if not res.ok:
            raise res.err or RuntimeError("download failed case by unknown reason")
    except Exception as e:
        logger.warning("download failed: %s: %s", util.errorLogInfo(e), e)

        fail()
    else:
        logger.info("download succeed")
        succeed()


def startDownload(
    videoInfo: dict, audioInfo: dict, cookie: str, savePath: pathlib.Path, video: str
):
    logger = util.getLogger("startDownload")

    refererUrl = util.getPageUrl(video)

    header = util.getHeader(cookie, refererUrl)

    videoPath = util.tempRoot.joinpath(f"video-{time.time()}.tmp")
    audioPath = util.tempRoot.joinpath(f"audio-{time.time()}.tmp")

    logger.info("videoPath: %s, audioPath: %s", videoPath, audioPath)

    def cancel():
        nonlocal cancelFlag
        if cancelFlag:
            return
        cancelFlag = True
        logger.info("download cancel")
        close()
        if videoThread is not None:
            videoThread._stop()
        if audioThread is not None:
            audioThread._stop()
        if mergeThread is not None:
            mergeThread._stop()
        logger.info("download cancel succeed")

    close, (canOK, _cannotOK), (videoProgress, audioProgress, mergeProgress) = (
        util.dialog.showProgress("下载进度", ["视频", "音频", "转码"], cancel)
    )

    mergeProgress.config(mode="indeterminate")
    mergeProgress.start()

    succeed = 0
    cancelFlag = False

    def downloadSuccess():
        nonlocal succeed
        succeed += 1
        if (succeed) >= 2:
            logger.info("download success")
            _start("merge")

    def fail(t=Literal["video", "audio"]):
        logger.info("%s download failed", t)
        if cancelFlag:
            return
        if messagebox.askokcancel("错误", f"{t}下载失败，是否重试"):
            logger.info("%s download retry", t)
            _start(t)
        else:
            logger.info("download cancel, case by download %s fail", t)
            cancel()

    def mergeSuccess():
        canOK()
        util.dialog.showinfo("下载完成", "下载完成")
        logger.info("merge succeed, download complete")

    def mergeFail():
        logger.info("merge failed")
        if messagebox.askokcancel("错误", "合并失败，是否重试"):
            logger.info("merge retry")
            _start("merge")
        else:
            logger.info("download cancel, case by merge fail")
            cancel()

    videoThread: threading.Thread | None = None
    audioThread: threading.Thread | None = None
    mergeThread: threading.Thread | None = None

    def _start(t=Literal["video", "audio", "merge"]):
        nonlocal videoThread, audioThread, mergeThread
        logger.info("start thread: %s", t)
        if t == "video":
            videoThread = threading.Thread(
                target=_download,
                args=(
                    videoInfo["baseUrl"],
                    header,
                    videoPath,
                    downloadSuccess,
                    lambda: fail(t),
                    videoProgress,
                ),
                daemon=True,
            )
            videoThread.start()
            logger.info("video thread started in thread %s", videoThread.ident)
        elif t == "audio":
            audioThread = threading.Thread(
                target=_download,
                args=(
                    audioInfo["baseUrl"],
                    header,
                    audioPath,
                    downloadSuccess,
                    lambda: fail(t),
                    audioProgress,
                ),
                daemon=True,
            )
            audioThread.start()
            logger.info("audio thread started in thread %s", videoThread.ident)
        elif t == "merge":
            mergeThread = threading.Thread(
                target=mergeVideo,
                args=(videoPath, audioPath, savePath, mergeSuccess, mergeFail),
                daemon=True,
            )
            mergeThread.start()
            logger.info("merge thread started in thread %s", mergeThread.ident)

    logger.info("window initialized")

    _start("video")
    _start("audio")


def askDownloadPart(
    videoList: List[types.VideoPart],
    callback: Callable[[types.VideoPart], None],
):

    util.dialog.askToSelect(
        "选择要下载的部分",
        [
            (
                "片段",
                [f"{index+1}. {value.title}" for index, value in enumerate(videoList)],
            )
        ],
        callback=lambda x: callback(videoList[x[0]]),
    )


def requestDownload():

    logger = util.getLogger("requestDownload")

    video = videoVar.get()
    cookie = cookieVar.get().replace("\r", "").replace("\n", "")
    savePath = savePathVar.get()

    logger.info("video: %s, cookie: %s, savePath: %s", video, cookie, savePath)

    if not (video and cookie and savePath):
        logger.info("Incomplete information, return")
        messagebox.showerror("错误", "请填写完整信息")
        return
    try:
        logger.info("Validating the save path")
        open(savePath, "wb").close()
    except Exception:
        logger.warning("Invalid save path, return")
        messagebox.showerror("错误", "无法打开保存路径")
        return
    getPlayList(video, cookie, savePath)


def getPlayList(video: str, cookie: str, savePath: str):
    logger = util.getLogger("getPlayList")
    for i in getPlayInfo.li:
        res: List[types.VideoPart] | None = i.get(video, cookie)
        if res is None:
            logger.warning("Play list not found")
            return
        elif res:
            if len(res) > 1:
                logger.info("Multiple play lists found, ask user to select")
                askDownloadPart(
                    res,
                    util.toCallback(
                        getPlayUrl, cookie=cookie, savePath=savePath, video=video
                    ),
                )
            elif len(res) == 1:
                logger.info("Single play list found, start get play url")
                getPlayUrl(res[0], cookie, savePath, video)
            return


def getPlayUrl(videoInfo: types.VideoPart, cookie: str, savePath: str, video: str):
    logger = util.getLogger("getPlayUrl")

    playinfo: types.PlayInfo = videoInfo.playinfo()

    logger.info("start ask download type")
    try:
        askDownloadType(
            playinfo["dash"]["video"],
            playinfo["dash"]["audio"],
            dict(zip(playinfo["accept_quality"], playinfo["accept_description"])),
            util.toCallback(
                startDownload, cookie=cookie, savePath=savePath, video=video
            ),
        )
    except Exception as e:
        logger.warning("Can't ask download type with error %s", util.errorLogInfo(e))
        messagebox.showerror("错误", f"无法获取视频信息\n{util.errorLogInfo(e,True)}")


def askDownloadType(
    videoList: List[Dict],
    audioList: List[Dict],
    acceptQuality: Dict[int, str],
    callback: Callable[[Dict, Dict], None],
):

    util.dialog.askToSelect(
        "选择音视频通道",
        [
            (
                "视频",
                [
                    f"{index+1}. {acceptQuality.get(value.get('id',-1),'Unknown')} - {value.get('width')}x{value.get('height')}@{value.get('frameRate')}fps"
                    for index, value in enumerate(videoList)
                ],
            ),
            (
                "音频",
                [
                    f"{index+1}. {value.get('id',-1)} - {value.get('codecs')}"
                    for index, value in enumerate(audioList)
                ],
            ),
        ],
        callback=lambda x: callback(videoList[x[0]], audioList[x[1]]),
    )


def mergeVideo(
    videoPath: pathlib.Path,
    audioPath: pathlib.Path,
    savePath: pathlib.Path,
    mergeSuccess: Callable[[], None],
    mergeFail: Callable[[], None],
):
    logger = util.getLogger("mergeVideo")

    logger.info("merge video: %s, audio: %s, save: %s", videoPath, audioPath, savePath)

    ffmpegProcess = subprocess.Popen(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(videoPath),
            "-i",
            str(audioPath),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-strict",
            "experimental",
            savePath,
            "-y",
        ],
        text=True,
        bufsize=50,
    )
    logger.info("ffmpeg process started")
    ffmpegProcess.wait()
    logger.info("ffmpeg process ended, with code: %s", ffmpegProcess.returncode)
    if ffmpegProcess.returncode != 0:
        logger.warning("ffmpeg process failed")
        mergeFail()
        return
    logger.info("ffmpeg process success")
    mergeSuccess()


class HelpButton(tk.Label):
    img = ImageTk.PhotoImage(
        Image.open(util.dataPath("help.png")).resize((18, 18), Image.LANCZOS)
    )
    helpTitle: str
    helpText: str

    def __init__(self, master, helpTitle: str, helpText: str, **kwargs):
        super().__init__(
            master,
            image=self.img,
            width=18,
            height=18,
            **kwargs,
            padx=2,
            pady=2,
            cursor="hand2",
        )
        self.helpTitle = helpTitle
        self.helpText = helpText
        self.bind("<Button-1>", self._showHelp)

    def _showHelp(self, *_args, **_kw):
        messagebox.showinfo(self.helpTitle, self.helpText)


rootLogger.info("starting")

rootWindow.title("视频下载器")
rootWindow.resizable(0, 0)
try:
    rootWindow.iconphoto(True, tk.PhotoImage(file=str(util.dataPath("icon.png"))))
except Exception as e:
    rootLogger.warning("failed to load icon")
else:
    rootLogger.info("icon loaded")


main = tk.Frame()
main.grid(row=0, column=0, padx=10, pady=10)

tk.Label(main, text="视频URL/ID号:").grid(row=0, column=0, sticky="e")

videoVar = tk.StringVar()

urlEntry = ttk.Entry(main, textvariable=videoVar, width=30)
urlEntry.grid(row=0, column=1)

HelpButton(
    main,
    helpTitle="关于视频URL/ID号",
    helpText="除了直接的b站链接外，目前还支持：\nBV号、AV号、EP号、SS号、MD号",
).grid(row=0, column=3)

ttk.Button(main, text="粘贴", command=lambda: videoVar.set(pyperclip.paste())).grid(
    row=0, column=2
)

cookieVar = tk.StringVar()
tk.Label(main, text="Cookie:").grid(row=1, column=0, sticky="e")
cookieEntry = ttk.Entry(main, textvariable=cookieVar, width=30)
cookieEntry.grid(row=1, column=1)

ttk.Button(main, text="粘贴", command=lambda: cookieVar.set(pyperclip.paste())).grid(
    row=1, column=2
)

HelpButton(
    main,
    helpTitle="关于Cookie",
    helpText="需要登录后才能下载，可以在浏览器中复制出来",
).grid(row=1, column=3)

savePathVar = tk.StringVar()
tk.Label(main, text="保存路径:").grid(row=2, column=0, sticky="e")
pathEntry = ttk.Entry(main, textvariable=savePathVar, width=30)
pathEntry.grid(row=2, column=1)

ttk.Button(
    main,
    text="选择",
    command=lambda: savePathVar.set(
        filedialog.asksaveasfilename(
            title="选择保存路径",
            filetypes=[("视频文件", ["*.mp4"]), ("所有文件", "*.*")],
            defaultextension=".mp4",
            parent=rootWindow,
        )
    ),
).grid(row=2, column=2)


def downloadButtonOnClick():
    downloadButton.configure(state="disabled")

    def _target():
        try:
            requestDownload()
        finally:
            downloadButton.configure(state="normal")

    requestDownloadThread = threading.Thread(
        target=_target,
        daemon=True,
    )
    requestDownloadThread.start()
    rootLogger.info(
        "download button onclick, starting download thread %s",
        requestDownloadThread.ident,
    )


downloadButton = ttk.Button(main, text="下载", command=downloadButtonOnClick)
downloadButton.grid(row=3, column=0, pady=10, columnspan=3, sticky="we")

rootLogger.info("Done")

if util.testFfmpeg(util.config.ffmpeg):
    rootLogger.info("ffmpeg test passed")
else:
    rootLogger.warning("ffmpeg test failed")
    messagebox.showerror("错误", "ffmpeg测试失败，请检查ffmpeg依赖状态")

rootWindow.mainloop()
