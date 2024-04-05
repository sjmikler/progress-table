#  Copyright (c) 2022-2024 Szymon Mikler

import hashlib
import random
import shutil
from io import StringIO

from progress_table import ProgressTableV1


def set_seed():
    random.seed(42)


def test_case_1():
    set_seed()
    shutil.get_terminal_size()
    out_buffer = StringIO()

    # Define the columns at the beginning
    table = ProgressTableV1(
        columns=["step", "x", "x squared"],
        # Default arguments:
        refresh_rate=1000000000,
        num_decimal_places=4,
        default_column_width=8,
        default_column_alignment="center",
        print_row_on_update=True,
        reprint_header_every_n_rows=10,
        custom_format=None,
        embedded_progress_bar=True,
        pbar_show_throughput=False,
        pbar_show_progress=True,
        file=out_buffer,
    )
    table.add_column("x", width=3)
    table.add_column("x root", color="red")
    table.add_column("random average", color=["bright", "red"], aggregate="mean")

    for _ in range(10):
        for step in range(10):
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

            table.update("x root", x**0.5)

            # Go to the next row when you're ready
            if step % 5 == 0:
                split = True
            else:
                split = False

            table.next_row(split=split)

    # Close the table when it's ready
    table.close()

    outputs = out_buffer.getvalue()
    md5hash = hashlib.md5(outputs.encode()).hexdigest()
    assert md5hash == "9911ff8b907db908e208778afaff508c", f"Got {md5hash}, expected 9911ff8b907db908e208778afaff508c"
