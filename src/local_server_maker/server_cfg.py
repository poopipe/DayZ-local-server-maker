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
    return enable_cfg_gameplay_file(text)


def enable_cfg_gameplay_file(text: str) -> str:
    pattern = re.compile(
        r"^(\s*enableCfgGameplayFile\s*=\s*)\d+(\s*;)",
        re.MULTILINE,
    )
    updated, count = pattern.subn(r"\g<1>1\2", text, count=1)
    if count == 1:
        return updated
    line = "enableCfgGameplayFile = 1;\n"
    marker = "class Missions"
    if marker in text:
        return text.replace(marker, line + "\n" + marker, 1)
    if text.endswith("\n"):
        return text + "\n" + line
    return text + "\n\n" + line


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
