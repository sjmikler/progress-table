#  Copyright (c) 2022 Szymon Mikler

import logging
import os
import pathlib
import re


def get_header(msg):
    msg_len = len(msg)
    header = [
        "#" * (msg_len + 6),
        "## " + msg + " ##",
        "#" * (msg_len + 6),
    ]
    return "\n".join(header) + "\n"


def scan_for_code_blobs(text):
    # Capture code blocks starting with py or python
    blobs = re.findall(r"```(py|python)\n([\s\S]+?)\n```", text)

    new_blobs = []
    for mode, blob in blobs:
        if "..." in blob:
            continue
        header = get_header(f"Generated ({mode})")
        blob = header + blob

        # For `py` code blocks, we append them to previous existing block
        # But `python` block starts a new scope and finishes the previous block
        # They usually need to include imports
        if mode == "py" and new_blobs:
            new_blobs[-1] = new_blobs[-1] + "\n" + blob
        else:
            new_blobs.append(blob)
    return new_blobs


def test_all_code_blobs():
    all_code_blobs = []

    for root, dirs, files in os.walk("."):
        for file in files:
            path = pathlib.Path(os.path.join(root, file))
            if path.suffix == ".md":
                code_blobs = scan_for_code_blobs(path.open("r").read())
                for blob in code_blobs:
                    all_code_blobs.append(blob)

    logging.warning(f"Detected {len(all_code_blobs)} code examples!")

    for idx, blob in enumerate(all_code_blobs):
        try:
            globals_temp = {}
            exec(blob, globals_temp)
        except Exception as e:
            print(f"Exception during automated documentation testing {idx}/{len(all_code_blobs)}:")
            print(blob)
            raise e
