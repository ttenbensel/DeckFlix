from deckflix_app.analysis import analyse_import
from deckflix_app.decision import Action
from deckflix_app.metadata.parser import parse_filename


def test_pipeline():
    library = [
        parse_filename("Avatar (2009) 720p WEB-DL x264.mkv"),
    ]

    shuttle = [
        parse_filename("Avatar (2009) 1080p BluRay HEVC.mkv"),
        parse_filename("Alien (1979) 1080p BluRay HEVC.mkv"),
    ]

    decisions, plan = analyse_import(library, shuttle)

    assert len(decisions) == 2
    assert decisions[0].action == Action.UPGRADE
    assert decisions[1].action == Action.NEW

    assert plan.upgrades == 1
    assert plan.new == 1
