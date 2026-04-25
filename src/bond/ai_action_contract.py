#!/usr/bin/env python3
import os
import re
from dataclasses import dataclass

from ai_policy import (
    POLICY_MODE_ACTION,
    POLICY_MODE_ACTION_CHAIN,
    PolicyDecision,
)
from ai_router import RouterDecision

ACTION_EXECUTE = "execute"
ACTION_DRY_RUN = "dry_run"
ACTION_CONFIRM_REQUIRED = "confirm_required"
ACTION_REJECT = "reject"
ACTION_CHAT = "chat"

CONTRACT_REASON_CHAT = "chat_no_action_contract"
CONTRACT_REASON_POLICY_REJECTED = "policy_rejected"
CONTRACT_REASON_POLICY_CONFIRM_REQUIRED = "policy_confirmation_required"
CONTRACT_REASON_EXPLICIT_DRY_RUN = "explicit_dry_run_requested"
CONTRACT_REASON_ENV_DRY_RUN = "environment_dry_run_enabled"
CONTRACT_REASON_SAFE_ACTION_EXECUTE = "safe_action_execute"
CONTRACT_REASON_SAFE_ACTION_CHAIN_EXECUTE = "safe_action_chain_execute"
CONTRACT_REASON_CONFIRMED_ACTION_EXECUTE = "confirmed_action_execute"
CONTRACT_REASON_CONFIRMED_ACTION_NO_EXECUTABLE_STEPS = "confirmed_action_no_executable_steps"


@dataclass
class ActionContract:
    mode: str
    allowed_to_execute: bool
    dry_run: bool
    requires_confirmation: bool
    reason: str
    risk_level: str
    action_steps: list[str]
    user_message: str
    exit_code: int
    metadata: dict

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "allowed_to_execute": self.allowed_to_execute,
            "dry_run": self.dry_run,
            "requires_confirmation": self.requires_confirmation,
            "reason": self.reason,
            "risk_level": self.risk_level,
            "action_steps": self.action_steps,
            "user_message": self.user_message,
            "exit_code": self.exit_code,
            "metadata": self.metadata,
        }


