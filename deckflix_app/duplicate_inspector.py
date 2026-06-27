from deckflix_app.library_manager import library_summary


def show_duplicate_inspector(movies_path, tv_path):
    """
    Display duplicate titles found in the library.

    This is the first version. Later it will compare
    quality, codec, bitrate and make recommendations.
    """

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

    print(f"Duplicate Titles Found : {len(duplicates)}")
    print()

    for index, title in enumerate(sorted(duplicates.keys()), start=1):
        if isinstance(title, tuple):
            name = title[0]
            year = title[1]

            if year:
                display = f"{name} ({year})"
            else:
                display = name
        else:
            display = str(title)

        print(f"{index:>2}. {display}")

        if index >= 20:
            break

    print()
    print("Showing first 20 duplicate titles.")
