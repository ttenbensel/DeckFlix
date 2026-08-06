from pathlib import Path

from deckflix_app.library_manager import library_summary

from .models import MaintenanceAction


def tv_destination(
    media,
    tv_library: Path,
) -> Path:

    filename = media.path.name

    if media.content_type == "episode":
        if media.season is None:
            raise ValueError(
                f"Episode has no season: {media.title}"
            )

        return (
            Path(tv_library)
            / media.title
            / f"Season {media.season:02d}"
            / filename
        )

    if media.content_type == "special":
        return (
            Path(tv_library)
            / media.title
            / "Specials"
            / filename
        )

    if media.content_type == "extra":
        return (
            Path(tv_library)
            / media.title
            / "Extras"
            / filename
        )

    raise ValueError(
        f"Unknown TV content type: {media.content_type}"
    )


def plan_misplaced_tv(
    movies_path: Path,
    tv_path: Path,
):

    summary = library_summary(
        movies_path,
        tv_path,
    )

    actions = []

    for media in summary["misplaced_tv"]:

        if media.path is None:
            continue

        actions.append(
            MaintenanceAction(
                action="MOVE_LIBRARY",
                source=media.path,
                destination=tv_destination(
                    media,
                    tv_path,
                ),
                reason=(
                    "TV content detected inside "
                    "Movies library"
                ),
                confidence=100,
            )
        )

    return actions
