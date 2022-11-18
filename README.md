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

progress = ProgressTable(columns=["step", "x", "x squared"])
progress.add_column("x root", color=Fore.RED)

for step in range(20):
    progress["step"] = step  # insert step value in the current row

    for _ in progress(range(10)):  # display progress bar
        time.sleep(0.1)  # simulate computations

    x = random.randint(0, 200)
    progress["x"] = x
    progress["x squared"] = x ** 2
    progress["x root"] = x ** 0.5
    progress.next_row()

progress.close()

# export your data
data = progress.to_list()
pandas_df = progress.to_df()
np_array = progress.to_numpy()
```

```stdout
┌──────────┬──────────┬───────────┬──────────┐
│   step   │    x     │ x squared │  x root  │
├──────────┼──────────┼───────────┼──────────┤
│    0     │   114    │   12996   │ 10.67707…│
│    1     │    15    │    225    │ 3.872983…│
│    2     │   118    │   13924   │ 10.86278…│
│    3     │    59    │    3481   │ 7.681145…│
│    4     │   179    │   32041   │ 13.37908…│
│    5     │   186    │   34596   │ 13.63818…│
│    6     │   192    │   36864   │ 13.85640…│
│    7     │    37    │    1369   │ 6.082762…│
│    8     │    75    │    5625   │ 8.660254…│
│    9     │    61    │    3721   │ 7.810249…│
│    10    │    18    │    324    │ 4.242640…│
│    11    │   160    │   25600   │ 12.64911…│
│    12    │   102    │   10404   │ 10.09950…│
│    13    │    99    │    9801   │ 9.949874…│
│    14    │    24    │    576    │ 4.898979…│
│    15    │   164    │   26896   │ 12.80624…│
│    16    │    40    │    1600   │ 6.324555…│
│    17    │    58    │    3364   │ 7.615773…│
│    18    │    91    │    8281   │ 9.539392…│
│    19    │   182    │   33124   │ 13.49073…│
└──────────┴──────────┴───────────┴──────────┘
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