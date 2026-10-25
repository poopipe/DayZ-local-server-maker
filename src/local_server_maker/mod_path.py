from pathlib import Path

from local_server_maker.config import ModEntry


def generate_mod_directory(
    entry: ModEntry, destination: Path, dayz_app_id: str
) -> Path:
    if entry["path"] != "":
        return Path(entry["path"])
    if entry["id"] == "":
        raise ValueError("mod entry has no workshop id or directory")
    return (
        destination
        / "steamapps"
        / "workshop"
        / "content"
        / dayz_app_id
        / entry["id"]
    )
