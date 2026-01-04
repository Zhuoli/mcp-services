# Oracle Cloud MCP Server

A comprehensive Model Context Protocol (MCP) server for Oracle Cloud Infrastructure (OCI) that enables AI assistants like Claude to manage OKE clusters, DevOps pipelines, and infrastructure resources.

## Overview

This MCP server provides **37 tools** for interacting with Oracle Cloud Infrastructure, including:

- **OKE (Oracle Kubernetes Engine)**: Cluster management, node pools, kubeconfig generation, scaling
- **OCI DevOps**: Build pipelines, deployment pipelines, artifacts, environments
- **Infrastructure**: Compute instances, compartments, bastions

## Prerequisites

### 1. OCI CLI Installation and Configuration

```bash
# Install OCI CLI
pip install oci-cli

# Configure OCI (interactive setup)
oci setup config
```

### 2. Session Token Authentication (Recommended)

For browser-based SSO authentication:

```bash
oci session authenticate --profile-name DEFAULT --region us-phoenix-1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OCI_CONFIG_FILE` | Path to OCI config file | `~/.oci/config` |
| `OCI_PROFILE` | OCI profile name | `DEFAULT` |
| `OCI_REGION` | OCI region (e.g., `us-phoenix-1`) | - |

## Running the Server

```bash
# Using uv (recommended)
uv run oracle-cloud-mcp

# Or directly with Python
python -m mcp_servers.oracle_cloud.server
```

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "oracle-cloud": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-services", "run", "oracle-cloud-mcp"],
      "env": {
        "OCI_CONFIG_FILE": "~/.oci/config",
        "OCI_PROFILE": "DEFAULT",
        "OCI_REGION": "us-phoenix-1"
      }
    }
  }
}
```

## Available Tools (37 total)

### Authentication (2 tools)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `create_session_token` | Create session token via browser SSO | `region` |
| `validate_session_token` | Check session token validity | `region` |

### Compartment Operations (1 tool)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_compartments` | List OCI compartments | `compartment_id`, `region` |

### Compute Instances (1 tool)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_instances` | List compute instances (optionally filter OKE nodes) | `compartment_id`, `region` |

### OKE Cluster Operations (8 tools)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_oke_clusters` | List OKE clusters in a compartment | `compartment_id`, `region` |
| `get_oke_cluster` | Get detailed cluster information | `cluster_id`, `region` |
| `get_kubeconfig` | Generate kubeconfig for cluster access | `cluster_id`, `region` |
| `list_node_pools` | List node pools in compartment/cluster | `compartment_id`, `region` |
| `get_node_pool` | Get node pool details | `node_pool_id`, `region` |
| `list_nodes` | List nodes in a node pool | `node_pool_id`, `region` |
| `scale_node_pool` | Scale node pool to specific size | `node_pool_id`, `size`, `region` |
| `list_work_requests` | Track async OKE operations | `compartment_id`, `region` |

### Bastion Operations (1 tool)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_bastions` | List bastion hosts | `compartment_id`, `region` |

### DevOps Projects (2 tools)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_devops_projects` | List DevOps projects | `compartment_id`, `region` |
| `get_devops_project` | Get project details | `project_id`, `region` |

### Build Pipelines & Runs (6 tools)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_build_pipelines` | List build pipelines in a project | `project_id`, `region` |
| `get_build_pipeline` | Get pipeline with stages | `build_pipeline_id`, `region` |
| `list_build_runs` | List build executions | `region` + one of: `project_id`, `build_pipeline_id`, `compartment_id` |
| `get_build_run` | Get build run details | `build_run_id`, `region` |
| `trigger_build_run` | Start a new build | `build_pipeline_id`, `region` |
| `cancel_build_run` | Cancel running build | `build_run_id`, `region` |

### Deployment Pipelines & Deployments (7 tools)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_deploy_pipelines` | List deployment pipelines | `project_id`, `region` |
| `get_deploy_pipeline` | Get pipeline with stages | `deploy_pipeline_id`, `region` |
| `list_deployments` | List deployments | `region` + one of: `project_id`, `deploy_pipeline_id`, `compartment_id` |
| `get_deployment` | Get deployment details | `deployment_id`, `region` |
| `create_deployment` | Trigger deployment | `deploy_pipeline_id`, `region` |
| `approve_deployment` | Approve/reject deployment stage | `deployment_id`, `stage_id`, `region` |
| `cancel_deployment` | Cancel running deployment | `deployment_id`, `region` |

### DevOps Artifacts & Environments (2 tools)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_deploy_artifacts` | List deployment artifacts | `project_id`, `region` |
| `list_deploy_environments` | List deployment targets (OKE, compute) | `project_id`, `region` |

### DevOps Repositories (4 tools)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_repositories` | List code repositories | `project_id`, `region` |
| `get_repository` | Get repository details | `repository_id`, `region` |
| `list_repository_refs` | List branches/tags | `repository_id`, `region` |
| `list_repository_commits` | List commits | `repository_id`, `region` |

### Triggers & Connections (2 tools)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_triggers` | List CI triggers | `project_id`, `region` |
| `list_connections` | List external SCM connections | `project_id`, `region` |

## Usage Examples

### Example 1: List OKE Clusters

```
User: List all OKE clusters in my production compartment

Claude: I'll list the OKE clusters in your production compartment.
[Uses list_oke_clusters tool with compartment_id and region]

Found 2 OKE clusters:
1. prod-cluster-1 (v1.28.2) - ACTIVE
2. prod-cluster-2 (v1.27.10) - ACTIVE
```

### Example 2: Scale Node Pool

```
User: Scale the prod-cluster-1 worker pool to 5 nodes

Claude: I'll scale the worker pool. First, let me get the node pools.
[Uses list_node_pools tool]
[Uses scale_node_pool tool with size=5]

Node pool scaling initiated. Work request ID: ocid1.workrequest...
Current status: IN_PROGRESS (0% complete)
```

### Example 3: Trigger a Build

```
User: Trigger a build for my app

Claude: I'll trigger a build. Let me list the available build pipelines first.
[Uses list_build_pipelines tool]
[Uses trigger_build_run tool]

Build run triggered successfully!
- Build Run ID: ocid1.buildrun...
- Status: ACCEPTED
- Pipeline: app-build-pipeline
```

### Example 4: Deploy to OKE

```
User: Deploy the latest version to production

Claude: I'll trigger the deployment pipeline.
[Uses list_deploy_pipelines tool]
[Uses create_deployment tool]

Deployment triggered successfully!
- Deployment ID: ocid1.deployment...
- Status: IN_PROGRESS
- Pipeline: prod-deploy-pipeline
```

## File Structure

```
src/mcp_servers/oracle_cloud/
├── __init__.py
├── server.py      # MCP server entry point
├── tools.py       # Tool implementations (37 tools)
├── client.py      # OCI client wrapper
├── auth.py        # Authentication helpers
├── models.py      # Data models
└── README.md      # This file
```

## Error Handling

All tools return JSON responses with consistent structure:

**Success:**
```json
{
  "region": "us-phoenix-1",
  "count": 2,
  "clusters": [...]
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

### Session Token Expired

If you see authentication errors, refresh your session token:

```bash
oci session authenticate --profile-name DEFAULT --region us-phoenix-1
```

### Permission Denied

Ensure your OCI user has the necessary IAM policies for the resources you're accessing.

### Region Not Set

Always specify the `region` parameter or set `OCI_REGION` environment variable.

## Related Resources

- [OCI CLI Documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm)
- [OKE Documentation](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm)
- [OCI DevOps Documentation](https://docs.oracle.com/en-us/iaas/Content/devops/using/home.htm)
