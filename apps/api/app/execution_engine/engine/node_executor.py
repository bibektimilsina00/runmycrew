from typing import Any

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.registry.registry import node_registry

logger = get_logger(__name__)


class NodeExecutor:
    async def execute_node(
        self,
        node_type: str,
        node_id: str,
        properties: dict[str, Any],
        input_data: dict[str, Any],
        context: NodeContext,
    ) -> NodeResult:
        try:
            node_class = node_registry.get_node(node_type)
            metadata = node_class.get_metadata()

            # 1. Instantiate (Pydantic validation happens in __init__)
            node_instance = node_class(node_id=node_id, properties=properties)

            # 2. Advanced Credential Injection
            if metadata.credential_type:
                selected_cred_id = properties.get("credential")
                credentials = context.credentials or []

                logger.info(
                    f"Resolving credential for node {node_id}. Type: {metadata.credential_type}, Selected ID: {selected_cred_id}"
                )
                logger.info(f"Available credentials IDs: {[c.get('id') for c in credentials]}")

                found_cred = None
                if selected_cred_id:
                    found_cred = next(
                        (c for c in credentials if str(c.get("id")) == str(selected_cred_id)), None
                    )

                if not found_cred:
                    found_cred = next(
                        (c for c in credentials if c.get("type") == metadata.credential_type), None
                    )

                if found_cred:
                    logger.info(
                        f"Found credential: {found_cred.get('id')} of type {found_cred.get('type')}"
                    )
                    node_instance.credential = found_cred.get("data")
                else:
                    logger.warning(f"No credential found for node {node_id}")

            logger.info(f"Executing node {node_id} of type {node_type}")
            result = await node_instance.execute(input_data, context)
            return result
        except Exception as e:
            # Handle Pydantic validation errors gracefully
            from pydantic import ValidationError

            if isinstance(e, ValidationError):
                errors = []
                for error in e.errors():
                    # Convert field path to human-readable property name
                    loc = error["loc"]
                    field = loc[-1] if loc else "unknown"  # last segment is the field name
                    raw_msg = error["msg"]
                    # Strip pydantic noise
                    msg = raw_msg.replace("Value error, ", "").replace("String should ", "").strip()
                    errors.append(f'"{field}" — {msg}')
                error_msg = "Missing or invalid fields: " + "; ".join(errors)
                logger.warning(f"Node {node_id} validation failed: {error_msg}")
                return NodeResult(success=False, error=error_msg, logs=[error_msg])

            logger.error(f"Error executing node {node_id}: {str(e)}", exc_info=True)
            return NodeResult(success=False, error=str(e), logs=[f"System Error: {str(e)}"])


node_executor = NodeExecutor()
