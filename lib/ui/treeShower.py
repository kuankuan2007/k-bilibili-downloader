import tkinter as tk
import typing as t

T = t.TypeVar("T")
D = t.TypeVar("D")
W = t.TypeVar("W", bound=tk.Widget)


class BaseTreeViewer(tk.Frame, t.Generic[T, D, W]):
    data: T
    titleLine: tk.Widget
    _ChileWeight: t.Callable[[D], W]
    __childrenPart: tk.Frame
    parent: "BaseTreeViewer[T, D,W] | None"
    indent: int
    booleanVar: tk.BooleanVar

    def __init__(
        self,
        master: tk.Misc | None,
        data: T,
        titleLine: "t.Callable[[tk.Misc|None,BaseTreeViewer[T, D, W]], tk.Widget]",
        ChildWidget: t.Callable[[tk.Frame, D], W],
        SubTree: t.Callable[[tk.Widget | None, T], "BaseTreeViewer[T, D, W]"],
        isSubTree: t.Callable[[T | D], bool],
        getChildren: t.Callable[[T], t.Iterable[D | T]],
        indent: int = 4,
        booleanVar: tk.BooleanVar | None = None,
        _parent: "BaseTreeViewer[T, D,W] | None" = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.data = data
        self.parent = _parent
        self.indent = indent

        self.booleanVar = booleanVar or tk.BooleanVar(value=_parent is not None)

        self.titleLine = titleLine(master, self)
        self.titleLine.grid(row=0, column=0, sticky="we")
        tk.Label(self, width=indent).grid(row=1, column=0)

        self.__childrenPart = tk.Frame(self)
        for index, i in enumerate(getChildren(data)):
            if isSubTree(i):
                w = SubTree(self.__childrenPart, i)  # type: ignore
            else:
                w = ChildWidget(self.__childrenPart, i)  # type: ignore
            w.grid(row=index, column=0, sticky="we")

        self.reGrid()
        self.booleanVar.trace_add("write", lambda *args: self.reGrid())

    def reGrid(self):
        self.grid_forget()
        self.titleLine.grid(row=0, column=0, sticky="we")
        if self.booleanVar.get():
            self.__childrenPart.grid(
                row=0, column=0, sticky="we", pady=(self.indent, 0)
            )
