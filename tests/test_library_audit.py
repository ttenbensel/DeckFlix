from pathlib import Path

from deckflix_app.library import (
    LibraryIssue,
    LibraryRoot,
    audit_libraries,
)


def roots(
    tmp_path: Path,
):
    primary_movies = (
        tmp_path
        / "library1"
        / "movie"
    )

    legacy_tv = (
        tmp_path
        / "library1"
        / "tv"
    )

    legacy_movies = (
        tmp_path
        / "library2"
        / "movie"
    )

    primary_tv = (
        tmp_path
        / "library2"
        / "tv"
    )

    for path in (
        primary_movies,
        legacy_tv,
        legacy_movies,
        primary_tv,
    ):
        path.mkdir(
            parents=True
        )

    specs = [
        LibraryRoot(
            name="Primary Movies",
            path=primary_movies,
            expected_media_type="movie",
            primary=True,
        ),
        LibraryRoot(
            name="Legacy TV",
            path=legacy_tv,
            expected_media_type="tv",
            primary=False,
        ),
        LibraryRoot(
            name="Legacy Movies",
            path=legacy_movies,
            expected_media_type="movie",
            primary=False,
        ),
        LibraryRoot(
            name="Primary TV",
            path=primary_tv,
            expected_media_type="tv",
            primary=True,
        ),
    ]

    return (
        specs,
        primary_movies,
        legacy_tv,
        legacy_movies,
        primary_tv,
    )


def find_entry(
    audit,
    filename: str,
):
    return next(
        entry
        for entry in audit.entries
        if entry.path.name == filename
    )


def test_correct_primary_media_is_ok(
    tmp_path: Path,
):
    (
        specs,
        movies,
        _,
        _,
        tv,
    ) = roots(tmp_path)

    (
        movies
        / "Alien (1979)"
    ).mkdir()

    (
        movies
        / "Alien (1979)"
        / "Alien.1979.1080p.BluRay.mkv"
    ).write_bytes(b"movie")

    (
        tv
        / "Barry"
        / "Season 01"
    ).mkdir(parents=True)

    (
        tv
        / "Barry"
        / "Season 01"
        / "Barry.S01E01.mkv"
    ).write_bytes(b"episode")

    audit = audit_libraries(
        specs
    )

    assert len(audit.entries) == 2

    assert all(
        entry.ok
        for entry in audit.entries
    )


def test_tv_in_movie_root_is_misplaced(
    tmp_path: Path,
):
    (
        specs,
        movies,
        _,
        _,
        _,
    ) = roots(tmp_path)

    path = (
        movies
        / "South Park"
        / "South.Park.S24E00.mkv"
    )

    path.parent.mkdir()
    path.write_bytes(b"tv")

    audit = audit_libraries(
        specs
    )

    entry = find_entry(
        audit,
        path.name,
    )

    assert (
        LibraryIssue.MISPLACED
        in entry.issues
    )


def test_movie_in_tv_root_is_misplaced(
    tmp_path: Path,
):
    (
        specs,
        _,
        _,
        _,
        tv,
    ) = roots(tmp_path)

    path = (
        tv
        / "Wrong Folder"
        / "Doctor.Sleep.2019.1080p.mkv"
    )

    path.parent.mkdir()
    path.write_bytes(b"movie")

    audit = audit_libraries(
        specs
    )

    entry = find_entry(
        audit,
        path.name,
    )

    assert (
        LibraryIssue.MISPLACED
        in entry.issues
    )


def test_correct_media_in_legacy_root_is_legacy(
    tmp_path: Path,
):
    (
        specs,
        _,
        _,
        legacy_movies,
        _,
    ) = roots(tmp_path)

    path = (
        legacy_movies
        / "Dune (2021)"
        / "Dune.2021.1080p.mkv"
    )

    path.parent.mkdir()
    path.write_bytes(b"movie")

    audit = audit_libraries(
        specs
    )

    entry = find_entry(
        audit,
        path.name,
    )

    assert (
        LibraryIssue.LEGACY_LOCATION
        in entry.issues
    )

    assert (
        LibraryIssue.MISPLACED
        not in entry.issues
    )


def test_duplicate_movie_is_detected_across_roots(
    tmp_path: Path,
):
    (
        specs,
        primary_movies,
        _,
        legacy_movies,
        _,
    ) = roots(tmp_path)

    first = (
        primary_movies
        / "Idiocracy (2006)"
        / "Idiocracy.2006.mkv"
    )

    second = (
        legacy_movies
        / "Idiocracy (2006)"
        / "Idiocracy.2006.1080p.mp4"
    )

    first.parent.mkdir()
    second.parent.mkdir()

    first.write_bytes(b"one")
    second.write_bytes(b"two")

    audit = audit_libraries(
        specs
    )

    assert len(
        audit.duplicate_groups
    ) == 1

    entries = [
        find_entry(
            audit,
            first.name,
        ),
        find_entry(
            audit,
            second.name,
        ),
    ]

    assert all(
        LibraryIssue.DUPLICATE_CANDIDATE
        in entry.issues
        for entry in entries
    )


