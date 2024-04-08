#  Copyright (c) 2024 Szymon Mikler

import random
import sys
import time

from progress_table import ProgressTable


def main(**overrides):
    table = ProgressTable(
        columns=["step", "x", "x squared"],
        interactive=2,
        refresh_rate=2,
        num_decimal_places=4,
        default_column_width=8,
        default_column_alignment="center",
        print_row_on_update=True,
        print_header_every_n_rows=10,
        pbar_show_progress=True,
        file=sys.stdout,
        **overrides,
    )
    table.add_column("x", width=3)
    table.add_column("x root", color="red")
    table.add_column("random average", color=["bright", "red"], aggregate="mean")

    for _ in table(2):
        for step in table(10):
            x = random.randint(0, 200)

            # There are two equivalent ways to add new values
            # First:
            table["step"] = step
            table["x"] = x
            # Second:
            table.update("x squared", x**2)

            # Display the progress bar by wrapping the iterator
            for _ in table(100):
                # You can use weights for aggregated values
                table.update("random average", random.random(), weight=1)
                time.sleep(0.01)
            time.sleep(0.01)

            table.update("x root", x**0.5)

            # Go to the next row when you're ready
            if step % 5 == 0:
                split = True
            else:
                split = False

            table.next_row(split=split)

    # Close the table when it's ready
    table.close()


if __name__ == "__main__":
    main()
