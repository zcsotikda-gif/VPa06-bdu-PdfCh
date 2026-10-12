import pytest

from pdf_checker.menu import choose, format_menu


def test_format_menu_numbers_from_one():
    text = format_menu("Файлы", ["a.csv", "b.json"])
    assert "Файлы" in text
    assert " 1. a.csv" in text
    assert " 2. b.json" in text


def test_choose_returns_zero_based_index():
    answers = iter(["2"])
    assert choose("T", ["a", "b"], input_fn=lambda _: next(answers), print_fn=lambda *_: None) == 1


def test_choose_reprompts_on_bad_input():
    answers = iter(["", "x", "0", "3", " 1 "])
    printed = []
    index = choose("T", ["a", "b"], input_fn=lambda _: next(answers), print_fn=printed.append)
    assert index == 0
    assert sum("от 1 до 2" in str(line) for line in printed) == 4


def test_choose_empty_options_raises():
    with pytest.raises(ValueError):
        choose("T", [], input_fn=lambda _: "1", print_fn=lambda *_: None)
