from . import dialog
import typing as t
from lib.util import types
from lib import util
from . import treeShower, iconButtons
import tkinter as tk
from tkinter import ttk
from pathlib import Path


class VideoPartResultsTreeTitleLine(tk.Frame):
    tree: treeShower.BaseTreeViewer

    def __init__(
        self,
        master: tk.Misc | None,
        tree: treeShower.BaseTreeViewer[
            types.VideoPartResults, types.VideoPart, "VideoPartShower"
        ],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.tree = tree
        ttk.Checkbutton(
            master,
            text=tree.data.title,
            variable=tree.booleanVar,
            onvalue=True,
            offvalue=False,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(master, text=tree.data.title).grid(row=0, column=0, sticky="w")
        iconButtons.FolderButton(master, tree.booleanVar).grid(
            row=0, column=1, sticky="e"
        )


class VideoPartResultsTree(
    treeShower.BaseTreeViewer[
        types.VideoPartResults, types.VideoPart, "VideoPartShower"
    ]
):
    def __init__(self, master: tk.Misc | None, data: types.VideoPartResults, **kwargs):
        super().__init__(
            master,
            data,
            VideoPartResultsTreeTitleLine,
            VideoPartShower,
            VideoPartResultsTree,
            lambda x: isinstance(x, types.VideoPartResults),
            lambda x: x.li,
            **kwargs,
        )


class VideoPartShower(tk.Frame):
    data: types.VideoPart
    __playinfo: types.PlayInfo | None = None
    active: tk.BooleanVar
    __savePath: Path | None = None
    __savePathStrVar: tk.StringVar
    __statue: t.Literal["等待分析", "等待选择", "就绪"] = "等待分析"
    _analyzeButton: ttk.Button
    _selectStream: ttk.Button
    _streamShow: tk.Label
    streams: t.Tuple[str, str] | None = None

    def __init__(self, master: tk.Misc | None, data: types.VideoPart, **kwargs):
        super().__init__(master, **kwargs)
        self.part = data
        self.__savePathStrVar = tk.StringVar()

        tk.Label(self, text=data.title).grid(row=0, column=0, sticky="w")

        self._analyzeButton = ttk.Button(self, text="分析", command=self.__analyze)
        self._analyzeButton.grid(row=0, column=1, sticky="e")

        self._selectStream = ttk.Button(
            self, text="选择流", command=self.__selectStream
        )
        self._selectStream.grid(row=0, column=2, sticky="e")

        self._streamShow = tk.Label(self)
        self._streamShow.grid(row=1, column=0, columnspan=3, sticky="nsew")

    @property
    def savePath(self) -> Path | None:
        return self.__savePath

    @savePath.setter
    def savePath(self, value: Path | None):
        self.__savePath = value
        self.__savePathStrVar.set(str(value) if value else "")

    @property
    def playinfo(self) -> types.PlayInfo | None:
        return self.__playinfo

    @playinfo.setter
    def playinfo(self, value: types.PlayInfo | None):
        self.__playinfo = value
        if self.__playinfo and self.statue == "等待分析":
            self.statue = "等待选择"

    @property
    def statue(self):
        return self.__statue

    @statue.setter
    def statue(self, value: t.Literal["等待分析", "等待选择", "就绪"]):
        self.__statue = value
        self._refreshStatue()

    def __analyze(self):
        self.playinfo = analyze(self.part)
        self.statue = "等待选择"

    def __selectStream(self):
        assert self.playinfo
        askStream(self.playinfo, self.__selectStreamDone)

    def __selectStreamDone(self, video: str, audio: str):
        self.streams = (video, audio)
        self.statue = "就绪"

    def _refreshStatue(self):
        if self.statue == "等待分析":
            self._analyzeButton.grid(row=0, column=1, sticky="e")
        elif self.statue == "等待选择":
            self._selectStream.grid(row=0, column=1, sticky="e")
        elif self.statue == "就绪":
            self._streamShow.grid(row=0, column=1, sticky="e")


def askStream(playinfo: types.PlayInfo, cb: t.Callable[[str, str], None]):
    videoList: t.List[t.Dict] = playinfo["dash"]["video"]
    audioList: t.List[t.Dict] = playinfo["dash"]["audio"]
    acceptQuality: t.Dict[int, str] = dict(
        zip(playinfo["accept_quality"], playinfo["accept_description"])
    )
    util.dialog.askToSelect(
        "选择流",
        [
            (
                "视频流",
                [
                    f"{index+1}. {acceptQuality.get(value.get('id',-1),'Unknown')} - {value.get('width')}x{value.get('height')}@{value.get('frameRate')}fps"
                    for index, value in enumerate(videoList)
                ],
            ),
            (
                "音频流",
                [
                    f"{index+1}. {value.get('id',-1)} - {value.get('codecs')}"
                    for index, value in enumerate(audioList)
                ],
            ),
        ],
        callback=lambda x: cb(videoList[x[0]]["baseUrl"], audioList[x[1]]["baseUrl"]),
    )


def analyze(part: types.VideoPart):
    try:
        return part.playinfo()
    except Exception as e:
        dialog.showerror("错误", f"无法获取视频信息\n{util.errorLogInfo(e, True)}")
        return None


def showSearchResult(vedio: str, cookie: str, result: types.VideoPartResults):
    window = dialog.showModal()
    window.title(f"搜索结果 - {vedio}")
