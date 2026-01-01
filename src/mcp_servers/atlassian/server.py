"""MCP Server for Atlassian (JIRA and Confluence)."""

import asyncio
import logging
import os
import sys
from typing import Any

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from rich.console import Console

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
console = Console(stderr=True)

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


def validate_atlassian_config() -> bool:
    """
    Validate Atlassian configuration at startup.

    Returns:
        True if configuration is valid, False otherwise
    """
    console.print("[blue]Atlassian MCP Server - Startup Validation[/blue]")
    console.print("-" * 50)

    all_valid = True
    jira_valid = False
    confluence_valid = False

    # Check JIRA configuration
    console.print("[bold]JIRA Configuration:[/bold]")
    jira_url = os.environ.get("JIRA_URL")
    jira_username = os.environ.get("JIRA_USERNAME")
    jira_token = os.environ.get("JIRA_API_TOKEN")

    if not jira_url:
        console.print("[red]  ERROR: JIRA_URL environment variable not set[/red]")
        all_valid = False
    elif not jira_username:
        console.print("[red]  ERROR: JIRA_USERNAME environment variable not set[/red]")
        all_valid = False
    elif not jira_token:
        console.print("[red]  ERROR: JIRA_API_TOKEN environment variable not set[/red]")
        all_valid = False
    else:
        console.print(f"[green]  ✓[/green] JIRA URL: {jira_url}")
        console.print(f"[green]  ✓[/green] JIRA Username: {jira_username}")
        console.print("[green]  ✓[/green] JIRA API Token: [dim]****[/dim]")

        # Test JIRA connection
        console.print("[dim]  Testing JIRA connection...[/dim]")
        try:
            response = requests.get(
                f"{jira_url.rstrip('/')}/rest/api/3/myself",
                auth=(jira_username, jira_token),
                headers={"Accept": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                user_data = response.json()
                display_name = user_data.get("displayName", "Unknown")
                console.print(f"[green]  ✓[/green] JIRA connection successful (logged in as: {display_name})")
                jira_valid = True
            elif response.status_code == 401:
                console.print("[red]  ERROR: JIRA authentication failed - invalid credentials[/red]")
                all_valid = False
            elif response.status_code == 403:
                console.print("[red]  ERROR: JIRA access forbidden - check API token permissions[/red]")
                all_valid = False
            else:
                console.print(f"[red]  ERROR: JIRA connection failed (HTTP {response.status_code})[/red]")
                all_valid = False
        except requests.exceptions.ConnectionError:
            console.print(f"[red]  ERROR: Cannot connect to JIRA at {jira_url}[/red]")
            console.print("[yellow]    Check if the URL is correct and accessible[/yellow]")
            all_valid = False
        except requests.exceptions.Timeout:
            console.print("[red]  ERROR: JIRA connection timed out[/red]")
            all_valid = False
        except Exception as e:
            console.print(f"[red]  ERROR: JIRA connection test failed: {e}[/red]")
            all_valid = False

    console.print("")

    # Check Confluence configuration
    console.print("[bold]Confluence Configuration:[/bold]")
    confluence_url = os.environ.get("CONFLUENCE_URL")
    confluence_username = os.environ.get("CONFLUENCE_USERNAME")
    confluence_token = os.environ.get("CONFLUENCE_API_TOKEN")
    confluence_space = os.environ.get("CONFLUENCE_SPACE_KEY")

    if not confluence_url:
        console.print("[red]  ERROR: CONFLUENCE_URL environment variable not set[/red]")
        all_valid = False
    elif not confluence_username:
        console.print("[red]  ERROR: CONFLUENCE_USERNAME environment variable not set[/red]")
        all_valid = False
    elif not confluence_token:
        console.print("[red]  ERROR: CONFLUENCE_API_TOKEN environment variable not set[/red]")
        all_valid = False
    else:
        console.print(f"[green]  ✓[/green] Confluence URL: {confluence_url}")
        console.print(f"[green]  ✓[/green] Confluence Username: {confluence_username}")
        console.print("[green]  ✓[/green] Confluence API Token: [dim]****[/dim]")
        if confluence_space:
            console.print(f"[green]  ✓[/green] Default Space: {confluence_space}")
        else:
            console.print("[yellow]  ⚠ CONFLUENCE_SPACE_KEY not set (will need to specify in each request)[/yellow]")

        # Test Confluence connection
        console.print("[dim]  Testing Confluence connection...[/dim]")
        try:
            response = requests.get(
                f"{confluence_url.rstrip('/')}/rest/api/user/current",
                auth=(confluence_username, confluence_token),
                headers={"Accept": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                user_data = response.json()
                display_name = user_data.get("displayName", user_data.get("username", "Unknown"))
                console.print(f"[green]  ✓[/green] Confluence connection successful (logged in as: {display_name})")
                confluence_valid = True
            elif response.status_code == 401:
                console.print("[red]  ERROR: Confluence authentication failed - invalid credentials[/red]")
                all_valid = False
            elif response.status_code == 403:
                console.print("[red]  ERROR: Confluence access forbidden - check API token permissions[/red]")
                all_valid = False
            else:
                console.print(f"[red]  ERROR: Confluence connection failed (HTTP {response.status_code})[/red]")
                all_valid = False
        except requests.exceptions.ConnectionError:
            console.print(f"[red]  ERROR: Cannot connect to Confluence at {confluence_url}[/red]")
            console.print("[yellow]    Check if the URL is correct and accessible[/yellow]")
            all_valid = False
        except requests.exceptions.Timeout:
            console.print("[red]  ERROR: Confluence connection timed out[/red]")
            all_valid = False
        except Exception as e:
            console.print(f"[red]  ERROR: Confluence connection test failed: {e}[/red]")
            all_valid = False

    console.print("")
    console.print("-" * 50)

    if not all_valid:
        console.print("[red]Configuration validation failed.[/red]")
        console.print("")
        console.print("[yellow]To fix these issues:[/yellow]")
        console.print("  1. Set the required environment variables in .env file")
        console.print("  2. Get API tokens from: https://id.atlassian.com/manage-profile/security/api-tokens")
        console.print("")
        console.print("[dim]Required environment variables:[/dim]")
        console.print("  JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN")
        console.print("  CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN")
        console.print("  CONFLUENCE_SPACE_KEY (optional)")
        return False

    if jira_valid and confluence_valid:
        console.print("[green]All validations passed. Server ready.[/green]")
    elif jira_valid:
        console.print("[yellow]JIRA ready. Confluence connection failed but server will start.[/yellow]")
    elif confluence_valid:
        console.print("[yellow]Confluence ready. JIRA connection failed but server will start.[/yellow]")

    console.print("")
    return True


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
    # Validate configuration before starting
    if not validate_atlassian_config():
        console.print("[red]Server startup aborted due to configuration errors.[/red]")
        sys.exit(1)

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
