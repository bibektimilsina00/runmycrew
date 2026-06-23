"""Workspace-level escalation handler for failed agent loops.

When an ``ai.agent`` (or ``ai.agent_loop``) ends with
``failure_policy='escalate'``, the runtime calls
``EscalationService.dispatch()`` with the run context. The handler
forwards a structured payload to whichever channel the workspace has
configured (Slack, email, webhook).

Configuration lives at the workspace level — every loop in the same
workspace shares one escalation endpoint. Configured via
``Settings → Automations → Escalation`` in the product UI, or via
``PUT /api/v1/workspaces/{id}/escalation-config``.

See ``docs/loop-engineering-plan.md`` section 8.8.
"""

from .schemas import EscalationConfig, EscalationPayload
from .service import EscalationService

__all__ = ["EscalationConfig", "EscalationPayload", "EscalationService"]
