# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

```bash
# Install dependencies (uses uv package manager)
uv sync

# Install with dev dependencies
uv sync --extra dev

# Run the CLI
uv run gh-space-shooter <username>

# Run tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_strategies.py -v

# Run a specific test
uv run pytest tests/test_strategies.py::test_column_strategy -v

# Run the web app (from app/ directory)
uv run --project gh-space-shooter-app uvicorn main:app
```

## Environment Setup

Requires a GitHub Personal Access Token with `read:user` scope:
```bash
export GH_TOKEN=your_token_here
# Or create a .env file with GH_TOKEN=your_token
```

## Project Context

**Current main usage**: GitHub Action that automatically updates a game GIF in user repositories daily (see `.github/workflows/` for the action definition).

**Web App**: A FastAPI-based web application is available in the `app/` directory for on-demand GIF generation. See `app/README.md` for details.

## Architecture Overview

This is a CLI tool that transforms GitHub contribution graphs into animated space shooter GIFs using Pillow.

### Core Flow

1. **CLI (`cli.py`)** - Typer-based entry point that orchestrates the pipeline
2. **GitHubClient (`github_client.py`)** - Fetches contribution data via GitHub GraphQL API, returns typed `ContributionData` dict
3. **Animator (`game/animator.py`)** - Main game loop that coordinates strategy execution and frame generation
4. **GameState (`game/game_state.py`)** - Central state container holding ship, enemies, bullets, explosions
5. **Renderer (`game/renderer.py`)** - Converts GameState to PIL Images each frame

### Strategy Pattern

Strategies (`game/strategies/`) define how the ship clears enemies:

- `BaseStrategy` - Abstract base defining `generate_actions(game_state) -> Iterator[Action]`
- `ColumnStrategy` - Clears enemies column by column (left to right)
- `RowStrategy` - Clears enemies row by row (top to bottom)
- `RandomStrategy` - Targets enemies in random order

Strategies yield `Action(x, shoot)` objects. The Animator processes these: moving the ship to position `x`, waiting for movement/cooldown to complete, then shooting if `shoot=True`.

### Drawable System

All game objects inherit from `Drawable` (`game/drawables/drawable.py`):

- `animate(delta_time)` - Update state (position, cooldowns, particles)
- `draw(draw, context)` - Render to PIL ImageDraw

Drawables: `Ship`, `Enemy`, `Bullet`, `Explosion`, `Starfield`

The `RenderContext` (`game/render_context.py`) holds theming (colors, cell sizes, padding) and coordinate conversion helpers.

### Animation Loop

In `Animator._generate_frames()`:

1. Strategy yields next action
2. Ship moves to target x position (animate frames until arrived)
3. Ship shoots if action.shoot (animate frames for bullet travel + explosions)
4. Repeat until all enemies destroyed

Frame rate is configurable (default 40 FPS). All speeds use delta_time for frame-rate independence.

### Key Constants (`constants.py`)

- `NUM_WEEKS = 52` - Contribution graph width
- `NUM_DAYS = 7` - Contribution graph height
- Speeds are in cells/second, durations in seconds
