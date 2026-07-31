from deckflix_app.decision import Action, Decision
from deckflix_app.planner import build_import_plan


def test_import_plan():
    decisions = [
        Decision(Action.NEW, "", 0, 100),
        Decision(Action.NEW, "", 0, 100),
        Decision(Action.UPGRADE, "", 50, 100),
        Decision(Action.DUPLICATE, "", 100, 100),
        Decision(Action.DOWNGRADE, "", 300, 100),
    ]

    plan = build_import_plan(decisions)

    assert plan.total == 5
    assert plan.new == 2
    assert plan.upgrades == 1
    assert plan.duplicates == 1
    assert plan.downgrades == 1
