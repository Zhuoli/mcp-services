# MCP Servers

A collection of Model Context Protocol (MCP) servers for Oracle Cloud, Atlassian (JIRA/Confluence), and Code Repository management.

## Overview

This repository contains three MCP servers that enable AI assistants to interact with various services:

| Server | Description | Tools |
|--------|-------------|-------|
| **oracle-cloud** | Oracle Cloud Infrastructure operations | 6 |
| **atlassian** | JIRA and Confluence integration | 11 |
| **code-repos** | Code repository discovery and navigation | 5 |

## Quick Start

```bash
# Clone and setup
cd mcp-servers
make install

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your credentials

# Run a server
make run-oracle
make run-atlassian
make run-repos
```

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

## Installation

```bash
# Install all dependencies
make install

# Or manually with uv
uv sync
```

## Usage

### Running Servers

Each MCP server runs independently via stdio transport:

```bash
# Oracle Cloud MCP Server
make run-oracle

# Atlassian MCP Server
make run-atlassian

# Code Repos MCP Server
make run-repos
```

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "oracle-cloud": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-servers", "python", "-m", "mcp_servers.oracle_cloud.server"],
      "env": {
        "OCI_CONFIG_FILE": "~/.oci/config",
        "OCI_PROFILE": "DEFAULT"
      }
    },
    "atlassian": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-servers", "python", "-m", "mcp_servers.atlassian.server"],
      "env": {
        "JIRA_URL": "https://your-company.atlassian.net",
        "JIRA_USERNAME": "your-email@company.com",
        "JIRA_API_TOKEN": "your-token",
        "CONFLUENCE_URL": "https://your-company.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your-email@company.com",
        "CONFLUENCE_API_TOKEN": "your-token",
        "CONFLUENCE_SPACE_KEY": "TEAM"
      }
    },
    "code-repos": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-servers", "python", "-m", "mcp_servers.code_repos.server"],
      "env": {
        "REPOS_CONFIG_PATH": "/path/to/mcp-servers/config/repos.yaml"
      }
    }
  }
}
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Oracle Cloud
OCI_CONFIG_FILE=~/.oci/config
OCI_PROFILE=DEFAULT
OCI_REGION=us-phoenix-1

# Atlassian - JIRA
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# Atlassian - Confluence
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-api-token
CONFLUENCE_SPACE_KEY=TEAM

# Code Repos
REPOS_CONFIG_PATH=./config/repos.yaml
```

### Code Repos Configuration

Edit `config/repos.yaml` to add your repositories:

```yaml
repositories:
  - name: my-project
    path: /path/to/my-project
    description: Description of the project
    tags:
      - python
      - api
```

## MCP Servers

### Oracle Cloud MCP

Tools for Oracle Cloud Infrastructure:

| Tool | Description |
|------|-------------|
| `create_session_token` | Create OCI session token via browser SSO |
| `validate_session_token` | Check token validity and remaining time |
| `list_compartments` | List OCI compartments |
| `list_instances` | List compute instances (with OKE filtering) |
| `list_oke_clusters` | List Kubernetes clusters |
| `list_bastions` | List bastion hosts |

**Authentication**: Uses session token authentication via OCI CLI. Tokens are valid for 60 minutes.

### Atlassian MCP

Tools for JIRA and Confluence:

**JIRA Tools**:
| Tool | Description |
|------|-------------|
| `get_my_jira_issues` | Get issues assigned to current user |
| `search_jira_tickets` | Search using JQL |
| `get_sprint_tasks` | Get current sprint tasks |
| `create_jira_ticket` | Create new issue |
| `update_jira_ticket` | Update existing issue |
| `add_jira_comment` | Add comment to issue |

**Confluence Tools**:
| Tool | Description |
|------|-------------|
| `search_confluence_pages` | Search using CQL |
| `get_confluence_page` | Get page by ID or title |
| `create_confluence_page` | Create page (with templates) |
| `update_confluence_page` | Update existing page |
| `get_recent_confluence_pages` | List recently modified pages |

**Page Templates**: `technical_doc`, `runbook`, `meeting_notes`, `project_doc`

### Code Repos MCP

Tools for repository discovery:

| Tool | Description |
|------|-------------|
| `list_repos` | List all configured repositories |
| `get_repo_info` | Get detailed repo information |
| `search_repos` | Search by query or tags |
| `get_repo_structure` | Get directory structure |
| `reload_config` | Reload repos.yaml configuration |

## Skills

Each MCP server includes a Claude Code skill with detailed usage instructions:

- `.claude/skills/oracle-cloud-mcp/SKILL.md` - OCI authentication and operations
- `.claude/skills/atlassian-mcp/SKILL.md` - JQL/CQL patterns and templates
- `.claude/skills/code-repos-mcp/SKILL.md` - Repository discovery patterns

## Development

```bash
# Install with dev dependencies
make install

# Run linting
make lint

# Run type checking
make typecheck

# Run tests
make test

# Format code
make format

# Run all checks
make check
```

## Project Structure

```
mcp-servers/
├── Makefile                    # Build and run commands
├── pyproject.toml              # Project configuration
├── .env.example                # Environment template
├── config/
│   └── repos.yaml              # Code repos configuration
├── src/mcp_servers/
│   ├── common/                 # Shared utilities
│   ├── oracle_cloud/           # Oracle Cloud MCP
│   ├── atlassian/              # Atlassian MCP
│   └── code_repos/             # Code Repos MCP
└── .claude/skills/             # Claude Code skills
```

## License

MIT
