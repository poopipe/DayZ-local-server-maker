import os
from pathlib import Path
from typing import Literal, TypedDict

from local_server_maker.ask import Prompt, ask_listed_name, pick_index
from local_server_maker.config import (
    ModEntry,
    ServerConfig,
    get_config,
    write_config,
)
from local_server_maker.links import (
    get_mod_folder_name,
    is_reparse_point,
    list_bikey_names,
    remove_mod_folder,
)
from local_server_maker.mod_path import generate_mod_directory
from local_server_maker.run import refresh_installed_mods, rewrite_launch_files
from local_server_maker.workshop import WorkshopSearch, ask_pick, bind_workshop_search

OPTIONS = (
    ("1", "Install a mod"),
    ("2", "Uninstall a mod"),
    ("3", "Rename"),
    ("4", "Change the mission"),
)

ModList = Literal["mods", "serverMods"]


class Installed(TypedDict):
    side: ModList
    entry: ModEntry
    label: str


def run_configure(
    config_path: Path,
    prompt: Prompt = input,
    search: WorkshopSearch | None = None,
) -> None:
    if os.name != "nt":
        raise ValueError("DayZ server setup runs on Windows")
    config_path = config_path.resolve()
    if search is None:
        search = bind_workshop_search(config_path.parent, prompt)
    config = get_config(config_path)
    destination = Path(config["destination"]).resolve()
    print(f"{config['hostname']} ({destination})")
    while True:
        for number, label in OPTIONS:
            print(f"{number}. {label}")
        choice = prompt("Choose an option (blank to finish): ").strip()
        if choice == "":
            return
        try:
            if choice == "1":
                install_mod(config_path, prompt, search)
            elif choice == "2":
                uninstall_mod(config_path, prompt)
            elif choice == "3":
                rename_server(config_path, prompt)
            elif choice == "4":
                change_mission(config_path, prompt)
            else:
                print("That option is not in the list.")
        except ValueError as error:
            print(error)


def get_missions(destination: Path) -> list[str]:
    root = destination / "mpmissions"
    if not root.is_dir():
        raise ValueError(f"{root} does not exist")
    names = sorted(path.name for path in root.iterdir() if path.is_dir())
    if not names:
        raise ValueError(f"{root} has no missions")
    return names


def install_mod(config_path: Path, prompt: Prompt, search: WorkshopSearch) -> None:
    side = ask_mod_side(prompt)
    name = prompt("Mod name (blank to cancel): ").strip()
    if name == "":
        return
    config = get_config(config_path)
    try:
        items = search(config["dayzAppId"], name)
    except ValueError as error:
        print(error)
        return
    if not items:
        print(f'No Workshop items matched "{name}".')
        return
    print(f'Found {len(items)} for "{name}":')
    for index, item in enumerate(items, start=1):
        print(f"{index}. {item['title']} ({item['id']})")
    picked = ask_pick(prompt, items)
    if any(
        entry["id"] == picked["id"]
        for entry in (*config["mods"], *config["serverMods"])
    ):
        print(f"{picked['title']} is already installed.")
        return
    entries = config["mods"] if side == "mods" else config["serverMods"]
    entries.append({"id": picked["id"], "title": picked["title"], "path": ""})
    write_config(config_path, config)
    try:
        refresh_installed_mods(config_path)
    except (OSError, ValueError):
        entries.pop()
        write_config(config_path, config)
        raise


def uninstall_mod(config_path: Path, prompt: Prompt) -> None:
    config = get_config(config_path)
    listed = installed_mods(config)
    if not listed:
        print("No mods are installed.")
        return
    for index, item in enumerate(listed, start=1):
        kind = "client" if item["side"] == "mods" else "server"
        print(f"{index}. {item['label']} ({kind})")
    picked = ask_installed_pick(prompt, listed)
    if picked is None:
        return
    destination = Path(config["destination"]).resolve()
    source = generate_mod_directory(
        picked["entry"], destination, config["dayzAppId"]
    )
    folder_name = ""
    try:
        folder_name = get_mod_folder_name(source)
    except ValueError as error:
        print(error)
    entries = config["mods"] if picked["side"] == "mods" else config["serverMods"]
    entries.remove(picked["entry"])
    write_config(config_path, config)
    if folder_name != "":
        installed = destination / f"@{folder_name}"
        if installed.exists() or is_reparse_point(installed):
            remove_mod_folder(installed)
        remaining = config["mods"] + config["serverMods"]
        remove_unused_bikeys(
            destination, source, remaining, config["dayzAppId"]
        )
    rewrite_launch_files(config_path, write_cfg=False, write_bat=True)


def rename_server(config_path: Path, prompt: Prompt) -> None:
    config = get_config(config_path)
    name = prompt(f"Server name [{config['hostname']}]: ").strip()
    if name == "" or name == config["hostname"]:
        return
    config["hostname"] = name
    write_config(config_path, config)
    rewrite_launch_files(config_path, write_cfg=True, write_bat=True)


def change_mission(config_path: Path, prompt: Prompt) -> None:
    config = get_config(config_path)
    destination = Path(config["destination"]).resolve()
    names = get_missions(destination)
    print("Missions:")
    for index, mission in enumerate(names, start=1):
        print(f"{index}. {mission}")
    mission = ask_listed_name(prompt, names, "Pick a mission (blank to cancel): ")
    if mission is None:
        return
    config["mission"] = mission
    write_config(config_path, config)
    rewrite_launch_files(config_path, write_cfg=True, write_bat=False)


def ask_mod_side(prompt: Prompt) -> ModList:
    while True:
        answer = prompt("Client or server mod? [client]: ").strip().casefold()
        if answer in ("", "client"):
            return "mods"
        if answer == "server":
            return "serverMods"
        print("Answer client or server.")


def installed_mods(config: ServerConfig) -> list[Installed]:
    listed: list[Installed] = []
    for entry in config["mods"]:
        listed.append(
            {"side": "mods", "entry": entry, "label": mod_label(entry)}
        )
    for entry in config["serverMods"]:
        listed.append(
            {
                "side": "serverMods",
                "entry": entry,
                "label": mod_label(entry),
            }
        )
    return listed


def mod_label(entry: ModEntry) -> str:
    if entry["title"] != "":
        return entry["title"]
    if entry["id"] != "":
        return entry["id"]
    return entry["path"]


def ask_installed_pick(prompt: Prompt, listed: list[Installed]) -> Installed | None:
    while True:
        choice = prompt("Pick a mod to uninstall (blank to cancel): ").strip()
        if choice == "":
            return None
        labels = [item["label"] for item in listed]
        index, message = pick_index(labels, choice)
        if index is None:
            print(message)
            continue
        return listed[index]


def remove_unused_bikeys(
    destination: Path,
    source: Path,
    remaining: list[ModEntry],
    dayz_app_id: str,
) -> None:
    used: set[str] = set()
    for entry in remaining:
        other = generate_mod_directory(entry, destination, dayz_app_id)
        used.update(list_bikey_names(other))
    keys_dir = destination / "keys"
    for name in list_bikey_names(source):
        if name in used:
            continue
        key_path = keys_dir / name
        if key_path.is_file():
            key_path.unlink()
