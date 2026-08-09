from collections import defaultdict
from pathlib import Path

from deckflix_app.scanner.media import scan_media

from .models import MissingEpisodeCandidate


def scan_missing_episodes(
    library: Path,
) -> list[MissingEpisodeCandidate]:

    items = scan_media(
        library
    )


    shows = defaultdict(
        lambda: defaultdict(set)
    )


    for item in items:

        if (
            item.media_type != "tv"
            or item.content_type != "episode"
            or item.season is None
            or item.episode is None
        ):
            continue


        show_name = (
            item.title
            .casefold()
            .strip()
        )


        shows[
            show_name
        ][
            item.season
        ].add(
            item.episode
        )


    results = []


    for show, seasons in shows.items():

        for season, episodes in seasons.items():

            #
            # Avoid incomplete seasons
            #
            if len(episodes) < 3:
                continue


            first = min(
                episodes
            )

            last = max(
                episodes
            )


            for episode in range(
                first,
                last + 1,
            ):

                if episode not in episodes:

                    results.append(
                        MissingEpisodeCandidate(
                            show=show,
                            season=season,
                            episode=episode,
                            reason=(
                                "Episode gap "
                                "detected"
                            ),
                        )
                    )


    return results
