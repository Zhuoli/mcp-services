"""MCP Server for Atlassian (JIRA and Confluence)."""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .tools import (
    add_jira_comment_tool,
    create_confluence_page_tool,
    create_jira_ticket_tool,
    get_confluence_page_tool,
    get_my_jira_issues_tool,
    get_recent_confluence_pages_tool,
    get_sprint_tasks_tool,
    search_confluence_pages_tool,
    search_jira_tickets_tool,
    update_confluence_page_tool,
    update_jira_ticket_tool,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("atlassian-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Atlassian tools."""
    return [
        # JIRA Tools
        Tool(
            name="get_my_jira_issues",
            description=(
                "Get JIRA issues assigned to the current user. Returns issue details "
                "including key, summary, status, priority, sprint, and story points."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of issues to return",
                        "default": 50,
                    },
                },
            },
        ),
        Tool(
            name="search_jira_tickets",
            description=(
                "Search JIRA tickets using JQL (JIRA Query Language). Supports complex "
                "queries like 'project = PROJ AND status = Open ORDER BY priority DESC'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query string",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 50,
                    },
                },
                "required": ["jql"],
            },
        ),
        Tool(
            name="get_sprint_tasks",
            description=(
                "Get tasks assigned to the current user in active sprints. "
                "Optionally include future sprints."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "include_future_sprints": {
                        "type": "boolean",
                        "description": "Include issues in future sprints",
                        "default": False,
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 50,
                    },
                },
            },
        ),
        Tool(
            name="create_jira_ticket",
            description=(
                "Create a new JIRA ticket. Specify project key, summary, description, "
                "and optionally issue type, priority, and labels."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "Project key (e.g., 'PROJ')",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Issue summary/title",
                    },
                    "description": {
                        "type": "string",
                        "description": "Issue description",
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Issue type (Task, Bug, Story, Epic)",
                        "default": "Task",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority (Highest, High, Medium, Low, Lowest)",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of labels to add",
                    },
                },
                "required": ["project_key", "summary"],
            },
        ),
        Tool(
            name="update_jira_ticket",
            description=(
                "Update an existing JIRA ticket. Can update summary, description, "
                "status, priority, and labels."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Issue key (e.g., 'PROJ-123')",
                    },
                    "summary": {
                        "type": "string",
                        "description": "New summary",
                    },
                    "description": {
                        "type": "string",
                        "description": "New description",
                    },
                    "status": {
                        "type": "string",
                        "description": "New status (must be a valid transition)",
                    },
                    "priority": {
                        "type": "string",
                        "description": "New priority",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New labels (replaces existing)",
                    },
                },
                "required": ["issue_key"],
            },
        ),
        Tool(
            name="add_jira_comment",
            description="Add a comment to a JIRA ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Issue key (e.g., 'PROJ-123')",
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment text",
                    },
                },
                "required": ["issue_key", "comment"],
            },
        ),
        # Confluence Tools
        Tool(
            name="search_confluence_pages",
            description=(
                "Search Confluence pages using text search or CQL (Confluence Query Language). "
                "Supports queries like 'type=page AND text~\"API documentation\"'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (text or CQL)",
                    },
                    "space_key": {
                        "type": "string",
                        "description": "Optional space key to filter",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 25,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_confluence_page",
            description=(
                "Get a Confluence page by ID or title. Returns full page content "
                "including body, version, and metadata."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Page ID",
                    },
                    "title": {
                        "type": "string",
                        "description": "Page title (if page_id not provided)",
                    },
                    "space_key": {
                        "type": "string",
                        "description": "Space key (required if using title)",
                    },
                },
            },
        ),
        Tool(
            name="create_confluence_page",
            description=(
                "Create a new Confluence page. Can use predefined templates: "
                "technical_doc, runbook, meeting_notes, project_doc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Page title",
                    },
                    "body": {
                        "type": "string",
                        "description": "Page body in HTML format (ignored if using template)",
                    },
                    "space_key": {
                        "type": "string",
                        "description": "Space key (uses default if not provided)",
                    },
                    "parent_id": {
                        "type": "string",
                        "description": "Parent page ID",
                    },
                    "template": {
                        "type": "string",
                        "description": "Template to use",
                        "enum": ["technical_doc", "runbook", "meeting_notes", "project_doc"],
                    },
                    "template_vars": {
                        "type": "object",
                        "description": "Variables to substitute in template",
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="update_confluence_page",
            description="Update an existing Confluence page title and/or body.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Page ID to update",
                    },
                    "title": {
                        "type": "string",
                        "description": "New title (optional)",
                    },
                    "body": {
                        "type": "string",
                        "description": "New body in HTML format (optional)",
                    },
                },
                "required": ["page_id"],
            },
        ),
        Tool(
            name="get_recent_confluence_pages",
            description="Get recently modified Confluence pages in a space.",
            inputSchema={
                "type": "object",
                "properties": {
                    "space_key": {
                        "type": "string",
                        "description": "Space key (uses default if not provided)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10,
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute a tool based on its name and arguments."""
    logger.info(f"Executing tool: {name} with arguments: {arguments}")

    tool_handlers = {
        # JIRA
        "get_my_jira_issues": get_my_jira_issues_tool,
        "search_jira_tickets": search_jira_tickets_tool,
        "get_sprint_tasks": get_sprint_tasks_tool,
        "create_jira_ticket": create_jira_ticket_tool,
        "update_jira_ticket": update_jira_ticket_tool,
        "add_jira_comment": add_jira_comment_tool,
        # Confluence
        "search_confluence_pages": search_confluence_pages_tool,
        "get_confluence_page": get_confluence_page_tool,
        "create_confluence_page": create_confluence_page_tool,
        "update_confluence_page": update_confluence_page_tool,
        "get_recent_confluence_pages": get_recent_confluence_pages_tool,
    }

    handler = tool_handlers.get(name)

    if not handler:
        error_message = f"Unknown tool: {name}. Available tools: {list(tool_handlers.keys())}"
        logger.error(error_message)
        return [TextContent(type="text", text=error_message)]

    try:
        result = await handler(arguments)
        logger.info(f"Tool {name} executed successfully")
        return [TextContent(type="text", text=result)]
    except Exception as e:
        error_message = f"Error executing tool {name}: {str(e)}"
        logger.error(error_message, exc_info=True)
        return [TextContent(type="text", text=error_message)]


async def run_server():
    """Run the MCP server."""
    logger.info("Starting Atlassian MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server initialized and ready")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Entry point for the Atlassian MCP server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
