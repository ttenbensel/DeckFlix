from deckflix_app.services.capability_manager import capabilities


def show_capabilities():
    """
    Display registered DeckFlix capabilities.

    Read-only. No workflows are executed.
    """

    print()
    print("DeckFlix Capabilities")
    print("════════════════════")

    for number, item in enumerate(capabilities(), start=1):
        print()
        print(f"{number}. {item.name}")
        print(f"   {item.description}")
        print(f"   Steps     {item.estimated_steps}")
        print(
            f"   Safety    "
            f"{'Approval required' if item.destructive else 'Read-safe'}"
        )

    print()
    print("Information only. No capability has been started.")
