#  Copyright (c) 2022-2024 Szymon Mikler

from __future__ import annotations

import atexit
import inspect
import logging
import math
import os
import shutil
import sys
import time
from dataclasses import dataclass
from threading import Thread
from typing import Any, Callable, Iterable, Sized, Type, Union

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
ColorFormat = Union[str, tuple, list, NoneType]
ColorFormatTuple = (str, tuple, list, NoneType)

EPS = 1e-9
CURSOR_UP = "\033[A"

# Flags that indicate if the warning was already triggered
WARNED_PBAR_HIDDEN = False
WARNED_PBAR_NOT_EMBEDDED = False

################
## V2 version ##
################


def aggregate_dont(value, old_value, weight, old_weight):
    return value


def aggregate_mean(value, old_value, weight, old_weight):
    return (old_value * old_weight + value * weight) / (old_weight + weight)


def aggregate_sum(value, old_value, weight, old_weight):
    return old_value + value


def aggregate_max(value, old_value, weight, old_weight):
    return max(old_value, value)


def aggregate_min(value, old_value, weight, old_weight):
    return min(old_value, value)


def get_aggregate_fn(aggregate: None | str | Callable):
    """Get the aggregate function from the provided value."""

    if aggregate is None:
        return aggregate_dont

    if callable(aggregate):
        num_parameters = len(inspect.signature(aggregate).parameters)
        assert num_parameters == 4, f"Aggregate function has to take 4 arguments, not {num_parameters}!"
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
    if color is None or color == "":
        return ""
    if isinstance(color, str):
        color = color.split(" ")
    results = [maybe_convert_to_colorama_str(x) for x in color]
    return "".join(results)


def get_default_format_func(decimal_places):
    def fmt(x) -> str:
        if isinstance(x, int):
            return str(x)
        else:
            try:
                return format(x, f".{decimal_places}f")
            except Exception:
                return str(x)

    return fmt


