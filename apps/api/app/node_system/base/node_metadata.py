from typing import Any

from pydantic import BaseModel

_RETRY_PROPERTIES: list[dict[str, Any]] = [
    {
        "name": "retries",
        "label": "Retries",
        "type": "number",
        "default": 0,
        "mode": "advanced",
        "group": "Retry",
        "description": "Number of times to retry this node on failure (0 = no retries).",
    },
    {
        "name": "retry_delay_ms",
        "label": "Retry Delay (ms)",
        "type": "number",
        "default": 1000,
        "mode": "advanced",
        "group": "Retry",
        "condition": {"field": "retries", "value": [1, 2, 3, 4, 5]},
        "description": "Milliseconds to wait between retries.",
    },
]


class NodeMetadata(BaseModel):
    type: str
    name: str
    category: str
    description: str
    properties: list[dict[str, Any]]
    inputs: int
    outputs: int
    icon: str = "Circle"
    color: str = "#3b82f6"
    outputs_schema: list[dict[str, Any]] = []
    allow_error: bool = False
    credential_type: str | list[str] | None = None
    tools: list[str] | None = None
    operation_tool_map: dict[str, str] | None = None
    default_width: int | None = None
    default_height: int | None = None

    def model_post_init(self, __context: Any) -> None:
        # Inject retry properties into every node automatically
        existing_names = {p["name"] for p in self.properties}
        for prop in _RETRY_PROPERTIES:
            if prop["name"] not in existing_names:
                self.properties.append(prop)
