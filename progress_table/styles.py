#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

"""Module defining styles for progress bars and tables.

Also includes functions to interpret style descriptions and converting them into style objects.
"""

from __future__ import annotations

from progress_table.common import ALL_COLOR_NAME, ColorFormat, maybe_convert_to_colorama


def _contains_word(short: str, long: str) -> bool:
    return any(short == word.strip(" ") for word in long.split(" "))


def _parse_colors_from_description(description: str) -> tuple[str, str, str]:
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


class UnknownStyleError(ValueError):
    """Raised when style description is not recognized."""

    pass


def parse_pbar_style(description: str | PbarStyleBase) -> PbarStyleBase:
    """Parse progress bar style description and return a style object.

    Example:
        >>> parse_pbar_style("square alt clean")

    """
    if isinstance(description, str):
        for obj in available_pbar_styles():
            if _contains_word(obj.name, description):
                description = description.replace(obj.name, "")
                color, color_empty, description = _parse_colors_from_description(description)
                is_alt = "alt" in description
                is_clean = "clean" in description
                description = description.replace("alt", "").replace("clean", "").strip(" ")
                if description.strip(" "):
                    msg = f"Name '{description}' is not recognized as a part of progress bar style"
                    raise UnknownStyleError(msg)

                return obj(alt=is_alt, clean=is_clean, color=color, color_empty=color_empty)

        available_names = ", ".join([obj.name for obj in available_pbar_styles()])
        msg = f"Progress bar style '{description}' not found. Available: {available_names}"
        raise UnknownStyleError(msg)
    return description


def parse_table_style(description: str | TableStyleBase) -> TableStyleBase:
    """Parse table style description and return a style object.

    Example:
        >>> parse_table_style("modern")

    """
    if isinstance(description, str):
        for obj in available_table_styles():
            if _contains_word(obj.name, description):
                description = description.replace(obj.name, "").strip(" ")
                if description:
                    msg = f"Name '{description}' is not recognized as a part of table style"
                    raise UnknownStyleError(msg)

                return obj()
        available_names = ", ".join([obj.name for obj in available_table_styles()])
        msg = f"Table style '{description}' not found. Available: {available_names}"
        raise UnknownStyleError(msg)
    return description


def available_table_styles() -> list[type[TableStyleBase]]:
    """Return a list of available table styles."""
    return [
        obj
        for name, obj in globals().items()
        if isinstance(obj, type) and issubclass(obj, TableStyleBase) and hasattr(obj, "name")
    ]


def available_pbar_styles() -> list[type[PbarStyleBase]]:
    """Return a list of available progress bar styles."""
    return [
        obj
        for name, obj in globals().items()
        if isinstance(obj, type) and issubclass(obj, PbarStyleBase) and hasattr(obj, "name")
    ]


#################
## PBAR STYLES ##
#################


class PbarStyleBase:
    """Base class for progress bar styles."""

    name: str
    filled: str
    empty: str
    head: str | tuple[str, ...]
    color: str = ""
    color_empty: str = ""

    def __init__(
        self,
        *,
        alt: bool = False,
        clean: bool = False,
        color: ColorFormat = None,
        color_empty: ColorFormat = None,
    ) -> None:
        """Initialize progress bar style.

        Args:
            alt: Use the same character for filled and empty parts.
            clean: Use space for empty parts.
            color: Color of the filled part.
            color_empty: Color of the empty part.

        """
        if color is not None:
            self.color = maybe_convert_to_colorama(color)
        if color_empty is not None:
            self.color_empty = maybe_convert_to_colorama(color_empty)
        if alt:
            self.empty = self.filled
        if clean:
            self.empty = " "


class PbarStyleSquare(PbarStyleBase):
    """Progress bar style.

    Example:
        >>> ■■■■■◩□□□□□

    """

    name = "square"
    filled = "■"
    empty = "□"
    head = "◩"


class PbarStyleFull(PbarStyleBase):
    """Progress bar style.

    Example:
        >>> █████▌

    """

    name = "full"
    filled = "█"
    empty = " "
    head = ("▏", "▎", "▍", "▌", "▋", "▊", "▉")


class PbarStyleDots(PbarStyleBase):
    """Progress bar style.

    Example:
        >>> ⣿⣿⣿⣿⣿⣦⣀⣀⣀⣀⣀

    """

    name = "dots"
    filled = "⣿"
    empty = "⣀"
    head = ("⣄", "⣤", "⣦", "⣶", "⣷")