@dataclass
class DATA_ROW:
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
        columns: tuple | list = (),
        interactive: int = os.environ.get("PTABLE_INTERACTIVE", 2),
        refresh_rate: int = 20,
        num_decimal_places: int = 4,
        default_column_width: int | None = None,
        default_column_color: ColorFormat = None,
        default_column_alignment: str | None = None,
        default_column_aggregate: str | None = None,
        default_row_color: ColorFormat = None,
        pbar_show_throughput: bool = True,
        pbar_show_progress: bool = True,
        pbar_show_percents: bool = False,
        pbar_show_eta: bool = False,
        pbar_embedded: bool = True,
        print_header_on_top: bool = True,
        print_header_every_n_rows: int = 30,
        custom_cell_format: Callable[[Any], str] | None = None,
        table_style: str | Type[styles.StyleNormal] = "round",
        file=None,
        # Deprecated arguments
        custom_format: None = None,
        embedded_progress_bar: None = None,
        print_row_on_update: None = None,
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
            interactive: Three interactivity levels are available: 2, 1 and 0. It's recommended to use 2, but some
                         terminal environments might not support it. If something breaks, try to decrease the interactivity.
                         On levels 2 and 1 a separate display thread is spawned. On level 2 you can modify rows above the current one.
                         On level 2 you can add columns on-the-fly or reorder them. You can use nested progress bars.
                         On level 1 you can only operate on the current row, the old rows are frozen, but you still get
                         to use a progress bar, albeit not nested. On level 0 there are no progress bars and rows are only
                         printed after calling `next_row`.
            refresh_rate: The maximal number of times per second the renderer will render updates in the table.
            num_decimal_places: This is only applicable when using the default formatting.
                                This won't be used if `custom_cell_repr` is set.
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
            default_row_color: Color of the row. This can be overwritten by using an argument in `next_row` method.
            pbar_show_throughput: Show throughput in the progress bar, for example `3.55 it/s`. Defaults to True.
            pbar_show_progress: Show progress in the progress bar, for example 10/40. Defaults to True.
            pbar_show_percents: Show percents in the progress bar, for example 25%. Defaults to False.
            pbar_show_eta: Show estimated time of finishing in the progress bar, for example 10s. Defaults to False.
            pbar_embedded: If True, changes the way the first (non-nested) progress bar looks.
                           Embedded version is more subtle, but does not prevent the current row from being displayed.
                           If False, the progress bar covers the current row, preventing the user from seeing values
                           that are being updated until the progress bar finishes. The default is True.
            print_header_every_n_rows: 30 by default. When table has a lot of rows, it can be useful to remind what the header is.
                                       If True, hedaer will be displayed periodically after the selected number of rows. 0 to supress.
            custom_cell_format: A function that defines how to get str value to display from a cell content.
                                This function should be universal and work for all datatypes as inputs.
                                It takes one value as an input and returns string as an output.
            table_style: Change the borders of the table. Cause KeyError to see all the available styles.
            file: Redirect the output to another stream. There can be multiple streams at once passed as list or tuple.
                  Defaults to None, which is interpreted as stdout.
        """
        # Deprecation handling
        if custom_format is not None:
            logging.warning("Argument `custom_format` is deprecated. Use `custom_cell_format` instead!")
        if embedded_progress_bar is not None:
            logging.warning("Argument `embedded_progress_bar` is deprecated. Use `pbar_embedded` instead!")
        if print_row_on_update is not None:
            logging.warning("Argument `print_row_on_update` is deprecated. Specify `interactive` instead!")

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
        self._closed = False

        self.files = (file,) if not isinstance(file, (list, tuple)) else file

        assert print_header_every_n_rows > 0, "Reprint header every n rows has to be positive!"
        self._print_header_on_top = print_header_on_top
        self._print_header_every_n_rows = print_header_every_n_rows
        self._previous_header_row_number = 0

        self._data_rows: list[DATA_ROW] = []
        self._display_rows: list[str | int] = []
        self._pending_display_rows: list[int] = []
        self._active_pbars: list[TableProgressBar] = []
        self._latest_row_decorations: list = ["SPLIT TOP"]
        if self._print_header_on_top:
            self._latest_row_decorations.append("HEADER")
            self._latest_row_decorations.append("SPLIT MID")

        self.custom_cell_format = custom_cell_format or get_default_format_func(num_decimal_places)
        self.pbar_show_throughput: bool = pbar_show_throughput
        self.pbar_show_progress: bool = pbar_show_progress
        self.pbar_show_percents: bool = pbar_show_percents
        self.pbar_show_eta: bool = pbar_show_eta
        self.pbar_embedded: bool = pbar_embedded

        self.refresh_rate: int = refresh_rate

        self._CURSOR_ROW = 0
        self._RENDERER_RUNNING = False

        # Interactivity settings
        self.interactive = int(interactive)
        assert self.interactive in (2, 1, 0)

        self._printing_buffer: list[str] = []
        self._renderer: Thread | None = None

        # Making function calls after init
        self.add_columns(*columns)
        self._append_new_empty_data_row()
        self._at_indexer = TableAtIndexer(self)

        # Close the table at program exit
        atexit.register(self.close)

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

        You can re-add existing columns to modify their properties.

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
        self._set_all_display_rows_as_pending()

    def add_columns(self, *columns, **kwds):
        """Add multiple columns to the table.

        This can be an integer - then the given number of columns will be created.

        Args:
            columns: Names of the columns or a number of columns to create.
            kwds: Additional arguments for the columns. Column properties will be identical for all added columns.
        """
        # Create the given number of columns
        if len(columns) == 1 and isinstance(columns[0], int):
            num_to_create = columns[0]
            col_idx = 0
            while num_to_create > 0:
                column_name = str(col_idx)
                if column_name not in self.column_names:
                    self.add_column(column_name, **kwds)
                    num_to_create -= 1
                col_idx += 1
        else:
            for column in columns:
                self.add_column(column, **kwds)

    def reorder_columns(self, *column_names):
        """Reorder columns in the table."""
        if all(x == y for x, y in zip(column_names, self.column_names)):
            return

        if self.interactive < 2 and self._RENDERER_RUNNING:
            raise Exception("Cannot reorder columns when table display started if interactive < 2!")

        assert isinstance(column_names, (list, tuple))
        assert all([x in self.column_names for x in column_names]), f"Columns {column_names} not in {self.column_names}"
        self.column_names = list(column_names)
        self.column_widths = {k: self.column_widths[k] for k in column_names}
        self.column_colors = {k: self.column_colors[k] for k in column_names}
        self.column_alignments = {k: self.column_alignments[k] for k in column_names}
        self.column_aggregates = {k: self.column_aggregates[k] for k in column_names}
        self._set_all_display_rows_as_pending()

    def update(self, name, value, *, row=-1, weight=1, cell_color=None, **column_kwds):
        """Update value in the current row. This is extends capabilities of __setitem__.

        Args:
            name: Name of the column.
            value: Value to be set.
            row: Index of the row. By default, it's the last row.
            weight: Weight of the value. This is used for aggregation.
            cell_color: Optionally override color for specific cell, independent from rows and columns.
            column_kwds: Additional arguments for the column. They will be only used for column creation.
                         If column already exists, they will have no effect.
        """
        if name not in self.column_names:
            self.add_column(name, **column_kwds)

        data_row_index = row if row >= 0 else len(self._data_rows) + row
        if data_row_index >= len(self._data_rows):
            raise ValueError(f"Row {data_row_index} out of range! Number of rows: {len(self._data_rows)}")

        # Set default values for new rows
        data_row = self._data_rows[row]
        data_row.VALUES.setdefault(name, 0)
        data_row.WEIGHTS.setdefault(name, 0)

        fn = self.column_aggregates[name]
        data_row.VALUES[name] = fn(value, data_row.VALUES[name], weight, data_row.WEIGHTS[name])
        data_row.WEIGHTS[name] += weight

        if cell_color is not None:
            data_row.COLORS[name] = maybe_convert_to_colorama(cell_color)
        self._append_or_update_display_row(data_row_index)

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            name, row = key
            if isinstance(name, int) and isinstance(row, str):
                name, row = row, name
        else:
            name = key
            row = -1
        assert isinstance(row, int), f"Row {row} has to be an integer, not {type(row)}!"
        self.update(name, value, row=row, weight=1)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            name, row = key
            if isinstance(name, int) and isinstance(row, int):
                name, row = row, name
        else:
            name = key
            row = -1
        assert name in self.column_names, f"Column {name} not in {self.column_names}"
        assert isinstance(row, int), f"Row {row} has to be an integer, not {type(row)}!"
        return self._data_rows[row].VALUES.get(key, None)

    def update_from_dict(self, dictionary):
        """Update multiple values in the current row."""
        for key, value in dictionary.items():
            self.update(key, value)

    @property
    def at(self):
        """Advanced indexing for the table."""
        return self._at_indexer

    def next_row(self, color: ColorFormat | dict[str, ColorFormat] = None, split: bool | None = None, header: bool | None = None):
        """End the current row."""

        # Force header if it wasn't printed for a long time
        if header is None and len(self._data_rows) - self._previous_header_row_number >= self._print_header_every_n_rows:
            header = True
        header = header or False
        split = split or False

        row = self._data_rows[-1]
        data_row_index = len(self._data_rows) - 1

        # Color is applied to the existing row - not the new one!
        row.COLORS.update(self._resolve_row_color_dict(color))

        # Refresh row is necessary to apply colors
        self._append_or_update_display_row(data_row_index)

        self._append_new_empty_data_row()
        self._latest_row_decorations = []
        if header:
            self._previous_header_row_number = len(self._data_rows)
            self._latest_row_decorations.extend(["SPLIT MID", "HEADER", "SPLIT MID"])
        elif split:
            self._latest_row_decorations.append("SPLIT MID")

        # There's no renderer thread when interactive==0, so we force refresh after every row
        if self.interactive == 0:
            self._print_pending_rows_to_buffer()
            self._flush_buffer()

    def add_row(self, *values, **kwds):
        """Mimicking rich.table behavior for adding whole rows in one call without providing names."""
        for key, value in zip(self.column_names, values):
            self.update(key, value)
        self.next_row(**kwds)

    def add_rows(self, *rows, **kwds):
        """Like `add_row`, but for multiple rows at once.

        Optionally, it accepts an integer as the first argument, which will create that number of empty rows.
        """
        if len(rows) == 1 and isinstance(rows[0], int):
            rows = [{} for _ in range(rows[0])]

        for row in rows:
            self.add_row(*row, **kwds)

    def num_rows(self):
        return len(self._data_rows)

    def num_columns(self):
        return len(self.column_names)

    def close(self):
        """Closes the table visually, removes the renderer thread. Closed table cannot be updated anymore."""
        if self._closed:
            return

        # Closing opened table
        if "SPLIT TOP" in self._display_rows:
            self._append_or_update_display_row("SPLIT BOT")

        self._RENDERER_RUNNING = False
        if self._renderer is not None and self._renderer.is_alive():
            self._renderer.join(timeout=1 / self.refresh_rate)
        self._renderer = None

        self._print_pending_rows_to_buffer()
        self._printing_buffer.append("\n")
        self._flush_buffer()
        self._freeze_view()
        self._closed = True

    def write(self, *args, sep=" "):
        """Write a message gracefully when the table is opened."""
        full_message = []
        for arg in args:
            full_message.append(str(arg))
        full_message_str = sep.join(full_message)
        message_lines = full_message_str.split("\n")
        for line in message_lines:
            self._append_or_update_display_row(("USER WRITE", line))

    def to_list(self):
        """Convert to Python nested list."""
        return [[row.VALUES.get(col, None) for col in self.column_names] for row in self._data_rows]

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
        return pd.DataFrame(self.to_list(), columns=self.column_names)

    #####################
    ## PRIVATE METHODS ##
    #####################

    def _rendering_loop(self):
        idle_time: float = 1 / self.refresh_rate
        while self._RENDERER_RUNNING:
            if self._display_rows:
                self._print_pending_rows_to_buffer()
                self._refresh_active_pbars()
                self._flush_buffer()

                # Clean-up pbars is necessary when displaying content shorter than the table
                self._refresh_active_pbars(clean=True)
            time.sleep(idle_time)

    def _start_rendering(self):
        # Rendering should start when
        # * User enters the first value into the table
        self._RENDERER_RUNNING = True
        if self.interactive > 0 and self.refresh_rate > 0:
            self._renderer = Thread(target=self._rendering_loop, daemon=True)
            self._renderer.start()

    def _append_or_update_display_row(self, element):
        if self._closed:
            raise Exception("Table was closed! Updating closed tables is not supported.")

        # Renderer starts on first update
        if not self._RENDERER_RUNNING:
            self._start_rendering()

        if isinstance(element, int):
            if element not in self._display_rows:
                # Display row decorations - if there are any
                for decoration in self._latest_row_decorations:
                    self._append_or_update_display_row(decoration)
                self._latest_row_decorations = []
                self._display_rows.append(element)
            elif element != len(self._data_rows) - 1 and self.interactive < 2:
                # Won't refresh existing rows for interactive<2
                return

            display_index = self._display_rows.index(element)
            self._pending_display_rows.append(display_index)
            return

        self._display_rows.append(element)
        self._pending_display_rows.append(len(self._display_rows) - 1)

    def _append_new_empty_data_row(self):
        # Add a new data row - but don't add it as display row yet
        row = DATA_ROW(VALUES={}, WEIGHTS={}, COLORS={})
        self._data_rows.append(row)

    def _move_cursor_in_buffer(self, row_index):
        if row_index < 0:
            row_index = len(self._display_rows) + row_index
        offset = self._CURSOR_ROW - row_index

        if offset > 0:
            self._print_to_buffer(CURSOR_UP * offset)
        else:
            offset = -offset
            self._print_to_buffer("\n" * offset)
        self._CURSOR_ROW = row_index

    def _print_selected_rows_to_buffer(self, selected_rows: list[int]):
        for row_index in selected_rows:
            item = self._display_rows[row_index]
            if isinstance(item, int):
                row = self._data_rows[item]
                row_str = self._get_row_str(row)
            elif item == "HEADER":
                row_str = self._get_header()
            elif item == "SPLIT TOP":
                row_str = self._get_bar_top()
            elif item == "SPLIT BOT":
                row_str = self._get_bar_bot()
            elif item == "SPLIT MID":
                row_str = self._get_bar_mid()
            elif isinstance(item, tuple) and len(item) > 0 and item[0] == "USER WRITE":
                row_str = item[1]
            else:
                raise ValueError(f"Unknown item: {item}")

            # Cannot use CURSOR_UP when interactivity is less than 2
            offset = self._CURSOR_ROW - row_index
            if self.interactive < 2 and offset > 0:
                continue

            self._move_cursor_in_buffer(row_index)
            self._print_to_buffer(row_str)
        self._move_cursor_in_buffer(-1)

    def _set_all_display_rows_as_pending(self):
        # Only interactivity=2 allows to modify already existing rows
        if self.interactive == 2:
            self._pending_display_rows = list(range(len(self._display_rows)))
        else:
            last_row_index = len(self._data_rows) - 1
            if last_row_index not in self._pending_display_rows:
                self._pending_display_rows.append(last_row_index)

    def _print_pending_rows_to_buffer(self):
        self._print_selected_rows_to_buffer(self._pending_display_rows)
        self._pending_display_rows = []

    def _freeze_view(self):
        # Empty the row informations
        self._CURSOR_ROW = 0
        self._data_rows = []
        self._display_rows = []
        self._pending_display_rows = []

    def _resolve_row_color_dict(self, color: ColorFormat | dict[str, ColorFormat] = None):
        color = color or self.row_color or {}
        if isinstance(color, ColorFormatTuple):
            color = {column: color for column in self.column_names}

        color = {column: color.get(column) or self.DEFAULT_ROW_COLOR for column in self.column_names}
        color_colorama = {column: maybe_convert_to_colorama(color) for column, color in color.items()}
        color_colorama = {col: self.column_colors[col] + color_colorama[col] for col in color}
        return color_colorama

    def _apply_cell_formatting(self, value: Any, column_name: str, color: str):
        str_value = self.custom_cell_format(value)
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

    #####################
    ## DISPLAY HELPERS ##
    #####################

    def _print_to_buffer(self, msg):
        self._printing_buffer.append(msg + "\r")

    def _flush_buffer(self):
        output = "".join(self._printing_buffer)
        self._printing_buffer = []

        for file in self.files:
            print(output, file=file or sys.stdout, end="")

    def _get_row_str(self, row: DATA_ROW, colored=True):
        content = []
        for column in self.column_names:
            value = row.VALUES.get(column, "")
            color = row.COLORS.get(column, "") if colored else ""
            value = self._apply_cell_formatting(value=value, column_name=column, color=color)
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

    def _get_header(self):
        content = []
        for column in self.column_names:
            value = self._apply_cell_formatting(column, column, color=self.column_colors[column])
            content.append(value)
        s = "".join(["\r", self.table_style.vertical, self.table_style.vertical.join(content), self.table_style.vertical])
        return s

    ##################
    ## PROGRESS BAR ##
    ##################

    def pbar(
        self,
        iterable: Iterable | int,
        *range_args,
        level=None,
        color="",
        total=None,
        refresh_rate=None,
        description="",
        show_throughput=None,
        show_progress=None,
        show_percents=None,
        show_eta=None,
    ):
        """Create iterable progress bar object.

        Args:
            iterable: Iterable to iterate over. If None, it will be created from as range(iterable, *range_args).
            range_args: Optional arguments for range function.
            level: Level of the progress bar. If not provided, it will be set automatically.
            color: Color of the progress bar.
            total: Total number of iterations. If not provided, it will be calculated from the length of the iterable.
            refresh_rate: The maximal number of times per second the progress bar will be refreshed.
            description: Custom description of the progress bar that will be shown as prefix.
            show_throughput: If True, the throughput will be displayed.
            show_progress: If True, the progress will be displayed.
            show_percents: If True, the percentage of the progress will be displayed.
            show_eta: If True, the estimated time of finishing will be displayed.
        """
        if isinstance(iterable, int):
            iterable = range(iterable, *range_args)

        if self.interactive == 0:
            global WARNED_PBAR_HIDDEN
            if not WARNED_PBAR_HIDDEN:
                logging.warning("Progress bars will be hidden when interactive=0")
            WARNED_PBAR_HIDDEN = True

        if level is None:
            if self.interactive == 1 and not self.pbar_embedded:
                global WARNED_PBAR_NOT_EMBEDDED
                if not WARNED_PBAR_NOT_EMBEDDED:
                    logging.warning("Progress bars will be embedded when interactive=1")
                WARNED_PBAR_NOT_EMBEDDED = True

            level = 0 if self.interactive < 2 else (len(self._active_pbars) + 1 - self.pbar_embedded)

        total = total if total is not None else (len(iterable) if isinstance(iterable, Sized) else 0)

        pbar = TableProgressBar(
            iterable=iterable,
            table=self,
            total=total,
            level=level,
            color=color,
            refresh_rate=refresh_rate if refresh_rate is not None else self.refresh_rate,
            description=description,
            show_throughput=show_throughput if show_throughput is not None else self.pbar_show_throughput,
            show_progress=show_progress if show_progress is not None else self.pbar_show_progress,
            show_percents=show_percents if show_percents is not None else self.pbar_show_percents,
            show_eta=show_eta if show_eta is not None else self.pbar_show_eta,
        )
        self._active_pbars.append(pbar)
        return pbar

    def _refresh_active_pbars(self, clean=False):
        for pbar in self._active_pbars:
            if clean:
                pbar.cleanup()
            else:
                pbar.display()

    def __call__(self, *args, **kwds):
        """Creates iterable progress bar object using .pbar method and returns it."""
        return self.pbar(*args, **kwds)


class TableProgressBar:
    def __init__(
        self,
        iterable,
        *,
        table,
        total,
        level,
        color,
        refresh_rate,
        description,
        show_throughput,
        show_progress,
        show_percents,
        show_eta,
    ):
        self.iterable: Iterable | None = iterable

        self._step: int = 0
        self._total: int = total
        self._creation_time: float = time.perf_counter()
        self._last_refresh_time: float = -float("inf")

        self.level: int = level
        self.color: str = maybe_convert_to_colorama(color)
        self.table: ProgressTableV1 = table
        self.refresh_rate: int = refresh_rate
        self.description: str = description
        self.show_throughput: bool = show_throughput
        self.show_progress: bool = show_progress
        self.show_percents: bool = show_percents
        self.show_eta: bool = show_eta
        self._is_active: bool = True
        self._clearing_str: str = ""

    def display(self):
        assert self._is_active, "Progress bar was closed!"

        is_embedded = self.level == 0
        terminal_width = shutil.get_terminal_size(fallback=(0, 0)).columns or int(1e9)

        total = self._total
        step = min(self._step, total) if total else self._step

        self._last_refresh_time = time.perf_counter()
        time_passed = self._last_refresh_time - self._creation_time
        throughput = self._step / time_passed if time_passed > 0 else 0.0
        eta = (total - step) / throughput if throughput > 0 and total else None

        inside_infobar = []
        if self.description:
            inside_infobar.append(self.description)
        if self.show_progress:
            if total:
                str_total = str(total)
                str_step = str(self._step).rjust(len(str(total - 1)))
                inside_infobar.append(f"{str_step}/{str_total}")
            else:
                inside_infobar.append(f"{self._step}")

        if self.show_percents:
            if total and total > 0:
                if step / total < 0.1:
                    percents_str = f"{100 * step / total: <.2f}%"
                elif step / total < 1:
                    percents_str = f"{100 * step / total: <.1f}%"
                else:
                    percents_str = f"{100 * step / total: <.0f}%"
            else:
                percents_str = "?%"
            inside_infobar.append(percents_str)

        if self.show_throughput:
            if throughput < 10:
                throughput_str = f"{throughput: <.2f} it/s"
            elif throughput < 100:
                throughput_str = f"{throughput: <.1f} it/s"
            else:
                throughput_str = f"{throughput: <.0f} it/s"

            inside_infobar.append(throughput_str)

        if self.show_eta:
            if eta is None:
                inside_infobar.append("ETA ?")
            elif eta < 60:
                eta_str = f"ETA {eta:>2.0f}s"
                inside_infobar.append(eta_str)
            elif eta < 3600:
                eta_str = f"ETA {eta / 60:>2.0f}m"
                inside_infobar.append(eta_str)
            else:
                eta_str = f"ETA {eta / 3600:>2.0f}h"
                inside_infobar.append(eta_str)

        infobar = "[" + ", ".join(inside_infobar) + "] " if inside_infobar else ""

        pbar = ["\n" * self.level]
        if not is_embedded:
            tot_width = sum(self.table.column_widths.values()) + 3 * (len(self.table.column_widths) - 1) + 2
            if tot_width >= terminal_width - 1:
                tot_width = terminal_width - 2

            if len(infobar) > tot_width:
                infobar = "[…] "

            tot_width = tot_width - len(infobar)
            if not total:
                step = self._step % tot_width

            num_filled = math.ceil(step / total * tot_width)
            num_empty = tot_width - num_filled

            pbar_body = "".join(
                [
                    self.table.table_style.vertical,
                    infobar,
                    self.color,
                    self.table.table_style.pbar_filled * num_filled,
                    Style.RESET_ALL if self.color else "",
                    self.table.table_style.pbar_empty * num_empty,
                    self.table.table_style.vertical,
                ]
            )
            pbar.append(pbar_body)
            self._clearing_str = " " * len(pbar_body)
        else:
            # Embedded progress bar doesn't make sense without any data rows
            if not self.table._display_rows or not isinstance(self.table._display_rows[-1], int):
                return

            row_idx = self.table._display_rows[-1]
            row = self.table._data_rows[row_idx]
            orig_row_str = row_str = self.table._get_row_str(row, colored=False)
            if len(infobar) > len(orig_row_str):
                infobar = "[…] "

            pbar_body_elements = [row_str[:2], infobar]
            row_str = row_str[2 + len(infobar) :]
            if not total:  # When total is unknown
                step = self._step % len(row_str)

            if self.color:
                pbar_body_elements.append(self.color)
            for letter_idx, letter in enumerate(row_str):
                is_bar = letter_idx / len(row_str) <= (step / total) % (1 + EPS)
                is_head = (letter_idx - 1) / len(row_str) <= (step / total) % (1 + EPS)
                if letter == " " and is_bar:
                    letter = self.table.table_style.embedded_pbar_filled
                if letter == " " and is_head:
                    letter = self.table.table_style.embedded_pbar_head

                if self.color and not is_bar and not is_head:
                    pbar_body_elements.append(Style.RESET_ALL)
                pbar_body_elements.append(letter)

            pbar_body_elements.append(Style.RESET_ALL)
            pbar_body = "".join(pbar_body_elements)
            pbar.append(pbar_body)
        pbar.append(CURSOR_UP * self.level)
        self.table._print_to_buffer("".join(pbar))

    def cleanup(self):
        pbar = ["\n" * self.level, self._clearing_str, CURSOR_UP * self.level]
        self.table._print_to_buffer("".join(pbar))

    def update(self, n=1):
        self._step += n

    def reset(self, total=None):
        self._step = total or 0

    def __iter__(self):
        try:
            assert self.iterable is not None, "No iterable provided!"
            for element in self.iterable:
                yield element
                self.update()
        finally:
            self.close()

    def close(self):
        self.table._active_pbars.remove(self)
        self._is_active = False
        self.cleanup()


class TableAtIndexer:
    def __init__(self, table: ProgressTableV1):
        self.table = table
        self.edit_mode_prefix_map = {}
        for word in ("VALUES", "WEIGHTS", "COLORS"):
            self.edit_mode_prefix_map.update({word[:i]: word for i in range(1, len(word))})
            self.edit_mode_prefix_map.update({word[:i].lower(): word for i in range(1, len(word))})

    def parse_index(self, key) -> tuple[Any, Any, str]:
        if isinstance(key, slice):
            rows = key
            cols = slice(None)
            mode = "VALUES"
        elif len(key) == 2:
            rows = key[0]
            cols = key[1]
            mode = "VALUES"
        elif len(key) >= 3:
            rows = key[0]
            cols = key[1]
            mode = key[2]
            assert mode in self.edit_mode_prefix_map, f"Unknown mode `{mode}`. Available: VALUES, WEIGHTS, COLORS"
            mode = self.edit_mode_prefix_map[mode]
        else:
            raise Exception

        assert isinstance(rows, slice) or isinstance(rows, int), "Rows have to be a slice or an integer!"
        assert isinstance(cols, slice) or isinstance(cols, int), "Columns have to be a slice or an integer!"
        data_rows = self.table._data_rows[rows] if isinstance(rows, slice) else [self.table._data_rows[rows]]
        column_names = self.table.column_names[cols] if isinstance(cols, slice) else [self.table.column_names[cols]]
        return data_rows, column_names, mode

    def __setitem__(self, key, value):
        data_rows, column_names, edit_mode = self.parse_index(key)
        if edit_mode == "COLORS":
            value = maybe_convert_to_colorama(value)

        for row in data_rows:
            for column in column_names:
                row.__getattribute__(edit_mode)[column] = value

            # Displaying the update
            data_row_index = self.table._data_rows.index(row)
            self.table._append_or_update_display_row(data_row_index)

    def __getitem__(self, key):
        data_rows, column_names, edit_mode = self.parse_index(key)
        gathered_values = []

        for row in data_rows:
            row_values = []
            for column in column_names:
                row_values.append(row.__getattribute__(edit_mode).get(column, None))
            gathered_values.append(row_values)

        # Flattening outputs
        if len(gathered_values) == 1 and len(gathered_values[0]) == 1:
            return gathered_values[0][0]
        if len(gathered_values) == 1:
            return gathered_values[0]
        if all(len(x) == 1 for x in gathered_values):
            return [x[0] for x in gathered_values]
        return gathered_values
