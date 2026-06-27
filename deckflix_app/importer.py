from pathlib import Path
import shutil


def target_path_for_media(media, movies_path, tv_path):
    """
    Decide where a media item should be copied.

    Nothing is copied here.
    """

    if media.media_type == "tv":
        show_folder = Path(tv_path) / media.title
        season_folder = show_folder / f"Season {media.season:02d}"
        return season_folder / media.path.name

    movie_folder_name = media.title

    if media.year:
        movie_folder_name = f"{media.title} ({media.year})"

    movie_folder = Path(movies_path) / movie_folder_name
    return movie_folder / media.path.name


def build_import_plan(queue, movies_path, tv_path):
    """
    Build a safe copy plan from approved import queue items.

    Only IMPORT actions are included.
    Nothing is copied here.
    """

    plan = []

    for item in queue:
        if item["action"] != "IMPORT":
            continue

        media = item["media"]
        target = target_path_for_media(
            media,
            movies_path,
            tv_path,
        )

        if target.exists():
            status = "SKIP_EXISTS"
        else:
            status = "READY"

        plan.append({
            "media": media,
            "source": media.path,
            "target": target,
            "status": status,
        })

    return plan


def print_import_plan(plan):
    print()
    print("Safe Import Plan")
    print("════════════════")
    print("Dry-run preview. Nothing has been copied.")
    print()

    if not plan:
        print("No approved import items.")
        return

    for index, item in enumerate(plan, start=1):
        print(f"{index}.")
        print(f"   Source: {item['source']}")
        print(f"   Target: {item['target']}")
        print(f"   Status: {item['status']}")
        print()

    print("Nothing has been changed.")


def copy_one_item(plan_item):
    """
    Copy one approved item.

    Never overwrite an existing destination file.
    """

    source = Path(plan_item["source"])
    target = Path(plan_item["target"])

    if target.exists():
        return {
            "source": source,
            "target": target,
            "status": "SKIPPED_EXISTS",
        }

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        source,
        target,
    )

    return {
        "source": source,
        "target": target,
        "status": "COPIED",
    }
