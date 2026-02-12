"""Tests for CLI data URL functionality."""

import json
import os
import tempfile

from typer.testing import CliRunner
from gh_space_shooter.cli import app

runner = CliRunner()


def test_mutual_exclusivity_error():
    """Should error when both --output and --write-dataurl-to are provided."""
    result = runner.invoke(app, ["testuser", "--output", "test.gif", "--write-dataurl-to", "test.txt", "--raw-input", "-"])
    assert result.exit_code == 1
    # Error goes to stderr in our CLI
    assert "Cannot specify both --output and --write-dataurl-to" in (result.stdout + result.stderr)


def test_dataurl_flag_works():
    """Should generate data URL when --write-dataurl-to is specified."""
    # Create a temporary file with test contribution data
    test_data = {
        "username": "testuser",
        "total_contributions": 0,
        "weeks": [
            {
                "days": [
                    {"date": "2025-01-05", "count": 0, "level": 0}
                    for _ in range(7)
                ]
            }
            for _ in range(52)
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create raw input file
        raw_file = os.path.join(tmpdir, "raw.json")
        with open(raw_file, "w") as f:
            json.dump(test_data, f)

        # Output file
        output_file = os.path.join(tmpdir, "output.txt")

        result = runner.invoke(app, [
            "testuser",
            "--raw-input", raw_file,
            "--write-dataurl-to", output_file
        ])

        assert result.exit_code == 0
        assert os.path.exists(output_file)

        with open(output_file, "r") as f:
            content = f.read()

        # Output should be an HTML img tag with the data URL
        assert content.startswith('<img src="data:image/webp;base64,')
        assert content.endswith('" />\n')
