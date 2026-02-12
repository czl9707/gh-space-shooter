"""Tests for CLI data URL functionality."""

from typer.testing import CliRunner
from gh_space_shooter.cli import app

runner = CliRunner()


def test_mutual_exclusivity_error():
    """Should error when both --output and --write-dataurl-to are provided."""
    result = runner.invoke(app, ["testuser", "--output", "test.gif", "--write-dataurl-to", "test.txt", "--raw-input", "-"])
    assert result.exit_code == 1
    # Error goes to stderr in our CLI
    assert "Cannot specify both --output and --write-dataurl-to" in (result.stdout + result.stderr)
