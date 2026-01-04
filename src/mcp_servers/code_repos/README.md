# Code Repos MCP Server

A Model Context Protocol (MCP) server for managing and querying local code repositories. This lightweight metadata manager enables AI assistants like Claude to discover, search, and explore repositories on your local filesystem.

## Overview

This MCP server provides **5 tools** for managing local repository metadata:

- **Discovery**: List and search configured repositories
- **Exploration**: Get repository info and directory structures
- **Configuration**: Reload configuration without server restart

**Important:** This server does **NOT** index repository contents. It manages metadata (names, paths, descriptions, tags) and performs on-demand filesystem traversal.

## How It Works

1. You define your repositories in a YAML configuration file
2. The MCP server reads this configuration and caches it in memory
3. AI assistants can query, search, and explore repositories through the tools
4. Use `reload_config` to refresh the configuration without restarting

## Configuration

### YAML Configuration File

Create a `repos.yaml` file with your repository definitions:

```yaml
# repos.yaml - Repository Configuration
# Define your local code repositories here

repositories:
  # Python project example
  - name: my-python-api
    path: /Users/username/Projects/my-python-api
    description: REST API built with FastAPI for user management
    tags:
      - python
      - fastapi
      - api
      - backend
    url: https://github.com/username/my-python-api  # Optional
    default_branch: main  # Optional, defaults to "main"

  # JavaScript/TypeScript project example
  - name: react-dashboard
    path: /Users/username/Projects/react-dashboard
    description: Admin dashboard built with React and TypeScript
    tags:
      - react
      - typescript
      - frontend
      - dashboard

  # Infrastructure project example
  - name: k8s-configs
    path: /Users/username/Projects/k8s-configs
    description: Kubernetes deployment manifests and Helm charts
    tags:
      - kubernetes
      - infrastructure
      - devops
      - helm

  # Rust project example
  - name: cli-tool
    path: /Users/username/Projects/cli-tool
    description: Command-line utility for file processing
    tags:
      - rust
      - cli
      - tools

  # Go project example
  - name: microservice
    path: /Users/username/Projects/microservice
    description: Microservice for handling payments
    tags:
      - go
      - microservice
      - payments
```

### Configuration Schema

Each repository entry supports these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique identifier for the repository |
| `path` | string | Yes | Absolute path to the repository on disk |
| `description` | string | Yes | Human-readable description |
| `tags` | list[string] | No | Searchable tags/keywords |
| `url` | string | No | Remote repository URL (for reference) |
| `default_branch` | string | No | Default branch name (defaults to "main") |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REPOS_CONFIG_PATH` | Path to the repos.yaml configuration file | `./config/repos.yaml` |

## Running the Server

```bash
# Using uv (recommended)
REPOS_CONFIG_PATH=/path/to/repos.yaml uv run code-repos-mcp

# Or set environment variable first
export REPOS_CONFIG_PATH=/path/to/repos.yaml
uv run code-repos-mcp

# Or directly with Python
python -m mcp_servers.code_repos.server
```

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "code-repos": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-services", "run", "code-repos-mcp"],
      "env": {
        "REPOS_CONFIG_PATH": "/path/to/repos.yaml"
      }
    }
  }
}
```

## Available Tools (5 total)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_repos` | List all configured repositories | None |
| `get_repo_info` | Get detailed info about a repository | `name` |
| `search_repos` | Search by query text and/or tags | `query` or `tags` |
| `get_repo_structure` | Get directory tree of a repository | `name` |
| `reload_config` | Reload configuration from YAML file | None |

## Tool Details

### `list_repos`

List all configured repositories.

**Parameters:**
- `include_details` (optional, default: true): Include full repository details

**Example Request:**
```json
{
  "include_details": true
}
```

**Example Response:**
```json
{
  "count": 5,
  "repositories": [
    {
      "name": "my-python-api",
      "path": "/Users/username/Projects/my-python-api",
      "description": "REST API built with FastAPI",
      "tags": ["python", "fastapi", "api"],
      "exists": true
    }
  ],
  "all_tags": ["python", "fastapi", "api", "react", "typescript", "kubernetes"]
}
```

### `get_repo_info`

Get detailed information about a specific repository, including project type detection.

**Parameters:**
- `name` (required): Repository name

**Example Request:**
```json
{
  "name": "my-python-api"
}
```

**Example Response:**
```json
{
  "success": true,
  "repository": {
    "name": "my-python-api",
    "path": "/Users/username/Projects/my-python-api",
    "description": "REST API built with FastAPI",
    "tags": ["python", "fastapi", "api"],
    "exists": true,
    "has_readme": true,
    "has_pyproject": true,
    "has_package_json": false,
    "has_cargo": false,
    "has_go_mod": false,
    "project_type": "python"
  }
}
```

**Project Type Detection:**

| Project Type | Detection File |
|--------------|----------------|
| Python | `pyproject.toml` |
| JavaScript/TypeScript | `package.json` |
| Rust | `Cargo.toml` |
| Go | `go.mod` |
| Unknown | None of the above |

### `search_repos`

Search repositories by text query and/or tags.

**Parameters:**
- `query` (optional): Text to search in name and description (case-insensitive)
- `tags` (optional): List of tags to filter by (any match)

*Note: At least one of `query` or `tags` must be provided.*

**Example Request:**
```json
{
  "query": "api",
  "tags": ["python"]
}
```

**Example Response:**
```json
{
  "query": "api",
  "tags": ["python"],
  "count": 1,
  "repositories": [
    {
      "name": "my-python-api",
      "path": "/Users/username/Projects/my-python-api",
      "description": "REST API built with FastAPI",
      "tags": ["python", "fastapi", "api"],
      "exists": true
    }
  ]
}
```

