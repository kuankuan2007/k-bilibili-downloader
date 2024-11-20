import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import requests
import re
import json
import threading
from typing import *
import io
import pyperclip
import tempfile
import pathlib
import time
import shutil
import subprocess


def showModal(master):
    window = tk.Toplevel(master)
    window.transient(master)
    window.grab_set()
    return window


def _download(
    url: str,
    header: Dict[str, str],
    saveIO: io.FileIO,
    succeed: Callable[[], None],
    fail: Callable[[], None],
    progress: ttk.Progressbar,
):
    response = requests.get(url, headers=header, stream=True)

    try:
        progress["maximum"] = int(response.headers["Content-Length"])
        assert response.status_code // 100 == 2
        for i in response.iter_content(1024):
            saveIO.write(i)
            progress["value"] += len(i)
            progress.update()

    except Exception:
        fail()
    else:
        saveIO.close()
        succeed()


def startDownload(
    videoInfo: dict, audioInfo: dict, header: dict, savePath: pathlib.Path
):

    tempRoot = pathlib.Path(tempfile.gettempdir()).joinpath(
        f"k-bilibili-download-{time.time()}"
    )
    if not tempRoot.exists():
        os.mkdir(tempRoot)

    videoPath = tempRoot.joinpath("video.tmp")
    audioPath = tempRoot.joinpath("audio.tmp")

    progressWindow = showModal(root)
    progressWindow.title("下载进度")

    main = tk.Frame(progressWindow)
    main.grid(column=0, row=0, padx=10, pady=10)

    tk.Label(main, text="视频").grid(row=0, column=0, sticky="e")
    tk.Label(main, text="音频").grid(row=1, column=0, sticky="e")
    tk.Label(main, text="转码").grid(row=2, column=0, sticky="e")

    videoProgress = ttk.Progressbar(
        main, orient="horizontal", mode="determinate", length=200
    )
    audioProgress = ttk.Progressbar(
        main, orient="horizontal", mode="determinate", length=200
    )
    mergeProgress = ttk.Progressbar(
        main, orient="horizontal", mode="indeterminate", length=200
    )

    videoProgress.grid(row=0, column=1)
    audioProgress.grid(row=1, column=1)
    mergeProgress.grid(row=2, column=1)

    buttonBox = tk.Frame(main)
    buttonBox.grid(row=3, column=0, columnspan=2, sticky="E")

    def cancel():
        videoThread and videoThread._stop()
        audioThread and audioThread._stop()
        mergeThread and mergeThread._stop()
        shutil.rmtree(str(tempRoot))
        close()

    def close():
        progressWindow.destroy()

    ttk.Button(buttonBox, text="取消", command=cancel).grid(row=0, column=0)

    okButton = ttk.Button(buttonBox, text="确定", state="disabled")
    okButton.grid(column=1, row=0)

    succeed = 0

    def downloadSuccess():
        nonlocal succeed
        succeed += 1
        if (succeed) >= 2:
            _start("merge")

    def fail(t=Literal["video", "audio"]):
        if messagebox.askokcancel("错误", f"{t}下载失败，是否重试"):
            _start(t)
        else:
            cancel()

    def mergeSuccess():
        close()
        messagebox.showinfo("完成", "下载完成")

    videoThread: threading.Thread
    audioThread: threading.Thread
    mergeThread: threading.Thread

    def _start(t=Literal["video", "audio", "merge"]):
        nonlocal videoThread, audioThread, mergeThread
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
        elif t == "merge":
            mergeThread = threading.Thread(
                target=mergeVideo,
                args=(videoPath, audioPath, savePath, mergeSuccess),
                daemon=True,
            )
            mergeThread.start()

    _start("video")
    _start("audio")


