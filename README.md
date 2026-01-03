# MCP Servers Collection

A comprehensive collection of Model Context Protocol (MCP) servers that enable AI assistants like Claude to interact with various services and infrastructure.

## Servers Included

| Server | Description | Tools |
|--------|-------------|-------|
| **Oracle Cloud MCP** | Comprehensive OCI integration for OKE clusters, DevOps pipelines, and infrastructure | 37 tools |
| **Atlassian MCP** | JIRA and Confluence integration | 11 tools |
| **Code Repos MCP** | Local code repository management | 5 tools |

## Installation

### From GitHub Actions Artifacts (Recommended)

1. Go to the [Actions tab](../../actions) in this repository
2. Click on the latest successful **CI** workflow run
3. Download the `mcp-servers-package` artifact (contains `.whl` and `.tar.gz`)
4. Unzip and install:

```bash
# Unzip the downloaded artifact
unzip mcp-servers-package.zip

# Install the wheel package
pip install mcp_servers_collection-*.whl

# Or with uv
uv pip install mcp_servers_collection-*.whl
```

### From Source

```bash
git clone https://github.com/your-org/mcp-services.git
cd mcp-services
uv sync
```

## Quick Start

### Running MCP Servers

After installation, you can run any MCP server directly:

```bash
# Oracle Cloud MCP
oracle-cloud-mcp

# Atlassian MCP
atlassian-mcp

# Code Repos MCP
code-repos-mcp
```

Or using `uv` from source:

```bash
# Oracle Cloud MCP
uv run oracle-cloud-mcp

# Atlassian MCP
uv run atlassian-mcp

# Code Repos MCP
uv run code-repos-mcp
```

## Claude Desktop Integration

To use these MCP servers with Claude Desktop, add them to your `claude_desktop_config.json`:

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/claude/claude_desktop_config.json`

### Example Configuration

```json
{
  "mcpServers": {
    "oracle-cloud": {
      "command": "oracle-cloud-mcp",
      "env": {
        "OCI_CONFIG_FILE": "~/.oci/config",
        "OCI_PROFILE": "DEFAULT",
        "OCI_REGION": "us-phoenix-1"
      }
    },
    "atlassian": {
      "command": "atlassian-mcp",
      "env": {
        "JIRA_URL": "https://your-company.atlassian.net",
        "JIRA_USERNAME": "your-email@company.com",
        "JIRA_API_TOKEN": "your-jira-api-token",
        "CONFLUENCE_URL": "https://your-company.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your-email@company.com",
        "CONFLUENCE_API_TOKEN": "your-confluence-api-token",
        "CONFLUENCE_SPACE_KEY": "TEAM"
      }
    },
    "code-repos": {
      "command": "code-repos-mcp",
      "env": {
        "REPOS_CONFIG_PATH": "/path/to/repos.yaml"
      }
    }
  }
}
```

See `examples/claude_desktop_config.json` for a complete example with both pip and uv configurations.

---

## Oracle Cloud MCP Server

Comprehensive MCP server for Oracle Cloud Infrastructure (OCI) with full support for:

- **OKE (Oracle Kubernetes Engine)**: Cluster management, node pools, kubeconfig generation, scaling
- **OCI DevOps**: Build pipelines, deployment pipelines, artifacts, environments
- **Infrastructure**: Compute instances, compartments, bastions

### Prerequisites

1. **OCI CLI installed and configured:**
   ```bash
   pip install oci-cli
   oci setup config
   ```

2. **For session token authentication:**
   ```bash
   oci session authenticate --profile-name DEFAULT --region us-phoenix-1
   ```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OCI_CONFIG_FILE` | Path to OCI config file | `~/.oci/config` |
| `OCI_PROFILE` | OCI profile name | `DEFAULT` |
| `OCI_REGION` | OCI region | - |

### Available Tools (37 total)

#### Authentication (2 tools)
| Tool | Description |
|------|-------------|
| `create_session_token` | Create session token via browser SSO |
| `validate_session_token` | Check session token validity |

