from unittest.mock import Mock

import deckflix_app.operations_ui as ui


def dependencies():
    return {
        "operation_manager": Mock(),
        "shuttle": Mock(),
        "config": Mock(),
        "operation_state_path": Mock(),
    }


def test_option_5_routes_to_shuttle_release(
    monkeypatch,
):
    called = Mock()

    monkeypatch.setattr(
        ui,
        "shuttle_release",
        called,
    )

    deps = dependencies()

    result = (
        ui.handle_shuttle_operation_choice(
            "5",
            **deps,
        )
    )

    assert result is True

    called.assert_called_once_with(
        operation_manager=deps[
            "operation_manager"
        ],
        operation_state_path=deps[
            "operation_state_path"
        ],
    )


def test_option_6_routes_to_dashboard(
    monkeypatch,
):
    called = Mock()

    monkeypatch.setattr(
        ui,
        "operation_dashboard",
        called,
    )

    deps = dependencies()

    result = (
        ui.handle_shuttle_operation_choice(
            "6",
            **deps,
        )
    )

    assert result is True

    called.assert_called_once_with(
        deps["operation_manager"]
    )


def test_option_7_routes_to_clear(
    monkeypatch,
):
    called = Mock()

    monkeypatch.setattr(
        ui,
        "clear_operation",
        called,
    )

    deps = dependencies()

    result = (
        ui.handle_shuttle_operation_choice(
            "7",
            **deps,
        )
    )

    assert result is True

    called.assert_called_once_with(
        operation_manager=deps[
            "operation_manager"
        ],
        operation_state_path=deps[
            "operation_state_path"
        ],
    )


def test_option_8_leaves_shuttle_menu():
    result = (
        ui.handle_shuttle_operation_choice(
            "8",
            **dependencies(),
        )
    )

    assert result is False
