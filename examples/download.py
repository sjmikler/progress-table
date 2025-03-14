#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License
import random
import time
from concurrent.futures import ThreadPoolExecutor

import colorama

from progress_table import ProgressTable


def create_random_file_info():
    info = {}
    index = random.randint(0, 1000)
    types = ["image_.jpg", "video_.mp4", "archive_.zip", "movie_.avi"]
    info["name"] = random.choice(types).replace("_", str(index))
    info["size int"] = random.randint(1, 1000)
    info["size unit"] = random.choice(["KB", "MB", "GB"])
    info["time"] = 2 + random.random() * 10
    return info


NUM_FILES = 15
files_to_download = [create_random_file_info() for _ in range(NUM_FILES)]


table = ProgressTable(
    pbar_show_progress=False,
    pbar_show_throughput=False,
    pbar_show_eta=True,
    default_column_width=8,
    default_header_color="bold",
)

main_pbar = table.pbar(
    NUM_FILES,
    position=1,
    show_progress=True,
    style="square clean blue",
)


def fake_download(idx, file_info):
    # Modify pbar styling so that emebedded pbar shows color only
    pbar = table.pbar(1, position=idx, static=True, style_embed="hidden", color=colorama.Back.BLACK)

    # Update table values in a specifc row
    table.update("total size", str(file_info["size int"]) + " " + file_info["size unit"], row=idx)
    table.update("name", file_info["name"], row=idx)
    table.update("seeds", random.randint(1, 30), row=idx)
    table.update("peers", random.randint(0, 5), row=idx)

    number_of_errors = 0

    t0 = time.time()
    td = 0
    while True:
        pbar.set_step(td / file_info["time"])  # Set specific pbar progress

        # Maybe add an error to the error counter
        if random.random() < 0.004:
            number_of_errors += 1
            random_delay = random.random()
            time.sleep(random_delay)
            t0 += random_delay

        downloaded_units = int(td / file_info["time"] * file_info["size int"])
        table.update("downloaded", str(downloaded_units) + " " + file_info["size unit"], row=idx)
        table.update("warnings", number_of_errors, row=idx)
        time.sleep(0.01)

        td = time.time() - t0
        if td > file_info["time"]:
            break
    pbar.close()
    main_pbar.update()


table.add_column("name", alignment="right", width=25)
table.add_columns("total size", "downloaded", "seeds", "peers", "warnings")
table.add_rows(len(files_to_download), color="blue")

threads = []
executor = ThreadPoolExecutor()

for idx, pkg in enumerate(files_to_download):
    threads.append(executor.submit(fake_download, idx, pkg))

for thread in threads:
    thread.result()

table.close()
