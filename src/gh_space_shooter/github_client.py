"""GitHub API client for fetching contribution graph data."""

from typing import TypedDict

import httpx

from .constants import NUM_WEEKS


class ContributionDay(TypedDict):
    """Represents a single day's contribution data."""

    date: str
    count: int
    level: int  # 0-4 intensity level


class ContributionWeek(TypedDict):
    """Represents a week of contribution data."""

    days: list[ContributionDay]


class ContributionData(TypedDict):
    """Complete contribution graph data."""

    username: str
    total_contributions: int
    weeks: list[ContributionWeek]


class GitHubAPIError(Exception):
    """Raised when GitHub API request fails."""

    pass


class GitHubClient:
    """Client for interacting with GitHub's GraphQL API."""

    GITHUB_API_URL = "https://api.github.com/graphql"
    GET_CONTRIBUTION_GRAPH_QUERY = """
        query($username: String!) {
            user(login: $username) {
            contributionsCollection {
                contributionCalendar {
                totalContributions
                weeks {
                    contributionDays {
                    date
                    contributionCount
                    contributionLevel
                    }
                }
                }
            }
            }
        }
    """

    def __init__(self, token: str):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token (required).
        """
        self.token = token
        self.client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close HTTP client."""
        self.close()

    def close(self):
        self.client.close()

    def get_contribution_graph(self, username: str) -> ContributionData:
        """
        Fetch contribution graph for a GitHub user (last 52 weeks).

        Args:
            username: GitHub username to fetch data for

        Returns:
            ContributionData with user's contribution information

        Raises:
            GitHubAPIError: If the API request fails
        """

        try:
            response = self.client.post(
                self.GITHUB_API_URL,
                json={
                    "query": self.GET_CONTRIBUTION_GRAPH_QUERY, 
                    "variables": {"username": username}
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise GitHubAPIError(f"Failed to fetch data from GitHub API: {e}") from e

        data = response.json()

        # Check for GraphQL errors
        if "errors" in data:
            errors = data["errors"]
            error_messages = [error.get("message", str(error)) for error in errors]
            raise GitHubAPIError(', '.join(error_messages))

        # Check if user exists
        if not data.get("data", {}).get("user"):
            raise GitHubAPIError(f"User '{username}' not found")

        # Extract contribution data
        calendar = data["data"]["user"]["contributionsCollection"][
            "contributionCalendar"
        ]

        # Parse weeks and days
        weeks: list[ContributionWeek] = []
        for week_data in calendar["weeks"]:
            days: list[ContributionDay] = []
            for day_data in week_data["contributionDays"]:
                days.append(
                    {
                        "date": day_data["date"],
                        "count": day_data["contributionCount"],
                        "level": self._contribution_level_to_int(
                            day_data["contributionLevel"]
                        ),
                    }
                )
            weeks.append({"days": days})

        # Always return exactly NUM_WEEKS (truncate if more)
        weeks = weeks[-NUM_WEEKS:] if len(weeks) > NUM_WEEKS else weeks

        return {
            "username": username,
            "total_contributions": calendar["totalContributions"],
            "weeks": weeks,
        }

    LEVEL_MAP = {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4,
    }

    def _contribution_level_to_int(self, level: str) -> int:
        return self.LEVEL_MAP.get(level, 0)


def fetch_contribution_data(username: str, token: str) -> ContributionData:
    """Fetch contribution graph data using a short-lived API client."""
    with GitHubClient(token) as client:
        return client.get_contribution_graph(username)
