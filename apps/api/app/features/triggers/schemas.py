from sqlmodel import SQLModel


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
