"""JIRA REST API client."""

import logging
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from tenacity import retry, stop_after_attempt, wait_exponential
from urllib3.util.retry import Retry

from .models import AtlassianConfig, JiraIssue

logger = logging.getLogger(__name__)


class JiraClient:
    """JIRA REST API client with retry logic."""

    def __init__(self, config: Optional[AtlassianConfig] = None):
        """
        Initialize JIRA client.

        Args:
            config: Atlassian configuration. If None, loads from environment.
        """
        self.config = config or AtlassianConfig()

        if not self.config.jira_url:
            raise ValueError("JIRA_URL environment variable is required")
        if not self.config.jira_username:
            raise ValueError("JIRA_USERNAME environment variable is required")
        if not self.config.jira_api_token:
            raise ValueError("JIRA_API_TOKEN environment variable is required")

        self.base_url = f"{self.config.jira_url.rstrip('/')}/rest/api/3"
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        session.auth = (self.config.jira_username, self.config.jira_api_token)
        session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _parse_issue(self, issue_data: dict[str, Any]) -> JiraIssue:
        """Parse JIRA API response into JiraIssue object."""
        fields = issue_data.get("fields", {})

        # Parse sprint from custom field
        sprint = None
        sprint_field = fields.get("customfield_10020")
        if sprint_field and isinstance(sprint_field, list) and len(sprint_field) > 0:
            sprint_info = sprint_field[0]
            if isinstance(sprint_info, dict):
                sprint = sprint_info.get("name")
            elif isinstance(sprint_info, str):
                # Parse sprint name from string format
                if "name=" in sprint_info:
                    start = sprint_info.find("name=") + 5
                    end = sprint_info.find(",", start)
                    sprint = sprint_info[start:end] if end > start else sprint_info[start:]

        # Parse story points
        story_points = fields.get("customfield_10016")

        return JiraIssue(
            key=issue_data.get("key", ""),
            summary=fields.get("summary", ""),
            status=fields.get("status", {}).get("name", "Unknown"),
            issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
            priority=fields.get("priority", {}).get("name") if fields.get("priority") else None,
            assignee=fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
            reporter=fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
            description=self._extract_text(fields.get("description")),
            created=fields.get("created"),
            updated=fields.get("updated"),
            labels=fields.get("labels", []),
            sprint=sprint,
            story_points=story_points,
            url=f"{self.config.jira_url}/browse/{issue_data.get('key', '')}",
        )

    def _extract_text(self, content: Any) -> Optional[str]:
        """Extract plain text from Atlassian Document Format (ADF)."""
        if not content:
            return None

        if isinstance(content, str):
            return content

        if isinstance(content, dict):
            text_parts = []
            for node in content.get("content", []):
                if node.get("type") == "paragraph":
                    for text_node in node.get("content", []):
                        if text_node.get("type") == "text":
                            text_parts.append(text_node.get("text", ""))
            return "\n".join(text_parts) if text_parts else None

        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_issues(self, jql: str, max_results: int = 50) -> list[JiraIssue]:
        """
        Search JIRA issues using JQL.

        Args:
            jql: JQL query string
            max_results: Maximum number of results to return

        Returns:
            List of JiraIssue objects
        """
        url = f"{self.base_url}/search"
        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": "summary,status,issuetype,priority,assignee,reporter,description,"
                     "created,updated,labels,customfield_10020,customfield_10016",
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return [self._parse_issue(issue) for issue in data.get("issues", [])]

    def get_my_issues(self, max_results: int = 50) -> list[JiraIssue]:
        """
        Get issues assigned to the current user.

        Args:
            max_results: Maximum number of results

        Returns:
            List of JiraIssue objects
        """
        jql = "assignee = currentUser() ORDER BY updated DESC"
        return self.search_issues(jql, max_results)

    def get_sprint_issues(
        self, include_future_sprints: bool = False, max_results: int = 50
    ) -> list[JiraIssue]:
        """
        Get issues in active (and optionally future) sprints assigned to current user.

        Args:
            include_future_sprints: Include issues in future sprints
            max_results: Maximum number of results

        Returns:
            List of JiraIssue objects
        """
        if include_future_sprints:
            jql = (
                "assignee = currentUser() AND sprint in openSprints() "
                "OR sprint in futureSprints() ORDER BY priority DESC"
            )
        else:
            jql = (
                "assignee = currentUser() AND sprint in openSprints() "
                "ORDER BY priority DESC"
            )
        return self.search_issues(jql, max_results)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: Optional[str] = None,
        labels: Optional[list[str]] = None,
        extra_fields: Optional[dict[str, Any]] = None,
    ) -> JiraIssue:
        """
        Create a new JIRA issue.

        Args:
            project_key: Project key (e.g., "PROJ")
            summary: Issue summary
            description: Issue description
            issue_type: Issue type (Task, Bug, Story, etc.)
            priority: Priority name
            labels: List of labels
            extra_fields: Additional fields to set

        Returns:
            Created JiraIssue object
        """
        url = f"{self.base_url}/issue"

        # Build Atlassian Document Format for description
        adf_description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}],
                }
            ],
        }

        payload: dict[str, Any] = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": adf_description,
                "issuetype": {"name": issue_type},
            }
        }

        if priority:
            payload["fields"]["priority"] = {"name": priority}
        if labels:
            payload["fields"]["labels"] = labels
        if extra_fields:
            payload["fields"].update(extra_fields)

        response = self.session.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        # Fetch the created issue to get full details
        return self.get_issue(data["key"])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_issue(self, issue_key: str) -> JiraIssue:
        """
        Get a JIRA issue by key.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")

        Returns:
            JiraIssue object
        """
        url = f"{self.base_url}/issue/{issue_key}"
        response = self.session.get(url)
        response.raise_for_status()
        return self._parse_issue(response.json())

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def update_issue(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[list[str]] = None,
        extra_fields: Optional[dict[str, Any]] = None,
    ) -> JiraIssue:
        """
        Update an existing JIRA issue.

        Args:
            issue_key: Issue key to update
            summary: New summary
            description: New description
            status: New status (requires transition)
            priority: New priority
            labels: New labels
            extra_fields: Additional fields to update

        Returns:
            Updated JiraIssue object
        """
        url = f"{self.base_url}/issue/{issue_key}"
        payload: dict[str, Any] = {"fields": {}}

        if summary:
            payload["fields"]["summary"] = summary
        if description:
            payload["fields"]["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": description}]}
                ],
            }
        if priority:
            payload["fields"]["priority"] = {"name": priority}
        if labels is not None:
            payload["fields"]["labels"] = labels
        if extra_fields:
            payload["fields"].update(extra_fields)

        if payload["fields"]:
            response = self.session.put(url, json=payload)
            response.raise_for_status()

        # Handle status transition separately if provided
        if status:
            self._transition_issue(issue_key, status)

        return self.get_issue(issue_key)

    def _transition_issue(self, issue_key: str, status_name: str) -> None:
        """Transition an issue to a new status."""
        # Get available transitions
        url = f"{self.base_url}/issue/{issue_key}/transitions"
        response = self.session.get(url)
        response.raise_for_status()
        transitions = response.json().get("transitions", [])

        # Find matching transition
        transition_id = None
        for t in transitions:
            if t.get("to", {}).get("name", "").lower() == status_name.lower():
                transition_id = t.get("id")
                break

        if transition_id:
            payload = {"transition": {"id": transition_id}}
            response = self.session.post(url, json=payload)
            response.raise_for_status()
        else:
            logger.warning(f"No transition found to status '{status_name}' for {issue_key}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def add_comment(self, issue_key: str, comment: str) -> dict[str, Any]:
        """
        Add a comment to a JIRA issue.

        Args:
            issue_key: Issue key
            comment: Comment text

        Returns:
            Created comment data
        """
        url = f"{self.base_url}/issue/{issue_key}/comment"
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": comment}]}
                ],
            }
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
