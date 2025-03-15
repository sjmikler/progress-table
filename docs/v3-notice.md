# Version 3.0.0

Version 3.0.0 of Progress Table is now available.

It introduces:

* Important internal changes to increase the stability.
* Minor breaking changes in the API.

## BREAKING API CHANGES

---

```python
ProgressTable(["c1", "c2", "c3"])
```

↑ becomes now ↓

```python
ProgressTable("c1", "c2", "c3")
# or
ProgressTable(columns=["c1", "c2", "c3"])
```

---

```python
ProgressTable([], 1, 20)
```

↑ will raise an error. Use named arguments instead ↓

```python
ProgressTable(interactive=1, refresh_rate=20)
```

---

```python
from progress_table import ProgressTableV1, ProgressTableV2
```

↑ multiple versions of ProgressTable are not available anymore. Use ↓

```python
from progress_table import ProgressTable
```

---

