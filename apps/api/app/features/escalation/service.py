"""Escalation handler — forwards failure events to Slack / email / webhook.

Stateless service: callers pass an ``EscalationConfig`` (loaded from
the workspace row) and an ``EscalationPayload``; we POST the right
payload to the right destination.

The runtime calls this from ``ai.agent.execute()`` finally-block when
``failure_policy == 'escalate'``. Failure to dispatch is logged but
NEVER re-raised — the loop already failed; making the failure handler
itself raise would mask the real cause in logs.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .schemas import EscalationConfig, EscalationPayload

logger = logging.getLogger(__name__)


SLACK_TIMEOUT = httpx.Timeout(10.0)
WEBHOOK_TIMEOUT = httpx.Timeout(10.0)


class EscalationService:
    """Stateless façade. Constructed per request; cheap."""

    async def dispatch(
        self,
        config: EscalationConfig | None,
        payload: EscalationPayload,
    ) -> dict[str, Any]:
        """Forward ``payload`` to whichever endpoint ``config`` points to.

        Returns a small status dict for logging / debugging:
        ``{'sent': bool, 'channel': str | None, 'error': str | None}``.

        Never raises — the loop already failed, the handler must not.
        """
        if config is None or not config.enabled:
            return {"sent": False, "channel": None, "error": "no_config"}

        try:
            if config.slack_webhook_url:
                await self._send_slack(config.slack_webhook_url, payload)
                return {"sent": True, "channel": "slack", "error": None}
            if config.webhook_url:
                await self._send_webhook(config.webhook_url, payload)
                return {"sent": True, "channel": "webhook", "error": None}
            if config.email_to:
                await self._send_email(config.email_to, payload)
                return {"sent": True, "channel": "email", "error": None}
        except Exception as exc:
            logger.exception(
                "escalation: dispatch failed for workflow=%s",
                payload.workflow_id,
            )
            return {"sent": False, "channel": None, "error": str(exc)}

        return {"sent": False, "channel": None, "error": "no_channel_configured"}

    # ── Channel implementations ──────────────────────────────────────

    async def _send_slack(self, webhook_url: str, payload: EscalationPayload) -> None:
        """POST a Block Kit message to Slack incoming-webhook URL.

        Renders the payload as a rich card. Reads cleanly inside a
        Slack thread without needing a custom app.
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"⚠️  Workflow escalation — {payload.workflow_name}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Status:*\n`{payload.status}`"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Reason:*\n{payload.failure_reason or '_unknown_'}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Started:*\n<!date^{int(payload.started_at.timestamp())}^{{date_short_pretty}} {{time}}|{payload.started_at.isoformat()}>",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Ended:*\n<!date^{int(payload.ended_at.timestamp())}^{{date_short_pretty}} {{time}}|{payload.ended_at.isoformat()}>",
                    },
                ],
            },
        ]
        if payload.trace_summary:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Trace:*\n```{payload.trace_summary[:2800]}```",
                    },
                }
            )
        if payload.usage:
            usage_lines = "\n".join(
                f"• *{k}:* `{v}`" for k, v in payload.usage.items() if not isinstance(v, dict)
            )
            if usage_lines:
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Usage:*\n{usage_lines}"},
                    }
                )
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Open run"},
                        "url": payload.run_url,
                    }
                ],
            }
        )

        body = {"blocks": blocks, "text": f"Workflow escalation: {payload.workflow_name}"}
        async with httpx.AsyncClient(timeout=SLACK_TIMEOUT) as client:
            resp = await client.post(webhook_url, json=body)
            resp.raise_for_status()

    async def _send_webhook(self, url: str, payload: EscalationPayload) -> None:
        """POST the full structured payload as JSON to a generic webhook."""
        async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT) as client:
            resp = await client.post(url, json=json.loads(payload.model_dump_json()))
            resp.raise_for_status()

    async def _send_email(self, to: str, payload: EscalationPayload) -> None:
        """Send via the existing SMTP service.

        Subject: ``[RunMyCrew escalation] {workflow_name}``. Body is
        a plain-text rendering — no HTML email until product asks for
        it (most ops alerts are read on mobile).
        """
        # Lazy import to avoid hard dependency at module load time —
        # tests can run without SMTP wired.
        from apps.api.app.utils.email_service import EmailService

        body = (
            f"Workflow escalation — {payload.workflow_name}\n"
            f"\n"
            f"Status: {payload.status}\n"
            f"Reason: {payload.failure_reason or 'unknown'}\n"
            f"Started: {payload.started_at.isoformat()}\n"
            f"Ended:   {payload.ended_at.isoformat()}\n"
            f"\n"
            f"Open the run: {payload.run_url}\n"
            f"\n"
            f"Trace summary:\n{payload.trace_summary or '(no trace summary)'}\n"
        )
        await EmailService().send_simple(
            to=to,
            subject=f"[RunMyCrew escalation] {payload.workflow_name}",
            body=body,
        )

    def build_payload_from_run(
        self,
        *,
        workflow_id,
        workflow_name: str,
        run_id,
        status: str,
        failure_reason: str | None,
        started_at,
        ended_at,
        trace: list[dict[str, Any]] | None,
        usage: dict[str, Any] | None,
        agent_label: str | None = None,
        base_url: str = "https://app.runmycrew.com",
    ) -> EscalationPayload:
        """Helper: construct a payload from raw run data.

        Used by the runtime so the failure handler doesn't have to
        know all the field names. Computes a trace summary (the last
        3 step thoughts + the last tool call) so Slack messages have
        useful context.
        """
        last_tool: str | None = None
        summary_lines: list[str] = []
        if trace:
            tail = trace[-5:]
            for step in tail:
                tc = step.get("tool_call") or {}
                if isinstance(tc, dict) and tc.get("name"):
                    last_tool = tc["name"]
                    summary_lines.append(
                        f"step {step.get('step', '?')}: {tc.get('name')}({_short(tc.get('args'))})"
                    )
                else:
                    summary_lines.append(f"step {step.get('step', '?')}: final")
        trace_summary = "\n".join(summary_lines) if summary_lines else None
        return EscalationPayload(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            run_id=run_id,
            run_url=f"{base_url.rstrip('/')}/runs/{run_id}",
            status=status,
            failure_reason=failure_reason,
            started_at=started_at,
            ended_at=ended_at,
            trace_summary=trace_summary,
            usage=usage or {},
            agent_label=agent_label,
            last_tool_call=last_tool,
        )


def _short(value: Any, max_len: int = 80) -> str:
    if value is None:
        return ""
    s = json.dumps(value) if not isinstance(value, str) else value
    return s if len(s) <= max_len else (s[: max_len - 1] + "…")
