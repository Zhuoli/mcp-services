"""MCP Server for Code Repositories."""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .tools import (
    get_repo_info_tool,
    get_repo_structure_tool,
    list_repos_tool,
    reload_config_tool,
    search_repos_tool,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("code-repos-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Code Repos tools."""
    return [
        Tool(
            name="list_repos",
            description=(
                "List all configured code repositories. Returns repository names, "
                "descriptions, paths, and tags. Use this to discover available projects."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "include_details": {
                        "type": "boolean",
                        "description": "Include full details (path, tags, exists status)",
                        "default": True,
                    },
                },
            },
        ),
        Tool(
            name="get_repo_info",
            description=(
                "Get detailed information about a specific repository including "
                "path, description, tags, project type detection, and existence status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Repository name",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="search_repos",
            description=(
                "Search repositories by text query and/or tags. "
                "Query searches in name and description. Tags filter by matching tags."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search in name and description",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to filter by (any match)",
                    },
                },
            },
        ),
        Tool(
            name="get_repo_structure",
            description=(
                "Get the directory structure of a repository. Useful for understanding "
                "project layout. Skips common directories like node_modules, __pycache__."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Repository name",
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum directory depth to traverse",
                        "default": 2,
                    },
                    "include_hidden": {
                        "type": "boolean",
                        "description": "Include hidden files and directories",
                        "default": False,
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="reload_config",
            description=(
                "Reload the repositories configuration from the YAML file. "
                "Use this after updating the config file to refresh the repo list."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute a tool based on its name and arguments."""
    logger.info(f"Executing tool: {name} with arguments: {arguments}")

    tool_handlers = {
        "list_repos": list_repos_tool,
        "get_repo_info": get_repo_info_tool,
        "search_repos": search_repos_tool,
        "get_repo_structure": get_repo_structure_tool,
        "reload_config": reload_config_tool,
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
    logger.info("Starting Code Repos MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server initialized and ready")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Entry point for the Code Repos MCP server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
