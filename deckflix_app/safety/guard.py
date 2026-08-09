from deckflix_app.config import DeckFlixConfig


class WriteBlockedError(RuntimeError):
    """
    Raised when DeckFlix attempts a write operation
    while operating in protected mode.
    """


def can_modify(
    config: DeckFlixConfig,
) -> bool:

    return not config.read_only


def require_write_access(
    config: DeckFlixConfig,
) -> None:

    if not can_modify(
        config
    ):

        raise WriteBlockedError(
            "DeckFlix is operating in read-only mode. "
            "No files may be modified."
        )
