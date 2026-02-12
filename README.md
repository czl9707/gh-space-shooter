# gh-space-shooter 🚀

Transform your GitHub contribution graph into an epic space shooter game! 

![Example Game](example.gif)

## Usage

### Onetime Generation

A [web interface](https://gh-space-shooter.kiyo-n-zane.com) is available for on-demand GIF generation without installing anything locally. 

### GitHub Action

Automatically update your game GIF daily using GitHub Actions! Add this workflow to your repository at `.github/workflows/update-game.yml`:

```yaml
name: Update Space Shooter Game

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
  workflow_dispatch:  # Allow manual trigger

permissions:
  contents: write

jobs:
  update-game:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: czl9707/gh-space-shooter@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          output-path: 'game.gif'
          # write-dataurl-to: 'README.md'   # for dataurl generation.
          strategy: 'random'
```

Then display it in your README:
```markdown
![My GitHub Game](game.gif)
```

**Action Inputs:**
- `github-token` (required): GitHub token for fetching contributions
- `username` (optional): Username to generate game for (defaults to repo owner)
- `output-path` (optional): Where to save the animation, supports `.gif` or `.webp` (default: `gh-space-shooter.gif`)
- `strategy` (optional): Attack pattern - `column`, `row`, or `random` (default: `random`)
- `fps` (optional): Frames per second for the animation (default: `40`)
- `write-dataurl-to` (optional): Write WebP as HTML `<img>` data URL to text file
- `commit-message` (optional): Commit message for the update

### From PyPI

```bash
pip install gh-space-shooter
```

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/gh-space-shooter.git
cd gh-space-shooter

# Install with uv
uv sync

# Or with pip
pip install -e .
```

## Setup

1. Create a GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `read:user`
   - Copy the generated token

2. Set up your environment:
   ```bash
   # Copy the example env file
   touch .env
   echo "GH_TOKEN=your_token_here" >> .env
   ```

   Alternatively, export the token directly:
   ```bash
   export GH_TOKEN=your_token_here
   ```

## CLI Usage

### Generate Your Game Animation (GIF or WebP)

Transform your GitHub contributions into an epic space shooter!

```bash
# Basic usage - generates username-gh-space-shooter.gif
gh-space-shooter <username>

# Examples
gh-space-shooter torvalds
gh-space-shooter octocat

# Specify custom output filename (GIF or WebP)
gh-space-shooter torvalds --output my-epic-game.gif
gh-space-shooter torvalds -o my-game.webp

# Choose enemy attack strategy
gh-space-shooter torvalds --strategy row      # Enemies attack in rows
gh-space-shooter torvalds -s random           # Random chaos (default)

# Adjust animation frame rate
gh-space-shooter torvalds --fps 25            # Lower Frame rate, Smaller file size
gh-space-shooter torvalds --fps 40            # Default Frame rate, Larger file size

# Stop the animation earlier
gh-space-shooter torvalds --max-frame 200     # Stop after 200 frames
```

This creates an animated GIF showing:
- Your contribution graph as enemies (more contributions = stronger enemies)
- A Galaga-style spaceship battling through your coding history
- Enemy attack patterns based on your chosen strategy
- Smooth animations with randomized particle effects
- Your contribution stats displayed in the console

### Generate Data URL (for embedding in HTML/Markdown)

For direct embedding in READMEs or HTML files, use `--write-dataurl-to` to generate a WebP data URL wrapped in an HTML `<img>` tag:

```bash
# Generate data URL and write to README.md
gh-space-shooter torvalds --write-dataurl-to README.md

# Short form
gh-space-shooter torvalds -wdt README.md
```

**Using section markers:** To use this feature, add section markers to your file where you want the game to appear:

```markdown
# My Profile

<!--START_SECTION:space-shooter-->
<!--END_SECTION:space-shooter-->

## About Me
```

This will:
- **Create new files** with content wrapped in section markers, if file not present.
- **Replace content** between existing markers (preserving surrounding content)
- **Raise error** if markers are missing or in wrong order (no silent fallback)

### Advanced Options

```bash
# Save raw contribution data to JSON
gh-space-shooter torvalds --raw-output data.json

# Load from previously saved JSON (saves API rate limits)
gh-space-shooter --raw-input data.json --output game.webp

# Combine options
gh-space-shooter torvalds -o game.webp -ro data.json -s column

# Generate data URL with custom strategy
gh-space-shooter torvalds -wdt README.md -s column
```

### Data Format

When saved to JSON, the data includes:
```json
{
  "username": "torvalds",
  "total_contributions": 1234,
  "weeks": [
    {
      "days": [
        {
          "date": "2024-01-01",
          "count": 5,
          "level": 2
        }
      ]
    }
  ]
}
```

## License

MIT
