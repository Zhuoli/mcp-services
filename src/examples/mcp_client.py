"""
MCP Client - Connects to MCP servers via stdio transport.

This module provides a client implementation for communicating with
MCP (Model Context Protocol) servers using JSON-RPC over stdio.
"""

import asyncio
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents an MCP tool."""

    name: str
    description: str
    input_schema: dict[str, Any]

    def to_claude_format(self) -> dict[str, Any]:
        """Convert to Claude API tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    name: str
    command: list[str]
    env: dict[str, str] = field(default_factory=dict)


class MCPClient:
    """
    Client for communicating with MCP servers.

    Uses JSON-RPC 2.0 protocol over stdio transport.

    Example:
        async with MCPClient(config) as client:
            tools = await client.list_tools()
            result = await client.call_tool("tool_name", {"arg": "value"})
    """

    def __init__(self, config: MCPServerConfig):
        """
        Initialize MCP client.

        Args:
            config: Server configuration with command and environment
        """
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._tools: list[MCPTool] = []

    async def __aenter__(self) -> "MCPClient":
        """Start the MCP server process."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop the MCP server process."""
        await self.stop()

    async def start(self) -> None:
        """Start the MCP server subprocess."""
        import os

        env = os.environ.copy()
        env.update(self.config.env)

        logger.info(f"Starting MCP server: {self.config.name}")
        logger.debug(f"Command: {' '.join(self.config.command)}")

        self.process = subprocess.Popen(
            self.config.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,
        )

        # Initialize the connection
        await self._initialize()

    async def stop(self) -> None:
        """Stop the MCP server subprocess."""
        if self.process:
            logger.info(f"Stopping MCP server: {self.config.name}")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    async def _initialize(self) -> dict[str, Any]:
        """Initialize the MCP connection."""
        response = await self._send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-example-client",
                    "version": "0.1.0",
                },
            },
        )

        # Send initialized notification
        await self._send_notification("notifications/initialized", {})

        return response

    def _next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    async def _send_request(
        self, method: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Send a JSON-RPC request and wait for response.

        Args:
            method: RPC method name
            params: Method parameters

        Returns:
            Response result

        Raises:
            RuntimeError: If server is not running or returns an error
        """
        if not self.process or not self.process.stdin or not self.process.stdout:
            raise RuntimeError("MCP server is not running")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params:
            request["params"] = params

        request_line = json.dumps(request) + "\n"
        logger.debug(f"Sending: {request_line.strip()}")

        # Write request
        self.process.stdin.write(request_line)
        self.process.stdin.flush()

        # Read response
        response_line = await asyncio.get_event_loop().run_in_executor(
            None, self.process.stdout.readline
        )

        if not response_line:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            raise RuntimeError(f"MCP server closed connection. stderr: {stderr}")

        logger.debug(f"Received: {response_line.strip()}")

        response = json.loads(response_line)

        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"MCP error: {error.get('message', error)}")

        return response.get("result", {})

    async def _send_notification(
        self, method: str, params: Optional[dict[str, Any]] = None
    ) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if not self.process or not self.process.stdin:
            raise RuntimeError("MCP server is not running")

        notification = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            notification["params"] = params

        notification_line = json.dumps(notification) + "\n"
        logger.debug(f"Sending notification: {notification_line.strip()}")

        self.process.stdin.write(notification_line)
        self.process.stdin.flush()

    async def list_tools(self) -> list[MCPTool]:
        """
        List available tools from the MCP server.

        Returns:
            List of MCPTool objects
        """
        result = await self._send_request("tools/list")

        self._tools = [
            MCPTool(
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("inputSchema", {}),
            )
            for tool in result.get("tools", [])
        ]

        return self._tools

    async def call_tool(
        self, name: str, arguments: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result as string
        """
        result = await self._send_request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments or {},
            },
        )

        # Extract text content from response
        content = result.get("content", [])
        if content and isinstance(content, list):
            texts = [c.get("text", "") for c in content if c.get("type") == "text"]
            return "\n".join(texts)

        return str(result)

    def get_tools_for_claude(self) -> list[dict[str, Any]]:
        """
        Get tools in Claude API format.

        Returns:
            List of tool definitions for Claude API
        """
        return [tool.to_claude_format() for tool in self._tools]


class MCPManager:
    """
    Manager for multiple MCP server connections.

    Example:
        configs = [
            MCPServerConfig("repos", ["uv", "run", "python", "-m", "mcp_servers.code_repos.server"]),
            MCPServerConfig("atlassian", ["uv", "run", "python", "-m", "mcp_servers.atlassian.server"]),
        ]

        async with MCPManager(configs) as manager:
            all_tools = manager.get_all_tools()
            result = await manager.call_tool("repos", "list_repos", {})
    """

    def __init__(self, configs: list[MCPServerConfig]):
        """
        Initialize MCP manager.

        Args:
            configs: List of server configurations
        """
        self.configs = configs
        self.clients: dict[str, MCPClient] = {}

    async def __aenter__(self) -> "MCPManager":
        """Start all MCP servers."""
        await self.start_all()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop all MCP servers."""
        await self.stop_all()

    async def start_all(self) -> None:
        """Start all configured MCP servers."""
        for config in self.configs:
            client = MCPClient(config)
            await client.start()
            await client.list_tools()  # Cache tools
            self.clients[config.name] = client
            logger.info(f"Started {config.name} with {len(client._tools)} tools")

    async def stop_all(self) -> None:
        """Stop all MCP servers."""
        for name, client in self.clients.items():
            await client.stop()
        self.clients.clear()

    def get_client(self, name: str) -> MCPClient:
        """Get a specific MCP client by name."""
        if name not in self.clients:
            raise ValueError(f"Unknown MCP server: {name}")
        return self.clients[name]

    def get_all_tools(self) -> list[dict[str, Any]]:
        """Get all tools from all servers in Claude API format."""
        tools = []
        for name, client in self.clients.items():
            for tool in client._tools:
                tool_def = tool.to_claude_format()
                # Prefix tool name with server name to avoid conflicts
                tool_def["name"] = f"{name}__{tool.name}"
                tools.append(tool_def)
        return tools

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any]
    ) -> str:
        """
        Call a tool on a specific server.

        Args:
            server_name: Name of the MCP server
            tool_name: Tool name (without server prefix)
            arguments: Tool arguments

        Returns:
            Tool result
        """
        client = self.get_client(server_name)
        return await client.call_tool(tool_name, arguments)

    async def call_tool_by_full_name(
        self, full_name: str, arguments: dict[str, Any]
    ) -> str:
        """
        Call a tool using its full prefixed name.

        Args:
            full_name: Tool name with server prefix (e.g., "repos__list_repos")
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if "__" not in full_name:
            raise ValueError(f"Invalid tool name format: {full_name}")

        server_name, tool_name = full_name.split("__", 1)
        return await self.call_tool(server_name, tool_name, arguments)
