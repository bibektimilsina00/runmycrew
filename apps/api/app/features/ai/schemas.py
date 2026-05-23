from sqlmodel import SQLModel


class AIStatusResponse(SQLModel):
    status: str


class AIProviderData(SQLModel):
    label: str
    value: str
    credentialType: str
    defaultModel: str
    supportsTools: bool
    supportsResponseFormat: bool
    apiType: str


class AIProviderResponse(SQLModel):
    ok: bool
    data: list[AIProviderData]


class AIModelData(SQLModel):
    label: str
    value: str


class AIModelResponse(SQLModel):
    ok: bool
    data: list[AIModelData]
    error: str | None = None
