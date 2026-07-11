#!/usr/bin/env python3
"""Supprime les messages d'un salon Discord (DM ou serveur) via un token utilisateur."""

from __future__ import annotations

import argparse
import os
import sys

from discord_deleter import DiscordClient, delete_channel_messages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Supprime les messages d'un salon Discord (messages privés ou serveur) "
            "en utilisant un token utilisateur."
        )
    )
    parser.add_argument(
        "channel_id",
        help="ID du salon Discord à nettoyer",
    )
    parser.add_argument(
        "-t",
        "--token",
        default=os.environ.get("DISCORD_TOKEN"),
        help="Token utilisateur Discord (ou variable DISCORD_TOKEN)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simuler sans supprimer réellement",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.35,
        help="Délai entre chaque suppression en secondes (défaut: 0.35)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.token:
        print(
            "Erreur: fournissez un token via --token ou la variable d'environnement DISCORD_TOKEN.",
            file=sys.stderr,
        )
        return 1

    client = DiscordClient(args.token.strip())

    try:
        user = client.get_current_user()
        channel = client.get_channel(args.channel_id)
    except Exception as exc:
        print(f"Erreur de connexion: {exc}", file=sys.stderr)
        return 1

    channel_type = channel.get("type")  # 0 = serveur, 1 = DM, 3 = groupe DM
    type_labels = {0: "serveur", 1: "DM", 3: "groupe DM"}
    channel_label = type_labels.get(channel_type, f"type {channel_type}")

    recipient = channel.get("recipients")
    channel_name = channel.get("name") or (
        recipient[0].get("username") if recipient else args.channel_id
    )

    print(f"Connecté en tant que: {user['username']}#{user.get('discriminator', '0')}")
    print(f"Salon: {channel_name} ({channel_label}) — ID {args.channel_id}")

    if args.dry_run:
        print("Mode simulation activé — aucun message ne sera supprimé.")

    print("Mode: suppression de vos messages uniquement\n")

    def on_progress(stats, message):
        author = message.get("author", {}).get("username", "?")
        content = (message.get("content") or "[sans texte]")[:60]
        action = "À supprimer" if args.dry_run else "Supprimé"
        print(f"[{stats.deleted}] {action}: @{author} — {content}")

    try:
        stats = delete_channel_messages(
            client,
            args.channel_id,
            dry_run=args.dry_run,
            delay=args.delay,
            on_progress=on_progress,
        )
    except PermissionError as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur.")
        return 130

    print(
        f"\nTerminé — supprimés: {stats.deleted}, ignorés: {stats.skipped}, échecs: {stats.failed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
