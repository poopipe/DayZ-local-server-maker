from pathlib import Path

from local_server_maker.ask import Prompt, ask_number, ask_required, ask_text
from local_server_maker.config import ModEntry, ServerConfig
from local_server_maker.consts import DAYZ_APP_ID, SERVER_APP_ID
from local_server_maker.play_bat import check_dayz_client
from local_server_maker.steam_id import get_saved_steam_id, is_steam64, save_steam_id
from local_server_maker.workshop import WorkshopItem, WorkshopSearch, ask_pick


def build_server_config(
    prompt: Prompt, search: WorkshopSearch, settings_dir: Path | None = None
) -> ServerConfig:
    folder = ask_required(prompt, "Server folder")
    hostname = ask_text(prompt, "Server name", Path(folder).name)
    mission = ask_text(prompt, "Mission", "dayzOffline.chernarusplus")
    port = ask_number(prompt, "Port", 2302)
    max_players = ask_number(prompt, "Max players", 10)
    password = ask_text(prompt, "Join password", "")
    password_admin = ask_text(prompt, "Admin password", "")
    cpu_count = ask_number(prompt, "CPU count", 4)
    instance_id = ask_number(prompt, "Instance id", 2)
    shard_id = ask_text(prompt, "Shard id", "local1")
    username = ask_required(prompt, "Steam account name")
    steam_id = ask_steam_id(prompt, settings_dir, username)
    dayz_client = ask_dayz_client(prompt)
    mods = collect_mods(prompt, search, "Client")
    server_mods = collect_mods(prompt, search, "Server")
    return {
        "steamCmdDir": "",
        "steamUsername": username,
        "steamId": steam_id,
        "dayzClient": dayz_client,
        "dayzAppId": DAYZ_APP_ID,
        "serverAppId": SERVER_APP_ID,
        "destination": folder,
        "hostname": hostname,
        "port": port,
        "cpuCount": cpu_count,
        "profileDir": "profile",
        "mission": mission,
        "password": password,
        "passwordAdmin": password_admin,
        "maxPlayers": max_players,
        "instanceId": instance_id,
        "shardId": shard_id,
        "restartSeconds": 0,
        "launch": False,
        "overwriteConfigs": False,
        "mods": mods,
        "serverMods": server_mods,
        "launchArgs": ["-dologs", "-adminlog", "-netlog", "-freezecheck"],
    }


def collect_mods(prompt: Prompt, search: WorkshopSearch, kind: str) -> list[ModEntry]:
    chosen: list[ModEntry] = []
    while True:
        name = prompt(f"{kind} mod name (blank to finish): ").strip()
        if name == "":
            return chosen
        items = search_mods(search, name)
        if items is None:
            continue
        if not items:
            print(f'No Workshop items matched "{name}".')
            continue
        print(f'Found {len(items)} for "{name}":')
        for index, item in enumerate(items, start=1):
            print(f"{index}. {item['title']} ({item['id']})")
        picked = ask_pick(prompt, items)
        chosen.append({"id": picked["id"], "title": picked["title"], "path": ""})


def search_mods(search: WorkshopSearch, name: str) -> list[WorkshopItem] | None:
    try:
        return search(DAYZ_APP_ID, name)
    except ValueError as error:
        print(error)
        return None


def ask_dayz_client(prompt: Prompt) -> str:
    while True:
        answer = prompt("DayZ client folder: ").strip()
        if answer == "":
            print("DayZ client folder is required")
            continue
        message = check_dayz_client(answer)
        if message != "":
            print(message)
            continue
        return str(Path(answer))


def ask_steam_id(prompt: Prompt, settings_dir: Path | None, username: str) -> str:
    if settings_dir is not None:
        saved = get_saved_steam_id(settings_dir, username)
        if saved is not None:
            print(f"Using Steam ID {saved}")
            return saved
    while True:
        answer = prompt("Steam ID: ").strip()
        if is_steam64(answer):
            if settings_dir is not None:
                save_steam_id(settings_dir, username, answer)
            return answer
        print("Steam ID must be 17 digits")
