from deckflix_app.operating_modes import (
    MODE_ORDER,
    apply_operating_mode,
    get_operating_mode,
    infer_operating_mode,
    mode_changes,
)


def show_operating_modes(config) -> bool:
    current = infer_operating_mode(config)

    print()
    print("Operating Modes")
    print("═══════════════")
    print()
    print("Current Mode")
    print("────────────")
    print(current.display_name)
    print(current.motto)
    print()
    print(f"Connectivity       {current.connectivity}")
    print(
        f"Library Protection "
        f"{current.library_protection}"
    )
    print(
        f"Low Impact         "
        f"{'Enabled' if current.low_impact else 'Off'}"
    )

    print()
    print("Available Modes")
    print("───────────────")

    for number, key in enumerate(MODE_ORDER, start=1):
        mode = get_operating_mode(key)
        marker = " (Current)" if key == current.key else ""

        print(
            f"{number}. {mode.display_name}{marker}"
        )
        print(f"   {mode.motto}")
        print(f"   {mode.description}")
        print()

    answer = input(
        "Select mode or press Enter to cancel: "
    ).strip()

    if not answer:
        print("Operating mode unchanged.")
        return False

    try:
        selected_index = int(answer) - 1
        selected_key = MODE_ORDER[selected_index]
    except (ValueError, IndexError):
        print("Invalid operating mode.")
        return False

    selected = get_operating_mode(selected_key)

    if selected.key == current.key:
        print("That operating mode is already active.")
        return False

    changes = mode_changes(config, selected)

    print()
    print(f"Switch to {selected.display_name}?")
    print(selected.motto)
    print()
    print("Settings that will apply")
    print("────────────────────────")

    if changes:
        for change in changes:
            print(f"- {change}")
    else:
        print("- Friendly operating-mode label only")

    if not selected.read_only:
        print()
        print("WARNING")
        print("───────")
        print(
            "This mode turns Library Protection OFF and permits "
            "approved imports to modify the media libraries."
        )

    print()
    confirmation = input(
        "Apply this operating mode? (y/N): "
    ).strip().lower()

    if confirmation != "y":
        print("Operating mode unchanged.")
        return False

    apply_operating_mode(
        config.source_path,
        selected,
    )

    print()
    print(f"Operating mode changed to {selected.display_name}.")
    print("Restart DeckFlix to activate the new mode.")

    return True
