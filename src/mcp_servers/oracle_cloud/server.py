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
    create_session_token_tool,
    list_bastions_tool,
    list_compartments_tool,
    list_instances_tool,
    list_oke_clusters_tool,
    validate_session_token_tool,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console(stderr=True)

server = Server("oracle-cloud-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Oracle Cloud tools."""
    return [
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
                    "region": {
                        "type": "string",
                        "description": "OCI region name (e.g., us-phoenix-1, us-ashburn-1)",
                    },
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
                    "config_file": {
                        "type": "string",
                        "description": "Optional path to OCI config file",
                    },
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
                    "region": {
                        "type": "string",
                        "description": "OCI region name",
                    },
                    "profile_name": {
                        "type": "string",
                        "description": "OCI profile name (default: from OCI_PROFILE env or DEFAULT)",
                    },
                    "config_file": {
                        "type": "string",
                        "description": "Optional path to OCI config file",
                    },
                },
                "required": ["region"],
            },
        ),
        Tool(
            name="list_compartments",
            description=(
                "List OCI compartments under a parent compartment. Compartments are "
                "logical containers for organizing and isolating cloud resources."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "OCI region name",
                    },
                    "compartment_id": {
                        "type": "string",
                        "description": "Parent compartment OCID to search under",
                    },
                    "include_root": {
                        "type": "boolean",
                        "description": "Include the root compartment in results",
                        "default": False,
                    },
                },
                "required": ["region", "compartment_id"],
            },
        ),
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
                    "region": {
                        "type": "string",
                        "description": "OCI region name",
                    },
                    "compartment_id": {
                        "type": "string",
                        "description": "Compartment OCID to search in",
                    },
                    "lifecycle_state": {
                        "type": "string",
                        "description": "Filter by lifecycle state (e.g., RUNNING, STOPPED)",
                        "enum": ["RUNNING", "STOPPED", "TERMINATED", "PROVISIONING"],
                    },
                    "oke_only": {
                        "type": "boolean",
                        "description": "If true, only return OKE cluster instances",
                        "default": False,
                    },
                },
                "required": ["region", "compartment_id"],
            },
        ),
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
                    "region": {
                        "type": "string",
                        "description": "OCI region name",
                    },
                    "compartment_id": {
                        "type": "string",
                        "description": "Compartment OCID",
                    },
                    "lifecycle_state": {
                        "type": "string",
                        "description": "Filter by lifecycle state",
                        "enum": ["ACTIVE", "CREATING", "DELETING", "DELETED", "FAILED"],
                    },
                },
                "required": ["region", "compartment_id"],
            },
        ),
        Tool(
            name="list_bastions",
            description=(
                "List bastion hosts in a compartment. Bastions provide secure SSH "
                "access to private instances. Returns bastion details including ID, "
                "name, type, target subnet, and session TTL."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "OCI region name",
                    },
                    "compartment_id": {
                        "type": "string",
                        "description": "Compartment OCID",
                    },
                },
                "required": ["region", "compartment_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute a tool based on its name and arguments."""
    logger.info(f"Executing tool: {name} with arguments: {arguments}")

    tool_handlers = {
        "create_session_token": create_session_token_tool,
        "validate_session_token": validate_session_token_tool,
        "list_compartments": list_compartments_tool,
        "list_instances": list_instances_tool,
        "list_oke_clusters": list_oke_clusters_tool,
        "list_bastions": list_bastions_tool,
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
