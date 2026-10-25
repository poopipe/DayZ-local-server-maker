def generate_configure_bat(python_executable: str, config_path: str) -> str:
    if '"' in python_executable or '"' in config_path:
        raise ValueError("configure.bat paths cannot contain quotes")
    return (
        "@echo off\n"
        f'"{python_executable}" -m local_server_maker '
        f'configure_server "{config_path}"\n'
        "pause\n"
    )
