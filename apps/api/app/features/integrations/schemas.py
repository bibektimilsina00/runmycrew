from sqlmodel import SQLModel


class IntegrationOption(SQLModel):
    label: str
    value: str


class IntegrationResponse(SQLModel):
    ok: bool
    error: str | None = None
    data: list[IntegrationOption] = []