def requestDownload():
    video = videoVar.get()
    cookie = cookieVar.get()
    savePath = savePathVar.get()

    if not (video and cookie and savePath):
        messagebox.showerror("错误", "请填写完整信息")
        return
    if re.match(
        r"^(((ht|f)tps?):\/\/)?([^!@#$%^&*?.\s-]([^!@#$%^&*?.\s]{0,63}[^!@#$%^&*?.\s])?\.)+[a-z]{2,6}\/?",
        video,
    ):
        url = video
    elif re.match(
        re.compile("av{1-9}\d*", re.I),
        video,
    ) or re.match("(?:B|b)(?:v|V)[0-9a-zA-Z]{10}", video):
        url = f"https://www.bilibili.com/video/{video}?spm_id_from=player_end_recommend_autoplay"
    else:
        messagebox.showerror("错误", "请输入正确的视频地址或av号/BV号")
        return
    headers = {
        "Referer": url,
        "Cookie": cookie,
        "Accept": "*/*" "Accept-language:zh-CN,zh;q=0.9,en;q=0.8",
        "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    }

    try:
        response = requests.get(url, headers=headers)
        assert response.status_code // 100 == 2
        html = response.text
    except Exception:
        messagebox.showerror(
            "错误",
            "请求错误，无法获取页面信息",
        )
        return

    try:
        flag = False
        for i in [
            r"window.__playinfo__=(.*?)</script>",
            r'"video_info":(.*),(\s\n\t)*"view_info"',
        ]:
            try:
                palyInfo = json.loads(re.findall(i, html)[0])
            except Exception:
                continue
            else:
                flag = True
                break
        if not flag:
            raise Exception()

        acceptQuality: Dict[int, str] = dict(
            zip(
                palyInfo["data"]["accept_quality"],
                palyInfo["data"]["accept_description"],
            )
        )

        videoList: List[dict] = palyInfo["data"]["dash"]["video"]
        audioList: List[dict] = palyInfo["data"]["dash"]["audio"]

        assert len(audioList)
        assert len(videoList)

    except Exception:
        messagebox.showerror("错误", "解析错误，无法获取视频信息")
        return
    try:
        open(savePath, "wb").close()
    except Exception:
        messagebox.showerror("错误", "无法打开保存路径")
        return

    def askDownloadTypeCallback(videoInfo: dict, audioInfo: dict):
        startDownload(videoInfo, audioInfo, headers, savePath)

    askDownloadType(videoList, audioList, acceptQuality, askDownloadTypeCallback)

    #     video_content = stream_download(
    #         video_url, headers, os.path.join(save_path, f"{title}.mp4")
    #     )
    #     audio_content = stream_download(
    #         audio_url, headers, os.path.join(save_path, f"{title}.mp3")
    #     )

    #     if video_content and audio_content:
    #         return title
    #     else:
    #         messagebox.showerror("错误", "下载失败。")


def askDownloadType(
    videoList: List[Dict],
    audioList: List[Dict],
    acceptQuality: Dict[int, str],
    callback: Callable[[Dict, Dict], None],
):

    selectWindow = showModal(root)
    selectWindow.title("选择音视频通道")

    main = tk.Frame(selectWindow)
    main.grid(row=0, column=0, padx=10, pady=10)

    tk.Label(main, text="视频通道:").grid(row=0, column=0)
    tk.Label(main, text="音频通道:").grid(row=1, column=0)

    videoCombobox = ttk.Combobox(main, width=40)
    videoCombobox["values"] = [
        f"{index+1}. {acceptQuality.get(value.get('id',-1),'Unknown')} - {value.get('width')}x{value.get('height')}@{value.get('frameRate')}fps"
        for index, value in enumerate(videoList)
    ]
    videoCombobox.current(0)
    videoCombobox.config(state="readonly")

    videoCombobox.grid(row=0, column=1)

    audioCombobox = ttk.Combobox(main, width=40)
    audioCombobox["values"] = [
        f"{index+1}. {value.get('id',-1)} - {value.get('codecs')}"
        for index, value in enumerate(audioList)
    ]
    audioCombobox.current(0)
    audioCombobox.config(state="readonly")

    audioCombobox.grid(row=1, column=1)

    buttonBox = tk.Frame(main)
    buttonBox.grid(row=2, column=0, columnspan=2, pady=10, sticky="e")

    def startDownload():
        video = videoList[videoCombobox.current()]
        audio = audioList[audioCombobox.current()]
        close()

        callback(video, audio)

    def close():
        selectWindow.destroy()

    ttk.Button(buttonBox, text="取消", command=close).grid(row=0, column=0)
    ttk.Button(buttonBox, text="确认", command=startDownload).grid(
        row=0, column=1, padx=2
    )


def mergeVideo(
    videoPath: pathlib.Path,
    audioPath: pathlib.Path,
    savePath: pathlib.Path,
    mergeSuccess: Callable[[], None],
):
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
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=50,
    )
    ffmpegProcess.wait()
    mergeSuccess()


# 创建主窗口
root = tk.Tk()
root.title("视频下载器")

main = tk.Frame()
main.grid(row=0, column=0, padx=10, pady=10)

tk.Label(main, text="视频URL/BV号/AV号:").grid(row=0, column=0, sticky="e")

videoVar = tk.StringVar()

urlEntry = ttk.Entry(main, textvariable=videoVar, width=30)
urlEntry.grid(row=0, column=1)

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
            parent=root,
        )
    ),
).grid(row=2, column=2)

ttk.Button(main, text="下载", command=requestDownload).grid(
    row=3, column=0, pady=10, columnspan=3, sticky="we"
)


root.mainloop()
