from deckflix_app.cli.main import main
import sys


def test_help(capsys):
    sys.argv = ["deckflix", "--help"]

    try:
        main()
    except SystemExit:
        pass

    output = capsys.readouterr().out

    assert "analyse" in output
