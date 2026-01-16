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
          strategy: 'random'
```

Then display it in your README:

```markdown
![My GitHub Game](game.gif)
```

Or add these markers to let the tool automatically insert the image tag
if it finds them:

```markdown
<!--START_SECTION:shooter-->
<!--END_SECTION:shooter-->
```

**Action Inputs:**

- `github-token` (required): GitHub token for fetching contributions
- `username` (optional): Username to generate game for (defaults to repo owner)
- `output-path` (optional): Where to save the GIF (default: `gh-space-shooter.gif`)
- `strategy` (optional): Attack pattern - `column`, `row`, or `random` (default: `random`)
- `fps` (optional): Frames per second for the animation (default: `40`)
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
   - Go to <https://github.com/settings/tokens>
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

### Generate Your Game GIF

Transform your GitHub contributions into an epic space shooter!

```bash
# Basic usage - generates username-gh-space-shooter.gif
gh-space-shooter <username>

# Examples
gh-space-shooter torvalds
gh-space-shooter octocat

# Specify custom output filename
gh-space-shooter torvalds --output my-epic-game.gif
gh-space-shooter torvalds -o my-game.gif

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

### Advanced Options

```bash
# Save raw contribution data to JSON
gh-space-shooter torvalds --raw-output data.json

# Load from previously saved JSON (saves API rate limits)
gh-space-shooter --raw-input data.json --output game.gif

# Combine options
gh-space-shooter torvalds -o game.gif -ro data.json -s column
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
