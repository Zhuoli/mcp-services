# MCP Server Examples

This folder contains example implementations demonstrating how to connect to and use the MCP servers.

## Files

| File | Description |
|------|-------------|
| `mcp_client.py` | MCP client library for connecting to MCP servers via stdio |
| `chatbot.py` | MVP chatbot agent that uses Claude with MCP tool calling |

## Quick Start

### 1. Install Dependencies

```bash
cd /path/to/mcp-servers
make install-dev

# Also install httpx for the chatbot example
uv add httpx
```

### 2. Set Environment Variables

```bash
export ANTHROPIC_API_KEY=your-api-key

# For Atlassian server (if using)
export JIRA_URL=https://your-company.atlassian.net
export JIRA_USERNAME=your-email@company.com
export JIRA_API_TOKEN=your-token
export CONFLUENCE_URL=https://your-company.atlassian.net/wiki
export CONFLUENCE_USERNAME=your-email@company.com
export CONFLUENCE_API_TOKEN=your-token

# For Oracle Cloud server (if using)
export OCI_CONFIG_FILE=~/.oci/config
export OCI_PROFILE=DEFAULT
```

### 3. Run the Chatbot

```bash
# With code-repos server only (default, no extra config needed)
uv run python -m examples.chatbot

# With multiple servers
uv run python -m examples.chatbot --servers repos,atlassian

# With all servers
uv run python -m examples.chatbot --servers repos,oracle,atlassian

# With debug logging
uv run python -m examples.chatbot --debug
```

## Usage

Once the chatbot starts, you can:

- Type messages to interact with Claude
- Claude will automatically use MCP tools when appropriate
- Type `tools` to see available tools
- Type `clear` to clear conversation history
- Type `quit` or Ctrl+C to exit

### Example Conversations

**With Code Repos Server:**
```
You: What repositories do I have?
Assistant: Let me check your configured repositories...
[Calls repos__list_repos tool]
You have 5 repositories configured:
1. oracle-sdk-client - Oracle Cloud SDK client...
...

You: Tell me about the mcp-servers repo
Assistant: [Calls repos__get_repo_info tool]
The mcp-servers repository is a Python project...
```

**With Atlassian Server:**
```
You: What JIRA tickets are assigned to me?
Assistant: [Calls atlassian__get_my_jira_issues tool]
You have 3 issues assigned:
1. PROJ-123: Fix authentication bug (In Progress)
...

You: Create a new Confluence page for our API documentation
Assistant: [Calls atlassian__create_confluence_page tool]
I've created a new page titled "API Documentation"...
```

## MCP Client Library

The `mcp_client.py` module can be used independently in your own projects:

```python
import asyncio
from examples.mcp_client import MCPClient, MCPServerConfig

async def main():
    config = MCPServerConfig(
        name="repos",
        command=["uv", "run", "python", "-m", "mcp_servers.code_repos.server"],
        env={"REPOS_CONFIG_PATH": "./config/repos.yaml"},
    )

    async with MCPClient(config) as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")

        # Call a tool
        result = await client.call_tool("list_repos", {"include_details": True})
        print(result)

asyncio.run(main())
```

### Managing Multiple Servers

```python
from examples.mcp_client import MCPManager, MCPServerConfig

configs = [
    MCPServerConfig("repos", ["uv", "run", "python", "-m", "mcp_servers.code_repos.server"]),
    MCPServerConfig("atlassian", ["uv", "run", "python", "-m", "mcp_servers.atlassian.server"]),
]

async with MCPManager(configs) as manager:
    # Get all tools from all servers
    all_tools = manager.get_all_tools()

    # Call a specific tool
    result = await manager.call_tool("repos", "list_repos", {})

    # Or use the full prefixed name
    result = await manager.call_tool_by_full_name("repos__list_repos", {})
```

## Architecture

```
┌─────────────────┐
│    Chatbot      │
│   (chatbot.py)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MCPManager    │
│ (mcp_client.py) │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│ MCP   │ │ MCP   │
│Server1│ │Server2│
└───────┘ └───────┘
```

The chatbot:
1. Starts MCP servers as subprocesses
2. Communicates via JSON-RPC over stdio
3. Gets tool definitions from servers
4. Sends user messages to Claude with tool definitions
5. Executes tool calls through MCP servers
6. Returns results to Claude for final response

## Troubleshooting

### "MCP server closed connection"

The MCP server crashed during startup. Check:
- Environment variables are set correctly
- Server can start independently: `make run-repos`

### "Claude API error: 401"

Invalid API key. Check:
- `ANTHROPIC_API_KEY` is set correctly
- Key is active at https://console.anthropic.com/

### Tool calls failing

Check server-specific requirements:
- **repos**: Needs `config/repos.yaml` to exist
- **atlassian**: Needs JIRA/Confluence credentials
- **oracle**: Needs OCI config and valid session token
