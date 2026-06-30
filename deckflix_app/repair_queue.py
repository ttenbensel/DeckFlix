repair_queue = []


def add(item):
    if item not in repair_queue:
        repair_queue.append(item)


def clear():
    repair_queue.clear()


def items():
    return list(repair_queue)


def count():
    return len(repair_queue)

from pathlib import Path


def estimated_recovery():
    total = 0

    for folder in repair_queue:
        folder = Path(folder)

        if not folder.exists():
            continue

        for file in folder.rglob("*"):
            if file.is_file():
                total += file.stat().st_size

    return total / 1024**3
