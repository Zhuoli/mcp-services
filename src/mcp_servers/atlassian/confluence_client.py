"""Confluence REST API client."""

import logging
import re
from datetime import datetime
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from tenacity import retry, stop_after_attempt, wait_exponential
from urllib3.util.retry import Retry

from .models import AtlassianConfig, ConfluencePage, CONFLUENCE_TEMPLATES

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Confluence REST API client with retry logic."""

    def __init__(self, config: Optional[AtlassianConfig] = None):
        """
        Initialize Confluence client.

        Args:
            config: Atlassian configuration. If None, loads from environment.
        """
        self.config = config or AtlassianConfig()

        if not self.config.confluence_url:
            raise ValueError("CONFLUENCE_URL environment variable is required")
        if not self.config.confluence_username:
            raise ValueError("CONFLUENCE_USERNAME environment variable is required")
        if not self.config.confluence_api_token:
            raise ValueError("CONFLUENCE_API_TOKEN environment variable is required")

        self.base_url = f"{self.config.confluence_url.rstrip('/')}/rest/api"
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        session.auth = (self.config.confluence_username, self.config.confluence_api_token)
        session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _parse_page(self, page_data: dict[str, Any]) -> ConfluencePage:
        """Parse Confluence API response into ConfluencePage object."""
        body = None
        if "body" in page_data:
            if "storage" in page_data["body"]:
                body = page_data["body"]["storage"].get("value")
            elif "view" in page_data["body"]:
                body = page_data["body"]["view"].get("value")

        # Strip HTML tags for preview
        if body:
            body = self._strip_html(body)

        version = page_data.get("version", {})
        history = page_data.get("history", {})

        # Parse labels
        labels = []
        if "metadata" in page_data and "labels" in page_data["metadata"]:
            labels = [
                label.get("name", "")
                for label in page_data["metadata"]["labels"].get("results", [])
            ]

        return ConfluencePage(
            page_id=page_data.get("id", ""),
            title=page_data.get("title", ""),
            space_key=page_data.get("space", {}).get("key", self.config.confluence_space_key),
            status=page_data.get("status", "current"),
            version=version.get("number", 1) if isinstance(version, dict) else 1,
            url=f"{self.config.confluence_url}/pages/{page_data.get('id', '')}",
            body=body,
            created=history.get("createdDate") if isinstance(history, dict) else None,
            updated=version.get("when") if isinstance(version, dict) else None,
            creator=history.get("createdBy", {}).get("displayName") if isinstance(history, dict) else None,
            last_modifier=version.get("by", {}).get("displayName") if isinstance(version, dict) else None,
            parent_id=page_data.get("ancestors", [{}])[-1].get("id") if page_data.get("ancestors") else None,
            labels=labels,
        )

    def _strip_html(self, html: str) -> str:
        """Strip HTML tags from content."""
        clean = re.compile("<.*?>")
        return re.sub(clean, "", html).strip()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_pages(
        self,
        query: str,
        space_key: Optional[str] = None,
        max_results: int = 25,
    ) -> list[ConfluencePage]:
        """
        Search Confluence pages using CQL.

        Args:
            query: Search query (text search or CQL)
            space_key: Optional space key to filter
            max_results: Maximum results to return

        Returns:
            List of ConfluencePage objects
        """
        url = f"{self.base_url}/content/search"

        # Build CQL query
        if "type=" in query or "space=" in query:
            cql = query
        else:
            cql = f'type=page AND text~"{query}"'
            if space_key:
                cql = f'space="{space_key}" AND {cql}'

        params = {
            "cql": cql,
            "limit": max_results,
            "expand": "version,space,history,metadata.labels",
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return [self._parse_page(page) for page in data.get("results", [])]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_page_by_id(self, page_id: str, include_body: bool = True) -> ConfluencePage:
        """
        Get a Confluence page by ID.

        Args:
            page_id: Page ID
            include_body: Whether to include the page body

        Returns:
            ConfluencePage object
        """
        url = f"{self.base_url}/content/{page_id}"
        expand = ["version", "space", "history", "ancestors", "metadata.labels"]
        if include_body:
            expand.append("body.storage")

        params = {"expand": ",".join(expand)}

        response = self.session.get(url, params=params)
        response.raise_for_status()
        return self._parse_page(response.json())

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_page_by_title(
        self, title: str, space_key: Optional[str] = None, include_body: bool = True
    ) -> Optional[ConfluencePage]:
        """
        Get a Confluence page by title.

        Args:
            title: Page title
            space_key: Space key (uses default if not provided)
            include_body: Whether to include the page body

        Returns:
            ConfluencePage object or None if not found
        """
        space = space_key or self.config.confluence_space_key
        url = f"{self.base_url}/content"

        expand = ["version", "space", "history", "ancestors", "metadata.labels"]
        if include_body:
            expand.append("body.storage")

        params = {
            "type": "page",
            "spaceKey": space,
            "title": title,
            "expand": ",".join(expand),
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()
        results = response.json().get("results", [])

        if results:
            return self._parse_page(results[0])
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_recent_pages(
        self, space_key: Optional[str] = None, max_results: int = 10
    ) -> list[ConfluencePage]:
        """
        Get recently modified pages.

        Args:
            space_key: Optional space key to filter
            max_results: Maximum results to return

        Returns:
            List of ConfluencePage objects
        """
        space = space_key or self.config.confluence_space_key
        cql = f'space="{space}" AND type=page ORDER BY lastModified DESC'
        return self.search_pages(cql, max_results=max_results)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_page(
        self,
        title: str,
        body: str,
        space_key: Optional[str] = None,
        parent_id: Optional[str] = None,
        template: Optional[str] = None,
        template_vars: Optional[dict[str, str]] = None,
    ) -> ConfluencePage:
        """
        Create a new Confluence page.

        Args:
            title: Page title
            body: Page body in HTML/storage format
            space_key: Space key (uses default if not provided)
            parent_id: Parent page ID
            template: Template name (technical_doc, runbook, meeting_notes, project_doc)
            template_vars: Variables to substitute in template

        Returns:
            Created ConfluencePage object
        """
        space = space_key or self.config.confluence_space_key
        url = f"{self.base_url}/content"

        # Use template if specified
        if template and template in CONFLUENCE_TEMPLATES:
            vars_dict = template_vars or {}
            vars_dict.setdefault("title", title)
            vars_dict.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
            vars_dict.setdefault("author", self.config.confluence_username)
            vars_dict.setdefault("attendees", "")

            body = CONFLUENCE_TEMPLATES[template].format(**vars_dict)

        payload: dict[str, Any] = {
            "type": "page",
            "title": title,
            "space": {"key": space},
            "body": {
                "storage": {
                    "value": body,
                    "representation": "storage",
                }
            },
        }

        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]

        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return self._parse_page(response.json())

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def update_page(
        self,
        page_id: str,
        title: Optional[str] = None,
        body: Optional[str] = None,
    ) -> ConfluencePage:
        """
        Update an existing Confluence page.

        Args:
            page_id: Page ID to update
            title: New title (uses existing if not provided)
            body: New body in HTML/storage format

        Returns:
            Updated ConfluencePage object
        """
        # Get current page to get version number
        current = self.get_page_by_id(page_id, include_body=True)

        url = f"{self.base_url}/content/{page_id}"

        payload: dict[str, Any] = {
            "type": "page",
            "title": title or current.title,
            "version": {"number": current.version + 1},
        }

        if body:
            payload["body"] = {
                "storage": {
                    "value": body,
                    "representation": "storage",
                }
            }

        response = self.session.put(url, json=payload)
        response.raise_for_status()
        return self._parse_page(response.json())

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def delete_page(self, page_id: str) -> bool:
        """
        Delete a Confluence page.

        Args:
            page_id: Page ID to delete

        Returns:
            True if deleted successfully
        """
        url = f"{self.base_url}/content/{page_id}"
        response = self.session.delete(url)
        response.raise_for_status()
        return True

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def add_labels(self, page_id: str, labels: list[str]) -> list[str]:
        """
        Add labels to a Confluence page.

        Args:
            page_id: Page ID
            labels: List of labels to add

        Returns:
            List of all labels on the page
        """
        url = f"{self.base_url}/content/{page_id}/label"
        payload = [{"name": label} for label in labels]

        response = self.session.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        return [label.get("name", "") for label in data.get("results", [])]
