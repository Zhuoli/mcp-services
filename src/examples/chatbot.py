#!/usr/bin/env python3
"""
MVP Chatbot Agent - Demonstrates MCP server integration.

This is a minimal chatbot that connects to MCP servers and uses
Claude to process user requests with tool calling capabilities.

Usage:
    # Set environment variables first
    export ANTHROPIC_API_KEY=your-api-key

    # Run the chatbot
    uv run python -m examples.chatbot

    # Or run with specific servers
    uv run python -m examples.chatbot --servers repos
    uv run python -m examples.chatbot --servers repos,atlassian
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from examples.mcp_client import MCPManager, MCPServerConfig

console = Console()
logger = logging.getLogger(__name__)


# Default server configurations
DEFAULT_SERVERS = {
    "repos": MCPServerConfig(
        name="repos",
        command=["uv", "run", "python", "-m", "mcp_servers.code_repos.server"],
        env={"REPOS_CONFIG_PATH": str(Path(__file__).parent.parent.parent / "config" / "repos.yaml")},
    ),
    "oracle": MCPServerConfig(
        name="oracle",
        command=["uv", "run", "python", "-m", "mcp_servers.oracle_cloud.server"],
        env={},
    ),
    "atlassian": MCPServerConfig(
        name="atlassian",
        command=["uv", "run", "python", "-m", "mcp_servers.atlassian.server"],
        env={},
    ),
}


async def call_claude(
    messages: list[dict],
    tools: list[dict],
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    """
    Call Claude API with messages and tools.

    Args:
        messages: Conversation messages
        tools: Available tools
        api_key: Anthropic API key
        model: Model to use

    Returns:
        Claude API response
    """
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 4096,
                "messages": messages,
                "tools": tools if tools else None,
            },
            timeout=60.0,
        )

        if response.status_code != 200:
            raise RuntimeError(f"Claude API error: {response.status_code} - {response.text}")

        return response.json()


async def process_tool_calls(
    response: dict,
    manager: MCPManager,
    messages: list[dict],
    tools: list[dict],
    api_key: str,
) -> str:
    """
    Process tool calls from Claude response.

    Args:
        response: Claude API response
        manager: MCP manager
        messages: Conversation messages
        tools: Available tools
        api_key: Anthropic API key

    Returns:
        Final assistant response text
    """
    while response.get("stop_reason") == "tool_use":
        # Find tool use blocks
        tool_uses = [
            block for block in response.get("content", [])
            if block.get("type") == "tool_use"
        ]

        if not tool_uses:
            break

        # Add assistant message with tool use
        messages.append({"role": "assistant", "content": response["content"]})

        # Process each tool call
        tool_results = []
        for tool_use in tool_uses:
            tool_name = tool_use["name"]
            tool_input = tool_use["input"]
            tool_id = tool_use["id"]

            console.print(f"[dim]Calling tool: {tool_name}[/dim]")
            console.print(f"[dim]  Input: {json.dumps(tool_input, indent=2)}[/dim]")

            try:
                result = await manager.call_tool_by_full_name(tool_name, tool_input)
                console.print(f"[dim]  Result: {result[:200]}{'...' if len(result) > 200 else ''}[/dim]")
            except Exception as e:
                result = f"Error: {e}"
                console.print(f"[red]  Error: {e}[/red]")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": result,
            })

        # Add tool results
        messages.append({"role": "user", "content": tool_results})

        # Get next response
        response = await call_claude(messages, tools, api_key)

    # Extract final text response
    text_blocks = [
        block.get("text", "")
        for block in response.get("content", [])
        if block.get("type") == "text"
    ]

    return "\n".join(text_blocks)


async def chat_loop(manager: MCPManager, api_key: str):
    """
    Main chat loop.

    Args:
        manager: MCP manager with connected servers
        api_key: Anthropic API key
    """
    tools = manager.get_all_tools()
    messages: list[dict] = []

    console.print(Panel.fit(
        "[bold blue]MCP Chatbot Agent[/bold blue]\n\n"
        f"Connected servers: {', '.join(manager.clients.keys())}\n"
        f"Available tools: {len(tools)}\n\n"
        "Type your message or 'quit' to exit.\n"
        "Type 'tools' to list available tools.",
        title="Welcome",
    ))

    while True:
        try:
            user_input = console.input("\n[bold green]You:[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            console.print("[dim]Goodbye![/dim]")
            break

        if user_input.lower() == "tools":
            console.print("\n[bold]Available Tools:[/bold]")
            for tool in tools:
                console.print(f"  [cyan]{tool['name']}[/cyan]")
                console.print(f"    {tool['description'][:80]}...")
            continue

        if user_input.lower() == "clear":
            messages.clear()
            console.print("[dim]Conversation cleared.[/dim]")
            continue

        # Add user message
        messages.append({"role": "user", "content": user_input})

        try:
            console.print("\n[dim]Thinking...[/dim]")

            # Call Claude
            response = await call_claude(messages, tools, api_key)

            # Process tool calls if any
            assistant_response = await process_tool_calls(
                response, manager, messages, tools, api_key
            )

            # Add final response to history
            messages.append({"role": "assistant", "content": assistant_response})

            # Display response
            console.print("\n[bold blue]Assistant:[/bold blue]")
            console.print(Markdown(assistant_response))

        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            # Remove failed user message
            if messages and messages[-1]["role"] == "user":
                messages.pop()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MVP Chatbot Agent with MCP server integration"
    )
    parser.add_argument(
        "--servers",
        type=str,
        default="repos",
        help="Comma-separated list of servers to connect (repos,oracle,atlassian)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    # Configure logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
        console.print("[dim]Get your API key from: https://console.anthropic.com/[/dim]")
        sys.exit(1)

    # Parse server list
    server_names = [s.strip() for s in args.servers.split(",")]
    configs = []

    for name in server_names:
        if name not in DEFAULT_SERVERS:
            console.print(f"[red]Unknown server: {name}[/red]")
            console.print(f"[dim]Available: {', '.join(DEFAULT_SERVERS.keys())}[/dim]")
            sys.exit(1)
        configs.append(DEFAULT_SERVERS[name])

    console.print(f"[dim]Connecting to MCP servers: {', '.join(server_names)}...[/dim]")

    try:
        async with MCPManager(configs) as manager:
            await chat_loop(manager, api_key)
    except Exception as e:
        console.print(f"[red]Failed to start MCP servers: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
