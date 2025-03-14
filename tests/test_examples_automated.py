#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

import hashlib
import importlib
import sys
from glob import glob
from io import StringIO

EXPECTED_OUTPUTS = {
    "examples.brown2d": "e85fcc33e982cb783059c09c090fca4e",
    "examples.training": "91ca0321e3776d5f2ac45add37e0db27",
    "examples.tictactoe": "b71d814bc517e3aa6d2477dd72e55e8f",
}


def capture_example_stdout(main_fn):
    # To eliminate run to run variation of the example outputs we need to be independent from the execution speed
    # This includes removing the influence of:
    # * refresh rate
    # * throughput display

    # We will replace stdout with custom StringIO and check whether example stdout is as expected
    out_buffer = StringIO()
    override_kwds = dict(
        pbar_show_throughput=False,
        refresh_rate=0,
        file=out_buffer,
    )
    main_fn(random_seed=42, sleep_duration=0, **override_kwds)
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
