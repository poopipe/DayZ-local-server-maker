import os
import subprocess
import sys
from pathlib import Path

from local_server_maker.config import (
    ModEntry,
    ServerConfig,
    generate_steamcmd_dir,
    generate_workshop_ids,
    get_config,
    require_steam_username,
)
from local_server_maker.configure_bat import generate_configure_bat
from local_server_maker.globals_xml import write_login_logout_times
from local_server_maker.update_bat import generate_update_bat
from local_server_maker.links import get_mod_directory_name, place_mod
from local_server_maker.mod_path import generate_mod_directory
from local_server_maker.play_bat import check_dayz_client, generate_play_bat
from local_server_maker.server_cfg import (
    enable_cfg_gameplay_file,
    generate_server_cfg,
)
from local_server_maker.start_bat import generate_start_bat
from local_server_maker.steamcmd import (
    download_steamcmd,
    generate_steamcmd_args,
    is_steamcmd_installed,
    run_steamcmd,
)


def run(config_path: Path) -> None:
    config, destination = load_server(config_path)
    kept_cfg = read_kept_server_cfg(destination, config["overwriteConfigs"])
    mod_names, server_mod_names = download_and_place(config, config_path, destination)
    write_server_cfg(destination, config, kept_cfg)
    write_start_bat(destination, config, mod_names, server_mod_names)
    write_play_bat(destination, config, mod_names)
    write_configure_bat(destination, config_path)
    write_update_bat(destination, config_path)
    write_login_logout_times(destination, config["mission"])
    if config["launch"]:
        launch_server(destination)


def refresh_installed_mods(config_path: Path) -> None:
    config, destination = load_server(config_path)
    mod_names, server_mod_names = download_and_place(config, config_path, destination)
    write_start_bat(destination, config, mod_names, server_mod_names, force=True)
    write_play_bat(destination, config, mod_names, force=True)


def load_server(config_path: Path) -> tuple[ServerConfig, Path]:
    if os.name != "nt":
        raise ValueError("DayZ server setup runs on Windows")
    config = get_config(config_path)
    return config, Path(config["destination"]).resolve()


def download_and_place(
    config: ServerConfig, config_path: Path, destination: Path
) -> tuple[list[str], list[str]]:
    steamcmd_dir = generate_steamcmd_dir(config, config_path)
    workshop_ids = generate_workshop_ids(config["mods"], config["serverMods"])
    require_steam_username(config["steamUsername"])
    exe = prepare_steamcmd(steamcmd_dir)
    install_server(exe, destination, config, workshop_ids)
    mod_names = place_mods(destination, config["mods"], config["dayzAppId"])
    server_mod_names = place_mods(
        destination, config["serverMods"], config["dayzAppId"]
    )
    return mod_names, server_mod_names


def rewrite_launch_files(
    config_path: Path, write_cfg: bool, write_bat: bool
) -> None:
    config = get_config(config_path)
    destination = Path(config["destination"]).resolve()
    if write_cfg:
        write_server_cfg(destination, config, None)
    if write_bat:
        mod_names = mod_directory_names(
            destination, config["mods"], config["dayzAppId"]
        )
        server_mod_names = mod_directory_names(
            destination, config["serverMods"], config["dayzAppId"]
        )
        write_start_bat(
            destination, config, mod_names, server_mod_names, force=True
        )
        write_play_bat(destination, config, mod_names, force=True)


