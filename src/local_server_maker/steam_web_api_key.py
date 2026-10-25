from pathlib import Path

from local_server_maker.consts import HEX_DIGITS, KEY_FILE_NAME


def is_steam_web_api_key(value: str) -> bool:
    return len(value) == 32 and all(char in HEX_DIGITS for char in value)


def get_saved_steam_web_api_key(directory: Path) -> str | None:
    path = directory / KEY_FILE_NAME
    if not path.is_file():
        return None
    key = path.read_text(encoding="utf-8").strip()
    if not is_steam_web_api_key(key):
        raise ValueError(f"{path} does not contain a Steam Web API key")
    return key


def save_steam_web_api_key(directory: Path, key: str) -> None:
    if not is_steam_web_api_key(key):
        raise ValueError("Steam Web API key must be 32 hex characters")
    path = directory / KEY_FILE_NAME
    path.write_text(key + "\n", encoding="utf-8")
