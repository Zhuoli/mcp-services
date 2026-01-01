"""Data models for Code Repos MCP server."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings


class ReposSettings(BaseSettings):
    """Settings from environment variables."""

    model_config = ConfigDict(env_prefix="", case_sensitive=False)

    repos_config_path: str = "./config/repos.yaml"


@dataclass
class RepoInfo:
    """Repository information."""

    name: str
    path: str
    description: str
    tags: list[str] = field(default_factory=list)
    url: Optional[str] = None
    default_branch: str = "main"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "description": self.description,
            "tags": self.tags,
            "url": self.url,
            "default_branch": self.default_branch,
            "exists": Path(self.path).exists(),
        }


class ReposConfig:
    """Configuration loader for code repositories."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize repos configuration.

        Args:
            config_path: Path to repos.yaml config file
        """
        settings = ReposSettings()
        self.config_path = Path(config_path or settings.repos_config_path)
        self._repos: list[RepoInfo] = []
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)

        self._repos = []
        for repo_data in data.get("repositories", []):
            repo = RepoInfo(
                name=repo_data.get("name", ""),
                path=repo_data.get("path", ""),
                description=repo_data.get("description", ""),
                tags=repo_data.get("tags", []),
                url=repo_data.get("url"),
                default_branch=repo_data.get("default_branch", "main"),
            )
            self._repos.append(repo)

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()

    @property
    def repos(self) -> list[RepoInfo]:
        """Get all repositories."""
        return self._repos

    def get_repo(self, name: str) -> Optional[RepoInfo]:
        """Get a repository by name."""
        for repo in self._repos:
            if repo.name.lower() == name.lower():
                return repo
        return None

    def search_repos(
        self,
        query: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> list[RepoInfo]:
        """
        Search repositories by name, description, or tags.

        Args:
            query: Text to search in name and description
            tags: Tags to filter by (any match)

        Returns:
            List of matching RepoInfo objects
        """
        results = self._repos

        if query:
            query_lower = query.lower()
            results = [
                r for r in results
                if query_lower in r.name.lower() or query_lower in r.description.lower()
            ]

        if tags:
            tags_lower = [t.lower() for t in tags]
            results = [
                r for r in results
                if any(t.lower() in tags_lower for t in r.tags)
            ]

        return results

    def get_all_tags(self) -> list[str]:
        """Get all unique tags across all repositories."""
        tags = set()
        for repo in self._repos:
            tags.update(repo.tags)
        return sorted(tags)
