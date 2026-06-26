from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class MediaInfo:
    path: Path
    media_type: str
    title: str
    year: int | None
    season: int | None
    episode: int | None
    resolution: str
    source: str
    codec: str
    quality_score: int

    @property
    def key(self):
        if self.media_type == "tv" and self.season is not None and self.episode is not None:
            return f"{self.title.lower()} s{self.season:02d}e{self.episode:02d}"

        if self.year:
            return f"{self.title.lower()} {self.year}"

        return self.title.lower()


def detect_year(text):
    match = re.search(r"\b(19|20)\d{2}\b", text)

    if not match:
        return None

    try:
        return int(match.group(0))
    except Exception:
        return None


def detect_tv_episode(text):
    patterns = [
        r"[Ss](\d{1,2})[Ee](\d{1,2})",
        r"\b(\d{1,2})x(\d{1,2})\b",
        r"season[ ._-]*(\d{1,2}).*episode[ ._-]*(\d{1,2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return int(match.group(1)), int(match.group(2))

    return None, None


def detect_resolution(text):
    lower = text.lower()

    if "2160p" in lower or "4k" in lower:
        return "2160p"

    if "1080p" in lower:
        return "1080p"

    if "720p" in lower:
        return "720p"

    if "480p" in lower:
        return "480p"

    return "unknown"


def detect_source(text):
    lower = text.lower()

    if "bluray" in lower or "blu-ray" in lower or "brrip" in lower:
        return "BluRay"

    if "web-dl" in lower or "webdl" in lower:
        return "WEB-DL"

    if "webrip" in lower:
        return "WEBRip"

    if "hdrip" in lower:
        return "HDRip"

    if "dvdscr" in lower or "screener" in lower:
        return "Screener"

    return "unknown"


def detect_codec(text):
    lower = text.lower()

    if "x265" in lower or "h265" in lower or "hevc" in lower:
        return "HEVC"

    if "x264" in lower or "h264" in lower:
        return "H264"

    return "unknown"


def clean_title(text):
    name = text

    name = re.sub(r"\[[^\]]*\]", " ", name)
    name = re.sub(r"\([^\)]*\)", " ", name)
    name = re.sub(r"\b(19|20)\d{2}\b", " ", name)

    remove_terms = [
        "2160p", "1080p", "720p", "480p", "4k",
        "webrip", "web-dl", "webdl", "bluray", "blu-ray",
        "brrip", "hdrip", "dvdscr", "screener",
        "x264", "x265", "h264", "h265", "hevc",
        "aac", "ddp", "dd5", "5.1", "10bit",
        "yts", "tgx", "rarbg", "galaxyrg",
        "repack", "proper", "imax",
    ]

    for term in remove_terms:
        name = re.sub(rf"\b{re.escape(term)}\b", " ", name, flags=re.IGNORECASE)

    name = re.sub(r"[._-]+", " ", name)
    name = re.sub(r"[^a-zA-Z0-9 ]+", " ", name)
    name = " ".join(name.split())

    return name.strip()


def score_quality(path):
    text = str(path).lower()
    score = 0

    resolution = detect_resolution(text)
    source = detect_source(text)
    codec = detect_codec(text)

    if resolution == "2160p":
        score += 60
    elif resolution == "1080p":
        score += 40
    elif resolution == "720p":
        score += 20
    elif resolution == "480p":
        score += 5

    if source == "BluRay":
        score += 25
    elif source == "WEB-DL":
        score += 20
    elif source == "WEBRip":
        score += 15
    elif source == "HDRip":
        score += 5
    elif source == "Screener":
        score -= 20

    if codec == "HEVC":
        score += 5

    if "repack" in text or "proper" in text:
        score += 5

    if "sample" in text:
        score -= 50

    if "copy" in text:
        score -= 30

    try:
        score += min(int(Path(path).stat().st_size / 1024**3), 20)
    except Exception:
        pass

    return score


def inspect_media(path):
    path = Path(path)
    text = str(path)

    season, episode = detect_tv_episode(text)
    year = detect_year(text)
    resolution = detect_resolution(text)
    source = detect_source(text)
    codec = detect_codec(text)

    if season is not None and episode is not None:
        media_type = "tv"
        title_source = path.parent.parent.name if path.parent.parent else path.parent.name
    else:
        media_type = "movie"
        title_source = path.parent.name

    return MediaInfo(
        path=path,
        media_type=media_type,
        title=clean_title(title_source),
        year=year,
        season=season,
        episode=episode,
        resolution=resolution,
        source=source,
        codec=codec,
        quality_score=score_quality(path),
    )
