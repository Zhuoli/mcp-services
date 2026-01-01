"""Tool implementations for Oracle Cloud MCP server."""

import logging
import os
from typing import Any

from ..common.base_server import format_error, format_result
from .auth import create_session_token, validate_session_token
from .client import OCIClient

logger = logging.getLogger(__name__)


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


async def list_compartments_tool(arguments: dict[str, Any]) -> str:
    """List OCI compartments."""
    region = arguments["region"]
    parent_compartment_id = arguments["compartment_id"]
    include_root = arguments.get("include_root", False)
    profile_name = arguments.get("profile_name", os.environ.get("OCI_PROFILE", "DEFAULT"))
    config_file = arguments.get("config_file", os.environ.get("OCI_CONFIG_FILE"))

    try:
        client = OCIClient(region=region, profile_name=profile_name, config_file=config_file)
        compartments = client.list_compartments(parent_compartment_id, include_root=include_root)

        return format_result({
            "region": region,
            "parent_compartment_id": parent_compartment_id,
            "count": len(compartments),
            "compartments": [c.to_dict() for c in compartments],
        })
    except Exception as e:
        return format_error(e, "list_compartments")


async def list_instances_tool(arguments: dict[str, Any]) -> str:
    """List OCI compute instances."""
    region = arguments["region"]
    compartment_id = arguments["compartment_id"]
    lifecycle_state = arguments.get("lifecycle_state")
    oke_only = arguments.get("oke_only", False)
    profile_name = arguments.get("profile_name", os.environ.get("OCI_PROFILE", "DEFAULT"))
    config_file = arguments.get("config_file", os.environ.get("OCI_CONFIG_FILE"))

    try:
        client = OCIClient(region=region, profile_name=profile_name, config_file=config_file)
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
            "region": region,
            "compartment_id": compartment_id,
            "oke_only": oke_only,
            "count": len(instances),
            "instances": [i.to_dict() for i in instances],
        })
    except Exception as e:
        return format_error(e, "list_instances")


async def list_oke_clusters_tool(arguments: dict[str, Any]) -> str:
    """List OKE clusters."""
    region = arguments["region"]
    compartment_id = arguments["compartment_id"]
    lifecycle_state = arguments.get("lifecycle_state")
    profile_name = arguments.get("profile_name", os.environ.get("OCI_PROFILE", "DEFAULT"))
    config_file = arguments.get("config_file", os.environ.get("OCI_CONFIG_FILE"))

    try:
        client = OCIClient(region=region, profile_name=profile_name, config_file=config_file)
        clusters = client.list_oke_clusters(compartment_id, lifecycle_state=lifecycle_state)

        return format_result({
            "region": region,
            "compartment_id": compartment_id,
            "count": len(clusters),
            "clusters": [c.to_dict() for c in clusters],
        })
    except Exception as e:
        return format_error(e, "list_oke_clusters")


async def list_bastions_tool(arguments: dict[str, Any]) -> str:
    """List OCI bastions."""
    region = arguments["region"]
    compartment_id = arguments["compartment_id"]
    profile_name = arguments.get("profile_name", os.environ.get("OCI_PROFILE", "DEFAULT"))
    config_file = arguments.get("config_file", os.environ.get("OCI_CONFIG_FILE"))

    try:
        client = OCIClient(region=region, profile_name=profile_name, config_file=config_file)
        bastions = client.list_bastions(compartment_id)

        return format_result({
            "region": region,
            "compartment_id": compartment_id,
            "count": len(bastions),
            "bastions": [b.to_dict() for b in bastions],
        })
    except Exception as e:
        return format_error(e, "list_bastions")
