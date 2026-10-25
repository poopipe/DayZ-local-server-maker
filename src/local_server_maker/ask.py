import getpass
from collections.abc import Callable

Prompt = Callable[[str], str]


def ask_text(prompt: Prompt, label: str, default: str) -> str:
    answer = prompt(f"{label} [{default}]: ").strip()
    if answer == "":
        return default
    return answer


def ask_number(prompt: Prompt, label: str, default: int) -> int:
    while True:
        answer = prompt(f"{label} [{default}]: ").strip()
        if answer == "":
            return default
        if answer.isdigit():
            return int(answer)
        print(f"{label} must be a whole number")


def ask_required(prompt: Prompt, label: str) -> str:
    while True:
        answer = prompt(f"{label}: ").strip()
        if answer != "":
            return answer
        print(f"{label} is required")


def ask_secret(prompt: Prompt, label: str) -> str:
    """Ask for a value that should not be shown on screen.

    The real console hides the typing. Any other prompt is called in
    the open so a test can supply the answer.
    """
    if prompt is input:
        while True:
            answer = getpass.getpass(f"{label}: ").strip()
            if answer != "":
                return answer
            print(f"{label} is required")
    while True:
        answer = prompt(f"{label}: ").strip()
        if answer != "":
            return answer
        print(f"{label} is required")


def pick_index(labels: list[str], choice: str) -> tuple[int | None, str]:
    """Return the chosen position, or no position and the reason it was refused.

    A number counts from 1. A name must match one label, ignoring case.
    Two labels with that name require the number.
    """
    text = choice.strip()
    if text.isdigit():
        index = int(text) - 1
        if 0 <= index < len(labels):
            return index, ""
        return None, "That number is not in the list."
    matches = [
        index
        for index, label in enumerate(labels)
        if label.casefold() == text.casefold()
    ]
    if len(matches) == 1:
        return matches[0], ""
    if not matches:
        return None, "That name is not in the list."
    return None, "More than one item has that name. Type its number."


def ask_listed_name(prompt: Prompt, names: list[str], question: str) -> str | None:
    while True:
        choice = prompt(question).strip()
        if choice == "":
            return None
        index, message = pick_index(names, choice)
        if index is None:
            print(message)
            continue
        return names[index]
