#  Copyright (c) 2022-2024 Szymon Mikler

import hashlib
import importlib
import random
import sys
from glob import glob
from io import StringIO


def set_seed():
    random.seed(42)


EXPECTED_TESTS_OUTPUTS = {
    "examples.nn_training": "dadfc581bf8e346df01905f901b8f57b",
    "examples.cumulating": "b5b7bc9b8232545ebfd5ca777bddacb4",
    "examples.fibonacci": "bae5411af4bf8a4326f1bce59ca9aad9",
}


def test_all_examples():
    # To eliminate run to run variation of the example outputs we need to be independent from the execution speed
    # This includes:
    # * refresh rate
    # * throughput indication

    override_kwds = dict(
        refresh_rate=1000000000,
        pbar_show_throughput=False,
    )

    for module in glob("examples/*"):
        module = module.replace(".py", "").replace("/", ".")

        print(f"Running example: {module}")
        main_fn = importlib.import_module(module).main

        # We will replace stdout with custom StringIO and check whether example stdout is as expected
        out_buffer = StringIO()
        sys.stdout = out_buffer
        set_seed()
        main_fn(**override_kwds)
        outputs = out_buffer.getvalue()
        sys.stdout = sys.__stdout__

        md5hash = hashlib.md5(outputs.encode()).hexdigest()
        expected_md5hash = EXPECTED_TESTS_OUTPUTS[module]
        assert md5hash == expected_md5hash, f"Got {md5hash}, expected {expected_md5hash}"
