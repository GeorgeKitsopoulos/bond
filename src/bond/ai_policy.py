#!/usr/bin/env python3
from dataclasses import dataclass

from ai_router import RouterDecision

POLICY_MODE_CHAT = "chat"
POLICY_MODE_ACTION = "action"
POLICY_MODE_ACTION_CHAIN = "action_chain"
POLICY_MODE_REJECT = "reject"
POLICY_MODE_CONFIRM_REQUIRED = "confirm_required"

POLICY_REASON_ALLOWED_CHAT = "allowed_chat"
POLICY_REASON_ALLOWED_ACTION = "allowed_action"
POLICY_REASON_ALLOWED_ACTION_CHAIN = "allowed_action_chain"
POLICY_REASON_MIXED_INTENT = "mixed_intent_request"
POLICY_REASON_HIGH_RISK_ACTION = "high_risk_action_requires_confirmation"


@dataclass
class PolicyDecision:
    mode: str
    allowed: bool
    reason: str
    risk_level: str
    requires_confirmation: bool
    exit_code: int
    user_message: str
    action_steps: list[str]
    metadata: dict

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "allowed": self.allowed,
            "reason": self.reason,
            "risk_level": self.risk_level,
            "requires_confirmation": self.requires_confirmation,
            "exit_code": self.exit_code,
            "user_message": self.user_message,
            "action_steps": self.action_steps,
            "metadata": self.metadata,
        }


def evaluate_request_policy(
    text: str,
    gatekeeper_result: str,
    chain_steps: list[str] | None,
    route_decision: RouterDecision | None,
    override_profile: str | None = None,
) -> PolicyDecision:
    steps = list(chain_steps or [])
    risk_level = route_decision.risk_level if route_decision else "low"
    route_intent = route_decision.intent if route_decision else None
    route_primary_agent = route_decision.primary_agent if route_decision else None

    if gatekeeper_result == "mixed":
        return PolicyDecision(
            mode=POLICY_MODE_REJECT,
            allowed=False,
            reason=POLICY_REASON_MIXED_INTENT,
            risk_level=risk_level,
            requires_confirmation=False,
            exit_code=4,
            user_message="Separate actions from questions. Run the action first, then ask the question.",
            action_steps=steps,
            metadata={
                "gatekeeper_result": gatekeeper_result,
                "route_intent": route_intent,
                "route_primary_agent": route_primary_agent,
                "override_profile": override_profile,
                "text_length": len(text),
            },
        )

    if gatekeeper_result == "pure_action" and risk_level == "high":
        return PolicyDecision(
            mode=POLICY_MODE_CONFIRM_REQUIRED,
            allowed=False,
            reason=POLICY_REASON_HIGH_RISK_ACTION,
            risk_level="high",
            requires_confirmation=True,
            exit_code=5,
            user_message=(
                "This looks privileged, destructive, or system-changing. Bond will not execute it without an explicit "
                "confirmation flow. For now, ask for an explanation or a safe dry-run plan instead."
            ),
            action_steps=steps,
            metadata={
                "gatekeeper_result": gatekeeper_result,
                "route_intent": route_intent,
                "route_primary_agent": route_primary_agent,
                "matched_signals": route_decision.matched_signals if route_decision else [],
                "override_profile": override_profile,
                "text_length": len(text),
            },
        )

    if gatekeeper_result == "pure_action" and steps:
        return PolicyDecision(
            mode=POLICY_MODE_ACTION_CHAIN,
            allowed=True,
            reason=POLICY_REASON_ALLOWED_ACTION_CHAIN,
            risk_level=risk_level,
            requires_confirmation=False,
            exit_code=0,
            user_message="",
            action_steps=steps,
            metadata={
                "gatekeeper_result": gatekeeper_result,
                "route_intent": route_intent,
                "route_primary_agent": route_primary_agent,
                "override_profile": override_profile,
                "text_length": len(text),
            },
        )

    if gatekeeper_result == "pure_action" and not steps:
        return PolicyDecision(
            mode=POLICY_MODE_ACTION,
            allowed=True,
            reason=POLICY_REASON_ALLOWED_ACTION,
            risk_level=risk_level,
            requires_confirmation=False,
            exit_code=0,
            user_message="",
            action_steps=[],
            metadata={
                "gatekeeper_result": gatekeeper_result,
                "route_intent": route_intent,
                "route_primary_agent": route_primary_agent,
                "override_profile": override_profile,
                "text_length": len(text),
            },
        )

    return PolicyDecision(
        mode=POLICY_MODE_CHAT,
        allowed=True,
        reason=POLICY_REASON_ALLOWED_CHAT,
        risk_level=risk_level,
        requires_confirmation=False,
        exit_code=0,
        user_message="",
        action_steps=[],
        metadata={
            "gatekeeper_result": gatekeeper_result,
            "route_intent": route_intent,
            "route_primary_agent": route_primary_agent,
            "override_profile": override_profile,
            "text_length": len(text),
        },
    )


def policy_to_log_meta(policy_decision: PolicyDecision | None) -> dict | None:
    if policy_decision is None:
        return None
    return policy_decision.to_dict()


def build_policy_rejection_response(policy_decision: PolicyDecision, assistant_name: str) -> dict:
    return {
        "ok": False,
        "assistant": assistant_name,
        "error": policy_decision.reason,
        "detail": policy_decision.user_message,
        "requires_confirmation": policy_decision.requires_confirmation,
        "risk_level": policy_decision.risk_level,
    }