def launch_server(destination: Path) -> None:
    subprocess.Popen(
        ["cmd", "/c", "start.bat"],
        cwd=destination,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


def prepare_steamcmd(steamcmd_dir: Path) -> Path:
    installed = is_steamcmd_installed(steamcmd_dir)
    if not installed:
        print(f"Downloading SteamCMD into {steamcmd_dir}")
    exe = download_steamcmd(steamcmd_dir)
    if not installed:
        print("Updating SteamCMD")
        # The first run often exits after SteamCMD has updated itself.
        if run_steamcmd(exe, ["+quit"]) != 0:
            run_steamcmd(exe, ["+quit"])
    return exe


def install_server(
    exe: Path,
    destination: Path,
    config: ServerConfig,
    workshop_ids: list[str],
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    print(f"Installing or updating the DayZ server in {destination}")
    args = generate_steamcmd_args(
        str(destination),
        config["steamUsername"],
        config["serverAppId"],
        config["dayzAppId"],
        workshop_ids,
    )
    run_steamcmd(exe, args)
    if not (destination / "DayZServer_x64.exe").is_file():
        raise ValueError(f"SteamCMD did not install DayZServer_x64.exe in {destination}")


def place_mods(
    destination: Path, entries: list[ModEntry], dayz_app_id: str
) -> list[str]:
    names: list[str] = []
    for entry in entries:
        source = generate_mod_directory(entry, destination, dayz_app_id)
        print(f"Copying mod {source}")
        names.append(place_mod(destination, source))
    return names


def mod_directory_names(
    destination: Path, entries: list[ModEntry], dayz_app_id: str
) -> list[str]:
    return [
        get_mod_directory_name(generate_mod_directory(entry, destination, dayz_app_id))
        for entry in entries
    ]


def read_kept_server_cfg(destination: Path, overwrite: bool) -> bytes | None:
    if overwrite:
        return None
    cfg_path = destination / "serverDZ.cfg"
    if not cfg_path.is_file():
        return None
    return cfg_path.read_bytes()


def write_server_cfg(
    destination: Path, config: ServerConfig, kept: bytes | None
) -> None:
    cfg_path = destination / "serverDZ.cfg"
    if kept is not None:
        text = enable_cfg_gameplay_file(kept.decode("utf-8-sig"))
        cfg_path.write_text(text, encoding="utf-8")
        return
    if not cfg_path.is_file():
        raise ValueError("SteamCMD did not write serverDZ.cfg")
    print(f"Writing {cfg_path}")
    stock = cfg_path.read_text(encoding="utf-8-sig")
    text = generate_server_cfg(stock, config)
    cfg_path.write_text(text, encoding="utf-8", newline="\r\n")


def write_start_bat(
    destination: Path,
    config: ServerConfig,
    mod_names: list[str],
    server_mod_names: list[str],
    force: bool = False,
) -> None:
    bat_path = destination / "start.bat"
    if bat_path.is_file() and not config["overwriteConfigs"] and not force:
        return
    print(f"Writing {bat_path}")
    text = generate_start_bat(
        str(destination),
        config["hostname"],
        config["port"],
        config["cpuCount"],
        config["profileDir"],
        mod_names,
        server_mod_names,
        config["launchArgs"],
        config["restartSeconds"],
        [entry["id"] for entry in config["mods"] if entry["id"] != ""],
        [entry["id"] for entry in config["serverMods"] if entry["id"] != ""],
    )
    bat_path.write_text(text, encoding="utf-8", newline="\r\n")


def write_play_bat(
    destination: Path,
    config: ServerConfig,
    mod_names: list[str],
    force: bool = False,
) -> None:
    if config["dayzClient"] == "":
        return
    bat_path = destination / "play.bat"
    if bat_path.is_file() and not config["overwriteConfigs"] and not force:
        return
    message = check_dayz_client(config["dayzClient"])
    if message != "":
        raise ValueError(message)
    print(f"Writing {bat_path}")
    mod_directories = [str(destination / f"@{name}") for name in mod_names]
    text = generate_play_bat(
        config["dayzClient"],
        mod_directories,
        config["hostname"],
        config["port"],
        config["profileDir"],
    )
    bat_path.write_text(text, encoding="utf-8", newline="\r\n")


def write_configure_bat(destination: Path, config_path: Path) -> None:
    bat_path = destination / "configure.bat"
    print(f"Writing {bat_path}")
    text = generate_configure_bat(sys.executable, str(config_path.resolve()))
    bat_path.write_text(text, encoding="utf-8", newline="\r\n")


def write_update_bat(destination: Path, config_path: Path) -> None:
    bat_path = destination / "update.bat"
    print(f"Writing {bat_path}")
    text = generate_update_bat(sys.executable, str(config_path.resolve()))
    bat_path.write_text(text, encoding="utf-8", newline="\r\n")
