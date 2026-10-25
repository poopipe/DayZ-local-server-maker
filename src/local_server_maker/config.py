import json
from pathlib import Path
from typing import TypedDict, cast

from local_server_maker.steam_id import is_steam64


class ModEntry(TypedDict):
    id: str
    title: str
    path: str


class ServerConfig(TypedDict):
    steamCmdDir: str
    steamUsername: str
    steamId: str
    dayzClient: str
    dayzAppId: str
    serverAppId: str
    destination: str
    hostname: str
    port: int
    cpuCount: int
    profileDir: str
    mission: str
    password: str
    passwordAdmin: str
    maxPlayers: int
    instanceId: int
    shardId: str
    restartSeconds: int
    launch: bool
    overwriteConfigs: bool
    mods: list[ModEntry]
    serverMods: list[ModEntry]
    launchArgs: list[str]


def write_config(path: Path, config: ServerConfig) -> None:
    previous = path.read_text(encoding="utf-8") if path.is_file() else None
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    try:
        get_config(path)
    except ValueError:
        if previous is None:
            path.unlink()
        else:
            path.write_text(previous, encoding="utf-8")
        raise


STRING_KEYS = (
    "steamCmdDir",
    "steamUsername",
    "dayzAppId",
    "serverAppId",
    "destination",
    "hostname",
    "profileDir",
    "mission",
    "password",
    "passwordAdmin",
    "shardId",
)

INT_KEYS = ("port", "cpuCount", "maxPlayers", "instanceId", "restartSeconds")

BOOL_KEYS = ("launch", "overwriteConfigs")

LIST_KEYS = ("mods", "serverMods", "launchArgs")


def get_config(path: Path) -> ServerConfig:
    raw = get_json_object(path)
    missing = [
        key
        for key in (*STRING_KEYS, *INT_KEYS, *BOOL_KEYS, *LIST_KEYS)
        if key not in raw
    ]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"config is missing {names}")
    config: ServerConfig = {
        "steamCmdDir": get_string(raw, "steamCmdDir"),
        "steamUsername": get_string(raw, "steamUsername"),
        "steamId": get_string(raw, "steamId") if "steamId" in raw else "",
        "dayzClient": get_string(raw, "dayzClient") if "dayzClient" in raw else "",
        "dayzAppId": get_string(raw, "dayzAppId"),
        "serverAppId": get_string(raw, "serverAppId"),
        "destination": get_string(raw, "destination"),
        "hostname": get_string(raw, "hostname"),
        "port": get_int(raw, "port"),
        "cpuCount": get_int(raw, "cpuCount"),
        "profileDir": get_string(raw, "profileDir"),
        "mission": get_string(raw, "mission"),
        "password": get_string(raw, "password"),
        "passwordAdmin": get_string(raw, "passwordAdmin"),
        "maxPlayers": get_int(raw, "maxPlayers"),
        "instanceId": get_int(raw, "instanceId"),
        "shardId": get_string(raw, "shardId"),
        "restartSeconds": get_int(raw, "restartSeconds"),
        "launch": get_bool(raw, "launch"),
        "overwriteConfigs": get_bool(raw, "overwriteConfigs"),
        "mods": get_mod_list(raw, "mods"),
        "serverMods": get_mod_list(raw, "serverMods"),
        "launchArgs": get_string_list(raw, "launchArgs"),
    }
    check_config_values(config)
    return config


def generate_steamcmd_dir(config: ServerConfig, config_path: Path) -> Path:
    raw = config["steamCmdDir"]
    if raw == "":
        return (config_path.parent / ".steamcmd").resolve()
    path = Path(raw)
    if not path.is_absolute():
        path = config_path.parent / path
    return path.resolve()


def generate_workshop_ids(
    mods: list[ModEntry], server_mods: list[ModEntry]
) -> list[str]:
    workshop_ids: list[str] = []
    for entry in (*mods, *server_mods):
        if entry["id"] != "" and entry["id"] not in workshop_ids:
            workshop_ids.append(entry["id"])
    return workshop_ids


