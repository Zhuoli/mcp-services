# Atlassian MCP Server

A Model Context Protocol (MCP) server for integrating with Atlassian JIRA and Confluence, enabling AI assistants like Claude to manage issues, search content, and create documentation.

## Overview

This MCP server provides **11 tools** for interacting with Atlassian products:

- **JIRA** (6 tools): Issue management, search, sprint tasks, comments
- **Confluence** (5 tools): Page search, creation, updates, recent pages

## Prerequisites

### 1. API Token Generation

Generate an API token from your Atlassian account:

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a descriptive name
4. Copy the token (you won't be able to see it again)

### 2. Instance URLs

You'll need the URLs for your Atlassian Cloud instances:
- JIRA: `https://your-company.atlassian.net`
- Confluence: `https://your-company.atlassian.net/wiki`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `JIRA_URL` | JIRA instance URL (e.g., `https://company.atlassian.net`) | Yes |
| `JIRA_USERNAME` | JIRA username/email | Yes |
| `JIRA_API_TOKEN` | JIRA API token | Yes |
| `CONFLUENCE_URL` | Confluence instance URL (e.g., `https://company.atlassian.net/wiki`) | Yes |
| `CONFLUENCE_USERNAME` | Confluence username/email | Yes |
| `CONFLUENCE_API_TOKEN` | Confluence API token | Yes |
| `CONFLUENCE_SPACE_KEY` | Default Confluence space key | No |

## Running the Server

```bash
# Using uv (recommended)
uv run atlassian-mcp

# Or directly with Python
python -m mcp_servers.atlassian.server
```

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-services", "run", "atlassian-mcp"],
      "env": {
        "JIRA_URL": "https://your-company.atlassian.net",
        "JIRA_USERNAME": "your-email@company.com",
        "JIRA_API_TOKEN": "your-jira-api-token",
        "CONFLUENCE_URL": "https://your-company.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your-email@company.com",
        "CONFLUENCE_API_TOKEN": "your-confluence-api-token",
        "CONFLUENCE_SPACE_KEY": "TEAM"
      }
    }
  }
}
```

## Available Tools (11 total)

### JIRA Tools (6 tools)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `get_my_jira_issues` | Get issues assigned to you | None |
| `search_jira_tickets` | Search issues with JQL | `jql` |
| `get_sprint_tasks` | Get current sprint issues | None |
| `create_jira_ticket` | Create new issue | `project_key`, `summary` |
| `update_jira_ticket` | Update existing issue | `issue_key` |
| `add_jira_comment` | Add comment to issue | `issue_key`, `comment` |

### Confluence Tools (5 tools)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `search_confluence_pages` | Search pages with CQL | `query` |
| `get_confluence_page` | Get page content | `page_id` or `title` |
| `create_confluence_page` | Create new page | `title` |
| `update_confluence_page` | Update existing page | `page_id` |
| `get_recent_confluence_pages` | Get recently modified pages | None |

## Tool Details

### JIRA Tools

#### `get_my_jira_issues`

Get all issues assigned to the current user.

**Parameters:**
- `max_results` (optional, default: 50): Maximum number of results

**Example:**
```json
{
  "max_results": 20
}
```

#### `search_jira_tickets`

Search issues using JQL (JIRA Query Language).

**Parameters:**
- `jql` (required): JQL query string
- `max_results` (optional, default: 50): Maximum number of results

**Example:**
```json
{
  "jql": "project = MYPROJ AND status = 'In Progress'",
  "max_results": 25
}
```

**Common JQL Patterns:**
```
# Issues in a project
project = MYPROJ

# Open issues assigned to me
assignee = currentUser() AND status != Done

# High priority bugs
project = MYPROJ AND type = Bug AND priority = High

# Recently updated
updated >= -7d

