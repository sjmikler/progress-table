#  Copyright (c) 2022 Szymon Mikler

import time

from colorama import Fore, Style

from progress_table import ProgressTable

progress = ProgressTable(columns=["EPOCH", "ACCURACY"])

progress.add_column("EP", width=0, color=Style.BRIGHT)
progress.add_column("STEP", width=0)
progress.add_column("TRAIN ACC", color=Fore.GREEN)
progress.add_column("VERY LONG TRAIN ACC")
progress.add_column("TIME")

for i in progress(range(3)):
    pass

for x in progress(range(1000)):
    time.sleep(0.001)

for _ in range(30):
    progress["EP"] = 1
    progress["TIME"] = 0.1
    progress["TRAIN ACC"] = 0.8
    progress["TRAIN ACC"] = 1 / 3

    progress.next_row()

for x in progress(range(10)):
    time.sleep(0.1)
progress["EP"] = 2
progress["TIME"] = 0.01
progress["TRAIN ACC"] = 1 / 3
progress["TRAIN ACC"] = 0.9
progress["VERY LONG TRAIN ACC"] = 0.9

progress.next_row()

for x in progress(range(10)):
    time.sleep(0.1)

progress["EP"] = 2
progress["TIME"] = 0.01
progress["TRAIN ACC"] = 1 / 3
progress["TRAIN ACC"] = 0.9
progress["VERY LONG TRAIN ACC"] = 0.9

progress.next_row()

progress.close()
