# Atlassian MCP Server Skill

This skill provides instructions for using the Atlassian MCP server to interact with JIRA and Confluence.

## Skill Overview

**Purpose**: Enable AI assistants to manage JIRA issues and Confluence documentation.

**When to use**: When the user needs to:
- Track and manage JIRA issues
- Search and create Confluence documentation
- Get sprint tasks and work assignments
- Create documentation from templates

## Prerequisites

### Environment Variables

```bash
# JIRA Configuration
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# Confluence Configuration
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-api-token
CONFLUENCE_SPACE_KEY=TEAM
```

### API Token Generation
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create a new API token
3. Use the token as the API_TOKEN value

## JIRA Tools

### get_my_jira_issues
Get issues assigned to the current user.

**Parameters**:
- `max_results`: Maximum issues to return (default: 50)

**Returns**: Issues with key, summary, status, priority, sprint, story points

### search_jira_tickets
Search using JQL (JIRA Query Language).

**Parameters**:
- `jql` (required): JQL query string
- `max_results`: Maximum results (default: 50)

**Common JQL Patterns**:
```jql
# Issues in a project
project = PROJ

# Open bugs with high priority
project = PROJ AND type = Bug AND status != Done AND priority = High

# Recently updated issues
project = PROJ AND updated >= -7d ORDER BY updated DESC

# Issues in current sprint
sprint in openSprints() AND assignee = currentUser()

# Unassigned issues
project = PROJ AND assignee is EMPTY

# Issues with specific label
project = PROJ AND labels = "api-docs"

# Issues created this month
project = PROJ AND created >= startOfMonth()
```

### get_sprint_tasks
Get tasks in active/future sprints.

**Parameters**:
- `include_future_sprints`: Include future sprint tasks (default: false)
- `max_results`: Maximum results (default: 50)

### create_jira_ticket
Create a new JIRA issue.

**Parameters**:
- `project_key` (required): Project key (e.g., "PROJ")
- `summary` (required): Issue title
- `description`: Issue description
- `issue_type`: Type (Task, Bug, Story, Epic) - default: Task
- `priority`: Priority level
- `labels`: List of labels

### update_jira_ticket
Update an existing issue.

**Parameters**:
- `issue_key` (required): Issue key (e.g., "PROJ-123")
- `summary`: New summary
- `description`: New description
- `status`: New status (requires valid transition)
- `priority`: New priority
- `labels`: New labels (replaces existing)

### add_jira_comment
Add a comment to an issue.

**Parameters**:
- `issue_key` (required): Issue key
- `comment` (required): Comment text

## Confluence Tools

### search_confluence_pages
Search pages using text or CQL.

**Parameters**:
- `query` (required): Search text or CQL query
- `space_key`: Filter by space
- `max_results`: Maximum results (default: 25)

**Common CQL Patterns**:
```cql
# Text search
type=page AND text~"authentication"

# Pages in specific space
type=page AND space=TEAM ORDER BY lastModified DESC

# Recently updated
type=page AND space=TEAM AND lastModified >= -7d

# Pages with label
type=page AND label="api-docs"

# Pages by creator
type=page AND creator=currentUser()

# Stale documentation
type=page AND space=TEAM AND lastModified < -180d
```

### get_confluence_page
Get a page by ID or title.

**Parameters**:
- `page_id`: Page ID
- `title`: Page title (if page_id not provided)
- `space_key`: Space key (required with title)

### create_confluence_page
Create a new page with optional template.

**Parameters**:
- `title` (required): Page title
- `body`: HTML content (ignored if using template)
- `space_key`: Space key (uses default if not provided)
- `parent_id`: Parent page ID
- `template`: Template name (see Templates section)
- `template_vars`: Variables for template

### update_confluence_page
Update an existing page.

**Parameters**:
- `page_id` (required): Page ID
- `title`: New title
- `body`: New HTML content

### get_recent_confluence_pages
Get recently modified pages.

**Parameters**:
- `space_key`: Filter by space
- `max_results`: Maximum results (default: 10)

## Page Templates

### Available Templates

Use the `template` parameter when creating pages:

#### technical_doc
Technical documentation with sections for:
- Overview
- Architecture
- Key Components
- API Reference
- Configuration
- Troubleshooting
- Change Log

#### runbook
Operational runbook with:
- Service Overview
- Monitoring & Alerts
- Common Issues & Resolution
- Escalation Path
- Contact Information

#### meeting_notes
Meeting notes with:
- Attendees & Date
- Agenda
- Discussion Notes
- Decisions
- Action Items
- Next Meeting

#### project_doc
Project documentation with:
- Executive Summary
- Goals & Objectives
- Scope (In/Out)
- Timeline
- Team
- Risks & Mitigation
- Success Metrics

### Template Variables

Pass variables via `template_vars`:
```json
{
  "title": "Q1 Planning Meeting",
  "date": "2025-01-15",
  "attendees": "@john, @jane, @bob",
  "author": "John Smith"
}
```

## Common Workflows

### Create Documentation for a New Feature

```
1. search_confluence_pages to check if similar docs exist
2. create_confluence_page with template="technical_doc"
3. Link to related JIRA epic using update_confluence_page
```

### Track Sprint Progress

```
1. get_sprint_tasks to see current assignments
2. For each task, update status using update_jira_ticket
3. Add comments with add_jira_comment for progress updates
```

### Create Meeting Notes

```
1. create_confluence_page with template="meeting_notes"
2. Update template_vars with attendees and date
3. After meeting, update_confluence_page with actual notes
4. Create JIRA tasks for action items using create_jira_ticket
```

### Create Runbook for New Service

```
1. search_confluence_pages for existing runbook patterns
2. create_confluence_page with template="runbook"
3. Add service-specific information
4. Link to monitoring dashboards and JIRA project
```

## Best Practices

### JIRA
1. **Use JQL effectively** - complex queries save multiple API calls
2. **Include context in comments** - mention related tickets with [PROJ-123]
3. **Set appropriate priority** - helps with sprint planning
4. **Use labels consistently** - enables better filtering

### Confluence
1. **Use templates** - ensures consistent structure
2. **Organize with parent pages** - use parent_id for hierarchy
3. **Add labels** - improves discoverability
4. **Include table of contents** - for long documents
5. **Link related pages** - builds documentation network

### General
1. **Check before creating** - search first to avoid duplicates
2. **Keep content updated** - use update tools regularly
3. **Cross-reference** - link JIRA issues in Confluence and vice versa
