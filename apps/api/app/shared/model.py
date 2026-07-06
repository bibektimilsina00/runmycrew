"""Register SQLAlchemy feature models with the shared metadata registry."""

import apps.api.app.features.api_keys.models  # noqa: F401
import apps.api.app.features.assets.models  # noqa: F401
import apps.api.app.features.copilot.models  # noqa: F401
import apps.api.app.features.credentials.models  # noqa: F401
import apps.api.app.features.crews.models  # noqa: F401
import apps.api.app.features.escalation.models  # noqa: F401
import apps.api.app.features.executions.models  # noqa: F401
import apps.api.app.features.folders.models  # noqa: F401
import apps.api.app.features.knowledge.models  # noqa: F401
import apps.api.app.features.logs.models  # noqa: F401
import apps.api.app.features.meta.models  # noqa: F401
import apps.api.app.features.secrets.models  # noqa: F401
import apps.api.app.features.skills.models  # noqa: F401
import apps.api.app.features.tables.models  # noqa: F401

# Templates depend on User + Workspace being registered first (Template.creator
# relationship resolves a string class name from the mapper registry), so this
# import lives at the end of the list.
import apps.api.app.features.templates.models  # noqa: F401  # noqa: E402
import apps.api.app.features.triggers.models  # noqa: F401
import apps.api.app.features.users.models  # noqa: F401
import apps.api.app.features.workflows.models  # noqa: F401
