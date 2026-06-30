from pathlib import Path

from deckflix_app.library_manager import library_summary
from deckflix_app.quality import quality_label
from deckflix_app.repair_engine import show_repair_preview
from deckflix_app.repair_queue import add as add_to_queue
from deckflix_app.repair_queue import count as queue_count


def format_duplicate_name(key):
    text = str(key)

    if isinstance(key, tuple):
        title = key[0]
        year = key[1]

        title = format_title(title)

        if year:
            return f"{title} ({year})"

        return title

    parts = text.split()

    if parts and parts[-1].isdigit() and len(parts[-1]) == 4:
        year = parts[-1]
        title = " ".join(parts[:-1])
        return f"{format_title(title)} ({year})"

    return format_title(text)


def format_title(title):
    small_words = {
        "and",
        "or",
        "of",
        "the",
        "a",
        "an",
        "in",
        "on",
        "at",
        "to",
        "for",
        "from",
        "with",
    }

    words = str(title).replace("_", " ").split()
    formatted = []

    for index, word in enumerate(words):
        lower = word.lower()

        if index != 0 and lower in small_words:
            formatted.append(lower)
        else:
            formatted.append(lower.capitalize())

    return " ".join(formatted)


def size_gb(path):
    try:
        return Path(path).stat().st_size / 1024**3
    except Exception:
        return 0


def folder_name(item):
    return Path(item.path).parent.name


def star_rating(score):
    if score >= 90:
        return "★★★★★"
    if score >= 75:
        return "★★★★☆"
    if score >= 60:
        return "★★★☆☆"
    if score >= 40:
        return "★★☆☆☆"
    return "★☆☆☆☆"


def confidence_bar(percent):
    filled = round(percent / 5)
    empty = 20 - filled

    return "█" * filled + "░" * empty


def same_release(first, second):
    return (
        first.resolution == second.resolution
        and first.source == second.source
        and first.codec == second.codec
        and first.quality_score == second.quality_score
    )


def same_filename(first, second):
    return first.path.name == second.path.name


def confidence_score(best, duplicates):
    if not duplicates:
        return 75

    score = 70

    for duplicate in duplicates:
        if same_filename(best, duplicate):
            score += 10
        if best.resolution == duplicate.resolution:
            score += 5
        if best.source == duplicate.source:
            score += 5
        if best.codec == duplicate.codec:
            score += 5
        if best.quality_score == duplicate.quality_score:
            score += 5

    return min(score, 100)


def recommendation_for_item(item, best):
    if item == best:
        return "KEEP"

    if same_release(item, best):
        return "REVIEW DUPLICATE"

    if item.quality_score >= best.quality_score - 10:
        return "OPTIONAL"

    return "REVIEW"


def show_confidence(percent):
    print("Confidence")
    print("──────────")
    print(f"{confidence_bar(percent)} {percent}%")
    print()


def show_group_recommendation(ranked):
    best = ranked[0]
    duplicates = [
        item
        for item in ranked[1:]
        if same_release(item, best)
    ]

    print("Recommendation")
    print("══════════════")
    print()

    if duplicates:
        saving = sum(size_gb(item.path) for item in duplicates)
        confidence = confidence_score(best, duplicates)

        print("⚠ REVIEW DUPLICATE")
        print()
        show_confidence(confidence)

        print("Reason")
        print("──────")

        if any(same_filename(best, item) for item in duplicates):
            print("✓ Same filename")

        print("✓ Same resolution")
        print("✓ Same source")
        print("✓ Same codec")
        print("✓ Same quality score")
        print()

        print("Folder Comparison")
        print("─────────────────")
        print()

        print("KEEP")
        print(f"📁 {folder_name(best)}")
        print()

        for duplicate in duplicates:
            print("REVIEW")
            print(f"📁 {folder_name(duplicate)}")
            print()

        print(f"Potential Saving : {saving:.2f} GB")
        print()
        return

    removable = ranked[1:]
    saving = sum(size_gb(item.path) for item in removable)

    print("✓ KEEP BEST COPY")
    print()
    show_confidence(75)
    print("Reason")
    print("──────")
    print("Highest quality score found.")
    print()
    print(f"Best Copy         : {quality_label(best)}")
    print(f"Potential Saving : {saving:.2f} GB")
    print()


def show_duplicate_group(title, items):
    ranked = sorted(
        items,
        key=lambda item: item.quality_score,
        reverse=True,
    )

    display_name = format_duplicate_name(title)

    print()
    print(display_name)
    print("═" * len(display_name))
    print()

    show_group_recommendation(ranked)

    for index, item in enumerate(ranked, start=1):
        recommendation = recommendation_for_item(
            item,
            ranked[0],
        )

        print(f"Copy {index}")
        print("──────")
        print(f"Rating          : {star_rating(item.quality_score)}")
        print(f"Quality         : {quality_label(item)}")
        print(f"Score           : {item.quality_score}")
        print(f"Size            : {size_gb(item.path):.2f} GB")
        print(f"Recommendation  : {recommendation}")
        print(f"File            : {item.path}")
        print()

    print("Nothing has been changed.")
    print()
    
    choice = input(
        "[A] Add to Queue   [R] Repair Preview   [Enter] Back : "
    ).strip().lower()

    if choice == "a":
        add_to_queue(Path(ranked[1].path).parent)

        print()
        print("✓ Added to Repair Queue")
        print(f"Items in Queue : {queue_count()}")
        input("\nPress Enter to continue...")

    if choice == "r":
        show_repair_preview(
            Path(ranked[1].path).parent
        )


def show_duplicate_inspector(movies_path, tv_path):
    summary = library_summary(
        movies_path,
        tv_path,
    )

    duplicates = summary["movie_duplicates"]

    print()
    print("Duplicate Inspector")
    print("═══════════════════")
    print()

    if not duplicates:
        print("No duplicate movie titles found.")
        return

    keys = sorted(duplicates.keys())

    while True:
        print(f"Duplicate Groups Found : {len(keys)}")
        print()

        for index, key in enumerate(keys[:20], start=1):
            print(f"{index:>2}. {format_duplicate_name(key)}")

        print()
        print("Select a duplicate group number to inspect.")
        print("Q. Back")
        print()

        choice = input("Select option: ").strip().lower()

        if choice == "q":
            break

        if not choice.isdigit():
            print("Invalid option.")
            continue

        index = int(choice)

        if index < 1 or index > min(len(keys), 20):
            print("Invalid option.")
            continue

        selected_key = keys[index - 1]

        show_duplicate_group(
            selected_key,
            duplicates[selected_key],
        )

        input("\nPress Enter to return to duplicate list...")
        print()
