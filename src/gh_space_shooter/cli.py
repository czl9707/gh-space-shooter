"""CLI interface for gh-space-shooter."""

import json
import os
import re
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console

from .constants import DEFAULT_FPS
from .game.strategies.base_strategy import BaseStrategy
from .console_printer import ContributionConsolePrinter
from .game import Animator, ColumnStrategy, RandomStrategy, RowStrategy
from .github_client import ContributionData, GitHubAPIError, GitHubClient

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
        help="Generate animated GIF visualization",
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
    maxFrame: int | None = typer.Option(
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
            raise CLIError("Username is required when not using --raw-input")
        if not out:
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

        # Generate GIF if requested
        _generate_gif(data, out, strategy, fps, watermark, maxFrame)

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


def _generate_gif(
    data: ContributionData, 
    file_path: str, 
    strategy_name: str, 
    fps: int, 
    watermark: bool, 
    maxFrame: int | None
) -> None:
    """Generate animated GIF visualization."""
    # GIF format limitation: delays below 20ms (>50 FPS) are clamped by most browsers
    if fps > 50:
        console.print(
            f"[yellow]Warning:[/yellow] FPS > 50 may not display correctly in browsers "
            f"(GIF delay will be {1000 // fps}ms, but browsers clamp delays < 20ms to ~100ms)"
        )
    console.print("\n[bold blue]Generating GIF animation...[/bold blue]")

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

    # Create animator and generate GIF
    try:
        animator = Animator(data, strategy, fps=fps, watermark=watermark)
        buffer = animator.generate_gif(maxFrame=maxFrame)
        console.print("[bold blue]Saving GIF animation...[/bold blue]")
        with open(file_path, "wb") as f:
            f.write(buffer.getvalue())

        console.print(f"[green]✓[/green] GIF saved to {file_path}")

        # if README.md has the shooter section markers, insert the image.
        _maybe_update_readme_with_gif(file_path)
    except Exception as e:
        raise CLIError(f"Failed to generate GIF: {e}")


def _maybe_update_readme_with_gif(gif_path: str) -> None:
    """If README.md at repo root contains shooter markers, replace the section with an image tag."""

    repo_root = Path(os.getenv("GITHUB_WORKSPACE") or os.getcwd()).resolve()
    readme_path = repo_root / "README.md"
    if not readme_path.is_file():
        return

    try:
        content = readme_path.read_text(encoding="utf-8")
    except OSError:
        return

    pattern = re.compile(
        r"(<!--START_SECTION:shooter-->)(.*?)(<!--END_SECTION:shooter-->)",
        flags=re.DOTALL,
    )

    match = pattern.search(content)
    if not match:
        return

    # The GIF can be anywhere; link it relative to the repo root and normalize for Markdown.
    try:
        gif_rel = os.path.relpath(Path(gif_path).resolve(), start=repo_root)
    except ValueError:
        gif_rel = Path(gif_path).name

    gif_rel = Path(gif_rel).as_posix()
    replacement = (
        f"{match.group(1)}\n"
        f"![GitHub Space Shooter]({gif_rel})\n"
        f"{match.group(3)}"
    )

    new_content = content[: match.start()] + replacement + content[match.end() :]
    if new_content == content:
        return

    try:
        readme_path.write_text(new_content, encoding="utf-8")
        console.print(f"[green]✓[/green] Updated {readme_path.name} shooter section")
    except OSError:
        return


app = typer.Typer()
app.command()(main)

if __name__ == "__main__":
    app()
