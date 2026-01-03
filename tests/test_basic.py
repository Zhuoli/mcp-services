"""Basic tests for MCP servers."""


def test_imports():
    """Test that main modules can be imported."""
    from mcp_servers.oracle_cloud import server as oracle_server
    from mcp_servers.atlassian import server as atlassian_server
    from mcp_servers.code_repos import server as repos_server

    assert oracle_server is not None
    assert atlassian_server is not None
    assert repos_server is not None
