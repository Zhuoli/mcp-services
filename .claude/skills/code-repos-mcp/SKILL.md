# Code Repos MCP Server Skill

This skill provides instructions for using the Code Repos MCP server to discover and navigate code repositories.

## Skill Overview

**Purpose**: Enable AI assistants to understand the available code repositories and their purposes.

**When to use**: When the user needs to:
- Find the right repository for a task
- Understand what code exists in the codebase
- Navigate project structure
- Discover related projects

## Prerequisites

### Environment Variables

```bash
REPOS_CONFIG_PATH=./config/repos.yaml
```

### Configuration File

The repositories are defined in `config/repos.yaml`:

```yaml
repositories:
  - name: oracle-sdk-client
    path: /path/to/oracle-sdk-client
    description: Oracle Cloud SDK client with MCP server
    tags:
      - oracle
      - oci
      - kubernetes
    url: https://github.com/user/oracle-sdk-client
    default_branch: main

  - name: my-project
    path: /path/to/my-project
    description: My awesome project
    tags:
      - python
      - api
```

## Available Tools

### list_repos
List all configured repositories.

**Parameters**:
- `include_details`: Include full details (default: true)

**Returns**:
- Repository count
- List of repositories with name, path, description, tags
- All unique tags across repositories
- Existence status (whether path exists locally)

**Use when**: Starting a task to understand available projects

### get_repo_info
Get detailed information about a specific repository.

**Parameters**:
- `name` (required): Repository name

**Returns**:
- Full repository details
- Existence status
- Project type detection (python, javascript, rust, go)
- Presence of common files (README, package.json, pyproject.toml)

**Use when**: Need to understand a specific project before working on it

### search_repos
Search repositories by query or tags.

**Parameters**:
- `query`: Text to search in name and description
- `tags`: Array of tags to filter by

**Returns**: Matching repositories with full details

**Use when**: Looking for a specific type of project or technology

### get_repo_structure
Get the directory structure of a repository.

**Parameters**:
- `name` (required): Repository name
- `max_depth`: Maximum directory depth (default: 2)
- `include_hidden`: Include hidden files (default: false)

**Returns**: Tree structure of the repository

**Note**: Automatically skips:
- node_modules
- __pycache__
- .git
- venv, .venv

**Use when**: Understanding project layout before making changes

### reload_config
Reload the configuration from YAML file.

**Use when**: After updating repos.yaml to refresh the repository list

## Common Patterns

### Discover Available Projects

```
1. list_repos to see all configured repositories
2. Note the tags to understand technology categories
```

### Find Project for a Technology

```
1. search_repos with tags: ["python", "api"]
2. Review matching projects
3. get_repo_info for the most relevant one
```

### Understand Project Before Working

```
1. get_repo_info for project details and type
2. get_repo_structure to see the layout
3. Identify key files and directories
```

### Add New Repository

1. Edit `config/repos.yaml`:
```yaml
repositories:
  # ... existing repos ...

  - name: new-project
    path: /path/to/new-project
    description: Description of the new project
    tags:
      - relevant
      - tags
```

2. Use `reload_config` to refresh the list

## Project Type Detection

The `get_repo_info` tool detects project types by checking for:

| File | Project Type |
|------|--------------|
| pyproject.toml | Python |
| package.json | JavaScript/TypeScript |
| Cargo.toml | Rust |
| go.mod | Go |

## Tag Conventions

Recommended tag categories:

### Technology
- `python`, `javascript`, `typescript`, `rust`, `go`
- `react`, `vue`, `fastapi`, `django`

### Domain
- `infrastructure`, `devops`, `frontend`, `backend`
- `api`, `database`, `messaging`

### Product
- `trading`, `payments`, `documentation`
- `monitoring`, `analytics`

### Tool Type
- `mcp`, `cli`, `library`, `service`

## Integration with Other MCPs

### With Oracle Cloud MCP
```
1. search_repos with tags: ["oracle", "oci"]
2. Find relevant OCI-related projects
3. Use Oracle Cloud MCP for actual OCI operations
```

### With Atlassian MCP
```
1. get_repo_info to understand a project
2. Create Confluence documentation for it using Atlassian MCP
3. Link JIRA issues to the repository
```

## Best Practices

1. **Maintain accurate descriptions** - Help future discovery
2. **Use consistent tags** - Enable effective filtering
3. **Keep paths updated** - Use reload_config after moves
4. **Check existence** - The `exists` field shows if path is valid
5. **Use structure for navigation** - Before deep file operations

## Troubleshooting

### Repository Not Found
- Check the name spelling (case-insensitive)
- Use `list_repos` to see available names
- Ensure repos.yaml is correctly formatted

### Path Does Not Exist
- The repository may have been moved
- Update the path in repos.yaml
- Run `reload_config` after updating

### Configuration Not Updated
- Changes to repos.yaml require `reload_config`
- Check YAML syntax if reload fails