class PbarStyleShort(PbarStyleBase):
    """Progress bar style.

    Example:
        >>> ▬▬▬▬▬▬▭▭▭▭▭

    """

    name = "short"
    filled = "▬"
    empty = "▭"
    head = "▬"


class PbarStyleCircle(PbarStyleBase):
    """Progress bar style.

    Example:
        >>> ●●●●●◉○○○○

    """

    name = "circle"
    filled = "●"
    empty = "○"
    head = "◉"


class PbarStyleAngled(PbarStyleBase):
    """Progress bar style.

    Example:
        >>> ▰▰▰▰▰▰▱▱▱▱

    """

    name = "angled"
    filled = "▰"
    empty = "▱"
    head = "▰"


class PbarStyleRich(PbarStyleBase):
    """Progress bar style.

    Example:
        >>> ━━━━━━━━

    """

    name = "rich"
    filled = "━"
    empty = " "
    head = "━"

    def __init__(self, *args, **kwds) -> None:
        """Similar to the default progress bar from rich."""
        super().__init__(*args, **kwds)
        if not self.color and not self.color_empty:
            self.color = maybe_convert_to_colorama("red")
            self.color_empty = maybe_convert_to_colorama("black")
            self.empty = self.filled


class PbarStyleCdots(PbarStyleBase):
    """Progress bar style.

    Example:
        >>> ꞏꞏꞏꞏꞏꞏꞏꞏ>

    """

    name = "cdots"
    filled = "ꞏ"
    empty = " "
    head = ">"


class PbarStyleDash(PbarStyleBase):
    """Progress bar style.

    Example:
        >>> ----->

    """

    name = "dash"
    filled = "-"
    empty = " "
    head = ">"


class PbarStyleUnder(PbarStyleBase):
    """Progress bar style.

    Example:
        >>> ________

    """

    name = "under"
    filled = "_"
    empty = " "
    head = "_"


class PbarStyleDoubleDash(PbarStyleBase):
    """Progress bar style.

    Example:
        >>> ========>

    """

    name = "doubledash"
    filled = "="
    empty = " "
    head = ">"


class PbarStyleNone(PbarStyleBase):
    """Progress bar style.

    Example:
        >>>

    """

    name = "hidden"
    filled = " "
    empty = " "
    head = " "


##################
## TABLE STYLES ##
##################


class TableStyleBase:
    """Base class for table styles."""

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
    """Table style.

    Example:
        >>> ┌─────────┬─────────┐
        >>> │ H1      │ H2      │
        >>> ├─────────┼─────────┤
        >>> │ V1      │ V2      │
        >>> │ V3      │ V4      │
        >>> └─────────┴─────────┘

    """

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
    """Table style.

    Example:
        >>> ────────── ──────────
        >>> H1         H2
        >>> ────────── ──────────
        >>> V1         V2
        >>> V3         V4
        >>> ────────── ──────────

    """

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
    """Table style.

    Example:
        >>> ╭─────────┬─────────╮
        >>> │ H1      │ H2      │
        >>> ├─────────┼─────────┤
        >>> │ V1      │ V2      │
        >>> │ V3      │ V4      │
        >>> ╰─────────┴─────────╯

    """

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
    """Table style.

    Example:
        >>> ╔═════════╦═════════╗
        >>> ║ H1      ║ H2      ║
        >>> ╠═════════╬═════════╣
        >>> ║ V1      ║ V2      ║
        >>> ║ V3      ║ V4      ║
        >>> ╚═════════╩═════════╝

    """

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
    """Table style.

    Example:
        >>> ┏━━━━━━━━━┳━━━━━━━━━┓
        >>> ┃ H1      ┃ H2      ┃
        >>> ┣━━━━━━━━━╋━━━━━━━━━┫
        >>> ┃ V1      ┃ V2      ┃
        >>> ┃ V3      ┃ V4      ┃
        >>> ┗━━━━━━━━━┻━━━━━━━━━┛

    """

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
    """Table style.

    Example:
        >>> +---------+---------+
        >>> | H1      | H2      |
        >>> +---------+---------+
        >>> | V1      | V2      |
        >>> | V3      | V4      |
        >>> +---------+---------+

    """

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
    """Table style.

    Example:
        >>> --------- ---------
        >>> H1        H2
        >>> --------- ---------
        >>> V1        V2
        >>> V3        V4
        >>> --------- ---------

    """

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
    """Table style.

    Example:
        >>>
        >>> H1        H2
        >>>
        >>> V1        V2
        >>> V3        V4
        >>>

    """

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
