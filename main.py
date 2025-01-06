import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from lib.util import session

import threading
import typing as t
import io
import pyperclip
import pathlib
import time
import subprocess
from PIL import Image, ImageTk

import lib.util.argparser as argParser

if __name__ == "__main__":
    argParser.parse()

import lib.bilibiliApi as bilibiliApi
import lib.util as util
import lib.util.types as types


rootLogger = util.getLogger("root")

rootLogger.info(f"base dir: {util.dataBasePath}")

rootWindow = util.rootWindow


def _download(
    url: str,
    header: Dict[str, str],
    saveIO: io.FileIO,
    succeed: Callable[[], None],
    fail: Callable[[], None],
    progress: ttk.Progressbar,
):
    logger = util.getLogger("_download")

    logger.info(f"start downloading {url}")

    try:
        response = session.get(
            url,
            headers=header,
            stream=True,
        )
        logger.info(f"response status code: {response.status_code}")
        print(response.headers)

        assert response.status_code // 100 == 2

        progress["maximum"] = int(response.headers["Content-Length"])

        for i in response.iter_content(1024):
            saveIO.write(i)
            progress["value"] += len(i)
            progress.update()

    except Exception as e:
        logger.warning(f"download failed: {util.errorLogInfo(e)}: {e}")

        fail()
    else:
        saveIO.close()
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

    logger.info(f"videoPath: {videoPath}, audioPath: {audioPath}")

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
        logger.info(f"{t} download failed")
        if cancelFlag:
            return
        if messagebox.askokcancel("错误", f"{t}下载失败，是否重试"):
            logger.info(f"{t} download retry")
            _start(t)
        else:
            logger.info(f"download cancel, case by download {t} fail")
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
        logger.info(f"start thread: {t}")
        if t == "video":
            videoThread = threading.Thread(
                target=_download,
                args=(
                    videoInfo["baseUrl"],
                    header,
                    io.FileIO(videoPath, "wb"),
                    downloadSuccess,
                    lambda: fail(t),
                    videoProgress,
                ),
                daemon=True,
            )
            videoThread.start()
            logger.info(f"video thread started in thread {videoThread.ident}")
        elif t == "audio":
            audioThread = threading.Thread(
                target=_download,
                args=(
                    audioInfo["baseUrl"],
                    header,
                    io.FileIO(audioPath, "wb"),
                    downloadSuccess,
                    lambda: fail(t),
                    audioProgress,
                ),
                daemon=True,
            )
            audioThread.start()
            logger.info(f"audio thread started in thread {videoThread.ident}")
        elif t == "merge":
            mergeThread = threading.Thread(
                target=mergeVideo,
                args=(videoPath, audioPath, savePath, mergeSuccess, mergeFail),
                daemon=True,
            )
            mergeThread.start()
            logger.info(f"merge thread started in thread {mergeThread.ident}")

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
        logger.warning(f"Can't ask download type with error {util.errorLogInfo(e)}")
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

    logger.info(f"merge video: {videoPath}, audio: {audioPath}, save: {savePath}")

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
    logger.info(f"ffmpeg process ended, with code: {ffmpegProcess.returncode}")
    if ffmpegProcess.returncode != 0:
        logger.warning("ffmpeg process failed")
        mergeFail()
        return
    logger.info("ffmpeg process success")
    mergeSuccess()


rootLogger.info("starting")

rootWindow.title("视频下载器")
