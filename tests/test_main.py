import subprocess
import sys


def test_module_entrypoint():
    result = subprocess.run(
        [sys.executable, "-m", "deckflix_app", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "analyse" in result.stdout
