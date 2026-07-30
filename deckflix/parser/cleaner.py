from __future__ import annotations

import re
from pathlib import Path


RELEASE_TERMS = re.compile(
    r"""(?ix)
    \b(
        2160p|1080p|720p|576p|480p|
        web[ ._-]?dl|web[ ._-]?rip|bluray|blu[ ._-]?ray|
        brrip|dvdrip|hdtv|hdrip|remux|
        x264|x265|h264|h265|hevc|av1|10bit|
        aac(?:\d(?:\.\d)?)?|ac3|eac3|ddp(?:\d(?:\.\d)?)?|
        dts(?:[ ._-]?hd)?|truehd|atmos|
        amzn|nf|dsnp|hmax|binge|
        repack|proper|internal|extended|unrated|complete|
        galaxyrg(?:265)?|galaxytv|rarbg|rartv|yts|tgx|evo|bone
    )\b
    """
)

BRACKETED_RELEASE = re.compile(r"[\[\{].*?[\]\}]")
MULTISPACE = re.compile(r"\s+")
SEPARATORS = re.compile(r"[._]+")
DASHES = re.compile(r"\s*-\s*")


def clean_release_name(value: str) -> str:
    value = Path(value).stem
    value = BRACKETED_RELEASE.sub(" ", value)
    value = SEPARATORS.sub(" ", value)
    value = DASHES.sub(" ", value)
    value = RELEASE_TERMS.sub(" ", value)
    value = MULTISPACE.sub(" ", value)

    return value.strip(" ._-")


def clean_title_case(value: str) -> str:
    cleaned = clean_release_name(value)

    if not cleaned:
        return cleaned

    if cleaned.isupper() or cleaned.islower():
        return cleaned.title()

    return cleaned
