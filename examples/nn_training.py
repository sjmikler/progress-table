#  Copyright (c) 2022-2024 Szymon Mikler

import random
import time

from progress_table import ProgressTable


def main(**overrides):
    default = dict(
        pbar_show_progress=True,
        pbar_show_throughput=False,
        interactive=2,
    )
    default = {**default, **overrides}
    table = ProgressTable(
        **default,
    )

    num_epochs = 10
    num_train_samples = 200
    num_valid_samples = 20

    table.add_column("epoch")

    for epoch in table(num_epochs):
        time.sleep(1)

        for step in table(num_train_samples, description="train epoch"):
            table["epoch"] = epoch

            loss_value = random.random()
            accuracy = random.random() ** 0.5
            time.sleep(0.01 + random.random() / 100)

            # We're using .update instead of __setitem__ so that we can specify column details
            table.update("train loss", loss_value, aggregate="mean", color="blue")
            table.update("train accuracy", accuracy, aggregate="mean", color="blue bold")

        run_validation = epoch % 5 == 0 or epoch == num_epochs - 1
        if run_validation:
            for step in table(num_valid_samples, description="valid epoch"):
                time.sleep(0.1)

            loss_value = random.random()
            accuracy = random.random() ** 0.5
            table["valid loss"] = loss_value
            table["valid accuracy"] = accuracy
        table.next_row(split=run_validation)

    table.close()


if __name__ == "__main__":
    main()
