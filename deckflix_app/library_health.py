from deckflix_app.library_manager import (
    library_summary,
    calculate_health_score,
)


def show_library_health(movies_path, tv_path):
    summary = library_summary(
        movies_path,
        tv_path,
    )

    score = calculate_health_score(summary)

    print()
    print("Library Health")
    print("══════════════")
    print()

    print("Movies")
    print("──────────────")
    print(f"Total Movies          : {summary['movies_total']}")
    print(f"Duplicate Titles      : {len(summary['movie_duplicates'])}")
    print(f"Missing Years         : {len(summary['missing_year_movies'])}")
    print()

    print("TV")
    print("──────────────")
    print(f"Total Episodes        : {summary['tv_total']}")
    print(f"Duplicate Episodes    : {len(summary['tv_duplicates'])}")
    print()

    print("Quality")
    print("──────────────")

    for quality in (
        "2160p",
        "1080p",
        "720p",
        "480p",
        "unknown",
    ):
        count = summary["quality_counts"].get(
            quality,
            0,
        )

        print(f"{quality:<18}: {count}")

    print()
    print(f"Unknown Quality Files : {len(summary['unknown_quality'])}")

    print()
    print("Overall Health")
    print("──────────────")

    if score >= 90:
        status = "🟢 Excellent"
    elif score >= 75:
        status = "🟡 Good"
    elif score >= 50:
        status = "🟠 Needs Attention"
    else:
        status = "🔴 Critical"

    print(f"Score               : {score}%")
    print(f"Status              : {status}")
