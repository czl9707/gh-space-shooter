"""Tests for output providers."""

import pytest
from PIL import Image
from gh_space_shooter.output.base import OutputProvider
from gh_space_shooter.output import GifOutputProvider, WebPOutputProvider, resolve_output_provider


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


def test_webp_provider_encodes_frames():
    """WebPOutputProvider should encode frames to WebP format."""
    provider = WebPOutputProvider(fps=30)
    frames = [create_test_frame("red"), create_test_frame("blue")]

    result = provider.encode(iter(frames))

    # WebP files start with RIFF....WEBP
    assert result.startswith(b"RIFF")
    assert b"WEBP" in result
    assert len(result) > 0


def test_webp_provider_empty_frames():
    """WebPOutputProvider should handle empty frame list."""
    provider = WebPOutputProvider(fps=30)
    result = provider.encode(iter([]))

    assert result == b""


def test_resolve_gif_provider():
    """resolve_output_provider should return GifOutputProvider for .gif files."""
    provider = resolve_output_provider("output.gif", fps=30, watermark=True)

    assert isinstance(provider, GifOutputProvider)
    assert provider.fps == 30
    assert provider.watermark is True


def test_resolve_webp_provider():
    """resolve_output_provider should return WebPOutputProvider for .webp files."""
    provider = resolve_output_provider("output.webp", fps=25)

    assert isinstance(provider, WebPOutputProvider)
    assert provider.fps == 25
    assert provider.watermark is False


def test_resolve_unsupported_format():
    """resolve_output_provider should raise ValueError for unsupported formats."""
    with pytest.raises(ValueError, match="Unsupported output format"):
        resolve_output_provider("output.mp4", fps=30)


def test_resolve_case_insensitive():
    """resolve_output_provider should handle uppercase extensions."""
    provider = resolve_output_provider("output.GIF", fps=30)
    assert isinstance(provider, GifOutputProvider)

    provider = resolve_output_provider("output.WEBP", fps=30)
    assert isinstance(provider, WebPOutputProvider)
