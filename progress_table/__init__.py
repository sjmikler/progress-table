#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

"""Progress Table provides an easy and pretty way to track your process.

Supported features:
    - Styling and coloring
    - Modifying existing cells
    - Progress bars integrated into the table
"""

__license__ = "MIT"
__version__ = "3.0.0"
__author__ = "Szymon Mikler"

from progress_table.progress_table import ProgressTable, styles

__all__ = ["ProgressTable", "styles"]
