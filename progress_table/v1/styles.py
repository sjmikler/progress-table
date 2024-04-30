#  Copyright (c) 2022-2024 Szymon Mikler

from __future__ import annotations

from typing import Tuple, Union

from progress_table.v1.common import ALL_COLOR_NAME, maybe_convert_to_colorama


def contains_word(short, long):
    return any([short == word.strip(" ") for word in long.split(" ")])


def parse_colors_from_description(description):
    color = ""
    color_empty = ""
    for word in description.split():
        for color_name in ALL_COLOR_NAME:
            if color_name.lower() == word.lower():
                if not color:
                    color = color_name
                else:
                    color_empty = color_name
                description = description.replace(word, "")
    return color, color_empty, description


def parse_pbar_style(description):
    if isinstance(description, str):
        for obj in available_pbar_styles():
            if contains_word(obj.name, description):
                description = description.replace(obj.name, "")
                color, color_empty, description = parse_colors_from_description(description)
                is_alt = "alt" in description
                is_clean = "clean" in description
                description = description.replace("alt", "").replace("clean", "").strip(" ")
                if description.strip(" "):
                    raise ValueError(f"Name '{description}' is not recognized as a part of progress bar style")

                return obj(alt=is_alt, clean=is_clean, color=color, color_empty=color_empty)

        available_names = ", ".join([obj.name for obj in available_pbar_styles()])
        raise ValueError(f"Progress bar style '{description}' not found. Available: {available_names}")
    else:
        return description


def parse_table_style(description):
    if isinstance(description, str):
        for obj in available_table_styles():
            if contains_word(obj.name, description):
                description = description.replace(obj.name, "").strip(" ")
                if description:
                    raise ValueError(f"Name '{description}' is not recognized as a part of table style")

                return obj()
        available_names = ", ".join([obj.name for obj in available_table_styles()])
        raise ValueError(f"Table style '{description}' not found. Available: {available_names}")
    else:
        return description


def available_table_styles():
    return [obj for name, obj in globals().items() if isinstance(obj, type) and issubclass(obj, TableStyleBase) and hasattr(obj, "name")]


def available_pbar_styles():
    return [obj for name, obj in globals().items() if isinstance(obj, type) and issubclass(obj, PbarStyleBase) and hasattr(obj, "name")]


#################
## PBAR STYLES ##
#################


class PbarStyleBase:
    name: str
    filled: str
    empty: str
    head: Union[str, Tuple[str, ...]]
    color: str = ""
    color_empty: str = ""

    def __init__(self, alt=False, clean=False, color=None, color_empty=None):
        if color is not None:
            self.color = maybe_convert_to_colorama(color)
        if color_empty is not None:
            self.color_empty = maybe_convert_to_colorama(color_empty)
        if alt:
            self.empty = self.filled
        if clean:
            self.empty = " "


class PbarStyleSquare(PbarStyleBase):
    name = "square"
    filled = "■"
    empty = "□"
    head = "◩"


class PbarStyleFull(PbarStyleBase):
    name = "full"
    filled = "█"
    empty = " "
    head = ("▏", "▎", "▍", "▌", "▋", "▊", "▉")


class PbarStyleDots(PbarStyleBase):
    name = "dots"
    filled = "⣿"
    empty = "⣀"
    head = ("⣄", "⣤", "⣦", "⣶", "⣷")


class PbarStyleShort(PbarStyleBase):
    name = "short"
    filled = "▬"
    empty = "▭"
    head = "▬"


class PbarStyleCircle(PbarStyleBase):
    name = "circle"
    filled = "●"
    empty = "○"
    head = "◉"


class PbarStyleAngled(PbarStyleBase):
    name = "angled"
    filled = "▰"
    empty = "▱"
    head = "▰"


class PbarStyleRich(PbarStyleBase):
    name = "rich"
    filled = "━"
    empty = " "
    head = "━"

    def __init__(self, *args, **kwds):
        """Similar to the default progress bar from rich"""
        super().__init__(*args, **kwds)
        if not self.color and not self.color_empty:
            self.color = maybe_convert_to_colorama("red")
            self.color_empty = maybe_convert_to_colorama("black")
            self.empty = self.filled


