"""Discord message deleter using a user token."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

import requests

DISCORD_API = "https://discord.com/api/v10"


@dataclass
class DeleteStats:
    deleted: int = 0
    skipped: int = 0
    failed: int = 0


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
                    "Accès refusé à ce salon. Vérifiez l'ID et vos permissions."
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

    def bulk_delete(self, channel_id: str, message_ids: list[str]) -> None:
        if len(message_ids) < 2:
            return
        payload = {"messages": message_ids}
        response = self._request(
            "POST", f"/channels/{channel_id}/messages/bulk-delete", json=payload
        )
        if response.status_code == 429:
            return
        response.raise_for_status()


def delete_channel_messages(
    client: DiscordClient,
    channel_id: str,
    *,
    own_only: bool = True,
    dry_run: bool = False,
    delay: float = 0.35,
    on_progress: Callable[..., None] | None = None,
) -> DeleteStats:
    stats = DeleteStats()
    user_id = client.user_id
    bulk_buffer: list[str] = []

    def flush_bulk() -> None:
        nonlocal bulk_buffer
        if dry_run or len(bulk_buffer) < 2:
            bulk_buffer = []
            return
        try:
            client.bulk_delete(channel_id, bulk_buffer)
            stats.deleted += len(bulk_buffer)
        except requests.HTTPError:
            for message_id in bulk_buffer:
                if client.delete_message(channel_id, message_id):
                    stats.deleted += 1
                else:
                    stats.failed += 1
                time.sleep(delay)
        bulk_buffer = []

    for message in client.iter_messages(channel_id):
        message_id = message["id"]
        author_id = message.get("author", {}).get("id")
        is_own = author_id == user_id

        if own_only and not is_own:
            stats.skipped += 1
            continue

        if dry_run:
            stats.deleted += 1
            if on_progress:
                on_progress(stats, message)
            continue

        if not own_only and not is_own:
            bulk_buffer.append(message_id)
            if len(bulk_buffer) >= 100:
                flush_bulk()
                time.sleep(1.0)
            continue

        if client.delete_message(channel_id, message_id):
            stats.deleted += 1
        else:
            stats.failed += 1

        if on_progress:
            on_progress(stats, message)

        time.sleep(delay)

    flush_bulk()
    return stats
