from deckflix_app.library_manager import (
    library_summary,
    calculate_health_score,
)
from deckflix_app.scanner import count_videos
from deckflix_app.shuttle import scan_shuttle
from deckflix_app.models.library_policy import LibraryPolicy
from deckflix_app.config.config import get_operational_profile_name
from deckflix_app.services.profile_presets import get_profile

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
    profile_name = get_operational_profile_name()
    profile = get_profile(profile_name)
    policy = profile.library

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

    print("Operational Profile")
    print("───────────────────")
    print(f"Name               {profile.name}")
    print(f"Description        {profile.description}")
    print()

    print("Network")
    print("───────")
    print(
        f"Downloads          "
        f"{'Enabled' if profile.network.downloads_enabled else 'Disabled'}"
    )
    print(
        f"VPN for Downloads  "
        f"{'On' if profile.network.use_vpn_for_downloads else 'Off'}"
    )
    print(
        f"VPN Required       "
        f"{'Yes' if profile.network.require_vpn_for_downloads else 'No'}"
    )

    bandwidth = profile.network.bandwidth_limit_mbps

    print(
        f"Bandwidth Limit    "
        f"{f'{bandwidth:.1f} Mbps' if bandwidth is not None else 'Unlimited'}"
    )
    print()
    print("Library Policy")
    print("──────────────")
    print(f"Profile            {policy.profile}")
    print(f"Target Resolution  {policy.preferred_resolution}")
    print(f"Preferred Codec    {policy.preferred_codec}")
    print(
        f"Maximum Movie      "
        f"{policy.maximum_movie_size_gb:.1f} GB"
    )
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
