from pathlib import Path

from local_server_maker.consts import STEAM_ID_FILE_NAME


def is_steam64(value: str) -> bool:
    return len(value) == 17 and value.isdigit()


def get_saved_steam_ids(directory: Path) -> dict[str, str]:
    path = directory / STEAM_ID_FILE_NAME
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if text == "" or is_steam64(text):
        # A bare ID is from before usernames were stored. It matches no account.
        return {}
    saved: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 2 or not is_steam64(parts[1]):
            raise ValueError(f"{path} does not contain username and Steam ID pairs")
        saved[parts[0]] = parts[1]
    return saved


def get_saved_steam_id(directory: Path, username: str) -> str | None:
    return get_saved_steam_ids(directory).get(username)


def save_steam_id(directory: Path, username: str, steam_id: str) -> None:
    if username == "" or any(char.isspace() for char in username):
        raise ValueError("steamUsername must not contain whitespace")
    if not is_steam64(steam_id):
        raise ValueError("steamId must be 17 digits")
    saved = get_saved_steam_ids(directory)
    saved[username] = steam_id
    path = directory / STEAM_ID_FILE_NAME
    lines = [f"{name} {value}\n" for name, value in saved.items()]
    path.write_text("".join(lines), encoding="utf-8")
