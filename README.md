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

progress = ProgressTable(columns=["step", "x", "x squared"], num_decimal_places=10)
progress.add_column("x root", color=Fore.RED, width=12)

for step in range(20):
    progress["step"] = step  # insert step value in the current row

    for _ in progress(range(10)):  # display progress bar
        time.sleep(0.1)  # simulate artificial work

    x = random.randint(0, 200)
    progress["x"] = x
    progress["x root"] = x ** 0.5
    progress["x squared"] = x ** 2
    progress.next_row()

progress.close()

# export your data
data = progress.to_list()
pandas_df = progress.to_df()
np_array = progress.to_numpy()
```

```stdout
┌──────────┬──────────┬───────────┬──────────────┐
│   step   │    x     │ x squared │    x root    │
├──────────┼──────────┼───────────┼──────────────┤
│    0     │    39    │    1521   │ 6.2449979984 │
│    1     │    86    │    7396   │ 9.2736184955 │
│    2     │    10    │    100    │ 3.1622776602 │
│    3     │    34    │    1156   │ 5.8309518948 │
│    4     │   178    │   31684   │ 13.341664064…│
│    5     │   141    │   19881   │ 11.874342087…│
│    6     │    66    │    4356   │ 8.1240384046 │
│    7     │    41    │    1681   │ 6.4031242374 │
│    8     │   109    │   11881   │ 10.440306508…│
│    9     │    95    │    9025   │ 9.7467943448 │
│    10    │   137    │   18769   │ 11.704699910…│
│    11    │   166    │   27556   │ 12.884098726…│
│    12    │   105    │   11025   │ 10.246950766…│
│    13    │    63    │    3969   │ 7.9372539332 │
│    14    │    75    │    5625   │ 8.6602540378 │
│    15    │    40    │    1600   │ 6.3245553203 │
│    16    │   192    │   36864   │ 13.856406460…│
│    17    │    15    │    225    │ 3.8729833462 │
│    18    │    42    │    1764   │ 6.4807406984 │
│    19    │    58    │    3364   │ 7.6157731059 │
└──────────┴──────────┴───────────┴──────────────┘
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