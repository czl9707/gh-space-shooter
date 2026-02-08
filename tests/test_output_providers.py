"""Tests for output providers."""

import pytest
from PIL import Image
from gh_space_shooter.output.base import OutputProvider
from gh_space_shooter.output import GifOutputProvider


def test_output_provider_is_abstract():
    """OutputProvider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        OutputProvider(fps=30)


def test_output_provider_has_required_attributes():
    """Concrete OutputProvider should have fps, watermark, frame_duration."""
    class DummyProvider(OutputProvider):
        def encode(self, frames):
            return b""

    provider = DummyProvider(fps=30, watermark=True)
    assert provider.fps == 30
    assert provider.watermark is True
    assert provider.frame_duration == 33  # 1000 // 30


def create_test_frame(color="red"):
    """Helper to create a test frame."""
    img = Image.new("RGB", (10, 10), color)
    return img


def test_gif_provider_encodes_frames():
    """GifOutputProvider should encode frames to GIF format."""
    provider = GifOutputProvider(fps=30)
    frames = [create_test_frame("red"), create_test_frame("blue")]

    result = provider.encode(iter(frames))

    assert result.startswith(b"GIF89")
    assert len(result) > 0


def test_gif_provider_empty_frames():
    """GifOutputProvider should handle empty frame list."""
    provider = GifOutputProvider(fps=30)
    result = provider.encode(iter([]))

    # Empty result for empty frames
    assert result == b""
