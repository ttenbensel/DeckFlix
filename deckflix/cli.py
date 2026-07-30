from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from deckflix.parser.media_parser import parse_media
from deckflix.scanner.inventory import save_inventory, scan_path


CONFIG_PATH = Path("/opt/deckflix/config/local.json")


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def command_parse(args: argparse.Namespace) -> int:
    result = parse_media(args.path)
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def command_scan_shuttle(_: argparse.Namespace) -> int:
    config = load_config()
    shuttle = Path(config["shuttle"])
    report_directory = Path(config["report_directory"])

    if not shuttle.exists():
        print(f"ERROR: Shuttle path does not exist: {shuttle}", file=sys.stderr)
        return 1

    if not shuttle.is_mount():
        print(f"ERROR: Shuttle is not mounted: {shuttle}", file=sys.stderr)
        return 1

    print("=" * 60)
    print("DECKFLIX V0.2 SHUTTLE SCAN")
    print("=" * 60)
    print(f"Path: {shuttle}")
    print("Mode: READ ONLY")
    print()

    payload = scan_path(shuttle)
    output = save_inventory(
        payload,
        report_directory,
        "shuttle-inventory-v0.2",
    )

    print()
    print("SCAN COMPLETE")
    print("-" * 60)
    print(f"Files: {payload['total_video_files']}")

    for category, count in sorted(payload["counts"].items()):
        print(f"{category:18} {count}")

    print()
    print(f"Report: {output}")
    print("No media files were changed.")

    return 0


def command_status(_: argparse.Namespace) -> int:
    config = load_config()
    shuttle = Path(config["shuttle"])

    print("DeckFlix 0.2.0")
    print(f"Shuttle:  {shuttle}")
    print(f"Exists:   {'yes' if shuttle.exists() else 'no'}")
    print(f"Mounted:  {'yes' if shuttle.is_mount() else 'no'}")
    print("Mode:     READ ONLY")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deckflix")
    subcommands = parser.add_subparsers(dest="command", required=True)

    status = subcommands.add_parser("status")
    status.set_defaults(function=command_status)

    scan = subcommands.add_parser("scan-shuttle")
    scan.set_defaults(function=command_scan_shuttle)

    parse = subcommands.add_parser("parse")
    parse.add_argument("path")
    parse.set_defaults(function=command_parse)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.function(args)


if __name__ == "__main__":
    raise SystemExit(main())
