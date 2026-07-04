"""WebP data URL output provider."""

import base64
import os
from io import BytesIO
from typing import Iterator
from PIL import Image
from .base import OutputProvider


# Section markers for injection mode
_SECTION_START_MARKER = "<!--START_SECTION:space-shooter-->"
_SECTION_END_MARKER = "<!--END_SECTION:space-shooter-->"


class WebpDataUrlOutputProvider(OutputProvider):
    """Output provider that generates WebP as a data URL and writes an HTML img tag to a file."""

    def __init__(self, output_path: str):
        """
        Initialize the provider with an output file path.

        Args:
            output_path: Path to the text file where the HTML img tag will be written
        """
        super().__init__(output_path)

    def encode(self, frames: Iterator[Image.Image], frame_duration: int) -> bytes:
        """
        Encode frames as a WebP data URL.

        Args:
            frames: Iterator of PIL Images
            frame_duration: Duration of each frame in milliseconds

        Returns:
            The data URL string as bytes (for consistency with other providers)
        """
        frame_list = list(frames)

        if not frame_list:
            data_url = ""
        else:
            # Encode as WebP using same settings as WebPOutputProvider
            buffer = BytesIO()
            frame_list[0].save(
                buffer,
                format="webp",
                save_all=True,
                append_images=frame_list[1:],
                duration=frame_duration,
                loop=0,
                lossless=False,
                quality=85,
                method=6,
            )

            # Convert to data URL
            webp_bytes = buffer.getvalue()
            base64_data = base64.b64encode(webp_bytes).decode("ascii")
            data_url = f"data:image/webp;base64,{base64_data}"

        # Return data URL as bytes
        return data_url.encode("utf-8")

    def write(self, data: bytes) -> None:
        """
        Write data URL to file as an HTML img tag with section-based injection.

        For new files, wraps content in section markers.
        For existing files, validates and replaces content between markers.

        Args:
            data: Data URL as bytes (will be decoded as UTF-8 text)

        Raises:
            ValueError: If section markers are missing or in wrong order
        """
        data_url = data.decode("utf-8")
        # Wrap in HTML img tag
        img_tag = f'<img src="{data_url}" />'

        # Try to create new file exclusively (avoids TOCTOU race condition)
        try:
            with open(self.path, "x") as f:
                # Wrap content in section markers
                f.write(_SECTION_START_MARKER + "\n")
                f.write(img_tag + "\n")
                f.write(_SECTION_END_MARKER + "\n")
            return
        except FileExistsError:
            # File exists - read contents
            with open(self.path, "r") as f:
                content = f.read()

        # Find start and end markers
        start_idx = content.find(_SECTION_START_MARKER)
        end_idx = content.find(_SECTION_END_MARKER)

        # Validate markers exist
        if start_idx == -1:
            raise ValueError(
                f"Start marker '{_SECTION_START_MARKER}' not found in file. "
                f"Please add both '{_SECTION_START_MARKER}' and '{_SECTION_END_MARKER}' markers to your file."
            )
        if end_idx == -1:
            raise ValueError(
                f"End marker '{_SECTION_END_MARKER}' not found in file. "
                f"Please add both '{_SECTION_START_MARKER}' and '{_SECTION_END_MARKER}' markers to your file."
            )

        # Validate marker order
        if start_idx > end_idx:
            raise ValueError(
                f"Start marker '{_SECTION_START_MARKER}' must appear before end marker '{_SECTION_END_MARKER}'."
            )

        # Calculate positions for content replacement
        # Content after start marker (skip newlines to insert after them)
        after_start = start_idx + len(_SECTION_START_MARKER)
        while after_start < len(content) and content[after_start] in "\r\n":
            after_start += 1

        # Content before end marker (include the newline before the end marker)
        before_end = end_idx
        # Include any newlines immediately before the end marker for proper formatting
        while before_end > after_start and content[before_end - 1] in "\r\n":
            before_end -= 1

        # Build new content: keep everything up to after_start (incl. newlines),
        # add img tag with newline if needed, then keep everything from before_end
        # If before_end == after_start, the section was empty - add a newline
        img_with_newline = img_tag if before_end > after_start else img_tag + "\n"
        new_content = (
            content[:after_start] +
            img_with_newline +
            content[before_end:]
        )

        # Write back
        with open(self.path, "w") as f:
            f.write(new_content)
