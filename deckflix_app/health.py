from pathlib import Path
from collections import defaultdict
import re

from deckflix_app.scanner import scan_videos


RELEASE_TAGS = [
    "720p", "1080p", "2160p", "4k",
    "webrip", "web-dl", "bluray", "brrip", "hdrip", "dvdscr",
    "x264", "x265", "h264", "h265", "hevc",
    "yts", "tgx", "rarbg", "galaxyrg",
    "repack", "proper", "10bit", "5.1"
]


def clean_title(name):
    name = name.lower()
    name = re.sub(r"\[[^\]]*\]", " ", name)
    name = re.sub(r"\([^\)]*\)", " ", name)

    for tag in RELEASE_TAGS:
        name = re.sub(rf"\b{re.escape(tag)}\b", " ", name)

    name = re.sub(r"[^a-z0-9]+", " ", name)
    name = re.sub(r"\b(19|20)\d{2}\b", " ", name)

    return " ".join(name.split()).strip()


def quality_score(path):
    name = str(path).lower()
    score = 0

    if "2160p" in name or "4k" in name:
        score += 60
    elif "1080p" in name:
        score += 40
    elif "720p" in name:
        score += 20

    if "bluray" in name or "brrip" in name:
        score += 25
    elif "web-dl" in name:
        score += 20
    elif "webrip" in name:
        score += 15
    elif "hdrip" in name:
        score += 5
    elif "dvdscr" in name or "screener" in name:
        score -= 20

    if "x265" in name or "hevc" in name:
        score += 5
    if "repack" in name or "proper" in name:
        score += 5
    if "sample" in name:
        score -= 50
    if "copy" in name:
        score -= 30

    try:
        score += min(int(Path(path).stat().st_size / 1024**3), 20)
    except Exception:
        pass

    return score


def size_gb(path):
    try:
        return Path(path).stat().st_size / 1024**3
    except Exception:
        return 0


def find_junk(files):
    junk_terms = ["sample", "desktop.ini", "thumbs.db", "__macosx", ".ds_store"]
    return [f for f in files if any(term in str(f).lower() for term in junk_terms)]


def find_nested(files, movies_root):
    nested = []

    root = Path(movies_root).resolve()

    for f in files:
        try:
            rel = Path(f).resolve().relative_to(root)
            if len(rel.parts) >= 3:
                nested.append(f)
        except Exception:
            pass

    return nested


def find_duplicates(files):
    groups = defaultdict(list)

    for f in files:
        title = clean_title(Path(f).parent.name)
        if title:
            groups[title].append(f)

    return {title: paths for title, paths in groups.items() if len(paths) > 1}


def library_report(movies_path, tv_path):
    movies = scan_videos(movies_path)
    tv = scan_videos(tv_path)

    duplicates = find_duplicates(movies)
    junk = find_junk(movies)
    nested = find_nested(movies, movies_path)

    return {
        "movies": movies,
        "tv": tv,
        "duplicates": duplicates,
        "junk": junk,
        "nested": nested,
    }
