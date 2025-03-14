#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

import colorama
import pytest

from progress_table.progress_table import ProgressTable, TableClosedError


def test_add_column_with_default_settings():
    table = ProgressTable()

    column_name = "test_column"
    table.add_column(column_name)
    assert column_name in table.column_names
    assert table.column_widths[column_name] == len(column_name)
    assert table.column_alignments[column_name] == table.DEFAULT_COLUMN_ALIGNMENT


def test_add_column_with_default_settings2():
    table = ProgressTable()

    column_name = "short"
    table.add_column(column_name)
    assert column_name in table.column_names
    assert table.column_widths[column_name] == table.DEFAULT_COLUMN_WIDTH
    assert table.column_alignments[column_name] == table.DEFAULT_COLUMN_ALIGNMENT


def test_add_column_with_custom_settings():
    table = ProgressTable()
    table.add_column("test_column", width=15, alignment="left", color="red", aggregate="sum")
    assert table.column_widths["test_column"] == 15
    assert table.column_alignments["test_column"] == "left"
    assert table.column_colors["test_column"] == colorama.Fore.RED
    assert table.column_aggregates["test_column"].__name__ == "aggregate_sum"


def test_add_multiple_columns():
    table = ProgressTable()
    table.add_columns("col1", "col2", "col3")
    assert "col1" in table.column_names
    assert "col2" in table.column_names
    assert "col3" in table.column_names


def test_add_multiple_columns2():
    table = ProgressTable("col1", "col2", "col3")
    assert "col1" in table.column_names
    assert "col2" in table.column_names
    assert "col3" in table.column_names


def test_add_multiple_columns3():
    table = ProgressTable("col1", "col2", columns=("col3", "col4"))
    assert "col1" in table.column_names
    assert "col2" in table.column_names
    assert "col3" in table.column_names
    assert "col4" in table.column_names


def test_reorder_columns():
    table = ProgressTable("col1", "col2", "col3")
    table.reorder_columns("col3", "col1", "col2")
    assert table.column_names == ["col3", "col1", "col2"]


def test_update_value_in_existing_row():
    table = ProgressTable("col1", "col2")
    table["col1"] = 10
    table.next_row()
    table["col1"] = 20
    assert table["col1", -1] == 20


def test_update_value_in_non_existing_row():
    table = ProgressTable("col1", "col2")

    with pytest.raises(IndexError):
        table.update("col1", 10, row=5)


def test_close_table():
    table = ProgressTable("col1", "col2")
    table.close()

    with pytest.raises(TableClosedError):
        table["col1"] = 10


def test_add_row_with_values():
    table = ProgressTable("col1", "col2")
    table.add_row(1, 2)
    assert table["col1", 0] == 1
    assert table["col2", 0] == 2


def test_add_multiple_rows():
    table = ProgressTable("col1", "col2")
    table.add_rows([1, 2], [3, 4])
    assert table["col1", 0] == 1
    assert table["col2", 0] == 2
    assert table["col1", 1] == 3
    assert table["col2", 1] == 4


def test_progress_bar_updates():
    table = ProgressTable("col1", "col2")
    pbar = table.pbar(range(5))
    for _ in pbar:
        pass
    assert pbar._step == 5
