"""Unit tests for Code Repos MCP server."""

import json
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_servers.code_repos import tools
from mcp_servers.code_repos.models import RepoInfo, ReposConfig


class TestReposConfig:
    """Tests for ReposConfig class."""

    def test_empty_config(self):
        """Test ReposConfig with no config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "repos.yaml")
            config = ReposConfig(config_path)

            assert config.repos == []
            assert config.get_all_tags() == []

    def test_load_config(self):
        """Test loading config from YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "repos.yaml")

            # Create test config
            with open(config_path, "w") as f:
                f.write("""
repositories:
  - name: test-repo
    path: /path/to/repo
    description: Test repository
    tags: [python, api]
    default_branch: main
""")

            config = ReposConfig(config_path)

            assert len(config.repos) == 1
            assert config.repos[0].name == "test-repo"
            assert config.repos[0].path == "/path/to/repo"
            assert "python" in config.repos[0].tags

    def test_get_repo(self):
        """Test getting a specific repo by name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "repos.yaml")

            with open(config_path, "w") as f:
                f.write("""
repositories:
  - name: test-repo
    path: /path/to/repo
    description: Test repository
""")

            config = ReposConfig(config_path)
            repo = config.get_repo("test-repo")

            assert repo is not None
            assert repo.name == "test-repo"

            # Test non-existent repo
            repo = config.get_repo("nonexistent")
            assert repo is None

    def test_search_repos(self):
        """Test searching repos by query and tags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "repos.yaml")

            with open(config_path, "w") as f:
                f.write("""
repositories:
  - name: frontend-app
    path: /path/to/frontend
    description: React frontend application
    tags: [react, typescript, frontend]
  - name: backend-api
    path: /path/to/backend
    description: Python API backend
    tags: [python, api, backend]
  - name: shared-lib
    path: /path/to/shared
    description: Shared utilities
    tags: [python, shared]
""")

            config = ReposConfig(config_path)

            # Search by query
            results = config.search_repos(query="frontend")
            assert len(results) == 1
            assert results[0].name == "frontend-app"

            # Search by tags
            results = config.search_repos(tags=["python"])
            assert len(results) == 2

            # Search by both
            results = config.search_repos(query="api", tags=["python"])
            assert len(results) == 1
            assert results[0].name == "backend-api"

    def test_get_all_tags(self):
        """Test getting all unique tags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "repos.yaml")

            with open(config_path, "w") as f:
                f.write("""
repositories:
  - name: repo1
    path: /path/to/repo1
    tags: [python, api]
  - name: repo2
    path: /path/to/repo2
    tags: [python, frontend]
