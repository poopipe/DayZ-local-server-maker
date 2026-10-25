import csv
import io
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

PLAYER_CONNECT_LINE = "Player connect enabled"
LOG_NAME = "DayZServer_x64_*.RPT"
SERVER_IMAGE = "dayzserver_x64.exe"


def generate_server_window_title(hostname: str, port: int) -> str:
    return f"{hostname} ({port})"


def is_server_window_open(hostname: str, port: int) -> bool:
    title = generate_server_window_title(hostname, port)
    completed = subprocess.run(
        ["tasklist", "/v", "/fi", "imagename eq DayZServer_x64.exe"],
        capture_output=True,
        text=True,
        check=False,
    )
    return title.casefold() in completed.stdout.casefold()


def get_newest_server_log(profile_dir: Path) -> Path | None:
    logs = list(profile_dir.glob(LOG_NAME))
    if not logs:
        return None
    return max(logs, key=lambda path: path.stat().st_mtime)


def is_player_connect_enabled(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    return PLAYER_CONNECT_LINE in text


def wait_for_player_connect(profile_dir: Path, previous: Path | None) -> None:
    while True:
        current = get_newest_server_log(profile_dir)
        if (
            current is not None
            and current != previous
            and is_player_connect_enabled(current)
        ):
            return
        time.sleep(1)


def read_server_pids(listing: str, hostname: str, port: int) -> list[int]:
    title = generate_server_window_title(hostname, port).casefold()
    pids: list[int] = []
    for row in csv.reader(io.StringIO(listing)):
        if len(row) < 2 or row[0].casefold() != SERVER_IMAGE:
            continue
        if row[-1].casefold() != title:
            continue
        pids.append(int(row[1]))
    return pids


def get_server_pids(hostname: str, port: int) -> list[int]:
    completed = subprocess.run(
        [
            "tasklist",
            "/v",
            "/fo",
            "csv",
            "/fi",
            "imagename eq DayZServer_x64.exe",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return read_server_pids(completed.stdout, hostname, port)


def is_process_running(pid: int) -> bool:
    completed = subprocess.run(
        ["tasklist", "/fi", f"pid eq {pid}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return f'"{pid}"' in completed.stdout or f" {pid} " in completed.stdout


def stop_process_tree(pid: int) -> None:
    subprocess.run(
        ["taskkill", "/f", "/t", "/pid", str(pid)],
        check=False,
    )


def start_server(destination: Path) -> int:
    process = subprocess.Popen(
        ["cmd", "/c", "start.bat"],
        cwd=destination,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    return process.pid


def stop_server(pid: int, hostname: str, port: int) -> None:
    for server_pid in get_server_pids(hostname, port):
        stop_process_tree(server_pid)
    stop_process_tree(pid)
    for _ in range(10):
        if not is_server_window_open(hostname, port) and not is_process_running(pid):
            return
        time.sleep(1)
    title = generate_server_window_title(hostname, port)
    raise ValueError(f"Could not stop {title}.")


def start_server_for_profile(
    destination: Path,
    hostname: str,
    port: int,
    profile_dir: Path,
    start: Callable[[Path], int] = start_server,
    stop: Callable[[int, str, int], None] = stop_server,
    is_window_open: Callable[[str, int], bool] = is_server_window_open,
    wait: Callable[[Path, Path | None], None] = wait_for_player_connect,
) -> None:
    if is_window_open(hostname, port):
        title = generate_server_window_title(hostname, port)
        raise ValueError(f"{title} is already running. Close it first.")
    previous = get_newest_server_log(profile_dir)
    pid = start(destination)
    wait(profile_dir, previous)
    stop(pid, hostname, port)
