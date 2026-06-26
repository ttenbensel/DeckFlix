def confirm_import(plan):
    """
    Ask for confirmation before copying files.

    Returns True if approved.
    """

    print()
    print("Import Confirmation")
    print("═══════════════════")
    print()

    print(f"Files ready to copy : {len(plan)}")
    print()

    if not plan:
        print("Nothing to import.")
        return False

    answer = input("Proceed with import? (y/N): ").strip().lower()

    return answer == "y"
