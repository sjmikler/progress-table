# Progress Table

[![PyPi version](https://img.shields.io/badge/dynamic/json?label=latest&query=info.version&url=https%3A%2F%2Fpypi.org%2Fpypi%2Fprogress-table%2Fjson)](https://pypi.org/project/progress-table)
[![PyPI license](https://img.shields.io/badge/dynamic/json?label=license&query=info.license&url=https%3A%2F%2Fpypi.org%2Fpypi%2Fprogress-table%2Fjson)](https://pypi.org/project/progress-table)

Lightweight utility to display the progress of your process as a pretty table in the command line.

![example](https://github.com/gahaalt/progress-table/blob/main/media/progress-table-example.png?raw=true)

Designed to monitor machine learning experiments, but can be used for anything.
Allows you to quickly see what is going on.
Increases readability and cuteness of your command line logging.

## Features

* Displaying pretty table in the terminal
* Progress bar embedded into the table
* Exporting data as lists, numpy arrays or pandas dataframes
* Built-in basic data aggregation: `sum` and `mean`

## Goal

Change this:

![example](https://github.com/gahaalt/progress-table/blob/main/media/progress-before3.gif?raw=true)

Into this:

![example](https://github.com/gahaalt/progress-table/blob/main/media/progress-after3.gif?raw=true)

## Example

> Click here for examples of integration with PyTorch and Keras:
> [integrations.md](https://github.com/gahaalt/progress-table/blob/main/integrations.md).

```python
import random
import time
from progress_table import ProgressTable

# Define the columns at the beginning
table = ProgressTable(
    columns=["step", "x", "x squared"],

    # Default values:
    refresh_rate=10,
    num_decimal_places=4,
    default_column_width=8,
    print_row_on_update=True,
    reprint_header_every_n_rows=30,
    custom_format=None,
    embedded_progress_bar=False,
)
table.add_column("x", width=3)
table.add_column("x root", color="red")
table.add_column("random average", color=["bright", "red"], aggregate="mean")

for step in range(10):
    x = random.randint(0, 200)

    # There are two equivalent ways to add new values
    # First:
    table["step"] = step
    table["x"] = x
    # Second:
    table.update("x root", x ** 0.5)
    table.update("x squared", x ** 2)

    # Display the progress bar by wrapping the iterator
    for _ in table(range(10)):
        # You can use weights for aggregated values
        table.update("random average", random.random(), weight=1)
        time.sleep(0.1)

    # Go to the next row when you're ready
    table.next_row()

# Close the table when it's ready
table.close()

# Export your data
data = table.to_list()
pandas_df = table.to_df()
np_array = table.to_numpy()
```

```stdout
┌──────────┬─────┬───────────┬──────────┬────────────────┐
│   step   │  x  │ x squared │  x root  │ random average │
├──────────┼─────┼───────────┼──────────┼────────────────┤
│    0     │  50 │    2500   │  7.0711  │     0.2796     │
│    1     │ 186 │   34596   │ 13.6382  │     0.3897     │
│    2     │  70 │    4900   │  8.3666  │     0.5524     │
│    3     │ 170 │   28900   │ 13.0384  │     0.5030     │
│    4     │  71 │    5041   │  8.4261  │     0.5756     │
│    5     │  17 │    289    │  4.1231  │     0.3962     │
│    6     │  77 │    5929   │  8.7750  │     0.6333     │
│    7     │ 138 │   19044   │ 11.7473  │     0.6287     │
│    8     │ 131 │   17161   │ 11.4455  │     0.3324     │
│    9     │ 154 │   23716   │ 12.4097  │     0.4751     │
└──────────┴─────┴───────────┴──────────┴────────────────┘
```

## Installation

Install Progress Table easily with pip:

```
pip install progress-table
```

## Links

* [See on GitHub](https://github.com/gahaalt/progress-table)
* [See on PyPI](https://pypi.org/project/progress-table)

## Alternatives

* Progress bars: great for tracking progress, but they do not provide pretty CLI data display
	* `tqdm`
	* `Keras.utils.Progbar`

* Libraries displaying data: great for presenting data, but they lack the tracking progress element
	* `tabulate`
	* `texttable`
