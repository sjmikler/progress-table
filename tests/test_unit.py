from progress_table.progress_table import ProgressTable


def test_aggregate_mean():
    table = ProgressTable()
    table.add_column("value", aggregate="mean")
    assert table.column_aggregates["value"].__name__ == "aggregate_mean"

    for i in range(10):
        table["value"] = i

    assert table["value"] == 4.5


def test_aggregate_sum():
    table = ProgressTable()
    table.add_column("value", aggregate="sum")
    assert table.column_aggregates["value"].__name__ == "aggregate_sum"

    for i in range(10):
        table["value"] = i

    assert table["value"] == 45


def test_aggregate_min():
    table = ProgressTable()
    table.add_column("value", aggregate="min")
    assert table.column_aggregates["value"].__name__ == "aggregate_min"

    for i in range(10):
        table["value"] = i

    assert table["value"] == 0


def test_aggregate_max():
    table = ProgressTable()
    table.add_column("value", aggregate="max")
    assert table.column_aggregates["value"].__name__ == "aggregate_max"

    for i in range(10):
        table["value"] = i

    assert table["value"] == 9
