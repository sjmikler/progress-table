#  Copyright (c) 2022 Szymon Mikler

from __future__ import annotations

import math

from colorama import Fore, Style
from dataclasses import dataclass
from collections import defaultdict
import time


@dataclass
class Boxes:
    horizontal: str = "─"
    vertical: str = "│"
    all: str = "┼"

    up_left: str = "┘"
    up_right: str = "└"
    down_left: str = "┐"
    down_right: str = "┌"

    no_left: str = "├"
    no_right: str = "┤"
    no_up: str = "┬"
    no_down: str = "┴"


class ProgressTable:
    def __init__(
        self,
        columns=(),
        default_column_width=8,
        progress_bar_fps=5,
        custom_formatting=None,
    ):
        self.default_width = default_column_width

        self.columns = list(columns)
        self.num_rows = 0

        self.widths = defaultdict(lambda: self.default_width)
        self.colors = defaultdict(lambda: None)
        self.values = defaultdict(str)

        self.progress_bar_fps = progress_bar_fps
        self.header_printed = False

        self.custom_formatting = custom_formatting or {}
        self.needs_line_ending = False
        self.finished_rows = []

    def add_column(self, name, width=None, color=None):
        assert not self.header_printed, "Header is already frozen!"
        self.columns.append(name)

        width = width if width is not None else self.default_width
        if width < len(name):
            width = len(name)

        if color is not None:
            self.colors[name] = color

        self.widths[name] = width

    def bar(self, left: str, center: str, right: str):
        content = []
        for col in self.columns:
            content.append(Boxes.horizontal * (self.widths[col] + 2))

        content = center.join(content)
        content = [left, content, right]
        print("".join(content), end="")

    def print_top_bar(self):
        return self.bar(
            left=Boxes.down_right, center=Boxes.no_up, right=Boxes.down_left
        )

    def print_bottom_bar(self):
        return self.bar(left=Boxes.up_right, center=Boxes.no_down, right=Boxes.up_left)

    def print_center_bar(self):
        return self.bar(left=Boxes.no_left, center=Boxes.all, right=Boxes.no_right)

    def print_header(self):
        self.print_top_bar()
        print()

        content = []
        for col in self.columns:
            width = self.widths[col]
            value = col[:width].center(width)

            if self.colors[col] is not None:
                value = f"{self.colors[col]}{value}{Style.RESET_ALL}"

            content.append(value)
        print(Boxes.vertical, f"{' │ '.join(content)}", Boxes.vertical)

        self.header_printed = True
        self.print_center_bar()
        print()

    def print_row(self):
        if not self.header_printed:
            self.print_header()

        if len(self.values) == 0:
            return
        else:
            self.needs_line_ending = True

        print(end="\r")

        content = []
        for col in self.columns:
            value = self.values[col]
            width = self.widths[col]

            value_type = type(value).__name__
            if value_type in self.custom_formatting:
                value = self.custom_formatting[value_type](value)

            value = str(value)[:width].center(width)

            if self.colors[col] is not None:
                value = f"{self.colors[col]}{value}{Style.RESET_ALL}"

            content.append(value)
        print(Boxes.vertical, f"{' │ '.join(content)}", Boxes.vertical, end="")

    def next_row(self, save=True):
        if self.needs_line_ending:
            print()
            self.needs_line_ending = False

        if save and len(self.values) > 0:
            self.finished_rows.append(self.values)
            self.num_rows += 1

        self.values = defaultdict(str)

    def close(self):
        self.print_row()
        self.next_row()
        self.print_bottom_bar()
        self.header_printed = False
        print()

    def print_progress_bar(self, i, n):
        tot_width = sum(self.widths.values()) + 3 * (len(self.widths) - 1)
        num_hashes = math.ceil(i / n * tot_width)
        num_empty = tot_width - num_hashes

        print(
            Boxes.vertical,
            " ",
            "#" * num_hashes,
            " " * num_empty,
            " ",
            Boxes.vertical,
            end="",
            sep="",
        )

    def to_list(self):
        return [[row[col] for col in self.columns] for row in self.finished_rows]

    def numpy(self):
        import numpy as np

        return np.array(self.to_list())

    def df(self):
        import pandas as pd

        return pd.DataFrame(self.to_list(), columns=self.columns)

    def display_custom(self, data):
        if self.header_printed:
            self.close()

        for row in data:
            assert len(row) == len(self.columns)
            for key, value in zip(self.columns, row):
                self.values[key] = value
            self.print_row()
            self.next_row(save=False)
        self.close()

    def display(self):
        if self.header_printed:
            self.close()
        self.display_custom(self.to_list())

    def __call__(self, iterator):
        if not self.header_printed:
            self.print_header()

        assert hasattr(iterator, "__len__")
        length = len(iterator)

        last_printed = -float("inf")
        for idx, element in enumerate(iterator):
            print(end="\r")

            if time.time() - last_printed > 1 / self.progress_bar_fps:
                self.print_progress_bar(idx, length)

            yield element
        self.print_row()

    def __setitem__(self, key, value):
        assert key in self.columns, f"Column {key} not in {self.columns}"
        self.values[key] = value
        self.print_row()
