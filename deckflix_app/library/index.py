from dataclasses import dataclass, field

from deckflix_app.metadata.models import MediaMetadata


@dataclass(slots=True)
class LibraryIndex:
    movies: dict[tuple[str, int | None], MediaMetadata] = field(default_factory=dict)

    def add(self, media: MediaMetadata) -> None:
        key = (media.title.casefold(), media.year)
        self.movies[key] = media

    def find(self, media: MediaMetadata) -> MediaMetadata | None:
        key = (media.title.casefold(), media.year)
        return self.movies.get(key)
