"""FastAPI web app for gh-space-shooter animation generation."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, Response
# from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from gh_space_shooter.animation_pipeline import encode_animation
from gh_space_shooter.game.strategies import (
    DEFAULT_STRATEGY_NAME,
    create_strategy,
    BaseStrategy,
)
from gh_space_shooter.github_client import GitHubAPIError, fetch_contribution_data
from gh_space_shooter.output import (
    media_type_for_output_format,
    output_path_for_format,
)

load_dotenv()

app = FastAPI(title="GitHub Space Shooter")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
# app.mount("/public", StaticFiles(directory=Path(__file__).parent / "public"), name="public")

def generate_output(
    username: str,
    strategy: BaseStrategy,
    token: str,
    output_path: str,
) -> bytes:
    """Generate a space shooter animation for a GitHub user."""
    data = fetch_contribution_data(username, token)

<<<<<<< HEAD
    strategy_class: type[BaseStrategy] = STRATEGY_MAP.get(strategy, RandomStrategy)
    strat = strategy_class()

    animator = Animator(data, strat, fps=25, watermark=True)
    provider = GifOutputProvider("dummy.gif")
    encoded = provider.encode(animator.generate_frames(max_frames=250), frame_duration=1000 // 25)
    return encoded
=======
    return encode_animation(
        data=data,
        strategy=strategy,
        output_path=output_path,
        fps=25,
        watermark=True,
        max_frames=250,
    )
>>>>>>> 6d86ba6 (chore: update cli and app for new pipeline)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main page."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/generate")
async def generate(
    username: str = Query(..., min_length=1, description="GitHub username"),
    strategy: str = Query(DEFAULT_STRATEGY_NAME, description="Animation strategy"),
    output_format: str = Query(
        "gif", alias="format", description="Output format: gif, webp, or svg"
    ),
):
    """Generate and return a space shooter animation."""
    token = os.getenv("GH_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    try:
        strategy_instance = create_strategy(strategy)
        output_path = output_path_for_format(output_format)
        media_type = media_type_for_output_format(output_format)
        encoded = generate_output(username, strategy_instance, token, output_path)
        return Response(
            content=encoded,
            media_type=media_type,
            headers={
                "Response-Type": "blob",
                "Content-Disposition": (
                    f"inline; filename={username}-space-shooter.{output_format}"
                ),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GitHubAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate animation: {e}")
