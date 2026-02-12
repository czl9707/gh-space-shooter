# gh-space-shooter Web App

A FastAPI web application that provides on-demand GitHub Space Shooter animation generation through a browser interface.

## Features

- Web UI for generating animations without CLI installation
- Select GitHub username and animation strategy (random, column, row)
- Choose output format: GIF, WebP, or SVG
- Download generated animations directly
- Share functionality for supported browsers

## Setup

1. Install dependencies:
   ```bash
   cd app
   uv sync
   ```

2. Set up environment:
   ```bash
   export GH_TOKEN=your_github_token
   # Or create a .env file with GH_TOKEN=your_token
   ```

## Running Locally

```bash
uv run --project gh-space-shooter-app uvicorn main:app
```

The app will be available at `http://localhost:8000`.

## API Endpoints

- `GET /` - Web UI for generating animations
- `GET /api/generate?username=<username>&strategy=<strategy>&format=<format>` - Generate and return an animation
  - `username` (required): GitHub username
  - `strategy` (optional): Animation strategy - `random`, `column`, or `row` (default: `random`)
  - `format` (optional): Output format - `gif`, `webp`, or `svg` (default: `gif`)

## Project Structure

```
app/
├── src/
│   ├── main.py           # FastAPI application
│   └── templates/
│       └── index.html    # Web UI template
├── public/
│   └── favicon.ico
├── pyproject.toml
└── README.md
```
