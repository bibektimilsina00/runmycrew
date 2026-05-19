from apps.api.app.node_system.registry.registry import node_registry


def _metadata_by_type() -> dict[str, dict]:
    return {metadata["type"]: metadata for metadata in node_registry.list_nodes()}


def _advanced_fields(node_type: str) -> set[str]:
    metadata = _metadata_by_type()[node_type]
    return {
        prop["name"]
        for prop in metadata["properties"]
        if prop.get("mode") == "advanced"
    }


def test_advanced_fields_are_declared_by_backend_metadata():
    expected_by_node = {
        "action.agent": {
            "toolChoice",
            "maxIterations",
            "memoryType",
            "memoryKey",
            "memoryLimit",
            "temperature",
            "maxTokens",
            "responseFormat",
            "timeout",
            "reasoningEffort",
            "streaming",
        },
        "action.http_request": {
            "headers",
            "params",
            "pathParams",
            "formData",
            "timeout",
        },
        "logic.for": {"start", "step", "parallel"},
        "logic.while": {"maxIterations"},
        "logic.do_while": {"maxIterations"},
        "logic.foreach": {"parallel"},
        "action.postgres": {"params"},
        "action.mysql": {"params"},
        "action.mongodb": {"limit"},
        "action.neo4j": {"params"},
        "action.a2a": {"inputData", "waitForCompletion", "authToken", "timeoutSeconds"},
    }

    for node_type, expected_fields in expected_by_node.items():
        assert expected_fields.issubset(_advanced_fields(node_type))
