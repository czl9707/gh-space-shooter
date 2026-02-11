"""Tests for WebP data URL output provider."""

from PIL import Image
import pytest
from gh_space_shooter.output.webp_dataurl_provider import WebpDataUrlOutputProvider
import tempfile
import os


def create_test_frame(color="red"):
    """Helper to create a test frame."""
    img = Image.new("RGB", (10, 10), color)
    return img


def test_provider_creates_new_file():
    """Provider should create file and write data URL when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.txt")
        provider = WebpDataUrlOutputProvider(output_path)
        frames = [create_test_frame("red"), create_test_frame("blue")]

        result = provider.encode(iter(frames), frame_duration=100)

        # File should exist and contain data URL
        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            content = f.read()
        assert content.startswith("data:image/webp;base64,")
        # Should return bytes as well
        assert result == content.encode("utf-8")


def test_injection_mode_replaces_marker_line():
    """Provider should replace line containing <!-- space-shooter --> with data URL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.txt")

        # Create file with marker
        with open(output_path, "w") as f:
            f.write("# My Contribution Graph\n")
            f.write("<!-- space-shooter -->\n")
            f.write("## Other content\n")

        provider = WebpDataUrlOutputProvider(output_path)
        frames = [create_test_frame("red")]
        provider.encode(iter(frames), frame_duration=100)

        # Verify injection worked
        with open(output_path, "r") as f:
            content = f.read()

        lines = content.splitlines()
        assert len(lines) == 3
        assert lines[0] == "# My Contribution Graph"
        assert lines[1].startswith("data:image/webp;base64,")
        assert lines[2] == "## Other content"


def test_append_mode_when_no_marker():
    """Provider should append data URL when no marker found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.txt")

        # Create file without marker
        with open(output_path, "w") as f:
            f.write("# My Contribution Graph\n")

        provider = WebpDataUrlOutputProvider(output_path)
        frames = [create_test_frame("red")]
        provider.encode(iter(frames), frame_duration=100)

        # Verify append worked
        with open(output_path, "r") as f:
            content = f.read()

        lines = content.splitlines()
        assert len(lines) == 2
        assert lines[0] == "# My Contribution Graph"
        assert lines[1].startswith("data:image/webp;base64,")


def test_empty_frames_writes_empty_string():
    """Provider should write empty string when no frames provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.txt")

        provider = WebpDataUrlOutputProvider(output_path)
        result = provider.encode(iter([]), frame_duration=100)

        # File should exist with empty content
        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            content = f.read()
        assert content == "\n"  # Empty URL + newline
        assert result == b"\n"  # Returns newline as bytes
