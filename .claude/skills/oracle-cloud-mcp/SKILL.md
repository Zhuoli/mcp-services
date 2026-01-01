# Oracle Cloud MCP Server Skill

This skill provides instructions for using the Oracle Cloud MCP server to interact with Oracle Cloud Infrastructure (OCI).

## Skill Overview

**Purpose**: Enable AI assistants to interact with Oracle Cloud Infrastructure for managing compute instances, OKE clusters, and bastions.

**When to use**: When the user needs to:
- Authenticate with OCI using session tokens
- List or manage compute instances
- Work with OKE (Kubernetes) clusters
- Access bastion hosts for SSH connectivity

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

3. User: "List my instances"
4. Assistant: First validate_session_token to ensure token is valid
5. Then use list_instances with the compartment_id
```

## Available Tools

### create_session_token
Create a new session token via browser-based authentication.

**When to use**: Before any OCI operations when using session auth, or when token has expired.

**Parameters**:
- `region` (required): OCI region name
- `profile_name`: Profile to create (default: DEFAULT)
- `tenancy_name`: Tenancy for auth (default: bmc_operator_access)
- `timeout_minutes`: Auth timeout (default: 5)

### validate_session_token
Check if the current session token is valid.

**When to use**: Before performing OCI operations to ensure authentication is valid.

**Parameters**:
- `region` (required): OCI region name
- `profile_name`: Profile to check

**Returns**: Validity status, token age, and remaining minutes

### list_compartments
List OCI compartments under a parent compartment.

**Parameters**:
- `region` (required): OCI region name
- `compartment_id` (required): Parent compartment OCID
- `include_root`: Include root compartment (default: false)

### list_instances
List compute instances in a compartment.

**Parameters**:
- `region` (required): OCI region name
- `compartment_id` (required): Compartment OCID
- `lifecycle_state`: Filter by state (RUNNING, STOPPED, etc.)
- `oke_only`: Only return OKE cluster instances (default: false)

### list_oke_clusters
List OKE (Kubernetes) clusters.

**Parameters**:
- `region` (required): OCI region name
- `compartment_id` (required): Compartment OCID
- `lifecycle_state`: Filter by state (ACTIVE, CREATING, etc.)

**Returns**: Cluster details including Kubernetes version and available upgrades

### list_bastions
List bastion hosts for SSH access to private instances.

**Parameters**:
- `region` (required): OCI region name
- `compartment_id` (required): Compartment OCID

## Common Patterns

### Get Running Instances in a Compartment

```
1. validate_session_token for the region
2. list_instances with:
   - region: "us-phoenix-1"
   - compartment_id: "ocid1.compartment.oc1..xxxxx"
   - lifecycle_state: "RUNNING"
```

### Find OKE Cluster Nodes

```
1. list_instances with oke_only: true
2. Results include cluster_name for grouping
```

### Check Available Kubernetes Upgrades

```
1. list_oke_clusters for the compartment
2. Check available_upgrades field for each cluster
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

### Region Not Available
Ensure the region name is valid (e.g., us-phoenix-1, us-ashburn-1, eu-frankfurt-1)

## Best Practices

1. **Always validate tokens first** before long-running operations
2. **Cache compartment IDs** - they don't change frequently
3. **Use OKE filtering** when specifically looking for Kubernetes nodes
4. **Check lifecycle states** to avoid operating on terminated resources
