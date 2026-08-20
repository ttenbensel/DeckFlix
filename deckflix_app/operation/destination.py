from pathlib import Path


def destination_for_media(
    media,
    *,
    movie_library: Path,
    tv_library: Path,
) -> Path:
    """
    Build the destination path for one media item.

    This policy is shared by import preflight and import
    execution so both phases evaluate exactly the same
    destination without depending on each other.
    """
    if media.path is None:
        raise ValueError(
            f"Media has no source path: {media.title}"
        )

    filename = media.path.name

    if media.media_type == "tv":
        content_type = getattr(
            media,
            "content_type",
            None,
        )

        if content_type == "extra":
            return (
                Path(tv_library)
                / media.title
                / "Extras"
                / filename
            )

        if content_type == "special":
            return (
                Path(tv_library)
                / media.title
                / "Specials"
                / filename
            )

        if media.season is None:
            raise ValueError(
                f"TV media has no season: {media.title}"
            )

        return (
            Path(tv_library)
            / media.title
            / f"Season {media.season:02d}"
            / filename
        )

    folder = media.title

    if media.year:
        folder = (
            f"{media.title} "
            f"({media.year})"
        )

    return (
        Path(movie_library)
        / folder
        / filename
    )
