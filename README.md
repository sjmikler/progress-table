# Progress Table

Lightweight utility to display the progress of your process as a pretty table in the command line.

![example](https://github.com/gahaalt/progress-table/blob/main/media/progress_table_example.png?raw=true)

Designed to monitor machine learning experiments, but can be used for anything.
Allows you to quickly see what is going on.
Increases readability and cuteness of your CLI logging.

Change this:

![example](https://github.com/gahaalt/progress-table/blob/main/media/before.gif?raw=true)

Into this:

![example](https://github.com/gahaalt/progress-table/blob/main/media/after.gif?raw=true)

## Example

```python
import random
import time
from progress_table import ProgressTable

# At the beginning, define all the columns
progress = ProgressTable(columns=["step", "x"], num_decimal_places=6)
progress.add_column("x squared", aggregate="sum")
progress.add_column("x root", color="red", width=12)

for step in range(20):
    progress["step"] = step

    # Display a progress bar by wrapping the iterator
    for _ in progress(range(10)):
        time.sleep(0.1)

    x = random.randint(0, 200)

    # There are ways to add new values
    progress["x"] = x  # OR
    progress.update("x root", x ** 0.5)

    # You can use weights for aggregated values
    progress.update("x squared", x ** 2, weight=1)

    # Go to next row when you're ready
    progress.next_row()

# Close the table when it's ready
progress.close()

# Export your data
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

* Progress bars: great for tracking progress, but they do not provide pretty CLI data display
	* `tqdm`
	* `Keras.utils.Progbar`

* Libraries displaying data: great for presenting data, but they lack the tracking progress element
	* `tabulate`
	* `texttable`
