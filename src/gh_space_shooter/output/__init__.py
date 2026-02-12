"""Output providers for different animation formats."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .base import OutputProvider
from .gif_provider import GifOutputProvider
from .svg_provider import SvgOutputProvider
from .webp_provider import WebPOutputProvider
from .webp_dataurl_provider import WebpDataUrlOutputProvider


@dataclass(frozen=True)
class OutputFormatSpec:
    extension: str
    media_type: str
    provider_class: type[OutputProvider[Any]]


_OUTPUT_FORMATS: dict[str, OutputFormatSpec] = {
    "gif": OutputFormatSpec(
        extension=".gif",
        media_type="image/gif",
        provider_class=GifOutputProvider,
    ),
    "webp": OutputFormatSpec(
        extension=".webp",
        media_type="image/webp",
        provider_class=WebPOutputProvider,
    ),
    "svg": OutputFormatSpec(
        extension=".svg",
        media_type="image/svg+xml",
        provider_class=SvgOutputProvider,
    ),
}


def resolve_output_provider(
    file_path: str,
) -> OutputProvider[Any]:
    """
    Resolve the appropriate output provider based on file extension.

    Args:
        file_path: Output file path (extension determines format)

    Returns:
        An OutputProvider instance

    Raises:
        ValueError: If file extension is not supported
    """
    ext = Path(file_path).suffix.lower()
    spec = _output_spec_from_extension(ext)
    return spec.provider_class(file_path)


def supported_output_formats() -> tuple[str, ...]:
    """Return supported output format names."""
    return tuple(_OUTPUT_FORMATS.keys())


def media_type_for_output_format(output_format: str) -> str:
    """Resolve media type for a supported output format."""
    spec = _output_spec_from_format(output_format)
    return spec.media_type


def output_path_for_format(output_format: str, base_name: str = "output") -> str:
    """Build a synthetic output path from an output format name."""
    spec = _output_spec_from_format(output_format)
    return f"{base_name}{spec.extension}"


def _output_spec_from_extension(ext: str) -> OutputFormatSpec:
    output_format = ext.removeprefix(".")
    spec = _OUTPUT_FORMATS.get(output_format)
    if spec is not None:
        return spec
    supported = ", ".join(spec.extension for spec in _OUTPUT_FORMATS.values())
    raise ValueError(f"Unsupported output format: {ext}. Supported formats: {supported}")


def _output_spec_from_format(output_format: str) -> OutputFormatSpec:
    spec = _OUTPUT_FORMATS.get(output_format.lower())
    if spec is not None:
        return spec
    supported = ", ".join(supported_output_formats())
    raise ValueError(f"Invalid format. Choose from: {supported}")


__all__ = [
    "OutputFormatSpec",
    "OutputProvider",
    "GifOutputProvider",
    "WebPOutputProvider",
    "SvgOutputProvider",
    "WebpDataUrlOutputProvider",
    "resolve_output_provider",
    "supported_output_formats",
    "media_type_for_output_format",
    "output_path_for_format",
]
