"""Basic tests for MCP servers."""


def test_oracle_cloud_imports():
    """Test that Oracle Cloud modules can be imported."""
    from mcp_servers.oracle_cloud import server as oracle_server
    from mcp_servers.oracle_cloud import tools as oracle_tools
    from mcp_servers.oracle_cloud import client as oracle_client
    from mcp_servers.oracle_cloud import models as oracle_models

    assert oracle_server is not None
    assert oracle_tools is not None
    assert oracle_client is not None
    assert oracle_models is not None


def test_atlassian_imports():
    """Test that Atlassian modules can be imported."""
    from mcp_servers.atlassian import server as atlassian_server
    from mcp_servers.atlassian import tools as atlassian_tools
    from mcp_servers.atlassian import jira_client
    from mcp_servers.atlassian import confluence_client

    assert atlassian_server is not None
    assert atlassian_tools is not None
    assert jira_client is not None
    assert confluence_client is not None


def test_code_repos_imports():
    """Test that Code Repos modules can be imported."""
    from mcp_servers.code_repos import server as repos_server
    from mcp_servers.code_repos import tools as repos_tools
    from mcp_servers.code_repos import models as repos_models

    assert repos_server is not None
    assert repos_tools is not None
    assert repos_models is not None


def test_common_imports():
    """Test that common modules can be imported."""
    from mcp_servers.common import base_server

    assert base_server is not None
    assert hasattr(base_server, "format_result")
    assert hasattr(base_server, "format_error")
