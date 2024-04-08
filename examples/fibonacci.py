#  Copyright (c) 2022-2024 Szymon Mikler

from progress_table import ProgressTable


def fibonacci(n):
    if n <= 1:
        return n, 1
    else:
        r1, c1 = fibonacci(n - 1)
        r2, c2 = fibonacci(n - 2)
        return r1 + r2, c1 + c2 + 1


def main(**overrides):
    table = ProgressTable(**overrides, default_column_alignment="left", interactive=2)
    table.add_column("n")
    table.add_column("fibonacci value")
    table.add_column("number of calls")

    for n in table(36):
        result, number_of_calls = fibonacci(n)
        table["n"] = n
        table["fibonacci value"] = result
        table["number of calls"] = number_of_calls
        table.next_row()
    table.close()


if __name__ == "__main__":
    main()
