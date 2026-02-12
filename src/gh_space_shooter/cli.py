"""CLI interface for gh-space-shooter."""

import json
import os
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

from .constants import DEFAULT_FPS
from .console_printer import ContributionConsolePrinter
from .game import Animator, ColumnStrategy, RandomStrategy, RowStrategy, BaseStrategy
from .github_client import ContributionData, GitHubAPIError, GitHubClient
from .output import resolve_output_provider
from .output import OutputProvider, WebpDataUrlOutputProvider

# Load environment variables from .env file
load_dotenv()

console = Console()
err_console = Console(stderr=True)


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
        help="Generate animated visualization (GIF or WebP)",
    ),
    write_dataurl_to: str = typer.Option(
        None,
        "--write-dataurl-to",
        help="Generate WebP as data URL and write to text file",
    ),
    strategy: str = typer.Option(
        "random",
        "--strategy",
        "-s",
        help="Strategy for clearing enemies (column, row, random)",
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
        help="Add watermark to the GIF",
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
            provider = _resolve_provider(output_path, bool(write_dataurl_to))
            _generate_output(data, provider, strategy, fps, watermark, max_frames)

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
        with GitHubClient(token) as client:
            return client.get_contribution_graph(username)
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


def _resolve_provider(file_path: str, is_dataurl: bool) -> OutputProvider:
    """
    Resolve the appropriate output provider based on file path and mode.
    """
    try:
        if is_dataurl:
            return WebpDataUrlOutputProvider(file_path)
        else:
            return resolve_output_provider(file_path)
    except ValueError as e:
        raise CLIError(str(e))


def _setup_animator(strategy_name: str, data: ContributionData, fps: int, watermark: bool) -> Animator:
    """
    Set up strategy and animator.
    """
    if strategy_name == "column":
        strategy: BaseStrategy = ColumnStrategy()
    elif strategy_name == "row":
        strategy = RowStrategy()
    elif strategy_name == "random":
        strategy = RandomStrategy()
    else:
        raise CLIError(
            f"Unknown strategy '{strategy_name}'. Available: column, row, random"
        )

    return Animator(data, strategy, fps=fps, watermark=watermark)


def _generate_output(
    data: ContributionData,
    provider: OutputProvider,
    strategy_name: str,
    fps: int,
    watermark: bool,
    max_frames: int | None,
) -> None:
    """
    Generate output using the provided provider.

    Args:
        data: Contribution data from GitHub
        provider: Output provider (already resolved with path)
        strategy_name: Name of the strategy (column, row, random)
        fps: Frames per second
        watermark: Whether to add watermark
        max_frames: Maximum number of frames to generate

    Raises:
        CLIError: If output generation fails
    """
    # Warn about GIF FPS limitation
    if provider.path.endswith(".gif") and fps > 50:
        console.print(
            f"[yellow]Warning:[/yellow] FPS > 50 may not display correctly in browsers "
            f"(GIF delay will be {1000 // fps}ms, but browsers clamp delays < 20ms to ~100ms)"
        )

    # Print generation message
    if isinstance(provider, WebpDataUrlOutputProvider):
        console.print("\n[bold blue]Generating WebP data URL...[/bold blue]")
    else:
        ext = Path(provider.path).suffix[1:].upper()
        console.print(f"\n[bold blue]Generating {ext} animation...[/bold blue]")

    # Setup strategy and animator
    animator = _setup_animator(strategy_name, data, fps, watermark)

    # Encode and write
    try:
        encoded = provider.encode(animator.generate_frames(max_frames), 1000 // fps)
        provider.write(encoded)

        # Console output based on provider type
        if isinstance(provider, WebpDataUrlOutputProvider):
            console.print(f"[green]✓[/green] Data URL written to {provider.path}")
        else:
            ext = Path(provider.path).suffix[1:].upper()
            console.print(f"[green]✓[/green] {ext} saved to {provider.path}")
    except Exception as e:
        raise CLIError(f"Failed to generate output: {e}")


app = typer.Typer()
app.command()(main)

if __name__ == "__main__":
    app()
