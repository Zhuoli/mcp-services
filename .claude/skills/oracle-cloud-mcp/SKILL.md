# Oracle Cloud MCP Server Skill

This skill provides instructions for using the Oracle Cloud MCP server to interact with Oracle Cloud Infrastructure (OCI).

## Skill Overview

**Purpose**: Enable AI assistants to interact with Oracle Cloud Infrastructure for managing OKE clusters, DevOps pipelines, compute instances, and more.

**When to use**: When the user needs to:
- Authenticate with OCI using session tokens
- Manage OKE (Kubernetes) clusters, node pools, and scaling
- Work with OCI DevOps build and deployment pipelines
- List or manage compute instances and bastions
- Access code repositories in OCI DevOps

## Prerequisites

### Environment Variables

```bash
# Required for OCI authentication
OCI_CONFIG_FILE=~/.oci/config    # Path to OCI config file
OCI_PROFILE=DEFAULT              # OCI profile name
OCI_REGION=us-phoenix-1          # Default region
```

### OCI CLI Installation

The OCI CLI is required for session token authentication:
```bash
pip install oci-cli
```

## Authentication

### Session Token Authentication (Recommended)

Session tokens provide time-limited access (60 minutes) via browser-based SSO:

1. **Create Session Token**:
   Use the `create_session_token` tool with:
   - `region`: Target region (e.g., "us-phoenix-1")
   - `profile_name`: Profile to create/update (default: "DEFAULT")
   - `tenancy_name`: Tenancy for authentication (default: "bmc_operator_access")

2. **Validate Token**:
   Use `validate_session_token` to check if the token is valid and see remaining time.

3. **Token Expiry**:
   - Tokens expire after 60 minutes
   - Validate before long operations
   - Create a new token when expired

### Example Authentication Flow

```
1. User: "Connect to OCI in us-phoenix-1"
2. Assistant: Use create_session_token tool
   - A browser window opens for SSO authentication
   - User completes authentication
   - Token is saved to ~/.oci/sessions/

3. User: "List my OKE clusters"
4. Assistant: First validate_session_token to ensure token is valid
5. Then use list_oke_clusters with the compartment_id
```

## Available Tools (37 total)

### Authentication Tools

| Tool | Description |
|------|-------------|
| `create_session_token` | Create session token via browser SSO |
| `validate_session_token` | Check token validity and remaining time |

### OKE Cluster Tools

| Tool | Description |
|------|-------------|
| `list_oke_clusters` | List OKE clusters in a compartment |
| `get_oke_cluster` | Get detailed cluster info (endpoints, versions, options) |
| `get_kubeconfig` | Generate kubeconfig for kubectl access |

### OKE Node Pool Tools

| Tool | Description |
|------|-------------|
| `list_node_pools` | List node pools in a compartment/cluster |
| `get_node_pool` | Get node pool details (shape, image, size) |
| `list_nodes` | List nodes in a node pool |
| `scale_node_pool` | Scale node pool to specific size |
| `list_work_requests` | Track async OKE operations |

### DevOps Project Tools

| Tool | Description |
|------|-------------|
| `list_devops_projects` | List DevOps projects |
| `get_devops_project` | Get project details |

### Build Pipeline Tools

| Tool | Description |
|------|-------------|
| `list_build_pipelines` | List build pipelines in a project |
| `get_build_pipeline` | Get pipeline with stages |
| `list_build_runs` | List build executions |
| `get_build_run` | Get build run details and progress |
| `trigger_build_run` | Start a new build |
| `cancel_build_run` | Cancel running build |

### Deployment Pipeline Tools

| Tool | Description |
|------|-------------|
| `list_deploy_pipelines` | List deployment pipelines |
| `get_deploy_pipeline` | Get pipeline with stages |
| `list_deployments` | List deployment executions |
| `get_deployment` | Get deployment details and progress |
| `create_deployment` | Trigger a deployment |
| `approve_deployment` | Approve/reject manual approval stage |
| `cancel_deployment` | Cancel running deployment |

### DevOps Resource Tools

| Tool | Description |
|------|-------------|
| `list_deploy_artifacts` | List deployment artifacts |
| `list_deploy_environments` | List deployment targets |
| `list_repositories` | List code repositories |
| `get_repository` | Get repository details |
| `list_repository_refs` | List branches/tags |
| `list_repository_commits` | List commits |
| `list_triggers` | List CI triggers |
| `list_connections` | List external SCM connections |

### Infrastructure Tools

| Tool | Description |
|------|-------------|
| `list_compartments` | List OCI compartments |
| `list_instances` | List compute instances |
| `list_bastions` | List bastion hosts |

## Common Patterns

### Manage OKE Cluster

```
1. list_oke_clusters to find clusters
2. get_oke_cluster for detailed info
3. list_node_pools to see worker pools
4. scale_node_pool to adjust capacity
5. list_work_requests to track scaling progress
```

### Get Kubeconfig for kubectl

```
1. get_kubeconfig with cluster_id
2. Save the returned kubeconfig to ~/.kube/config
3. Use kubectl to manage the cluster
```

### Trigger Build Pipeline

```
1. list_devops_projects to find project
2. list_build_pipelines to find pipeline
3. trigger_build_run with pipeline ID
4. get_build_run to monitor progress
```

### Deploy Application to OKE

```
1. list_deploy_pipelines to find pipeline
2. create_deployment with pipeline ID
3. If manual approval required:
   - get_deployment shows stage waiting for approval
   - approve_deployment to proceed
4. get_deployment to monitor completion
```

### Check Build/Deploy Status

```
1. list_build_runs or list_deployments with lifecycle_state filter
   - IN_PROGRESS: Currently running
   - SUCCEEDED: Completed successfully
   - FAILED: Execution failed
2. get_build_run or get_deployment for detailed stage progress
```

### Find OKE Cluster Nodes

```
1. list_instances with oke_only: true
2. Results include cluster_name for grouping
```

## Error Handling

### Token Expired
If operations fail with 401 errors:
1. Use validate_session_token to confirm expiry
2. Use create_session_token to get a new token
3. Retry the operation

### Compartment Not Found
If compartment_id is invalid:
1. Use list_compartments from a known parent to find valid IDs
2. Compartment OCIDs start with "ocid1.compartment.oc1.."

### Async Operations
Scaling and some DevOps operations are async:
1. The tool returns a work_request_id
2. Use list_work_requests to monitor progress
3. Check percent_complete and status fields

## Best Practices

1. **Always validate tokens first** before long-running operations
2. **Cache compartment IDs** - they don't change frequently
3. **Use OKE filtering** when specifically looking for Kubernetes nodes
4. **Check lifecycle states** to avoid operating on terminated resources
5. **Monitor async operations** using work requests for OKE or get_build_run/get_deployment for DevOps
6. **Use appropriate filters** to reduce API calls and response size
