#  Copyright (c) 2022 Szymon Mikler

from __future__ import annotations

import functools
import logging
import math
import sys
import time
from builtins import KeyError, staticmethod
from collections import defaultdict
from typing import Any, Callable, Dict, List, Tuple

from colorama import Fore, Style

from . import symbols

ALL_COLORS = [getattr(Fore, x) for x in dir(Fore) if not x.startswith("__")]
ALL_STYLES = [getattr(Style, x) for x in dir(Style) if not x.startswith("__")]
ALL_COLOR_STYLES = ALL_COLORS + ALL_STYLES

ITERATOR_LENGTH_UNKNOWN_WARNED_ONCE = False
ITERATOR_LENGTH_CACHE: Dict[int, int] = {}


class ProgressTable:
    def __init__(
        self,
        columns: Tuple | List = (),
        refresh_rate: int = 10,
        num_decimal_places: int = 4,
        default_column_width: int = 8,
        default_column_alignment: str = "center",
        print_row_on_update: bool = True,
        reprint_header_every_n_rows: int = 30,
        custom_format: Callable[[Any], Any] | None = None,
        embedded_progress_bar: bool = False,
        table_style="normal",
        file=sys.stdout,
    ):
        self.refresh_rate = refresh_rate
        self.default_width = default_column_width
        self.default_alignment = default_column_alignment
        self.print_row_on_update = print_row_on_update
        self.reprint_header_every_n_rows = reprint_header_every_n_rows
        self.custom_format = custom_format or self.get_default_format_func(num_decimal_places)
        self.embedded_progress_bar = embedded_progress_bar

        self.file = file
        self._print = functools.partial(print, file=self.file)

        # Helpers
        self._widths: Dict[str, int] = {}
        self._colors: Dict[str, str] = {}
        self._alignment: Dict[str, str] = {}
        self._aggregate: Dict[str, str | None] = {}
        self._new_row: Dict[str, Any] = defaultdict(str)
        self._aggregate_n: Dict[str, int] = defaultdict(int)

        self.num_rows = 0
        self.columns: List[str] = []
        self.finished_rows: List[Dict[Any, Any]] = []

        self._needs_line_ending = False
        self._last_time_row_printed = 0
        self._last_header_printed_at_row_count = 0

        self.header_printed = False
        self.progress_bar_active = False
        self._refresh_progress_bar: Callable = lambda: None

        self._symbols: symbols.Symbols

        if table_style == "normal":
            self._symbols = symbols.SymbolsUnicode()
        elif table_style == "round":
            self._symbols = symbols.SymbolsUnicodeRound()
        elif table_style == "double":
            self._symbols = symbols.SymbolsUnicodeDouble()
        elif table_style == "bold":
            self._symbols = symbols.SymbolsUnicodeBold()
        elif table_style == "basic":
            self._symbols = symbols.SymbolsBasic()
        else:
            allowed_styles = ["normal", "round", "double", "bold", "basic"]
            raise KeyError(f"Style '{table_style}' not in {allowed_styles}!")

        for column in columns:
            self.add_column(column)

    @staticmethod
    def get_default_format_func(decimal_places):
        def fmt(x):
            if isinstance(x, int):
                return x
            else:
                try:
                    return format(x, f".{decimal_places}f")
                except Exception:
                    return x

        return fmt

    def apply_cell_formatting(self, str_value: str, column: str):
        width = self._widths[column]

        alignment = self._alignment[column]
        if alignment == "center":
            str_value = str_value.center(width)
        elif alignment == "left":
            str_value = str_value.ljust(width)
        elif alignment == "right":
            str_value = str_value.rjust(width)
        else:
            allowed_alignments = ["center", "left", "right"]
            raise KeyError(f"Alignment '{alignment}' not in {allowed_alignments}!")

        clipped = len(str_value) > width
        str_value = "".join(
            [
                " ",  # space at the beginning of the row
                str_value[:width].center(width),
                self._symbols.dots if clipped else " ",
            ]
        )

        if self._colors[column] is not None:
            str_value = f"{self._colors[column]}{str_value}{Style.RESET_ALL}"
        return str_value

    def add_column(self, name, *, width=None, alignment=None, color=None, aggregate=None):
        assert not self.header_printed, "Columns cannot be modified after displaying the first row!"

        if name in self.columns:
            logging.info(f"Column '{name}' already exists!")
        else:
            self.columns.append(name)

        width = width if width is not None else self.default_width
        if width < len(name):
            width = len(name)

        self._colors.setdefault(name, "")
        if color is not None:
            if isinstance(color, str):
                color = [color]
            for str_color in color:
                byte_color = self._maybe_convert_to_colorama(str_color)
                self._check_color(byte_color, str_color)
                self._colors[name] += byte_color

        alignment = alignment if alignment is not None else self.default_alignment
        self._alignment[name] = alignment

        assert aggregate in [None, "mean", "sum"], "Allowed aggregate types: [None, 'mean', 'sum']"
        self._aggregate[name] = aggregate
        self._widths[name] = width

    def add_columns(self, iterable, **kwds):
        for column in iterable:
            self.add_column(column, **kwds)

    def next_row(self, save=True):
        self._print_row()
        self._maybe_line_ending()
        if self.progress_bar_active:
            self._refresh_progress_bar()
        sys.stdout.flush()

        if save and len(self._new_row) > 0:
            self.finished_rows.append(self._new_row)
            self.num_rows += 1

        self._new_row = defaultdict(str)
        self._aggregate_n = defaultdict(int)

    def close(self):
        self.next_row()
        self._print_bottom_bar()
        self.header_printed = False
        self._print()

    def to_list(self):
        return [[row[col] for col in self.columns] for row in self.finished_rows]

    def to_numpy(self):
        import numpy as np

        return np.array(self.to_list())

    def to_df(self):
        import pandas as pd

        return pd.DataFrame(self.to_list(), columns=self.columns)

    def display(self):
        if self.header_printed:
            self.close()
        self._display_custom(self.to_list())

    def _bar(self, left: str, center: str, right: str):
        content_list: List[str] = []
        for col in self.columns:
            content_list.append(self._symbols.horizontal * (self._widths[col] + 2))

        center = center.join(content_list)
        content = ["\r", left, center, right]
        self._print("".join(content), end="")

    def _bar_custom_center(self, left: str, center: List[str] | str, right: str):
        """UNUSED"""
        content_list: List[str] = []

        if isinstance(center, str):
            center = [center] * (len(self.columns) - 1)
        assert len(center) == len(self.columns) - 1

        for col in self.columns:
            content_list.append(self._symbols.horizontal * (self._widths[col] + 2))
            if center:
                content_list.append(center.pop(0))

        center = "".join(content_list)
        content = ["\r", left, center, right]
        self._print("".join(content), end="")

    def _print_transition_bar(self, previous_n_cols, new_n_cols):
        """UNUSED"""
        assert previous_n_cols > 0
        assert new_n_cols > previous_n_cols
        added_cols = new_n_cols - previous_n_cols

        symbols = [
            *([self._symbols.all] * previous_n_cols),
            *([self._symbols.no_up] * (added_cols - 1)),
        ]
        return self._bar_custom_center(
            left=self._symbols.no_left, center=symbols, right=self._symbols.down_left
        )

    def _print_top_bar(self):
        return self._bar(
            left=self._symbols.down_right, center=self._symbols.no_up, right=self._symbols.down_left
        )

    def _print_bottom_bar(self):
        return self._bar(
            left=self._symbols.up_right, center=self._symbols.no_down, right=self._symbols.up_left
        )

    def _print_center_bar(self):
        return self._bar(left=self._symbols.no_left, center=self._symbols.all, right=self._symbols.no_right)

    @staticmethod
    def _maybe_convert_to_colorama(color):
        if isinstance(color, str):
            if hasattr(Fore, color.upper()):
                return getattr(Fore, color.upper())
            if hasattr(Style, color.upper()):
                return getattr(Style, color.upper())
        return color

    @staticmethod
    def _check_color(color, color_str=None):
        if color_str is None:
            color_str = color
        assert color in ALL_COLOR_STYLES, f"Only colorama colors are allowed (not {color_str})!"

    def _print_header(self, top=True):
        assert self.columns, "Columns are required! Use .add_column method or specify them in __init__!"

        if top:
            self._print_top_bar()
        else:
            self._print_center_bar()
        self._print()

        content = []
        for column in self.columns:
            value = self.apply_cell_formatting(column, column)
            content.append(value)
        s = "".join(
            ["\r", self._symbols.vertical, self._symbols.vertical.join(content), self._symbols.vertical]
        )
        self._print(s)

        self._last_header_printed_at_row_count = self.num_rows
        self.header_printed = True
        self._print_center_bar()
        self._print()

    def _get_row(self):
        content = []
        for column in self.columns:
            value = self._new_row[column]
            value = self.custom_format(value)
            value = self.apply_cell_formatting(str_value=str(value), column=column)
            content.append(value)
        return "".join(
            ["\r", self._symbols.vertical, self._symbols.vertical.join(content), self._symbols.vertical]
        )

    def _print_row(self):
        if not self.header_printed:
            self._print_header(top=True)
        if self.num_rows - self._last_header_printed_at_row_count >= self.reprint_header_every_n_rows:
            self._print_header(top=False)

        if len(self._new_row) == 0:
            return
        self._needs_line_ending = True
        self._print(self._get_row(), end="")

    def _print_progress_bar(self, i, n, show_before=" ", show_after=" ", embedded=False):
        i = min(i, n)  # clip i to be not bigger than n

        if not embedded:
            tot_width = sum(self._widths.values()) + 3 * (len(self._widths) - 1) + 2
            tot_width = tot_width - len(show_before) - len(show_after)

            num_hashes = math.ceil(i / n * tot_width)
            num_empty = tot_width - num_hashes

            self._print(
                self._symbols.vertical,
                show_before,
                self._symbols.pbar_filled * num_hashes,
                self._symbols.pbar_empty * num_empty,
                show_after,
                self._symbols.vertical,
                end="\r",
                sep="",
            )
        else:
            row = self._get_row()
            new_row = []
            for idx, letter in enumerate(row):
                if idx / len(row) <= i / n:
                    if letter == " ":
                        letter = self._symbols.embedded_pbar_filled
                new_row.append(letter)
            row = "".join(new_row)
            self._print(row, end="\r")
        sys.stdout.flush()

    def _maybe_line_ending(self):
        if self._needs_line_ending:
            self._print()
            self._needs_line_ending = False

    def _display_custom(self, data):
        if self.header_printed:
            self.close()

        for row in data:
            assert len(row) == len(self.columns)
            for key, value in zip(self.columns, row):
                self._new_row[key] = value
            self._print_row()
            self.next_row(save=False)
        self.close()

    def __call__(self, iterator, length=None, prefix="", show_throughput=True):
        """Display progress bar over the iterator."""
        global ITERATOR_LENGTH_UNKNOWN_WARNED_ONCE, ITERATOR_LENGTH_CACHE

        if not self.header_printed:
            self._print_header()

        if length is None and not hasattr(iterator, "__len__"):
            if not ITERATOR_LENGTH_UNKNOWN_WARNED_ONCE:
                logging.warning("Iterator length is unknown!")
                ITERATOR_LENGTH_UNKNOWN_WARNED_ONCE = True

            # We have a back-up mechanism in case of unknown-length iterators.
            # If we progress over the same unknown length iterator more than once,
            # we will use its length from the previous launch.
            save_length_to_cache = True

            if id(iterator) in ITERATOR_LENGTH_CACHE:
                length = ITERATOR_LENGTH_CACHE[id(iterator)]
            else:
                length = 1
        else:
            save_length_to_cache = False
            length = length or len(iterator)

        t_last_printed = -float("inf")
        t_beginning = time.time()

        self.progress_bar_active = True

        idx = 0
        for idx, element in enumerate(iterator):
            if time.time() - t_last_printed > 1 / self.refresh_rate:

                # Reenable here, in case of nested progress bars
                self.progress_bar_active = True

                self._print(end="\r")
                s = time.time() - t_beginning
                throughput = idx / s if s > 0 else 0.0

                full_prefix = [" [", prefix]
                if show_throughput:
                    full_prefix.append(f"{throughput: <.2f} it/s")
                full_prefix.append("] ")
                full_prefix = "".join(full_prefix)
                full_prefix = full_prefix if full_prefix != " [] " else " "

                self._refresh_progress_bar = lambda: self._print_progress_bar(
                    idx,
                    length,
                    show_before=full_prefix,
                    embedded=self.embedded_progress_bar,
                )
                self._refresh_progress_bar()

                t_last_printed = time.time()
            yield element
        if save_length_to_cache:
            ITERATOR_LENGTH_CACHE[id(iterator)] = idx

        self.progress_bar_active = False
        self._print_row()

    def update_from_dict(self, dictionary):
        for key, value in dictionary.items():
            self.update(key, value)

    def update(self, key, value, *, weight=1):
        """Update value in the current row."""
        assert key in self.columns, f"Column '{key}' not in {self.columns}"

        if self._aggregate[key] == "sum":
            aggr_value = self._new_row[key] if self._aggregate_n[key] > 0 else 0
            self._new_row[key] = aggr_value + value * weight
            self._aggregate_n[key] += weight

        elif self._aggregate[key] == "mean":
            n = self._aggregate_n[key]
            aggr_value = self._new_row[key] if n > 0 else 0
            self._new_row[key] = (aggr_value * n + value * weight) / (n + weight)
            self._aggregate_n[key] += weight

        else:
            self._new_row[key] = value

        t0 = time.time()
        td = t0 - self._last_time_row_printed
        if self.print_row_on_update and td > 1 / self.refresh_rate:
            self._last_time_row_printed = t0

            if not self.progress_bar_active:
                self._print_row()
            elif self.embedded_progress_bar:
                self._refresh_progress_bar()

    def __setitem__(self, key, value):
        self.update(key, value, weight=1)

    def __getitem__(self, key):
        assert key in self.columns, f"Column '{key}' not in {self.columns}"

        return self._new_row[key]
