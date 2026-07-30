from __future__ import annotations

import unittest

from deckflix.parser.media_parser import parse_media


class MediaParserTests(unittest.TestCase):
    def test_sxe_episode(self) -> None:
        item = parse_media(
            "Succession/Season 04/Succession.S04E01.1080p.WEB-DL.mkv"
        )

        self.assertEqual(item.media_type, "tv")
        self.assertEqual(item.season, 4)
        self.assertEqual(item.episode, 1)

    def test_uppercase_x_episode(self) -> None:
        item = parse_media(
            "Adventure Time S01-S10/Adventure Time S01X01 The Wand.mp4"
        )

        self.assertEqual(item.media_type, "tv")
        self.assertEqual(item.season, 1)
        self.assertEqual(item.episode, 1)

    def test_number_x_number_episode(self) -> None:
        item = parse_media("Sneaky Pete/Sneaky.Pete.1x03.mkv")

        self.assertEqual(item.media_type, "tv")
        self.assertEqual(item.season, 1)
        self.assertEqual(item.episode, 3)

    def test_movie_with_year(self) -> None:
        item = parse_media(
            "Strange Way of Life/"
            "Strange.Way.Of.Life.2023.1080p.WEB-DL.x265.mkv"
        )

        self.assertEqual(item.media_type, "movie")
        self.assertEqual(item.year, 2023)
        self.assertEqual(item.title, "Strange Way Of Life")

    def test_season_folder_episode_filename(self) -> None:
        item = parse_media(
            "South Park/Season 02/Episode 04 Cartman Gets an Anal Probe.mkv"
        )

        self.assertEqual(item.media_type, "tv")
        self.assertEqual(item.show, "South Park")
        self.assertEqual(item.season, 2)
        self.assertEqual(item.episode, 4)


if __name__ == "__main__":
    unittest.main()
