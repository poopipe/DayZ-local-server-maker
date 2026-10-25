import argparse
import sys
from pathlib import Path

from local_server_maker.config import save_server_config
from local_server_maker.configure_server import run_configure
from local_server_maker.run import run
from local_server_maker.new_server import build_server_config


def run_setup() -> None:
    config = build_server_config(input)
    config_path = Path(config["destination"]) / "config.json"
    save_server_config(config_path, config)
    run(config_path)


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m local_server_maker",
        usage=(
            "%(prog)s CONFIG.json\n"
            "       %(prog)s new_server\n"
            "       %(prog)s configure_server CONFIG.json"
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser("run")
    install.add_argument("config", type=Path)
    commands.add_parser("new_server")
    configure_server = commands.add_parser("configure_server")
    configure_server.add_argument("config", type=Path)
    return parser


def main(argv: list[str] | None = None) -> None:
    arguments = sys.argv[1:] if argv is None else argv
    known = {"run", "new_server", "configure_server", "-h", "--help"}
    if not arguments or arguments[0] not in known:
        arguments = ["run", *arguments]
    try:
        parsed = argument_parser().parse_args(arguments)
        if parsed.command == "new_server":
            run_setup()
            return
        config = Path(parsed.config)
        if parsed.command == "configure_server":
            run_configure(config)
        else:
            run(config)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
