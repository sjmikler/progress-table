#  Copyright (c) 2022-2024 Szymon Mikler

__version__ = "1.3.1"

from progress_table.v0.progress_table import ProgressTableV0
from progress_table.v1.progress_table import ProgressTableV1

ProgressTable = ProgressTableV1

__all__ = ["ProgressTable", "ProgressTableV0", "ProgressTableV1"]
