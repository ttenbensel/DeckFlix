import argparse

from .analyse import analyse


def main():
    parser = argparse.ArgumentParser(prog="deckflix")

    subparsers = parser.add_subparsers(dest="command", required=True)

    analyse_parser = subparsers.add_parser(
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

    args = parser.parse_args()

    if args.command == "analyse":
        analyse(args.library, args.shuttle)


if __name__ == "__main__":
    main()
