from deckflix_app.import_queue import queue_summary
from deckflix_app.quality import quality_label


def media_name(media):
    if media.media_type == "movie":
        if media.year:
            return f"{media.title} ({media.year})"
        return media.title

    return f"{media.title} S{media.season:02d}E{media.episode:02d}"


def show_quality_comparison(item):
    if "comparison" not in item:
        return

    comparison = item["comparison"]
    incoming = comparison["incoming"]
    existing = comparison["existing"]

    print("    Existing:")
    print(f"      Quality : {quality_label(existing)}")
    print(f"      Score   : {comparison['existing_score']}")
    print()
    print("    Incoming:")
    print(f"      Quality : {quality_label(incoming)}")
    print(f"      Score   : {comparison['incoming_score']}")
    print()
    print(f"    Difference: {comparison['difference']}")


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
    print(f"Keep existing   : {summary['keep']}")
    print()

    print("Queue")
    print("─────")

    if not queue:
        print("Queue is empty.")
        return

    for index, item in enumerate(queue[:20], start=1):
        media = item["media"]

        print(f"{index:2}. {media_name(media)}")
        print(f"    Status : {item['status']}")
        print(f"    Action : {item['action']}")
        print(f"    Reason : {item['reason']}")

        show_quality_comparison(item)

        print()

    print("Nothing has been changed.")
