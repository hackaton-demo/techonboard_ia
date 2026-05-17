import logging
from typing import Any

from github import Github, GithubException
from github.Organization import Organization

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GitHubClient:
    """Thin wrapper around PyGithub for TechOnboard operations."""

    def __init__(self) -> None:
        token = settings.GITHUB_TOKEN
        if token:
            self._gh = Github(token)
        else:
            logger.warning("GITHUB_TOKEN not set — GitHub features will be limited")
            self._gh = Github()  # unauthenticated (rate-limited)

    def _org(self) -> Organization:
        return self._gh.get_organization(settings.GITHUB_ORG)

    async def get_user_profile(self, username: str) -> dict[str, Any]:
        """Fetch public profile info for a GitHub user."""
        try:
            user = self._gh.get_user(username)
            repos = list(user.get_repos())
            languages: dict[str, int] = {}
            for repo in repos[:3]:  # 3 repos max to keep demo fast
                try:
                    for lang, bytes_count in repo.get_languages().items():
                        languages[lang] = languages.get(lang, 0) + bytes_count
                except Exception:
                    pass

            return {
                "username": user.login,
                "name": user.name,
                "bio": user.bio,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "company": user.company,
                "location": user.location,
                "top_languages": dict(
                    sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
                ),
                "recent_repos": [
                    {
                        "name": r.name,
                        "description": r.description,
                        "language": r.language,
                        "stars": r.stargazers_count,
                        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                    }
                    for r in sorted(repos, key=lambda r: r.updated_at or __import__("datetime").datetime.min, reverse=True)[:5]
                ],
            }
        except GithubException as exc:
            logger.error(f"GitHub get_user_profile failed for '{username}': {exc}")
            return {"username": username, "error": str(exc)}
        except Exception as exc:
            logger.error(f"Unexpected error fetching GitHub profile for '{username}': {exc}")
            return {"username": username, "error": str(exc)}

    async def invite_to_org(self, username: str, org: str | None = None) -> bool:
        """Invite a user to the GitHub org."""
        org_name = org or settings.GITHUB_ORG
        try:
            organization = self._gh.get_organization(org_name)
            user = self._gh.get_user(username)
            organization.invite_user(user)
            logger.info(f"Invited {username} to org {org_name}")
            return True
        except GithubException as exc:
            logger.error(f"Failed to invite {username} to org {org_name}: {exc}")
            return False
        except Exception as exc:
            logger.error(f"Unexpected error inviting {username} to org: {exc}")
            return False

    async def invite_to_repo(
        self, username: str, repo: str, permission: str = "pull"
    ) -> bool:
        """Add a collaborator to a repository with the given permission."""
        try:
            repo_obj = self._gh.get_repo(f"{settings.GITHUB_ORG}/{repo}")
            user = self._gh.get_user(username)
            repo_obj.add_to_collaborators(user, permission=permission)
            logger.info(f"Added {username} to {repo} with {permission} permission")
            return True
        except GithubException as exc:
            logger.error(f"Failed to add {username} to repo {repo}: {exc}")
            return False
        except Exception as exc:
            logger.error(f"Unexpected error adding {username} to repo: {exc}")
            return False

    async def get_user_repos(self, username: str) -> list[dict[str, Any]]:
        """Return a list of public repos for a user."""
        try:
            user = self._gh.get_user(username)
            return [
                {
                    "name": r.name,
                    "full_name": r.full_name,
                    "language": r.language,
                    "description": r.description,
                    "stars": r.stargazers_count,
                    "fork": r.fork,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in user.get_repos()
            ]
        except GithubException as exc:
            logger.error(f"Failed to get repos for {username}: {exc}")
            return []
        except Exception as exc:
            logger.error(f"Unexpected error getting repos for {username}: {exc}")
            return []
