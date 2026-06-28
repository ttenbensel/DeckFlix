from pathlib import Path

from deckflix_app.library_manager import library_summary
from deckflix_app.quality import quality_label


def format_duplicate_name(key):
    if isinstance(key, tuple):
        title = key[0]
        year = key[1]

        if year:
            return f"{title} ({year})"

        return title

    return str(key)


def size_gb(path):
    try:
        return Path(path).stat().st_size / 1024**3
    except Exception:
        return 0


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


def same_release(first, second):
    return (
        first.resolution == second.resolution
        and first.source == second.source
        and first.codec == second.codec
        and first.quality_score == second.quality_score
    )


def recommendation_for_item(item, best):
    if item == best:
        return "KEEP"

    if same_release(item, best):
        return "REVIEW DUPLICATE"

    if item.quality_score >= best.quality_score - 10:
        return "OPTIONAL"

    return "REVIEW"


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

        print("⚠ REVIEW DUPLICATE")
        print()
        print("Reason")
        print("──────")
        print("✓ Same resolution")
        print("✓ Same source")
        print("✓ Same codec")
        print("✓ Same quality score")
        print()
        print("These files appear to be the same release.")
        print()
        print(f"Potential Saving : {saving:.2f} GB")
        print()
        return

    removable = ranked[1:]
    saving = sum(size_gb(item.path) for item in removable)

    print("✓ KEEP BEST COPY")
    print()
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
