"""MCP Server for Oracle Cloud Infrastructure."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from rich.console import Console

from .tools import (
    approve_deployment_tool,
    cancel_build_run_tool,
    cancel_deployment_tool,
    create_deployment_tool,
    create_session_token_tool,
    get_build_pipeline_tool,
    get_build_run_tool,
    get_deploy_pipeline_tool,
    get_deployment_tool,
    get_devops_project_tool,
    get_kubeconfig_tool,
    get_node_pool_tool,
    get_oke_cluster_tool,
    get_repository_tool,
    list_bastions_tool,
    list_build_pipelines_tool,
    list_build_runs_tool,
    list_compartments_tool,
    list_connections_tool,
    list_deploy_artifacts_tool,
    list_deploy_environments_tool,
    list_deploy_pipelines_tool,
    list_deployments_tool,
    list_devops_projects_tool,
    list_instances_tool,
    list_node_pools_tool,
    list_nodes_tool,
    list_oke_clusters_tool,
    list_repositories_tool,
    list_repository_commits_tool,
    list_repository_refs_tool,
    list_triggers_tool,
    list_work_requests_tool,
    scale_node_pool_tool,
    trigger_build_run_tool,
    validate_session_token_tool,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console(stderr=True)

server = Server("oracle-cloud-mcp")

# Common properties used across tools
REGION_PROP = {
    "type": "string",
    "description": "OCI region name (e.g., us-phoenix-1, us-ashburn-1)",
}
COMPARTMENT_PROP = {
    "type": "string",
    "description": "Compartment OCID",
}
PROFILE_PROP = {
    "type": "string",
    "description": "OCI profile name (default: from OCI_PROFILE env or DEFAULT)",
}
CONFIG_FILE_PROP = {
    "type": "string",
    "description": "Optional path to OCI config file",
}
LIFECYCLE_STATE_PROP = {
    "type": "string",
    "description": "Filter by lifecycle state",
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Oracle Cloud tools."""
    return [
        # =====================================================================
        # Authentication Tools
        # =====================================================================
        Tool(
            name="create_session_token",
            description=(
                "Create a session token for OCI authentication via browser-based login. "
                "This initiates the OCI CLI session authenticate flow which opens a browser "
                "for SSO authentication. Required before other OCI operations if using "
                "session token authentication."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "profile_name": {
                        "type": "string",
                        "description": "OCI profile name to create/update (default: DEFAULT)",
                        "default": "DEFAULT",
                    },
                    "tenancy_name": {
                        "type": "string",
                        "description": "Tenancy name for authentication",
                        "default": "bmc_operator_access",
                    },
                    "config_file": CONFIG_FILE_PROP,
                    "timeout_minutes": {
                        "type": "integer",
                        "description": "Timeout for authentication in minutes",
                        "default": 5,
                    },
                },
                "required": ["region"],
            },
        ),
        Tool(
            name="validate_session_token",
            description=(
                "Check if the OCI session token is valid and how much time remains. "
                "Session tokens are typically valid for 60 minutes. Use this to verify "
                "authentication before performing operations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region"],
            },
        ),
        # =====================================================================
        # Compartment Tools
        # =====================================================================
        Tool(
            name="list_compartments",
            description=(
                "List OCI compartments under a parent compartment. Compartments are "
                "logical containers for organizing and isolating cloud resources."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "compartment_id": {
                        "type": "string",
                        "description": "Parent compartment OCID to search under",
                    },
                    "include_root": {
                        "type": "boolean",
                        "description": "Include the root compartment in results",
                        "default": False,
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "compartment_id"],
            },
        ),
        # =====================================================================
        # Compute Instance Tools
        # =====================================================================
        Tool(
            name="list_instances",
            description=(
                "List OCI compute instances in a compartment. Returns instance details "
                "including ID, name, IPs, shape, lifecycle state, and cluster association. "
                "Can filter to show only OKE (Kubernetes) cluster instances."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "compartment_id": COMPARTMENT_PROP,
                    "lifecycle_state": {
                        "type": "string",
                        "description": "Filter by lifecycle state",
                        "enum": ["RUNNING", "STOPPED", "TERMINATED", "PROVISIONING"],
                    },
                    "oke_only": {
                        "type": "boolean",
                        "description": "If true, only return OKE cluster instances",
                        "default": False,
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "compartment_id"],
            },
        ),
        # =====================================================================
        # OKE Cluster Tools
        # =====================================================================
        Tool(
            name="list_oke_clusters",
            description=(
                "List OKE (Oracle Kubernetes Engine) clusters in a compartment. Returns "
                "cluster details including ID, name, Kubernetes version, lifecycle state, "
                "and available upgrade versions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "compartment_id": COMPARTMENT_PROP,
                    "lifecycle_state": {
                        "type": "string",
                        "description": "Filter by lifecycle state",
                        "enum": ["ACTIVE", "CREATING", "DELETING", "DELETED", "FAILED", "UPDATING"],
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "compartment_id"],
            },
        ),
        Tool(
            name="get_oke_cluster",
            description=(
                "Get detailed information about an OKE cluster including endpoints, "
                "network configuration, available upgrades, and cluster options."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "cluster_id": {
                        "type": "string",
                        "description": "OKE cluster OCID",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "cluster_id"],
            },
        ),
        Tool(
            name="get_kubeconfig",
            description=(
                "Generate a kubeconfig file for accessing an OKE cluster. The kubeconfig "
                "can be used with kubectl to manage the cluster."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "cluster_id": {
                        "type": "string",
                        "description": "OKE cluster OCID",
                    },
                    "expiration_seconds": {
                        "type": "integer",
                        "description": "Token expiration in seconds (default: 30 days)",
                        "default": 2592000,
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "cluster_id"],
            },
        ),
        # =====================================================================
        # OKE Node Pool Tools
        # =====================================================================
        Tool(
            name="list_node_pools",
            description=(
                "List node pools in a compartment or cluster. Node pools are groups of "
                "worker nodes with the same configuration."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "compartment_id": COMPARTMENT_PROP,
                    "cluster_id": {
                        "type": "string",
                        "description": "Optional cluster OCID to filter by",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "compartment_id"],
            },
        ),
        Tool(
            name="get_node_pool",
            description=(
                "Get detailed information about a specific node pool including shape, "
                "image, node count, and configuration."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "node_pool_id": {
                        "type": "string",
                        "description": "Node pool OCID",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "node_pool_id"],
            },
        ),
        Tool(
            name="list_nodes",
            description=(
                "List nodes (worker instances) in a node pool with their IPs, status, "
                "and Kubernetes version."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "node_pool_id": {
                        "type": "string",
                        "description": "Node pool OCID",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "node_pool_id"],
            },
        ),
        Tool(
            name="scale_node_pool",
            description=(
                "Scale a node pool to a specific number of nodes. This is an async "
                "operation - use list_work_requests to monitor progress."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "node_pool_id": {
                        "type": "string",
                        "description": "Node pool OCID",
                    },
                    "size": {
                        "type": "integer",
                        "description": "Target number of nodes",
                        "minimum": 0,
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "node_pool_id", "size"],
            },
        ),
        Tool(
            name="list_work_requests",
            description=(
                "List work requests for OKE operations. Work requests track async "
                "operations like scaling, updates, and deletions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "compartment_id": COMPARTMENT_PROP,
                    "cluster_id": {
                        "type": "string",
                        "description": "Optional cluster OCID to filter by",
                    },
                    "status": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by status (e.g., IN_PROGRESS, SUCCEEDED, FAILED)",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "compartment_id"],
            },
        ),
        # =====================================================================
        # Bastion Tools
        # =====================================================================
        Tool(
            name="list_bastions",
            description=(
                "List bastion hosts in a compartment. Bastions provide secure SSH "
                "access to private instances."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "compartment_id": COMPARTMENT_PROP,
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "compartment_id"],
            },
        ),
        # =====================================================================
        # DevOps Project Tools
        # =====================================================================
        Tool(
            name="list_devops_projects",
            description=(
                "List OCI DevOps projects in a compartment. DevOps projects contain "
                "build pipelines, deployment pipelines, artifacts, and repositories."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "compartment_id": COMPARTMENT_PROP,
                    "name": {
                        "type": "string",
                        "description": "Optional project name filter",
                    },
                    "lifecycle_state": LIFECYCLE_STATE_PROP,
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "compartment_id"],
            },
        ),
        Tool(
            name="get_devops_project",
            description="Get detailed information about a DevOps project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "project_id": {
                        "type": "string",
                        "description": "DevOps project OCID",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "project_id"],
            },
        ),
        # =====================================================================
        # Build Pipeline Tools
        # =====================================================================
        Tool(
            name="list_build_pipelines",
            description=(
                "List build pipelines in a DevOps project. Build pipelines define "
                "the CI process for building and testing code."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "project_id": {
                        "type": "string",
                        "description": "DevOps project OCID",
                    },
                    "lifecycle_state": LIFECYCLE_STATE_PROP,
                    "display_name": {
                        "type": "string",
                        "description": "Optional display name filter",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "project_id"],
            },
        ),
        Tool(
            name="get_build_pipeline",
            description=(
                "Get detailed information about a build pipeline including its stages "
                "and parameters."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "build_pipeline_id": {
                        "type": "string",
                        "description": "Build pipeline OCID",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "build_pipeline_id"],
            },
        ),
        # =====================================================================
        # Build Run Tools
        # =====================================================================
        Tool(
            name="list_build_runs",
            description=(
                "List build runs (build executions). Can filter by project, pipeline, "
                "or lifecycle state."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "project_id": {
                        "type": "string",
                        "description": "Optional DevOps project OCID filter",
                    },
                    "build_pipeline_id": {
                        "type": "string",
                        "description": "Optional build pipeline OCID filter",
                    },
                    "compartment_id": {
                        "type": "string",
                        "description": "Optional compartment OCID filter",
                    },
                    "lifecycle_state": {
                        "type": "string",
                        "description": "Filter by lifecycle state",
                        "enum": ["ACCEPTED", "IN_PROGRESS", "FAILED", "SUCCEEDED", "CANCELING", "CANCELED"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 50,
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region"],
            },
        ),
        Tool(
            name="get_build_run",
            description=(
                "Get detailed information about a build run including progress, "
                "outputs, and stage execution details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "build_run_id": {
                        "type": "string",
                        "description": "Build run OCID",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "build_run_id"],
            },
        ),
        Tool(
            name="trigger_build_run",
            description=(
                "Trigger a new build run for a build pipeline. Optionally specify "
                "commit info and build arguments."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "build_pipeline_id": {
                        "type": "string",
                        "description": "Build pipeline OCID to trigger",
                    },
                    "display_name": {
                        "type": "string",
                        "description": "Optional display name for the build run",
                    },
                    "commit_info": {
                        "type": "object",
                        "description": "Optional commit information",
                        "properties": {
                            "repository_url": {"type": "string"},
                            "repository_branch": {"type": "string"},
                            "commit_hash": {"type": "string"},
                        },
                    },
                    "build_run_arguments": {
                        "type": "object",
                        "description": "Optional build arguments as key-value pairs",
                        "additionalProperties": {"type": "string"},
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "build_pipeline_id"],
            },
        ),
        Tool(
            name="cancel_build_run",
            description="Cancel a running build.",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "build_run_id": {
                        "type": "string",
                        "description": "Build run OCID to cancel",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional cancellation reason",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "build_run_id"],
            },
        ),
        # =====================================================================
        # Deploy Pipeline Tools
        # =====================================================================
        Tool(
            name="list_deploy_pipelines",
            description=(
                "List deployment pipelines in a DevOps project. Deployment pipelines "
                "define the CD process for deploying applications."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "project_id": {
                        "type": "string",
                        "description": "DevOps project OCID",
                    },
                    "lifecycle_state": LIFECYCLE_STATE_PROP,
                    "display_name": {
                        "type": "string",
                        "description": "Optional display name filter",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "project_id"],
            },
        ),
        Tool(
            name="get_deploy_pipeline",
            description=(
                "Get detailed information about a deployment pipeline including its "
                "stages and parameters."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "deploy_pipeline_id": {
                        "type": "string",
                        "description": "Deploy pipeline OCID",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "deploy_pipeline_id"],
            },
        ),
        # =====================================================================
        # Deployment Tools
        # =====================================================================
        Tool(
            name="list_deployments",
            description=(
                "List deployments (deployment executions). Can filter by project, "
                "pipeline, or lifecycle state."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "project_id": {
                        "type": "string",
                        "description": "Optional DevOps project OCID filter",
                    },
                    "deploy_pipeline_id": {
                        "type": "string",
                        "description": "Optional deploy pipeline OCID filter",
                    },
                    "compartment_id": {
                        "type": "string",
                        "description": "Optional compartment OCID filter",
                    },
                    "lifecycle_state": {
                        "type": "string",
                        "description": "Filter by lifecycle state",
                        "enum": ["ACCEPTED", "IN_PROGRESS", "FAILED", "SUCCEEDED", "CANCELING", "CANCELED"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 50,
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region"],
            },
        ),
        Tool(
            name="get_deployment",
            description=(
                "Get detailed information about a deployment including progress "
                "and stage execution details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "deployment_id": {
                        "type": "string",
                        "description": "Deployment OCID",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "deployment_id"],
            },
        ),
        Tool(
            name="create_deployment",
            description=(
                "Create a new deployment (trigger a deployment pipeline). Supports "
                "full pipeline, single stage, or redeployment modes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "deploy_pipeline_id": {
                        "type": "string",
                        "description": "Deploy pipeline OCID to trigger",
                    },
                    "display_name": {
                        "type": "string",
                        "description": "Optional display name for the deployment",
                    },
                    "deployment_arguments": {
                        "type": "object",
                        "description": "Optional deployment arguments as key-value pairs",
                        "additionalProperties": {"type": "string"},
                    },
                    "deploy_stage_id": {
                        "type": "string",
                        "description": "Optional stage ID for single stage deployment",
                    },
                    "previous_deployment_id": {
                        "type": "string",
                        "description": "Optional previous deployment ID for redeployment",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "deploy_pipeline_id"],
            },
        ),
        Tool(
            name="approve_deployment",
            description=(
                "Approve or reject a deployment stage that is waiting for manual approval."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "deployment_id": {
                        "type": "string",
                        "description": "Deployment OCID",
                    },
                    "stage_id": {
                        "type": "string",
                        "description": "Stage OCID requiring approval",
                    },
                    "action": {
                        "type": "string",
                        "description": "Action to take",
                        "enum": ["APPROVE", "REJECT"],
                        "default": "APPROVE",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for the action",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "deployment_id", "stage_id"],
            },
        ),
        Tool(
            name="cancel_deployment",
            description="Cancel a running deployment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "deployment_id": {
                        "type": "string",
                        "description": "Deployment OCID to cancel",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional cancellation reason",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "deployment_id"],
            },
        ),
        # =====================================================================
        # Deploy Artifacts Tools
        # =====================================================================
        Tool(
            name="list_deploy_artifacts",
            description=(
                "List deployment artifacts in a project. Artifacts include container "
                "images, Kubernetes manifests, Helm charts, and more."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "project_id": {
                        "type": "string",
                        "description": "DevOps project OCID",
                    },
                    "lifecycle_state": LIFECYCLE_STATE_PROP,
                    "display_name": {
                        "type": "string",
                        "description": "Optional display name filter",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "project_id"],
            },
        ),
        # =====================================================================
        # Deploy Environments Tools
        # =====================================================================
        Tool(
            name="list_deploy_environments",
            description=(
                "List deployment environments in a project. Environments define "
                "deployment targets like OKE clusters, compute instances, or functions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "project_id": {
                        "type": "string",
                        "description": "DevOps project OCID",
                    },
                    "lifecycle_state": LIFECYCLE_STATE_PROP,
                    "display_name": {
                        "type": "string",
                        "description": "Optional display name filter",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "project_id"],
            },
        ),
        # =====================================================================
        # DevOps Repository Tools
        # =====================================================================
        Tool(
            name="list_repositories",
            description=(
                "List code repositories in a DevOps project. Repositories can be "
                "hosted in OCI or mirrored from external sources like GitHub."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "project_id": {
                        "type": "string",
                        "description": "DevOps project OCID",
                    },
                    "lifecycle_state": LIFECYCLE_STATE_PROP,
                    "name": {
                        "type": "string",
                        "description": "Optional repository name filter",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "project_id"],
            },
        ),
        Tool(
            name="get_repository",
            description=(
                "Get detailed information about a code repository including URLs "
                "and mirror configuration."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "repository_id": {
                        "type": "string",
                        "description": "Repository OCID",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "repository_id"],
            },
        ),
        Tool(
            name="list_repository_refs",
            description=(
                "List refs (branches and tags) in a repository."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "repository_id": {
                        "type": "string",
                        "description": "Repository OCID",
                    },
                    "ref_type": {
                        "type": "string",
                        "description": "Filter by ref type",
                        "enum": ["BRANCH", "TAG"],
                    },
                    "ref_name": {
                        "type": "string",
                        "description": "Optional ref name filter",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "repository_id"],
            },
        ),
        Tool(
            name="list_repository_commits",
            description="List commits in a repository, optionally filtered by branch.",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "repository_id": {
                        "type": "string",
                        "description": "Repository OCID",
                    },
                    "ref_name": {
                        "type": "string",
                        "description": "Optional branch/tag name to list commits from",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of commits to return",
                        "default": 50,
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "repository_id"],
            },
        ),
        # =====================================================================
        # Trigger Tools
        # =====================================================================
        Tool(
            name="list_triggers",
            description=(
                "List triggers in a DevOps project. Triggers automatically start "
                "build pipelines based on events like code pushes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "project_id": {
                        "type": "string",
                        "description": "DevOps project OCID",
                    },
                    "lifecycle_state": LIFECYCLE_STATE_PROP,
                    "display_name": {
                        "type": "string",
                        "description": "Optional display name filter",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "project_id"],
            },
        ),
        # =====================================================================
        # Connection Tools
        # =====================================================================
        Tool(
            name="list_connections",
            description=(
                "List external SCM connections in a project. Connections enable "
                "integration with external repositories like GitHub or GitLab."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": REGION_PROP,
                    "project_id": {
                        "type": "string",
                        "description": "DevOps project OCID",
                    },
                    "lifecycle_state": LIFECYCLE_STATE_PROP,
                    "display_name": {
                        "type": "string",
                        "description": "Optional display name filter",
                    },
                    "profile_name": PROFILE_PROP,
                    "config_file": CONFIG_FILE_PROP,
                },
                "required": ["region", "project_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute a tool based on its name and arguments."""
    logger.info(f"Executing tool: {name} with arguments: {arguments}")

    tool_handlers = {
        # Authentication
        "create_session_token": create_session_token_tool,
        "validate_session_token": validate_session_token_tool,
        # Compartments
        "list_compartments": list_compartments_tool,
        # Compute Instances
        "list_instances": list_instances_tool,
        # OKE Clusters
        "list_oke_clusters": list_oke_clusters_tool,
        "get_oke_cluster": get_oke_cluster_tool,
        "get_kubeconfig": get_kubeconfig_tool,
        # OKE Node Pools
        "list_node_pools": list_node_pools_tool,
        "get_node_pool": get_node_pool_tool,
        "list_nodes": list_nodes_tool,
        "scale_node_pool": scale_node_pool_tool,
        "list_work_requests": list_work_requests_tool,
        # Bastions
        "list_bastions": list_bastions_tool,
        # DevOps Projects
        "list_devops_projects": list_devops_projects_tool,
        "get_devops_project": get_devops_project_tool,
        # Build Pipelines
        "list_build_pipelines": list_build_pipelines_tool,
        "get_build_pipeline": get_build_pipeline_tool,
        # Build Runs
        "list_build_runs": list_build_runs_tool,
        "get_build_run": get_build_run_tool,
        "trigger_build_run": trigger_build_run_tool,
        "cancel_build_run": cancel_build_run_tool,
        # Deploy Pipelines
        "list_deploy_pipelines": list_deploy_pipelines_tool,
        "get_deploy_pipeline": get_deploy_pipeline_tool,
        # Deployments
        "list_deployments": list_deployments_tool,
        "get_deployment": get_deployment_tool,
        "create_deployment": create_deployment_tool,
        "approve_deployment": approve_deployment_tool,
        "cancel_deployment": cancel_deployment_tool,
        # Deploy Artifacts
        "list_deploy_artifacts": list_deploy_artifacts_tool,
        # Deploy Environments
        "list_deploy_environments": list_deploy_environments_tool,
        # Repositories
        "list_repositories": list_repositories_tool,
        "get_repository": get_repository_tool,
        "list_repository_refs": list_repository_refs_tool,
        "list_repository_commits": list_repository_commits_tool,
        # Triggers
        "list_triggers": list_triggers_tool,
        # Connections
        "list_connections": list_connections_tool,
    }

    handler = tool_handlers.get(name)

    if not handler:
        error_message = f"Unknown tool: {name}. Available tools: {list(tool_handlers.keys())}"
        logger.error(error_message)
        return [TextContent(type="text", text=error_message)]

    try:
        result = await handler(arguments)
        logger.info(f"Tool {name} executed successfully")
        return [TextContent(type="text", text=result)]
    except Exception as e:
        error_message = f"Error executing tool {name}: {str(e)}"
        logger.error(error_message, exc_info=True)
        return [TextContent(type="text", text=error_message)]


def validate_oci_config() -> bool:
    """
    Validate OCI configuration at startup.

    Returns:
        True if configuration is valid, False otherwise
    """
    console.print("[blue]Oracle Cloud MCP Server - Startup Validation[/blue]")
    console.print("-" * 50)

    # Check for OCI config file
    config_file = os.environ.get("OCI_CONFIG_FILE")
    if config_file:
        config_path = Path(config_file)
    else:
        config_path = Path.home() / ".oci" / "config"

    if not config_path.exists():
        console.print(f"[red]ERROR: OCI config file not found: {config_path}[/red]")
        console.print("")
        console.print("[yellow]To fix this issue:[/yellow]")
        console.print("  1. Install OCI CLI: pip install oci-cli")
        console.print("  2. Run: oci setup config")
        console.print("  3. Or set OCI_CONFIG_FILE environment variable to your config path")
        console.print("")
        console.print("[dim]For session token authentication:[/dim]")
        console.print("  oci session authenticate --profile-name DEFAULT --region <region>")
        return False

    console.print(f"[green]✓[/green] OCI config file found: {config_path}")

    # Check profile
    profile_name = os.environ.get("OCI_PROFILE", "DEFAULT")

    try:
        import oci
        oci_config = oci.config.from_file(
            file_location=str(config_path),
            profile_name=profile_name
        )
        console.print(f"[green]✓[/green] Profile '{profile_name}' loaded successfully")

        # Check if using session token
        if oci_config.get("security_token_file"):
            token_path = Path(oci_config["security_token_file"])
            if not token_path.exists():
                console.print(f"[red]ERROR: Session token file not found: {token_path}[/red]")
                console.print("")
                console.print("[yellow]To fix this issue:[/yellow]")
                console.print(f"  oci session authenticate --profile-name {profile_name} --region <region>")
                return False

            # Check token age
            import time
            token_age_minutes = (time.time() - token_path.stat().st_mtime) / 60
            if token_age_minutes > 60:
                console.print(f"[yellow]⚠ Session token may be expired (age: {token_age_minutes:.0f} minutes)[/yellow]")
                console.print("[dim]  Use 'create_session_token' tool to refresh[/dim]")
            else:
                remaining = 60 - token_age_minutes
                console.print(f"[green]✓[/green] Session token valid (~{remaining:.0f} minutes remaining)")

        # Test connection
        console.print("[dim]Testing OCI connection...[/dim]")
        try:
            from .auth import OCIAuthenticator
            from .models import OCIConfig

            region = os.environ.get("OCI_REGION", oci_config.get("region", "us-phoenix-1"))
            config = OCIConfig(
                region=region,
                profile_name=profile_name,
                config_file=str(config_path)
            )
            authenticator = OCIAuthenticator(config)
            oci_config_dict, signer = authenticator.authenticate()

            # Quick API test
            identity_client = oci.identity.IdentityClient(oci_config_dict, signer=signer)
            regions = identity_client.list_regions()
            console.print(f"[green]✓[/green] Connection successful (found {len(regions.data)} regions)")

        except Exception as e:
            console.print(f"[red]ERROR: Connection test failed: {e}[/red]")
            console.print("")
            console.print("[yellow]Possible causes:[/yellow]")
            console.print("  - Session token expired (refresh with 'oci session authenticate')")
            console.print("  - Invalid API key configuration")
            console.print("  - Network connectivity issues")
            return False

    except Exception as e:
        console.print(f"[red]ERROR: Failed to load OCI config: {e}[/red]")
        console.print("")
        console.print("[yellow]To fix this issue:[/yellow]")
        console.print(f"  1. Ensure profile '{profile_name}' exists in {config_path}")
        console.print("  2. Or set OCI_PROFILE environment variable")
        return False

    console.print("-" * 50)
    console.print("[green]All validations passed. Server ready.[/green]")
    console.print(f"[dim]Available tools: 37[/dim]")
    console.print("")
    return True


async def run_server():
    """Run the MCP server."""
    logger.info("Starting Oracle Cloud MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server initialized and ready")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Entry point for the Oracle Cloud MCP server."""
    # Validate configuration before starting
    if not validate_oci_config():
        console.print("[red]Server startup aborted due to configuration errors.[/red]")
        sys.exit(1)

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
