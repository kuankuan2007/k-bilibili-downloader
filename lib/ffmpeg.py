from typing import *
import platform
import subprocess
import urllib.parse as urlparse
import requests
import zipfile
import py7zr
import tarfile
from . import util
import mimetypes
import pathlib
import io
import threading


ffmpegDefaultPath = pathlib.Path.home().joinpath("ffmpeg")
ffmpegCallable = util.config.ffmpeg


def testFFmpeg(path: str) -> bool:
    try:
        subprocess.call(
            [path, "-version"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
        )
    except Exception:
        return False
    return True


def searchFFmpeg() -> bool:
    global ffmpegCallable
    # if testFFmpeg(ffmpegCallable):
    #     return True
    if ffmpegCallable != "ffmpeg":
        ffmpegCallable = "ffmpeg"
        if testFFmpeg(ffmpegCallable):
            return True
    ffmpegCallable = dfsFindFFmpeg(ffmpegDefaultPath)
    if ffmpegCallable is None:
        return False
    return testFFmpeg(ffmpegCallable)


def dfsFindFFmpeg(now: pathlib.Path) -> Optional[pathlib.Path]:
    print(now)
    if not now.exists():
        return
    if now.is_dir():
        for i in now.iterdir():
            res = dfsFindFFmpeg(i)
            if res is not None:
                return res
    elif now.name.startswith("ffmpeg") and now.parent.name == "bin":
        return now


def downloadFfmpeg():
    global ffmpegCallable
    downloadUrl: str | None = None
    if platform.system() == "Windows":
        downloadUrl = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    elif platform.system() == "Linux":
        if platform.machine() == "aarch64":
            downloadUrl = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"
        else:
            downloadUrl = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"

    elif platform.system() == "Darwin":
        downloadUrl = "https://evermeet.cx/ffmpeg/get/zip"

    if downloadUrl is None:
        raise Exception("Unsupported platform")

    def cancel():
        try:
            downloadThread._stop()
        finally:
            close()

    close, (canOK, _cannotOK), (downloadProgressBar, unzipProgressBar) = (
        util.dialog.showProgress("下载FFmpeg", ["下载", "解压"], cancel)
    )
    unzipProgressBar.config(mode="indeterminate")
    unzipProgressBar.start()

    filepath = util.tempRoot.joinpath("ffmpeg.tmp")

    def onHeader(res: requests.Response, changeSaveIo: Callable[[io.FileIO], None]):
        nonlocal filepath
        mimetypes.add_type("application/x-7z-compressed", ".7z")
        extension = (
            mimetypes.guess_extension(
                res.headers.get("Content-Type", "application/octet-stream"), True
            )
            or ".bin"
        )
        if extension == ".bin":
            try:
                extension='.'+urlparse.urlparse(downloadUrl).path.split(".")[-1]
            except Exception as e:
                raise Exception("Unknown file type") from e
        filepath = util.tempRoot.joinpath("ffmpeg" + extension)
        print(filepath)
        changeSaveIo(io.FileIO(filepath, "wb"))

    def downloadFail():
        if util.dialog.askokcancel("下载失败", "下载失败，是否重试?"):
            threading.Thread(target=downloadFfmpeg, daemon=True).start()
        else:
            cancel()

    def afterDownload():
        global ffmpegCallable
        ffmpegDefaultPath.mkdir(parents=True, exist_ok=True)

        if filepath.suffix == ".zip":
            with zipfile.ZipFile(filepath, "r") as f:
                f.extractall(str(ffmpegDefaultPath))
        elif filepath.suffix == ".xz":
            with tarfile.open(filepath, "r:xz") as f:
                f.extractall(str(ffmpegDefaultPath))
        elif filepath.suffix == ".7z":
            with py7zr.SevenZipFile(filepath, "r") as f:
                f.extractall(str(ffmpegDefaultPath))
        else:
            raise Exception("Unknown file type")
        ffmpegCallable = dfsFindFFmpeg(ffmpegDefaultPath)
        canOK()
        util.dialog.showinfo("下载成功", "ffmpeg已成功下载")

    downloadThread = threading.Thread(
        target=util.download,
        args=[
            downloadUrl,
            None,
            None,
            afterDownload,
            downloadFail,
            downloadProgressBar,
            onHeader,
        ],
    )
    downloadThread.start()
