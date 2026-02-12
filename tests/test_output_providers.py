"""Tests for output providers."""

from PIL import Image
import pytest
from gh_space_shooter.game.renderer import WATERMARK_TEXT
from gh_space_shooter.game.svg_timeline import SvgTimelineFrame
from gh_space_shooter.output import (
    GifOutputProvider,
    SvgOutputProvider,
    WebPOutputProvider,
    resolve_output_provider,
)

def create_test_frame(color="red"):
    """Helper to create a test frame."""
    img = Image.new("RGB", (10, 10), color)
    return img


def create_test_timeline_frame(
    time_ms: int,
    ship_x: float,
    width: int = 10,
    height: int = 10,
    watermark: bool = False,
) -> SvgTimelineFrame:
    return SvgTimelineFrame(
        width=width,
        height=height,
        time_ms=time_ms,
        watermark=watermark,
        ship_x=ship_x,
        stars=(),
        enemies=(),
        bullets=(),
        explosions=(),
    )


def test_gif_provider_encodes_frames():
    """GifOutputProvider should encode frames to GIF format."""
    provider = GifOutputProvider("test_output.gif")
    frames = [create_test_frame("red"), create_test_frame("blue")]

    result = provider.encode(iter(frames), frame_duration=100)

    assert result.startswith(b"GIF89")
    assert len(result) > 0


def test_gif_provider_empty_frames():
    """GifOutputProvider should handle empty frame list."""
    provider = GifOutputProvider("test_output.gif")
    result = provider.encode(iter([]), frame_duration=100)

    # Empty result for empty frames
    assert result == b""


def test_webp_provider_encodes_frames():
    """WebPOutputProvider should encode frames to WebP format."""
    provider = WebPOutputProvider("test_output.webp")
    frames = [create_test_frame("red"), create_test_frame("blue")]

    result = provider.encode(iter(frames), frame_duration=100)

    # WebP files start with RIFF....WEBP
    assert result.startswith(b"RIFF")
    assert b"WEBP" in result
    assert len(result) > 0


def test_webp_provider_empty_frames():
    """WebPOutputProvider should handle empty frame list."""
    provider = WebPOutputProvider("test_output.webp")
    result = provider.encode(iter([]), frame_duration=100)

    assert result == b""


def test_svg_provider_empty_frames():
    """SvgOutputProvider should handle empty frame list."""
    provider = SvgOutputProvider()
    result = provider.encode(iter([]), frame_duration=100)

    assert result == b""


def test_svg_provider_encodes_timeline_frames():
    """SvgOutputProvider should encode timeline snapshots to animated SVG."""
    provider = SvgOutputProvider()
    frames = [create_test_timeline_frame(0, 0.0), create_test_timeline_frame(100, 1.0)]

    result = provider.encode(iter(frames), frame_duration=100)

    assert result.startswith(b"<?xml")
    assert b"<animate " in result
    assert b'id="fallback-frame"' not in result
    assert b'<g visibility="hidden">' not in result
    assert len(result) > 0


def test_svg_provider_clamps_non_positive_frame_duration():
    """SvgOutputProvider should clamp frame duration to at least 1ms."""
    provider = SvgOutputProvider()
    frames = [create_test_timeline_frame(0, 0.0), create_test_timeline_frame(100, 1.0)]

    result = provider.encode(iter(frames), frame_duration=0)

    assert b'dur="2ms"' in result
    assert b'dur="0ms"' not in result


def test_svg_provider_raises_on_mixed_timeline_dimensions():
    """SvgOutputProvider should reject mixed-size timeline frame sequences."""
    provider = SvgOutputProvider()
    frames = [
        create_test_timeline_frame(0, 0.0, width=10, height=10),
        create_test_timeline_frame(100, 1.0, width=11, height=10),
    ]

    with pytest.raises(ValueError, match="All SVG timeline frames must have the same dimensions"):
        provider.encode(iter(frames), frame_duration=100)


def test_svg_provider_rejects_non_timeline_frames():
    """SvgOutputProvider should reject non-timeline frame payloads."""
    provider = SvgOutputProvider()
    frames = [object()]  # type: ignore[list-item]

    with pytest.raises(TypeError, match="SVG output only supports timeline frames"):
        provider.encode(iter(frames), frame_duration=100)


def test_svg_provider_timeline_watermark_renders_text():
    """Timeline SVG output should include watermark text when enabled."""
    provider = SvgOutputProvider()
    frames = [
        create_test_timeline_frame(0, 0.0, watermark=True),
        create_test_timeline_frame(100, 1.0, watermark=True),
    ]

    result = provider.encode(iter(frames), frame_duration=100)

    assert WATERMARK_TEXT.encode("utf-8") in result


def test_resolve_gif_provider():
    """resolve_output_provider should return GifOutputProvider for .gif files."""
    provider = resolve_output_provider("output.gif")

    assert isinstance(provider, GifOutputProvider)

def test_resolve_webp_provider():
    """resolve_output_provider should return WebPOutputProvider for .webp files."""
    provider = resolve_output_provider("output.webp")

    assert isinstance(provider, WebPOutputProvider)


def test_resolve_svg_provider():
    """resolve_output_provider should return SvgOutputProvider for .svg files."""
    provider = resolve_output_provider("output.svg")

    assert isinstance(provider, SvgOutputProvider)


def test_resolve_unsupported_format():
    """resolve_output_provider should raise ValueError for unsupported formats."""
    with pytest.raises(ValueError, match="Unsupported output format"):
        resolve_output_provider("output.mp4")


def test_resolve_case_insensitive():
    """resolve_output_provider should handle uppercase extensions."""
    provider = resolve_output_provider("output.GIF", )
    assert isinstance(provider, GifOutputProvider)

    provider = resolve_output_provider("output.WEBP", )
    assert isinstance(provider, WebPOutputProvider)

    provider = resolve_output_provider("output.SVG", )
    assert isinstance(provider, SvgOutputProvider)
