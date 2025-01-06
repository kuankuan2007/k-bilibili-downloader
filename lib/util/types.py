import typing as t
from dataclasses import dataclass

from pathlib import Path


@dataclass(frozen=True, eq=True)
class Config:
    timeout: int = 10
    log_level: t.Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    ffmpeg: str = "ffmpeg"


PlayInfo = t.Dict[str, t.Any]


@dataclass
class VideoPart:
    title: str
    playinfo: t.Callable[[], PlayInfo]


@dataclass
class VideoPartResults:
    title: str
    li: "t.List[VideoPart | VideoPartResults]"


DownloadTaskCallback = t.Callable[
    [bool, Exception | None],
    None,
]


@dataclass
class DownloadTask:
    url: str
    file: Path
    cookie: str
    referer: str
    cb: DownloadTaskCallback
