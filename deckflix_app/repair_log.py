from datetime import datetime
from pathlib import Path


LOG_FILE = Path("/mnt/dest4tb/deckflix-repair.log")


def write_log(action, source, destination, status):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_FILE.open("a") as log:
        log.write(
            f"{datetime.now():%Y-%m-%d %H:%M:%S}\n"
        )
        log.write(f"Action      : {action}\n")
        log.write(f"Source      : {source}\n")
        log.write(f"Destination : {destination}\n")
        log.write(f"Status      : {status}\n")
        log.write("-" * 50 + "\n")
