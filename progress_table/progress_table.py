#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

"""Progress Table provides an easy and pretty way to track your process."""

from __future__ import annotations  # for PEP 563

import inspect
import logging
import math
import os
import shutil
import sys
import time
from collections.abc import Callable, Iterable, Iterator, Sized
from dataclasses import dataclass
from threading import Thread
from typing import TextIO

from colorama import Style

from progress_table import styles
from progress_table.common import CURSOR_UP, ColorFormat, ColorFormatTuple, maybe_convert_to_colorama

######################
## HELPER FUNCTIONS ##
######################

logger = logging.getLogger("progress_table")


class TableClosedError(Exception):
    """Raised when trying to update a closed table."""


def aggregate_dont(value, *_):
    """Don't aggregate the values."""
    return value


def aggregate_mean(value, old_value, weight, old_weight):
    """Aggregate the values by keeping the mean."""
    return (old_value * old_weight + value * weight) / (old_weight + weight)


def aggregate_sum(value, old_value, *_):
    """Aggregate the values by keeping the sum."""
    return old_value + value


def aggregate_max(value, old_value, *_):
    """Aggregate the values by keeping the maximum."""
    return max(old_value, value)


def aggregate_min(value, old_value, *_):
    """Aggregate the values by keeping the minimum."""
    return min(old_value, value)


def get_aggregate_fn(aggregate: None | str | Callable) -> Callable:
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
        if aggregate == "sum":
            return aggregate_sum
        if aggregate == "max":
            return aggregate_max
        if aggregate == "min":
            return aggregate_min
        msg = f"Unknown aggregate type string: {aggregate}"
        raise ValueError(msg)
    msg = f"Unknown aggregate type: {type(aggregate)}"
    raise ValueError(msg)


def get_default_format_fn(decimal_places: int) -> Callable[[object], str]:
    def fmt(x: object) -> str:
        if isinstance(x, int):
            return str(x)
        try:
            return format(x, f".{decimal_places}f")
        except ValueError:
            return str(x)

    return fmt


################
## MAIN CLASS ##
################


@dataclass
class DataRow:
    """Basic unit of data storage for the table."""

    values: dict[str, object]
    weights: dict[str, float]
    colors: dict[str, str]

    def is_empty(self) -> bool:
        """Check if the row is empty."""
        return not any(self.values)


