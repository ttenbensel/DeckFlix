from deckflix_app.planner import ImportPlan


def print_import_report(plan: ImportPlan) -> None:
    print()
    print("=" * 40)
    print("      DECKFLIX IMPORT REPORT")
    print("=" * 40)
    print(f"New         : {plan.new}")
    print(f"Upgrades    : {plan.upgrades}")
    print(f"Duplicates  : {plan.duplicates}")
    print(f"Downgrades  : {plan.downgrades}")
    print("-" * 40)
    print(f"Total Files : {plan.total}")
    print(f"Transfer    : {plan.total_bytes / (1024**3):.2f} GB")
    print("=" * 40)
