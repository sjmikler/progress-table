#  Copyright (c) 2022 Szymon Mikler

from progress_table import ProgressTable
from colorama import Fore
import time

progress = ProgressTable(progress_bar_fps=10)

progress.add_column("EP", width=0)
progress.add_column("STEP", width=0)
progress.add_column("TRAIN ACC", color=Fore.GREEN)
progress.add_column("VERY LONG TRAIN ACC")
progress.add_column("TIME")

progress.next_row()

for x in progress(range(1000)):
    time.sleep(0.001)

progress["EP"] = 1
progress["TIME"] = 0.1
progress["TRAIN ACC"] = 0.8
progress["TRAIN ACC"] = 0.9

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

progress.close()
