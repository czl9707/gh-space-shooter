"""FastAPI web app for gh-space-shooter GIF generation."""

import os
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, Response
# from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from gh_space_shooter.game import Animator, ColumnStrategy, RandomStrategy, RowStrategy, BaseStrategy
from gh_space_shooter.github_client import GitHubAPIError, GitHubClient

load_dotenv()

app = FastAPI(title="GitHub Space Shooter")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
# app.mount("/public", StaticFiles(directory=Path(__file__).parent / "public"), name="public")


STRATEGY_MAP: dict[str, type[BaseStrategy]] = {
    "column": ColumnStrategy,
    "row": RowStrategy,
    "random": RandomStrategy,
}


def generate_gif(username: str, strategy: str, token: str) -> BytesIO:
    """Generate a space shooter GIF for a GitHub user."""
    with GitHubClient(token) as client:
        data = client.get_contribution_graph(username)

    strategy_class: type[BaseStrategy] = STRATEGY_MAP.get(strategy, RandomStrategy)
    strat = strategy_class()

    animator = Animator(data, strat, fps=20, watermark=True)
    return animator.generate_gif(maxFrame=250)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main page."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/generate")
async def generate(
    username: str = Query(..., min_length=1, description="GitHub username"),
    strategy: str = Query("random", description="Animation strategy"),
):
    """Generate and return a space shooter GIF."""
    token = os.getenv("GH_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    if strategy not in STRATEGY_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy. Choose from: {', '.join(STRATEGY_MAP.keys())}",
        )

    try:
        gif_buffer = generate_gif(username, strategy, token)
        return Response(
            content=gif_buffer.getvalue(),
            media_type="image/gif",
            headers={
                "Response-Type": "blob",
                "Content-Disposition": f"inline; filename={username}-space-shooter.gif"
            },
        )
    except GitHubAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate GIF: {e}")
