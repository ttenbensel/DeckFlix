from deckflix_app.approval import approve_imports
from deckflix_app.import_confirm import confirm_import
from deckflix_app.importer import (
    build_import_plan,
    copy_one_item,
)


def run_import(queue, movies_path, tv_path):
    """
    Execute an approved import.

    Currently imports ONE file only.
    This keeps testing safe.
    """

    approved = approve_imports(queue)

    plan = build_import_plan(
        approved,
        movies_path,
        tv_path,
    )

    if not confirm_import(plan):
        print()
        print("Import cancelled.")
        return False

    if not plan:
        print()
        print("Nothing to import.")
        return False

    result = copy_one_item(plan[0])

    print()
    print("Import Complete")
    print("═══════════════")
    print(f"Copied:")
    print(result["source"])
    print()
    print("Destination:")
    print(result["target"])
    print()

    return True
