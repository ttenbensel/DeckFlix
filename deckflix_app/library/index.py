from dataclasses import dataclass, field

from deckflix_app.metadata.models import MediaMetadata


MediaKey = (
    tuple[str, str, int | None]
    | tuple[str, str, int | None, int | None]
)


def media_key(media: MediaMetadata) -> MediaKey:
    title = media.title.casefold().strip()

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
    items: dict[MediaKey, MediaMetadata] = field(
        default_factory=dict
    )

    def add(self, media: MediaMetadata) -> None:
        self.items[media_key(media)] = media

    def find(
        self,
        media: MediaMetadata,
    ) -> MediaMetadata | None:
        return self.items.get(media_key(media))
