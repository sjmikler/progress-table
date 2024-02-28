#  Copyright (c) 2022 Szymon Mikler

from .compat.progress_table import ProgressTable as ProgressTableV1
from .progress_table import ProgressTable

__all__ = ["ProgressTableV1", "ProgressTable"]
