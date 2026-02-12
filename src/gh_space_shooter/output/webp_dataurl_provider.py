"""WebP data URL output provider."""

import base64
import os
from io import BytesIO
from typing import Iterator
from PIL import Image
from .base import OutputProvider


# Marker to search for in files for injection mode
_MARKER = "<!-- space-shooter -->"


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
                lossless=True,
                quality=100,
                method=4,
            )

            # Convert to data URL
            webp_bytes = buffer.getvalue()
            base64_data = base64.b64encode(webp_bytes).decode("ascii")
            data_url = f"data:image/webp;base64,{base64_data}"

        # Return data URL as bytes
        return data_url.encode("utf-8")

    def write(self, data: bytes) -> None:
        """
        Write data URL to file as an HTML img tag with injection or append mode.

        This handles text mode properly with newlines.

        Args:
            data: Data URL as bytes (will be decoded as UTF-8 text)
        """
        data_url = data.decode("utf-8")
        # Wrap in HTML img tag
        img_tag = f'<img src="{data_url}" />'

        # Try to create new file exclusively (avoids TOCTOU race condition)
        try:
            with open(self.path, "x") as f:
                f.write(img_tag + "\n")
            return
        except FileExistsError:
            # File exists - read contents
            with open(self.path, "r") as f:
                content = f.read()

        # Check for marker
        if _MARKER in content:
            # Injection mode: replace the line containing the marker
            lines = content.splitlines(keepends=True)
            for i, line in enumerate(lines):
                if _MARKER in line:
                    lines[i] = img_tag + "\n"
                    break
            content = "".join(lines)
        else:
            # Append mode: add to end
            if content and not content.endswith("\n"):
                content += "\n"
            content += img_tag + "\n"

        # Write back
        with open(self.path, "w") as f:
            f.write(content)
