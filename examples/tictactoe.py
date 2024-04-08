#  Copyright (c) 2024 Szymon Mikler

import random
import time

from progress_table import ProgressTable
from progress_table.v1.styles import StyleAsciiBare

table = ProgressTable(
    table_style=StyleAsciiBare(),
)

table.add_columns("0", "1", "2")
table["0"] = ""
table["1"] = ""
table["2"] = ""
table.next_row()
table["0"] = ""
table["1"] = ""
table["2"] = ""
table.next_row()
table["0"] = ""
table["1"] = ""
table["2"] = ""
table.next_row()

sign = 0
x = "0"
y = 0
for i in range(9):
    current = "x"
    while current:
        x = str(random.randint(0, 2))
        y = random.randint(0, 2)
        current = table[y, x]
    sign = 1 - sign
    table[y, x] = "X" if sign else "O"
    time.sleep(0.25)

table.close()
