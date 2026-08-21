from dataclasses import dataclass, field

from deckflix_app.metadata.models import MediaMetadata


MediaKey = tuple[
    str | int | None,
    ...,
]


def _normalized_title(
    value: str,
) -> str:
    return " ".join(
        value.casefold().split()
    )


def _special_path_identity(
    media: MediaMetadata,
) -> str | None:
    """
    Return a conservative identity for an unnumbered TV special.

    Multiple specials from the same series deliberately use their
    exact normalized filename stem as the discriminator.

    This solves the unsafe case where:

        Walker University

    and:

        Season 9 Preview Special

    previously both collapsed to:

        ("tv", "the walking dead", None, None)

    We intentionally do not fuzzy-match special filenames. If the
    same special arrives under a substantially different filename,
    failing closed as NEW is safer than replacing unrelated media.
    """
    if media.path is None:
        return None

    stem = " ".join(
        media.path.stem
        .casefold()
        .split()
    )

    if not stem:
        return None

    return stem


def _is_unnumbered_special(
    media: MediaMetadata,
) -> bool:
    return (
        media.media_type == "tv"
        and media.content_type == "special"
        and (
            media.season is None
            or media.episode is None
        )
    )


def media_key(
    media: MediaMetadata,
) -> MediaKey:
    title = _normalized_title(
        media.title
    )

    if _is_unnumbered_special(
        media
    ):
        special_identity = (
            _special_path_identity(
                media
            )
        )

        return (
            "tv-special",
            title,
            special_identity,
        )

    if media.media_type == "tv":
        return (
            "tv",
            title,
            media.season,
            media.episode,
        )

    return (
        "movie",
        title,
        media.year,
    )


@dataclass(slots=True)
class LibraryIndex:
    items: dict[
        MediaKey,
        MediaMetadata,
    ] = field(
        default_factory=dict
    )

    def add(
        self,
        media: MediaMetadata,
    ) -> None:
        # An unnumbered special without a path does not have enough
        # information for a strong library identity.
        #
        # Do not index it under a weak series-only key.
        if (
            _is_unnumbered_special(media)
            and _special_path_identity(media)
            is None
        ):
            return

        self.items[
            media_key(media)
        ] = media

    def find(
        self,
        media: MediaMetadata,
    ) -> MediaMetadata | None:
        # Match the same fail-closed rule used by add().
        if (
            _is_unnumbered_special(media)
            and _special_path_identity(media)
            is None
        ):
            return None

        return self.items.get(
            media_key(media)
        )
