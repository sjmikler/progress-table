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
    name = "normal"
    pbar_filled = "■"
    pbar_empty = "□"
    embedded_pbar_filled = "_"
    dots = "…"
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


@dataclass
class SymbolsUnicodeBare(Symbols):
    name = "bare"
    pbar_filled = "■"
    pbar_empty = "□"
    embedded_pbar_filled = "_"
    dots = "…"
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


@dataclass
class SymbolsUnicodeRound(Symbols):
    name = "round"
    pbar_filled = "■"
    pbar_empty = "□"
    embedded_pbar_filled = "_"
    dots = "…"
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


@dataclass
class SymbolsUnicodeDouble(Symbols):
    name = "double"
    pbar_filled = "■"
    pbar_empty = "□"
    embedded_pbar_filled = "_"
    dots = "…"
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


@dataclass
class SymbolsUnicodeBold(Symbols):
    name = "bold"
    pbar_filled = "■"
    pbar_empty = "□"
    embedded_pbar_filled = "_"
    dots = "…"
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


@dataclass
class SymbolsAscii(Symbols):
    name = "ascii"
    pbar_filled = "#"
    pbar_empty = "."
    embedded_pbar_filled = "_"
    dots = "_"
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


@dataclass
class SymbolsAsciiBare(Symbols):
    name = "ascii_bare"
    pbar_filled = "#"
    pbar_empty = "."
    embedded_pbar_filled = "_"
    dots = "_"
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
