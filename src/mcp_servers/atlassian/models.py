"""Data models for Atlassian MCP server."""

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings


class AtlassianConfig(BaseSettings):
    """Atlassian configuration from environment variables."""

    model_config = ConfigDict(env_prefix="", case_sensitive=False)

    # JIRA configuration
    jira_url: str = ""
    jira_username: str = ""
    jira_api_token: str = ""

    # Confluence configuration
    confluence_url: str = ""
    confluence_username: str = ""
    confluence_api_token: str = ""
    confluence_space_key: str = ""

    # User email for filtering
    user_email: Optional[str] = None


@dataclass
class JiraIssue:
    """JIRA issue information."""

    key: str
    summary: str
    status: str
    issue_type: str
    priority: Optional[str] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    description: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    labels: list[str] = field(default_factory=list)
    sprint: Optional[str] = None
    story_points: Optional[float] = None
    url: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "summary": self.summary,
            "status": self.status,
            "issue_type": self.issue_type,
            "priority": self.priority,
            "assignee": self.assignee,
            "reporter": self.reporter,
            "description": self.description[:500] if self.description else None,
            "created": self.created,
            "updated": self.updated,
            "labels": self.labels,
            "sprint": self.sprint,
            "story_points": self.story_points,
            "url": self.url,
        }


@dataclass
class ConfluencePage:
    """Confluence page information."""

    page_id: str
    title: str
    space_key: str
    status: str = "current"
    version: int = 1
    url: Optional[str] = None
    body: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    creator: Optional[str] = None
    last_modifier: Optional[str] = None
    parent_id: Optional[str] = None
    labels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "page_id": self.page_id,
            "title": self.title,
            "space_key": self.space_key,
            "status": self.status,
            "version": self.version,
            "url": self.url,
            "body_preview": self.body[:500] if self.body else None,
            "created": self.created,
            "updated": self.updated,
            "creator": self.creator,
            "last_modifier": self.last_modifier,
            "parent_id": self.parent_id,
            "labels": self.labels,
        }


# Confluence page templates
CONFLUENCE_TEMPLATES = {
    "technical_doc": """<h1>{title}</h1>

<h2>Overview</h2>
<p>Brief description of what this is and why it exists.</p>

<h2>Architecture</h2>
<p>High-level architecture diagram and explanation.</p>

<h2>Key Components</h2>
<ul>
<li><strong>Component 1</strong>: Description</li>
<li><strong>Component 2</strong>: Description</li>
</ul>

<h2>API Reference</h2>
<h3>Endpoints</h3>
<ul>
<li><code>GET /api/resource</code>: Description</li>
<li><code>POST /api/resource</code>: Description</li>
</ul>

<h2>Configuration</h2>
<p>How to configure this feature/component.</p>

<h2>Troubleshooting</h2>
<p>Common issues and solutions.</p>

<h2>Related Documentation</h2>
<ul>
<li>Link to related page 1</li>
<li>Link to related page 2</li>
</ul>

<h2>Change Log</h2>
<table>
<tr><th>Date</th><th>Author</th><th>Change</th></tr>
<tr><td>{date}</td><td>{author}</td><td>Initial version</td></tr>
</table>
""",
    "runbook": """<h1>{title} Runbook</h1>

<h2>Service Overview</h2>
<p>What is this service? What does it do?</p>

<h2>Monitoring &amp; Alerts</h2>
<ul>
<li><strong>Dashboard</strong>: Link to dashboard</li>
<li><strong>Key Metrics</strong>: List of important metrics</li>
<li><strong>Alert Conditions</strong>: When alerts fire</li>
</ul>

<h2>Common Issues</h2>

<h3>Issue 1: [Problem Description]</h3>
<p><strong>Symptoms</strong>: What you'll observe</p>
<p><strong>Cause</strong>: Why this happens</p>
<p><strong>Resolution</strong>:</p>
<ol>
<li>Step 1</li>
<li>Step 2</li>
<li>Step 3</li>
</ol>

<h2>Escalation Path</h2>
<ol>
<li>On-call engineer</li>
<li>Team lead</li>
<li>Engineering manager</li>
</ol>

<h2>Contact Information</h2>
<ul>
<li><strong>Owner</strong>: Team Name</li>
<li><strong>Slack Channel</strong>: #team-channel</li>
</ul>
""",
    "meeting_notes": """<h1>{title} - {date}</h1>

<p><strong>Attendees</strong>: {attendees}</p>
<p><strong>Date</strong>: {date}</p>

<h2>Agenda</h2>
<ol>
<li>Topic 1</li>
<li>Topic 2</li>
<li>Topic 3</li>
</ol>

<h2>Discussion</h2>

<h3>Topic 1</h3>
<p>Notes from discussion...</p>

<p><strong>Decisions</strong>:</p>
<ul>
<li>Decision 1</li>
<li>Decision 2</li>
</ul>

<p><strong>Action Items</strong>:</p>
<ul>
<li>[ ] @person: Action item 1</li>
<li>[ ] @person: Action item 2</li>
</ul>

<h2>Next Meeting</h2>
<ul>
<li><strong>Date</strong>: TBD</li>
<li><strong>Topics</strong>: Preview of next agenda</li>
</ul>
""",
    "project_doc": """<h1>{title}</h1>

<h2>Executive Summary</h2>
<p>One-paragraph overview for stakeholders.</p>

<h2>Goals &amp; Objectives</h2>
<ul>
<li>Goal 1</li>
<li>Goal 2</li>
<li>Goal 3</li>
</ul>

<h2>Scope</h2>
<h3>In Scope</h3>
<ul>
<li>Item 1</li>
<li>Item 2</li>
</ul>

<h3>Out of Scope</h3>
<ul>
<li>Item 1</li>
<li>Item 2</li>
</ul>

<h2>Timeline</h2>
<table>
<tr><th>Phase</th><th>Start Date</th><th>End Date</th><th>Status</th></tr>
<tr><td>Planning</td><td>TBD</td><td>TBD</td><td>Pending</td></tr>
<tr><td>Development</td><td>TBD</td><td>TBD</td><td>Pending</td></tr>
<tr><td>Testing</td><td>TBD</td><td>TBD</td><td>Pending</td></tr>
</table>

<h2>Team</h2>
<table>
<tr><th>Role</th><th>Name</th><th>Responsibilities</th></tr>
<tr><td>Project Lead</td><td>@person</td><td>Overall delivery</td></tr>
<tr><td>Tech Lead</td><td>@person</td><td>Technical decisions</td></tr>
</table>

<h2>Risks &amp; Mitigation</h2>
<table>
<tr><th>Risk</th><th>Impact</th><th>Probability</th><th>Mitigation</th></tr>
<tr><td>Risk 1</td><td>High</td><td>Medium</td><td>Strategy 1</td></tr>
</table>

<h2>Success Metrics</h2>
<ul>
<li>Metric 1: Target value</li>
<li>Metric 2: Target value</li>
</ul>

<h2>Resources</h2>
<ul>
<li>Jira Epic</li>
<li>Design Mockups</li>
<li>Technical Specs</li>
</ul>
""",
}
