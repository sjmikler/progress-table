#  Copyright (c) 2022 Szymon Mikler

from __future__ import annotations

import inspect
import logging
import math
import shutil
import sys
import time
from builtins import KeyError, staticmethod
from collections import defaultdict
from typing import Any, Callable, Dict, List, Tuple

from colorama import Fore, Style

from . import symbols

ALL_COLOR_NAMES = [x for x in dir(Fore) if not x.startswith("__")]
ALL_STYLE_NAMES = [x for x in dir(Style) if not x.startswith("__")]
ALL_COLORS_STYLES_NAMES = ALL_COLOR_NAMES + ALL_STYLE_NAMES

ALL_COLORS = [getattr(Fore, x) for x in ALL_COLOR_NAMES]
ALL_STYLES = [getattr(Style, x) for x in ALL_STYLE_NAMES]
ALL_COLORS_STYLES = ALL_COLORS + ALL_STYLES

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
        table_style: str = "normal",
        file=sys.stdout,
    ):
        """Progress Table instance.

        Columns have to be specified before displaying the first row or launching a progress bar!

        Args:
            columns: Columns that will be displayed in the header. Columns can be provided directly in
                     `__init__` or through methods `add_column` and `add_columns`. Columns added through
                     `__init__` will have default settings like alignment, color and width, while
                     columns added through methods can have those customized.
            refresh_rate: The maximal number of times per second the last row of the Table will be refreshed.
                          This applies only when using Progress Bar or when `print_row_on_update = True`.
            num_decimal_places: This is only applicable when using the default formatting. This won't be used
                                if `custom_format` is set. If applicable, for every displayed value except
                                integers there will be an attempt to round it.
            default_column_width: Width of the column excluding cell padding. This can be overwritten by
                                  columns by using an argument in `add_column` method.
            default_column_alignment: Alignment in the column. Can be aligned either to `left`, `right` or
                                      `center` (default). This can be overwritten by columns by using
                                      an argument in `add_column` method.
            print_row_on_update: True by default. If False, the current row will be displayed only when
                                 it's ready. Row is considered ready after calling `.next_row` or `.close`
                                 methods.
            reprint_header_every_n_rows: 30 by default. When table has a lot of rows, it can be useful to
                                         remind what the header is. If True, hedaer will be displayed
                                         periodically after the selected number of rows. 0 to supress.
            custom_format: A function that allows specyfing custom formatting for values in cells.
                           This function should be universal and work for all datatypes as inputs.
                           It takes one value as an input and returns one value as an output.
            embedded_progress_bar: False by default. If True, changes the way the progress bar looks.
                                   Embedded version is more subtle, but does not prevent the current row
                                   from being displayed. If False, the progress bar covers the current
                                   row, preventing the user from seeing values that are being updated
                                   until the progress bar finishes.
            table_style: Change the borders of the table. Cause KeyError to see all the available styles.
            file: Redirect the output to another stream. There can be multiple streams at once passed as
                  a list or a tuple. Defaults to sys.stdout.
        """
        self.refresh_rate = refresh_rate
        self.default_width = default_column_width
        self.default_alignment = default_column_alignment
        self.print_row_on_update = print_row_on_update
        self.reprint_header_every_n_rows = reprint_header_every_n_rows
        self.custom_format = custom_format or self.get_default_format_func(num_decimal_places)
        self.embedded_progress_bar = embedded_progress_bar

        if not isinstance(file, list) and not isinstance(file, tuple):
            file = (file,)
        self.files = file

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
        self._needs_splitter = False

        self._last_row_content = None

        allowed_styles = [getattr(symbols, class_name) for class_name in dir(symbols)]
        allowed_styles = [x for x in allowed_styles if inspect.isclass(x) and issubclass(x, symbols.Symbols)]
        style_name_to_style = {x.name: x for x in allowed_styles if hasattr(x, "name")}

        if table_style in style_name_to_style:
            self._symbols = style_name_to_style[table_style]
        else:
            allowed_style_names = list(style_name_to_style)
            raise KeyError(f"Style '{table_style}' not in {allowed_style_names}!")

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

    def add_column(self, name, *, width=None, alignment=None, color=None, aggregate=None):
        """Add column to the table.

        Args:
            name: Name of the column. Will be displayed in the header.
            width: Width of the column. If width is smaller than the name, width will be automatically
                   increased to the smallest possible value. This means setting `width=0` will set the column
                   to the smallest possible width allowed by `name`.
            alignment: Alignment of the data in the column.
            color: Color of the header and the data in the column.
            aggregate: By default, there's no aggregation. But if this is for example 'mean', then
                       after every update in the current row, the mean of the provided values will be
                       displayed. Aggregation is reset at every new row.
        """
        assert not self.header_printed, "Columns cannot be modified after displaying the first row!"

        if name in self.columns:
            logging.info(f"Column '{name}' already exists!")
        else:
            self.columns.append(name)

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

        assert aggregate in [
            None,
            "mean",
            "sum",
            "max",
            "min",
        ], "Allowed aggregate types: [None, 'mean', 'sum', 'max', 'min']"
        self._aggregate[name] = aggregate

        width = width if width is not None else self.default_width
        if width < len(name):
            width = len(name)
        self._widths[name] = width

    def add_columns(self, iterable, **kwds):
        """Add multiple columns to the table."""
        for column in iterable:
            self.add_column(column, **kwds)

    def next_row(self, save=True, split=False, header=False):
        """End the current row."""
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

        if split:
            self._needs_splitter = True

        if header:
            self._print_header(top=False)

    def close(self):
        """End the table and close it."""
        self._needs_splitter = False

        self.next_row()
        self._print_bottom_bar()
        self.header_printed = False
        self._print()

    def to_list(self):
        """Convert to Python nested list."""
        return [[row[col] for col in self.columns] for row in self.finished_rows]

    def to_numpy(self):
        """Convert to numpy array."""
        import numpy as np

        return np.array(self.to_list())

    def to_df(self):
        """Convert to pandas DataFrame."""
        import pandas as pd

        return pd.DataFrame(self.to_list(), columns=self.columns)

    def display(self):
        """Display the whole table. Can be used after closing the table."""
        if self.header_printed:
            self.close()
        self._display_custom(self.to_list())

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

        elif self._aggregate[key] == "max":
            n = self._aggregate_n[key]
            aggr_value = self._new_row[key] if n > 0 else -float("inf")
            self._new_row[key] = max(aggr_value, value)
            self._aggregate_n[key] += 1

        elif self._aggregate[key] == "min":
            n = self._aggregate_n[key]
            aggr_value = self._new_row[key] if n > 0 else float("inf")
            self._new_row[key] = min(aggr_value, value)
            self._aggregate_n[key] += 1

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

    def update_from_dict(self, dictionary):
        """Update multiple values in the current row."""
        for key, value in dictionary.items():
            self.update(key, value)

    def _apply_cell_formatting(self, str_value: str, column: str):
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
        return self._bar_custom_center(left=self._symbols.no_left, center=symbols, right=self._symbols.down_left)

    def _print_top_bar(self):
        return self._bar(left=self._symbols.down_right, center=self._symbols.no_up, right=self._symbols.down_left)

    def _print_bottom_bar(self):
        return self._bar(left=self._symbols.up_right, center=self._symbols.no_down, right=self._symbols.up_left)

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
        assert (
            color in ALL_COLORS_STYLES
        ), f"Only colorama colors are allowed, not '{color_str}'! Available: {ALL_COLORS_STYLES_NAMES}"

    def _print_header(self, top=True):
        assert self.columns, "Columns are required! Use .add_column method or specify them in __init__!"

        self._needs_splitter = False

        if top:
            self._print_top_bar()
        else:
            self._print_center_bar()
        self._print()

        content = []
        for column in self.columns:
            value = self._apply_cell_formatting(column, column)
            content.append(value)
        s = "".join(["\r", self._symbols.vertical, self._symbols.vertical.join(content), self._symbols.vertical])
        self._print(s)

        self._last_header_printed_at_row_count = self.num_rows
        self.header_printed = True
        self._print_center_bar()
        self._print()
        self._last_row_content = "header"

    def _print_splitter(self):
        if self._last_row_content == "row":
            self._print_center_bar()
            self._print()

            self._needs_splitter = False
            self._last_row_content = "splitter"

    def _get_row(self):
        content = []
        for column in self.columns:
            value = self._new_row[column]
            value = self.custom_format(value)
            value = self._apply_cell_formatting(str_value=str(value), column=column)
            content.append(value)
        return "".join(["\r", self._symbols.vertical, self._symbols.vertical.join(content), self._symbols.vertical])

    def _print_row(self):
        if not self.header_printed:
            self._print_header(top=True)

        if self.reprint_header_every_n_rows != 0:
            if self.num_rows - self._last_header_printed_at_row_count >= self.reprint_header_every_n_rows:
                self._print_header(top=False)

        if self._needs_splitter:
            self._print_splitter()

        if len(self._new_row) == 0:
            return
        self._needs_line_ending = True
        self._print(self._get_row(), end="")

    def _print_progress_bar(self, i, n, show_before=" ", show_after=" ", embedded=False):
        i = min(i, n)  # clip the iteration number to be not bigger than the total number of iterations
        terminal_width = shutil.get_terminal_size(fallback=(0, 0)).columns or float("inf")

        if not embedded:
            tot_width = sum(self._widths.values()) + 3 * (len(self._widths) - 1) + 2
            if tot_width >= terminal_width - 1:
                tot_width = terminal_width - 2

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
            self._needs_splitter = False
            self._needs_line_ending = False
            self._last_row_content = "row"

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
        self._last_row_content = "close"

    def _print(self, *args, **kwds):
        for file in self.files:
            print(*args, **kwds, file=file)

    def __call__(self, iterator, *range_args, length=None, prefix="", show_throughput=True):
        """Display progress bar over the iterator. Try to figure out the iterator length."""
        global ITERATOR_LENGTH_UNKNOWN_WARNED_ONCE, ITERATOR_LENGTH_CACHE

        if not self.header_printed:
            self._print_header()

        if isinstance(iterator, int):
            iterator = range(iterator, *range_args)
        else:
            assert len(range_args) == 0, "Unnamed args are not allowed here!"

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

    def __setitem__(self, key, value):
        self.update(key, value, weight=1)

    def __getitem__(self, key):
        assert key in self.columns, f"Column '{key}' not in {self.columns}"

        return self._new_row[key]
