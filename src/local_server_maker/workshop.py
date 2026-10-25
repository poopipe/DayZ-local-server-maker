import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

from local_server_maker.ask import Prompt, ask_secret, pick_index
from local_server_maker.consts import QUERY_URL
from local_server_maker.steam_web_api_key import (
    get_saved_steam_web_api_key,
    is_steam_web_api_key,
    save_steam_web_api_key,
)


class WorkshopItem(TypedDict):
    id: str
    title: str


WorkshopSearch = Callable[[str, str], list[WorkshopItem]]


def bind_workshop_search(directory: Path, prompt: Prompt) -> WorkshopSearch:
    """Return a Workshop search that asks for the API key on its first use.

    Later searches from the same function reuse that key. The key file is
    stored in directory.
    """
    saved: list[str] = []

    def search(app_id: str, text: str) -> list[WorkshopItem]:
        """Search one app by title, asking for the API key only the first time."""
        if not saved:
            saved.append(ask_steam_web_api_key(directory, prompt))
        return fetch_workshop_items(saved[0], app_id, text)

    return search


def ask_steam_web_api_key(directory: Path, prompt: Prompt) -> str:
    """Return the saved key, or ask for one and save it in directory.

    A missing key is created on Steam's key page. The domain name there is
    only a label. This tool uses localhost.
    """
    saved = get_saved_steam_web_api_key(directory)
    if saved is not None:
        print("Using the saved Steam Web API key.")
        return saved
    print("Create a Steam Web API key at https://steamcommunity.com/dev/apikey")
    print("Domain name: localhost")
    while True:
        answer = ask_secret(prompt, "Steam Web API key")
        if is_steam_web_api_key(answer):
            save_steam_web_api_key(directory, answer)
            return answer
        print("Steam Web API key must be 32 hex characters")


def ask_pick(prompt: Prompt, items: list[WorkshopItem]) -> WorkshopItem:
    """Keep asking until the answer is one number or one title from items."""
    while True:
        choice = prompt("Pick a number or a name from the list: ").strip()
        item, message = pick_workshop_item(items, choice)
        if item is None:
            print(message)
            continue
        return item


def fetch_workshop_items(
    api_key: str, app_id: str, search_text: str
) -> list[WorkshopItem]:
    """Ask Steam for Workshop items whose title matches search_text.

    The request address contains the API key, so it is not written out.
    A rejected key and a failed request are both reported as errors.
    """
    query = urllib.parse.urlencode(query_fields(api_key, app_id, search_text))
    request = urllib.request.Request(f"{QUERY_URL}?{query}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            raise ValueError("Workshop search rejected the Steam Web API key") from None
        raise ValueError(f"Workshop search failed ({error.code})") from None
    except urllib.error.URLError:
        raise ValueError("Workshop search failed") from None
    return parse_workshop_items(payload)


def query_fields(api_key: str, app_id: str, search_text: str) -> dict[str, str]:
    """Build the QueryFiles fields for a title search.

    The empty tag and flag fields are sent because Steam expects them.
    At most 10 matches are requested, with details so each match has a title.
    """
    return {
        "key": api_key,
        "query_type": "12",
        "page": "1",
        "cursor": "*",
        "numperpage": "10",
        "creator_appid": app_id,
        "appid": app_id,
        "requiredtags": "",
        "excludedtags": "",
        "match_all_tags": "0",
        "required_flags": "",
        "omitted_flags": "",
        "search_text": search_text,
        "filetype": "0",
        "child_publishedfileid": "0",
        "days": "0",
        "include_recent_votes_only": "0",
        "cache_max_age_seconds": "0",
        "totalonly": "0",
        "ids_only": "0",
        "return_vote_data": "0",
        "return_tags": "0",
        "return_kv_tags": "0",
        "return_previews": "0",
        "return_children": "0",
        "return_short_description": "0",
        "return_for_sale_data": "0",
        "return_metadata": "0",
        "return_playtime_stats": "0",
        "language": "0",
        "return_details": "1",
    }


def parse_workshop_items(payload: object) -> list[WorkshopItem]:
    """Read ids and titles from a QueryFiles response.

    The response must contain a list of published file details. An entry
    without a numeric id and a title is left out.
    """
    if not isinstance(payload, dict):
        raise ValueError("Workshop search returned an unexpected response")
    response = payload.get("response")
    if not isinstance(response, dict):
        raise ValueError("Workshop search returned an unexpected response")
    details = response.get("publishedfiledetails", [])
    if not isinstance(details, list):
        raise ValueError("Workshop search returned an unexpected response")
    items: list[WorkshopItem] = []
    for detail in details:
        item = workshop_item(detail)
        if item is not None:
            items.append(item)
    return items


def pick_workshop_item(
    items: list[WorkshopItem], choice: str
) -> tuple[WorkshopItem | None, str]:
    """Return the item whose title is choice, or no item and the reason."""
    index, message = pick_index([item["title"] for item in items], choice)
    if index is None:
        return None, message
    return items[index], ""


def workshop_item(detail: object) -> WorkshopItem | None:
    """Turn one published file detail into an id and a title.

    Steam may send the id as text or as a number. An entry without a numeric
    id and a title is skipped.
    """
    if not isinstance(detail, dict):
        return None
    file_id = detail.get("publishedfileid")
    title = detail.get("title")
    if isinstance(file_id, int) and not isinstance(file_id, bool):
        file_id = str(file_id)
    if not isinstance(file_id, str) or not isinstance(title, str):
        return None
    if not file_id.isdigit() or title == "":
        return None
    return {"id": file_id, "title": title}
