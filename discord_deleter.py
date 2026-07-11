"""Discord message deleter using a user token."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

import requests

DISCORD_API = "https://discord.com/api/v10"


@dataclass
class MessageTarget:
    channel_id: str
    message_id: str
    content: str


@dataclass
class DeleteStats:
    deleted: int = 0
    failed: int = 0
    total: int = 0
    last_deleted: list[MessageTarget] = field(default_factory=list)


class DiscordClient:
    def __init__(self, token: str) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": token,
                "Content-Type": "application/json",
                "User-Agent": "DiscordDeleter/1.0",
            }
        )
        self._user_id: str | None = None

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{DISCORD_API}{path}"
        while True:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 429:
                retry_after = float(response.json().get("retry_after", 1))
                time.sleep(retry_after)
                continue
            return response

    def get_current_user(self) -> dict[str, Any]:
        response = self._request("GET", "/users/@me")
        response.raise_for_status()
        return response.json()

    @property
    def user_id(self) -> str:
        if self._user_id is None:
            self._user_id = self.get_current_user()["id"]
        return self._user_id

    def get_channel(self, channel_id: str) -> dict[str, Any]:
        response = self._request("GET", f"/channels/{channel_id}")
        response.raise_for_status()
        return response.json()

    def iter_messages(self, channel_id: str):
        before: str | None = None
        while True:
            params: dict[str, Any] = {"limit": 100}
            if before:
                params["before"] = before

            response = self._request("GET", f"/channels/{channel_id}/messages", params=params)
            if response.status_code == 403:
                raise PermissionError(
                    f"Accès refusé au salon {channel_id}. Vérifiez l'ID et vos permissions."
                )
            response.raise_for_status()

            messages = response.json()
            if not messages:
                break

            for message in messages:
                yield message

            before = messages[-1]["id"]

    def delete_message(self, channel_id: str, message_id: str) -> bool:
        response = self._request("DELETE", f"/channels/{channel_id}/messages/{message_id}")
        if response.status_code in (200, 204):
            return True
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return False


def collect_own_messages(
    client: DiscordClient,
    channel_ids: list[str],
    on_scan: Callable[[str, int], None] | None = None,
) -> list[MessageTarget]:
    user_id = client.user_id
    targets: list[MessageTarget] = []

    for channel_id in channel_ids:
        if on_scan:
            on_scan(channel_id, len(targets))

        for message in client.iter_messages(channel_id):
            if message.get("author", {}).get("id") != user_id:
                continue

            content = message.get("content") or "[sans texte]"
            if message.get("attachments"):
                content = f"{content} [fichier]" if content != "[sans texte]" else "[fichier]"

            targets.append(
                MessageTarget(
                    channel_id=channel_id,
                    message_id=message["id"],
                    content=content[:80],
                )
            )

            if on_scan:
                on_scan(channel_id, len(targets))

    return targets
