import shutil

from deckflix_app.scanner import count_videos


def show_dashboard(movies_path, tv_path, shuttle_path):

    movies = count_videos(movies_path)
    tv = count_videos(tv_path)
    shuttle = count_videos(shuttle_path)

    usage = shutil.disk_usage(movies_path)

    used_tb = usage.used / 1024**4
    total_tb = usage.total / 1024**4
    free_tb = usage.free / 1024**4

    print()
    print("Bridge Dashboard")
    print("────────────────")
    print("Vessel Mode        ⚓ Harbour")
    print("Low Impact         Enabled")
    print()
    print(f"Movies             {movies}")
    print(f"TV Episodes        {tv}")
    print(f"Shuttle Videos     {shuttle}")
    print()
    print(f"Media Storage      {used_tb:.2f} TB / {total_tb:.2f} TB")
    print(f"Free Space         {free_tb:.2f} TB")
    print()
    print(f"Movies Path        {movies_path}")
    print(f"TV Path            {tv_path}")
    print(f"Shuttle Path       {shuttle_path}")
    print()
    print("Status             Ready")
    print("Nothing has been changed.")
