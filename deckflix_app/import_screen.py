from deckflix_app.importer import (
    build_import_plan,
    print_import_plan,
)


def show_import_plan(queue, movies_path, tv_path):
    """
    Display a dry-run import plan.

    No files are copied.
    """

    plan = build_import_plan(
        queue,
        movies_path,
        tv_path,
    )

    print_import_plan(plan)

    return plan
