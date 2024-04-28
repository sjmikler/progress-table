#  Copyright (c) 2024 Szymon Mikler
import random
import time
from concurrent.futures import ThreadPoolExecutor

import colorama

from progress_table import ProgressTable


def create_random_file():
    info = {}
    index = random.randint(0, 1000)
    types = ["image_.jpg", "video_.mp4", "archive_.zip", "movie_.avi"]
    info["name"] = random.choice(types).replace("_", str(index))
    info["size int"] = random.randint(1, 1000)
    info["size unit"] = random.choice(["KB", "MB", "GB"])
    info["time"] = 2 + random.random() * 10
    return info


packages = [create_random_file() for _ in range(15)]


table = ProgressTable(
    pbar_show_progress=False,
    pbar_show_throughput=False,
    pbar_show_eta=True,
    default_column_width=8,
    # Modify table styling so that emebedded pbar shows color only
    pbar_color=colorama.Back.BLACK,
    pbar_style_embed="none",
)


def fake_download(file_info):
    idx = file_info["idx"]
    pbar = file_info["pbar"]

    name = file_info["name"]
    table.update("total size", str(file_info["size int"]) + " " + file_info["size unit"], row=idx)
    table.update("name", name, row=idx)

    table.update("seeds", random.randint(1, 30), row=idx)
    table.update("peers", random.randint(0, 5), row=idx)

    errors = 0

    t0 = time.time()
    td = 0
    while True:
        pbar.reset(td / file_info["time"])

        if random.random() < 0.004:
            errors += 1
            random_delay = random.random()
            time.sleep(random_delay)
            t0 += random_delay

        downloaded = int(td / file_info["time"] * file_info["size int"])
        table.update("downloaded", str(downloaded) + " " + file_info["size unit"], row=idx)
        table.update("warnings", errors, row=idx)
        time.sleep(0.01)

        td = time.time() - t0
        if td > file_info["time"]:
            break
    pbar.close()


table.add_column("name", alignment="right", width=25)
table.add_columns("total size", "downloaded", "seeds", "peers", "warnings")
table.add_rows(len(packages), color="blue")

threads = []
executor = ThreadPoolExecutor()

for i, pkg in enumerate(packages):
    pbar = table.pbar(1, position=i, static=True)
    pkg["idx"] = i
    pkg["pbar"] = pbar
    threads.append(executor.submit(fake_download, pkg))

for thread in threads:
    thread.result()
