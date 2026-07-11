#!/usr/bin/env python3
"""Supprime vos messages Discord avec un dashboard en temps réel."""

from __future__ import annotations

import time
from datetime import timedelta

from rich.console import Console
from rich.live import Live
from rich.text import Text

from discord_deleter import DiscordClient, DeleteStats, collect_own_messages

# ── Configuration ──────────────────────────────────────────────────────────────
DISCORD_TOKEN = "VOTRE_TOKEN_ICI"
DELETE_DELAY = 0.35
# ──────────────────────────────────────────────────────────────────────────────

console = Console()


def format_duration(seconds: float) -> str:
    if seconds < 0 or seconds == float("inf"):
        return "--:--:--"
    return str(timedelta(seconds=int(seconds)))


def parse_channel_ids(raw: str) -> list[str]:
    ids = [part.strip() for part in raw.split(",") if part.strip()]
    if not ids:
        raise ValueError("Aucun ID de salon fourni.")
    return ids


def build_dashboard(
    stats: DeleteStats,
    elapsed: float,
    *,
    status: str = "Suppression en cours...",
    scanning_channel: str | None = None,
) -> Text:
    remaining = max(stats.total - stats.deleted - stats.failed, 0)

    if stats.deleted > 0:
        avg_per_msg = elapsed / stats.deleted
        eta_seconds = avg_per_msg * remaining
    else:
        eta_seconds = float("inf")

    lines = [
        "[bold red]deleted[/]",
        "",
        f"[cyan]time[/] : [white]{format_duration(elapsed)}[/]",
        f"[cyan]supprimé[/] : [green]{stats.deleted}[/]",
        f"[cyan]restants[/] : [yellow]{remaining}[/]",
        f"[cyan]eta[/] : [white]{format_duration(eta_seconds)}[/]",
        "",
        "[magenta]last deleted :[/]",
    ]

    if stats.last_deleted:
        for target in stats.last_deleted:
            lines.append(f"[dim]{target.content}[/] [dim](ID : {target.message_id})[/]")
    else:
        lines.append("[dim]—[/]")

    if scanning_channel:
        lines.extend(["", f"[yellow]scan du salon {scanning_channel}...[/]"])
    elif status != "Suppression en cours...":
        color = "green" if remaining == 0 else "yellow"
        lines.extend(["", f"[{color}]{status}[/]"])

    return Text.from_markup("\n".join(lines))


def prompt_channel_ids() -> list[str]:
    console.print()
    console.print("[bold cyan]Discord Message Deleter[/bold cyan]")
    console.print("[dim]Supprime uniquement vos propres messages.[/dim]\n")

    while True:
        raw = console.input(
            "[bold yellow]IDs des salons[/bold yellow] "
            "[dim](séparés par des virgules, ex: 123,456)[/dim] : "
        ).strip()

        try:
            return parse_channel_ids(raw)
        except ValueError as exc:
            console.print(f"[bold red]Erreur:[/bold red] {exc}")


def run_deletion(client: DiscordClient, channel_ids: list[str]) -> DeleteStats:
    stats = DeleteStats()
    start_time = time.monotonic()
    scanning_channel: str | None = channel_ids[0]

    with Live(console=console, refresh_per_second=8, screen=False) as live:
        def refresh(status: str = "Suppression en cours...") -> None:
            elapsed = time.monotonic() - start_time
            live.update(
                build_dashboard(
                    stats,
                    elapsed,
                    status=status,
                    scanning_channel=scanning_channel,
                )
            )

        def on_scan(channel_id: str, found: int) -> None:
            nonlocal scanning_channel
            scanning_channel = channel_id
            stats.total = found
            refresh(status="Scan des messages...")

        refresh(status="Scan des messages...")
        targets = collect_own_messages(client, channel_ids, on_scan=on_scan)
        stats.total = len(targets)
        scanning_channel = None

        if stats.total == 0:
            refresh(status="Aucun message à supprimer.")
            return stats

        for target in targets:
            if client.delete_message(target.channel_id, target.message_id):
                stats.deleted += 1
                stats.last_deleted.insert(0, target)
                stats.last_deleted = stats.last_deleted[:5]
            else:
                stats.failed += 1

            refresh()
            time.sleep(DELETE_DELAY)

        refresh(status="Terminé !")

    return stats


def main() -> int:
    if not DISCORD_TOKEN or DISCORD_TOKEN == "VOTRE_TOKEN_ICI":
        console.print(
            "[bold red]Erreur:[/bold red] Renseignez votre token dans la variable "
            "[cyan]DISCORD_TOKEN[/cyan] en haut de main.py."
        )
        return 1

    client = DiscordClient(DISCORD_TOKEN.strip())

    try:
        user = client.get_current_user()
    except Exception as exc:
        console.print(f"[bold red]Connexion impossible:[/bold red] {exc}")
        return 1

    console.print(
        f"[bold green]Connecté[/bold green] en tant que "
        f"[cyan]{user['username']}[/cyan]"
    )

    try:
        channel_ids = prompt_channel_ids()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[bold yellow]Annulé.[/bold yellow]")
        return 130

    console.print(
        f"\n[dim]{len(channel_ids)} salon(s) sélectionné(s). "
        f"Lancement de la suppression...[/dim]\n"
    )

    try:
        stats = run_deletion(client, channel_ids)
    except PermissionError as exc:
        console.print(f"\n[bold red]Erreur:[/bold red] {exc}")
        return 1
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Interrompu par l'utilisateur.[/bold yellow]")
        return 130

    console.print(
        f"\n[bold green]Fin[/bold green] — "
        f"[cyan]{stats.deleted}[/cyan] supprimé(s), "
        f"[red]{stats.failed}[/red] échec(s), "
        f"[dim]{stats.total}[/dim] au total."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
