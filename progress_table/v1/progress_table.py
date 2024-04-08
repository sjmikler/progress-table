#  Copyright (c) 2022-2024 Szymon Mikler

from __future__ import annotations

import inspect
import logging
import math
import shutil
import sys
import time
import typing
from dataclasses import dataclass
from threading import Thread
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


@dataclass
class ROW:
    VALUES: dict[str, Any]
    WEIGHTS: dict[str, float]
    COLORS: dict[str, str]


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
        pbar_show_throughput: bool = True,
        pbar_show_progress: bool = False,
        print_row_on_update: bool = True,
        reprint_header_every_n_rows: int = 30,
        custom_cell_format: Callable[[Any], Any] | None = None,
        table_style: str | Type[styles.StyleNormal] = "round",
        file=None,
        interactive: int = 2,
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
            num_decimal_places: This is only applicable when using the default formatting. This won't be used if `custom_cell_format` is set.
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
            custom_cell_format: A function that allows specyfing custom formatting for values in cells. This function should be universal and
                           work for all datatypes as inputs. It takes one value as an input and returns one value as an output.
            embedded_progress_bar: True by default. If True, the first progress bar will be embedded in the row.
                                   Non-embedded progress bars are displayed below the table - might not work well with some terminals.
            table_style: Change the borders of the table. Cause KeyError to see all the available styles.
            file: Redirect the output to another stream. There can be multiple streams at once passed as list or tuple.
                  Defaults to None, which is interpreted as stdout.
        """
        if isinstance(table_style, str):
            assert table_style in styles.PREDEFINED_STYLES, f"Style {table_style} unknown! Available: {' '.join(styles.PREDEFINED_STYLES)}"
            self.table_style = styles.PREDEFINED_STYLES[table_style]
        else:
            self.table_style = table_style

        assert isinstance(default_row_color, ColorFormatTuple), "Row color has to be a color format!"  # type: ignore
        assert isinstance(default_column_color, ColorFormatTuple), "Column color has to be a color format!"  # type: ignore

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

        self.display_rows = []
        self.data_rows: list[ROW] = []
        self.updated_display_rows: list[int] = []
        self.files = (file,) if not isinstance(file, (list, tuple)) else file

        assert reprint_header_every_n_rows > 0, "Reprint header every n rows has to be positive!"
        self.reprint_header_every_n_rows = reprint_header_every_n_rows
        self.previous_header_counter = 0

        self._active_pbars: dict[int, TableProgressBar] = {}

        self.custom_cell_format = custom_cell_format or get_default_format_func(num_decimal_places)
        self.pbar_show_throughput: bool = pbar_show_throughput
        self.pbar_show_progress: bool = pbar_show_progress
        self.print_row_on_update: bool = print_row_on_update
        self.refresh_rate: int = refresh_rate

        self._last_time_refresh = -float("inf")
        self._is_table_opened = False

        for column in columns:
            self.add_column(column)

        self.CURSOR_ROW = 0
        self.RENDERING_ON = False
        self.NEXT_ROW_PENDING: tuple | None = None
        self.message_queue = []

        # Interactivity settings
        self.interactive = int(interactive)
        assert self.interactive in (2, 1, 0)
        self.max_active_pbars = 10 if interactive == 2 else 1
        self.embedded_progress_bar = False if interactive == 2 else True

    def render_loop(self):
        idle_time = 1 / self.refresh_rate
        while self.RENDERING_ON:
            self.render_updated()
            self._refresh_active_pbars()
            time.sleep(idle_time)

    def start_rendering(self):
        self.RENDERING_ON = True
        self.NEXT_ROW_PENDING = (False, True)

        if self.interactive > 0:
            self.render_thread = Thread(target=self.render_loop, daemon=True)
            self.render_thread.start()

    def close(self):
        self.RENDERING_ON = False
        if self.interactive > 0:
            self.render_thread.join(timeout=1.0)
        self.add_display_row("SPLIT BOT")
        self.render_updated()
        self.freeze_view()

    def add_display_row(self, element):
        self.updated_display_rows.append(len(self.display_rows))
        self.display_rows.append(element)

    def add_empty_row(self, split=False, header=False):
        if header:
            self.add_display_row("SPLIT TOP")
            self.add_display_row("HEADER")
            self.add_display_row("SPLIT MID")
        elif split:
            self.add_display_row("SPLIT MID")

        row = ROW(VALUES={}, WEIGHTS={}, COLORS={})
        self.add_display_row(len(self.data_rows))
        self.data_rows.append(row)

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

        You can re-add an existing column to modify its properties.

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

        if self.interactive < 2 and self.RENDERING_ON:
            raise Exception("Cannot add new columns when table display started when interactive < 2!")

        resolved_width = width or self.column_width or self.DEFAULT_COLUMN_WIDTH
        if not width and resolved_width < len(str(name)):
            resolved_width = len(str(name))
        self.column_widths[name] = resolved_width
        self.column_colors[name] = maybe_convert_to_colorama(color or self.column_color or self.DEFAULT_COLUMN_COLOR)
        self.column_alignments[name] = alignment or self.column_alignment or self.DEFAULT_COLUMN_ALIGNMENT
        self.column_aggregates[name] = get_aggregate_fn(aggregate or self.column_aggregate or self.DEFAULT_COLUMN_AGGREGATE)
        self.invalidate_displayed_rows()

    def add_columns(self, *columns, **kwds):
        """Add multiple columns to the table.

        Args:
            columns: Names of the columns.
            kwds: Additional arguments for the columns. Column properties will be identical for all added columns.
        """
        for column in columns:
            self.add_column(column, **kwds)

    def reorder_columns(self, *column_names):
        """Reorder columns in the table."""
        if all(x == y for x, y in zip(column_names, self.column_names)):
            return

        logging.info("Closing table (reordering columns)")
        # self.close(close_pbars=False, close_row=False)

        assert isinstance(column_names, (List, Tuple))
        assert all([x in self.column_names for x in column_names]), f"Columns {column_names} not in {self.column_names}"
        self.column_names = list(column_names)
        self.column_widths = {k: self.column_widths[k] for k in column_names}
        self.column_colors = {k: self.column_colors[k] for k in column_names}
        self.column_alignments = {k: self.column_alignments[k] for k in column_names}
        self.column_aggregates = {k: self.column_aggregates[k] for k in column_names}
        self.invalidate_displayed_rows()

    def add_pending_row(self):
        self.add_empty_row(*self.NEXT_ROW_PENDING)
        self.NEXT_ROW_PENDING = None

    def update(self, key, value, *, row=-1, weight=1, **column_kwds):
        """Update value in the current row. This is extends capabilities of __setitem__.

        Args:
            key: Name of the column.
            value: Value to be set.
            row: Index of the row. By default, it's the last row.
            weight: Weight of the value. This is used for aggregation.
            column_kwds: Additional arguments for the column. They will be only used for column creation.
                         If column already exists, they will have no effect.
        """
        if not self.RENDERING_ON:
            self.start_rendering()

        if key not in self.column_names:
            self.add_column(key, **column_kwds)

        num_rows = len(self.data_rows)
        if self.NEXT_ROW_PENDING is not None:
            num_rows += 1
        data_row_index = row if row >= 0 else num_rows + row

        if data_row_index == len(self.data_rows):
            assert self.NEXT_ROW_PENDING is not None
            self.add_pending_row()
        if data_row_index >= len(self.data_rows):
            raise ValueError(f"Row {data_row_index} out of range! Number of rows: {len(self.data_rows)}")

        display_row_index = self.display_rows.index(data_row_index)
        self.updated_display_rows.append(display_row_index)

        # Set default values for new rows
        row = self.data_rows[row]
        row.VALUES.setdefault(key, 0)
        row.WEIGHTS.setdefault(key, 0)

        fn = self.column_aggregates[key]
        row.VALUES[key] = fn(value, row.VALUES[key], row.WEIGHTS[key])
        row.WEIGHTS[key] += weight

    def update_from_dict(self, dictionary):
        """Update multiple values in the current row."""
        for key, value in dictionary.items():
            self.update(key, value)

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            row, key = key
        else:
            row = -1
        self.update(key, value, row=row, weight=1)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            row, key = key
        else:
            row = -1

        assert key in self.column_names, f"Column '{key}' not in {self.column_names}"
        return self.data_rows[row].VALUES[key]

    def next_row(self, color: ColorFormat | Dict[str, ColorFormat] = None, split=False, header=False):
        """End the current row."""
        if self.previous_header_counter >= self.reprint_header_every_n_rows:
            # Force header if it wasn't printed for a long time
            header = True

        row = self.data_rows[-1]

        # Color is applied to the existing row - not the new one!
        row.COLORS.update(self._prepare_row_color_dict(color))
        self.NEXT_ROW_PENDING = (split, header)

        if self.interactive == 0:
            self.render_updated()

    def num_rows(self):
        return len(self.data_rows) + int(self.NEXT_ROW_PENDING is not None)

    def add_row(self, *values, **kwds):
        """Mimicking rich.table behavior for adding rows in one call."""
        for key, value in zip(self.column_names, values):
            self.update(key, value)
        self.next_row(**kwds)

    def move_cursor(self, row_index):
        if row_index < 0:
            row_index = len(self.display_rows) + row_index
        offset = self.CURSOR_ROW - row_index

        if offset > 0:
            self._print(CURSOR_UP * offset, end="")
        else:
            offset = -offset
            self._print("\n" * offset, end="")
        self.CURSOR_ROW = row_index

    def render_selected_rows(self, selected_rows: list[int]):
        for row_index in selected_rows:
            item = self.display_rows[row_index]
            if isinstance(item, int):
                row = self.data_rows[item]
                row_str = self._get_row_str(row)
            elif item == "HEADER":
                row_str = self._get_header()
            elif item == "SPLIT TOP":
                row_str = self._get_bar_top()
            elif item == "SPLIT BOT":
                row_str = self._get_bar_bot()
            elif item == "SPLIT MID":
                row_str = self._get_bar_mid()
            elif isinstance(item, tuple) and len(item) > 0 and item[0] == "CUSTOM WRITE":
                row_str = item[1]
            else:
                raise ValueError(f"Unknown item: {item}")

            self.move_cursor(row_index)
            self._print(row_str, end="\r")
        self.move_cursor(-1)

    def render_updated(self):
        if self.updated_display_rows:
            self.render_selected_rows(self.updated_display_rows)
            self.updated_display_rows = []

    def invalidate_displayed_rows(self):
        self.updated_display_rows = list(range(len(self.display_rows)))

    def freeze_view(self):
        self._print()
        self.CURSOR_ROW = 0
        self.display_rows = []
        self.updated_display_rows = []

    # def _clear_line(self):
    #     row_str = self._get_row_str(coloring=False)
    #     self._print(len(row_str) * " ", end="\r")
    #
    def write(self, *args, sep=" "):
        """Write a message gracefully when the table is opened."""
        full_message = []
        for arg in args:
            full_message.append(str(arg))
        full_message = sep.join(full_message)
        message_lines = full_message.split("\n")
        for line in message_lines:
            self.add_display_row(("CUSTOM WRITE", line))

    #
    # def to_list(self):
    #     """Convert to Python nested list."""
    #     all_columns = []
    #     for row in self.rows:
    #         for col in row:
    #             if col not in all_columns:
    #                 all_columns.append(col)
    #     return [[row.get(col, None) for col in all_columns] for row in self.rows]
    #
    # def to_numpy(self):
    #     """Convert to numpy array."""
    #     try:
    #         import numpy as np
    #     except ImportError:
    #         raise ImportError("Numpy is not installed!")
    #     return np.array(self.to_list())
    #
    # def to_df(self):
    #     """Convert to pandas DataFrame."""
    #     try:
    #         import pandas as pd
    #     except ImportError:
    #         raise ImportError("Pandas is not installed!")
    #     all_columns = []
    #     for row in self.rows:
    #         for col in row:
    #             if col not in all_columns:
    #                 all_columns.append(col)
    #     return pd.DataFrame(self.to_list(), columns=all_columns)

    #####################
    ## DISPLAY HELPERS ##
    #####################

    def _print(self, *args, **kwds):
        for file in self.files:
            print(*args, **kwds, file=file or sys.stdout)

    def _get_row_str(self, row: ROW, colored=True):
        content = []
        for column in self.column_names:
            value = row.VALUES.get(column, "")
            value = self.custom_cell_format(value)

            color = row.COLORS.get(column, "") if colored else ""
            value = self._apply_cell_formatting(str_value=str(value), column_name=column, color=color)
            content.append(value)
        return "".join(["\r", self.table_style.vertical, self.table_style.vertical.join(content), self.table_style.vertical])

    def _get_bar(self, left: str, center: str, right: str):
        content_list: list[str] = []
        for column_name in self.column_names:
            content_list.append(self.table_style.horizontal * (self.column_widths[column_name] + 2))

        center = center.join(content_list)
        content = ["\r", left, center, right]
        return "".join(content)

    def _get_bar_top(self):
        return self._get_bar(self.table_style.down_right, self.table_style.no_up, self.table_style.down_left)

    def _get_bar_bot(self):
        return self._get_bar(self.table_style.up_right, self.table_style.no_down, self.table_style.up_left)

    def _get_bar_mid(self):
        return self._get_bar(self.table_style.no_left, self.table_style.all, self.table_style.no_right)

    @typing.no_type_check
    def _prepare_row_color_dict(self, color: ColorFormat | Dict[str, ColorFormat] = None):
        color = color or self.row_color or {}
        if isinstance(color, ColorFormatTuple):
            color = {column: color for column in self.column_names}

        color = {column: color.get(column) or self.DEFAULT_ROW_COLOR for column in self.column_names}
        color = {column: maybe_convert_to_colorama(color) for column, color in color.items()}
        color = {col: self.column_colors[col] + color[col] for col in color}
        return color

    def _apply_cell_formatting(self, str_value: str, column_name: str, color: str):
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
        reset = Style.RESET_ALL if color else ""
        str_value = f"{color}{str_value}{reset}"
        return str_value

    def _get_header(self):
        content = []
        for column in self.column_names:
            value = self._apply_cell_formatting(column, column, color=self.column_colors[column])
            content.append(value)
        s = "".join(["\r", self.table_style.vertical, self.table_style.vertical.join(content), self.table_style.vertical])
        return s

    def _refresh_active_pbars(self):
        for pbar_level in list(self._active_pbars):
            if pbar_level in self._active_pbars:
                pbar = self._active_pbars[pbar_level]
                if pbar:
                    pbar.display()

    def pbar(
        self,
        iterable: Iterable | int | None = None,
        *range_args,
        level=None,
        total=None,
        refresh_rate=None,
        description="",
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
            description: Custom description of the progress bar that will be shown as prefix.
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
            description=description,
            show_throughput=show_throughput if show_throughput is not None else self.pbar_show_throughput,
            show_progress=show_progress if show_progress is not None else self.pbar_show_progress,
        )
        self._active_pbars[level] = pbar

        if len(self._active_pbars) > self.max_active_pbars:
            raise ValueError("Too many active pbars, remember to .close() old pbars!")
        return pbar

    def __call__(self, *args, **kwds):
        """Creates iterable progress bar object using .pbar method and returns it."""
        return self.pbar(*args, **kwds)


class TableProgressBar:
    def __init__(self, iterable, *, table, total, level, refresh_rate, description, show_throughput, show_progress):
        self.iterable: Iterable | None = iterable

        self._step: int = 0
        self._total: int = total
        self._creation_time: float = time.perf_counter()
        self._last_refresh_time: float = -float("inf")

        self.level: int = level
        self.table: ProgressTableV1 = table
        self.refresh_rate: int = refresh_rate
        self.description: str = description
        self.show_progress: bool = show_progress
        self.show_throughput: bool = show_throughput
        self._is_active: bool = True
        self._last_pbar_width = 0

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
        if self.description:
            inside_infobar.append(self.description)
        if self.show_progress:
            if self._total:
                inside_infobar.append(f"{self._step}/{self._total}")
            else:
                inside_infobar.append(f"{self._step}")
        if self.show_throughput:
            inside_infobar.append(f"{throughput: <.2f} it/s")
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

            pbar_body = "".join(
                [
                    self.table.table_style.vertical,
                    infobar,
                    self.table.table_style.pbar_filled * num_filled,
                    self.table.table_style.pbar_empty * num_empty,
                    self.table.table_style.vertical,
                ]
            )
            pbar.append(pbar_body)
            self._last_pbar_width = len(pbar_body)
        else:
            if not self.table.display_rows or not isinstance(self.table.display_rows[-1], int):
                return

            row_idx = self.table.display_rows[-1]
            row = self.table.data_rows[row_idx]

            row_str = self.table._get_row_str(row, colored=False)
            pbar.extend(row_str[:2] + infobar)
            row_str = row_str[2 + len(infobar) :]

            if not self._total:  # When total is unknown
                total = len(row_str)
                step = self._step % total

            new_row = [Style.BRIGHT]
            for letter_idx, letter in enumerate(row_str):
                is_bar = letter_idx / len(row_str) <= (step / total) % (1 + EPS)
                is_head = (letter_idx - 1) / len(row_str) <= (step / total) % (1 + EPS)
                if letter == " " and is_bar:
                    letter = self.table.table_style.embedded_pbar_filled
                if letter == " " and is_head:
                    letter = self.table.table_style.embedded_pbar_head

                if not is_bar and not is_head:
                    new_row.append(Style.RESET_ALL)
                new_row.append(letter)
            pbar.extend(new_row)
        pbar.append(CURSOR_UP * self.level)
        self.table._print("".join(pbar), end="\r")

    def cleanup(self):
        pbar = ["\n" * self.level, " " * self._last_pbar_width, CURSOR_UP * self.level]
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
        self.cleanup()
