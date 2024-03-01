import time

from progress_table import ProgressTable


def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


def fibonacci_timed(n):
    time0 = time.perf_counter()
    result = fibonacci(n)
    time1 = time.perf_counter()
    return result, time1 - time0


table = ProgressTable()

for n in table(40):
    result, td = fibonacci_timed(n)
    table["n"] = n
    table["time (s)"] = td
    table["value"] = result
    table.next_row()
table.close()
