import re

from local_server_maker.config import ServerConfig


def generate_server_cfg(stock: str, config: ServerConfig) -> str:
    text = stock
    text = replace_string(text, "hostname", config["hostname"])
    text = replace_string(text, "password", config["password"])
    text = replace_string(text, "passwordAdmin", config["passwordAdmin"])
    text = replace_assignment(text, "maxPlayers", str(config["maxPlayers"]))
    text = replace_string(text, "shardId", config["shardId"])
    text = replace_assignment(text, "instanceId", str(config["instanceId"]))
    text = replace_string(text, "template", config["mission"])
    return text


def replace_string(text: str, key: str, value: str) -> str:
    if '"' in value or "\n" in value or "\r" in value:
        raise ValueError(f"{key} cannot contain quotes or newlines")
    return replace_assignment(text, key, f'"{value}"')


def replace_assignment(text: str, key: str, rendered: str) -> str:
    pattern = re.compile(
        rf'^(\s*{re.escape(key)}\s*=\s*)(?:"[^"]*"|-?\d+)(\s*;)',
        re.MULTILINE,
    )

    def repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}{rendered}{match.group(2)}"

    updated, count = pattern.subn(repl, text, count=1)
    if count != 1:
        raise ValueError(f"serverDZ.cfg has no {key} assignment")
    return updated
