#  Copyright (c) 2022-2024 Szymon Mikler

import hashlib
import importlib
import random
import sys
from glob import glob
from io import StringIO

EXPECTED_OUTPUTS = {
    "examples.training": "bad7ddd345b24694eba2a46da53231fd",
    "examples.tictactoe": "e60d06f1ab9caec30ce7715307e0804c",
    "examples.brown2d": "656b8bc42cef99bf2b390d1a1d550e8a",
}


def set_seed():
    random.seed(42)


def capture_example_stdout(main_fn):
    # To eliminate run to run variation of the example outputs we need to be independent from the execution speed
    # This includes removing the influence of:
    # * refresh rate
    # * throughput display
    override_kwds = dict(
        pbar_show_throughput=False,
        interactive=0,
    )

    # We will replace stdout with custom StringIO and check whether example stdout is as expected
    out_buffer = StringIO()
    sys.stdout = out_buffer
    set_seed()
    main_fn(**override_kwds)
    sys.stdout = sys.__stdout__
    return out_buffer.getvalue()


def test_all_examples():
    # Testing whether examples run exactly as intended

    outputs = {}
    for module in glob("examples/*"):
        module = module.replace(".py", "").replace("/", ".")

        if module not in EXPECTED_OUTPUTS:
            print(f"Skipping example: {module}")
            continue
        print(f"Running example: {module}")

        main_fn = importlib.import_module(module).main
        out_str = capture_example_stdout(main_fn)

        md5hash = hashlib.md5(out_str.encode()).hexdigest()
        outputs[module] = md5hash

    err_msg = []
    for key in EXPECTED_OUTPUTS:
        output = outputs.get(key, None)
        expected = EXPECTED_OUTPUTS[key]
        if output != expected:
            err_msg.append(f" {output} instead of {expected} in {key}")
    err_msg = "\n".join(err_msg)

    if err_msg:
        assert False, f"Errors in example outputs\n{err_msg}"
