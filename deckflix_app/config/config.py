import json
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parents[2] / "config" / "deckflix.json"


def load_config():
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


_config = load_config()


def get_config():
    return _config


def get_libraries():
    return _config["storage"]["libraries"]


def get_enabled_libraries():
    return [
        lib for lib in get_libraries()
        if lib.get("enabled", True)
    ]


def get_movie_paths():
    return [
        Path(lib["path"]) / "movie"
        for lib in get_enabled_libraries()
    ]


def get_tv_paths():
    return [
        Path(lib["path"]) / "tv"
        for lib in get_enabled_libraries()
    ]


def get_shuttle_path():
    return Path(_config["storage"]["shuttle"])

def get_quarantine_path():
    return Path(_config["repair"]["quarantine"])

def get_operational_profile_name():
    return _config["application"].get(
        "operational_profile",
        "shipboard",
    )
