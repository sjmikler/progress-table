class StyleNormal:
    name = "normal"
    pbar_filled = "■"
    pbar_empty = "□"
    embedded_pbar_filled = "ꞏ"
    embedded_pbar_head = ">"
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


class StyleUnicodeBare(StyleNormal):
    name = "bare"
    pbar_filled = "■"
    pbar_empty = "□"
    embedded_pbar_filled = "ꞏ"
    embedded_pbar_head = ">"
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


class StyleUnicodeRound(StyleNormal):
    name = "round"
    pbar_filled = "■"
    pbar_empty = "□"
    embedded_pbar_filled = "ꞏ"
    embedded_pbar_head = ">"
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


class StyleUnicodeDouble(StyleNormal):
    name = "double"
    pbar_filled = "■"
    pbar_empty = "□"
    embedded_pbar_filled = "ꞏ"
    embedded_pbar_head = ">"
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


class StyleUnicodeBold(StyleNormal):
    name = "bold"
    pbar_filled = "■"
    pbar_empty = "□"
    embedded_pbar_filled = "ꞏ"
    embedded_pbar_head = ">"
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


class StyleAscii(StyleNormal):
    name = "ascii"
    pbar_filled = "#"
    pbar_empty = "."
    embedded_pbar_filled = "-"
    embedded_pbar_head = ">"
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


class StyleAsciiBare(StyleNormal):
    name = "ascii_bare"
    pbar_filled = "#"
    pbar_empty = "."
    embedded_pbar_filled = "-"
    embedded_pbar_head = ">"
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


PREDEFINED_STYLES = {
    style.name: style
    for style in [
        StyleNormal,
        StyleUnicodeBare,
        StyleUnicodeRound,
        StyleUnicodeDouble,
        StyleUnicodeBold,
        StyleAscii,
        StyleAsciiBare,
    ]
}
