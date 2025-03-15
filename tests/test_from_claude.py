#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

import colorama
import pytest

from progress_table.styles import (
    PbarStyleBase,
    PbarStyleRich,
    PbarStyleSquare,
    TableStyleBase,
    TableStyleModern,
    UnknownStyleError,
    _contains_word,
    _parse_colors_from_description,
    available_pbar_styles,
    available_table_styles,
    parse_pbar_style,
    parse_table_style,
)


def test_word_contained_in_string():
    assert _contains_word("foo", "foo bar baz") is True
    assert _contains_word("bar", "foo bar baz") is True


def test_word_not_contained_in_string():
    assert _contains_word("qux", "foo bar baz") is False
    assert _contains_word("fo", "foo bar baz") is False


def test_words_with_spaces_properly_detected():
    assert _contains_word("foo", " foo  bar  baz ") is True
    assert _contains_word(" foo ", "foo bar baz") is False


def test_primary_color_extracted_from_description():
    color, empty_color, rest = _parse_colors_from_description("red square")
    assert color == "RED"
    assert empty_color == ""
    assert "square" in rest


def test_both_colors_extracted_from_description():
    color, empty_color, rest = _parse_colors_from_description("red green square")
    assert color == "RED"
    assert empty_color == "GREEN"
    assert "square" in rest


def test_no_colors_returns_empty_strings():
    color, empty_color, rest = _parse_colors_from_description("square style")
    assert color == ""
    assert empty_color == ""
    assert rest == "square style"


def test_pbar_style_created_from_valid_name():
    style = parse_pbar_style("square")
    assert isinstance(style, PbarStyleSquare)
    assert style.name == "square"


def test_pbar_style_alt_option_copies_filled_to_empty():
    style = parse_pbar_style("square alt")
    assert style.empty == style.filled


def test_pbar_style_clean_option_sets_empty_to_space():
    style = parse_pbar_style("square clean")
    assert style.empty == " "


def test_pbar_style_with_colors_sets_color_attributes():
    style = parse_pbar_style("red green square")
    assert style.color == colorama.Fore.RED
    assert style.color_empty == colorama.Fore.GREEN


def test_pbar_style_with_invalid_name_raises_error():
    with pytest.raises(UnknownStyleError):
        parse_pbar_style("invalid_style")


def test_pbar_style_with_unknown_word_raises_error():
    with pytest.raises(UnknownStyleError):
        parse_pbar_style("square unknown_word")


def test_pbar_style_returns_object_if_passed_directly():
    style = PbarStyleSquare()
    result = parse_pbar_style(style)
    assert result is style


def test_table_style_created_from_valid_name():
    style = parse_table_style("modern")
    assert isinstance(style, TableStyleModern)
    assert style.name == "modern"


def test_table_style_with_invalid_name_raises_error():
    with pytest.raises(UnknownStyleError):
        parse_table_style("invalid_style")


def test_table_style_returns_object_if_passed_directly():
    style = TableStyleModern()
    result = parse_table_style(style)
    assert result is style


def test_available_table_styles_returns_list_of_style_classes():
    styles_list = available_table_styles()
    assert len(styles_list) > 0
    assert all(issubclass(style, TableStyleBase) for style in styles_list)


def test_available_pbar_styles_returns_list_of_style_classes():
    styles_list = available_pbar_styles()
    assert len(styles_list) > 0
    assert all(issubclass(style, PbarStyleBase) for style in styles_list)


def test_pbar_style_rich_sets_default_colors():
    style = PbarStyleRich()
    assert style.color != ""
    assert style.color_empty != ""
    assert style.empty == style.filled
