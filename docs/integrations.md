# Integrations

Progress Table is not tied up to any specific deep learning framework.
Because of it, it's lightweight and minimal. You can still easily integrate it with your code and your favourite framework. Below you will find examples of how to do this.

# PyTorch

This is an example of a simple custom training loop in PyTorch. We present two versions: without and with Progress Bar.

### Without Progress Table

Manual logging is often done in haste. It can look like this:

```python
...

for epoch in range(n_epochs):
    print(f'Epoch {epoch}')
    cumulated_loss = 0
    cumulated_accuracy = 0

    for batch_idx, (x, y) in enumerate(train_loader):
        loss, predictions = training_step(x, y)
        accuracy = torch.mean((predictions == y).float()).item()

        cumulated_loss += loss.item()
        cumulated_accuracy += accuracy

        if (batch_idx) % 100 == 0:
            print('Epoch [{}/{}], Step [{}/{}], Loss: {:.4f}, Accuracy: {:.4f}'.format(
                epoch,
                n_epochs,
                batch_idx,
                len(train_loader),
                cumulated_loss / (batch_idx + 1),
                cumulated_accuracy / (batch_idx + 1),
            ))

print('Epoch [{}/{}], Step [FINISHED], Loss: {:.4f}, Accuracy: {:.4f}'.format(
    epoch,
    n_epochs,
    cumulated_loss / len(train_loader),
    cumulated_accuracy / len(train_loader),
))
```

### With Progress Table

When using Progress Table, you get detailed and clean logs. Moreover, your code is shorter, simpler and you get more functionality out of it.

```python
...

table = ProgressTable("Epoch", "Step")
table.add_columns(["Loss", "Accuracy"], aggregate="mean")

for epoch in range(n_epochs):
    table["Epoch"] = f"{epoch}/{n_epochs}"

    for x, y in table(train_loader):
        loss, predictions = training_step(x, y)
        accuracy = torch.mean((predictions == y).float()).item()

        table["Loss"] = loss
        table["Accuracy"] = accuracy
    table.next_row()

table.close()
```

# Keras

In case of PyTorch or TensorFlow, we often use custom training loops 
where we can integrate Progress Table as shown above.
What about Keras, where the progress bar is built-in the `model.fit` method?
You can create a callback that will replace the progress bar built-in Keras
with a progress table. Callback should inherit from `ProgbarLogger`.

Here's an example:

```python
...

table = ProgressTable()
table.add_columns(["loss", "accuracy", "val_loss", "val_accuracy"], aggregate="mean")


class TableCallback(tf.keras.callbacks.ProgbarLogger):
    def __init__(self, table):
        super().__init__()
        self.table = table

    def on_epoch_begin(self, epoch, logs=None):
        pass

    def on_epoch_end(self, epoch, logs=None):
        self.table.update_from_dict(logs)
        self.table.next_row()

    def on_train_end(self, logs=None):
        self.table.close()

    def on_train_batch_end(self, batch, logs=None):
        self.table.update_from_dict(logs)


model.fit(
    x_train,
    y_train,
    validation_data=(x_train, y_train),
    callbacks=[TableCallback(table)],
    epochs=10,
)
```
