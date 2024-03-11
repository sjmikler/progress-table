#  Copyright (c) 2022 Szymon Mikler

from __future__ import annotations

import inspect
import logging
import math
import shutil
import sys
import time
import typing
from typing import Any, Callable, Dict, Iterable, List, Sized, Tuple, Type, Union

from colorama import Fore, Style

from . import styles

ALL_COLOR_NAME = [x for x in dir(Fore) if not x.startswith("__")]
ALL_STYLE_NAME = [x for x in dir(Style) if not x.startswith("__")]
ALL_COLOR_STYLE_NAME = ALL_COLOR_NAME + ALL_STYLE_NAME

ALL_COLOR = [getattr(Fore, x) for x in ALL_COLOR_NAME]
ALL_STYLE = [getattr(Style, x) for x in ALL_STYLE_NAME]
ALL_COLOR_STYLE = ALL_COLOR + ALL_STYLE

COLORAMA_TRANSLATE = {
    "bold": "bright",
}

NoneType = type(None)
ColorFormat = Union[str, Tuple, List, NoneType]
ColorFormatTuple = (str, Tuple, List, NoneType)

EPS = 1e-9
CURSOR_UP = "\033[A"
MAX_ACITVE_PBARS = 10

################
## V2 version ##
################


def aggregate_dont(new_value, old_value, n):
    return new_value


def aggregate_mean(new_value, old_value, n):
    return (old_value * n + new_value) / (n + 1)


def aggregate_sum(new_value, old_value, n):
    return old_value + new_value


def aggregate_max(new_value, old_value, n):
    return max(old_value, new_value)


def aggregate_min(new_value, old_value, n):
    return min(old_value, new_value)


def get_aggregate_fn(aggregate: str | Callable | None):
    """Get the aggregate function from the provided value."""

    if aggregate is None:
        return aggregate_dont

    if callable(aggregate):
        assert len(inspect.signature(aggregate).parameters) == 3, "Aggregate function has to take 3 arguments"
        return aggregate

    if isinstance(aggregate, str):
        if aggregate == "mean":
            return aggregate_mean
        elif aggregate == "sum":
            return aggregate_sum
        elif aggregate == "max":
            return aggregate_max
        elif aggregate == "min":
            return aggregate_min
        else:
            raise ValueError(f"Unknown aggregate type string: {aggregate}")
    else:
        raise ValueError(f"Unknown aggregate type: {type(aggregate)}")


def maybe_convert_to_colorama_str(color: str) -> str:
    # Translation layer to fix unintuitive colorama names
    color = COLORAMA_TRANSLATE.get(color.lower(), color)

    if isinstance(color, str):
        if hasattr(Fore, color.upper()):
            return getattr(Fore, color.upper())
        if hasattr(Style, color.upper()):
            return getattr(Style, color.upper())

    assert color in ALL_COLOR_STYLE, f"Color {color!r} incorrect! Available: {' '.join(ALL_COLOR_STYLE_NAME)}"
    return color


def maybe_convert_to_colorama(color: ColorFormat) -> str:
    if color is None:
        return ""
    if isinstance(color, str):
        color = color.split(" ")
    results = [maybe_convert_to_colorama_str(x) for x in color]
    return "".join(results)


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


