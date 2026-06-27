from deckflix_app.library_manager import (
    library_summary,
    calculate_health_score,
)
from deckflix_app.scanner import count_videos
from deckflix_app.shuttle import scan_shuttle


def health_status(score):
    if score >= 90:
        return "🟢 Excellent"
    if score >= 75:
        return "🟡 Good"
    if score >= 50:
        return "🟠 Needs Attention"
    return "🔴 Critical"


def show_dashboard(movies_path, tv_path, shuttle_path):
    summary = library_summary(
        movies_path,
        tv_path,
    )

    score = calculate_health_score(summary)
    shuttle = scan_shuttle(shuttle_path)

    print()
    print("Bridge Dashboard")
    print("════════════════")
    print()

    print("Library")
    print("───────")
    print(f"Health             {score}% {health_status(score)}")
    print(f"Movies             {summary['movies_total']}")
    print(f"TV Episodes        {summary['tv_total']}")
    print()
    print("Top Issues")
    print("──────────")
    print(f"Duplicate Titles   {len(summary['movie_duplicates'])}")
    print(f"Unknown Quality    {len(summary['unknown_quality'])}")
    print(f"Missing Years      {len(summary['missing_year_movies'])}")
    print()

    print("Shuttle")
    print("───────")
    if shuttle["connected"]:
        print("Status             Connected")
        print(f"Path               {shuttle['path']}")
        print(f"Video Files         {len(shuttle['files'])}")
    else:
        print("Status             Not Found")

    print()
    print("System")
    print("──────")
    print("Jellyfin           Not connected yet")
    print()
    print("Nothing has been changed.")
