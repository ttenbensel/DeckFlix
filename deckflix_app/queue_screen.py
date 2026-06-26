from deckflix_app.import_queue import queue_summary


def show_queue(queue):
    summary = queue_summary(queue)

    print()
    print("Import Queue")
    print("════════════")
    print()

    print(f"Items to review : {summary['total']}")
    print(f"Ready to import : {summary['import']}")
    print(f"Needs review    : {summary['review']}")
    print(f"Replace existing: {summary['replace']}")
    print(f"Ignore          : {summary['ignore']}")
    print()

    print("Queue")
    print("─────")

    if not queue:
        print("Queue is empty.")
        return

    for index, item in enumerate(queue[:20], start=1):
        media = item["media"]

        if media.media_type == "movie":
            name = media.title
            if media.year:
                name += f" ({media.year})"
        else:
            name = f"{media.title} S{media.season:02d}E{media.episode:02d}"

        print(f"{index:2}. {name}")
        print(f"    Status : {item['status']}")
        print(f"    Action : {item['action']}")
        print(f"    Reason : {item['reason']}")
        print()

    print("Nothing has been changed.")
