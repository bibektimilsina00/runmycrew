from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

_MAX_ROUNDS = 20


class AgentCrewProperties(BaseModel):
    goal: str = ""
    maxRounds: int = 4
    minRounds: int = 1
    stagnationRounds: int = 2
    verificationLevel: int = 3  # 1-5, informational, passed through to output
    maxCostUsd: float = 0.5


class AgentCrewNode(BaseNode[AgentCrewProperties]):
    @classmethod
    def get_properties_model(cls) -> type[AgentCrewProperties]:
        return AgentCrewProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="ai.agent_crew",
            name="Agent Crew",
            category="ai",
            description=(
                "Orchestrate downstream role-agents in a verified maker/checker loop "
                "with named terminal states and a cost-per-accepted-change metric."
            ),
            icon="Repeat",
            color="#8b5cf6",
            properties=[
                {
                    "name": "goal",
                    "label": "Goal",
                    "type": "string",
                    "placeholder": "Describe the objective the crew should achieve.",
                    "description": "Passed to every downstream round as `goal`.",
                },
                {
                    "name": "maxRounds",
                    "label": "Max Rounds",
                    "type": "number",
                    "default": 4,
                    "description": "Maximum maker/checker rounds before the loop is exhausted.",
                },
                {
                    "name": "minRounds",
                    "label": "Min Rounds",
                    "type": "number",
                    "default": 1,
                    "description": "Minimum rounds before success/blocked can terminate the loop.",
                },
                {
                    "name": "stagnationRounds",
                    "label": "Stagnation Rounds",
                    "type": "number",
                    "default": 2,
                    "mode": "advanced",
                    "description": (
                        "Terminate as 'stalled' when the checker average fails to "
                        "improve for this many consecutive rounds."
                    ),
                },
                {
                    "name": "verificationLevel",
                    "label": "Verification Level",
                    "type": "number",
                    "default": 3,
                    "mode": "advanced",
                    "description": "1-5 rigor hint (informational, passed through to output).",
                },
                {
                    "name": "maxCostUsd",
                    "label": "Max Cost (USD)",
                    "type": "number",
                    "default": 0.5,
                    "description": "Budget cap; loop terminates as 'exhausted' when exceeded.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "status", "type": "string"},
                {"label": "terminal_state", "type": "string"},
                {"label": "rounds", "type": "number"},
                {"label": "result", "type": "object"},
                {"label": "usage", "type": "object"},
                {"label": "cost_per_accepted_change", "type": "number"},
                {"label": "verification_level", "type": "number"},
            ],
        )

    @staticmethod
    def _accumulate_usage(source: Any) -> tuple[float, int]:
        """Best-effort scan of a value for usage dicts.

        Looks for `agent_usage` / `usage` / `tokens` sub-dicts and sums
        `cost_usd` and `total_tokens` when present. Returns (cost, tokens).
        """
        cost = 0.0
        tokens = 0
        if not isinstance(source, dict):
            return cost, tokens
        for key in ("agent_usage", "usage", "tokens"):
            usage = source.get(key)
            if isinstance(usage, dict):
                raw_cost = usage.get("cost_usd")
                if isinstance(raw_cost, int | float):
                    cost += float(raw_cost)
                raw_tokens = usage.get("total_tokens")
                if isinstance(raw_tokens, int | float) and not isinstance(raw_tokens, bool):
                    tokens += int(raw_tokens)
        return cost, tokens

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.run_downstream is None:
            return NodeResult(success=False, error="run_downstream not injected")

        max_rounds = max(1, min(self.props.maxRounds, _MAX_ROUNDS))
        min_rounds = max(1, self.props.minRounds)
        stagnation_rounds = max(1, self.props.stagnationRounds)

        current_input = input_data
        last_feedback: Any = None
        iteration_result: dict[str, Any] = {}

        total_cost = 0.0
        total_tokens = 0
        rounds_done = 0

        best_average: float | None = None
        stagnant_streak = 0

        terminal = "no_op"

        for round_idx in range(max_rounds):
            sub = await context.run_downstream(
                {
                    **current_input,
                    "goal": self.props.goal,
                    "round": round_idx,
                    "feedback": last_feedback,
                },
                loop_data={
                    "round": round_idx,
                    "total": max_rounds,
                    "feedback": last_feedback,
                },
            )
            rounds_done = round_idx + 1
            iteration_result = sub[-1] if sub else {}

            # Accumulate cost/tokens best-effort across the whole sub-run.
            for entry in sub or []:
                c, t = self._accumulate_usage(entry)
                total_cost += c
                total_tokens += t

            passed = bool(iteration_result.get("passed"))
            feedback = iteration_result.get("feedback")
            average = iteration_result.get("average")

            reached_min = round_idx + 1 >= min_rounds

            # Blocked/failed sub-run (or nothing ran) after min rounds.
            status = iteration_result.get("status") if isinstance(iteration_result, dict) else None
            if reached_min and (not sub or status in {"failed", "blocked"}):
                terminal = "blocked"
                last_feedback = feedback
                break

            # Success verdict from the checker.
            if passed and reached_min:
                terminal = "success"
                last_feedback = feedback
                break

            # Stagnation tracking on the checker average.
            if isinstance(average, int | float) and not isinstance(average, bool):
                if best_average is None or average > best_average:
                    best_average = float(average)
                    stagnant_streak = 0
                else:
                    stagnant_streak += 1
            if stagnant_streak >= stagnation_rounds:
                terminal = "stalled"
                last_feedback = feedback
                break

            # Budget exhausted.
            if total_cost > self.props.maxCostUsd:
                terminal = "exhausted"
                last_feedback = feedback
                break

            # Loop ran but no verdict/success yet — remember we did work.
            terminal = "exhausted"
            last_feedback = feedback

        accepted_changes = 1 if terminal == "success" else 0
        cost_per_accepted_change = (total_cost / accepted_changes) if accepted_changes else None

        return NodeResult(
            success=True,
            output_data={
                "status": terminal,
                "terminal_state": terminal,
                "rounds": rounds_done,
                "result": iteration_result,
                "usage": {
                    "total_tokens": total_tokens,
                    "cost_usd": total_cost,
                    "rounds": rounds_done,
                },
                "cost_per_accepted_change": cost_per_accepted_change,
                "verification_level": self.props.verificationLevel,
            },
            handled_successors=True,
        )
