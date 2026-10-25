import os
import shutil
from pathlib import Path

from local_server_maker.steam import get_mod_name


def place_mod(destination: Path, source: Path) -> str:
    name = get_mod_folder_name(source)
    copy_mod(destination / f"@{name}", source)
    copy_bikeys(source, destination / "keys")
    return name


def get_mod_folder_name(source: Path) -> str:
    if not source.is_dir():
        raise ValueError(f"mod folder does not exist: {source}")
    meta_path = source / "meta.cpp"
    if not meta_path.is_file():
        raise ValueError(f"{source} has no meta.cpp")
    return get_mod_name(meta_path.read_text(encoding="utf-8"))


def copy_mod(destination: Path, source: Path) -> None:
    if not source.is_dir():
        raise ValueError(f"mod folder does not exist: {source}")
    if destination.exists() or is_reparse_point(destination):
        remove_mod_folder(destination)
    shutil.copytree(source, destination)


def remove_mod_folder(path: Path) -> None:
    if is_reparse_point(path):
        os.rmdir(path)
        return
    shutil.rmtree(path)


def list_bikey_names(mod_dir: Path) -> list[str]:
    if not mod_dir.is_dir():
        return []
    names: list[str] = []
    for folder_name in ("keys", "Keys"):
        folder = mod_dir / folder_name
        if not folder.is_dir():
            continue
        names.extend(path.name for path in folder.glob("*.bikey"))
    return names


def copy_bikeys(mod_dir: Path, keys_dir: Path) -> None:
    copied = False
    for folder_name in ("keys", "Keys"):
        folder = mod_dir / folder_name
        if not folder.is_dir():
            continue
        for key_file in folder.glob("*.bikey"):
            if not copied:
                keys_dir.mkdir(parents=True, exist_ok=True)
                copied = True
            target = keys_dir / key_file.name
            target.write_bytes(key_file.read_bytes())


def is_reparse_point(path: Path) -> bool:
    try:
        os.readlink(path)
    except OSError:
        return False
    return True