class ProgressTable:
    """Provides an easy and pretty way to track your process."""

    DEFAULT_COLUMN_WIDTH = 8
    DEFAULT_COLUMN_COLOR = None
    DEFAULT_COLUMN_ALIGNMENT = "center"
    DEFAULT_COLUMN_AGGREGATE = None
    DEFAULT_ROW_COLOR = None

    def __init__(
        self,
        *cols: str,
        columns: Iterable[str] = (),
        interactive: int = int(os.environ.get("PTABLE_INTERACTIVE", "2")),
        refresh_rate: int = 20,
        num_decimal_places: int = 4,
        default_column_width: int | None = None,
        default_column_color: ColorFormat = None,
        default_column_alignment: str | None = None,
        default_column_aggregate: str | None = None,
        default_header_color: ColorFormat = None,
        default_row_color: ColorFormat = None,
        pbar_show_throughput: bool = True,
        pbar_show_progress: bool = False,
        pbar_show_percents: bool = False,
        pbar_show_eta: bool = False,
        pbar_embedded: bool = True,
        pbar_style: str | styles.PbarStyleBase = "square",
        pbar_style_embed: str | styles.PbarStyleBase = "cdots",
        print_header_on_top: bool = True,
        print_header_every_n_rows: int = 30,
        custom_cell_format: Callable[[object], str] | None = None,
        table_style: str | styles.TableStyleBase = "round",
        file: TextIO | list[TextIO] | tuple[TextIO] | None = None,
        # DEPRECATED ARGUMENTS
        custom_format: None = None,
        embedded_progress_bar: None = None,
        print_row_on_update: None = None,
    ) -> None:
        """Progress Table instance.

        Columns can be specified using `add_column` method, but they can be added on the fly as well.
        Use `next_row` method to display the current row and reset the values for the next row.

        Example:
            >>> table = ProgressTable()
            >>> table.add_column("b", width=10)
            >>> table["a"] = 1
            >>> table["b"] = "xyz"
            >>> table.next_row()

        Args:
            cols: Columns that will be displayed in the header. Columns can be provided directly in `__init__` or
                  through methods `add_column` and `add_columns`. Columns added through `__init__` will have default
                  settings like alignment, color and width, while columns added through methods can have those
                  customized.
            columns: Alias for `cols`.
            interactive: Three interactivity levels are available: 2, 1 and 0. It's recommended to use 2, but some
                         terminal environments might not all features. When using decreased interactivity, some features
                         will be supressed. If something doesn't look right in your terminal, try to decrease the
                         interactivity.
                         On level 2 you can modify all rows, including the rows above the current one.
                         You can also add columns on-the-fly or reorder them. You can use nested progress bars.
                         On level 1 you can only operate on the current row, the old rows are frozen, but you still get
                         to use a progress bar, albeit not nested. On level 0 there are no progress bars and rows are
                         only printed after calling `next_row`.
            refresh_rate: The maximal number of times per second to render the updates in the table.
            num_decimal_places: This is only applicable when using the default formatting. This won't be used if
                                `custom_cell_repr` is set. If applicable, for every displayed value except integers
                                there will be an attempt to round it.
            default_column_color: Color of the header and the data in the column.
                                  This can be overwritten in columns by using an argument in `add_column` method.
            default_column_width: Width of the column excluding cell padding.
                                  This can be overwritten in columns by using an argument in `add_column` method.
            default_column_alignment: Alignment in the column. Can be aligned either to `left`, `right` or `center`.
                                      This can be overwritten by columns by using an argument in `add_column` method.
            default_column_aggregate: By default, there's no aggregation. But if this is for example 'mean', then after
                                      every update in the current row, the mean of the provided values will be
                                      displayed. Aggregated values is reset at every new row. This can be overwritten
                                      by columns by using an argument in `add_column` method.
            default_header_color: Color of the header. This can be overwritten by column-specific color.
            default_row_color: Color of the row. This can be overwritten by using an argument in `next_row` method.
            pbar_show_throughput: Show throughput in the progress bar, for example `3.55 it/s`. Defaults to True.
            pbar_show_progress: Show progress in the progress bar, for example 10/40. Defaults to True.
            pbar_show_percents: Show percents in the progress bar, for example 25%. Defaults to False.
            pbar_show_eta: Show estimated time of finishing in the progress bar, for example 10s. Defaults to False.
            pbar_embedded: If True, changes the way the first (non-nested) progress bar looks.
                           Embedded version is more subtle, but does not prevent the current row from being displayed.
                           If False, the progress bar covers the current row, preventing the user from seeing values
                           that are being updated until the progress bar finishes. The default is True.
            pbar_style: Change the style of the progress bar. Either a string or 'PbarStyleBase' type class.
            pbar_style_embed: Change the style of the embedded progress bar. Same as pbar_style, but for embedded pbars.
            print_header_on_top: If True, header will be displayed as the first row in the table.
            print_header_every_n_rows: 30 by default. When table has a lot of rows, it can be useful to remind what the
                                       header is. If True, hedaer will be displayed periodically after the selected
                                       number of rows. 0 to supress.
            custom_cell_format: A function that defines how to get str value to display from a cell content.
                                This function should be universal and work for all datatypes as inputs.
                                It takes one value as an input and returns string as an output.
            table_style: Change the borders of the table. Either a string or 'TableStyleBase' type class.
            file: Redirect the output to another stream. There can be multiple streams at once passed as list or tuple.
                  Defaults to None, which is interpreted as stdout.

        """
        # Deprecation handling
        if custom_format is not None:
            logger.warning("Argument `custom_format` is deprecated. Use `custom_cell_format` instead!")
        if embedded_progress_bar is not None:
            logger.warning("Argument `embedded_progress_bar` is deprecated. Use `pbar_embedded` instead!")
        if print_row_on_update is not None:
            logger.warning("Argument `print_row_on_update` is deprecated. Specify `interactive` instead!")

        self.pbar_style = styles.parse_pbar_style(pbar_style)
        self.table_style = styles.parse_table_style(table_style)
        self.pbar_style_embed = styles.parse_pbar_style(pbar_style_embed)

        assert isinstance(default_row_color, ColorFormatTuple), "Row color has to be a color format!"
        assert isinstance(default_column_color, ColorFormatTuple), "Column color has to be a color format!"
        assert isinstance(default_header_color, ColorFormatTuple), "Header color has to be a color format!"

        # Default values for column and
        self.column_width = default_column_width
        self.column_color = default_column_color
        self.column_alignment = default_column_alignment
        self.column_aggregate = default_column_aggregate
        self.row_color = default_row_color
        self.header_color = default_header_color

        # We are storing column configs
        self.column_widths: dict[str, int] = {}
        self.column_colors: dict[str, str] = {}
        self.column_alignments: dict[str, str] = {}
        self.column_aggregates: dict[str, Callable] = {}
        self.column_names: list[str] = []  # Names serve as keys for column configs
        self._closed = False

        self.files = (file,) if not isinstance(file, (list, tuple)) else file

        assert print_header_every_n_rows >= 0, "Value must be non-negative!"
        self._print_header_on_top = print_header_on_top
        self._print_header_every_n_rows = print_header_every_n_rows
        self._previous_header_row_number = 0

        self._data_rows: list[DataRow] = []
        self._display_rows: list[str | int] = []
        self._pending_display_rows: list[int] = []

        self._REFRESH_PENDING: bool = False
        self._RENDERER_RUNNING: bool = False

        self._active_pbars: list[TableProgressBar] = []
        self._cleaning_pbar_instructions: list[tuple[int, str]] = []

        self._latest_row_decorations: list[str]
        if self._print_header_on_top:
            self._latest_row_decorations = ["SPLIT TOP", "HEADER", "SPLIT MID"]
        else:
            self._latest_row_decorations = ["SPLIT TOP"]

        self.custom_cell_format = custom_cell_format or get_default_format_fn(num_decimal_places)
        self.pbar_show_throughput: bool = pbar_show_throughput
        self.pbar_show_progress: bool = pbar_show_progress
        self.pbar_show_percents: bool = pbar_show_percents
        self.pbar_show_eta: bool = pbar_show_eta
        self.pbar_embedded: bool = pbar_embedded

        self.refresh_rate: int = refresh_rate
        self._frame_time: float = 1 / self.refresh_rate if self.refresh_rate else 0.0

        self._CURSOR_ROW = 0

        # Interactivity settings
        self.interactive = interactive
        assert self.interactive in (2, 1, 0)

        self._printing_buffer: list[str] = []
        self.add_columns(*cols, *columns)

        self._append_new_empty_data_row()
        self._at_indexer = TableAtIndexer(self)

    ####################
    ## PUBLIC METHODS ##
    ####################

    def add_column(
        self,
        name: str,
        *,
        width: int | None = None,
        color: ColorFormat = None,
        alignment: str | None = None,
        aggregate: None | str | Callable = None,
    ) -> None:
        """Add column to the table.

        You can re-add existing columns to modify their properties.

        Args:
            name: Name of the column. Will be displayed in the header. Must be unique.
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
            logger.info("Column '%s' already exists!", name)
        else:
            self.column_names.append(name)

        resolved_width = width or self.column_width or self.DEFAULT_COLUMN_WIDTH
        if not width and resolved_width < len(str(name)):
            resolved_width = len(str(name))
        self.column_widths[name] = resolved_width
        self.column_colors[name] = maybe_convert_to_colorama(color or self.column_color or self.DEFAULT_COLUMN_COLOR)
        self.column_alignments[name] = alignment or self.column_alignment or self.DEFAULT_COLUMN_ALIGNMENT
        self.column_aggregates[name] = get_aggregate_fn(
            aggregate or self.column_aggregate or self.DEFAULT_COLUMN_AGGREGATE,
        )
        self._set_all_display_rows_as_pending()

    def add_columns(self, *columns, **kwds) -> None:
        """Add multiple columns to the table.

        This can be an integer - then the given number of columns will be created.
        In this case their names will be integers starting from 0.

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

    def reorder_columns(self, *column_names) -> None:
        """Reorder columns in the table.

        Args:
            column_names: Names of the columns in the desired order.

        """
        if all(x == y for x, y in zip(column_names, self.column_names)):
            return

        assert isinstance(column_names, (list, tuple))
        assert all(x in self.column_names for x in column_names), f"Columns {column_names} not in {self.column_names}"
        self.column_names = list(column_names)
        self.column_widths = {k: self.column_widths[k] for k in column_names}
        self.column_colors = {k: self.column_colors[k] for k in column_names}
        self.column_alignments = {k: self.column_alignments[k] for k in column_names}
        self.column_aggregates = {k: self.column_aggregates[k] for k in column_names}
        self._set_all_display_rows_as_pending()

    def update(
        self,
        name: str,
        value: object,
        *,
        row: int = -1,
        weight: float = 1.0,
        cell_color: ColorFormat = None,
        **column_kwds,
    ) -> None:
        """Update value in the current row. More powerful than __setitem__.

        Args:
            name: Name of the column.
            value: Value to be set.
            row: Index of the row. By default, it's the last row.
            weight: Weight of the value. This is used for aggregation.
            cell_color: Optionally override color for specific cell, independent of rows and columns.
            column_kwds: Additional arguments for the column. They will be only used for column creation.
                         If column already exists, they will have no effect.

        """
        if name not in self.column_names:
            self.add_column(name, **column_kwds)

        data_row_index = row if row >= 0 else len(self._data_rows) + row
        if data_row_index >= len(self._data_rows):
            msg = f"Row {data_row_index} out of range! Number of rows: {len(self._data_rows)}"
            raise IndexError(msg)

        # Set default values for rows without values in this column
        data_row = self._data_rows[row]
        data_row.values.setdefault(name, 0)
        data_row.weights.setdefault(name, 0)

        fn = self.column_aggregates[name]
        data_row.values[name] = fn(value, data_row.values[name], weight, data_row.weights[name])
        data_row.weights[name] += weight

        if cell_color is not None:
            data_row.colors[name] = maybe_convert_to_colorama(cell_color)

        if self.interactive > 0:
            self._append_or_update_display_row(data_row_index)

    def __setitem__(self, key: str | tuple[str, int], value: object) -> None:
        """Update value in the current row. Calls 'update'."""
        if isinstance(key, tuple):
            name, row = key
            if isinstance(name, int) and isinstance(row, str):
                name, row = row, name
        else:
            name = key
            row = -1
        assert isinstance(row, int), f"Row {row} has to be an integer, not {type(row)}!"
        self.update(name, value, row=row, weight=1)

    def __getitem__(self, key: str | tuple[str, int]) -> object | None:
        """Get the value from the current row in table."""
        if isinstance(key, tuple):
            name, row = key
            if isinstance(name, int) and isinstance(row, int):
                name, row = row, name
        else:
            name = key
            row = -1
        assert name in self.column_names, f"Column {name} not in {self.column_names}"
        assert isinstance(row, int), f"Row {row} has to be an integer, not {type(row)}!"
        return self._data_rows[row].values.get(name, None)

    def update_from_dict(self, dictionary: dict[str, object]) -> None:
        """Update multiple values in the current row."""
        for key, value in dictionary.items():
            self.update(key, value)

    @property
    def at(self) -> TableAtIndexer:
        """Advanced indexing and splicing for the table.

        Indexing with respect to data rows.
        Headers and decorations are ignored.

        Example:
            >>> table.at[:] = 0.0  # Initialize all values to 0.0
            >>> table.at[0, :] = 2.0  # Set all values in the first row to 2.0
            >>> table.at[:, 1] = 2.0  # Set all values in the second column to 2.0
            >>> table.at[-2, 0] = 3.0  # Set the first column in the second-to-last row to 3.0

        """
        return self._at_indexer

    def next_row(
        self,
        color: ColorFormat | dict[str, ColorFormat] = None,
        split: bool | None = None,
        header: bool | None = None,
    ) -> None:
        """End the current row."""
        # Force header if it wasn't printed for a long enough time
        if (
            header is None
            and len(self._data_rows) - self._previous_header_row_number >= self._print_header_every_n_rows
            and self._print_header_every_n_rows > 0
        ):
            header = True
        header = header or False
        split = split or False

        row = self._data_rows[-1]
        data_row_index = len(self._data_rows) - 1

        # Color is applied to the existing row - not the new one!
        # Existing colors applied by `update` get the priority over row color
        row.colors = {**self._resolve_row_color_dict(color), **row.colors}

        # Refreshing the existing row is necessary to apply colors
        # Or - if row is empty, this will cause the first addition to display rows
        self._append_or_update_display_row(data_row_index)

        self._append_new_empty_data_row()
        # Add decorations and a new row
        if header:
            self._previous_header_row_number = len(self._data_rows) - 1
            self._latest_row_decorations.extend(["SPLIT MID", "HEADER", "SPLIT MID"])
        elif split:
            self._latest_row_decorations.append("SPLIT MID")

    def add_row(self, *values, **kwds) -> None:
        """Mimicking rich.table behavior for adding full rows in one call."""
        for key, value in zip(self.column_names, values):
            self.update(key, value)
        self.next_row(**kwds)

    def add_rows(self, *rows, **kwds) -> None:
        """Like `add_row` but adds multiple rows at once.

        Optionally, it accepts an integer as the first argument, which will create that number of empty rows.
        """
        if len(rows) == 1 and isinstance(rows[0], int):
            rows = [{} for _ in range(rows[0])]

        for row in rows:
            self.add_row(*row, **kwds)

    def num_rows(self) -> int:
        """Get the number of rows in the table."""
        return len(self._data_rows)

    def num_columns(self) -> int:
        """Get the number of columns in the table."""
        return len(self.column_names)

    def close(self) -> None:
        """Close the table gracefully. Closed table cannot be updated anymore."""
        if self._closed:
            return
        for pbar in self._active_pbars:
            pbar.close()
        if "SPLIT TOP" in self._display_rows:
            self._append_or_update_display_row("SPLIT BOT")
        self._refresh()
        self._closed = True

    def write(self, *args, sep: str = " ") -> None:
        """Write a text message gracefully when the table is opened.

        Example:
            >>> ┌─────────┬─────────┐
            >>> │ H1      │ H2      │
            >>> ├─────────┼─────────┤
            >>> │ V1      │ V2      │
            >>> │ Your message here │
            >>> │ V3      │ V4      │
            >>> └─────────┴─────────┘

        """
        full_message = [str(arg) for arg in args]
        full_message_str = sep.join(full_message)
        message_lines = full_message_str.split("\n")

        tot_width = self._get_outer_inner_width()
        for raw_line in message_lines:
            line = self.table_style.vertical + raw_line

            if len(line) < tot_width:
                n_spaces = tot_width - len(line) - 1
                line += " " * n_spaces + self.table_style.vertical

            self._append_or_update_display_row("USER WRITE " + line)

    def to_list(self) -> list[list[object]]:
        """Convert to Python nested list."""
        values = [[row.values.get(col, None) for col in self.column_names] for row in self._data_rows]
        if self._data_rows[-1].is_empty():
            values.pop(-1)
        return values

    def to_numpy(self) -> object:
        """Convert to numpy array.

        Numpy library is required.
        """
        import numpy as np

        return np.array(self.to_list())

    def to_df(self) -> object:
        """Convert to pandas DataFrame.

        Pandas library is required.
        """
        import pandas as pd

        return pd.DataFrame(self.to_list(), columns=pd.Series(self.column_names))

    def show(self) -> None:
        """Show the full table in the console."""
        self._CURSOR_ROW = 0
        self._set_all_display_rows_as_pending()

    #####################
    ## PRIVATE METHODS ##
    #####################

    def _trigger_refresh(self) -> None:
        """Trigger refresh event.

        If fps>0 the refresh won't happen immediately.
        """
        if self.refresh_rate == 0:
            return self._refresh()

        # Inform the renderer to refresh
        self._REFRESH_PENDING = True

        if not self._RENDERER_RUNNING:
            # Spawn the renderer thread
            self._RENDERER_RUNNING = True
            Thread(target=self._rendering_loop).start()
            return None
        return None

    def _rendering_loop(self) -> None:
        """Render in a loop.

        Renderer loop that runs as long as there's something to display.
        If no external events happen, the rendering will stop after a while.
        """
        while True:
            time.sleep(self._frame_time)

            if not self._REFRESH_PENDING:
                # No triggers during wait time.
                # Waiting some more to be sure...

                time.sleep(self._frame_time)
                if not self._REFRESH_PENDING:
                    self._RENDERER_RUNNING = False
                    return  # Kill the unused renderer

            self._REFRESH_PENDING = False
            self._refresh()

    def _refresh(self) -> None:
        """Immediate refresh of the table."""
        if self._display_rows:
            self._print_pending_rows_to_buffer()
            self._flush_buffer()

    def _append_or_update_display_row(self, element: int | str) -> None:
        """Refresh or append a display row.

        For integer - this adds the corresponding existing data row as pending.
        For string - this appends a new row decoration.
        """
        if self._closed:
            msg = "Table was closed! Updating closed tables is not supported."
            raise TableClosedError(msg)

        if isinstance(element, int):
            if element not in self._display_rows:
                for decoration in self._latest_row_decorations:
                    self._append_or_update_display_row(decoration)
                self._latest_row_decorations.clear()
                self._display_rows.append(element)
            elif element != len(self._data_rows) - 1 and self.interactive < 2:
                # Won't refresh non-current rows for interactive<2
                return

            display_index = self._display_rows.index(element)
            if display_index not in self._pending_display_rows:
                # Check if the row isn't already pending
                self._pending_display_rows.append(display_index)
        else:
            self._display_rows.append(element)
            self._pending_display_rows.append(len(self._display_rows) - 1)

        self._trigger_refresh()

    def _set_all_display_rows_as_pending(self) -> None:
        """Set all display rows as pending.

        This will refresh all rows in the next tick.
        """
        self._pending_display_rows = list(range(len(self._display_rows)))
        self._trigger_refresh()

    def _append_new_empty_data_row(self) -> None:
        # Add a new data row - but don't add it as display row yet
        row = DataRow(values={}, weights={}, colors={})
        self._data_rows.append(row)

    def _get_cursor_offset(self, row_index: int) -> int:
        if row_index < 0:
            row_index = len(self._display_rows) + row_index
        return self._CURSOR_ROW - row_index

    def _move_cursor_in_buffer(self, row_index: int) -> None:
        if row_index < 0:
            row_index = len(self._display_rows) + row_index
        offset = self._CURSOR_ROW - row_index

        if offset > 0:
            self._print_to_buffer(CURSOR_UP * offset)
        elif offset < 0:
            self._print_to_buffer("\n" * (-offset))
        self._CURSOR_ROW = row_index

    def _get_item_str(self, display_row_index: int) -> str:
        item: str | int = self._display_rows[display_row_index]
        if isinstance(item, int):
            row = self._data_rows[item]  # item is the data row index
            row_str = self._get_row_str(row)  # here we pass the row item, not index
        elif item == "HEADER":
            row_str = self._get_header()
        elif item == "SPLIT TOP":
            row_str = self._get_bar_top()
        elif item == "SPLIT BOT":
            row_str = self._get_bar_bot() + "\n"
        elif item == "SPLIT MID":
            row_str = self._get_bar_mid()
        elif item.startswith("USER WRITE"):
            row_str = item.split("USER WRITE", 1)[1].strip()
        else:
            msg = f"Unknown item: {item}"
            raise ValueError(msg)
        return row_str

    def _print_pending_rows_to_buffer(self) -> None:
        # Clearing progress bars below the table happens here
        for display_row_idx, cleaning_str in self._cleaning_pbar_instructions:
            assert self.interactive >= 2, "Should not need to clean pbars when interactive < 2!"
            self._move_cursor_in_buffer(display_row_idx)
            self._print_to_buffer(cleaning_str, prefix="\r")
            self._move_cursor_in_buffer(-1)
            self._cleaning_pbar_instructions.clear()

        # Remove duplicate pending and sort them
        self._pending_display_rows = sorted(set(self._pending_display_rows))

        for display_row_index in self._pending_display_rows:
            offset = self._get_cursor_offset(display_row_index)

            # Cannot use CURSOR_UP when interactivity is less than 2
            # However, we can ALLOW going down with the cursor
            if self.interactive < 2 and offset > 0:
                continue

            self._move_cursor_in_buffer(display_row_index)

            # We don't need to print carriage return if cursor was moved DOWN.
            # After moving, cursor is in the right position to overwrite text.
            prefix = "" if offset < 0 else "\r"
            row_str = self._get_item_str(display_row_index)
            self._print_to_buffer(row_str, prefix=prefix)
        self._pending_display_rows.clear()

        # Printing progress bars happens here
        for pbar in self._active_pbars:
            if self.interactive == 0:
                break  # No progress bars in non-interactive mode

            num_rows = len(self._display_rows)
            pbar_display_row_idx = (
                self._display_rows.index(pbar.position) if pbar.static else num_rows + pbar.position - 1
            )

            offset = self._get_cursor_offset(pbar_display_row_idx)
            # Cannot use CURSOR_UP when interactivity is less than 2
            # Here we DON'T ALLOW going down with the cursor
            if self.interactive < 2 and offset != 0:
                continue

            # We add the display row to pending if we were writing over a row
            # So in next tick the row will be printed again
            if pbar_display_row_idx < num_rows:
                self._pending_display_rows.append(pbar_display_row_idx)

            self._move_cursor_in_buffer(pbar_display_row_idx)

            row_str = None
            if self.pbar_embedded and pbar_display_row_idx < num_rows:
                data_row_idx = self._display_rows[pbar_display_row_idx]
                if isinstance(data_row_idx, int):
                    data_row = self._data_rows[data_row_idx]
                    row_str = self._get_row_str(data_row, colored=False)

            pbar_str = pbar.display(embed_str=row_str)

            # We need to take care of clearing pbars that are printed below the table
            if pbar_display_row_idx > num_rows:
                self._cleaning_pbar_instructions.append((pbar_display_row_idx, pbar._cleaning_str))

            self._print_to_buffer(pbar_str, prefix="\r")
        self._move_cursor_in_buffer(-1)

    def _resolve_row_color_dict(self, color: ColorFormat | dict[str, ColorFormat] = None) -> dict[str, str]:
        color = color or self.row_color or {}
        if isinstance(color, ColorFormatTuple):
            color = dict.fromkeys(self.column_names, color)

        color = {column: color.get(column) or self.DEFAULT_ROW_COLOR for column in self.column_names}
        color_colorama = {column: maybe_convert_to_colorama(color) for column, color in color.items()}
        return {col: self.column_colors[col] + color_colorama[col] for col in color}

    def _apply_cell_formatting(self, value: object, column_name: str, color: str) -> str:
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
            msg = f"Alignment '{alignment}' not in {allowed_alignments}!"
            raise KeyError(msg)

        clipped = len(str_value) > width
        str_value = "".join(
            [
                " ",  # space at the beginning of the row
                str_value[:width].center(width),
                self.table_style.cell_overflow if clipped else " ",
            ],
        )
        reset = Style.RESET_ALL if color else ""
        return f"{color}{str_value}{reset}"

    def _get_outer_inner_width(self) -> int:
        return sum(self.column_widths.values()) + 3 * len(self.column_widths) + 1

    def _get_inner_table_width(self) -> int:
        return sum(self.column_widths.values()) + 3 * len(self.column_widths) - 1

    #####################
    ## DISPLAY HELPERS ##
    #####################

    def _print_to_buffer(self, msg: str = "", prefix: str = "", suffix: str = "") -> None:
        """Prints to table's buffer.

        Not displayed to stdout yet.
        """
        self._printing_buffer.append(prefix + msg + suffix)

    def _flush_buffer(self) -> None:
        """This is where table prints to the stdout."""
        output = "".join(self._printing_buffer)

        # Start by clearing the existing line
        self._printing_buffer = []

        for file in self.files:
            print(output, file=file or sys.stdout, end="")

    def _get_row_str(self, row: DataRow, *, colored: bool = True) -> str:
        """Get the string representation of the data row."""
        content = []
        for column in self.column_names:
            value = row.values.get(column, "")
            color = row.colors.get(column, "") if colored else ""
            value = self._apply_cell_formatting(value=value, column_name=column, color=color)
            content.append(value)
        return "".join(
            [
                self.table_style.vertical,
                self.table_style.vertical.join(content),
                self.table_style.vertical,
            ],
        )

    def _get_bar(self, left: str, center: str, right: str) -> str:
        content_list: list[str] = []
        for column_name in self.column_names:
            content_list.append(self.table_style.horizontal * (self.column_widths[column_name] + 2))

        center = center.join(content_list)
        content = [
            left,
            center,
            right,
        ]
        return "".join(content)

    def _get_bar_top(self) -> str:
        return self._get_bar(
            self.table_style.down_right,
            self.table_style.no_up,
            self.table_style.down_left,
        )

    def _get_bar_bot(self) -> str:
        return self._get_bar(
            self.table_style.up_right,
            self.table_style.no_down,
            self.table_style.up_left,
        )

    def _get_bar_mid(self) -> str:
        return self._get_bar(self.table_style.no_left, self.table_style.all, self.table_style.no_right)

    def _get_header(self) -> str:
        content = []
        colors = self.column_colors if self.header_color is None else self._resolve_row_color_dict(self.header_color)

        for column in self.column_names:
            value = self._apply_cell_formatting(column, column, color=colors[column])
            content.append(value)
        return "".join(
            [
                self.table_style.vertical,
                self.table_style.vertical.join(content),
                self.table_style.vertical,
            ],
        )

    ##################
    ## PROGRESS BAR ##
    ##################

    def pbar(
        self,
        iterable: Iterable | int,
        *range_args,
        position=None,
        static=False,
        total=None,
        description="",
        show_throughput: bool | None = None,
        show_progress: bool | None = None,
        show_percents: bool | None = None,
        show_eta: bool | None = None,
        style=None,
        style_embed=None,
        color=None,
        color_empty=None,
    ) -> TableProgressBar:
        """Create iterable progress bar object.

        Args:
            iterable: Iterable to iterate over. If None, it will be created from as range(iterable, *range_args).
            range_args: Optional arguments for range function.
            position: Level of the progress bar. If not provided, it will be set automatically.
            static: If True, the progress bar will stick to the row with index given by position.
                    If False, the position will be interpreted as the offset from the last row.
            total: Total number of iterations. If not provided, it will be calculated from the length of the iterable.
            description: Custom description of the progress bar that will be shown as prefix.
            show_throughput: If True, the throughput will be displayed.
            show_progress: If True, the progress will be displayed.
            show_percents: If True, the percentage of the progress will be displayed.
            show_eta: If True, the estimated time of finishing will be displayed.
            style: Style of the progress bar. If None, the default style will be used.
            style_embed: Style of the embedded progress bar. If None, the default style will be used.
            color: Color of the progress bar. This overrides the default color.
            color_empty: Color of the empty progress bar. This overrides the default color.

        """
        if isinstance(iterable, int):
            iterable = range(iterable, *range_args)

        if static is True and position is None:
            msg = "For static pbar position cannot be None!"
            raise ValueError(msg)
        if position is None:
            position = 0 if self.interactive < 2 else len(self._active_pbars) + 1 - self.pbar_embedded

        total = total if total is not None else (len(iterable) if isinstance(iterable, Sized) else 0)

        style = styles.parse_pbar_style(style) if style else self.pbar_style
        style_embed = styles.parse_pbar_style(style_embed) if style_embed else self.pbar_style_embed

        pbar = TableProgressBar(
            iterable=iterable,
            table=self,
            total=total,
            style=style,
            style_embed=style_embed,
            color=color,
            color_empty=color_empty,
            position=position,
            static=static,
            description=description,
            show_throughput=(show_throughput if show_throughput is not None else self.pbar_show_throughput),
            show_progress=(show_progress if show_progress is not None else self.pbar_show_progress),
            show_percents=(show_percents if show_percents is not None else self.pbar_show_percents),
            show_eta=show_eta if show_eta is not None else self.pbar_show_eta,
        )
        self._active_pbars.append(pbar)
        return pbar

    def __call__(self, *args, **kwds) -> TableProgressBar:
        """Creates iterable progress bar object using .pbar method and returns it."""
        return self.pbar(*args, **kwds)


