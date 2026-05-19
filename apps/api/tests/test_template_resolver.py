from apps.api.app.execution_engine.engine.template_resolver import TemplateResolver


def test_resolves_node_output_path_when_node_id_contains_dots() -> None:
    resolver = TemplateResolver(
        node_outputs={
            "action.http_request-1778949244013": {
                "body": {"message": "hello"},
            },
        },
        trigger_data={},
        variables={},
    )

    assert resolver.resolve_properties({
        "content": "{{action.http_request-1778949244013.output.body}}"
    }) == {"content": {"message": "hello"}}


def test_resolves_nested_node_output_path_when_node_id_contains_dots() -> None:
    resolver = TemplateResolver(
        node_outputs={
            "action.http_request-1778949244013": {
                "body": {"message": "hello"},
            },
        },
        trigger_data={},
        variables={},
    )

    assert resolver.resolve_properties({
        "content": "{{action.http_request-1778949244013.output.body.message}}"
    }) == {"content": "hello"}
