# Progress Table

Lightweight utility to display progress as a pretty table in the command line.

Designed to monitor machine learning experiments, but can be used for anything.

Produces pretty tables on the fly during your experiment, allowing you to quickly see what is going on.

![example](https://github.com/gahaalt/progress-table/blob/main/progress_table_example.png?raw=true)

## Example

```python
import random
import time
from colorama import Fore
from progress_table import ProgressTable

progress = ProgressTable(columns=["step", "x", "x squared"], default_column_width=2)
progress.add_column("x root", color=Fore.RED)

for step in range(20):
    progress["step"] = step  # insert value in the current row

    for _ in progress(range(10)):  # progress bar
        time.sleep(0.1)  # simulate artificial work

    x = random.randint(0, 100)
    progress["x"] = x
    progress["x squared"] = x ** 2
    progress["x root"] = x ** 0.5
    progress.next_row()

progress.close()

# export your data
data = progress.to_list()
pandas_df = progress.df()
np_array = progress.numpy()
```

```stdout
┌──────┬────┬───────────┬────────┐
│ step │ x  │ x squared │ x root │
├──────┼────┼───────────┼────────┤
│  0   │ 8  │     64    │ 2.8284 │
│  1   │ 78 │    6084   │ 8.8317 │
│  2   │ 21 │    441    │ 4.5825 │
│  3   │ 28 │    784    │ 5.2915 │
│  4   │ 11 │    121    │ 3.3166 │
│  5   │ 6  │     36    │ 2.4494 │
│  6   │ 44 │    1936   │ 6.6332 │
│  7   │ 28 │    784    │ 5.2915 │
│  8   │ 6  │     36    │ 2.4494 │
│  9   │ 20 │    400    │ 4.4721 │
│  10  │ 73 │    5329   │ 8.5440 │
│  11  │ 56 │    3136   │ 7.4833 │
│  12  │ 38 │    1444   │ 6.1644 │
│  13  │ 44 │    1936   │ 6.6332 │
│  14  │ 83 │    6889   │ 9.1104 │
│  15  │ 51 │    2601   │ 7.1414 │
│  16  │ 96 │    9216   │ 9.7979 │
│  17  │ 65 │    4225   │ 8.0622 │
│  18  │ 39 │    1521   │ 6.2449 │
│  19  │ 78 │    6084   │ 8.8317 │
└──────┴────┴───────────┴────────┘
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

* Progress bars: many of them are great and useful, but they do not provide pretty CLI logging