from deckflix_app.cli.report import print_import_report
from deckflix_app.planner import ImportPlan


def test_report(capsys):
    plan = ImportPlan(
        total=10,
        new=2,
        upgrades=3,
        duplicates=4,
        downgrades=1,
        total_bytes=1024**3,
    )

    print_import_report(plan)

    output = capsys.readouterr().out

    assert "DECKFLIX IMPORT REPORT" in output
    assert "New" in output
    assert "Transfer" in output
