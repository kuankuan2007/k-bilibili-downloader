from lib import util
from lib.util import types
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox
import typing as t


class IconButton(tk.Label):
    command: t.Callable[..., t.Any] | None

    def __init__(
        self,
        master,
        image: str | types.Path | Image.Image | ImageTk.PhotoImage,
        width=18,
        height=18,
        command: t.Callable[..., t.Any] | None = None,
        padx=2,
        pady=2,
        cursor="hand2",
        **kwargs
    ):
        self.command = command
        super().__init__(
            master,
            width=width,
            height=height,
            padx=padx,
            pady=pady,
            cursor=cursor,
            **kwargs,
        )
        self.bind("<Button-1>", self.onClick)
        self.setImage(image)

    def onClick(self, *args, **kw):
        if self.command:
            self.command(*args, **kw)

    def setImage(self, image: str | types.Path | Image.Image | ImageTk.PhotoImage):
        if isinstance(image, (str, types.Path)):
            image = Image.open(util.dataPath(image))
        if isinstance(image, Image.Image):
            image = ImageTk.PhotoImage(
                image.resize(
                    (self.winfo_width(), self.winfo_height()), Image.Resampling.LANCZOS
                )
            )


class HelpButton(IconButton):
    img = ImageTk.PhotoImage(
        Image.open(util.dataPath("help.png")).resize((18, 18), Image.Resampling.LANCZOS)
    )
    helpTitle: str
    helpText: str

    def __init__(self, master, helpTitle: str, helpText: str, **kwargs):
        super().__init__(
            master,
            image=self.img,
            command=self._showHelp,
            **kwargs,
        )
        self.helpTitle = helpTitle
        self.helpText = helpText

    def _showHelp(self, *_args, **_kw):
        messagebox.showinfo(self.helpTitle, self.helpText)


class FolderButton(IconButton):
    imgFolded = ImageTk.PhotoImage(
        Image.open(util.dataPath("folder.png"))
        .resize((18, 18), Image.Resampling.LANCZOS)
        .transpose(Image.Transpose.ROTATE_90)
    )
    imgUnfolded = ImageTk.PhotoImage(
        Image.open(util.dataPath("folder.png")).resize(
            (18, 18), Image.Resampling.LANCZOS
        )
    )
    booleanVar: tk.BooleanVar

    def __init__(self, master, boolVar: tk.BooleanVar, **kwargs):
        super().__init__(
            master,
            image=self.imgFolded if boolVar.get() else self.imgUnfolded,
            cursor="hand2",
            **kwargs,
        )
        self.booleanVar = boolVar
        self.booleanVar.trace_add("write", lambda *_args, **_kw: self.refresh())

    def onClick(self, *_args, **_kw):
        self.booleanVar.set(not self.booleanVar.get())

    def refresh(self):
        self.setImage(
            image=self.imgFolded if self.booleanVar.get() else self.imgUnfolded
        )
