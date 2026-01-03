"""Unit tests for Atlassian MCP server."""

import json
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from mcp_servers.atlassian import tools
from mcp_servers.atlassian.models import JiraIssue, ConfluencePage


@dataclass
class MockJiraIssue:
    """Mock JIRA issue for testing."""
    key: str = "TEST-123"
    summary: str = "Test issue"
    description: str = "Test description"
    status: str = "Open"
    priority: str = "Medium"
    issue_type: str = "Task"
    assignee: str = "test@example.com"
    reporter: str = "reporter@example.com"
    created: str = "2024-01-01T00:00:00.000+0000"
    updated: str = "2024-01-02T00:00:00.000+0000"
    labels: list = None
    components: list = None
    sprint: str = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.components is None:
            self.components = []

    def to_dict(self):
        return {
            "key": self.key,
            "summary": self.summary,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "issue_type": self.issue_type,
            "assignee": self.assignee,
            "reporter": self.reporter,
            "created": self.created,
            "updated": self.updated,
            "labels": self.labels,
            "components": self.components,
            "sprint": self.sprint,
        }


@dataclass
class MockConfluencePage:
    """Mock Confluence page for testing."""
    page_id: str = "12345"
    title: str = "Test Page"
    space_key: str = "TEST"
    version: int = 1
    created: str = "2024-01-01T00:00:00.000Z"
    updated: str = "2024-01-02T00:00:00.000Z"
    author: str = "test@example.com"
    url: str = "https://confluence.example.com/pages/12345"
    body: str = "<p>Test content</p>"
    excerpt: str = "Test content"

    def to_dict(self):
        return {
            "page_id": self.page_id,
            "title": self.title,
            "space_key": self.space_key,
            "version": self.version,
            "created": self.created,
            "updated": self.updated,
            "author": self.author,
            "url": self.url,
            "excerpt": self.excerpt,
        }


