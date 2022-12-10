from dataclasses import dataclass


@dataclass
class Symbols:
    pbar_filled: str
    pbar_empty: str
    embedded_pbar_filled: str
    dots: str

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


@dataclass
class SymbolsUnicode(Symbols):
    pbar_filled: str = "■"
    pbar_empty: str = "□"
    embedded_pbar_filled: str = "_"
    dots: str = "…"

    horizontal: str = "─"
    vertical: str = "│"
    all: str = "┼"

    up_left: str = "┘"
    up_right: str = "└"
    down_left: str = "┐"
    down_right: str = "┌"

    no_left: str = "├"
    no_right: str = "┤"
    no_up: str = "┬"
    no_down: str = "┴"


@dataclass
class SymbolsUnicodeRound(Symbols):
    pbar_filled: str = "■"
    pbar_empty: str = "□"
    embedded_pbar_filled: str = "_"
    dots: str = "…"

    horizontal: str = "─"
    vertical: str = "│"
    all: str = "┼"

    up_left: str = "╯"
    up_right: str = "╰"
    down_left: str = "╮"
    down_right: str = "╭"

    no_left: str = "├"
    no_right: str = "┤"
    no_up: str = "┬"
    no_down: str = "┴"


@dataclass
class SymbolsUnicodeDouble(Symbols):
    pbar_filled: str = "■"
    pbar_empty: str = "□"
    embedded_pbar_filled: str = "_"
    dots: str = "…"

    horizontal: str = "═"
    vertical: str = "║"
    all: str = "╬"

    up_left: str = "╝"
    up_right: str = "╚"
    down_left: str = "╗"
    down_right: str = "╔"

    no_left: str = "╠"
    no_right: str = "╣"
    no_up: str = "╦"
    no_down: str = "╩"


@dataclass
class SymbolsUnicodeBold(Symbols):
    pbar_filled: str = "■"
    pbar_empty: str = "□"
    embedded_pbar_filled: str = "_"
    dots: str = "…"

    horizontal: str = "━"
    vertical: str = "┃"
    all: str = "╋"

    up_left: str = "┛"
    up_right: str = "┗"
    down_left: str = "┓"
    down_right: str = "┏"

    no_left: str = "┣"
    no_right: str = "┫"
    no_up: str = "┳"
    no_down: str = "┻"


@dataclass
class SymbolsBasic(Symbols):
    pbar_filled: str = "#"
    pbar_empty: str = "."
    embedded_pbar_filled: str = "_"
    dots: str = "_"

    horizontal: str = "-"
    vertical: str = "|"
    all: str = "+"

    up_left: str = "+"
    up_right: str = "+"
    down_left: str = "+"
    down_right: str = "+"

    no_left: str = "+"
    no_right: str = "+"
    no_up: str = "+"
    no_down: str = "+"
