#  Copyright (c) 2022-2024 Szymon Mikler


def figure_pbar_style(pbar_style_name):
    if isinstance(pbar_style_name, str):
        pbar_style_name = pbar_style_name.lower()
        for obj in available_pbar_styles():
            if obj.name == pbar_style_name:
                return obj
        available_names = ", ".join([obj.name for obj in available_pbar_styles()])
        raise ValueError(f"Progress bar style '{pbar_style_name}' not found. Available: {available_names}")
    else:
        return pbar_style_name


def figure_table_style(table_style_name):
    if isinstance(table_style_name, str):
        table_style_name = table_style_name.lower()
        for obj in available_table_styles():
            if obj.name == table_style_name:
                return obj
        available_names = ", ".join([obj.name for obj in available_table_styles()])
        raise ValueError(f"Table style '{table_style_name}' not found. Available: {available_names}")
    else:
        return table_style_name


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
    head: str


class PbarStyleNormal(PbarStyleBase):
    name = "normal"
    filled = "■"
    empty = "□"
    head = "◩"


class PbarStyleShort(PbarStyleBase):
    name = "short"
    filled = "▬"
    empty = "▭"
    head = "▬"


class PbarStyleNormalClean(PbarStyleBase):
    name = "normal clean"
    filled = "■"
    empty = " "
    head = "◩"


class PbarStyleCircle(PbarStyleBase):
    name = "circle"
    filled = "●"
    empty = "○"
    head = "◉"


class PbarStyleCircleClean(PbarStyleBase):
    name = "circle clean"
    filled = "●"
    empty = " "
    head = "◉"


class PbarStyleAngled(PbarStyleBase):
    name = "angled"
    filled = "▰"
    empty = "▱"
    head = "▰"


class PbarStyleAngledClean(PbarStyleBase):
    name = "angled clean"
    filled = "▰"
    empty = " "
    head = "▰"


class PbarStyleEmbed(PbarStyleBase):
    name = "embed"
    filled = "ꞏ"
    empty = " "
    head = ">"


class PbarStyleRich(PbarStyleBase):
    name = "rich"
    filled = "━"
    empty = " "
    head = "━"


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


class TableStyleNormal(TableStyleBase):
    name = "normal"
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
    name = "ascii bare"
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