""")

            config = ReposConfig(config_path)
            tags = config.get_all_tags()

            assert "python" in tags
            assert "api" in tags
            assert "frontend" in tags
            assert len(tags) == 3


class TestRepoInfo:
    """Tests for RepoInfo class."""

    def test_to_dict(self):
        """Test RepoInfo to_dict method."""
        repo = RepoInfo(
            name="test-repo",
            path="/path/to/repo",
            description="Test repository",
            tags=["python", "api"],
            default_branch="main",
        )

        data = repo.to_dict()

        assert data["name"] == "test-repo"
        assert data["path"] == "/path/to/repo"
        assert data["description"] == "Test repository"
        assert "python" in data["tags"]
        assert data["default_branch"] == "main"


class TestListReposTool:
    """Tests for list_repos_tool."""

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_list_repos_with_details(self, mock_get_config):
        """Test list_repos_tool with details."""
        mock_config = MagicMock()
        mock_config.repos = [
            RepoInfo(
                name="test-repo",
                path="/path/to/repo",
                description="Test repository",
                tags=["python"],
            )
        ]
        mock_config.get_all_tags.return_value = ["python"]
        mock_get_config.return_value = mock_config

        result = await tools.list_repos_tool({"include_details": True})

        data = json.loads(result)
        assert data["count"] == 1
        assert data["repositories"][0]["name"] == "test-repo"
        assert "all_tags" in data

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_list_repos_without_details(self, mock_get_config):
        """Test list_repos_tool without details."""
        mock_config = MagicMock()
        mock_config.repos = [
            RepoInfo(
                name="test-repo",
                path="/path/to/repo",
                description="Test repository",
                tags=["python"],
            )
        ]
        mock_get_config.return_value = mock_config

        result = await tools.list_repos_tool({"include_details": False})

        data = json.loads(result)
        assert data["count"] == 1
        assert "name" in data["repositories"][0]
        assert "description" in data["repositories"][0]
        # Path should not be included without details
        assert "path" not in data["repositories"][0]


class TestGetRepoInfoTool:
    """Tests for get_repo_info_tool."""

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_get_repo_info_found(self, mock_get_config):
        """Test get_repo_info_tool when repo is found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock repo structure
            Path(tmpdir, "README.md").touch()
            Path(tmpdir, "pyproject.toml").touch()

            mock_config = MagicMock()
            mock_config.get_repo.return_value = RepoInfo(
                name="test-repo",
                path=tmpdir,
                description="Test repository",
                tags=["python"],
            )
            mock_get_config.return_value = mock_config

            result = await tools.get_repo_info_tool({"name": "test-repo"})

            data = json.loads(result)
            assert data["success"] is True
            assert data["repository"]["name"] == "test-repo"
            assert data["repository"]["has_readme"] is True
            assert data["repository"]["has_pyproject"] is True
            assert data["repository"]["project_type"] == "python"

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_get_repo_info_not_found(self, mock_get_config):
        """Test get_repo_info_tool when repo is not found."""
        mock_config = MagicMock()
        mock_config.get_repo.return_value = None
        mock_config.repos = [
            RepoInfo(name="other-repo", path="/path/to/other")
        ]
        mock_get_config.return_value = mock_config

        result = await tools.get_repo_info_tool({"name": "nonexistent"})

        data = json.loads(result)
        assert data["success"] is False
        assert "not found" in data["error"]
        assert "available_repos" in data

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_get_repo_info_detect_project_types(self, mock_get_config):
        """Test get_repo_info_tool project type detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test JavaScript/TypeScript detection
            Path(tmpdir, "package.json").touch()

            mock_config = MagicMock()
            mock_config.get_repo.return_value = RepoInfo(
                name="js-repo",
                path=tmpdir,
            )
            mock_get_config.return_value = mock_config

            result = await tools.get_repo_info_tool({"name": "js-repo"})

            data = json.loads(result)
            assert data["repository"]["project_type"] == "javascript/typescript"


class TestSearchReposTool:
    """Tests for search_repos_tool."""

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_search_repos_by_query(self, mock_get_config):
        """Test search_repos_tool with query."""
        mock_config = MagicMock()
        mock_config.search_repos.return_value = [
            RepoInfo(
                name="frontend-app",
                path="/path/to/frontend",
                description="React frontend",
                tags=["react"],
            )
        ]
        mock_get_config.return_value = mock_config

        result = await tools.search_repos_tool({"query": "frontend"})

        data = json.loads(result)
        assert data["count"] == 1
        assert data["query"] == "frontend"

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_search_repos_by_tags(self, mock_get_config):
        """Test search_repos_tool with tags."""
        mock_config = MagicMock()
        mock_config.search_repos.return_value = [
            RepoInfo(
                name="python-api",
                path="/path/to/api",
                tags=["python", "api"],
            )
        ]
        mock_get_config.return_value = mock_config

        result = await tools.search_repos_tool({"tags": ["python"]})

        data = json.loads(result)
        assert data["count"] == 1
        assert data["tags"] == ["python"]

    @pytest.mark.asyncio
    async def test_search_repos_no_params(self):
        """Test search_repos_tool without params."""
        result = await tools.search_repos_tool({})

        data = json.loads(result)
        assert data["success"] is False
        assert "query or tags" in data["error"]


class TestGetRepoStructureTool:
    """Tests for get_repo_structure_tool."""

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_get_repo_structure(self, mock_get_config):
        """Test get_repo_structure_tool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock repo structure
            src_dir = Path(tmpdir, "src")
            src_dir.mkdir()
            Path(src_dir, "main.py").touch()
            Path(tmpdir, "README.md").touch()

            mock_config = MagicMock()
            mock_config.get_repo.return_value = RepoInfo(
                name="test-repo",
                path=tmpdir,
            )
            mock_get_config.return_value = mock_config

            result = await tools.get_repo_structure_tool({
                "name": "test-repo",
                "max_depth": 2,
            })

            data = json.loads(result)
            assert data["success"] is True
            assert data["repository"] == "test-repo"
            assert "structure" in data

            # Check that structure contains expected items
            structure = data["structure"]
            assert structure["type"] == "directory"
            child_names = [c["name"] for c in structure["children"]]
            assert "README.md" in child_names
            assert "src" in child_names

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_get_repo_structure_not_found(self, mock_get_config):
        """Test get_repo_structure_tool when repo not found."""
        mock_config = MagicMock()
        mock_config.get_repo.return_value = None
        mock_get_config.return_value = mock_config

        result = await tools.get_repo_structure_tool({"name": "nonexistent"})

        data = json.loads(result)
        assert data["success"] is False
        assert "not found" in data["error"]

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_get_repo_structure_path_not_exists(self, mock_get_config):
        """Test get_repo_structure_tool when path doesn't exist."""
        mock_config = MagicMock()
        mock_config.get_repo.return_value = RepoInfo(
            name="test-repo",
            path="/nonexistent/path",
        )
        mock_get_config.return_value = mock_config

        result = await tools.get_repo_structure_tool({"name": "test-repo"})

        data = json.loads(result)
        assert data["success"] is False
        assert "does not exist" in data["error"]

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_get_repo_structure_skips_common_dirs(self, mock_get_config):
        """Test that get_repo_structure_tool skips node_modules, etc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directories that should be skipped
            Path(tmpdir, "node_modules").mkdir()
            Path(tmpdir, "__pycache__").mkdir()
            Path(tmpdir, "src").mkdir()

            mock_config = MagicMock()
            mock_config.get_repo.return_value = RepoInfo(
                name="test-repo",
                path=tmpdir,
            )
            mock_get_config.return_value = mock_config

            result = await tools.get_repo_structure_tool({
                "name": "test-repo",
                "max_depth": 2,
            })

            data = json.loads(result)
            assert data["success"] is True

            # Check that skipped directories are marked
            children = data["structure"]["children"]
            node_modules = next(
                (c for c in children if c["name"] == "node_modules"), None
            )
            if node_modules:
                assert node_modules.get("skipped") is True


class TestReloadConfigTool:
    """Tests for reload_config_tool."""

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_reload_config(self, mock_get_config):
        """Test reload_config_tool."""
        mock_config = MagicMock()
        mock_config.repos = [RepoInfo(name="test", path="/test")]
        mock_config.config_path = "/path/to/repos.yaml"
        mock_get_config.return_value = mock_config

        # Clear cache first
        tools._config_cache = None

        result = await tools.reload_config_tool({})

        data = json.loads(result)
        assert data["success"] is True
        assert "reloaded" in data["message"]


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_list_repos_error(self, mock_get_config):
        """Test error handling in list_repos_tool."""
        mock_get_config.side_effect = Exception("Config error")

        result = await tools.list_repos_tool({})

        data = json.loads(result)
        assert "error" in data
        assert "Config error" in data["error"]

    @pytest.mark.asyncio
    @patch("mcp_servers.code_repos.tools._get_config")
    async def test_get_repo_info_error(self, mock_get_config):
        """Test error handling in get_repo_info_tool."""
        mock_get_config.side_effect = Exception("Config error")

        result = await tools.get_repo_info_tool({"name": "test"})

        data = json.loads(result)
        assert "error" in data
