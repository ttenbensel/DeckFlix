from dataclasses import dataclass, field


@dataclass(slots=True)
class MediaRelease:
    """
    Represents one release of a movie.

    A release may contain one or more identical copies.
    """

    key: tuple

    representative: object

    copies: list = field(default_factory=list)

    confirmed_sha256: str | None = None

    @property
    def copy_count(self):
        return len(self.copies)

    @property
    def confirmed(self):
        return self.confirmed_sha256 is not None