##################
## PROGRESS BAR ##
##################


class TableProgressBar:
    def __init__(
        self,
        iterable,
        *,
        table,
        total,
        style,
        style_embed,
        color,
        color_empty,
        position,
        static,
        description,
        show_throughput: bool,
        show_progress: bool,
        show_percents: bool,
        show_eta: bool,
    ) -> None:
        self.iterable: Iterable | None = iterable

        self._step: int = 0
        self._total: int = total
        self._creation_time: float = time.perf_counter()
        self._last_refresh_time: float = -float("inf")

        self.style = style
        self.style_embed = style_embed

        # Modyfing styles
        if color:
            color = maybe_convert_to_colorama(color)
            self.style.color = color
            self.style_embed.color = color
        if color_empty:
            color_empty = maybe_convert_to_colorama(color_empty)
            self.style.color_empty = color_empty
            self.style_embed.color_empty = color_empty

        self.table: ProgressTable = table
        self.position: int = position
        self.static: bool = static
        self.description: str = description
        self.show_throughput: bool = show_throughput
        self.show_progress: bool = show_progress
        self.show_percents: bool = show_percents
        self.show_eta: bool = show_eta
        self._is_active: bool = True
        self._cleaning_str: str = ""

        self._modified_rows = []

    def _get_infobar(self, step, total):
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
            elif eta < 100:
                eta_str = f"ETA {eta:>2.0f}s"
                inside_infobar.append(eta_str)
            elif round(eta / 60) < 100:
                eta_str = f"ETA {eta / 60:>2.0f}m"
                inside_infobar.append(eta_str)
            else:
                eta_str = f"ETA {eta / 3600:>2.0f}h"
                inside_infobar.append(eta_str)

        return "[" + ", ".join(inside_infobar) + "] " if inside_infobar else ""

    def display(self, embed_str: str | None) -> str:
        assert self._is_active, "Progress bar was closed!"
        terminal_width = shutil.get_terminal_size(fallback=(0, 0)).columns or int(1e9)

        total = self._total
        step = min(self._step, total) if total else self._step
        infobar = self._get_infobar(step, total)
        pbar = []

        inner_width = self.table._get_inner_table_width()
        if inner_width >= terminal_width - 1:
            inner_width = terminal_width - 2

        if len(infobar) > inner_width:
            infobar = "[…] "

        inner_width = inner_width - len(infobar)
        if not total:
            step = self._step % inner_width
            total = inner_width

        num_filled = math.ceil(step / total * inner_width)
        frac_missing = step / total * inner_width - num_filled
        num_empty = inner_width - num_filled

        if embed_str is not None:
            row_str = embed_str[1 + len(infobar) :]

            filled_part = row_str[:num_filled]
            if len(filled_part) > 0 and filled_part[-1] == " ":
                head = self.style_embed.head
                if isinstance(head, (tuple, list)):
                    head = head[round(frac_missing * len(head))]
                filled_part = filled_part[:-1] + head
            filled_part = filled_part.replace(" ", self.style_embed.filled)
            empty_part = row_str[num_filled:-1]
            color_filled = self.style_embed.color
            color_empty = self.style_embed.color_empty
        else:
            filled_part = self.style.filled * num_filled
            if len(filled_part) > 0:
                head = self.style.head
                if isinstance(head, (tuple, list)):
                    head = head[round(frac_missing * len(head))]
                filled_part = filled_part[:-1] + head
            empty_part = self.style.empty * num_empty
            color_filled = self.style.color
            color_empty = self.style.color_empty

        pbar_body = "".join(
            [
                self.table.table_style.vertical,
                infobar,
                color_filled,
                filled_part,
                Style.RESET_ALL if color_filled else "",
                color_empty,
                empty_part,
                Style.RESET_ALL if color_empty else "",
                self.table.table_style.vertical,
            ],
        )
        pbar.append(pbar_body)
        self._cleaning_str = " " * len(pbar_body)
        return "".join(pbar)

    def update(self, n: int = 1) -> None:
        """Update the progress bar steps.

        Args:
            n: Number of steps to update the progress bar.

        """
        self._step += n
        self.table._trigger_refresh()

    def reset(self, total: int | None = None) -> None:
        """Reset the progress bar.

        Args:
            total: Modify the total number of iterations. Optional.

        """
        self._step = 0

        if total:
            self._total = total
        self.table._trigger_refresh()

    def set_step(self, step: int) -> None:
        """Overwrite the current step.

        Args:
            step: New value of the current step.

        """
        self._step = step
        self.table._trigger_refresh()

    def set_total(self, total: int) -> None:
        """Overwrite the total number of iterations.

        Args:
            total: New value of the total number of iterations

        """
        self._total = total
        self.table._trigger_refresh()

    def __iter__(self) -> Iterator:
        """Iterate over iterable while updating the progress bar."""
        try:
            assert self.iterable is not None, "No iterable provided!"
            for element in self.iterable:
                yield element
                self.update()
        finally:
            self.close()

    def close(self) -> None:
        """Close the progress bar."""
        self.table._active_pbars.remove(self)
        self._is_active = False


