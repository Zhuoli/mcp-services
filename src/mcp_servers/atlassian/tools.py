"""Tool implementations for Atlassian MCP server."""

import logging
from typing import Any

from ..common.base_server import format_error, format_result
from .jira_client import JiraClient
from .confluence_client import ConfluenceClient
from .models import AtlassianConfig

logger = logging.getLogger(__name__)


def _get_config() -> AtlassianConfig:
    """Get Atlassian configuration from environment."""
    return AtlassianConfig()


# JIRA Tools

async def get_my_jira_issues_tool(arguments: dict[str, Any]) -> str:
    """Get JIRA issues assigned to the current user."""
    max_results = arguments.get("max_results", 50)

    try:
        client = JiraClient(_get_config())
        issues = client.get_my_issues(max_results=max_results)

        return format_result({
            "count": len(issues),
            "issues": [issue.to_dict() for issue in issues],
        })
    except Exception as e:
        return format_error(e, "get_my_jira_issues")


async def search_jira_tickets_tool(arguments: dict[str, Any]) -> str:
    """Search JIRA tickets using JQL."""
    jql = arguments["jql"]
    max_results = arguments.get("max_results", 50)

    try:
        client = JiraClient(_get_config())
        issues = client.search_issues(jql, max_results=max_results)

        return format_result({
            "jql": jql,
            "count": len(issues),
            "issues": [issue.to_dict() for issue in issues],
        })
    except Exception as e:
        return format_error(e, "search_jira_tickets")


async def get_sprint_tasks_tool(arguments: dict[str, Any]) -> str:
    """Get current sprint tasks assigned to the user."""
    include_future = arguments.get("include_future_sprints", False)
    max_results = arguments.get("max_results", 50)

    try:
        client = JiraClient(_get_config())
        issues = client.get_sprint_issues(
            include_future_sprints=include_future,
            max_results=max_results,
        )

        return format_result({
            "include_future_sprints": include_future,
            "count": len(issues),
            "issues": [issue.to_dict() for issue in issues],
        })
    except Exception as e:
        return format_error(e, "get_sprint_tasks")


async def create_jira_ticket_tool(arguments: dict[str, Any]) -> str:
    """Create a new JIRA ticket."""
    project_key = arguments["project_key"]
    summary = arguments["summary"]
    description = arguments.get("description", "")
    issue_type = arguments.get("issue_type", "Task")
    priority = arguments.get("priority")
    labels = arguments.get("labels", [])

    try:
        client = JiraClient(_get_config())
        issue = client.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=issue_type,
            priority=priority,
            labels=labels,
        )

        return format_result({
            "success": True,
            "message": f"Created issue {issue.key}",
            "issue": issue.to_dict(),
        })
    except Exception as e:
        return format_error(e, "create_jira_ticket")


async def update_jira_ticket_tool(arguments: dict[str, Any]) -> str:
    """Update an existing JIRA ticket."""
    issue_key = arguments["issue_key"]
    summary = arguments.get("summary")
    description = arguments.get("description")
    status = arguments.get("status")
    priority = arguments.get("priority")
    labels = arguments.get("labels")

    try:
        client = JiraClient(_get_config())
        issue = client.update_issue(
            issue_key=issue_key,
            summary=summary,
            description=description,
            status=status,
            priority=priority,
            labels=labels,
        )

        return format_result({
            "success": True,
            "message": f"Updated issue {issue.key}",
            "issue": issue.to_dict(),
        })
    except Exception as e:
        return format_error(e, "update_jira_ticket")


async def add_jira_comment_tool(arguments: dict[str, Any]) -> str:
    """Add a comment to a JIRA ticket."""
    issue_key = arguments["issue_key"]
    comment = arguments["comment"]

    try:
        client = JiraClient(_get_config())
        result = client.add_comment(issue_key, comment)

        return format_result({
            "success": True,
            "message": f"Added comment to {issue_key}",
            "comment_id": result.get("id"),
        })
    except Exception as e:
        return format_error(e, "add_jira_comment")


# Confluence Tools

async def search_confluence_pages_tool(arguments: dict[str, Any]) -> str:
    """Search Confluence pages."""
    query = arguments["query"]
    space_key = arguments.get("space_key")
    max_results = arguments.get("max_results", 25)

    try:
        client = ConfluenceClient(_get_config())
        pages = client.search_pages(query, space_key=space_key, max_results=max_results)

        return format_result({
            "query": query,
            "space_key": space_key,
            "count": len(pages),
            "pages": [page.to_dict() for page in pages],
        })
    except Exception as e:
        return format_error(e, "search_confluence_pages")


async def get_confluence_page_tool(arguments: dict[str, Any]) -> str:
    """Get a Confluence page by ID or title."""
    page_id = arguments.get("page_id")
    title = arguments.get("title")
    space_key = arguments.get("space_key")

    if not page_id and not title:
        return format_result({
            "success": False,
            "error": "Either page_id or title must be provided",
        })

    try:
        client = ConfluenceClient(_get_config())

        if page_id:
            page = client.get_page_by_id(page_id, include_body=True)
        else:
            page = client.get_page_by_title(title, space_key=space_key, include_body=True)

        if page:
            return format_result({
                "success": True,
                "page": page.to_dict(),
                "full_body": page.body,
            })
        else:
            return format_result({
                "success": False,
                "error": f"Page not found: {title or page_id}",
            })
    except Exception as e:
        return format_error(e, "get_confluence_page")


async def create_confluence_page_tool(arguments: dict[str, Any]) -> str:
    """Create a new Confluence page."""
    title = arguments["title"]
    body = arguments.get("body", "")
    space_key = arguments.get("space_key")
    parent_id = arguments.get("parent_id")
    template = arguments.get("template")
    template_vars = arguments.get("template_vars", {})

    try:
        client = ConfluenceClient(_get_config())
        page = client.create_page(
            title=title,
            body=body,
            space_key=space_key,
            parent_id=parent_id,
            template=template,
            template_vars=template_vars,
        )

        return format_result({
            "success": True,
            "message": f"Created page: {page.title}",
            "page": page.to_dict(),
        })
    except Exception as e:
        return format_error(e, "create_confluence_page")


async def update_confluence_page_tool(arguments: dict[str, Any]) -> str:
    """Update an existing Confluence page."""
    page_id = arguments["page_id"]
    title = arguments.get("title")
    body = arguments.get("body")

    try:
        client = ConfluenceClient(_get_config())
        page = client.update_page(page_id, title=title, body=body)

        return format_result({
            "success": True,
            "message": f"Updated page: {page.title}",
            "page": page.to_dict(),
        })
    except Exception as e:
        return format_error(e, "update_confluence_page")


async def get_recent_confluence_pages_tool(arguments: dict[str, Any]) -> str:
    """Get recently modified Confluence pages."""
    space_key = arguments.get("space_key")
    max_results = arguments.get("max_results", 10)

    try:
        client = ConfluenceClient(_get_config())
        pages = client.get_recent_pages(space_key=space_key, max_results=max_results)

        return format_result({
            "space_key": space_key,
            "count": len(pages),
            "pages": [page.to_dict() for page in pages],
        })
    except Exception as e:
        return format_error(e, "get_recent_confluence_pages")
