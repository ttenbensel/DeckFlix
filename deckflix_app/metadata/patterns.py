import re


TV_PATTERN = re.compile(
    r"""
    (?:
        [Ss](?P<s1>\d{1,2})[Ee](?P<e1>\d{1,3})

        |
        [Ss](?P<s4>\d{1,2})[Xx](?P<e4>\d{1,3})

        |
        (?P<s5>\d{1,2})[Xx](?P<e5>\d{1,3})

        |
        \[(?P<s6>\d{1,2})[.](?P<e6>\d{1,3})\]

        |
        (?P<s7>\d{1,2})[Ee](?P<e7>\d{1,3})

        |
        [Ss]eason[ ._-]*(?P<s3>\d{1,2})[ ._-]*(?:[Ee]pisode[ ._-]*)?(?P<e3>\d{1,3})

        |
        [Ss]eries[ ._-]*(?P<s2>\d{1,2})[ ._-]*(?P<e2>\d{1,3})of\d+
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


TV_CONTEXT_PATTERN = re.compile(
    r"""
    (
        [Ss]eason[ ._-]*\d{1,2}
        |
        [Ss]eries[ ._-]*\d{1,2}
        |
        [Ss]\d{1,2}
    )
    """,
    re.IGNORECASE | re.VERBOSE,
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