#############
## INDEXER ##
#############


class BadKeyError(Exception):
    """Raised when the TableAtIndexer key is not valid."""


class TableAtIndexer:
    """Advanced indexing for the table."""

    def __init__(self, table: ProgressTable) -> None:
        """Initialize the indexer."""
        self.table = table
        self.edit_mode_prefix_map: dict[str, str] = {}
        for word in ("values", "weights", "colors"):
            self.edit_mode_prefix_map.update({word[:i].lower(): word for i in range(1, len(word) + 1)})
            self.edit_mode_prefix_map.update({word[:i].upper(): word for i in range(1, len(word) + 1)})

    def _parse_index(self, key: slice | tuple) -> tuple:
        if isinstance(key, slice):
            rows: slice | int = key
            cols: slice | int = slice(None)
            mode: str = "values"
        elif len(key) == 2:
            rows: slice | int = key[0]
            cols: slice | int = key[1]
            mode: str = "values"
        elif len(key) >= 3:
            rows: slice | int = key[0]
            cols: slice | int = key[1]
            mode: str = key[2]
            assert mode in self.edit_mode_prefix_map, f"Unknown mode `{mode}`. Available: values, weights, colors"
            mode = self.edit_mode_prefix_map[mode]
        else:
            msg = "Expected slice or tuple with 2 or 3 elements!"
            raise BadKeyError(msg)

        assert isinstance(rows, (slice, int)), f"Rows have to be a slice or an integer, not {type(rows)}!"
        assert isinstance(cols, (slice, int)), f"Columns have to be a slice or an integer, not {type(cols)}!"
        row_indices = [rows] if isinstance(rows, int) else list(range(len(self.table._data_rows)))[rows]
        column_names = self.table.column_names[cols] if isinstance(cols, slice) else [self.table.column_names[cols]]
        return row_indices, column_names, mode

    def __setitem__(self, key: slice | tuple, value: object) -> None:
        """Set the values, colors, or weights of a slice in the table."""
        row_indices, column_names, edit_mode = self._parse_index(key)
        if edit_mode == "colors":
            assert isinstance(value, ColorFormatTuple), f"Color must be compatible with ColorFormat, not {type(value)}!"
            value = maybe_convert_to_colorama(value)

        for row_idx in row_indices:
            data_row = self.table._data_rows[row_idx]

            for column in column_names:
                data_row.__getattribute__(edit_mode)[column] = value

            # Displaying the update
            self.table._append_or_update_display_row(row_idx)

    def __getitem__(self, key: slice | tuple) -> list:
        """Get the values of a slice and flatten before returning."""
        row_indices, column_names, edit_mode = self._parse_index(key)
        gathered_values = []

        for row_idx in row_indices:
            row = self.table._data_rows[row_idx]
            row_values = [row.__getattribute__(edit_mode).get(c, None) for c in column_names]
            gathered_values.append(row_values)

        # Flattening outputs
        if len(gathered_values) == 1 and len(gathered_values[0]) == 1:
            return gathered_values[0][0]
        if len(gathered_values) == 1:
            return gathered_values[0]
        if all(len(x) == 1 for x in gathered_values):
            return [x[0] for x in gathered_values]
        return gathered_values
