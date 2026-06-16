from typing import Any

from sqlmodel import SQLModel


class TriggerFixtureResponse(SQLModel):
    node_id: str
    source: str
    captured_at: str
    payload: dict[str, Any]


class TriggerListenRequest(SQLModel):
    """Optional body for POST /workflows/{id}/listen.

    `node_id` is required only when the workflow contains more than one
    Meta trigger node — otherwise the lone trigger is auto-selected.
    """

    node_id: str | None = None


class TriggerListenResponse(SQLModel):
    execution_id: str
    node_id: str
    waiting_for: str
    target_id: str
    ttl_seconds: int


class TriggerListenStatusResponse(SQLModel):
    active: bool
    execution_id: str | None
    waiting_for: str | None
    target_id: str | None


class CronValidateRequest(SQLModel):
    expression: str
    count: int = 5


class CronValidateResponse(SQLModel):
    valid: bool
    expression: str
    next_runs: list[str]


class CronNextRunsResponse(SQLModel):
    expression: str
    next_runs: list[str]


class WebhookSecretResponse(SQLModel):
    secret: str


class WebhookInfoResponse(SQLModel):
    path: str
    webhook_url: str
    active: bool
    workflow_count: int


class WebhookReceiveResponse(SQLModel):
    status: str
    triggered_count: int
    execution_ids: list[str]


class WebhookGithubReceiveResponse(SQLModel):
    status: str
    execution_id: str
    event: str