def test_deep_movie_nesting_is_suspicious(
    tmp_path: Path,
):
    (
        specs,
        movies,
        _,
        _,
        _,
    ) = roots(tmp_path)

    path = (
        movies
        / "Batman"
        / "Other Movie"
        / "Other.Movie.2021.mkv"
    )

    path.parent.mkdir(
        parents=True
    )

    path.write_bytes(b"movie")

    audit = audit_libraries(
        specs
    )

    entry = find_entry(
        audit,
        path.name,
    )

    assert (
        LibraryIssue.STRUCTURE_REVIEW
        in entry.issues
    )


def test_summary_counts_issue_types(
    tmp_path: Path,
):
    (
        specs,
        movies,
        _,
        legacy_movies,
        tv,
    ) = roots(tmp_path)

    movie = (
        movies
        / "Alien (1979)"
        / "Alien.1979.mkv"
    )

    movie.parent.mkdir()
    movie.write_bytes(b"a")

    legacy = (
        legacy_movies
        / "Dune (2021)"
        / "Dune.2021.mkv"
    )

    legacy.parent.mkdir()
    legacy.write_bytes(b"d")

    episode = (
        tv
        / "Barry"
        / "Season 01"
        / "Barry.S01E01.mkv"
    )

    episode.parent.mkdir(
        parents=True
    )

    episode.write_bytes(b"b")

    audit = audit_libraries(
        specs
    )

    summary = audit.summary

    assert summary.total_videos == 3
    assert summary.movie_videos == 2
    assert summary.tv_videos == 1
    assert summary.legacy == 1
    assert summary.misplaced == 0


def test_legacy_part_series_is_not_misclassified_as_movies(
    tmp_path: Path,
):
    (
        specs,
        _,
        _,
        legacy_movies,
        _,
    ) = roots(tmp_path)

    show = (
        legacy_movies
        / "Band of Brothers"
    )

    show.mkdir()

    for number in range(
        1,
        4,
    ):
        (
            show
            / (
                "Band of Brothers "
                f"- Part {number:02d}.avi"
            )
        ).touch()

    audit = audit_libraries(
        specs
    )

    entries = [
        entry
        for entry in audit.entries
        if (
            "Band of Brothers"
            in str(entry.path)
        )
    ]

    assert len(entries) == 3

    assert all(
        entry.media.media_type == "tv"
        for entry in entries
    )

    assert all(
        LibraryIssue.MISPLACED
        in entry.issues
        for entry in entries
    )


def test_tv_extra_is_not_misplaced(
    tmp_path: Path,
):
    (
        specs,
        _,
        _,
        _,
        tv,
    ) = roots(tmp_path)

    path = (
        tv
        / "Breaking Bad"
        / "Extras"
        / "Behind The Scenes.mkv"
    )

    path.parent.mkdir(
        parents=True
    )

    path.touch()

    audit = audit_libraries(
        specs
    )

    entry = find_entry(
        audit,
        path.name,
    )

    assert (
        LibraryIssue.MISPLACED
        not in entry.issues
    )


def test_tv_sxxx_special_is_not_misplaced(
    tmp_path: Path,
):
    (
        specs,
        _,
        _,
        _,
        tv,
    ) = roots(tmp_path)

    path = (
        tv
        / "Adventure Time"
        / "Season 06"
        / (
            "Adventure Time S06X01 "
            "Special.mp4"
        )
    )

    path.parent.mkdir(
        parents=True
    )

    path.touch()

    audit = audit_libraries(
        specs
    )

    entry = find_entry(
        audit,
        path.name,
    )

    assert (
        LibraryIssue.MISPLACED
        not in entry.issues
    )


def test_real_movie_in_tv_root_remains_misplaced(
    tmp_path: Path,
):
    (
        specs,
        _,
        _,
        _,
        tv,
    ) = roots(tmp_path)

    path = (
        tv
        / "Wrong Show"
        / "Doctor.Sleep.2019.1080p.mkv"
    )

    path.parent.mkdir()
    path.touch()

    audit = audit_libraries(
        specs
    )

    entry = find_entry(
        audit,
        path.name,
    )

    assert (
        LibraryIssue.MISPLACED
        in entry.issues
    )


def test_movie_collection_is_not_structure_review(
    tmp_path: Path,
):
    (
        specs,
        movies,
        _,
        _,
        _,
    ) = roots(tmp_path)

    path = (
        movies
        / "Harry Potter Movies"
        / "Harry Potter (2001)"
        / "Harry.Potter.2001.mkv"
    )

    path.parent.mkdir(
        parents=True
    )

    path.touch()

    audit = audit_libraries(
        specs
    )

    entry = find_entry(
        audit,
        path.name,
    )

    assert (
        LibraryIssue.STRUCTURE_REVIEW
        not in entry.issues
    )


def test_weak_movie_identity_does_not_form_duplicate_group(
    tmp_path: Path,
):
    (
        specs,
        movies,
        _,
        legacy_movies,
        _,
    ) = roots(tmp_path)

    first = (
        movies
        / "Unknown"
        / "Unknown.mkv"
    )

    second = (
        legacy_movies
        / "Unknown"
        / "Unknown.mp4"
    )

    first.parent.mkdir()
    second.parent.mkdir()

    first.touch()
    second.touch()

    audit = audit_libraries(
        specs
    )

    assert (
        len(
            audit.duplicate_groups
        )
        == 0
    )
