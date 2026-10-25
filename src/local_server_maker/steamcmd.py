import subprocess
import urllib.request
import zipfile
from pathlib import Path

from local_server_maker.consts import STEAMCMD_URL


def is_steamcmd_installed(directory: Path) -> bool:
    return (directory / "steamcmd.exe").is_file()


def download_steamcmd(directory: Path, url: str = STEAMCMD_URL) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    exe = directory / "steamcmd.exe"
    if exe.is_file():
        return exe
    zip_path = directory / "steamcmd.zip"
    urllib.request.urlretrieve(url, zip_path)
    extract_steamcmd_zip(zip_path, directory)
    zip_path.unlink()
    if not exe.is_file():
        raise ValueError(f"steamcmd zip did not contain steamcmd.exe in {directory}")
    return exe


def run_steamcmd(exe: Path, args: list[str]) -> int:
    completed = subprocess.run([str(exe), *args], cwd=exe.parent, check=False)
    return completed.returncode


def generate_steamcmd_args(
    destination: str,
    username: str,
    server_app_id: str,
    dayz_app_id: str,
    workshop_ids: list[str],
) -> list[str]:
    login_name = username if username != "" else "anonymous"
    # app_info_print loads the app record. A fresh SteamCMD has none, and the
    # following app_update then reports "Missing configuration".
    args = [
        "+@ShutdownOnFailedCommand",
        "1",
        "+force_install_dir",
        destination,
        "+login",
        login_name,
        "+app_info_update",
        "1",
        "+app_info_print",
        server_app_id,
        "+app_update",
        server_app_id,
        "validate",
    ]
    for workshop_id in workshop_ids:
        args.extend(["+workshop_download_item", dayz_app_id, workshop_id])
    args.append("+quit")
    return args


def extract_steamcmd_zip(zip_path: Path, directory: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            member = Path(info.filename)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError(f"steamcmd zip has an unsafe path: {info.filename}")
        archive.extractall(directory)