class ProgressTableV1:
    DEFAULT_COLUMN_WIDTH = 8
    DEFAULT_COLUMN_COLOR = None
    DEFAULT_COLUMN_ALIGNMENT = "center"
    DEFAULT_COLUMN_AGGREGATE = None
    DEFAULT_ROW_COLOR = None

    def __init__(
        self,
        columns: Tuple | List = (),
        refresh_rate: int = 20,
        num_decimal_places: int = 4,
        default_column_width: int | None = None,
        default_column_color: ColorFormat = None,
        default_column_alignment: str | None = None,
        default_column_aggregate: str | None = None,
        default_row_color: ColorFormat = None,
        embedded_progress_bar: bool = True,
        pbar_show_throughput: bool = True,
        pbar_show_progress: bool = False,
        print_row_on_update: bool = True,
        reprint_header_every_n_rows: int = 30,
        custom_format: Callable[[Any], Any] | None = None,
        table_style: str | Type[styles.StyleNormal] = "round",
        file=None,
    ):
        """Progress Table instance.

        Columns can be specified using `add_column` method, but they can be added on the fly as well.
        Use `next_row` method to display the current row and reset the values for the next row.

        Example:
            >>> table = ProgressTableV1()
            >>> table.add_column("b", width=10)
            >>> table["a"] = 1
            >>> table["b"] = "xyz"
            >>> table.next_row()

        Args:
            columns: Columns that will be displayed in the header. Columns can be provided directly in `__init__` or through methods
                     `add_column` and `add_columns`. Columns added through `__init__` will have default settings like alignment,
                     color and width, while columns added through methods can have those customized.
            refresh_rate: The maximal number of times per second the last row of the Table will be refreshed.
                          This applies only when using Progress Bar or when `print_row_on_update = True`.
            num_decimal_places: This is only applicable when using the default formatting. This won't be used if `custom_format` is set.
                                If applicable, for every displayed value except integers there will be an attempt to round it.
            default_column_color: Color of the header and the data in the column.
                                  This can be overwritten in columns by using an argument in `add_column` method.
            default_column_width: Width of the column excluding cell padding.
                                  This can be overwritten in columns by using an argument in `add_column` method.
            default_column_alignment: Alignment in the column. Can be aligned either to `left`, `right` or `center` (default).
                                      This can be overwritten by columns by using an argument in `add_column` method.
            default_column_aggregate: By default, there's no aggregation. But if this is for example 'mean', then after every update in
                                      the current row, the mean of the provided values will be displayed. Aggregated values is reset at
                                      every new row. This can be overwritten by columns by using an argument in `add_column` method.
            print_row_on_update: True by default. If False, the current row will be displayed only when it's ready.
                                 Row is considered ready after calling `.next_row` or `.close` methods.
            reprint_header_every_n_rows: 30 by default. When table has a lot of rows, it can be useful to remind what the header is.
                                         If True, hedaer will be displayed periodically after the selected number of rows. 0 to supress.
            custom_format: A function that allows specyfing custom formatting for values in cells. This function should be universal and
                           work for all datatypes as inputs. It takes one value as an input and returns one value as an output.
            embedded_progress_bar: True by default. If True, changes the way the progress bar looks.
                                   Embedded version is more subtle, but does not prevent the current row
                                   from being displayed. If False, the progress bar covers the current
                                   row, preventing the user from seeing values that are being updated
                                   until the progress bar finishes.
            table_style: Change the borders of the table. Cause KeyError to see all the available styles.
            file: Redirect the output to another stream. There can be multiple streams at once passed as list or tuple.
                  Defaults to None, which is interpreted as stdout.
        """
        if isinstance(table_style, str):
            assert table_style in styles.PREDEFINED_STYLES, f"Style {table_style} unknown! Available: {' '.join(styles.PREDEFINED_STYLES)}"
            self.table_style = styles.PREDEFINED_STYLES[table_style]
        else:
            self.table_style = table_style

        assert isinstance(default_row_color, ColorFormatTuple), "Row color has to be a color format!"
        assert isinstance(default_column_color, ColorFormatTuple), "Column color has to be a color format!"

        # Default values for column and
        self.column_width = default_column_width
        self.column_color = default_column_color
        self.column_alignment = default_column_alignment
        self.column_aggregate = default_column_aggregate
        self.row_color = default_row_color

        # We are storing column configs
        self.column_widths: dict[str, int] = {}
        self.column_colors: dict[str, str] = {}
        self.column_alignments: dict[str, str] = {}
        self.column_aggregates: dict[str, Callable] = {}
        self.column_names: list[str] = []  # Names serve as keys for column configs

        # We are storing row configs
        self.row_colors: dict[str, str] = {}
        self.finished_rows: list[dict[str, Any]] = []

        self._new_row: dict[str, Any] = {}
        self.new_row_cumulated_weight: dict[str, int] = {}
        self.files = (file,) if not isinstance(file, (list, tuple)) else file

        self.previous_header_counter = 0
        assert reprint_header_every_n_rows > 0, "Reprint header every n rows has to be positive!"
        self.reprint_header_every_n_rows = reprint_header_every_n_rows

        # Various flags for table flow
        self._request_header = True
        self._request_splitter = False
        self._active_pbars: dict[int, TableProgressBar] = {}

        self.custom_format = custom_format or get_default_format_func(num_decimal_places)
        self.embedded_progress_bar: bool = embedded_progress_bar
        self.pbar_show_throughput: bool = pbar_show_throughput
        self.pbar_show_progress: bool = pbar_show_progress
        self.print_row_on_update: bool = print_row_on_update
        self.refresh_rate: int = refresh_rate

        self._last_time_row_printed = -float("inf")
        self._refresh_progress_bar: Callable = lambda: None
        self._is_table_opened = False

        for column in columns:
            self.add_column(column)

    def add_column(
        self,
        name: str,
        *,
        width=None,
        color=None,
        alignment=None,
        aggregate=None,
    ):
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
                       displayed. Aggregated values is reset at every new row.
        """
        assert isinstance(name, str), f"Column name has to be a string, not {type(name)}!"
        if name in self.column_names:
            logging.info(f"Column '{name}' already exists!")
        else:
            self.column_names.append(name)

        resolved_width = width or self.column_width or self.DEFAULT_COLUMN_WIDTH
        if not width and resolved_width < len(str(name)):
            resolved_width = len(str(name))
        self.column_widths[name] = resolved_width
        self.column_colors[name] = maybe_convert_to_colorama(color or self.column_color or self.DEFAULT_COLUMN_COLOR)
        self.column_alignments[name] = alignment or self.column_alignment or self.DEFAULT_COLUMN_ALIGNMENT
        self.column_aggregates[name] = get_aggregate_fn(aggregate or self.column_aggregate or self.DEFAULT_COLUMN_AGGREGATE)

        # Columns might be added later - in this case we need to reprint header
        self._request_header = True
        self._is_table_opened = False

        # Initialize color for the column in the new row
        self._prepare_row_color_dict()

    def add_columns(self, iterable, **kwds):
        """Add multiple columns to the table."""
        for column in iterable:
            self.add_column(column, **kwds)

    def update(self, key, value, *, weight=1):
        """Update value in the current row."""
        if key not in self.column_names:
            if self._is_table_opened:
                logging.info("Closing table (new column added to opened table)")
                self.close(close_pbars=False)

            self.add_column(key)

        # Set default values for new rows
        self._new_row.setdefault(key, 0)
        self.new_row_cumulated_weight.setdefault(key, 0)

        fn = self.column_aggregates[key]
        self._new_row[key] = fn(value, self._new_row[key], self.new_row_cumulated_weight[key])
        self.new_row_cumulated_weight[key] += weight

        t0 = time.time()
        td = t0 - self._last_time_row_printed
        if self._is_table_opened:
            if self.print_row_on_update and td > 1 / self.refresh_rate:
                self._last_time_row_printed = t0
                self._display_new_row_or_pbar()

    def update_from_dict(self, dictionary):
        """Update multiple values in the current row."""
        for key, value in dictionary.items():
            self.update(key, value)

    def __setitem__(self, key, value):
        self.update(key, value, weight=1)

    def __getitem__(self, key):
        assert key in self.column_names, f"Column '{key}' not in {self.column_names}"

        return self._new_row[key]

    def reorder_columns(self, *column_names):
        if all(x == y for x, y in zip(column_names, self.column_names)):
            return

        logging.info("Closing table (reordering columns)")
        self.close(close_pbars=False)

        assert isinstance(column_names, (List, Tuple))
        assert all([x in self.column_names for x in column_names]), f"Columns {column_names} not in {self.column_names}"
        self.column_names = list(column_names)
        self.column_widths = {k: self.column_widths[k] for k in column_names}
        self.column_colors = {k: self.column_colors[k] for k in column_names}
        self.column_alignments = {k: self.column_alignments[k] for k in column_names}
        self.column_aggregates = {k: self.column_aggregates[k] for k in column_names}

    def _clear_line(self):
        row_str = self._get_row_str(coloring=False)
        self._print(len(row_str) * " ", end="\r")

    def write(self, *args, **kwds):
        """Write a message gracefully when the table is opened.

        Table will be closed, the message will be printed and the table will be opened again.
        """
        self.close(close_pbars=False, close_row=False)
        self._clear_line()
        self._print(*args, **kwds)
        self.print_header()

    def close(self, close_pbars=True, close_row=True):
        """End the table and close it."""
        if close_row and self._new_row:
            self.next_row()

        if close_pbars and self._active_pbars:
            for pbar in list(self._active_pbars.values()):
                pbar.close()

        if self._is_table_opened:
            self._is_table_opened = False
            self._request_header = True
            self._print_bar_bot()

    def to_list(self):
        """Convert to Python nested list."""
        all_columns = []
        for row in self.finished_rows:
            for col in row:
                if col not in all_columns:
                    all_columns.append(col)
        return [[row.get(col, None) for col in all_columns] for row in self.finished_rows]

    def to_numpy(self):
        """Convert to numpy array."""
        try:
            import numpy as np
        except ImportError:
            raise ImportError("Numpy is not installed!")
        return np.array(self.to_list())

    def to_df(self):
        """Convert to pandas DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas is not installed!")
        all_columns = []
        for row in self.finished_rows:
            for col in row:
                if col not in all_columns:
                    all_columns.append(col)
        return pd.DataFrame(self.to_list(), columns=all_columns)

    #####################
    ## DISPLAY HELPERS ##
    #####################

    def _print(self, *args, **kwds):
        for file in self.files:
            print(*args, **kwds, file=file or sys.stdout)

    def _print_bar(self, left: str, center: str, right: str):
        content_list: list[str] = []
        for column_name in self.column_names:
            content_list.append(self.table_style.horizontal * (self.column_widths[column_name] + 2))

        center = center.join(content_list)
        content = ["\r", left, center, right]
        self._print("".join(content), end="\n")

    def _print_bar_top(self):
        return self._print_bar(self.table_style.down_right, self.table_style.no_up, self.table_style.down_left)

    def _print_bar_bot(self):
        return self._print_bar(self.table_style.up_right, self.table_style.no_down, self.table_style.up_left)

    def _print_bar_mid(self):
        return self._print_bar(self.table_style.no_left, self.table_style.all, self.table_style.no_right)

    def _get_row_str(self, coloring: bool):
        content = []
        for column in self.column_names:
            value = self._new_row.get(column, "")
            value = self.custom_format(value)
            value = self._apply_cell_formatting(str_value=str(value), column_name=column, coloring=coloring)
            content.append(value)
        return "".join(["\r", self.table_style.vertical, self.table_style.vertical.join(content), self.table_style.vertical])

    def _display_new_row(self):
        row_str = self._get_row_str(coloring=True)
        self._print(row_str, end="\r")

    def _display_new_row_or_pbar(self):
        if self._active_pbars.get(0, None) is not None:
            self._active_pbars[0].display()  # Level 0 pbar is embedded into the row, if it exists we want to display it instead of a row
        else:
            self._display_new_row()

    @typing.no_type_check
    def _prepare_row_color_dict(self, color: ColorFormat | Dict[str, ColorFormat] = None):
        color = color or self.row_color or {}
        if isinstance(color, ColorFormatTuple):
            color = {column: color for column in self.column_names}

        color = {column: color.get(column) or self.DEFAULT_ROW_COLOR for column in self.column_names}
        color = {column: maybe_convert_to_colorama(color) for column, color in color.items()}
        self.row_colors = color

    def next_row(self, color: ColorFormat | Dict[str, ColorFormat] = None, split=False, header=False):
        """End the current row."""
        if header or self._request_header or self.previous_header_counter >= self.reprint_header_every_n_rows:
            self.print_header()
            split = False
        if split or self._request_splitter:
            self._print_splitter()

        self._prepare_row_color_dict(color)
        self._display_new_row()
        self._print()  # Insert a newline
        self._prepare_row_color_dict()
        self.previous_header_counter += 1

        # Reset the new row
        self.finished_rows.append(self._new_row)
        self._new_row = {}

        # Clear up the new row
        self._refresh_active_pbars()
        self._display_new_row_or_pbar()

    def add_row(self, *values, **kwds):
        """Mimicking rich.table behavior for adding rows in one call."""
        for key, value in zip(self.column_names, values):
            self.update(key, value)
        self.next_row(**kwds)

    def _apply_cell_formatting(self, str_value: str, column_name: str, coloring: bool):
        width = self.column_widths[column_name]
        alignment = self.column_alignments[column_name]

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
                self.table_style.cell_overflow if clipped else " ",
            ]
        )
        if coloring:
            reset = Style.RESET_ALL if (self.column_colors[column_name] or self.row_colors[column_name]) else ""
            str_value = f"{self.column_colors[column_name]}{self.row_colors[column_name]}{str_value}{reset}"
        return str_value

    def _print_splitter(self):
        self._print_bar_mid()
        self._request_splitter = False

    def print_header(self):
        if self._is_table_opened:
            self._print_bar_mid()
        else:
            self._print_bar_top()

        content = []
        for column in self.column_names:
            value = self._apply_cell_formatting(column, column, coloring=True)
            content.append(value)
        s = "".join(["\r", self.table_style.vertical, self.table_style.vertical.join(content), self.table_style.vertical])
        self._print(s)

        self._request_header = False
        self._request_splitter = False
        self._is_table_opened = True
        self.previous_header_counter = 0
        self._print_bar_mid()

    def _refresh_active_pbars(self):
        for pbar in self._active_pbars.values():
            if pbar:
                pbar.display()

    def pbar(
        self,
        iterable: Iterable | int | None = None,
        *range_args,
        level=None,
        total=None,
        refresh_rate=None,
        show_throughput=None,
        show_progress=None,
    ):
        """Create iterable progress bar object.

        Args:
            iterable: Iterable to iterate over. If None, it will be created from as range(iterable, *range_args).
            range_args: Optional arguments for range function.
            level: Level of the progress bar. If not provided, it will be set automatically.
            total: Total number of iterations. If not provided, it will be calculated from the length of the iterable.
            refresh_rate: The maximal number of times per second the progress bar will be refreshed.
            show_throughput: If True, the throughput will be displayed.
            show_progress: If True, the progress will be displayed.
        """
        if isinstance(iterable, int):
            iterable = range(iterable, *range_args)

        level = level if level is not None else (len(self._active_pbars) + 1 - self.embedded_progress_bar)
        total = total if total is not None else (len(iterable) if isinstance(iterable, Sized) else 0)

        pbar = TableProgressBar(
            iterable=iterable,
            table=self,
            total=total,
            level=level,
            refresh_rate=refresh_rate if refresh_rate is not None else self.refresh_rate,
            show_throughput=show_throughput if show_throughput is not None else self.pbar_show_throughput,
            show_progress=show_progress if show_progress is not None else self.pbar_show_progress,
        )
        self._active_pbars[level] = pbar

        if len(self._active_pbars) > MAX_ACITVE_PBARS:
            raise ValueError("Too many active pbars, remember to .close() old pbars!")
        return pbar

    def __call__(self, *args, **kwds):
        """Creates iterable progress bar object using .pbar method and returns it."""
        return self.pbar(*args, **kwds)


