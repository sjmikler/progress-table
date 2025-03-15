#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

import pytest

from progress_table import ProgressTable, progress_table, styles


def test_add_column_with_custom_properties():
    table = ProgressTable()
    table.add_column("col1", width=15, color="red", alignment="right", aggregate="sum")
    assert table.column_widths["col1"] == 15
    assert table.column_colors["col1"] == "\x1b[31m"
    assert table.column_alignments["col1"] == "right"
    assert callable(table.column_aggregates["col1"])


def test_add_columns_with_same_properties():
    table = ProgressTable()
    table.add_columns("col1", "col2", width=10, color="blue", alignment="center", aggregate="mean")
    assert table.column_widths["col1"] == 10
    assert table.column_colors["col1"] == "\x1b[34m"
    assert table.column_alignments["col1"] == "center"
    assert callable(table.column_aggregates["col1"])
    assert table.column_widths["col2"] == 10
    assert table.column_colors["col2"] == "\x1b[34m"
    assert table.column_alignments["col2"] == "center"
    assert callable(table.column_aggregates["col2"])


def test_add_columns_with_integer_argument():
    table = ProgressTable()
    table.add_columns(3, width=5)
    assert "0" in table.column_names
    assert "1" in table.column_names
    assert "2" in table.column_names
    assert table.column_widths["0"] == 5
    assert table.column_widths["1"] == 5
    assert table.column_widths["2"] == 5


def test_reorder_columns():
    table = ProgressTable("col1", "col2", "col3")
    table.reorder_columns("col3", "col1", "col2")
    assert table.column_names == ["col3", "col1", "col2"]


def test_reorder_columns_no_change():
    table = ProgressTable("col1", "col2", "col3")
    table.reorder_columns("col1", "col2", "col3")
    assert table.column_names == ["col1", "col2", "col3"]


def test_update_value_in_specific_row():
    table = ProgressTable("col1", "col2")
    table["col1"] = 10
    table.next_row()
    table["col1"] = 20
    table.update("col1", 5, row=0)
    assert table[("col1", 0)] == 5
    assert table[("col1", 1)] == 20


def test_update_with_column_kwargs():
    table = ProgressTable()
    table.update("new_col", 10, width=20, color="green")
    assert "new_col" in table.column_names
    assert table.column_widths["new_col"] == 20
    assert table.column_colors["new_col"] == "\x1b[32m"


def test_get_item_with_tuple_key():
    table = ProgressTable("col1", "col2")
    table["col1"] = 10
    assert table[("col1", -1)] == 10


def test_get_item_with_invalid_column():
    table = ProgressTable("col1", "col2")
    with pytest.raises(AssertionError):
        table["invalid_col"]


def test_update_from_dict():
    table = ProgressTable("col1", "col2")
    data = {"col1": 10, "col2": "abc"}
    table.update_from_dict(data)
    assert table["col1"] == 10
    assert table["col2"] == "abc"


def test_next_row_with_color_dict():
    table = ProgressTable("col1", "col2")
    table["col1"] = 1
    table["col2"] = 2
    table.next_row(color={"col1": "red", "col2": "blue"})
    assert table._data_rows[0].colors["col1"] == table.column_colors["col1"] + "\x1b[31m"
    assert table._data_rows[0].colors["col2"] == table.column_colors["col2"] + "\x1b[34m"


def test_next_row_with_split_and_header():
    table = ProgressTable("col1")
    table.next_row(split=True, header=True)
    assert "SPLIT MID" in table._latest_row_decorations
    assert "HEADER" in table._latest_row_decorations


def test_add_row():
    table = ProgressTable("col1", "col2")
    table.add_row(1, "abc")
    assert table[("col1", 0)] == 1
    assert table[("col2", 0)] == "abc"
    assert len(table._data_rows) == 2


def test_add_rows_with_integer_argument():
    table = ProgressTable("col1")
    table.add_rows(2)
    assert len(table._data_rows) == 3


def test_num_rows():
    table = ProgressTable()
    table.add_rows(5)
    assert table.num_rows() == 6


def test_num_columns():
    table = ProgressTable("col1", "col2", "col3")
    assert table.num_columns() == 3


def test_close():
    table = ProgressTable("col1")
    table.close()
    assert table._closed


def test_write_message():
    table = ProgressTable("col1", "col2")
    table.add_row(1, 2)
    table.write("test message")
    assert isinstance(table._display_rows[-1], str)
    assert "USER WRITE" in table._display_rows[-1]


def test_to_list():
    table = ProgressTable("col1", "col2")
    table.add_row(1, "a")
    table.add_row(2, "b")
    expected_list = [[1, "a"], [2, "b"]]
    assert table.to_list() == expected_list


def test_table_at_setitem_slice_rows_cols():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[:2, :] = 5
    assert table.at[:2, :] == [[5, 5], [5, 5]]


def test_table_at_setitem_slice_rows():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[0, :] = 5
    assert table.at[0, :] == [5, 5]
    assert table.at[1, :] == [None, None]


def test_table_at_setitem_slice_cols():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[:2, 0] = 5
    assert table.at[:2, 0] == [5, 5]
    assert table.at[:2, 1] == [None, None]


def test_table_at_setitem_int_rows_cols():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[1, 0] = 5
    assert table.at[1, 0] == 5
    assert table.at[0, 0] is None


def test_table_at_setitem_slice_rows_cols_mode():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[:2, :, "weights"] = 1
    assert table.at[:2, :, "weights"] == [[1, 1], [1, 1]]


def test_table_at_setitem_slice_rows_cols_mode_colors():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[:, :, "colors"] = "red"
    assert table._data_rows[0].colors["col1"] == "\x1b[31m"
    assert table._data_rows[0].colors["col2"] == "\x1b[31m"
    assert table._data_rows[1].colors["col1"] == "\x1b[31m"
    assert table._data_rows[1].colors["col2"] == "\x1b[31m"


