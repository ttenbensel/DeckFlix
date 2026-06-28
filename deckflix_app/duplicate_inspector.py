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

    for index, item in enumerate(ranked, start=1):
        if index == 1:
            recommendation = "KEEP"
        elif item.quality_score >= ranked[0].quality_score - 10:
            recommendation = "OPTIONAL"
        else:
            recommendation = "REVIEW"

        print(f"Copy {index}")
        print("──────")
        print(f"Rating          : {star_rating(item.quality_score)}")
        print(f"Quality         : {quality_label(item)}")
        print(f"Score           : {item.quality_score}")
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
