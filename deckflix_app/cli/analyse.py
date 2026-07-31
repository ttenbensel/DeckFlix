from deckflix_app.analysis import analyse_import
from deckflix_app.cli.report import print_import_report
from deckflix_app.scanner import scan_media


def analyse(library_path: str, shuttle_path: str) -> None:
    library = scan_media(library_path)
    shuttle = scan_media(shuttle_path)

    _, plan = analyse_import(library, shuttle)

    print_import_report(plan)
