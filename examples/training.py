#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

import random
import time

try:
    import numpy as np
except ImportError as ex:
    raise ImportError("Numpy is required to run the example!") from ex

try:
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split
    from sklearn.utils import shuffle
except ImportError as ex:
    raise ImportError("Scikit-learn is required to run the example!") from ex

from progress_table import ProgressTable

# Training parameters
SGD_LR = 0.01
NUM_EPOCHS = 15
SLEEP_DURATION = 0.04


def softmax(x):
    exp = np.exp(x)
    return exp / np.sum(exp, axis=1, keepdims=True)


def log_softmax(x):
    bot = np.sum(np.exp(x), axis=1, keepdims=True)
    return x - np.log(bot)


def cross_entropy_loss(targets, logits):
    # Simulate heavy computation
    time.sleep(SLEEP_DURATION)

    assert len(targets) == len(logits)
    num_elements = len(targets)

    logits = log_softmax(logits)
    return -logits[np.arange(num_elements), targets]


def cross_entropy_loss_grads(targets, logits):
    one_hot_targets = np.zeros_like(logits)
    one_hot_targets[np.arange(len(targets)), targets] = 1
    return one_hot_targets - softmax(logits)


def model_grads(targets, logits, inputs):
    cross_entropy_grads = cross_entropy_loss_grads(targets, logits)
    return inputs.T @ cross_entropy_grads


def main(random_seed=None, sleep_duration=SLEEP_DURATION, **overrides):
    if random_seed is None:
        random_seed = random.randint(0, 100)
    global SLEEP_DURATION
    SLEEP_DURATION = sleep_duration

    random.seed(random_seed)
    np.random.seed(random_seed)

    table = ProgressTable(
        pbar_embedded=False,  # Do not use embedded pbar
        pbar_style="angled alt red blue",
        **overrides,
    )
    print("Training a simple linear model on the Iris dataset.")

    # Loading dataset
    X, Y = load_iris(return_X_y=True)
    X_train, X_valid, Y_train, Y_valid = train_test_split(X, Y)
    weights = np.random.rand(4, 3)

    for epoch in table(NUM_EPOCHS, show_throughput=False, show_eta=True):
        table["epoch"] = epoch
        # Shuffling training dataset each epoch
        X_train, Y_train = shuffle(X_train, Y_train)  # type: ignore

        NUM_BATCHES = 16
        X_batches = np.array_split(X_train, NUM_BATCHES)
        Y_batches = np.array_split(Y_train, NUM_BATCHES)

        for batch in table(zip(X_batches, Y_batches), total=NUM_BATCHES, description="train epoch"):
            x, y = batch
            logits = x @ weights

            # Computing and applying gradient update
            weights_updates = model_grads(y, logits, x)
            weights = weights + SGD_LR * weights_updates

            # Computing loss function for the logging
            accuracy = np.mean(np.argmax(logits, axis=1) == y)
            loss_value = np.mean(cross_entropy_loss(y, logits))

            # We're using .update instead of __setitem__ so that we can specify column details
            table.update("train loss", loss_value, aggregate="mean", color="blue")
            table.update("train accuracy", accuracy, aggregate="mean", color="blue bold")

        run_validation = epoch % 5 == 4 or epoch == NUM_EPOCHS - 1
        if run_validation:
            NUM_BATCHES = 32
            X_batches = np.array_split(X_valid, NUM_BATCHES)
            Y_batches = np.array_split(Y_valid, NUM_BATCHES)

            for batch in table(zip(X_batches, Y_batches), total=NUM_BATCHES, description="valid epoch"):
                x, y = batch
                logits = x @ weights
                accuracy = np.mean(np.argmax(logits, axis=1) == y)
                loss_value = np.mean(cross_entropy_loss(y, logits))

                # Use aggregation weight equal to batch size to get real mean over the validation dataset
                batch_size = x.shape[0]
                table.update(
                    "valid loss",
                    loss_value,
                    weight=batch_size,
                    aggregate="mean",
                    color="red",
                )
                table.update(
                    "valid accuracy",
                    accuracy,
                    weight=batch_size,
                    aggregate="mean",
                    color="red bold",
                )
        table.next_row(split=run_validation)
    table.close()


if __name__ == "__main__":
    main()
