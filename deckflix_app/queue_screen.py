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

def show_policy_recommendation(item):
    """
    Display the policy recommendation for an existing media item.
    """

    recommendation = item.get("policy")

    if recommendation is None:
        return

    labels = {
        "KEEP_EXISTING": "Keep Current Copy",
        "UPGRADE": "Upgrade Library Copy",
        "REPLACE_EFFICIENTLY": "Replace with Efficient Version",
        "REVIEW": "Review Manually",
    }

    print()
    print("    Policy Recommendation:")
    print(
        "      Action  : "
        f"{labels.get(recommendation.action, recommendation.action)}"
    )
    print(f"      Confidence: {recommendation.confidence}%")

    print("      Why:")

    for reason in recommendation.reasons:
        print(f"        • {reason}")

    if recommendation.storage_change_bytes:
        sign = "+" if recommendation.storage_change_bytes > 0 else ""

        print(
            "      Storage : "
            f"{sign}{recommendation.storage_change_gb:.2f} GB"
        )

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
        show_policy_recommendation(item)

        print()

    print("Nothing has been changed.")
