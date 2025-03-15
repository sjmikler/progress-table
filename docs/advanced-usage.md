# Advanced usage

## Indexing

Progress Table with `interactive>=2` supports modyfing already closed rows (rows above the current row).
This can be done either with `.update` method or using `.at` indexing which is a shorthand for `AtIndexer` object.


> When using `interactive<2` mode, you can only modify the current row.
> Any changes made to other rows will not be displayed.

### `.update` method

When using `.update` method you update one value at once.
Use column name and row index to specify the cell location.
Example of using `.update` method:

```python
from progress_table import ProgressTable

table = ProgressTable()
table.add_column("Value")
table.add_rows(3)  # Adding empty rows

table.update(name="Value", value=1.0, row=1)
table.update(name="Value", value=2.0, row=0, cell_color="red bold")
table.update(name="Value", value=3.0, row=2)  # modify last-but-one row
table.close()
```

Which might give you the following:

```output
╭──────────╮
│  Value   │
├──────────┤
│  2.0000  │
│  1.0000  │
│  3.0000  │
╰──────────╯
```

### `.at` indexing

When using `.at` indexing you do not use column names, instead you use column indices.
First column has index 0, second 1, etc. Slicing operations are also supported with `.at` indexing.
Treat the table similarly to a numpy array:

```python
from progress_table import ProgressTable

table = ProgressTable()
table.add_columns(4)  # Add more columns with automatic names
table.add_rows(4)  # Adding empty rows

table.at[:] = 0.0  # Initialize all values to 0.0
table.at[0, :] = 2.0  # Set all values in the first row to 2.0
table.at[:, 1] = 2.0  # Set all values in the second column to 2.0
table.at[2, 0] = 3.0  # Set the first column in the second-to-last row to 3.0

table.close()
```

Which should give you the following:

```
╭──────────┬──────────┬──────────┬──────────╮
│    0     │    1     │    2     │    3     │
├──────────┼──────────┼──────────┼──────────┤
│  2.0000  │  2.0000  │  2.0000  │  2.0000  │
│  0.0000  │  2.0000  │  0.0000  │  0.0000  │
│  3.0000  │  2.0000  │  0.0000  │  0.0000  │
│  0.0000  │  2.0000  │  0.0000  │  0.0000  │
╰──────────┴──────────┴──────────┴──────────╯
```

## Progress Bars

There are two types of progress bars in Progress Table: embedded and non-embedded.


> When using `interactive=0` mode, the progress bars will not be displayed.

> When using `interactive=1` mode, progress bars are be displayed only in the bottom row.

### Embedded progress bars

Embedded progress bars are displayed as an overlay under a table row that contains data.
This allows you to see the progress and the new data all at once.
Those progress bars are displayed 'under' the row and are aligned with the data columns.
It is possible to customize the looks of the embedded progress bar by specyfing an argument when creating a table:

```python
from progress_table import ProgressTable

table = ProgressTable(pbar_style_embed="dash")
```

Below we show a sample of available styles for embedded progress bars:

`dash`

```
|   Name   |   Value   |   Number   |
|-----------------------------------|
|   test1  |    1.0    |     42     |
|---test2--|----2.0->  |     37     |
```

`rich`

```
|   Name   |   Value   |   Number   |
|-----------------------------------|
|   test1  |    1.0    |     42     |
|━━━test2━━|━━━━2.0━━  |     37     |
```

`under`

```
|   Name   |   Value   |   Number   |
|-----------------------------------|
|   test1  |    1.0    |     42     |
|___test2__|____2.0__  |     37     |
```

---

To see the exahustive list of available options, one can use the following code:

```python
from progress_table import styles

print(styles.available_pbar_styles())
```

### Non-embedded progress bars

Non-embedded progress bars are displayed as a separate row under the row that contains data.
Optionally, you can force every progress bar, including the embedded ones, to look like a non-embedded and cover the data.
You might want to do that if you aim for specific looks of your progress bars.

```python
from progress_table import ProgressTable

table = ProgressTable(
    pbar_style="square",  # specify specific style
    pbar_embedded=False,  # force all progress bars to be non-embedded
)
```

Below we show a sample of available styles for non-embedded progress bars

---

`square`

```
|   Name   |   Value   |   Number   |
|-----------------------------------|
|   test1  |    1.0    |     42     |
|   test2  |    2.0    |     37     |
|■■■■■■■■■■■■■■■■■■■■□□□□□□□□□□□□□□□|
```

`circle`

```
|   Name   |   Value   |   Number   |
|-----------------------------------|
|   test1  |    1.0    |     42     |
|   test2  |    2.0    |     37     |
| ●●●●●●●●●●●●●●●●●●◉○○○○○○○○○○○○○○○|
```

---

As previously, you can see the exhaustive list of available options by using the following code:

```python
from progress_table import styles

print(styles.available_pbar_styles())
```

> You can create custom styles by following code in `styles.py` file.

### Infobar

You can display detailed information like:

* throughput
* progress in percents
* progress as the current step and total steps
* ETA (estimated time arrival) - estimated time in seconds, minutes or hours when the progress bar will finish
* custom description

To add or remove some of this information, specify the arguments like below.
Additionaly, you can create a progress bar object and specify
all the options only for this specific progress bar.

```python
from progress_table import ProgressTable

table = ProgressTable(
    pbar_show_throughput=True,
    pbar_show_progress=False,
    pbar_show_percents=False,
    pbar_show_eta=False,
)

pbar = table.pbar(
    range(1000),
    description="train epoch",
    show_throughput=True,
    show_progress=False,
    show_percents=False,
    show_eta=True,
    style="circle",
    style_embed="cdots",
)
```

Which, when used, might look like this:

```
│           │           │           │           │
│[train epoch, 24.1 it/s, ETA 53s] ●●●●●●●◉○○○○○│
```

### More progress bar customization

There is more ways to customize the look and feel of your progress bars
by adding special keywords to the style string:

```python
from progress_table import ProgressTable

table = ProgressTable(pbar_style="angled alt red blue")
```

The example above would result in an angled-type pbar with alternative way of displaying empty bars,
with filled bars colored red and empty bars colored blue. There's a separate style string
for the embedded type progress bars - styling of embedded and non-embedded progress bars is indepedent.

```python
from progress_table import ProgressTable

table = ProgressTable(pbar_style_embed="cdots red blue")
```

The available keywords are:

* `alt` - alternative way of displaying empty bars, for example `■` instead of `□`.
  This is only useful when using colors, otherwise you might not be able to differentiate between filled and empty bars.
* `clean` - removes empty bars from the progress bar. Spaces are used instead.
* `red`, `green`, `blue`, `yellow` and other colors available in colorama. If more than one is provided,
  the first one is used for filled bars and the last one is used for empty bars.

---

Additionaly, you can specify the color of the progress bar using
`color` and `color_empty` arguments when creating a progress bar object.
This will override whatever color is set in `style` or `style_embed`.
We can combine this option with `colorama.Back` to modify colors
of the background instead of the foreground symbols.

```python
from progress_table import ProgressTable
import colorama
import time

table = ProgressTable("a", "b", "c")
table.add_rows(1)

pbar = table.pbar(
    range(100),
    style_embed="hidden",
    color=colorama.Back.RED,
    color_empty=colorama.Back.BLUE,
)

for _ in pbar:
    time.sleep(0.1)
```

Try the example above. It contains a different type of embedded progress bar.
Here the typical progress bar symbols will are hidden,
but the background color will show us the progress of the process.
