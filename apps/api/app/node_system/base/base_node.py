from abc import ABC, abstractmethod
from typing import Any, cast, get_args, get_origin

from pydantic import BaseModel

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class BaseNode[TProps: BaseModel](ABC):
    # Default property model if none is specified
    class DefaultProps(BaseModel):
        pass

    def __init__(self, node_id: str, properties: dict[str, Any]):
        self.node_id = node_id
        # Raw properties (still useful for dynamic access)
        self.raw_properties = properties
        # Typed properties (populated during validation)
        self.props: TProps = self.validate_properties(properties)
        # Injected credential (Step 3)
        self.credential: dict[str, Any] | None = None

    @classmethod
    @abstractmethod
    def get_metadata(cls) -> NodeMetadata:
        """Static node metadata — type, name, category, properties schema."""
        pass

    @classmethod
    def get_properties_model(cls) -> type[TProps]:
        """Override this to provide a Pydantic model for property validation."""

        return cast(type[TProps], cls.DefaultProps)

    def validate_properties(self, properties: dict[str, Any]) -> TProps:
        """Validate properties against the Pydantic model.

        Coerces numeric / boolean values to strings for fields whose
        annotation is ``str`` (or ``str | None``). JSONata expressions
        like ``=2`` resolve to the typed value ``2`` (int), and
        Pydantic v2's strict typing rejects that for a string field.
        Text-input fields should accept whatever the user typed — the
        coercion mirrors that expectation at the boundary.
        """
        model = self.get_properties_model()
        coerced = dict(properties)
        for name, field in getattr(model, "model_fields", {}).items():
            if name not in coerced:
                continue
            if not _field_accepts_only_str(field.annotation):
                continue
            value = coerced[name]
            # bool is a subclass of int — guard so we don't lose `True`/`False`
            # round-trips via numeric coercion.
            if isinstance(value, bool):
                coerced[name] = "true" if value else "false"
            elif isinstance(value, int | float):
                coerced[name] = str(value)
        return model(**coerced)

    @abstractmethod
    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        """Core execution logic for the node."""
        pass


def _field_accepts_only_str(annotation: Any) -> bool:
    """Return True when the field annotation is ``str`` or a union that
    accepts ``str`` (e.g. ``str | None`` or ``Optional[str]``).

    A union like ``int | str`` is intentionally false — the caller meant
    to accept both kinds and Pydantic will pick the right branch
    without our help.
    """
    if annotation is str:
        return True
    origin = get_origin(annotation)
    # Union / Optional / new-style `str | None`.
    if origin is None:
        return False
    args = [a for a in get_args(annotation) if a is not type(None)]
    return len(args) == 1 and args[0] is str
