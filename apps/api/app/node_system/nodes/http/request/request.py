import json
from typing import Any

import httpx
from pydantic import BaseModel, Field

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class HttpRequestProperties(BaseModel):
    url: str
    method: str = "GET"
    headers: dict[str, Any] | None = Field(default_factory=dict)
    params: dict[str, Any] | None = Field(default_factory=dict)
    pathParams: dict[str, Any] | None = Field(default_factory=dict)
    body: Any | None = None
    formData: dict[str, Any] | None = Field(default_factory=dict)
    timeout: int = 30000


class HttpRequestNode(BaseNode[HttpRequestProperties]):
    @classmethod
    def get_properties_model(cls) -> type[HttpRequestProperties]:
        return HttpRequestProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.http_request",
            name="HTTP Request",
            category="action",
            description="Make HTTP requests with comprehensive support for methods, headers, query parameters, path parameters, and form data. Features configurable timeout and status validation for robust API interactions.",
            icon="Globe",
            color="#3b82f6",
            properties=[
                {"name": "url", "label": "URL", "type": "string", "required": True},
                {
                    "name": "method",
                    "label": "Method",
                    "type": "options",
                    "default": "GET",
                    "options": [
                        {"label": "GET", "value": "GET"},
                        {"label": "POST", "value": "POST"},
                        {"label": "PUT", "value": "PUT"},
                        {"label": "DELETE", "value": "DELETE"},
                        {"label": "PATCH", "value": "PATCH"},
                    ],
                },
                {
                    "name": "headers",
                    "label": "Headers",
                    "type": "key-value",
                    "required": False,
                    "mode": "advanced",
                },
                {
                    "name": "params",
                    "label": "Query Parameters",
                    "type": "key-value",
                    "required": False,
                    "mode": "advanced",
                },
                {
                    "name": "pathParams",
                    "label": "Path Parameters",
                    "type": "key-value",
                    "required": False,
                    "mode": "advanced",
                },
                {
                    "name": "body",
                    "label": "Body",
                    "type": "json",
                    "required": False,
                    "condition": {
                        "field": "method",
                        "value": ["POST", "PUT", "PATCH", "DELETE"],
                    },
                },
                {
                    "name": "formData",
                    "label": "Form Data",
                    "type": "key-value",
                    "required": False,
                    "mode": "advanced",
                },
                {
                    "name": "timeout",
                    "label": "Timeout (ms)",
                    "type": "number",
                    "default": 30000,
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "status_code", "type": "number"},
                {"label": "body", "type": "object"},
                {"label": "headers", "type": "object"},
                {"label": "ok", "type": "boolean"},
            ],
            allow_error=True,
            tools=["http_request"],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        try:
            url = self.props.url
            method = self.props.method.upper()
            headers = self.props.headers or {}
            params = self.props.params or {}
            path_params = self.props.pathParams or {}
            form_data = self.props.formData or {}
            body = self.props.body
            timeout_ms = float(self.props.timeout)

            # Handle path parameters (e.g. /users/:id)
            for key, val in path_params.items():
                url = url.replace(f":{key}", str(val))
                url = url.replace(f"{{{key}}}", str(val))

            # Use shared client from context if available, otherwise create a temporary one
            client = context.http_client or httpx.AsyncClient(timeout=timeout_ms / 1000.0)

            try:
                request_kwargs = {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "params": params,
                    "timeout": timeout_ms / 1000.0 if not context.http_client else None,
                }

                if form_data:
                    request_kwargs["data"] = form_data
                elif body:
                    if isinstance(body, str):
                        try:
                            request_kwargs["json"] = json.loads(body)
                        except json.JSONDecodeError:
                            request_kwargs["content"] = body
                    else:
                        request_kwargs["json"] = body

                response = await client.request(**request_kwargs)

                # Try to parse response as JSON
                try:
                    response_body = response.json()
                except Exception:
                    response_body = response.text

                return NodeResult(
                    success=True,
                    output_data={
                        "status_code": response.status_code,
                        "body": response_body,
                        "headers": dict(response.headers),
                        "ok": response.is_success,
                    },
                )
            finally:
                # ONLY close if we created it locally
                if not context.http_client:
                    await client.aclose()

        except httpx.TimeoutException:
            return NodeResult(
                success=False, error=f"Request timed out after {self.props.timeout}ms"
            )
        except Exception as e:
            logger.error(f"HttpRequestNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