class TestJiraTools:
    """Tests for JIRA tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.JiraClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_get_my_jira_issues(self, mock_get_config, mock_jira_client):
        """Test get_my_jira_issues_tool."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_issue = JiraIssue(
            key="TEST-123",
            summary="Test issue",
            status="Open",
            priority="Medium",
            issue_type="Task",
        )

        mock_client_instance = MagicMock()
        mock_client_instance.get_my_issues.return_value = [mock_issue]
        mock_jira_client.return_value = mock_client_instance

        result = await tools.get_my_jira_issues_tool({})

        data = json.loads(result)
        assert data["count"] == 1
        assert data["issues"][0]["key"] == "TEST-123"

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.JiraClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_search_jira_tickets(self, mock_get_config, mock_jira_client):
        """Test search_jira_tickets_tool."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_issue = JiraIssue(
            key="TEST-456",
            summary="Search result",
            status="In Progress",
            priority="High",
            issue_type="Bug",
        )

        mock_client_instance = MagicMock()
        mock_client_instance.search_issues.return_value = [mock_issue]
        mock_jira_client.return_value = mock_client_instance

        result = await tools.search_jira_tickets_tool({
            "jql": "project = TEST AND status = 'In Progress'",
        })

        data = json.loads(result)
        assert data["count"] == 1
        assert data["jql"] == "project = TEST AND status = 'In Progress'"

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.JiraClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_get_sprint_tasks(self, mock_get_config, mock_jira_client):
        """Test get_sprint_tasks_tool."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_issue = JiraIssue(
            key="TEST-789",
            summary="Sprint task",
            status="To Do",
            priority="Medium",
            issue_type="Story",
            sprint="Sprint 1",
        )

        mock_client_instance = MagicMock()
        mock_client_instance.get_sprint_issues.return_value = [mock_issue]
        mock_jira_client.return_value = mock_client_instance

        result = await tools.get_sprint_tasks_tool({})

        data = json.loads(result)
        assert data["count"] == 1

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.JiraClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_create_jira_ticket(self, mock_get_config, mock_jira_client):
        """Test create_jira_ticket_tool."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_issue = JiraIssue(
            key="TEST-NEW",
            summary="New issue",
            status="Open",
            priority="Medium",
            issue_type="Task",
        )

        mock_client_instance = MagicMock()
        mock_client_instance.create_issue.return_value = mock_issue
        mock_jira_client.return_value = mock_client_instance

        result = await tools.create_jira_ticket_tool({
            "project_key": "TEST",
            "summary": "New issue",
            "description": "Test description",
        })

        data = json.loads(result)
        assert data["success"] is True
        assert "TEST-NEW" in data["message"]

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.JiraClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_update_jira_ticket(self, mock_get_config, mock_jira_client):
        """Test update_jira_ticket_tool."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_issue = JiraIssue(
            key="TEST-123",
            summary="Updated issue",
            status="In Progress",
            priority="High",
            issue_type="Task",
        )

        mock_client_instance = MagicMock()
        mock_client_instance.update_issue.return_value = mock_issue
        mock_jira_client.return_value = mock_client_instance

        result = await tools.update_jira_ticket_tool({
            "issue_key": "TEST-123",
            "summary": "Updated issue",
            "status": "In Progress",
        })

        data = json.loads(result)
        assert data["success"] is True
        assert "TEST-123" in data["message"]

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.JiraClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_add_jira_comment(self, mock_get_config, mock_jira_client):
        """Test add_jira_comment_tool."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_client_instance.add_comment.return_value = {"id": "12345"}
        mock_jira_client.return_value = mock_client_instance

        result = await tools.add_jira_comment_tool({
            "issue_key": "TEST-123",
            "comment": "This is a test comment",
        })

        data = json.loads(result)
        assert data["success"] is True
        assert data["comment_id"] == "12345"


class TestConfluenceTools:
    """Tests for Confluence tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.ConfluenceClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_search_confluence_pages(self, mock_get_config, mock_confluence_client):
        """Test search_confluence_pages_tool."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_page = ConfluencePage(
            page_id="12345",
            title="Test Page",
            space_key="TEST",
            version=1,
            url="https://confluence.example.com/pages/12345",
        )

        mock_client_instance = MagicMock()
        mock_client_instance.search_pages.return_value = [mock_page]
        mock_confluence_client.return_value = mock_client_instance

        result = await tools.search_confluence_pages_tool({
            "query": "test search",
        })

        data = json.loads(result)
        assert data["count"] == 1
        assert data["query"] == "test search"

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.ConfluenceClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_get_confluence_page_by_id(self, mock_get_config, mock_confluence_client):
        """Test get_confluence_page_tool with page_id."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_page = ConfluencePage(
            page_id="12345",
            title="Test Page",
            space_key="TEST",
            version=1,
            url="https://confluence.example.com/pages/12345",
            body="<p>Test content</p>",
        )

        mock_client_instance = MagicMock()
        mock_client_instance.get_page_by_id.return_value = mock_page
        mock_confluence_client.return_value = mock_client_instance

        result = await tools.get_confluence_page_tool({
            "page_id": "12345",
        })

        data = json.loads(result)
        assert data["success"] is True
        assert data["page"]["title"] == "Test Page"

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.ConfluenceClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_get_confluence_page_by_title(self, mock_get_config, mock_confluence_client):
        """Test get_confluence_page_tool with title."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_page = ConfluencePage(
            page_id="12345",
            title="Test Page",
            space_key="TEST",
            version=1,
            url="https://confluence.example.com/pages/12345",
            body="<p>Test content</p>",
        )

        mock_client_instance = MagicMock()
        mock_client_instance.get_page_by_title.return_value = mock_page
        mock_confluence_client.return_value = mock_client_instance

        result = await tools.get_confluence_page_tool({
            "title": "Test Page",
            "space_key": "TEST",
        })

        data = json.loads(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.ConfluenceClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_get_confluence_page_not_found(self, mock_get_config, mock_confluence_client):
        """Test get_confluence_page_tool when page not found."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_client_instance.get_page_by_id.return_value = None
        mock_confluence_client.return_value = mock_client_instance

        result = await tools.get_confluence_page_tool({
            "page_id": "nonexistent",
        })

        data = json.loads(result)
        assert data["success"] is False
        assert "not found" in data["error"]

    @pytest.mark.asyncio
    async def test_get_confluence_page_no_params(self):
        """Test get_confluence_page_tool without required params."""
        result = await tools.get_confluence_page_tool({})

        data = json.loads(result)
        assert data["success"] is False
        assert "page_id or title" in data["error"]

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.ConfluenceClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_create_confluence_page(self, mock_get_config, mock_confluence_client):
        """Test create_confluence_page_tool."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_page = ConfluencePage(
            page_id="67890",
            title="New Page",
            space_key="TEST",
            version=1,
            url="https://confluence.example.com/pages/67890",
        )

        mock_client_instance = MagicMock()
        mock_client_instance.create_page.return_value = mock_page
        mock_confluence_client.return_value = mock_client_instance

        result = await tools.create_confluence_page_tool({
            "title": "New Page",
            "body": "<p>New content</p>",
        })

        data = json.loads(result)
        assert data["success"] is True
        assert "New Page" in data["message"]

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.ConfluenceClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_update_confluence_page(self, mock_get_config, mock_confluence_client):
        """Test update_confluence_page_tool."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_page = ConfluencePage(
            page_id="12345",
            title="Updated Page",
            space_key="TEST",
            version=2,
            url="https://confluence.example.com/pages/12345",
        )

        mock_client_instance = MagicMock()
        mock_client_instance.update_page.return_value = mock_page
        mock_confluence_client.return_value = mock_client_instance

        result = await tools.update_confluence_page_tool({
            "page_id": "12345",
            "title": "Updated Page",
            "body": "<p>Updated content</p>",
        })

        data = json.loads(result)
        assert data["success"] is True
        assert "Updated Page" in data["message"]

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.ConfluenceClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_get_recent_confluence_pages(self, mock_get_config, mock_confluence_client):
        """Test get_recent_confluence_pages_tool."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_page = ConfluencePage(
            page_id="12345",
            title="Recent Page",
            space_key="TEST",
            version=1,
            url="https://confluence.example.com/pages/12345",
        )

        mock_client_instance = MagicMock()
        mock_client_instance.get_recent_pages.return_value = [mock_page]
        mock_confluence_client.return_value = mock_client_instance

        result = await tools.get_recent_confluence_pages_tool({})

        data = json.loads(result)
        assert data["count"] == 1


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.JiraClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_jira_error_handling(self, mock_get_config, mock_jira_client):
        """Test that JIRA tools properly handle exceptions."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_client_instance.get_my_issues.side_effect = Exception("JIRA API Error")
        mock_jira_client.return_value = mock_client_instance

        result = await tools.get_my_jira_issues_tool({})

        data = json.loads(result)
        assert "error" in data
        assert "JIRA API Error" in data["error"]

    @pytest.mark.asyncio
    @patch("mcp_servers.atlassian.tools.ConfluenceClient")
    @patch("mcp_servers.atlassian.tools._get_config")
    async def test_confluence_error_handling(self, mock_get_config, mock_confluence_client):
        """Test that Confluence tools properly handle exceptions."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        mock_client_instance = MagicMock()
        mock_client_instance.search_pages.side_effect = Exception("Confluence API Error")
        mock_confluence_client.return_value = mock_client_instance

        result = await tools.search_confluence_pages_tool({
            "query": "test",
        })

        data = json.loads(result)
        assert "error" in data
        assert "Confluence API Error" in data["error"]
