from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class JiraProperties(BaseModel):
    credential: str | None = None
    operation: str = "get_issue"
    issue_key: str | None = None
    project_key: str | None = None
    summary: str | None = None
    description: str | None = None
    issue_type: str = "Task"
    assignee_id: str | None = None
    priority: str | None = None
    status_name: str | None = None
    comment_body: str | None = None
    transition_id: str | None = None
    jql: str | None = None
    max_results: int = 20


class JiraNode(BaseNode[JiraProperties]):
    @classmethod
    def get_properties_model(cls):
        return JiraProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.jira",
            name="Jira",
            category="integration",
            description="Create issues, update status, add comments, and search Jira projects.",
            icon="jira",
            color="#ffffff",
            properties=[
                {
                    "name": "credential",
                    "label": "Jira Credential",
                    "type": "credential",
                    "credentialType": "jira_api_key",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "get_issue",
                    "options": [
                        {"label": "Create Issue", "value": "create_issue"},
                        {"label": "Get Issue", "value": "get_issue"},
                        {"label": "Update Issue", "value": "update_issue"},
                        {"label": "Search Issues (JQL)", "value": "search_issues"},
                        {"label": "Add Comment", "value": "add_comment"},
                        {"label": "Transition Issue", "value": "transition_issue"},
                        {"label": "List Transitions", "value": "list_transitions"},
                    ],
                },
                {
                    "name": "issue_key",
                    "label": "Issue Key",
                    "type": "string",
                    "placeholder": "PROJ-123",
                    "condition": {
                        "field": "operation",
                        "value": [
                            "get_issue",
                            "update_issue",
                            "add_comment",
                            "transition_issue",
                            "list_transitions",
                        ],
                    },
                },
                {
                    "name": "project_key",
                    "label": "Project Key",
                    "type": "string",
                    "placeholder": "PROJ",
                    "condition": {"field": "operation", "value": "create_issue"},
                },
                {
                    "name": "summary",
                    "label": "Summary",
                    "type": "string",
                    "condition": {"field": "operation", "value": ["create_issue", "update_issue"]},
                },
                {
                    "name": "description",
                    "label": "Description",
                    "type": "string",
                    "condition": {"field": "operation", "value": ["create_issue", "update_issue"]},
                },
                {
                    "name": "issue_type",
                    "label": "Issue Type",
                    "type": "options",
                    "default": "Task",
                    "options": [
                        {"label": "Task", "value": "Task"},
                        {"label": "Bug", "value": "Bug"},
                        {"label": "Story", "value": "Story"},
                        {"label": "Epic", "value": "Epic"},
                    ],
                    "condition": {"field": "operation", "value": "create_issue"},
                },
                {
                    "name": "comment_body",
                    "label": "Comment",
                    "type": "string",
                    "condition": {"field": "operation", "value": "add_comment"},
                },
                {
                    "name": "transition_id",
                    "label": "Transition ID",
                    "type": "string",
                    "condition": {"field": "operation", "value": "transition_issue"},
                },
                {
                    "name": "jql",
                    "label": "JQL Query",
                    "type": "string",
                    "placeholder": 'project = "PROJ" AND status = "Open"',
                    "condition": {"field": "operation", "value": "search_issues"},
                },
                {
                    "name": "max_results",
                    "label": "Max Results",
                    "type": "number",
                    "default": 20,
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "search_issues"},
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "key", "type": "string"},
                {"label": "summary", "type": "string"},
                {"label": "issues", "type": "array"},
            ],
            allow_error=True,
            credential_type="jira_api_key",
        )

    def _get_auth(self) -> tuple[str, str] | None:
        if not self.credential:
            return None
        email = self.credential.get("email", "")
        api_token = self.credential.get("api_key", "")
        base_url = self.credential.get("base_url", "")
        if not all([email, api_token, base_url]):
            return None
        return email, api_token

    def _base_url(self) -> str:
        if not self.credential:
            return ""
        return self.credential.get("base_url", "").rstrip("/")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        auth = self._get_auth()
        if not auth:
            return NodeResult(
                success=False, error="Jira credential required (email + api_key + base_url)."
            )
        email, api_token = auth
        base = f"{self._base_url()}/rest/api/3"
        op = self.props.operation
        try:
            async with httpx.AsyncClient(timeout=30, auth=(email, api_token)) as c:
                headers = {"Accept": "application/json", "Content-Type": "application/json"}

                if op == "create_issue":
                    if not self.props.project_key or not self.props.summary:
                        return NodeResult(success=False, error="project_key and summary required")
                    body: dict = {
                        "fields": {
                            "project": {"key": self.props.project_key},
                            "summary": self.props.summary,
                            "issuetype": {"name": self.props.issue_type},
                        }
                    }
                    if self.props.description:
                        body["fields"]["description"] = {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": self.props.description}],
                                }
                            ],
                        }
                    r = await c.post(f"{base}/issue", json=body, headers=headers)
                    r.raise_for_status()
                    d = r.json()
                    return NodeResult(
                        success=True,
                        output_data={
                            "id": d["id"],
                            "key": d["key"],
                            "url": f"{self._base_url()}/browse/{d['key']}",
                        },
                    )

                elif op == "get_issue":
                    if not self.props.issue_key:
                        return NodeResult(success=False, error="issue_key required")
                    r = await c.get(f"{base}/issue/{self.props.issue_key}", headers=headers)
                    r.raise_for_status()
                    d = r.json()
                    f = d.get("fields", {})
                    return NodeResult(
                        success=True,
                        output_data={
                            "id": d["id"],
                            "key": d["key"],
                            "summary": f.get("summary"),
                            "status": f.get("status", {}).get("name"),
                            "assignee": (f.get("assignee") or {}).get("displayName"),
                            "priority": (f.get("priority") or {}).get("name"),
                        },
                    )

                elif op == "update_issue":
                    if not self.props.issue_key:
                        return NodeResult(success=False, error="issue_key required")
                    fields: dict = {}
                    if self.props.summary:
                        fields["summary"] = self.props.summary
                    if self.props.description:
                        fields["description"] = {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": self.props.description}],
                                }
                            ],
                        }
                    r = await c.put(
                        f"{base}/issue/{self.props.issue_key}",
                        json={"fields": fields},
                        headers=headers,
                    )
                    r.raise_for_status()
                    return NodeResult(
                        success=True, output_data={"key": self.props.issue_key, "updated": True}
                    )

                elif op == "search_issues":
                    params = {
                        "jql": self.props.jql or "",
                        "maxResults": min(self.props.max_results, 100),
                    }
                    r = await c.get(f"{base}/search", params=params, headers=headers)
                    r.raise_for_status()
                    d = r.json()
                    return NodeResult(
                        success=True,
                        output_data={"issues": d.get("issues", []), "total": d.get("total", 0)},
                    )

                elif op == "add_comment":
                    if not self.props.issue_key or not self.props.comment_body:
                        return NodeResult(success=False, error="issue_key and comment required")
                    body = {
                        "body": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": self.props.comment_body}],
                                }
                            ],
                        }
                    }
                    r = await c.post(
                        f"{base}/issue/{self.props.issue_key}/comment", json=body, headers=headers
                    )
                    r.raise_for_status()
                    d = r.json()
                    return NodeResult(
                        success=True, output_data={"id": d["id"], "created": d.get("created")}
                    )

                elif op == "transition_issue":
                    if not self.props.issue_key or not self.props.transition_id:
                        return NodeResult(
                            success=False, error="issue_key and transition_id required"
                        )
                    r = await c.post(
                        f"{base}/issue/{self.props.issue_key}/transitions",
                        json={"transition": {"id": self.props.transition_id}},
                        headers=headers,
                    )
                    r.raise_for_status()
                    return NodeResult(
                        success=True,
                        output_data={"transitioned": True, "key": self.props.issue_key},
                    )

                elif op == "list_transitions":
                    if not self.props.issue_key:
                        return NodeResult(success=False, error="issue_key required")
                    r = await c.get(
                        f"{base}/issue/{self.props.issue_key}/transitions", headers=headers
                    )
                    r.raise_for_status()
                    d = r.json()
                    return NodeResult(
                        success=True,
                        output_data={
                            "transitions": [
                                {"id": t["id"], "name": t["name"]} for t in d.get("transitions", [])
                            ]
                        },
                    )

                else:
                    return NodeResult(success=False, error=f"Unknown operation: {op}")

        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False, error=f"Jira API {e.response.status_code}: {e.response.text[:200]}"
            )
        except Exception as e:
            logger.error(f"JiraNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
