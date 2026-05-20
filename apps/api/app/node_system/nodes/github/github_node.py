from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class GitHubProperties(BaseModel):
    credential: str | None = None
    operation: str = "create_issue"
    owner: str | None = None
    repo: str | None = None
    issue_number: int | None = None
    title: str | None = None
    body: str | None = None
    state: str | None = None
    labels: str | None = None
    assignees: str | None = None
    comment_body: str | None = None
    state_filter: str = "open"
    per_page: int = 30


class GitHubNode(BaseNode[GitHubProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.github",
            name="GitHub",
            category="integration",
            description="GitHub integration: manage issues, comments, and repositories.",
            icon="Github",
            color="#24292e",
            properties=[
                {
                    "name": "credential",
                    "label": "GitHub Account",
                    "type": "credential",
                    "credentialType": "github_oauth",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "create_issue",
                    "options": [
                        {"label": "Create Issue", "value": "create_issue"},
                        {"label": "List Issues", "value": "list_issues"},
                        {"label": "Get Issue", "value": "get_issue"},
                        {"label": "Update Issue", "value": "update_issue"},
                        {"label": "Add Comment", "value": "add_comment"},
                        {"label": "List Comments", "value": "list_comments"},
                        {"label": "Get Repository", "value": "get_repo"},
                        {"label": "List Repositories", "value": "list_repos"},
                    ],
                },
                {
                    "name": "owner",
                    "label": "Owner (user or org)",
                    "type": "string",
                    "required": True,
                    "placeholder": "octocat",
                    "condition": {
                        "field": "operation",
                        "value": [
                            "create_issue",
                            "list_issues",
                            "get_issue",
                            "update_issue",
                            "add_comment",
                            "list_comments",
                            "get_repo",
                        ],
                    },
                },
                {
                    "name": "repo",
                    "label": "Repository",
                    "type": "string",
                    "required": True,
                    "placeholder": "hello-world",
                    "condition": {
                        "field": "operation",
                        "value": [
                            "create_issue",
                            "list_issues",
                            "get_issue",
                            "update_issue",
                            "add_comment",
                            "list_comments",
                            "get_repo",
                        ],
                    },
                    "loadOptions": "/integrations/github/repos",
                    "loadOptionsDependsOn": ["credential", "owner"],
                },
                {
                    "name": "issue_number",
                    "label": "Issue Number",
                    "type": "number",
                    "required": True,
                    "condition": {
                        "field": "operation",
                        "value": ["get_issue", "update_issue", "add_comment", "list_comments"],
                    },
                },
                {
                    "name": "title",
                    "label": "Title",
                    "type": "string",
                    "condition": {"field": "operation", "value": ["create_issue", "update_issue"]},
                    "description": "Required for create_issue, optional for update_issue",
                },
                {
                    "name": "body",
                    "label": "Body",
                    "type": "string",
                    "condition": {
                        "field": "operation",
                        "value": ["create_issue", "update_issue"],
                    },
                },
                {
                    "name": "comment_body",
                    "label": "Comment",
                    "type": "string",
                    "required": True,
                    "condition": {"field": "operation", "value": "add_comment"},
                },
                {
                    "name": "state",
                    "label": "State",
                    "type": "options",
                    "options": [
                        {"label": "Open", "value": "open"},
                        {"label": "Closed", "value": "closed"},
                    ],
                    "condition": {"field": "operation", "value": "update_issue"},
                },
                {
                    "name": "state_filter",
                    "label": "State Filter",
                    "type": "options",
                    "default": "open",
                    "options": [
                        {"label": "Open", "value": "open"},
                        {"label": "Closed", "value": "closed"},
                        {"label": "All", "value": "all"},
                    ],
                    "condition": {"field": "operation", "value": "list_issues"},
                },
                {
                    "name": "labels",
                    "label": "Labels (comma-separated)",
                    "type": "string",
                    "required": False,
                    "condition": {
                        "field": "operation",
                        "value": ["create_issue", "update_issue", "list_issues"],
                    },
                },
                {
                    "name": "assignees",
                    "label": "Assignees (comma-separated)",
                    "type": "string",
                    "required": False,
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "create_issue"},
                },
                {
                    "name": "per_page",
                    "label": "Limit",
                    "type": "number",
                    "default": 30,
                    "mode": "advanced",
                    "condition": {
                        "field": "operation",
                        "value": ["list_issues", "list_comments", "list_repos"],
                    },
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "number", "type": "number"},
                {"label": "id", "type": "number"},
                {"label": "title", "type": "string"},
                {"label": "body", "type": "string"},
                {"label": "state", "type": "string"},
                {"label": "html_url", "type": "string"},
                {"label": "user", "type": "object"},
                {"label": "labels", "type": "array"},
                {"label": "issues", "type": "array"},
                {"label": "repos", "type": "array"},
                {"label": "comments", "type": "array"},
            ],
            allow_error=True,
            credential_type="github_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[GitHubProperties]:
        return GitHubProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        try:
            if not self.credential:
                return NodeResult(
                    success=False,
                    error="GitHub credential not found. Please connect your GitHub account.",
                )

            access_token = self.credential.get("access_token")
            if not access_token:
                return NodeResult(success=False, error="GitHub access token missing in credential.")

            from apps.api.app.integrations.github.service import GitHubService

            service = GitHubService(access_token=access_token, client=context.http_client)
            op = self.props.operation

            def _parse_csv(val: str | None) -> list[str]:
                if not val:
                    return []
                return [v.strip() for v in val.split(",") if v.strip()]

            if op == "create_issue":
                owner = (self.props.owner or "").strip()
                repo = (self.props.repo or "").strip()
                if not owner or not repo:
                    return NodeResult(success=False, error="owner and repo are required")
                if not self.props.title:
                    return NodeResult(success=False, error="title is required")

                issue = await service.create_issue(
                    owner=owner,
                    repo=repo,
                    title=self.props.title,
                    body=self.props.body,
                    labels=_parse_csv(self.props.labels) or None,
                    assignees=_parse_csv(self.props.assignees) or None,
                )
                return NodeResult(success=True, output_data=issue)

            elif op == "list_issues":
                owner = (self.props.owner or "").strip()
                repo = (self.props.repo or "").strip()
                if not owner or not repo:
                    return NodeResult(success=False, error="owner and repo are required")

                issues = await service.list_issues(
                    owner=owner,
                    repo=repo,
                    state=self.props.state_filter,
                    labels=self.props.labels or None,
                    per_page=self.props.per_page,
                )
                return NodeResult(success=True, output_data={"issues": issues, "count": len(issues)})

            elif op == "get_issue":
                owner = (self.props.owner or "").strip()
                repo = (self.props.repo or "").strip()
                if not owner or not repo:
                    return NodeResult(success=False, error="owner and repo are required")
                if not self.props.issue_number:
                    return NodeResult(success=False, error="issue_number is required")

                issue = await service.get_issue(owner=owner, repo=repo, issue_number=self.props.issue_number)
                return NodeResult(success=True, output_data=issue)

            elif op == "update_issue":
                owner = (self.props.owner or "").strip()
                repo = (self.props.repo or "").strip()
                if not owner or not repo:
                    return NodeResult(success=False, error="owner and repo are required")
                if not self.props.issue_number:
                    return NodeResult(success=False, error="issue_number is required")

                labels = _parse_csv(self.props.labels) or None
                issue = await service.update_issue(
                    owner=owner,
                    repo=repo,
                    issue_number=self.props.issue_number,
                    title=self.props.title or None,
                    body=self.props.body or None,
                    state=self.props.state or None,
                    labels=labels,
                )
                return NodeResult(success=True, output_data=issue)

            elif op == "add_comment":
                owner = (self.props.owner or "").strip()
                repo = (self.props.repo or "").strip()
                if not owner or not repo:
                    return NodeResult(success=False, error="owner and repo are required")
                if not self.props.issue_number:
                    return NodeResult(success=False, error="issue_number is required")
                if not self.props.comment_body:
                    return NodeResult(success=False, error="comment is required")

                comment = await service.add_comment(
                    owner=owner,
                    repo=repo,
                    issue_number=self.props.issue_number,
                    body=self.props.comment_body,
                )
                return NodeResult(success=True, output_data=comment)

            elif op == "list_comments":
                owner = (self.props.owner or "").strip()
                repo = (self.props.repo or "").strip()
                if not owner or not repo:
                    return NodeResult(success=False, error="owner and repo are required")
                if not self.props.issue_number:
                    return NodeResult(success=False, error="issue_number is required")

                comments = await service.list_comments(owner=owner, repo=repo, issue_number=self.props.issue_number)
                return NodeResult(success=True, output_data={"comments": comments, "count": len(comments)})

            elif op == "get_repo":
                owner = (self.props.owner or "").strip()
                repo = (self.props.repo or "").strip()
                if not owner or not repo:
                    return NodeResult(success=False, error="owner and repo are required")

                repo_data = await service.get_repo(owner=owner, repo=repo)
                return NodeResult(success=True, output_data=repo_data)

            elif op == "list_repos":
                repos = await service.list_repos(per_page=self.props.per_page)
                return NodeResult(success=True, output_data={"repos": repos, "count": len(repos)})

            else:
                return NodeResult(success=False, error=f"Unsupported operation: {op}")

        except Exception as e:
            logger.error(f"GitHubNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