def is_env_dry_run_enabled() -> bool:
    value = os.environ.get("BOND_ACTION_DRY_RUN", "")
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def detect_explicit_dry_run(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    signals = [
        "dry run",
        "dry-run",
        "preview only",
        "no execute",
        "don't execute",
        "do not execute",
        "without executing",
        "show what you would do",
        "what would you do",
        "plan only",
        "simulate",
        "χωρις εκτελεση",
        "χωρίς εκτέλεση",
        "μην εκτελεσεις",
        "μην εκτελέσεις",
        "μη το εκτελεσεις",
        "μη το εκτελέσεις",
        "μονο σχεδιο",
        "μόνο σχέδιο",
        "προεπισκοπηση",
        "προεπισκόπηση",
        "δειξε τι θα εκανες",
        "δείξε τι θα έκανες",
        "προσομοιωση",
        "προσομοίωση",
    ]
    return any(signal in normalized for signal in signals)


def build_action_contract(
    text: str,
    policy_decision: PolicyDecision,
    route_decision: RouterDecision | None = None,
    *,
    confirmation_granted: bool = False,
) -> ActionContract:
    env_dry_run = is_env_dry_run_enabled()
    explicit_dry_run = detect_explicit_dry_run(text)

    shared_metadata = {
        "policy_reason": policy_decision.reason,
        "policy_mode": policy_decision.mode,
        "route_intent": route_decision.intent if route_decision else None,
        "route_primary_agent": route_decision.primary_agent if route_decision else None,
        "route_risk_level": route_decision.risk_level if route_decision else None,
        "env_dry_run": env_dry_run,
        "explicit_dry_run": explicit_dry_run,
        "text_length": len(text),
    }

    if not policy_decision.allowed and policy_decision.requires_confirmation and not confirmation_granted:
        return ActionContract(
            mode=ACTION_CONFIRM_REQUIRED,
            allowed_to_execute=False,
            dry_run=False,
            requires_confirmation=True,
            reason=CONTRACT_REASON_POLICY_CONFIRM_REQUIRED,
            risk_level=policy_decision.risk_level,
            action_steps=policy_decision.action_steps,
            user_message=policy_decision.user_message,
            exit_code=policy_decision.exit_code,
            metadata=shared_metadata,
        )

    if not policy_decision.allowed and not (confirmation_granted and policy_decision.requires_confirmation):
        return ActionContract(
            mode=ACTION_REJECT,
            allowed_to_execute=False,
            dry_run=False,
            requires_confirmation=False,
            reason=CONTRACT_REASON_POLICY_REJECTED,
            risk_level=policy_decision.risk_level,
            action_steps=policy_decision.action_steps,
            user_message=policy_decision.user_message,
            exit_code=policy_decision.exit_code,
            metadata=shared_metadata,
        )

    effective_mode = policy_decision.mode
    effective_action_steps = list(policy_decision.action_steps)
    effective_risk_level = policy_decision.risk_level
    execute_reason = CONTRACT_REASON_SAFE_ACTION_EXECUTE
    confirmed_no_executable_steps = False

    if confirmation_granted and policy_decision.requires_confirmation:
        if policy_decision.action_steps:
            effective_mode = POLICY_MODE_ACTION_CHAIN
            effective_action_steps = list(policy_decision.action_steps)
        else:
            effective_mode = POLICY_MODE_ACTION
            effective_action_steps = []
            confirmed_no_executable_steps = True
        execute_reason = CONTRACT_REASON_CONFIRMED_ACTION_EXECUTE

    if effective_mode not in {POLICY_MODE_ACTION, POLICY_MODE_ACTION_CHAIN}:
        return ActionContract(
            mode=ACTION_CHAT,
            allowed_to_execute=False,
            dry_run=False,
            requires_confirmation=False,
            reason=CONTRACT_REASON_CHAT,
            risk_level=effective_risk_level,
            action_steps=[],
            user_message="",
            exit_code=0,
            metadata=shared_metadata,
        )

    if explicit_dry_run:
        return ActionContract(
            mode=ACTION_DRY_RUN,
            allowed_to_execute=False,
            dry_run=True,
            requires_confirmation=False,
            reason=CONTRACT_REASON_EXPLICIT_DRY_RUN,
            risk_level=effective_risk_level,
            action_steps=effective_action_steps,
            user_message="Dry-run only. No action was executed.",
            exit_code=0,
            metadata=shared_metadata,
        )

    if env_dry_run:
        return ActionContract(
            mode=ACTION_DRY_RUN,
            allowed_to_execute=False,
            dry_run=True,
            requires_confirmation=False,
            reason=CONTRACT_REASON_ENV_DRY_RUN,
            risk_level=effective_risk_level,
            action_steps=effective_action_steps,
            user_message="Dry-run only. No action was executed.",
            exit_code=0,
            metadata=shared_metadata,
        )

    if confirmed_no_executable_steps:
        return ActionContract(
            mode=ACTION_REJECT,
            allowed_to_execute=False,
            dry_run=False,
            requires_confirmation=False,
            reason=CONTRACT_REASON_CONFIRMED_ACTION_NO_EXECUTABLE_STEPS,
            risk_level=effective_risk_level,
            action_steps=effective_action_steps,
            user_message="Confirmation was valid, but no safe executable action steps were parsed.",
            exit_code=3,
            metadata=shared_metadata,
        )

    if effective_mode == POLICY_MODE_ACTION_CHAIN:
        return ActionContract(
            mode=ACTION_EXECUTE,
            allowed_to_execute=True,
            dry_run=False,
            requires_confirmation=False,
            reason=CONTRACT_REASON_SAFE_ACTION_CHAIN_EXECUTE if execute_reason != CONTRACT_REASON_CONFIRMED_ACTION_EXECUTE else execute_reason,
            risk_level=effective_risk_level,
            action_steps=effective_action_steps,
            user_message="",
            exit_code=0,
            metadata=shared_metadata,
        )

    return ActionContract(
        mode=ACTION_EXECUTE,
        allowed_to_execute=True,
        dry_run=False,
        requires_confirmation=False,
        reason=execute_reason,
        risk_level=effective_risk_level,
        action_steps=effective_action_steps,
        user_message="",
        exit_code=0,
        metadata=shared_metadata,
    )


def action_contract_to_log_meta(contract: ActionContract | None) -> dict | None:
    if contract is None:
        return None
    return contract.to_dict()


def build_dry_run_response(contract: ActionContract, assistant_name: str) -> dict:
    return {
        "ok": True,
        "assistant": assistant_name,
        "dry_run": True,
        "would_execute": False,
        "reason": contract.reason,
        "risk_level": contract.risk_level,
        "action_steps": contract.action_steps,
        "detail": contract.user_message,
    }


def build_confirmation_required_response(contract: ActionContract, assistant_name: str) -> dict:
    return {
        "ok": False,
        "assistant": assistant_name,
        "error": "confirmation_required",
        "detail": contract.user_message,
        "requires_confirmation": True,
        "risk_level": contract.risk_level,
        "action_steps": contract.action_steps,
    }
