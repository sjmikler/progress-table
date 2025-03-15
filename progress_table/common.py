#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

"""Common utilities for progress_table."""

from typing import Union

from colorama import Back, Fore, Style

ALL_COLOR_NAME = [x for x in dir(Fore) if not x.startswith("__")]
ALL_STYLE_NAME = [x for x in dir(Style) if not x.startswith("__")]
ALL_COLOR_STYLE_NAME = ALL_COLOR_NAME + ALL_STYLE_NAME
ALL_COLOR = [getattr(Fore, x) for x in ALL_COLOR_NAME] + [getattr(Back, x) for x in ALL_COLOR_NAME]
ALL_STYLE = [getattr(Style, x) for x in ALL_STYLE_NAME]
ALL_COLOR_STYLE = ALL_COLOR + ALL_STYLE

COLORAMA_TRANSLATE = {
    "bold": "bright",
}

NoneType = type(None)
ColorFormat = Union[str, tuple, list, NoneType]
ColorFormatTuple = (str, tuple, list, NoneType)
CURSOR_UP = "\033[A"


def maybe_convert_to_colorama_str(color: str) -> str:
    """Convert color from string to colorama string."""
    color = COLORAMA_TRANSLATE.get(color.lower(), color)

    if isinstance(color, str):
        if hasattr(Fore, color.upper()):
            return getattr(Fore, color.upper())
        if hasattr(Style, color.upper()):
            return getattr(Style, color.upper())

    assert color in ALL_COLOR_STYLE, f"Color {color!r} incorrect! Available: {' '.join(ALL_COLOR_STYLE_NAME)}"
    return color


def maybe_convert_to_colorama(color: ColorFormat) -> str:
    """Fix unintuitive colorama names.

    Translation layer from user-passed to colorama-compatible names.
    """
    if color is None or color == "":
        return ""
    if isinstance(color, str):
        color = color.split(" ")
    results = [maybe_convert_to_colorama_str(x) for x in color]
    return "".join(results)