# Sprint-based queries
sprint in openSprints() AND assignee = currentUser()
```

#### `get_sprint_tasks`

Get tasks in the current sprint assigned to you.

**Parameters:**
- `include_future_sprints` (optional, default: false): Include future sprints
- `max_results` (optional, default: 50): Maximum number of results

#### `create_jira_ticket`

Create a new JIRA issue.

**Parameters:**
- `project_key` (required): Project key (e.g., "MYPROJ")
- `summary` (required): Issue summary/title
- `description` (optional): Issue description
- `issue_type` (optional, default: "Task"): Issue type
- `priority` (optional): Priority level
- `labels` (optional): Array of labels

**Example:**
```json
{
  "project_key": "MYPROJ",
  "summary": "Implement user authentication",
  "description": "Add OAuth2 login support",
  "issue_type": "Story",
  "priority": "High",
  "labels": ["backend", "security"]
}
```

#### `update_jira_ticket`

Update an existing JIRA issue.

**Parameters:**
- `issue_key` (required): Issue key (e.g., "MYPROJ-123")
- `summary` (optional): New summary
- `description` (optional): New description
- `status` (optional): New status
- `priority` (optional): New priority
- `labels` (optional): New labels

#### `add_jira_comment`

Add a comment to an issue.

**Parameters:**
- `issue_key` (required): Issue key
- `comment` (required): Comment text

### Confluence Tools

#### `search_confluence_pages`

Search for Confluence pages.

**Parameters:**
- `query` (required): Search query (CQL or text)
- `space_key` (optional): Limit to specific space
- `max_results` (optional, default: 25): Maximum results

**Example:**
```json
{
  "query": "API documentation",
  "space_key": "TEAM",
  "max_results": 10
}
```

#### `get_confluence_page`

Get a specific Confluence page.

**Parameters:**
- `page_id` (optional): Page ID
- `title` (optional): Page title
- `space_key` (optional): Space key (required when using title)

*Note: Either `page_id` or `title` must be provided.*

#### `create_confluence_page`

Create a new Confluence page.

**Parameters:**
- `title` (required): Page title
- `body` (optional): Page content (HTML or storage format)
- `space_key` (optional): Space key (uses default if not specified)
- `parent_id` (optional): Parent page ID
- `template` (optional): Template to use
- `template_vars` (optional): Template variables

**Example:**
```json
{
  "title": "Sprint 42 Retrospective",
  "body": "<h1>What went well</h1><ul><li>Item 1</li></ul>",
  "space_key": "TEAM",
  "parent_id": "12345678"
}
```

#### `update_confluence_page`

Update an existing Confluence page.

**Parameters:**
- `page_id` (required): Page ID
- `title` (optional): New title
- `body` (optional): New content

#### `get_recent_confluence_pages`

Get recently modified pages.

**Parameters:**
- `space_key` (optional): Filter by space
- `max_results` (optional, default: 10): Maximum results

## Usage Examples

### Example 1: Get My Tasks

```
User: What JIRA tickets are assigned to me?

Claude: I'll get your assigned issues.
[Uses get_my_jira_issues tool]

You have 5 issues assigned:
1. PROJ-123 - Fix login bug (In Progress)
2. PROJ-124 - Add password reset (To Do)
3. PROJ-125 - Update API docs (In Review)
...
```

### Example 2: Search Issues

```
User: Find all high priority bugs in the BACKEND project

Claude: I'll search for high priority bugs.
[Uses search_jira_tickets with jql="project = BACKEND AND type = Bug AND priority = High"]

Found 3 high priority bugs:
1. BACKEND-89 - Database connection timeout (Critical)
2. BACKEND-92 - Memory leak in worker (High)
3. BACKEND-95 - API rate limiting broken (High)
```

### Example 3: Create Documentation

```
User: Create a Confluence page for our new API endpoint

Claude: I'll create the documentation page.
[Uses create_confluence_page tool]

Created page: "New API Endpoint Documentation"
- Page ID: 12345678
- URL: https://company.atlassian.net/wiki/spaces/TEAM/pages/12345678
```

### Example 4: Update Issue Status

```
User: Move PROJ-123 to Done and add a comment that it's deployed

Claude: I'll update the issue.
[Uses update_jira_ticket with status="Done"]
[Uses add_jira_comment with comment="Deployed to production"]

Updated PROJ-123:
- Status: Done
- Added comment: "Deployed to production"
```

## File Structure

```
src/mcp_servers/atlassian/
├── __init__.py
├── server.py           # MCP server entry point
├── tools.py            # Tool implementations (11 tools)
├── jira_client.py      # JIRA API client
├── confluence_client.py # Confluence API client
├── models.py           # Data models and config
└── README.md           # This file
```

## Error Handling

All tools return JSON responses with consistent structure:

**Success:**
```json
{
  "success": true,
  "count": 5,
  "issues": [...]
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

### Authentication Failed

Ensure your API token is correct and your username is the email address associated with your Atlassian account.

### Permission Denied

Check that your Atlassian account has access to the projects/spaces you're trying to access.

### Rate Limiting

Atlassian Cloud has rate limits. If you hit them, wait a few minutes before retrying.

## JQL Quick Reference

| Query | Description |
|-------|-------------|
| `project = PROJ` | Issues in project PROJ |
| `assignee = currentUser()` | Assigned to you |
| `status = "In Progress"` | In Progress status |
| `type = Bug` | Bug issues only |
| `priority = High` | High priority |
| `updated >= -7d` | Updated in last 7 days |
| `sprint in openSprints()` | In active sprints |
| `labels = backend` | Has "backend" label |

## Related Resources

- [JIRA REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Confluence REST API Documentation](https://developer.atlassian.com/cloud/confluence/rest/)
- [JQL Syntax Guide](https://support.atlassian.com/jira-software-cloud/docs/use-advanced-search-with-jira-query-language-jql/)
- [CQL Syntax Guide](https://developer.atlassian.com/cloud/confluence/advanced-searching-using-cql/)