### `get_repo_structure`

Get the directory structure of a repository.

**Parameters:**
- `name` (required): Repository name
- `max_depth` (optional, default: 2): Maximum directory depth to traverse
- `include_hidden` (optional, default: false): Include hidden files/directories

**Auto-skipped directories:** `node_modules`, `__pycache__`, `.git`, `venv`, `.venv`

**Example Request:**
```json
{
  "name": "my-python-api",
  "max_depth": 2,
  "include_hidden": false
}
```

**Example Response:**
```json
{
  "success": true,
  "repository": "my-python-api",
  "path": "/Users/username/Projects/my-python-api",
  "max_depth": 2,
  "structure": {
    "name": "my-python-api",
    "type": "directory",
    "children": [
      {
        "name": "src",
        "type": "directory",
        "children": [
          {"name": "main.py", "type": "file", "size": 1234},
          {"name": "models.py", "type": "file", "size": 567}
        ]
      },
      {"name": "pyproject.toml", "type": "file", "size": 890},
      {"name": "README.md", "type": "file", "size": 2345},
      {"name": "__pycache__", "type": "directory", "skipped": true}
    ]
  }
}
```

### `reload_config`

Reload the configuration from the YAML file without restarting the server.

**Parameters:** None (empty object)

**Example Request:**
```json
{}
```

**Example Response:**
```json
{
  "success": true,
  "message": "Configuration reloaded successfully",
  "repo_count": 5,
  "config_path": "/path/to/repos.yaml"
}
```

**Use this when:**
- You've added new repositories to the YAML file
- You've updated repository metadata
- You've removed repositories from the configuration

## Usage Examples

### Example 1: Discover Repositories

```
User: What repositories do I have configured?

Claude: I'll list your configured repositories.
[Uses list_repos tool]

You have 5 repositories configured:
1. my-python-api - REST API built with FastAPI
2. react-dashboard - Admin dashboard with React
3. k8s-configs - Kubernetes deployment manifests
4. cli-tool - Command-line utility in Rust
5. microservice - Payment processing in Go

Available tags: python, fastapi, react, typescript, kubernetes, rust, go
```

### Example 2: Search by Tags

```
User: Show me all my frontend projects

Claude: I'll search for frontend projects.
[Uses search_repos tool with tags=["frontend"]]

Found 1 frontend project:
1. react-dashboard (/Users/username/Projects/react-dashboard)
   - Admin dashboard built with React and TypeScript
   - Tags: react, typescript, frontend, dashboard
```

### Example 3: Explore Repository Structure

```
User: What's the structure of my Python API project?

Claude: I'll get the directory structure.
[Uses get_repo_structure tool with name="my-python-api"]

my-python-api/
├── src/
│   ├── main.py (1.2 KB)
│   ├── models.py (567 B)
│   └── routes/
│       ├── users.py
│       └── auth.py
├── tests/
│   └── test_api.py
├── pyproject.toml (890 B)
└── README.md (2.3 KB)

Project type: Python (detected pyproject.toml)
```

### Example 4: Update Configuration

```
User: I just added a new repository to my config file

Claude: I'll reload the configuration.
[Uses reload_config tool]

Configuration reloaded successfully!
- Previous count: 5 repositories
- New count: 6 repositories
- Config path: /path/to/repos.yaml
```

## File Structure

```
src/mcp_servers/code_repos/
├── __init__.py
├── server.py      # MCP server entry point
├── tools.py       # Tool implementations (5 tools)
├── models.py      # Data models (RepoInfo, ReposConfig)
└── README.md      # This file
```

## Error Handling

All tools return JSON responses with consistent structure:

**Success:**
```json
{
  "success": true,
  "repository": {...}
}
```

**Error:**
```json
{
  "error": "Error message",
  "error_type": "ExceptionType",
  "tool": "tool_name"
}
```

## Common Issues

### Configuration File Not Found

```
FileNotFoundError: Configuration file not found
```

**Solution:** Set `REPOS_CONFIG_PATH` to the correct path or create `./config/repos.yaml`.

### Repository Path Doesn't Exist

The `exists` field in responses will be `false` if the path doesn't exist on disk. The server will still return metadata, but filesystem operations like `get_repo_structure` will fail.

### Repository Not Found

When using `get_repo_info` or `get_repo_structure` with an unknown name:

```json
{
  "success": false,
  "error": "Repository not found: unknown-repo",
  "available_repos": ["my-python-api", "react-dashboard", ...]
}
```

## Best Practices

1. **Use descriptive names**: Choose repository names that are easy to remember and search
2. **Add relevant tags**: Tags make searching more effective
3. **Keep descriptions concise**: Brief but informative descriptions
4. **Use absolute paths**: Always use full paths to avoid ambiguity
5. **Update configuration**: Use `reload_config` after editing the YAML file

## Comparison with Code Indexing

This MCP server is a **metadata manager**, not a code indexer:

| Feature | Code Repos MCP | Code Indexer |
|---------|----------------|--------------|
| Content indexing | No | Yes |
| Full-text search in code | No | Yes |
| Configuration-based | Yes | Usually no |
| Instant updates | Yes (`reload_config`) | Requires re-indexing |
| Storage overhead | Minimal (YAML only) | Significant (index files) |
| Setup complexity | Low | Higher |

Use this server when you need quick repository discovery and navigation. For full-text code search, consider dedicated tools like `ripgrep` or code search engines.
