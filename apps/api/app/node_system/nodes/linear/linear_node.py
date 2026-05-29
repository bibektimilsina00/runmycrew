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
LINEAR_API = "https://api.linear.app/graphql"


class LinearProperties(BaseModel):
    credential: str | None = None
    operation: str = "create_issue"
    title: str | None = None
    description: str | None = None
    team_id: str | None = None
    issue_id: str | None = None
    state_id: str | None = None
    assignee_id: str | None = None
    priority: int | None = None
    label_ids: str | None = None
    query: str | None = None


class LinearNode(BaseNode[LinearProperties]):
    @classmethod
    def get_properties_model(cls):
        return LinearProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.linear",
            name="Linear",
            category="integration",
            description="Create and manage Linear issues, projects, and teams.",
            icon="si:SiLinear",
            color="#5e6ad2",
            properties=[
                {
                    "name": "credential",
                    "label": "Linear API Key",
                    "type": "credential",
                    "credentialType": "linear_api_key",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "create_issue",
                    "options": [
                        {"label": "Create Issue", "value": "create_issue"},
                        {"label": "Update Issue", "value": "update_issue"},
                        {"label": "Get Issue", "value": "get_issue"},
                        {"label": "List Issues", "value": "list_issues"},
                        {"label": "List Teams", "value": "list_teams"},
                        {"label": "Get Viewer (me)", "value": "get_viewer"},
                    ],
                },
                {
                    "name": "title",
                    "label": "Title",
                    "type": "string",
                    "required": True,
                    "condition": {"field": "operation", "value": "create_issue"},
                },
                {
                    "name": "title",
                    "label": "Title",
                    "type": "string",
                    "condition": {"field": "operation", "value": "update_issue"},
                },
                {
                    "name": "description",
                    "label": "Description (Markdown)",
                    "type": "string",
                    "condition": {"field": "operation", "value": ["create_issue", "update_issue"]},
                },
                {
                    "name": "team_id",
                    "label": "Team ID",
                    "type": "string",
                    "required": True,
                    "condition": {"field": "operation", "value": "create_issue"},
                },
                {
                    "name": "issue_id",
                    "label": "Issue ID",
                    "type": "string",
                    "required": True,
                    "condition": {"field": "operation", "value": ["update_issue", "get_issue"]},
                },
                {
                    "name": "state_id",
                    "label": "State ID",
                    "type": "string",
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": ["create_issue", "update_issue"]},
                },
                {
                    "name": "assignee_id",
                    "label": "Assignee ID",
                    "type": "string",
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": ["create_issue", "update_issue"]},
                },
                {
                    "name": "priority",
                    "label": "Priority (0=none,1=urgent,2=high,3=medium,4=low)",
                    "type": "number",
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": ["create_issue", "update_issue"]},
                },
                {
                    "name": "query",
                    "label": "Filter (JSON)",
                    "type": "string",
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "list_issues"},
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "title", "type": "string"},
                {"label": "url", "type": "string"},
                {"label": "issues", "type": "array"},
                {"label": "teams", "type": "array"},
            ],
            allow_error=True,
            credential_type="linear_api_key",
        )

    def _get_api_key(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("api_key")

    async def _gql(
        self, client: httpx.AsyncClient, query: str, variables: dict | None = None
    ) -> dict:
        token = self._get_api_key()
        r = await client.post(
            LINEAR_API,
            headers={"Authorization": token or "", "Content-Type": "application/json"},
            json={"query": query, "variables": variables or {}},
        )
        r.raise_for_status()
        data = r.json()
        if "errors" in data:
            raise RuntimeError(data["errors"][0]["message"])
        return data.get("data", {})

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self._get_api_key():
            return NodeResult(success=False, error="Linear API key required.")
        op = self.props.operation
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if op == "create_issue":
                    if not self.props.title or not self.props.team_id:
                        return NodeResult(success=False, error="title and team_id required")
                    inp: dict = {"title": self.props.title, "teamId": self.props.team_id}
                    if self.props.description:
                        inp["description"] = self.props.description
                    if self.props.state_id:
                        inp["stateId"] = self.props.state_id
                    if self.props.assignee_id:
                        inp["assigneeId"] = self.props.assignee_id
                    if self.props.priority is not None:
                        inp["priority"] = self.props.priority
                    q = """mutation CreateIssue($input: IssueCreateInput!) { issueCreate(input: $input) { success issue { id title url identifier } } }"""
                    data = await self._gql(client, q, {"input": inp})
                    issue = data.get("issueCreate", {}).get("issue", {})
                    return NodeResult(success=True, output_data=issue)
                elif op == "update_issue":
                    if not self.props.issue_id:
                        return NodeResult(success=False, error="issue_id required")
                    inp = {}
                    if self.props.title:
                        inp["title"] = self.props.title
                    if self.props.description:
                        inp["description"] = self.props.description
                    if self.props.state_id:
                        inp["stateId"] = self.props.state_id
                    if self.props.assignee_id:
                        inp["assigneeId"] = self.props.assignee_id
                    if self.props.priority is not None:
                        inp["priority"] = self.props.priority
                    q = """mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) { issueUpdate(id: $id, input: $input) { success issue { id title url } } }"""
                    data = await self._gql(client, q, {"id": self.props.issue_id, "input": inp})
                    return NodeResult(
                        success=True, output_data=data.get("issueUpdate", {}).get("issue", {})
                    )
                elif op == "get_issue":
                    if not self.props.issue_id:
                        return NodeResult(success=False, error="issue_id required")
                    q = """query GetIssue($id: String!) { issue(id: $id) { id title description url state { name } assignee { name email } priority createdAt } }"""
                    data = await self._gql(client, q, {"id": self.props.issue_id})
                    return NodeResult(success=True, output_data=data.get("issue", {}))
                elif op == "list_issues":
                    q = """query ListIssues { issues(first: 50) { nodes { id title url state { name } priority createdAt } } }"""
                    data = await self._gql(client, q)
                    issues = data.get("issues", {}).get("nodes", [])
                    return NodeResult(
                        success=True, output_data={"issues": issues, "count": len(issues)}
                    )
                elif op == "list_teams":
                    q = """query ListTeams { teams { nodes { id name key } } }"""
                    data = await self._gql(client, q)
                    teams = data.get("teams", {}).get("nodes", [])
                    return NodeResult(
                        success=True, output_data={"teams": teams, "count": len(teams)}
                    )
                elif op == "get_viewer":
                    q = """query Me { viewer { id name email } }"""
                    data = await self._gql(client, q)
                    return NodeResult(success=True, output_data=data.get("viewer", {}))
                else:
                    return NodeResult(success=False, error=f"Unknown operation: {op}")
        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False,
                error=f"Linear API error {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            logger.error(f"LinearNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
