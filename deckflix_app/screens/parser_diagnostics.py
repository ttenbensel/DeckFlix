from dataclasses import dataclass
from pathlib import Path
import re

from deckflix_app.media import MediaInfo, inspect_media
from deckflix_app.scanner import scan_videos


EPISODE_TEXT = re.compile(
    r"\bS\d{1,2}E\d{1,3}\b",
    re.IGNORECASE,
)

RELEASE_TERMS = {
    "hdtv",
    "webrip",
    "web-dl",
    "webdl",
    "bluray",
    "blu-ray",
    "brrip",
    "xvid",
    "x264",
    "x265",
    "h264",
    "h265",
    "hevc",
    "aac",
    "ddp",
    "repack",
    "proper",
}


@dataclass(slots=True)
class ParserDiagnostic:
    media: MediaInfo
    issues: list[str]

    @property
    def needs_review(self) -> bool:
        return bool(self.issues)


@dataclass(slots=True)
class ParserDiagnosticReport:
    total: int
    clean: int
    needs_review: int
    diagnostics: list[ParserDiagnostic]


def diagnose_media(media: MediaInfo, shuttle_path: Path) -> ParserDiagnostic:
    issues: list[str] = []

    title = (media.title or "").strip()
    title_lower = title.lower()

    generic_titles = {
        shuttle_path.name.lower(),
        "shuttle",
        "movies",
        "movie",
        "tv",
        "television",
        "season",
        "media",
        "",
    }

    if title_lower in generic_titles:
        issues.append("Generic or folder-derived title")

    if media.media_type == "tv":
        if media.season is None or media.episode is None:
            issues.append("TV episode number is incomplete")

        if EPISODE_TEXT.search(title):
            issues.append("Episode code remains in title")

    title_words = set(
        re.findall(r"[a-z0-9-]+", title_lower)
    )

    release_words = sorted(title_words & RELEASE_TERMS)

    if release_words:
        issues.append(
            "Release metadata remains in title: "
            + ", ".join(release_words)
        )

    if len(title) > 80:
        issues.append("Title is unusually long")

    return ParserDiagnostic(
        media=media,
        issues=issues,
    )


def build_parser_diagnostic_report(
    shuttle_path: Path,
) -> ParserDiagnosticReport:
    shuttle_path = Path(shuttle_path)
    files = scan_videos(shuttle_path)

    diagnostics = [
        diagnose_media(
            inspect_media(file),
            shuttle_path,
        )
        for file in files
    ]

    review = [
        diagnostic
        for diagnostic in diagnostics
        if diagnostic.needs_review
    ]

    return ParserDiagnosticReport(
        total=len(diagnostics),
        clean=len(diagnostics) - len(review),
        needs_review=len(review),
        diagnostics=review,
    )


def display_name(media: MediaInfo) -> str:
    if media.media_type == "tv":
        season = (
            f"{media.season:02d}"
            if media.season is not None
            else "??"
        )
        episode = (
            f"{media.episode:02d}"
            if media.episode is not None
            else "??"
        )
        return f"{media.title} S{season}E{episode}"

    if media.year:
        return f"{media.title} ({media.year})"

    return media.title


def show_parser_diagnostics(
    shuttle_path: Path,
    *,
    sample_limit: int = 40,
) -> None:
    shuttle_path = Path(shuttle_path)

    print()
    print("Parser Diagnostics")
    print("══════════════════")
    print("Read-only scan. No files will be changed.")
    print()

    if not shuttle_path.exists():
        print(f"Shuttle not found: {shuttle_path}")
        return

    print("Scanning shuttle metadata...")
    report = build_parser_diagnostic_report(shuttle_path)

    print()
    print("Summary")
    print("───────")
    print(f"Files scanned       {report.total}")
    print(f"Clean results       {report.clean}")
    print(f"Needs review        {report.needs_review}")

    if report.total:
        clean_percent = report.clean / report.total * 100
        print(f"Clean percentage    {clean_percent:.1f}%")

    print()
    print("Examples Needing Review")
    print("───────────────────────")

    if not report.diagnostics:
        print("No suspicious parser results found.")
        return

    for index, diagnostic in enumerate(
        report.diagnostics[:sample_limit],
        start=1,
    ):
        print(f"{index:2}. {display_name(diagnostic.media)}")
        print(f"    File: {diagnostic.media.path}")

        for issue in diagnostic.issues:
            print(f"    - {issue}")

        print()

    remaining = report.needs_review - sample_limit

    if remaining > 0:
        print(f"...and {remaining} more items requiring review.")

    print()
    print("Nothing has been changed.")
