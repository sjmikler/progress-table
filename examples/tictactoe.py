#  Copyright (c) 2022-2025 Szymon Mikler

import random
import time

from progress_table import ProgressTable

BOARD_SIZE = 10
STREAK_LENGTH = 5


def main(random_seed=random.randint(0, 100), sleep_duration=0.05, **overrides):
    random.seed(random_seed)

    table = ProgressTable(
        pbar_embedded=False,
        default_column_width=1,
        print_header_on_top=False,
        pbar_style="circle alt red",
        **overrides,
    )

    print("Two players are playing tic-tac-toe.")
    print(f"The first to get a streak of {STREAK_LENGTH} wins.")

    # Use convenience method to add multiple columns at once
    table.add_columns(BOARD_SIZE)

    # Adding multiple new rows at once is also possible
    # We get the 1-st row automatically, so we add one less
    table.add_rows(BOARD_SIZE, split=True)

    sign = 0
    x = 0
    y = 0
    for i in table(BOARD_SIZE * BOARD_SIZE, show_throughput=False, show_progress=True):
        current_symbol = True
        while current_symbol:
            x = random.randint(0, BOARD_SIZE - 1)
            y = random.randint(0, BOARD_SIZE - 1)
            current_symbol = table.at[y, x]
        sign = 1 - sign

        table.at[y, x] = "X" if sign else "O"
        table.at[y, x, "COLOR"] = "CYAN" if sign else "BLUE"

        finished = False

        # Coloring the winner
        for row_idx in range(BOARD_SIZE):
            row = table.at[row_idx, :]
            for j in range(BOARD_SIZE - STREAK_LENGTH):
                values = set(row[j : j + STREAK_LENGTH])
                if values == {"X"} or values == {"O"}:
                    table.at[row_idx, j : j + STREAK_LENGTH, "C"] = "bold red"
                    finished = True
        for col_idx in range(BOARD_SIZE):
            col = table.at[:, col_idx]

            for j in range(BOARD_SIZE - STREAK_LENGTH):
                values = set(col[j : j + STREAK_LENGTH])
                if values == {"X"} or values == {"O"}:
                    table.at[j : j + STREAK_LENGTH, col_idx, "C"] = "bold red"
                    finished = True
        if finished:
            break
        time.sleep(sleep_duration)
    table.close()


if __name__ == "__main__":
    main()
