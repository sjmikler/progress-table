# Progress Table

Display progress as a pretty table in CLI.

Designed to monitor machine learning experiments, but can be used for anything.

Produce pretty tables on the fly, during your experiment to quickly see what is going on.

![example](progress_table_example.png)

## Example

```python
from progress_table import ProgressTable

progress = ProgressTable(columns=["x", "x square"])
progress.add_column("x root", color=)
```

## Alternatives

* `tqdm`: great and quick tool, but combining CLI logging with it is not pretty
* `keras.utils.Progbar`: as above