def test_table_at_getitem_slice_rows_cols():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[0, 0] = 5
    table.at[1, 1] = 10
    assert table.at[:2, :] == [[5, None], [None, 10]]


def test_table_at_getitem_slice_rows():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[0, 0] = 5
    table.at[1, 1] = 10
    assert table.at[0, :] == [5, None]


def test_table_at_getitem_slice_cols():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[0, 0] = 5
    table.at[1, 1] = 10
    assert table.at[:2, 1] == [None, 10]


def test_table_at_getitem_int_rows_cols():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[0, 0] = 5
    table.at[1, 1] = 10
    assert table.at[1, 1] == 10


def test_table_at_getitem_slice_rows_cols_mode():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[:2, :, "weights"] = 1
    assert table.at[:2, :, "weights"] == [[1, 1], [1, 1]]


def test_table_at_getitem_slice_rows_cols_mode_colors():
    table = ProgressTable("col1", "col2")
    table.add_rows(2)
    table.at[:2, :, "colors"] = "red"
    assert table.at[:2, :, "colors"] == [["\x1b[31m", "\x1b[31m"], ["\x1b[31m", "\x1b[31m"]]


def test_aggregate_dont():
    assert progress_table.aggregate_dont(5, 10) == 5


def test_aggregate_mean():
    assert progress_table.aggregate_mean(5, 10, 1, 1) == 7.5


def test_aggregate_sum():
    assert progress_table.aggregate_sum(5, 10) == 15


def test_aggregate_max():
    assert progress_table.aggregate_max(5, 10) == 10


def test_aggregate_min():
    assert progress_table.aggregate_min(5, 10) == 5


def test_get_aggregate_fn_none():
    assert callable(progress_table.get_aggregate_fn(None))


def test_get_aggregate_fn_mean():
    assert callable(progress_table.get_aggregate_fn("mean"))


def test_get_aggregate_fn_sum():
    assert callable(progress_table.get_aggregate_fn("sum"))


def test_get_aggregate_fn_max():
    assert callable(progress_table.get_aggregate_fn("max"))


def test_get_aggregate_fn_min():
    assert callable(progress_table.get_aggregate_fn("min"))


def test_get_aggregate_fn_invalid_string():
    with pytest.raises(ValueError):
        progress_table.get_aggregate_fn("invalid")


def test_get_aggregate_fn_invalid_type():
    with pytest.raises(ValueError):
        progress_table.get_aggregate_fn(123)


def test_get_default_format_fn_int():
    fmt = progress_table.get_default_format_fn(2)
    assert fmt(5) == "5"


def test_get_default_format_fn_float():
    fmt = progress_table.get_default_format_fn(2)
    assert fmt(5.123) == "5.12"


def test_get_default_format_fn_invalid():
    fmt = progress_table.get_default_format_fn(2)
    assert fmt("abc") == "abc"


def test_pbar_iterable():
    table = ProgressTable()
    iterable = range(5)
    pbar = table.pbar(iterable)
    assert pbar.iterable == iterable
    assert pbar._total == 5


def test_pbar_int():
    table = ProgressTable()
    pbar = table.pbar(5)
    assert isinstance(pbar.iterable, range)
    assert pbar._total == 5


def test_pbar_static_position():
    table = ProgressTable()
    pbar = table.pbar(5, position=1, static=True)
    assert pbar.position == 1
    assert pbar.static is True


def test_pbar_dynamic_position():
    table = ProgressTable()
    pbar = table.pbar(5, position=2, static=False)
    assert pbar.position == 2
    assert pbar.static is False


def test_pbar_no_total_sized():
    table = ProgressTable()
    iterable = [1, 2, 3]
    pbar = table.pbar(iterable)
    assert pbar._total == 3


def test_pbar_no_total_unSized():
    table = ProgressTable()
    iterable = iter([1, 2, 3])
    pbar = table.pbar(iterable)
    assert pbar._total == 0


def test_pbar_custom_styles():
    table = ProgressTable()
    pbar = table.pbar(5, style="square", style_embed="cdots")
    assert isinstance(pbar.style, styles.PbarStyleSquare)
    assert isinstance(pbar.style_embed, styles.PbarStyleCdots)


def test_pbar_custom_colors():
    table = ProgressTable()
    pbar = table.pbar(5, color="red", color_empty="blue")
    assert pbar.style.color == "\x1b[31m"
    assert pbar.style.color_empty == "\x1b[34m"
    assert pbar.style_embed.color == "\x1b[31m"
    assert pbar.style_embed.color_empty == "\x1b[34m"


def test_pbar_custom_description():
    table = ProgressTable()
    pbar = table.pbar(5, description="Test Progress")
    assert pbar.description == "Test Progress"


def test_pbar_custom_show_flags():
    table = ProgressTable()
    pbar = table.pbar(
        5,
        show_throughput=False,
        show_progress=False,
        show_percents=False,
        show_eta=False,
    )
    assert pbar.show_throughput is False
    assert pbar.show_progress is False
    assert pbar.show_percents is False
    assert pbar.show_eta is False


def test_pbar_call_method():
    table = ProgressTable()
    pbar = table(5)
    assert isinstance(pbar, progress_table.TableProgressBar)


def test_table_progress_bar_update():
    table = ProgressTable()
    pbar = table.pbar(10)
    pbar.update(3)
    assert pbar._step == 3


def test_table_progress_bar_reset():
    table = ProgressTable()
    pbar = table.pbar(10)
    pbar.update(5)
    pbar.reset()
    assert pbar._step == 0
    assert pbar._total == 10
