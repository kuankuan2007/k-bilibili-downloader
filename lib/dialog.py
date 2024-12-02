from typing import *
from tkinter.messagebox import *
import tkinter as tk
from tkinter import ttk
from . import util


def askToSelect(
    title: str,
    questions: List[Tuple[str, List[str]]],
    callback: Callable[[List[int]], None],
    width: int = 40,
    master: tk.Tk | tk.Toplevel = util.rootWindow,
) -> List[int]:
    """
    Ask the user to select answers from a list of questions.

    Args:
        title (str): The title of the window.
        questions (List[Tuple[str, List[str]]]): A list of tuples, where each tuple contains a question string and a list of answer strings.

    Returns:
        List[int]: A list of indices representing the selected answers.
    """

    logger = util.getLogger("askToSelect")

    window = util.showModal(master)
    window.title(title)

    selecters: ttk.Combobox = []

    for index, (question, answers) in enumerate(questions):
        tk.Label(window, text=question).grid(
            row=index, column=0, padx=5, pady=5, sticky="e"
        )
        selecter = ttk.Combobox(window, width=width)
        selecter.grid(row=index, column=1, padx=5)
        selecters.append(selecter)
        selecter["values"] = answers
        selecter.current(0)

    buttonBox = tk.Frame(window)
    buttonBox.grid(row=len(questions), column=0, columnspan=2, pady=5, sticky="e")

    def confirmed():
        """
        Callback function for the "Confirm" button.
        Closes the window and returns the selected answers.
        """
        result = [i.current() for i in selecters]
        close()
        callback(result)

    def close():
        logger.info("window closed")
        window.destroy()

    ttk.Button(buttonBox, text="确定", command=confirmed).grid(row=0, column=1, padx=10)
    ttk.Button(buttonBox, text="取消", command=close).grid(row=0, column=0, padx=10)