#### OKE Cluster Operations (8 tools)
| Tool | Description |
|------|-------------|
| `list_oke_clusters` | List OKE clusters in a compartment |
| `get_oke_cluster` | Get detailed cluster information |
| `get_kubeconfig` | Generate kubeconfig for cluster access |
| `list_node_pools` | List node pools |
| `get_node_pool` | Get node pool details |
| `list_nodes` | List nodes in a node pool |
| `scale_node_pool` | Scale node pool to specific size |
| `list_work_requests` | Track async OKE operations |

#### DevOps Projects (2 tools)
| Tool | Description |
|------|-------------|
| `list_devops_projects` | List DevOps projects |
| `get_devops_project` | Get project details |

#### Build Pipelines & Runs (6 tools)
| Tool | Description |
|------|-------------|
| `list_build_pipelines` | List build pipelines |
| `get_build_pipeline` | Get pipeline with stages |
| `list_build_runs` | List build executions |
| `get_build_run` | Get build run details |
| `trigger_build_run` | Start a new build |
| `cancel_build_run` | Cancel running build |

#### Deployment Pipelines & Deployments (7 tools)
| Tool | Description |
|------|-------------|
| `list_deploy_pipelines` | List deployment pipelines |
| `get_deploy_pipeline` | Get pipeline with stages |
| `list_deployments` | List deployments |
| `get_deployment` | Get deployment details |
| `create_deployment` | Trigger deployment |
| `approve_deployment` | Approve/reject deployment stage |
| `cancel_deployment` | Cancel running deployment |

#### DevOps Resources (9 tools)
| Tool | Description |
|------|-------------|
| `list_deploy_artifacts` | List deployment artifacts |
| `list_deploy_environments` | List deployment targets (OKE, compute) |
| `list_repositories` | List code repositories |
| `get_repository` | Get repository details |
| `list_repository_refs` | List branches/tags |
| `list_repository_commits` | List commits |
| `list_triggers` | List CI triggers |
| `list_connections` | List external SCM connections |

#### Infrastructure (3 tools)
| Tool | Description |
|------|-------------|
| `list_compartments` | List OCI compartments |
| `list_instances` | List compute instances |
| `list_bastions` | List bastion hosts |

### Example Usage with Claude

```
User: List all OKE clusters in my production compartment

Claude: I'll list the OKE clusters in your production compartment.
[Uses list_oke_clusters tool]

Found 2 OKE clusters:
1. prod-cluster-1 (v1.28.2) - ACTIVE
2. prod-cluster-2 (v1.27.10) - ACTIVE

User: Scale the prod-cluster-1 worker pool to 5 nodes

Claude: I'll scale the worker pool. First, let me get the node pools.
[Uses list_node_pools tool]
[Uses scale_node_pool tool]

Node pool scaling initiated. Work request ID: ocid1.workrequest...
Current status: IN_PROGRESS (0% complete)

User: Trigger a build for my app

Claude: I'll trigger a build. Let me list the available build pipelines first.
[Uses list_build_pipelines tool]
[Uses trigger_build_run tool]

Build run triggered successfully!
- Build Run ID: ocid1.buildrun...
- Status: ACCEPTED
- Pipeline: app-build-pipeline
```

---

## Atlassian MCP Server

MCP server for JIRA and Confluence integration.

### Prerequisites

1. **JIRA API Token:** Generate at https://id.atlassian.com/manage-profile/security/api-tokens
2. **Confluence API Token:** Same as JIRA token (if using Atlassian Cloud)

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `JIRA_URL` | JIRA instance URL | Yes |
| `JIRA_USERNAME` | JIRA username/email | Yes |
| `JIRA_API_TOKEN` | JIRA API token | Yes |
| `CONFLUENCE_URL` | Confluence instance URL | Yes |
| `CONFLUENCE_USERNAME` | Confluence username/email | Yes |
| `CONFLUENCE_API_TOKEN` | Confluence API token | Yes |
| `CONFLUENCE_SPACE_KEY` | Default Confluence space | No |

### Available Tools (11 total)

#### JIRA Tools (6 tools)
| Tool | Description |
|------|-------------|
| `get_my_jira_issues` | Get issues assigned to you |
| `search_jira_tickets` | Search with JQL |
| `get_sprint_tasks` | Get sprint issues |
| `create_jira_ticket` | Create new issue |
| `update_jira_ticket` | Update existing issue |
| `add_jira_comment` | Add comment to issue |

