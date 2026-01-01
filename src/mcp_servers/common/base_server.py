"""Base utilities for MCP servers."""

import json
import logging
from typing import Any

from mcp.types import TextContent

logger = logging.getLogger(__name__)


def format_result(data: Any, pretty: bool = True) -> str:
    """
    Format data as a string for MCP response.

    Args:
        data: Data to format (dict, list, or any JSON-serializable object)
        pretty: Whether to use pretty printing with indentation

    Returns:
        Formatted string representation
    """
    if isinstance(data, str):
        return data

    try:
        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize data: {e}")
        return str(data)


def format_error(error: Exception, context: str = "") -> str:
    """
    Format an error for MCP response.

    Args:
        error: The exception to format
        context: Additional context about where the error occurred

    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)

    if context:
        return f"Error ({error_type}) in {context}: {error_msg}"
    return f"Error ({error_type}): {error_msg}"


def create_text_response(content: str) -> list[TextContent]:
    """
    Create a standard MCP text response.

    Args:
        content: The text content to return

    Returns:
        List containing a single TextContent object
    """
    return [TextContent(type="text", text=content)]


def validate_required_params(arguments: dict, required: list[str]) -> tuple[bool, str]:
    """
    Validate that required parameters are present in arguments.

    Args:
        arguments: The arguments dictionary to check
        required: List of required parameter names

    Returns:
        Tuple of (is_valid, error_message)
    """
    missing = [param for param in required if param not in arguments or arguments[param] is None]

    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}"
    return True, ""
