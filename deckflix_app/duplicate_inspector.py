from pathlib import Path

from deckflix_app.library_manager import library_summary
from deckflix_app.repair_engine import show_repair_preview
from deckflix_app.repair_queue import add as add_to_queue
from deckflix_app.repair_queue import count as queue_count
from deckflix_app.quality import quality_score


def format_duplicate_name(key):
    if isinstance(key, tuple):

        if key[0] == "movie":
            title = key[1]

            if len(key) > 2 and key[2]:
                return f"{format_title(title)} ({key[2]})"

            return format_title(title)

        if key[0] == "tv":
            title = key[1]

            if len(key) > 3:
                return (
                    f"{format_title(title)} "
                    f"S{key[2]:02d}E{key[3]:02d}"
                )

            return format_title(title)

    return format_title(str(key))


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
        and first.video_codec == second.video_codec
        and quality_score(first) == quality_score(second)
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

        if best.video_codec == duplicate.video_codec:
            score += 5

        if quality_score(best) == quality_score(duplicate):
            score += 5

    return min(score, 100)


def recommendation_for_item(item, best):
    if item == best:
        return "KEEP"

    if same_release(item, best):
        return "REVIEW DUPLICATE"

    if quality_score(item) >= quality_score(best) - 10:
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
        saving = sum(
            size_gb(item.path)
            for item in duplicates
        )

        confidence = confidence_score(
            best,
            duplicates,
        )

        print("⚠ REVIEW DUPLICATE")
        print()

        show_confidence(confidence)

        print("Reason")
        print("──────")

        if any(
            same_filename(best, item)
            for item in duplicates
        ):
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

        print(
            f"Potential Saving : "
            f"{saving:.2f} GB"
        )

        print()
        return

    removable = ranked[1:]

    saving = sum(
        size_gb(item.path)
        for item in removable
    )

    print("✓ KEEP BEST COPY")
    print()

    show_confidence(75)

    print("Reason")
    print("──────")
    print("Highest quality score found.")
    print()

    print(
        f"Best Copy         : "
        f"{best.resolution or 'unknown'} "
        f"{best.source or 'unknown'} "
        f"{best.video_codec or 'unknown'} "
        f"(Score {quality_score(best)})"
    )

    print(
        f"Potential Saving : "
        f"{saving:.2f} GB"
    )

    print()

def show_duplicate_group(title, items):
    ranked = sorted(
        items,
        key=lambda item: quality_score(item),
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

        print(
            f"Rating          : "
            f"{star_rating(quality_score(item))}"
        )

        print(
            f"Quality         : "
            f"{item.resolution or 'unknown'} "
            f"{item.source or 'unknown'} "
            f"{item.video_codec or 'unknown'}"
        )

        print(
            f"Score           : "
            f"{quality_score(item)}"
        )

        print(
            f"Size            : "
            f"{size_gb(item.path):.2f} GB"
        )

        print(
            f"Recommendation  : "
            f"{recommendation}"
        )

        print(
            f"File            : "
            f"{item.path}"
        )

        print()

    print("Nothing has been changed.")
    print()

    choice = input(
        "[A] Add to Queue   "
        "[R] Repair Preview   "
        "[Enter] Back : "
    ).strip().lower()

    if choice == "a":
        add_to_queue(
            Path(ranked[1].path).parent
        )

        print()
        print("✓ Added to Repair Queue")
        print(
            f"Items in Queue : "
            f"{queue_count()}"
        )

        input(
            "\nPress Enter to continue..."
        )

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
        input("\nPress Enter to return...")
        return

    keys = sorted(
        duplicates.keys()
    )

    while True:
        print(
            f"Duplicate Groups Found : "
            f"{len(keys)}"
        )

        print()

        for index, key in enumerate(
            keys[:20],
            start=1,
        ):
            print(
                f"{index:>2}. "
                f"{format_duplicate_name(key)}"
            )

        print()
        print(
            "Select a duplicate group number "
            "to inspect."
        )
        print("Q. Back")
        print()

        choice = input(
            "Select option: "
        ).strip().lower()

        if choice == "q":
            break

        if not choice.isdigit():
            print("Invalid option.")
            continue

        index = int(choice)

        if index < 1 or index > min(
            len(keys),
            20,
        ):
            print("Invalid option.")
            continue

        selected_key = keys[index - 1]

        show_duplicate_group(
            selected_key,
            duplicates[selected_key],
        )

        input(
            "\nPress Enter to return "
            "to duplicate list..."
        )


