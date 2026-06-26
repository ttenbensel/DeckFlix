#!/usr/bin/env bash
set -e

cd /opt
rm -rf deckflix
mkdir -p deckflix
cd deckflix

cat > deckflix.py <<'EOF'
#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import re

MOVIES = Path("/mnt/dest4tb/movie")
TV = Path("/mnt/dest4tb/tv")
SHUTTLE = Path("/mnt/source2tb")
LOGS = Path("/mnt/dest4tb/deckflix-logs")

VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".mov", ".wmv", ".m4v"}

def logo():
    print("""
═══════════════════════════════════════════════
                 DECKFLIX
        Shipboard Media Management
═══════════════════════════════════════════════
Version 0.1.0
""")

def scan_videos(path):
    if not path.exists():
        return []
    return [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTS]

def clean_title(name):
    name = name.lower()
    name = re.sub(r"\[[^\]]*\]", " ", name)
    name = re.sub(r"\([^\)]*\)", " ", name)
    name = re.sub(r"\b(720p|1080p|2160p|webrip|web-dl|bluray|brrip|hdrip|dvdscr|x264|x265|yts|tgx|rarbg|galaxyrg|repack|proper|5.1|10bit)\b", " ", name)
    name = re.sub(r"[^a-z0-9]+", " ", name)
    name = re.sub(r"\b(19|20)\d{2}\b", " ", name)
    return " ".join(name.split()).strip()

def quality_score(path):
    n = str(path).lower()
    score = 0
    if "2160p" in n or "4k" in n:
        score += 60
    elif "1080p" in n:
        score += 40
    elif "720p" in n:
        score += 20
    if "bluray" in n:
        score += 25
    elif "web-dl" in n:
        score += 20
    elif "webrip" in n:
        score += 15
    if "repack" in n or "proper" in n:
        score += 5
    if "sample" in n:
        score -= 50
    try:
        score += min(int(path.stat().st_size / 1024**3), 20)
    except Exception:
        pass
    return score

def size_gb(path):
    try:
        return path.stat().st_size / 1024**3
    except Exception:
        return 0

def dashboard():
    movies = scan_videos(MOVIES)
    tv = scan_videos(TV)
    shuttle = scan_videos(SHUTTLE)

    print()
    print("Dashboard")
    print("─────────")
    print(f"Movies video files: {len(movies)}")
    print(f"TV video files:     {len(tv)}")
    print(f"Shuttle videos:     {len(shuttle)}")
    print(f"Movies path:        {MOVIES}")
    print(f"TV path:            {TV}")
    print(f"Shuttle path:       {SHUTTLE}")
    print()
    print("Nothing has been changed.")

def library_health():
    movies = scan_videos(MOVIES)
    tv = scan_videos(TV)

    groups = defaultdict(list)
    junk = []

    for f in movies:
        key = clean_title(f.parent.name)
        if key:
            groups[key].append(f)
        if "sample" in str(f).lower():
            junk.append(f)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}

    print()
    print("Library Health")
    print("──────────────")
    print(f"Movies video files:      {len(movies)}")
    print(f"TV video files:          {len(tv)}")
    print(f"Possible duplicates:     {len(duplicates)}")
    print(f"Sample/junk candidates:  {len(junk)}")
    print()

    print("Sample/junk candidates")
    print("──────────────────────")
    for f in junk[:20]:
        print(f"- {f}")
    if not junk:
        print("None found")

    print()
    print("Top duplicate candidates")
    print("────────────────────────")
    shown = 0
    for title, files in sorted(duplicates.items()):
        ranked = sorted(files, key=quality_score, reverse=True)
        print()
        print(title.title())
        for f in ranked:
            marker = "KEEP" if f == ranked[0] else "REVIEW"
            print(f"{marker:6} score {quality_score(f):>3} {size_gb(f):>5.1f} GB {f}")
        shown += 1
        if shown >= 20:
            break

    print()
    print("Nothing has been changed.")

def scan_shuttle():
    files = scan_videos(SHUTTLE)
    print()
    print("Shuttle Scan")
    print("────────────")
    print(f"Video files found: {len(files)}")
    for f in files[:40]:
        print(f"[DRY RUN] {f}")
    print()
    print("Nothing has been changed.")

def main():
    while True:
        logo()
        print("1. Dashboard")
        print("2. Scan Shuttle")
        print("3. Library Health")
        print("4. Ship Mode")
        print("5. Exit")
        print()
        choice = input("Select option: ").strip()

        if choice == "1":
            dashboard()
        elif choice == "2":
            scan_shuttle()
        elif choice == "3":
            library_health()
        elif choice == "4":
            print("\\nShip Mode: Harbour")
            print("Low Impact: planned")
        elif choice == "5":
            print("Exiting DeckFlix.")
            break
        else:
            print("Invalid option.")

        input("\\nPress Enter to return to menu...")

if __name__ == "__main__":
    main()
EOF

chmod +x deckflix.py

echo "DeckFlix installed to /opt/deckflix"
echo "Run with:"
echo "cd /opt/deckflix && ./deckflix.py"
