#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

from io import StringIO


def test_simple_example_1():
    from progress_table import ProgressTable

    file = StringIO()
    table = ProgressTable(interactive=0, file=file)
    table.add_column("Value")
    table.add_rows(3)  # Adding empty rows

    table.update(name="Value", value=1.0, row=1)
    table.update(name="Value", value=2.0, row=0)
    table.update(name="Value", value=3.0, row=2)
    table.close()

    results = file.getvalue()
    expected = """
╭──────────╮
│  Value   │
├──────────┤
│  2.0000  │
│  1.0000  │
│  3.0000  │
╰──────────╯
"""
    assert results.strip() == expected.strip()


def test_simple_example_2():
    from progress_table import ProgressTable

    file = StringIO()
    table = ProgressTable(interactive=0, file=file)
    table.add_columns(4)  # Add more columns with automatic names
    table.add_rows(4)  # Adding empty rows

    table.at[:] = 0.0  # Initialize all values to 0.0
    table.at[0, :] = 2.0  # Set all values in the first row to 2.0
    table.at[:, 1] = 2.0  # Set all values in the second column to 2.0
    table.at[2, 0] = 3.0  # Set the first column in the second-to-last row to 3.0
    table.close()

    results = file.getvalue()
    expected = """
╭──────────┬──────────┬──────────┬──────────╮
│    0     │    1     │    2     │    3     │
├──────────┼──────────┼──────────┼──────────┤
│  2.0000  │  2.0000  │  2.0000  │  2.0000  │
│  0.0000  │  2.0000  │  0.0000  │  0.0000  │
│  3.0000  │  2.0000  │  0.0000  │  0.0000  │
│  0.0000  │  2.0000  │  0.0000  │  0.0000  │
╰──────────┴──────────┴──────────┴──────────╯
"""
    assert results.strip() == expected.strip()


def test_example_3():
    import random

    from progress_table import ProgressTable

    random.seed(42)

    file = StringIO()
    table = ProgressTable(interactive=0, file=file)
    table.add_column("x")

    for _step in range(9):
        x = random.randint(0, 200)

        table["x"] = x
        table.update("x", value=x, weight=1.0)

        for _ in table(13):
            table["y"] = random.randint(0, 200)
            table["x-y"] = table["x"] - table["y"]
            table.update("average x-y", value=table["x-y"], weight=1.0, aggregate="mean")

        table.next_row()

    table.close()
    results = file.getvalue()
    expected = """
╭──────────┬──────────┬──────────┬─────────────╮
│    x     │    y     │   x-y    │ average x-y │
├──────────┼──────────┼──────────┼─────────────┤
│   163    │    22    │   141    │   71.9231   │
│   151    │   166    │   -15    │   67.0769   │
│   179    │    71    │   108    │   77.7692   │
│    39    │   186    │   -147   │   -45.8462  │
│   117    │    17    │   100    │   16.7692   │
│    11    │    41    │   -30    │   -79.9231  │
│    94    │   186    │   -92    │   -29.0769  │
│    62    │    14    │    48    │   -55.5385  │
│    58    │   101    │   -43    │   -33.1538  │
╰──────────┴──────────┴──────────┴─────────────╯
"""
    assert results.strip() == expected.strip()
