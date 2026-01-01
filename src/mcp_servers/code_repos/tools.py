"""Tool implementations for Code Repos MCP server."""

import logging
import os
from pathlib import Path
from typing import Any, Optional

from ..common.base_server import format_error, format_result
from .models import ReposConfig

logger = logging.getLogger(__name__)

# Cache for config to avoid reloading on every call
_config_cache: Optional[ReposConfig] = None


def _get_config() -> ReposConfig:
    """Get repos configuration, loading from file if needed."""
    global _config_cache

    config_path = os.environ.get("REPOS_CONFIG_PATH")
    if _config_cache is None:
        _config_cache = ReposConfig(config_path)

    return _config_cache


async def list_repos_tool(arguments: dict[str, Any]) -> str:
    """List all configured repositories."""
    include_details = arguments.get("include_details", True)

    try:
        config = _get_config()
        repos = config.repos

        if include_details:
            result = {
                "count": len(repos),
                "repositories": [repo.to_dict() for repo in repos],
                "all_tags": config.get_all_tags(),
            }
        else:
            result = {
                "count": len(repos),
                "repositories": [
                    {"name": repo.name, "description": repo.description}
                    for repo in repos
                ],
            }

        return format_result(result)
    except Exception as e:
        return format_error(e, "list_repos")


async def get_repo_info_tool(arguments: dict[str, Any]) -> str:
    """Get detailed information about a specific repository."""
    name = arguments["name"]

    try:
        config = _get_config()
        repo = config.get_repo(name)

        if repo:
            repo_dict = repo.to_dict()

            # Add additional info if the repo exists locally
            repo_path = Path(repo.path)
            if repo_path.exists():
                # Check for common files
                repo_dict["has_readme"] = (repo_path / "README.md").exists()
                repo_dict["has_package_json"] = (repo_path / "package.json").exists()
                repo_dict["has_pyproject"] = (repo_path / "pyproject.toml").exists()
                repo_dict["has_cargo"] = (repo_path / "Cargo.toml").exists()
                repo_dict["has_go_mod"] = (repo_path / "go.mod").exists()

                # Detect project type
                if repo_dict["has_pyproject"]:
                    repo_dict["project_type"] = "python"
                elif repo_dict["has_package_json"]:
                    repo_dict["project_type"] = "javascript/typescript"
                elif repo_dict["has_cargo"]:
                    repo_dict["project_type"] = "rust"
                elif repo_dict["has_go_mod"]:
                    repo_dict["project_type"] = "go"
                else:
                    repo_dict["project_type"] = "unknown"

            return format_result({
                "success": True,
                "repository": repo_dict,
            })
        else:
            return format_result({
                "success": False,
                "error": f"Repository not found: {name}",
                "available_repos": [r.name for r in config.repos],
            })
    except Exception as e:
        return format_error(e, "get_repo_info")


async def search_repos_tool(arguments: dict[str, Any]) -> str:
    """Search repositories by query or tags."""
    query = arguments.get("query")
    tags = arguments.get("tags", [])

    if not query and not tags:
        return format_result({
            "success": False,
            "error": "Either query or tags must be provided",
        })

    try:
        config = _get_config()
        repos = config.search_repos(query=query, tags=tags)

        return format_result({
            "query": query,
            "tags": tags,
            "count": len(repos),
            "repositories": [repo.to_dict() for repo in repos],
        })
    except Exception as e:
        return format_error(e, "search_repos")


async def get_repo_structure_tool(arguments: dict[str, Any]) -> str:
    """Get the directory structure of a repository."""
    name = arguments["name"]
    max_depth = arguments.get("max_depth", 2)
    include_hidden = arguments.get("include_hidden", False)

    try:
        config = _get_config()
        repo = config.get_repo(name)

        if not repo:
            return format_result({
                "success": False,
                "error": f"Repository not found: {name}",
            })

        repo_path = Path(repo.path)
        if not repo_path.exists():
            return format_result({
                "success": False,
                "error": f"Repository path does not exist: {repo.path}",
            })

        def get_structure(path: Path, current_depth: int = 0) -> dict[str, Any]:
            """Recursively get directory structure."""
            if current_depth > max_depth:
                return {"name": path.name, "type": "directory", "truncated": True}

            items = []
            try:
                for item in sorted(path.iterdir()):
                    if not include_hidden and item.name.startswith("."):
                        continue

                    if item.is_dir():
                        if item.name in ["node_modules", "__pycache__", ".git", "venv", ".venv"]:
                            items.append({
                                "name": item.name,
                                "type": "directory",
                                "skipped": True,
                            })
                        else:
                            items.append(get_structure(item, current_depth + 1))
                    else:
                        items.append({
                            "name": item.name,
                            "type": "file",
                            "size": item.stat().st_size,
                        })
            except PermissionError:
                return {"name": path.name, "type": "directory", "permission_denied": True}

            return {
                "name": path.name,
                "type": "directory",
                "children": items,
            }

        structure = get_structure(repo_path)

        return format_result({
            "success": True,
            "repository": repo.name,
            "path": repo.path,
            "max_depth": max_depth,
            "structure": structure,
        })
    except Exception as e:
        return format_error(e, "get_repo_structure")


async def reload_config_tool(arguments: dict[str, Any]) -> str:
    """Reload the repositories configuration from file."""
    global _config_cache

    try:
        _config_cache = None
        config = _get_config()

        return format_result({
            "success": True,
            "message": "Configuration reloaded successfully",
            "repo_count": len(config.repos),
            "config_path": str(config.config_path),
        })
    except Exception as e:
        return format_error(e, "reload_config")
