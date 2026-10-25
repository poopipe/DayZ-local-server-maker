import json
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

from local_server_maker.ask import Prompt, ask_listed_name
from local_server_maker.steam_id import is_steam64

COMMUNITY_ONLINE_TOOLS_ID = "1564026768"


class SupportedMod(TypedDict):
    id: str
    label: str
    configure: Callable[[Path, str], None]


def generate_community_online_tools_admin() -> str:
    return json.dumps({"Roles": ["admin"]}, indent=4) + "\n"


def generate_community_online_tools_player_path(
    profile_dir: Path, steam_id: str
) -> Path:
    return (
        profile_dir / "PermissionsFramework" / "Players" / f"{steam_id}.json"
    )


def configure_community_online_tools(profile_dir: Path, steam_id: str) -> None:
    if not is_steam64(steam_id):
        raise ValueError("steamId is required.")
    path = generate_community_online_tools_player_path(profile_dir, steam_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_community_online_tools_admin(), encoding="utf-8")


SUPPORTED_MODS: tuple[SupportedMod, ...] = (
    {
        "id": COMMUNITY_ONLINE_TOOLS_ID,
        "label": "Community Online Tools",
        "configure": configure_community_online_tools,
    },
)


def configure_supported_mod(
    prompt: Prompt,
    profile_dir: Path,
    steam_id: str,
    supported: tuple[SupportedMod, ...] = SUPPORTED_MODS,
) -> None:
    labels = [mod["label"] for mod in supported]
    print("Supported mods:")
    for index, label in enumerate(labels, start=1):
        print(f"{index}. {label}")
    chosen = ask_listed_name(prompt, labels, "Pick a mod (blank to cancel): ")
    if chosen is None:
        return
    for mod in supported:
        if mod["label"] == chosen:
            mod["configure"](profile_dir, steam_id)
            return
