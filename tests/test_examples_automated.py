#  Copyright (c) 2022-2024 Szymon Mikler

import hashlib
import importlib
import random
import sys
from glob import glob
from io import StringIO

EXPECTED_OUTPUTS = {
    "examples.nn_training": "dadfc581bf8e346df01905f901b8f57b",
    "examples.cumulating": "b5b7bc9b8232545ebfd5ca777bddacb4",
    "examples.fibonacci": "bae5411af4bf8a4326f1bce59ca9aad9",
    "examples.features": "474d4aff94a3070d2300d78d4159e0a6",
}


def set_seed():
    random.seed(42)


def capture_example_stdout(main_fn):
    # To eliminate run to run variation of the example outputs we need to be independent from the execution speed
    # This includes removing the influence of:
    # * refresh rate
    # * throughput display
    override_kwds = dict(
        refresh_rate=1000000000,
        pbar_show_throughput=False,
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