def is_workshop_id(entry: str) -> bool:
    return entry.isdigit()


def save_server_config(config_path: Path, config: ServerConfig) -> None:
    if config_path.exists():
        raise ValueError(f"{config_path} already exists")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    try:
        get_config(config_path)
    except ValueError:
        config_path.unlink()
        raise


def require_steam_username(username: str) -> None:
    if username == "":
        raise ValueError(
            "steamUsername is required. Anonymous login cannot install the DayZ server."
        )


def get_json_object(path: Path) -> dict[str, object]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("config must be a JSON object")
    raw: dict[str, object] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            raise ValueError("config keys must be strings")
        raw[key] = value
    return raw


def get_string(raw: dict[str, object], key: str) -> str:
    value = raw[key]
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def get_int(raw: dict[str, object], key: str) -> int:
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def get_bool(raw: dict[str, object], key: str) -> bool:
    value = raw[key]
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be true or false")
    return value


def get_mod_list(raw: dict[str, object], key: str) -> list[ModEntry]:
    value = raw[key]
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return [get_mod_entry(item, key) for item in value]


def get_mod_entry(item: object, key: str) -> ModEntry:
    if isinstance(item, str):
        if item == "":
            raise ValueError(f"{key} must not contain an empty entry")
        if is_workshop_id(item):
            return {"id": item, "title": "", "path": ""}
        return {"id": "", "title": "", "path": item}
    if isinstance(item, dict):
        workshop_id = item.get("id", "")
        title = item.get("title", "")
        if not isinstance(workshop_id, str) or not isinstance(title, str):
            raise ValueError(f"{key} entries must use a string id and title")
        if workshop_id == "":
            raise ValueError(f"{key} entries must include an id")
        return {"id": workshop_id, "title": title, "path": ""}
    raise ValueError(f"{key} must be workshop ids or objects with an id and title")


def get_string_list(raw: dict[str, object], key: str) -> list[str]:
    value = raw[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return cast(list[str], value)


def check_config_values(config: ServerConfig) -> None:
    require_plain(config["dayzClient"], "dayzClient")
    require_plain(config["destination"], "destination")
    require_plain(config["hostname"], "hostname")
    require_plain(config["profileDir"], "profileDir")
    require_plain(config["mission"], "mission")
    require_plain(config["password"], "password")
    require_plain(config["passwordAdmin"], "passwordAdmin")
    if config["hostname"] == "":
        raise ValueError("hostname must not be empty")
    if config["destination"] == "":
        raise ValueError("destination must not be empty")
    if any(char in config["hostname"] for char in '&|<>^%'):
        raise ValueError("hostname cannot contain command characters")
    if not 1 <= config["port"] <= 65535:
        raise ValueError("port must be from 1 to 65535")
    if config["cpuCount"] < 1:
        raise ValueError("cpuCount must be at least 1")
    if config["maxPlayers"] < 1:
        raise ValueError("maxPlayers must be at least 1")
    if config["instanceId"] < 0:
        raise ValueError("instanceId must not be negative")
    if config["restartSeconds"] < 0:
        raise ValueError("restartSeconds must not be negative")
    if len(config["shardId"]) != 6 or not config["shardId"].isalnum():
        raise ValueError("shardId must be six letters or digits")
    if config["steamId"] != "" and not is_steam64(config["steamId"]):
        raise ValueError("steamId must be 17 digits")
    for entry in (*config["mods"], *config["serverMods"]):
        check_mod_entry(entry)


def check_mod_entry(entry: ModEntry) -> None:
    if entry["id"] == "" and entry["path"] == "":
        raise ValueError("mod entries must not be empty")
    if entry["id"] != "" and not is_workshop_id(entry["id"]):
        raise ValueError("mod id must be digits")
    if entry["path"] != "":
        require_plain(entry["path"], "mod path")
    if "\n" in entry["title"] or "\r" in entry["title"]:
        raise ValueError("mod title must not contain newlines")


def require_plain(value: str, key: str) -> None:
    if any(char in value for char in '"\n\r'):
        raise ValueError(f"{key} must not contain quotes or newlines")

