"""Нумерованное меню в консоли. Ввод и вывод передаются параметрами ради тестов."""

from collections.abc import Callable, Sequence


def format_menu(title: str, options: Sequence[str]) -> str:
    width = len(str(len(options)))
    lines = [title, "-" * len(title)]
    lines += [f" {n:>{width}}. {option}" for n, option in enumerate(options, start=1)]
    return "\n".join(lines)


def choose(
    title: str,
    options: Sequence[str],
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> int:
    """Показывает меню и возвращает индекс выбранного варианта (с нуля)."""
    if not options:
        raise ValueError(f"нечего выбирать: {title}")
    print_fn("")
    print_fn(format_menu(title, options))
    return ask_index(len(options), "Номер", input_fn, print_fn)


def ask_index(
    count: int,
    label: str,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> int:
    """Спрашивает номер от 1 до count, пока не введут верный; возвращает индекс с нуля."""
    while True:
        answer = input_fn(f"{label} (1–{count}): ").strip()
        if answer.isdigit() and 1 <= int(answer) <= count:
            return int(answer) - 1
        print_fn(f"Введите число от 1 до {count}.")
