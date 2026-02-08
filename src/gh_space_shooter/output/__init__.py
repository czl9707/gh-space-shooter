"""Output providers for different animation formats."""

from pathlib import Path
from .base import OutputProvider
from .gif_provider import GifOutputProvider
from .webp_provider import WebPOutputProvider


# Extension -> Provider class mapping
_PROVIDER_MAP: dict[str, type[OutputProvider]] = {
    ".gif": GifOutputProvider,
    ".webp": WebPOutputProvider,
}


def resolve_output_provider(
    file_path: str,
    fps: int,
    watermark: bool = False,
) -> OutputProvider:
    """
    Resolve the appropriate output provider based on file extension.

    Args:
        file_path: Output file path (extension determines format)
        fps: Frames per second
        watermark: Whether to add watermark

    Returns:
        An OutputProvider instance

    Raises:
        ValueError: If file extension is not supported
    """
    ext = Path(file_path).suffix.lower()

    if ext not in _PROVIDER_MAP:
        supported = ", ".join(_PROVIDER_MAP.keys())
        raise ValueError(
            f"Unsupported output format: {ext}. Supported formats: {supported}"
        )

    provider_class = _PROVIDER_MAP[ext]
    return provider_class(fps=fps, watermark=watermark)


__all__ = ["OutputProvider", "GifOutputProvider", "WebPOutputProvider", "resolve_output_provider"]
