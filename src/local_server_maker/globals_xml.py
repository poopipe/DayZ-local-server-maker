import re
from pathlib import Path

LOGIN_LOGOUT_SECONDS = "5"


def set_login_logout_times(text: str, seconds: str = LOGIN_LOGOUT_SECONDS) -> str:
    text = set_global_value(text, "TimeLogin", seconds)
    return set_global_value(text, "TimeLogout", seconds)


def set_global_value(text: str, name: str, value: str) -> str:
    pattern = re.compile(
        rf'(<var name="{re.escape(name)}" type="0" value=")\d+("\s*/>)'
    )
    updated, count = pattern.subn(rf"\g<1>{value}\2", text, count=1)
    if count != 1:
        raise ValueError(f"globals.xml has no {name}")
    return updated


def write_login_logout_times(destination: Path, mission: str) -> None:
    path = destination / "mpmissions" / mission / "db" / "globals.xml"
    if not path.is_file():
        raise ValueError(f"{path} does not exist")
    text = path.read_text(encoding="utf-8")
    path.write_text(set_login_logout_times(text), encoding="utf-8")
