from deckflix_app.decision import Decision, decide
from deckflix_app.library import LibraryIndex
from deckflix_app.metadata.models import MediaMetadata
from deckflix_app.planner import ImportPlan, build_import_plan


def analyse_import(
    library: list[MediaMetadata],
    incoming: list[MediaMetadata],
) -> tuple[list[Decision], ImportPlan]:

    index = LibraryIndex()

    for media in library:
        index.add(media)

    decisions: list[Decision] = []

    total_bytes = 0

    for media in incoming:
        existing = index.find(media)

        decisions.append(decide(existing, media))

        if hasattr(media, "size") and media.size:
            total_bytes += media.size

    plan = build_import_plan(
        decisions,
        total_bytes=total_bytes,
    )

    return decisions, plan
