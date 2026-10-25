def quote_launch_argument(flag: str, value: str) -> str:
    argument = f"{flag}={value}"
    if any(char.isspace() for char in value):
        return f'"{argument}"'
    return argument


def generate_start_bat(
    destination: str,
    hostname: str,
    port: int,
    cpu_count: int,
    profile_dir: str,
    mod_names: list[str],
    server_mod_names: list[str],
    launch_args: list[str],
    restart_seconds: int,
    mod_ids: list[str] | None = None,
    server_mod_ids: list[str] | None = None,
) -> str:
    title = f"{hostname} ({port})"
    launch = " ".join(
        generate_server_arguments(
            port,
            cpu_count,
            profile_dir,
            mod_names,
            server_mod_names,
            launch_args,
        )
    )
    wait = "/wait " if restart_seconds == 0 else ""
    start_line = f'start "{title}" {wait}/min DayZServer_x64.exe {launch}'
    lines = ["@echo off", *generate_id_lines("mod ids", mod_ids or [])]
    lines.extend(generate_id_lines("server mod ids", server_mod_ids or []))
    lines.extend(
        [
            "setlocal",
            f'cd /d "{destination}"',
            f'if not exist "{profile_dir}" mkdir "{profile_dir}"',
        ]
    )
    if restart_seconds == 0:
        lines.append(f"echo (%time%) {hostname} started.")
        lines.append(start_line)
    else:
        lines.extend(
            [
                ":restart",
                f"echo (%time%) {hostname} started.",
                start_line,
                f"timeout /t {restart_seconds} /nobreak",
                f'taskkill /FI "WINDOWTITLE eq {title}" /T /F',
                "timeout /t 10 /nobreak",
                "goto restart",
            ]
        )
    return "\n".join(lines) + "\n"


def generate_server_arguments(
    port: int,
    cpu_count: int,
    profile_dir: str,
    mod_names: list[str],
    server_mod_names: list[str],
    launch_args: list[str],
) -> list[str]:
    arguments = [
        "-config=serverDZ.cfg",
        f"-port={port}",
        f"-cpuCount={cpu_count}",
    ]
    mod_argument = generate_mod_argument("-mod", mod_names)
    if mod_argument != "":
        arguments.append(mod_argument)
    server_argument = generate_mod_argument("-servermod", server_mod_names)
    if server_argument != "":
        arguments.append(server_argument)
    arguments.extend(launch_args)
    arguments.append(f"-profiles={profile_dir}")
    return arguments


def generate_id_lines(label: str, workshop_ids: list[str]) -> list[str]:
    if not workshop_ids:
        return []
    return [f"rem {label}: {' '.join(workshop_ids)}"]


def generate_mod_argument(flag: str, names: list[str]) -> str:
    if not names:
        return ""
    joined = ";".join(f"@{name}" for name in names)
    return quote_launch_argument(flag, joined)
