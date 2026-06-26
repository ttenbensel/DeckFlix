from deckflix_app.approval import approval_summary


def show_approval(approved):
    summary = approval_summary(approved)

    print()
    print("Approval")
    print("════════")
    print()

    print(f"Approved items : {summary['approved']}")
    print()

    if not approved:
        print("Nothing approved.")
        return

    print("Approved Queue")
    print("──────────────")

    for index, item in enumerate(approved, start=1):
        media = item["media"]

        if media.media_type == "movie":
            if media.year:
                name = f"{media.title} ({media.year})"
            else:
                name = media.title
        else:
            name = f"{media.title} S{media.season:02d}E{media.episode:02d}"

        print(f"{index}. {name}")
        print(f"   Action : {item['action']}")
        print()

    print("Nothing has been changed.")
