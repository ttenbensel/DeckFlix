import argparse

from deckflix_app.cli.analyse import analyse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deckflix",
        description="DeckFlix shipboard media management",
    )

    commands = parser.add_subparsers(
        dest="command",
        required=False,
    )

    commands.add_parser(
        "home",
        help="Open the DeckFlix interactive console",
    )

    analyse_parser = commands.add_parser(
        "analyse",
        help="Analyse a shuttle drive",
    )

    analyse_parser.add_argument(
        "--library",
        required=True,
        help="Library path",
    )

    analyse_parser.add_argument(
        "--shuttle",
        required=True,
        help="Shuttle path",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        from deckflix_app.app import main as run_home

        run_home()
        return

    if args.command == "home":
        from deckflix_app.app import main as run_home

        run_home()
        return

    if args.command == "analyse":
        analyse(args.library, args.shuttle)
        return

    parser.error(f"Unknown command: {args.command}")
