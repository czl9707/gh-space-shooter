"""CLI interface for gh-space-shooter."""

import json
import os
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

from .animation_pipeline import encode_animation
from .constants import DEFAULT_FPS
from .console_printer import ContributionConsolePrinter
from .game.strategies import (
    DEFAULT_STRATEGY_NAME,
    create_strategy,
    supported_strategy_names,
)
from .game.strategies.base_strategy import BaseStrategy
from .github_client import ContributionData, GitHubAPIError, fetch_contribution_data
from .output import WebpDataUrlOutputProvider, supported_output_formats

# Load environment variables from .env file
load_dotenv()

console = Console()
err_console = Console(stderr=True)
SUPPORTED_OUTPUT_FORMATS_TEXT = ", ".join(supported_output_formats()).upper()


class CLIError(Exception):
    """Base exception for CLI errors with user-friendly messages."""
    pass


def main(
    username: str = typer.Argument(None, help="GitHub username to fetch data for"),
    raw_input: str = typer.Option(
        None,
        "--raw-input",
        "--raw-in",
        "-ri",
        help="Load contribution data from JSON file (skips GitHub API call)",
    ),
    raw_output: str = typer.Option(
        None,
        "--raw-output",
        "--raw-out",
        "-ro",
        help="Save contribution data to JSON file",
    ),
    out: str = typer.Option(
        None,
        "--output",
        "-out",
        "-o",
        help=f"Generate animated visualization ({SUPPORTED_OUTPUT_FORMATS_TEXT})",
    ),
    write_dataurl_to: str = typer.Option(
        None,
        "--write-dataurl-to",
        help="Generate WebP as data URL and write to text file",
    ),
    strategy: str = typer.Option(
        DEFAULT_STRATEGY_NAME,
        "--strategy",
        "-s",
        help=f"Strategy for clearing enemies ({', '.join(supported_strategy_names())})",
    ),
    fps: int = typer.Option(
        DEFAULT_FPS,
        "--fps",
        help="Frames per second for the animation",
    ),
    max_frames: int | None = typer.Option(
        None,
        "--max-frame",
        help="Maximum number of frames to generate",
    ),
    watermark: bool = typer.Option(
        False,
        "--watermark",
        help="Add watermark to the output animation",
    ),
) -> None:
    """
    Fetch or load GitHub contribution graph data and display it.

    You can either fetch fresh data from GitHub or load from a previously saved file.
    This is useful for saving API rate limits.

    Examples:
      # Fetch from GitHub and save
      gh-space-shooter czl9707 --raw-output data.json

      # Load from saved file
      gh-space-shooter --raw-input data.json
    """
    try:
        if not username:
            raise CLIError("Username is required")

        # Validate mutual exclusivity of output options
        if out and write_dataurl_to:
            raise CLIError(
                "Cannot specify both --output and --write-dataurl-to. Choose one."
            )
        if not out and not write_dataurl_to:
            out = f"{username}-gh-space-shooter.gif"

        # Load data from file or GitHub
        if raw_input:
            data = _load_data_from_file(raw_input)
        else:
            data = _load_data_from_github(username)

        # Display the data
        printer = ContributionConsolePrinter()
        printer.display_stats(data)
        printer.display_contribution_graph(data)

        # Save to file if requested
        if raw_output:
            _save_data_to_file(data, raw_output)

        # Generate output if requested
        if write_dataurl_to or out:
            output_path = write_dataurl_to or out
            provider = None
            if write_dataurl_to:
                provider = WebpDataUrlOutputProvider(output_path)
            
            _generate_output(data, output_path, strategy, fps, watermark, max_frames, provider)

    except CLIError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    except Exception as e:
        err_console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        sys.exit(1)


def _load_env_and_validate() -> str:
    """Load environment variables and validate required settings. Returns token."""
    token = os.getenv("GH_TOKEN")
    if not token:
        raise CLIError(
            "GitHub token not found. "
            "Set your GitHub token in the GH_TOKEN environment variable."
        )
    return token


def _load_data_from_file(file_path: str) -> ContributionData:
    """Load contribution data from a JSON file."""
    console.print(f"[bold blue]Loading data from {file_path}...[/bold blue]")
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise CLIError(f"File '{file_path}' not found")
    except json.JSONDecodeError as e:
        raise CLIError(f"Invalid JSON in '{file_path}': {e}")


def _load_data_from_github(username: str) -> ContributionData:
    """Fetch contribution data from GitHub API."""
    token = _load_env_and_validate()

    console.print(f"[bold blue]Fetching contribution data for {username}...[/bold blue]")
    try:
        return fetch_contribution_data(username, token)
    except GitHubAPIError as e:
        raise CLIError(f"GitHub API error: {e}")


def _save_data_to_file(data: ContributionData, file_path: str) -> None:
    """Save contribution data to a JSON file."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        console.print(f"\n[green]✓[/green] Data saved to {file_path}")
    except IOError as e:
        raise CLIError(f"Failed to save file '{file_path}': {e}")


def _generate_output(
    data: ContributionData,
    output_path: str,
    strategy_name: str,
    fps: int,
    watermark: bool,
    max_frames: int | None,
    provider: OutputProvider | None = None,
) -> None:
    """Generate animation in the format specified by output_path or provider."""
    # Warn about GIF FPS limitation
    if output_path.lower().endswith(".gif") and fps > 50:
        console.print(
            f"[yellow]Warning:[/yellow] FPS > 50 may not display correctly in browsers "
            f"(GIF delay will be {1000 // fps}ms, but browsers clamp delays < 20ms to ~100ms)"
        )

    if isinstance(provider, WebpDataUrlOutputProvider):
        console.print("\n[bold blue]Generating WebP data URL...[/bold blue]")
    else:
        ext = Path(output_path).suffix[1:].upper()
        console.print(f"\n[bold blue]Generating {ext} animation...[/bold blue]")

    # Resolve strategy
    strategy = _resolve_strategy(strategy_name)

    # Generate animation
    try:
        encoded = encode_animation(
            data=data,
            strategy=strategy,
            output_path=output_path,
            fps=fps,
            watermark=watermark,
            max_frames=max_frames,
            provider=provider,
        )

        if isinstance(provider, WebpDataUrlOutputProvider):
            # For data provider, we need to call write explicitly or let it handle it?
            # provider.encode returns bytes (data url string). 
            # We need to write it using the provider's write method which handles injection.
            console.print(f"[bold blue]Injecting into {output_path}...[/bold blue]")
            provider.write(encoded)
            console.print(f"[green]✓[/green] Data URL written to {output_path}")
        else:
            console.print(f"[bold blue]Saving to {output_path}...[/bold blue]")
            with open(output_path, "wb") as f:
                f.write(encoded)
            ext = Path(output_path).suffix[1:].upper()
            console.print(f"[green]✓[/green] {ext} saved to {output_path}")

    except Exception as e:
        raise CLIError(f"Failed to generate output: {e}")
    except Exception as e:
        raise CLIError(f"Failed to generate output: {e}")


def _resolve_strategy(strategy_name: str) -> BaseStrategy:
    try:
        return create_strategy(strategy_name)
    except ValueError as exc:
        raise CLIError(str(exc))


app = typer.Typer()
app.command()(main)

if __name__ == "__main__":
    app()
