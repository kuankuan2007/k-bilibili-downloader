import tkinter as tk
from tkinter import ttk, filedialog
from lib import util
from . import iconButtons, dialog
import pyperclip
import threading
from lib import bilibiliApi

util.rootWindow.title("Bilibili Downloader")

uiLogger = util.getLogger("ui")

util.rootWindow.resizable(False, False)
try:
    util.rootWindow.iconphoto(True, tk.PhotoImage(file=str(util.dataPath("icon.png"))))
except Exception as e:
    uiLogger.warning("failed to load icon")
else:
    uiLogger.info("icon loaded")


main = tk.Frame(util.rootWindow)
main.grid(row=0, column=0, padx=10, pady=10)

tk.Label(main, text="视频URL/ID号:").grid(row=0, column=0, sticky="e")

videoVar = tk.StringVar()

urlEntry = ttk.Entry(main, textvariable=videoVar, width=30)
urlEntry.grid(row=0, column=1)

iconButtons.HelpButton(
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

iconButtons.HelpButton(
    main,
    helpTitle="关于Cookie",
    helpText="需要登录后才能下载，可以在浏览器中复制出来",
).grid(row=1, column=3)


def downloadButtonOnClick():
    downloadButton.configure(state="disabled")

    def _target():
        try:
            res = bilibiliApi.analyzeUrl(
                videoVar.get(),
                cookieVar.get(),
            )
        except Exception as e:
            util.dialog.showerror(
                "错误",
                f"下载失败\n{util.errorLogInfo(e)}",
            )

    requestDownloadThread = threading.Thread(
        target=_target,
        daemon=True,
    )
    requestDownloadThread.start()
    uiLogger.info(
        f"download button onclick, starting download thread {requestDownloadThread.ident}"
    )


downloadButton = ttk.Button(main, text="下载", command=downloadButtonOnClick)
downloadButton.grid(row=3, column=0, pady=10, columnspan=3, sticky="we")

uiLogger.info("Done")
