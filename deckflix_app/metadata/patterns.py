import re

TV_PATTERN = re.compile(
    r"[Ss](\d{1,2})[Ee](\d{1,2})"
)

YEAR_PATTERN = re.compile(
    r"(19\d{2}|20\d{2})"
)

RESOLUTION_PATTERN = re.compile(
    r"(2160p|1080p|720p|480p)",
    re.IGNORECASE,
)

SOURCE_PATTERN = re.compile(
    r"(BluRay|WEB-DL|WEBRip|WEB|Remux|DVD)",
    re.IGNORECASE,
)

CODEC_PATTERN = re.compile(
    r"(HEVC|x265|x264|H264|H265)",
    re.IGNORECASE,
)
