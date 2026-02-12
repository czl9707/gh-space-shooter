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
    """Provider should create file and write HTML img tag when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.txt")
        provider = WebpDataUrlOutputProvider(output_path)
        frames = [create_test_frame("red"), create_test_frame("blue")]

        data = provider.encode(iter(frames), frame_duration=100)
        provider.write(data)

        # File should exist and contain HTML img tag
        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            content = f.read()
        assert content.startswith('<img src="data:image/webp;base64,')
        assert content.endswith('" />\n')


def test_injection_mode_replaces_marker_line():
    """Provider should replace line containing <!-- space-shooter --> with HTML img tag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.txt")

        # Create file with marker
        with open(output_path, "w") as f:
            f.write("# My Contribution Graph\n")
            f.write("<!-- space-shooter -->\n")
            f.write("## Other content\n")

        provider = WebpDataUrlOutputProvider(output_path)
        frames = [create_test_frame("red")]
        data = provider.encode(iter(frames), frame_duration=100)
        provider.write(data)

        # Verify injection worked
        with open(output_path, "r") as f:
            content = f.read()

        lines = content.splitlines()
        assert len(lines) == 3
        assert lines[0] == "# My Contribution Graph"
        assert lines[1].startswith('<img src="data:image/webp;base64,')
        assert lines[1].endswith('" />')
        assert lines[2] == "## Other content"


def test_append_mode_when_no_marker():
    """Provider should append HTML img tag when no marker found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.txt")

        # Create file without marker
        with open(output_path, "w") as f:
            f.write("# My Contribution Graph\n")

        provider = WebpDataUrlOutputProvider(output_path)
        frames = [create_test_frame("red")]
        data = provider.encode(iter(frames), frame_duration=100)
        provider.write(data)

        # Verify append worked
        with open(output_path, "r") as f:
            content = f.read()

        lines = content.splitlines()
        assert len(lines) == 2
        assert lines[0] == "# My Contribution Graph"
        assert lines[1].startswith('<img src="data:image/webp;base64,')
        assert lines[1].endswith('" />')


def test_empty_frames_writes_empty_img_tag():
    """Provider should write empty img tag when no frames provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.txt")

        provider = WebpDataUrlOutputProvider(output_path)
        data = provider.encode(iter([]), frame_duration=100)
        provider.write(data)

        # File should exist with empty img tag
        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            content = f.read()
        # write() wraps empty data URL in img tag with newline
        assert content == '<img src="" />\n'
        # encode() returns empty bytes
        assert data == b""


def test_multiple_markers_only_first_replaced():
    """Provider should only replace first marker occurrence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.txt")

        # Create file with multiple markers
        with open(output_path, "w") as f:
            f.write("<!-- space-shooter -->\n")
            f.write("<!-- space-shooter -->\n")
            f.write("more content\n")

        provider = WebpDataUrlOutputProvider(output_path)
        frames = [create_test_frame("red")]
        data = provider.encode(iter(frames), frame_duration=100)
        provider.write(data)

        # Verify only first marker replaced
        with open(output_path, "r") as f:
            content = f.read()

        lines = content.splitlines()
        assert len(lines) == 3
        assert lines[0].startswith('<img src="data:image/webp;base64,')
        assert lines[0].endswith('" />')
        assert lines[1] == "<!-- space-shooter -->"  # Second marker untouched
        assert lines[2] == "more content"
