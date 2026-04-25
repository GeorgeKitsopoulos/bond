#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any

from ai_action_parse import parse_request
from ai_intent import classify_request
from ai_linguistics import normalize_action_text

STATUS_CHAT_OR_QUESTION = "chat_or_question"
STATUS_MIXED = "mixed"
STATUS_UNKNOWN = "unknown"
STATUS_PARSED_ACTION = "parsed_action"
STATUS_PARSED_ACTION_CHAIN = "parsed_action_chain"
STATUS_UNPARSED_ACTION = "unparsed_action"
STATUS_PARTIAL_ACTION_CHAIN = "partial_action_chain"

REASON_NOT_ACTION = "not_action"
REASON_MIXED_INTENT = "mixed_intent"
REASON_UNKNOWN_INTENT = "unknown_intent"
REASON_SINGLE_ACTION_PARSED = "single_action_parsed"
REASON_ALL_CHAIN_STEPS_PARSED = "all_chain_steps_parsed"
REASON_SINGLE_ACTION_UNPARSED = "single_action_unparsed"
REASON_ONE_OR_MORE_CHAIN_STEPS_UNPARSED = "one_or_more_chain_steps_unparsed"


@dataclass
class ParseContract:
    status: str
    executable: bool
    ambiguous: bool
    reason: str
    raw_text: str
    normalized_text: str
    gatekeeper_result: str
    chain_steps: list[str]
    parsed_intents: list[dict[str, Any]]
    unparsed_steps: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "executable": self.executable,
            "ambiguous": self.ambiguous,
            "reason": self.reason,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "gatekeeper_result": self.gatekeeper_result,
            "chain_steps": self.chain_steps,
            "parsed_intents": self.parsed_intents,
            "unparsed_steps": self.unparsed_steps,
            "metadata": self.metadata,
        }


def _parse_step(step: str) -> dict[str, Any] | None:
    normalized = normalize_action_text(step)
    parsed = parse_request(normalized)
    if not parsed:
        return None
    return dict(parsed)


def build_parse_contract(
    text: str,
    gatekeeper_result: str | None = None,
    chain_steps: list[str] | None = None,
) -> ParseContract:
    raw_text = text.strip()
    normalized_text = normalize_action_text(raw_text)

    if gatekeeper_result is None:
        gatekeeper_result, detected_chain_steps = classify_request(normalized_text)
        if chain_steps is None:
            chain_steps = detected_chain_steps

    steps = list(chain_steps or [])

    base_metadata: dict[str, Any] = {
        "text_length": len(raw_text),
        "normalized_text_length": len(normalized_text),
        "chain_step_count": len(steps),
    }

    if gatekeeper_result == "mixed":
        return ParseContract(
            status=STATUS_MIXED,
            executable=False,
            ambiguous=True,
            reason=REASON_MIXED_INTENT,
            raw_text=raw_text,
            normalized_text=normalized_text,
            gatekeeper_result=gatekeeper_result,
            chain_steps=steps,
            parsed_intents=[],
            unparsed_steps=[],
            metadata=base_metadata,
        )

    if gatekeeper_result == "pure_question":
        return ParseContract(
            status=STATUS_CHAT_OR_QUESTION,
            executable=False,
            ambiguous=False,
            reason=REASON_NOT_ACTION,
            raw_text=raw_text,
            normalized_text=normalized_text,
            gatekeeper_result=gatekeeper_result,
            chain_steps=steps,
            parsed_intents=[],
            unparsed_steps=[],
            metadata=base_metadata,
        )

    if gatekeeper_result == "unknown":
        return ParseContract(
            status=STATUS_UNKNOWN,
            executable=False,
            ambiguous=True,
            reason=REASON_UNKNOWN_INTENT,
            raw_text=raw_text,
            normalized_text=normalized_text,
            gatekeeper_result=gatekeeper_result,
            chain_steps=steps,
            parsed_intents=[],
            unparsed_steps=[],
            metadata=base_metadata,
        )

    if gatekeeper_result != "pure_action":
        return ParseContract(
            status=STATUS_CHAT_OR_QUESTION,
            executable=False,
            ambiguous=False,
            reason=REASON_NOT_ACTION,
            raw_text=raw_text,
            normalized_text=normalized_text,
            gatekeeper_result=gatekeeper_result or "",
            chain_steps=steps,
            parsed_intents=[],
            unparsed_steps=[],
            metadata=base_metadata,
        )

    if steps:
        parsed_intents: list[dict[str, Any]] = []
        unparsed_steps: list[str] = []

        for step in steps:
            parsed = _parse_step(step)
            if parsed:
                parsed_intents.append(parsed)
            else:
                unparsed_steps.append(step)

        if unparsed_steps:
            return ParseContract(
                status=STATUS_PARTIAL_ACTION_CHAIN,
                executable=False,
                ambiguous=True,
                reason=REASON_ONE_OR_MORE_CHAIN_STEPS_UNPARSED,
                raw_text=raw_text,
                normalized_text=normalized_text,
                gatekeeper_result=gatekeeper_result,
                chain_steps=steps,
                parsed_intents=parsed_intents,
                unparsed_steps=unparsed_steps,
                metadata={
                    **base_metadata,
                    "parsed_step_count": len(parsed_intents),
                    "unparsed_step_count": len(unparsed_steps),
                },
            )

        return ParseContract(
            status=STATUS_PARSED_ACTION_CHAIN,
            executable=True,
            ambiguous=False,
            reason=REASON_ALL_CHAIN_STEPS_PARSED,
            raw_text=raw_text,
            normalized_text=normalized_text,
            gatekeeper_result=gatekeeper_result,
            chain_steps=steps,
            parsed_intents=parsed_intents,
            unparsed_steps=[],
            metadata={
                **base_metadata,
                "parsed_step_count": len(parsed_intents),
                "unparsed_step_count": 0,
            },
        )

    parsed_single = _parse_step(normalized_text)
    if parsed_single:
        return ParseContract(
            status=STATUS_PARSED_ACTION,
            executable=True,
            ambiguous=False,
            reason=REASON_SINGLE_ACTION_PARSED,
            raw_text=raw_text,
            normalized_text=normalized_text,
            gatekeeper_result=gatekeeper_result,
            chain_steps=[],
            parsed_intents=[parsed_single],
            unparsed_steps=[],
            metadata={
                **base_metadata,
                "parsed_step_count": 1,
                "unparsed_step_count": 0,
            },
        )

    return ParseContract(
        status=STATUS_UNPARSED_ACTION,
        executable=False,
        ambiguous=True,
        reason=REASON_SINGLE_ACTION_UNPARSED,
        raw_text=raw_text,
        normalized_text=normalized_text,
        gatekeeper_result=gatekeeper_result,
        chain_steps=[],
        parsed_intents=[],
        unparsed_steps=[normalized_text or raw_text],
        metadata={
            **base_metadata,
            "parsed_step_count": 0,
            "unparsed_step_count": 1,
        },
    )


def parse_contract_to_log_meta(contract: ParseContract | None) -> dict[str, Any] | None:
    if contract is None:
        return None
    return contract.to_dict()


def build_action_not_parsed_response(contract: ParseContract, assistant_name: str) -> dict[str, Any]:
    return {
        "ok": False,
        "assistant": assistant_name,
        "error": "action_not_parsed",
        "detail": "This looked like an action, but Bond did not parse a safe executable action shape.",
        "requires_confirmation": False,
        "would_execute": False,
        "dry_run": False,
        "reason": contract.reason,
        "unparsed_steps": contract.unparsed_steps,
    }
