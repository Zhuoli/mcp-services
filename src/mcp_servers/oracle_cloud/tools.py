"""Tool implementations for Oracle Cloud MCP server."""

import functools
import logging
import os
from typing import Any, Awaitable, Callable, TypeVar

import oci

from ..common.base_server import format_auth_error, format_error, format_result
from .auth import OCIAuthenticationError, create_session_token, validate_session_token
from .client import OCIClient

logger = logging.getLogger(__name__)

# Type variable for async tool functions
F = TypeVar("F", bound=Callable[..., Awaitable[str]])


def oci_tool(tool_name: str) -> Callable[[F], F]:
    """
    Decorator for OCI tool functions that handles authentication errors gracefully.

    This decorator wraps async tool functions to catch authentication-related
    exceptions (OCIAuthenticationError and OCI ServiceError with status 401)
    and returns a structured JSON response with recovery instructions for
    agentic LLM clients.

    Args:
        tool_name: The name of the tool (used for logging and error context)

    Returns:
        Decorated function that handles auth errors with recovery instructions

    Example:
        @oci_tool("list_compartments")
        async def list_compartments_tool(arguments: dict[str, Any]) -> str:
            client = _get_client(arguments)
            # ... tool implementation
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(arguments: dict[str, Any]) -> str:
            try:
                return await func(arguments)
            except OCIAuthenticationError as e:
                logger.warning(f"Authentication error in {tool_name}: {e}")
                return format_auth_error(e.profile_name)
            except oci.exceptions.ServiceError as e:
                if e.status == 401:
                    # Extract profile name from arguments if available
                    profile_name = arguments.get(
                        "profile_name", os.environ.get("OCI_PROFILE", "DEFAULT")
                    )
                    logger.warning(
                        f"OCI 401 error in {tool_name}: {e.message}. "
                        f"Session token may be expired."
                    )
                    return format_auth_error(profile_name)
                # Re-raise other service errors to be handled by generic handler
                raise
            except Exception as e:
                return format_error(e, tool_name)

        return wrapper  # type: ignore[return-value]

    return decorator


def _get_client(arguments: dict[str, Any]) -> OCIClient:
    """Helper to create OCI client from arguments."""
    region = arguments["region"]
    profile_name = arguments.get("profile_name", os.environ.get("OCI_PROFILE", "DEFAULT"))
    config_file = arguments.get("config_file", os.environ.get("OCI_CONFIG_FILE"))
    return OCIClient(region=region, profile_name=profile_name, config_file=config_file)


# =============================================================================
# Authentication Tools
# =============================================================================


async def create_session_token_tool(arguments: dict[str, Any]) -> str:
    """
    Create a session token for OCI authentication.

    This initiates browser-based authentication with OCI.
    """
    profile_name = arguments.get("profile_name", "DEFAULT")
    region_name = arguments["region"]
    tenancy_name = arguments.get("tenancy_name", "bmc_operator_access")
    config_file = arguments.get("config_file")
    timeout = arguments.get("timeout_minutes", 5)

    try:
        success = create_session_token(
            profile_name=profile_name,
            region_name=region_name,
            tenancy_name=tenancy_name,
            config_file_path=config_file,
            timeout_minutes=timeout,
        )

        if success:
            return format_result({
                "success": True,
                "message": f"Session token created successfully for profile '{profile_name}'",
                "profile": profile_name,
                "region": region_name,
            })
        else:
            return format_result({
                "success": False,
                "message": "Failed to create session token. Check the logs for details.",
            })
    except Exception as e:
        return format_error(e, "create_session_token")


async def validate_session_token_tool(arguments: dict[str, Any]) -> str:
    """Validate if the session token is valid and check remaining time."""
    region = arguments["region"]
    profile_name = arguments.get("profile_name", os.environ.get("OCI_PROFILE", "DEFAULT"))
    config_file = arguments.get("config_file", os.environ.get("OCI_CONFIG_FILE"))

    try:
        result = validate_session_token(
            region=region,
            profile_name=profile_name,
            config_file=config_file,
        )
        return format_result(result)
    except Exception as e:
        return format_error(e, "validate_session_token")


# =============================================================================
# Compartment Tools
# =============================================================================


@oci_tool("list_compartments")
async def list_compartments_tool(arguments: dict[str, Any]) -> str:
    """List OCI compartments."""
    parent_compartment_id = arguments["compartment_id"]
    include_root = arguments.get("include_root", False)

    client = _get_client(arguments)
    compartments = client.list_compartments(parent_compartment_id, include_root=include_root)

    return format_result({
        "region": arguments["region"],
        "parent_compartment_id": parent_compartment_id,
        "count": len(compartments),
        "compartments": [c.to_dict() for c in compartments],
    })


# =============================================================================
# Compute Instance Tools
# =============================================================================


@oci_tool("list_instances")
async def list_instances_tool(arguments: dict[str, Any]) -> str:
    """List OCI compute instances."""
    compartment_id = arguments["compartment_id"]
    lifecycle_state = arguments.get("lifecycle_state")
    oke_only = arguments.get("oke_only", False)

    client = _get_client(arguments)
    instances = client.list_instances(compartment_id, lifecycle_state=lifecycle_state)

    if oke_only:
        # Filter for OKE instances by checking metadata
        oke_instances = []
        for instance in instances:
            metadata = instance.metadata
            is_oke = (
                metadata.get("oke-cluster-display-name")
                or metadata.get("oci.oraclecloud.com/oke-cluster-id")
                or metadata.get("oke-cluster-id")
            )
            if is_oke:
                instance.cluster_name = (
                    metadata.get("oke-cluster-display-name")
                    or metadata.get("oci.oraclecloud.com/oke-cluster-name")
                    or metadata.get("oke-cluster-name")
                )
                oke_instances.append(instance)
        instances = oke_instances

    return format_result({
        "region": arguments["region"],
        "compartment_id": compartment_id,
        "oke_only": oke_only,
        "count": len(instances),
        "instances": [i.to_dict() for i in instances],
    })


# =============================================================================
# OKE Cluster Tools
# =============================================================================


@oci_tool("list_oke_clusters")
async def list_oke_clusters_tool(arguments: dict[str, Any]) -> str:
    """List OKE clusters."""
    compartment_id = arguments["compartment_id"]
    lifecycle_state = arguments.get("lifecycle_state")

    client = _get_client(arguments)
    clusters = client.list_oke_clusters(compartment_id, lifecycle_state=lifecycle_state)

    return format_result({
        "region": arguments["region"],
        "compartment_id": compartment_id,
        "count": len(clusters),
        "clusters": [c.to_dict() for c in clusters],
    })


@oci_tool("get_oke_cluster")
async def get_oke_cluster_tool(arguments: dict[str, Any]) -> str:
    """Get detailed information about an OKE cluster."""
    cluster_id = arguments["cluster_id"]

    client = _get_client(arguments)
    cluster = client.get_oke_cluster(cluster_id)

    return format_result({
        "region": arguments["region"],
        "cluster": cluster.to_dict(),
    })


@oci_tool("get_kubeconfig")
async def get_kubeconfig_tool(arguments: dict[str, Any]) -> str:
    """Generate kubeconfig for an OKE cluster."""
    cluster_id = arguments["cluster_id"]
    expiration = arguments.get("expiration_seconds", 2592000)  # Default 30 days

    client = _get_client(arguments)
    kubeconfig = client.get_kubeconfig(cluster_id, expiration=expiration)

    return format_result({
        "region": arguments["region"],
        "cluster_id": cluster_id,
        "expiration_seconds": expiration,
        "kubeconfig": kubeconfig,
    })


# =============================================================================
# OKE Node Pool Tools
# =============================================================================


@oci_tool("list_node_pools")
async def list_node_pools_tool(arguments: dict[str, Any]) -> str:
    """List node pools in a compartment or cluster."""
    compartment_id = arguments["compartment_id"]
    cluster_id = arguments.get("cluster_id")

    client = _get_client(arguments)
    node_pools = client.list_node_pools(compartment_id, cluster_id=cluster_id)

    return format_result({
        "region": arguments["region"],
        "compartment_id": compartment_id,
        "cluster_id": cluster_id,
        "count": len(node_pools),
        "node_pools": [np.to_dict() for np in node_pools],
    })


@oci_tool("get_node_pool")
async def get_node_pool_tool(arguments: dict[str, Any]) -> str:
    """Get details of a specific node pool."""
    node_pool_id = arguments["node_pool_id"]

    client = _get_client(arguments)
    node_pool = client.get_node_pool(node_pool_id)

    return format_result({
        "region": arguments["region"],
        "node_pool": node_pool.to_dict(),
    })


@oci_tool("list_nodes")
async def list_nodes_tool(arguments: dict[str, Any]) -> str:
    """List nodes in a node pool."""
    node_pool_id = arguments["node_pool_id"]

    client = _get_client(arguments)
    nodes = client.list_nodes(node_pool_id)

    return format_result({
        "region": arguments["region"],
        "node_pool_id": node_pool_id,
        "count": len(nodes),
        "nodes": [n.to_dict() for n in nodes],
    })


@oci_tool("scale_node_pool")
async def scale_node_pool_tool(arguments: dict[str, Any]) -> str:
    """Scale a node pool to a specific size."""
    node_pool_id = arguments["node_pool_id"]
    size = arguments["size"]

    client = _get_client(arguments)
    work_request = client.scale_node_pool(node_pool_id, size)

    return format_result({
        "region": arguments["region"],
        "node_pool_id": node_pool_id,
        "target_size": size,
        "work_request": work_request.to_dict(),
        "message": f"Node pool scaling initiated. Work request ID: {work_request.work_request_id}",
    })


@oci_tool("list_work_requests")
async def list_work_requests_tool(arguments: dict[str, Any]) -> str:
    """List work requests for OKE operations."""
    compartment_id = arguments["compartment_id"]
    cluster_id = arguments.get("cluster_id")
    status = arguments.get("status")

    client = _get_client(arguments)
    work_requests = client.list_work_requests(
        compartment_id, cluster_id=cluster_id, status=status
    )

    return format_result({
        "region": arguments["region"],
        "compartment_id": compartment_id,
        "cluster_id": cluster_id,
        "count": len(work_requests),
        "work_requests": [wr.to_dict() for wr in work_requests],
    })


# =============================================================================
# Bastion Tools
# =============================================================================


@oci_tool("list_bastions")
async def list_bastions_tool(arguments: dict[str, Any]) -> str:
    """List OCI bastions."""
    compartment_id = arguments["compartment_id"]

    client = _get_client(arguments)
    bastions = client.list_bastions(compartment_id)

    return format_result({
        "region": arguments["region"],
        "compartment_id": compartment_id,
        "count": len(bastions),
        "bastions": [b.to_dict() for b in bastions],
    })


# =============================================================================
# DevOps Project Tools
# =============================================================================


@oci_tool("list_devops_projects")
async def list_devops_projects_tool(arguments: dict[str, Any]) -> str:
    """List DevOps projects in a compartment."""
    compartment_id = arguments["compartment_id"]
    name = arguments.get("name")
    lifecycle_state = arguments.get("lifecycle_state")

    client = _get_client(arguments)
    projects = client.list_devops_projects(
        compartment_id, name=name, lifecycle_state=lifecycle_state
    )

    return format_result({
        "region": arguments["region"],
        "compartment_id": compartment_id,
        "count": len(projects),
        "projects": [p.to_dict() for p in projects],
    })


@oci_tool("get_devops_project")
async def get_devops_project_tool(arguments: dict[str, Any]) -> str:
    """Get details of a DevOps project."""
    project_id = arguments["project_id"]

    client = _get_client(arguments)
    project = client.get_devops_project(project_id)

    return format_result({
        "region": arguments["region"],
        "project": project.to_dict(),
    })


# =============================================================================
# Build Pipeline Tools
# =============================================================================


@oci_tool("list_build_pipelines")
async def list_build_pipelines_tool(arguments: dict[str, Any]) -> str:
    """List build pipelines in a project."""
    project_id = arguments["project_id"]
    lifecycle_state = arguments.get("lifecycle_state")
    display_name = arguments.get("display_name")

    client = _get_client(arguments)
    pipelines = client.list_build_pipelines(
        project_id, lifecycle_state=lifecycle_state, display_name=display_name
    )

    return format_result({
        "region": arguments["region"],
        "project_id": project_id,
        "count": len(pipelines),
        "build_pipelines": [p.to_dict() for p in pipelines],
    })


@oci_tool("get_build_pipeline")
async def get_build_pipeline_tool(arguments: dict[str, Any]) -> str:
    """Get details of a build pipeline."""
    build_pipeline_id = arguments["build_pipeline_id"]

    client = _get_client(arguments)
    pipeline = client.get_build_pipeline(build_pipeline_id)
    stages = client.list_build_pipeline_stages(build_pipeline_id)

    return format_result({
        "region": arguments["region"],
        "build_pipeline": pipeline.to_dict(),
        "stages": [s.to_dict() for s in stages],
    })


# =============================================================================
# Build Run Tools
# =============================================================================


@oci_tool("list_build_runs")
async def list_build_runs_tool(arguments: dict[str, Any]) -> str:
    """List build runs."""
    project_id = arguments.get("project_id")
    build_pipeline_id = arguments.get("build_pipeline_id")
    compartment_id = arguments.get("compartment_id")
    lifecycle_state = arguments.get("lifecycle_state")
    limit = arguments.get("limit", 50)

    client = _get_client(arguments)
    runs = client.list_build_runs(
        project_id=project_id,
        build_pipeline_id=build_pipeline_id,
        compartment_id=compartment_id,
        lifecycle_state=lifecycle_state,
        limit=limit,
    )

    return format_result({
        "region": arguments["region"],
        "project_id": project_id,
        "build_pipeline_id": build_pipeline_id,
        "count": len(runs),
        "build_runs": [r.to_dict() for r in runs],
    })


@oci_tool("get_build_run")
async def get_build_run_tool(arguments: dict[str, Any]) -> str:
    """Get details of a build run."""
    build_run_id = arguments["build_run_id"]

    client = _get_client(arguments)
    run = client.get_build_run(build_run_id)

    return format_result({
        "region": arguments["region"],
        "build_run": run.to_dict(),
    })


@oci_tool("trigger_build_run")
async def trigger_build_run_tool(arguments: dict[str, Any]) -> str:
    """Trigger a new build run."""
    build_pipeline_id = arguments["build_pipeline_id"]
    display_name = arguments.get("display_name")
    commit_info = arguments.get("commit_info")
    build_run_arguments = arguments.get("build_run_arguments")

    client = _get_client(arguments)
    run = client.trigger_build_run(
        build_pipeline_id,
        display_name=display_name,
        commit_info=commit_info,
        build_run_arguments=build_run_arguments,
    )

    return format_result({
        "region": arguments["region"],
        "message": f"Build run triggered successfully: {run.build_run_id}",
        "build_run": run.to_dict(),
    })


@oci_tool("cancel_build_run")
async def cancel_build_run_tool(arguments: dict[str, Any]) -> str:
    """Cancel a running build."""
    build_run_id = arguments["build_run_id"]
    reason = arguments.get("reason")

    client = _get_client(arguments)
    run = client.cancel_build_run(build_run_id, reason=reason)

    return format_result({
        "region": arguments["region"],
        "message": f"Build run cancellation requested: {run.build_run_id}",
        "build_run": run.to_dict(),
    })


# =============================================================================
# Deploy Pipeline Tools
# =============================================================================


@oci_tool("list_deploy_pipelines")
async def list_deploy_pipelines_tool(arguments: dict[str, Any]) -> str:
    """List deployment pipelines in a project."""
    project_id = arguments["project_id"]
    lifecycle_state = arguments.get("lifecycle_state")
    display_name = arguments.get("display_name")

    client = _get_client(arguments)
    pipelines = client.list_deploy_pipelines(
        project_id, lifecycle_state=lifecycle_state, display_name=display_name
    )

    return format_result({
        "region": arguments["region"],
        "project_id": project_id,
        "count": len(pipelines),
        "deploy_pipelines": [p.to_dict() for p in pipelines],
    })


@oci_tool("get_deploy_pipeline")
async def get_deploy_pipeline_tool(arguments: dict[str, Any]) -> str:
    """Get details of a deployment pipeline."""
    deploy_pipeline_id = arguments["deploy_pipeline_id"]

    client = _get_client(arguments)
    pipeline = client.get_deploy_pipeline(deploy_pipeline_id)
    stages = client.list_deploy_stages(deploy_pipeline_id)

    return format_result({
        "region": arguments["region"],
        "deploy_pipeline": pipeline.to_dict(),
        "stages": [s.to_dict() for s in stages],
    })


# =============================================================================
# Deployment Tools
# =============================================================================


@oci_tool("list_deployments")
async def list_deployments_tool(arguments: dict[str, Any]) -> str:
    """List deployments."""
    project_id = arguments.get("project_id")
    deploy_pipeline_id = arguments.get("deploy_pipeline_id")
    compartment_id = arguments.get("compartment_id")
    lifecycle_state = arguments.get("lifecycle_state")
    limit = arguments.get("limit", 50)

    client = _get_client(arguments)
    deployments = client.list_deployments(
        project_id=project_id,
        deploy_pipeline_id=deploy_pipeline_id,
        compartment_id=compartment_id,
        lifecycle_state=lifecycle_state,
        limit=limit,
    )

    return format_result({
        "region": arguments["region"],
        "project_id": project_id,
        "deploy_pipeline_id": deploy_pipeline_id,
        "count": len(deployments),
        "deployments": [d.to_dict() for d in deployments],
    })


@oci_tool("get_deployment")
async def get_deployment_tool(arguments: dict[str, Any]) -> str:
    """Get details of a deployment."""
    deployment_id = arguments["deployment_id"]

    client = _get_client(arguments)
    deployment = client.get_deployment(deployment_id)

    return format_result({
        "region": arguments["region"],
        "deployment": deployment.to_dict(),
    })


@oci_tool("create_deployment")
async def create_deployment_tool(arguments: dict[str, Any]) -> str:
    """Create a new deployment (trigger a deployment pipeline)."""
    deploy_pipeline_id = arguments["deploy_pipeline_id"]
    display_name = arguments.get("display_name")
    deployment_arguments = arguments.get("deployment_arguments")
    deploy_stage_id = arguments.get("deploy_stage_id")
    previous_deployment_id = arguments.get("previous_deployment_id")

    client = _get_client(arguments)
    deployment = client.create_deployment(
        deploy_pipeline_id,
        display_name=display_name,
        deployment_arguments=deployment_arguments,
        deploy_stage_id=deploy_stage_id,
        previous_deployment_id=previous_deployment_id,
    )

    return format_result({
        "region": arguments["region"],
        "message": f"Deployment triggered successfully: {deployment.deployment_id}",
        "deployment": deployment.to_dict(),
    })


@oci_tool("approve_deployment")
async def approve_deployment_tool(arguments: dict[str, Any]) -> str:
    """Approve or reject a deployment stage waiting for approval."""
    deployment_id = arguments["deployment_id"]
    stage_id = arguments["stage_id"]
    action = arguments.get("action", "APPROVE")
    reason = arguments.get("reason")

    client = _get_client(arguments)
    deployment = client.approve_deployment(
        deployment_id, stage_id, action=action, reason=reason
    )

    return format_result({
        "region": arguments["region"],
        "message": f"Deployment {action.lower()}d: {deployment.deployment_id}",
        "deployment": deployment.to_dict(),
    })


@oci_tool("cancel_deployment")
async def cancel_deployment_tool(arguments: dict[str, Any]) -> str:
    """Cancel a running deployment."""
    deployment_id = arguments["deployment_id"]
    reason = arguments.get("reason")

    client = _get_client(arguments)
    deployment = client.cancel_deployment(deployment_id, reason=reason)

    return format_result({
        "region": arguments["region"],
        "message": f"Deployment cancellation requested: {deployment.deployment_id}",
        "deployment": deployment.to_dict(),
    })


# =============================================================================
# Deploy Artifacts Tools
# =============================================================================


@oci_tool("list_deploy_artifacts")
async def list_deploy_artifacts_tool(arguments: dict[str, Any]) -> str:
    """List deployment artifacts in a project."""
    project_id = arguments["project_id"]
    lifecycle_state = arguments.get("lifecycle_state")
    display_name = arguments.get("display_name")

    client = _get_client(arguments)
    artifacts = client.list_deploy_artifacts(
        project_id, lifecycle_state=lifecycle_state, display_name=display_name
    )

    return format_result({
        "region": arguments["region"],
        "project_id": project_id,
        "count": len(artifacts),
        "artifacts": [a.to_dict() for a in artifacts],
    })


# =============================================================================
# Deploy Environments Tools
# =============================================================================


@oci_tool("list_deploy_environments")
async def list_deploy_environments_tool(arguments: dict[str, Any]) -> str:
    """List deployment environments in a project."""
    project_id = arguments["project_id"]
    lifecycle_state = arguments.get("lifecycle_state")
    display_name = arguments.get("display_name")

    client = _get_client(arguments)
    environments = client.list_deploy_environments(
        project_id, lifecycle_state=lifecycle_state, display_name=display_name
    )

    return format_result({
        "region": arguments["region"],
        "project_id": project_id,
        "count": len(environments),
        "environments": [e.to_dict() for e in environments],
    })


# =============================================================================
# DevOps Repository Tools
# =============================================================================


@oci_tool("list_repositories")
async def list_repositories_tool(arguments: dict[str, Any]) -> str:
    """List code repositories in a DevOps project."""
    project_id = arguments["project_id"]
    lifecycle_state = arguments.get("lifecycle_state")
    name = arguments.get("name")

    client = _get_client(arguments)
    repositories = client.list_repositories(
        project_id, lifecycle_state=lifecycle_state, name=name
    )

    return format_result({
        "region": arguments["region"],
        "project_id": project_id,
        "count": len(repositories),
        "repositories": [r.to_dict() for r in repositories],
    })


@oci_tool("get_repository")
async def get_repository_tool(arguments: dict[str, Any]) -> str:
    """Get details of a code repository."""
    repository_id = arguments["repository_id"]

    client = _get_client(arguments)
    repository = client.get_repository(repository_id)

    return format_result({
        "region": arguments["region"],
        "repository": repository.to_dict(),
    })


@oci_tool("list_repository_refs")
async def list_repository_refs_tool(arguments: dict[str, Any]) -> str:
    """List refs (branches/tags) in a repository."""
    repository_id = arguments["repository_id"]
    ref_type = arguments.get("ref_type")
    ref_name = arguments.get("ref_name")

    client = _get_client(arguments)
    refs = client.list_repository_refs(
        repository_id, ref_type=ref_type, ref_name=ref_name
    )

    return format_result({
        "region": arguments["region"],
        "repository_id": repository_id,
        "count": len(refs),
        "refs": [r.to_dict() for r in refs],
    })


@oci_tool("list_repository_commits")
async def list_repository_commits_tool(arguments: dict[str, Any]) -> str:
    """List commits in a repository."""
    repository_id = arguments["repository_id"]
    ref_name = arguments.get("ref_name")
    limit = arguments.get("limit", 50)

    client = _get_client(arguments)
    commits = client.list_repository_commits(
        repository_id, ref_name=ref_name, limit=limit
    )

    return format_result({
        "region": arguments["region"],
        "repository_id": repository_id,
        "ref_name": ref_name,
        "count": len(commits),
        "commits": [c.to_dict() for c in commits],
    })


# =============================================================================
# Trigger Tools
# =============================================================================


@oci_tool("list_triggers")
async def list_triggers_tool(arguments: dict[str, Any]) -> str:
    """List triggers in a project."""
    project_id = arguments["project_id"]
    lifecycle_state = arguments.get("lifecycle_state")
    display_name = arguments.get("display_name")

    client = _get_client(arguments)
    triggers = client.list_triggers(
        project_id, lifecycle_state=lifecycle_state, display_name=display_name
    )

    return format_result({
        "region": arguments["region"],
        "project_id": project_id,
        "count": len(triggers),
        "triggers": [t.to_dict() for t in triggers],
    })


# =============================================================================
# Connection Tools
# =============================================================================


@oci_tool("list_connections")
async def list_connections_tool(arguments: dict[str, Any]) -> str:
    """List external SCM connections in a project."""
    project_id = arguments["project_id"]
    lifecycle_state = arguments.get("lifecycle_state")
    display_name = arguments.get("display_name")

    client = _get_client(arguments)
    connections = client.list_connections(
        project_id, lifecycle_state=lifecycle_state, display_name=display_name
    )

    return format_result({
        "region": arguments["region"],
        "project_id": project_id,
        "count": len(connections),
        "connections": [c.to_dict() for c in connections],
    })