class PbarStyleCdots(PbarStyleBase):
    name = "cdots"
    filled = "ꞏ"
    empty = " "
    head = ">"


class PbarStyleDash(PbarStyleBase):
    name = "dash"
    filled = "-"
    empty = " "
    head = ">"


class PbarStyleUnder(PbarStyleBase):
    name = "under"
    filled = "_"
    empty = " "
    head = "_"


class PbarStyleDoubleDash(PbarStyleBase):
    name = "doubledash"
    filled = "="
    empty = " "
    head = ">"


class PbarStyleNone(PbarStyleBase):
    name = "hidden"
    filled = " "
    empty = " "
    head = " "


##################
## TABLE STYLES ##
##################


class TableStyleBase:
    name: str
    cell_overflow: str
    horizontal: str
    vertical: str
    all: str
    up_left: str
    up_right: str
    down_left: str
    down_right: str
    no_left: str
    no_right: str
    no_up: str
    no_down: str


class TableStyleModern(TableStyleBase):
    name = "modern"
    cell_overflow = "…"
    horizontal = "─"
    vertical = "│"
    all = "┼"
    up_left = "┘"
    up_right = "└"
    down_left = "┐"
    down_right = "┌"
    no_left = "├"
    no_right = "┤"
    no_up = "┬"
    no_down = "┴"


class TableStyleUnicodeBare(TableStyleBase):
    name = "bare"
    cell_overflow = "…"
    horizontal = "─"
    vertical = " "
    all = "─"
    up_left = "─"
    up_right = "─"
    down_left = "─"
    down_right = "─"
    no_left = "─"
    no_right = "─"
    no_up = "─"
    no_down = "─"


class TableStyleUnicodeRound(TableStyleBase):
    name = "round"
    cell_overflow = "…"
    horizontal = "─"
    vertical = "│"
    all = "┼"
    up_left = "╯"
    up_right = "╰"
    down_left = "╮"
    down_right = "╭"
    no_left = "├"
    no_right = "┤"
    no_up = "┬"
    no_down = "┴"


class TableStyleUnicodeDouble(TableStyleBase):
    name = "double"
    cell_overflow = "…"
    horizontal = "═"
    vertical = "║"
    all = "╬"
    up_left = "╝"
    up_right = "╚"
    down_left = "╗"
    down_right = "╔"
    no_left = "╠"
    no_right = "╣"
    no_up = "╦"
    no_down = "╩"


class TableStyleUnicodeBold(TableStyleBase):
    name = "bold"
    cell_overflow = "…"
    horizontal = "━"
    vertical = "┃"
    all = "╋"
    up_left = "┛"
    up_right = "┗"
    down_left = "┓"
    down_right = "┏"
    no_left = "┣"
    no_right = "┫"
    no_up = "┳"
    no_down = "┻"


class TableStyleAscii(TableStyleBase):
    name = "ascii"
    cell_overflow = "_"
    horizontal = "-"
    vertical = "|"
    all = "+"
    up_left = "+"
    up_right = "+"
    down_left = "+"
    down_right = "+"
    no_left = "+"
    no_right = "+"
    no_up = "+"
    no_down = "+"


class TableStyleAsciiBare(TableStyleBase):
    name = "asciib"
    cell_overflow = "_"
    horizontal = "-"
    vertical = " "
    all = "-"
    up_left = "-"
    up_right = "-"
    down_left = "-"
    down_right = "-"
    no_left = "-"
    no_right = "-"
    no_up = "-"
    no_down = "-"


class TableStyleHidden(TableStyleBase):
    name = "hidden"
    cell_overflow = " "
    horizontal = " "
    vertical = " "
    all = " "
    up_left = " "
    up_right = " "
    down_left = " "
    down_right = " "
    no_left = " "
    no_right = " "
    no_up = " "
    no_down = " "