#### Confluence Tools (5 tools)
| Tool | Description |
|------|-------------|
| `search_confluence_pages` | Search pages with CQL |
| `get_confluence_page` | Get page content |
| `create_confluence_page` | Create new page |
| `update_confluence_page` | Update existing page |
| `get_recent_confluence_pages` | Get recently modified pages |

---

## Code Repos MCP Server

MCP server for managing and querying local code repositories.

### Configuration

Create a `repos.yaml` file:

```yaml
repositories:
  - name: my-project
    path: /path/to/my-project
    description: Main project repository
    tags: [python, api, backend]
    default_branch: main

  - name: frontend
    path: /path/to/frontend
    description: React frontend
    tags: [react, typescript, frontend]
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REPOS_CONFIG_PATH` | Path to repos.yaml | `./config/repos.yaml` |

### Available Tools (5 tools)

| Tool | Description |
|------|-------------|
| `list_repos` | List all configured repositories |
| `get_repo_info` | Get repository details with project type detection |
| `search_repos` | Search by query or tags |
| `get_repo_structure` | Get directory structure |
| `reload_config` | Reload repos.yaml configuration |

---

## Examples

### MVP Chatbot Agent

An interactive chatbot that connects to MCP servers and uses Claude for tool calling:

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY=your-api-key

# Run with code-repos server only
make chatbot

# Run with all servers
make chatbot-all
```

### MCP Client Library

Use the MCP client in your own projects:

```python
from examples.mcp_client import MCPClient, MCPServerConfig

config = MCPServerConfig(
    name="repos",
    command=["code-repos-mcp"],
)

async with MCPClient(config) as client:
    tools = await client.list_tools()
    result = await client.call_tool("list_repos", {})
```

---

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/your-org/mcp-services.git
cd mcp-services

# Install dependencies
uv sync --dev

# Run linting
uv run ruff check src/
uv run ruff format src/

# Run type checking
uv run mypy src/

# Run tests
uv run pytest tests/ -v
```

### Building the Package

```bash
uv build
```

This creates:
- `dist/mcp_servers_collection-*.whl` (wheel)
- `dist/mcp_servers_collection-*.tar.gz` (source)

### Makefile Commands

```bash
make install      # Install dependencies
make lint         # Run ruff linter
make format       # Format code with ruff
make typecheck    # Run mypy type checking
make test         # Run pytest
make check        # Run all checks
make run-oracle   # Run Oracle Cloud MCP
make run-atlassian # Run Atlassian MCP
make run-repos    # Run Code Repos MCP
```

### Project Structure

```
mcp-services/
├── src/
│   ├── mcp_servers/
│   │   ├── oracle_cloud/      # Oracle Cloud MCP (37 tools)
│   │   │   ├── auth.py        # OCI authentication
│   │   │   ├── client.py      # OCI client operations
│   │   │   ├── models.py      # Data models
│   │   │   ├── server.py      # MCP server
│   │   │   └── tools.py       # Tool implementations
│   │   ├── atlassian/         # Atlassian MCP (11 tools)
│   │   ├── code_repos/        # Code Repos MCP (5 tools)
│   │   └── common/            # Shared utilities
│   └── examples/              # Example implementations
├── examples/
│   └── claude_desktop_config.json  # Claude Desktop config example
├── config/
│   └── repos.yaml             # Repository configuration
├── tests/                     # Test suite
├── .github/
│   └── workflows/             # CI/CD workflows
│       └── ci.yml             # Test, build, upload artifacts
├── pyproject.toml
├── Makefile
└── README.md
```

---

## Skills

Each MCP server includes Claude Code skills with detailed usage instructions:

- `.claude/skills/oracle-cloud-mcp/SKILL.md` - OCI authentication and operations
- `.claude/skills/atlassian-mcp/SKILL.md` - JQL/CQL patterns and templates
- `.claude/skills/code-repos-mcp/SKILL.md` - Repository discovery patterns

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests and linting: `make check`
5. Commit your changes: `git commit -am 'Add my feature'`
6. Push to the branch: `git push origin feature/my-feature`
7. Submit a pull request

---

## License

MIT License - see LICENSE file for details.

---

## Support

- **Issues:** https://github.com/your-org/mcp-services/issues
- **Documentation:** https://github.com/your-org/mcp-services/wiki