class TableProgressBar:
    def __init__(self, iterable, *, table, total, level, refresh_rate, show_throughput, show_progress):
        self.iterable: Iterable | None = iterable

        self._step: int = 0
        self._total: int = total
        self._creation_time: float = time.perf_counter()
        self._last_refresh_time: float = -float("inf")

        self.level: int = level
        self.table: ProgressTableV1 = table
        self.refresh_rate: int = refresh_rate
        self.show_progress: bool = show_progress
        self.show_throughput: bool = show_throughput
        self._is_active: bool = True

    def display(self):
        assert self._is_active, "Progress bar was closed!"

        is_embedded = self.level == 0
        terminal_width = shutil.get_terminal_size(fallback=(0, 0)).columns or float("inf")

        total = self._total
        step = min(self._step, total) if total else self._step

        self._last_refresh_time = time.perf_counter()
        time_passed = self._last_refresh_time - self._creation_time
        throughput = self._step / time_passed if time_passed > 0 else 0.0

        inside_infobar = []
        if self.show_throughput:
            inside_infobar.append(f"{throughput: <.2f} it/s")
        if self.show_progress:
            if self._total:
                inside_infobar.append(f"{self._step}/{self._total}")
            else:
                inside_infobar.append(f"{self._step}")
        infobar = "[" + ", ".join(inside_infobar) + "] " if inside_infobar else ""

        pbar = ["\n" * self.level]
        if not is_embedded:
            tot_width = sum(self.table.column_widths.values()) + 3 * (len(self.table.column_widths) - 1) + 2
            if tot_width >= terminal_width - 1:
                tot_width = terminal_width - 2

            tot_width = tot_width - len(infobar)
            if not self._total:
                total = tot_width
                step = self._step % total

            num_filled = math.ceil(step / total * tot_width)
            num_empty = tot_width - num_filled

            pbar.extend(
                [
                    self.table.table_style.vertical,
                    infobar,
                    self.table.table_style.pbar_filled * num_filled,
                    self.table.table_style.pbar_empty * num_empty,
                    self.table.table_style.vertical,
                ]
            )
        else:
            row = self.table._get_row_str(coloring=False)
            pbar.extend(row[:2] + infobar)
            row = row[2 + len(infobar) :]

            if not self._total:  # When total is unknown
                total = len(row)
                step = self._step % total

            new_row = []
            for letter_idx, letter in enumerate(row):
                if letter == " ":
                    if letter_idx / len(row) <= (step / total) % (1 + EPS):
                        letter = self.table.table_style.embedded_pbar_filled
                    elif (letter_idx - 1) / len(row) <= (step / total) % (1 + EPS):
                        letter = self.table.table_style.embedded_pbar_head
                new_row.append(letter)
            pbar.extend(new_row)
        pbar.append(CURSOR_UP * self.level)
        self.table._print("".join(pbar), end="\r")

    def _update(self, n):
        self._step += n

    def update(self, n=1):
        self._update(n)
        time_passed = time.perf_counter() - self._last_refresh_time
        if self.table._is_table_opened and time_passed >= 1 / self.refresh_rate:
            self.display()

    def __iter__(self):
        try:
            assert self.iterable is not None, "No iterable provided!"
            self.update(0)
            for element in self.iterable:
                yield element
                self.update()
        finally:
            self.close()

    def close(self):
        self.table._active_pbars.pop(self.level)
        self._is_active = False
