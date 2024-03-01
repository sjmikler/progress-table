import random
import time

from progress_table import ProgressTable

table = ProgressTable()

total = 0
target = 1000
pbar = table.pbar(1000)

while total < target:
    new_value = random.randint(0, 100)
    total += new_value

    table["random int"] = new_value
    table["random float"] = random.random()
    table["current total"] = total

    pbar.update(new_value)
    table.next_row()
    time.sleep(0.1)
table.close()
