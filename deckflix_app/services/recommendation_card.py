from deckflix_app.services.policy_engine import PolicyRecommendation


ACTION_LABELS = {
    "KEEP_EXISTING": "Keep Current Copy",
    "UPGRADE": "Upgrade Library Copy",
    "REPLACE_EFFICIENTLY": "Replace with Efficient Version",
    "REVIEW": "Review Manually",
}


def confidence_stars(confidence: int) -> str:
    """
    Convert a confidence score into a five-star rating.
    """

    stars = max(1, min(5, round(confidence / 20)))
    return "★" * stars + "☆" * (5 - stars)


def show_recommendation_card(title: str, recommendation: PolicyRecommendation):
    """
    Display a user-friendly recommendation.
    """

    print()
    print("══════════════════════════════════════")
    print(title)
    print()

    print("Recommendation")
    print("──────────────")

    print(
        ACTION_LABELS.get(
            recommendation.action,
            recommendation.action,
        )
    )

    print()
    print("Confidence")
    print("──────────")

    print(confidence_stars(recommendation.confidence))

    print()
    print("Why")
    print("───")

    for reason in recommendation.reasons:
        print(f"✓ {reason}")

    print()

    if recommendation.storage_change_bytes:
        sign = "+" if recommendation.storage_change_bytes > 0 else ""

        print("Storage Impact")
        print("──────────────")

        print(
            f"{sign}"
            f"{recommendation.storage_change_gb:.2f} GB"
        )

    print()
    print("══════════════════════════════════════")
