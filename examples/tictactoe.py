#  Copyright (c) 2024 Szymon Mikler

import random
import time

from progress_table import ProgressTable, styles

BOARD_SIZE = 10
STREAK_LENGTH = 2

table = ProgressTable(
    # table_style=styles.StyleAscii(),
    default_column_width=3,
    print_header_on_top=False,
)

# Column names don't matter for this example
table.add_columns(*[str(i) for i in range(BOARD_SIZE)])

# Adding multiple new rows
for row in range(BOARD_SIZE):
    table.next_row(split=True)


sign = 0
x = 0
y = 0
for i in table(BOARD_SIZE * BOARD_SIZE):
    current_symbol = True
    while current_symbol:
        x = random.randint(0, BOARD_SIZE - 1)
        y = random.randint(0, BOARD_SIZE - 1)
        current_symbol = table[y, x]
    sign = 1 - sign

    table.update(x, "X" if sign else "O", row=y, cell_color="bold red" if random.random() > 0.5 else None)
    time.sleep(0.025)

table.close()
