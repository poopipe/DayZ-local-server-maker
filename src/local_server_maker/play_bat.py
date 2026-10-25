from pathlib import Path

from local_server_maker.start_bat import quote_launch_argument


def check_dayz_client(client_dir: str) -> str:
    path = Path(client_dir)
    if (path / "DayZ_BE.exe").is_file() and (path / "DayZ_x64.exe").is_file():
        return ""
    return f"{path} must contain DayZ_BE.exe and DayZ_x64.exe"


def steam_restart_lines() -> list[str]:
    steam_key = "HKCU\\Software\\Valve\\Steam"
    process_key = steam_key + "\\ActiveProcess"
    steam_path = (
        'for /f "tokens=2*" %%A in ('
        f'\'reg query {steam_key} /v SteamPath ^| find "SteamPath"\') '
        'do set "STEAMDIR=%%B"'
    )
    old_pid = (
        'for /f "tokens=3" %%A in ('
        f'\'reg query {process_key} /v pid ^| find "pid"\') '
        'do set "OLDPID=%%A"'
    )
    new_pid = (
        'for /f "tokens=3" %%A in ('
        f'\'reg query {process_key} /v pid ^| find "pid"\') '
        'do set "NEWPID=%%A"'
    )
    active_user = (
        'for /f "tokens=3" %%A in ('
        f'\'reg query {process_key} /v ActiveUser ^| find "ActiveUser"\') '
        'do set "STEAMUSER=%%A"'
    )
    return [
        'tasklist /fi "imagename eq steam.exe" | find /i "steam.exe" >nul',
        "if errorlevel 1 goto restart_steam",
        active_user,
        "if not defined STEAMUSER goto restart_steam",
        'if "%STEAMUSER%"=="0x0" goto restart_steam',
        'if "%STEAMUSER%"=="0x00000000" goto restart_steam',
        "echo Steam is signed in",
        "goto launch_dayz",
        ":restart_steam",
        "echo Restarting Steam",
        steam_path,
        "if not defined STEAMDIR (",
        "  echo Steam install path was not found",
        "  pause",
        "  exit /b 1",
        ")",
        'set "STEAMDIR=%STEAMDIR:/=\\%"',
        'if not exist "%STEAMDIR%\\steam.exe" (',
        '  echo Steam was not found at "%STEAMDIR%\\steam.exe"',
        "  pause",
        "  exit /b 1",
        ")",
        old_pid,
        'tasklist /fi "imagename eq steam.exe" | find /i "steam.exe" >nul',
        "if errorlevel 1 goto start_steam",
        '"%STEAMDIR%\\steam.exe" -shutdown',
        ":wait_steam_exit",
        'tasklist /fi "imagename eq steam.exe" | find /i "steam.exe" >nul',
        "if errorlevel 1 goto start_steam",
        "timeout /t 1 /nobreak >nul",
        "goto wait_steam_exit",
        ":start_steam",
        'start "" "%STEAMDIR%\\steam.exe"',
        "echo Waiting for Steam to sign in",
        'set "SAWLOGOUT="',
        'set "HOLD=0"',
        ":wait_steam_login",
        "timeout /t 1 /nobreak >nul",
        'tasklist /fi "imagename eq steam.exe" | find /i "steam.exe" >nul',
        "if errorlevel 1 goto wait_steam_login",
        new_pid,
        active_user,
        'if "%NEWPID%"=="0x0" goto wait_steam_login',
        'if "%NEWPID%"=="0x00000000" goto wait_steam_login',
        'if "%NEWPID%"=="%OLDPID%" goto wait_steam_login',
        'if "%STEAMUSER%"=="0x0" goto mark_logged_out',
        'if "%STEAMUSER%"=="0x00000000" goto mark_logged_out',
        "if defined SAWLOGOUT goto launch_dayz",
        "set /a HOLD+=1",
        "if %HOLD% geq 8 goto launch_dayz",
        "goto wait_steam_login",
        ":mark_logged_out",
        'set "SAWLOGOUT=1"',
        'set "HOLD=0"',
        "goto wait_steam_login",
        ":launch_dayz",
    ]


def server_lines(hostname: str, port: int) -> list[str]:
    title = f"{hostname} ({port})"
    running = (
        'tasklist /v /fi "imagename eq DayZServer_x64.exe" '
        '| find /i "%SERVER_TITLE%" >nul'
    )
    return [
        f'set "SERVER_TITLE={title}"',
        running,
        "if errorlevel 1 goto start_server",
        "echo Server is running",
        "goto launch_client",
        ":start_server",
        "echo Starting the server",
        "call :newest_log",
        'set "OLDLOG=%NEWLOG%"',
        'start "DayZ server" "%~dp0start.bat"',
        "echo Waiting for the mission to load",
        ":wait_mission",
        "timeout /t 1 /nobreak >nul",
        "call :newest_log",
        "if not defined NEWLOG goto wait_mission",
        'if /i "%NEWLOG%"=="%OLDLOG%" goto wait_mission',
        'findstr /c:"Player connect enabled" "%NEWLOG%" >nul',
        "if errorlevel 1 goto wait_mission",
        ":launch_client",
    ]


def newest_log_lines(profile_dir: str) -> list[str]:
    directory = f"%~dp0{profile_dir}\\"
    listed = (
        'for /f "delims=" %%F in ('
        f'\'dir /b /o-d "{directory}DayZServer_x64_*.RPT" 2^>nul\') do ('
    )
    return [
        ":newest_log",
        'set "NEWLOG="',
        listed,
        f'  set "NEWLOG={directory}%%F"',
        "  goto :eof",
        ")",
        "goto :eof",
    ]


def generate_play_bat(
    dayz_client: str,
    mod_directories: list[str],
    hostname: str,
    port: int,
    profile_dir: str,
) -> str:
    quoted = '"' in dayz_client or '"' in hostname or '"' in profile_dir
    if quoted or any('"' in path for path in mod_directories):
        raise ValueError("play.bat paths cannot contain quotes")
    game_dir = str(Path(dayz_client))
    executable = str(Path(dayz_client) / "DayZ_BE.exe")
    launch = f'start "" "{executable}" 0 1 1 -exe DayZ_x64.exe'
    if mod_directories:
        mods = quote_launch_argument("-mod", ";".join(mod_directories))
        launch = f"{launch} {mods}"
    launch = f"{launch} -connect=127.0.0.1 -port={port}"
    lines = ["@echo off", "setlocal", *steam_restart_lines()]
    lines.extend(server_lines(hostname, port))
    lines.extend([f'cd /d "{game_dir}"', launch, "goto :eof"])
    lines.extend(newest_log_lines(profile_dir))
    return "\n".join(lines) + "\n"
