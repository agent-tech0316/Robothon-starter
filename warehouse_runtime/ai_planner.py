from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class PlannerDecision:
    planner_mode: str
    strategy: str
    handoff_enabled: bool
    zone_bias: str
    priority_boost: float
    latest_decision: str
    source: str = "local"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def local_planner_decision(summary: dict[str, Any]) -> PlannerDecision:
    load = summary.get("load", "medium")
    active = int(summary.get("active_orders", 0))
    waiting = int(summary.get("waiting_robots", 0))
    deadlocks = int(summary.get("deadlocks", 0))

    if deadlocks:
        return PlannerDecision(
            planner_mode="local",
            strategy="deadlock_recovery_first",
            handoff_enabled=False,
            zone_bias="buffer",
            priority_boost=18.0,
            latest_decision="Local planner prioritizes deadlock recovery and buffer reroutes.",
        )
    if load == "high" or active > 40:
        return PlannerDecision(
            planner_mode="local",
            strategy="surge_throughput",
            handoff_enabled=True,
            zone_bias="outbound",
            priority_boost=12.0,
            latest_decision="Local planner enables surge routing with optional handoff buffers.",
        )
    if waiting > 3:
        return PlannerDecision(
            planner_mode="local",
            strategy="decongest_aisles",
            handoff_enabled=False,
            zone_bias="wide_aisle",
            priority_boost=8.0,
            latest_decision="Local planner reroutes around waiting robots and balances aisles.",
        )
    return PlannerDecision(
        planner_mode="local",
        strategy="balanced_direct_fulfillment",
        handoff_enabled=False,
        zone_bias="nearest_pick",
        priority_boost=5.0,
        latest_decision="Local planner keeps balanced direct fulfillment routes.",
    )


def openai_planner_decision(summary: dict[str, Any], fallback: PlannerDecision) -> PlannerDecision:
    """Optional OpenAI planner hook.

    This function is deliberately optional and dependency-free. It uses the
    standard OpenAI API key from OPENAI_API_KEY and model name from OPENAI_MODEL.
    If either value is missing, the network is unavailable, or the response is
    not valid JSON, the runtime falls back to the local planner.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL")
    if not api_key or not model:
        fallback.source = "local_fallback_no_openai_env"
        fallback.latest_decision += " OpenAI planner not called because OPENAI_API_KEY or OPENAI_MODEL is missing."
        return fallback

    prompt = {
        "role": "runtime_planner",
        "task": "Choose a warehouse scheduling strategy for the next 10 simulated minutes.",
        "allowed_output": {
            "strategy": "short snake_case strategy name",
            "handoff_enabled": "boolean",
            "zone_bias": "nearest_pick|outbound|wide_aisle|buffer",
            "priority_boost": "number between 0 and 25",
            "latest_decision": "one short operator-readable sentence",
        },
        "runtime_summary": summary,
    }
    body = json.dumps({
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Return only compact JSON for this warehouse runtime planning decision: "
                        + json.dumps(prompt, ensure_ascii=False),
                    }
                ],
            }
        ],
    }).encode("utf-8")

    try:
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        text = _extract_response_text(payload)
        decision_data = json.loads(text)
        return PlannerDecision(
            planner_mode="openai",
            strategy=str(decision_data.get("strategy", fallback.strategy)),
            handoff_enabled=bool(decision_data.get("handoff_enabled", fallback.handoff_enabled)),
            zone_bias=str(decision_data.get("zone_bias", fallback.zone_bias)),
            priority_boost=float(decision_data.get("priority_boost", fallback.priority_boost)),
            latest_decision=str(decision_data.get("latest_decision", fallback.latest_decision)),
            source="openai",
        )
    except Exception as exc:  # noqa: BLE001 - planner must never stop the simulator.
        fallback.source = "local_fallback_openai_error"
        fallback.latest_decision += f" OpenAI planner fallback: {type(exc).__name__}."
        return fallback


def _extract_response_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    chunks: list[str] = []
    for item in payload.get("output", []) or []:
        for content in item.get("content", []) or []:
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    if chunks:
        return "".join(chunks).strip()
    raise ValueError("OpenAI response did not include output text")
