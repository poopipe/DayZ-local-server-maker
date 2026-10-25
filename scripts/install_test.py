import sys
from pathlib import Path

from local_server_maker.config import (
    generate_steamcmd_dir,
    get_config,
    require_steam_username,
    save_server_config,
)
from local_server_maker.consts import KEY_FILE_NAME, STEAM_ID_FILE_NAME
from local_server_maker.install_dir import (
    remove_tree,
    require_removable_install_dir,
    require_removable_steamcmd_dir,
)
from local_server_maker.run import run
from local_server_maker.new_server import build_server_config

USAGE = "Usage: install_test.py [--clear-steamcmd] [CONFIG.json]"


def main(argv: list[str] | None = None) -> None:
    arguments = sys.argv[1:] if argv is None else argv
    clear_steamcmd, config_arguments = get_clear_steamcmd(arguments)
    if len(config_arguments) > 1:
        raise SystemExit(USAGE)
    project_root = Path(__file__).resolve().parents[1]
    config_path = get_config_path(config_arguments, project_root)
    try:
        clear_previous_install(config_path, project_root, clear_steamcmd)
        print("Answer the setup questions. Install starts after the answers.")
        config = build_server_config(input)
        config_path = Path(config["destination"]) / "config.json"
        save_server_config(config_path, config)
        clear_server_files(config_path, project_root, clear_steamcmd)
        run(config_path)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error


def clear_server_files(
    config_path: Path, project_root: Path, clear_steamcmd: bool
) -> None:
    config = get_config(config_path)
    require_steam_username(config["steamUsername"])
    destination = Path(config["destination"])
    steamcmd_dir = generate_steamcmd_dir(config, config_path)
    require_removable_install_dir(destination, project_root, steamcmd_dir)
    if clear_steamcmd:
        require_removable_steamcmd_dir(steamcmd_dir, project_root)
        remove_if_present(steamcmd_dir)
    else:
        print(f"Keeping {steamcmd_dir.resolve()}")
    keep = {"config.json", STEAM_ID_FILE_NAME, KEY_FILE_NAME}
    if not destination.exists():
        print(f"{destination.resolve()} does not exist yet")
        return
    for child in list(destination.iterdir()):
        if child.name in keep:
            continue
        print(f"Removing {child.resolve()}")
        remove_tree(child.resolve())


def clear_install_dir(
    config_path: Path, project_root: Path, clear_steamcmd: bool
) -> None:
    config = get_config(config_path)
    require_steam_username(config["steamUsername"])
    destination = Path(config["destination"])
    steamcmd_dir = generate_steamcmd_dir(config, config_path)
    require_removable_install_dir(destination, project_root, steamcmd_dir)
    if clear_steamcmd:
        require_removable_steamcmd_dir(steamcmd_dir, project_root)
        remove_if_present(steamcmd_dir)
    else:
        print(f"Keeping {steamcmd_dir.resolve()}")
    remove_if_present(destination)


def get_clear_steamcmd(arguments: list[str]) -> tuple[bool, list[str]]:
    clear_steamcmd = False
    remaining: list[str] = []
    for argument in arguments:
        if argument == "--clear-steamcmd":
            clear_steamcmd = True
        else:
            remaining.append(argument)
    return clear_steamcmd, remaining


def get_config_path(arguments: list[str], project_root: Path) -> Path:
    if arguments:
        config_path = Path(arguments[0])
        if not config_path.is_absolute():
            config_path = Path.cwd() / config_path
    else:
        config_path = project_root / "config.json"
    example = project_root / "config.example.json"
    if config_path.resolve() == example.resolve():
        raise ValueError(
            "install_test writes config.json and will not replace the example"
        )
    return config_path


def clear_previous_install(
    config_path: Path, project_root: Path, clear_steamcmd: bool
) -> None:
    if config_path.is_file():
        clear_install_dir(config_path, project_root, clear_steamcmd)
        config_path.unlink()
        return
    example = project_root / "config.example.json"
    if example.is_file():
        clear_install_dir(example, project_root, clear_steamcmd)


def remove_if_present(path: Path) -> None:
    if not path.exists():
        print(f"{path.resolve()} does not exist yet")
        return
    print(f"Removing {path.resolve()}")
    remove_tree(path.resolve())


if __name__ == "__main__":
    main()
