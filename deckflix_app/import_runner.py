from datetime import datetime
from pathlib import Path

from deckflix_app.approval import approve_imports
from deckflix_app.import_confirm import confirm_import
from deckflix_app.importer import (
    ImportEngine,
    ShuttleCertificate,
    ShuttleSafetyChecker,
    print_certificate,
    queue_from_legacy_plan,
)
from deckflix_app.importer.legacy import build_import_plan




def run_import(
    queue,
    movies_path,
    tv_path,
    shuttle_path=Path("/data/shuttle"),
    staging_directory=Path("/tmp/deckflix-import"),
):
    approved = approve_imports(queue)

    plan = build_import_plan(
        approved,
        movies_path,
        tv_path,
    )

    if not plan:
        print()
        print("Nothing to import.")
        return False

    if not confirm_import(plan):
        print()
        print("Import cancelled.")
        return False

    import_queue = queue_from_legacy_plan(plan)

    result = ImportEngine().execute(
        import_queue,
        staging_directory,
    )

    safety = ShuttleSafetyChecker().check(
        queue=import_queue,
        import_result=result,
        shuttle_path=Path(shuttle_path),
        temp_dir=staging_directory,
    )

    certificate = ShuttleCertificate(
        shuttle_path=Path(shuttle_path),
        import_result=result,
        safety=safety,
        created_at=datetime.now(),
    )

    print_certificate(certificate)

    if safety.safe:
        print()
        print("Shuttle actions are not enabled yet.")
        print("No files will be deleted or ejected.")

    return safety.safe
