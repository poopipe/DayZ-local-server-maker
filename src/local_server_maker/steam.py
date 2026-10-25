import re

NAME = re.compile(r'^\s*name\s*=\s*"([^"]*)"\s*;', re.MULTILINE)


def get_mod_name(meta_text: str) -> str:
    match = NAME.search(meta_text)
    if match is None or match.group(1) == "":
        raise ValueError("meta.cpp has no name")
    name = match.group(1)
    if any(char in name for char in '\\/:"*?<>|;'):
        raise ValueError(f"mod name cannot be used as a folder name: {name}")
    return name
