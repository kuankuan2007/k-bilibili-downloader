from dataclasses import dataclass
import typing as _tt


@dataclass(frozen=True, eq=True)
class Config:
    timeout: int = 10
    log_level: _tt.Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    ffmpeg: str = "ffmpeg"


PlayInfo = dict


@dataclass
class VideoPart:
    title: str
    playinfo: _tt.Callable[[], PlayInfo]
