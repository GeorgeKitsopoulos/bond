"""Contract for Bond's transitional linguistic intent handling.

Stage 2F-E-B records the current language-handling boundary without
claiming that smart linguistic support exists today. The current
mechanism is deterministic alias scaffolding behind the capability
classifier boundary. Future semantic or model-based handling must plug
in behind that boundary without spreading phrase lists into answer
generation code.
"""

from __future__ import annotations

from dataclasses import dataclass


CONTRACT_STAGE = "Stage 2F-E-B"
CONTRACT_NAME = "transitional_linguistic_intent_normalization"

CURRENT_MECHANISM = "deterministic_alias_scaffolding"
CLASSIFIER_BOUNDARY_MODULE = "ai_capability_classifier"
ANSWER_BOUNDARY_MODULE = "ai_capability_answer"

SCOPE_CAPABILITY_INTENT_ONLY = "capability_intent_only"
LANGUAGE_SCOPE_ENGLISH_GREEK = ("english", "greek")

PROHIBITED_CURRENT_CLAIMS = (
    "smart_linguistic_support_implemented",
    "semantic_classification_implemented",
    "model_based_classification_implemented",
    "broad_normal_answers_probe_backed",
    "arbitrary_language_understanding_implemented",
)

ALLOWED_TRANSITIONAL_SCAFFOLDING = (
    "deterministic_phrase_aliases",
    "explicit_capability_question_routing",
    "bounded_context_general_specific_answer_kinds",
    "compatibility_helper_imports",
)

FUTURE_EXTENSION_RULES = (
    "future language handling must plug in behind the classifier boundary",
    "answer generation must not own growing phrase lists",
    "semantic or model-based classification must preserve safety contracts",
    "new language behavior must be tested before it changes routing",
    "fallbacks must prefer no classification over unsafe overclassification",
)

SAFETY_INVARIANTS = (
    "classification must not execute actions",
    "classification must not run probes",
    "classification must not authorize execution",
    "classification must not make normal assistant answers broadly probe-backed",
    "classification must not imply unavailable capabilities are implemented",
)


@dataclass(frozen=True)
class LinguisticIntentNormalizationContract:
    stage: str
    name: str
    current_mechanism: str
    scope: str
    classifier_boundary_module: str
    answer_boundary_module: str
    language_scope: tuple[str, ...]
    allowed_transitional_scaffolding: tuple[str, ...]
    prohibited_current_claims: tuple[str, ...]
    future_extension_rules: tuple[str, ...]
    safety_invariants: tuple[str, ...]
    final_nlp_layer: bool
    smart_linguistic_support_available: bool
    semantic_classification_available: bool
    model_based_classification_available: bool


_CONTRACT = LinguisticIntentNormalizationContract(
    stage=CONTRACT_STAGE,
    name=CONTRACT_NAME,
    current_mechanism=CURRENT_MECHANISM,
    scope=SCOPE_CAPABILITY_INTENT_ONLY,
    classifier_boundary_module=CLASSIFIER_BOUNDARY_MODULE,
    answer_boundary_module=ANSWER_BOUNDARY_MODULE,
    language_scope=LANGUAGE_SCOPE_ENGLISH_GREEK,
    allowed_transitional_scaffolding=ALLOWED_TRANSITIONAL_SCAFFOLDING,
    prohibited_current_claims=PROHIBITED_CURRENT_CLAIMS,
    future_extension_rules=FUTURE_EXTENSION_RULES,
    safety_invariants=SAFETY_INVARIANTS,
    final_nlp_layer=False,
    smart_linguistic_support_available=False,
    semantic_classification_available=False,
    model_based_classification_available=False,
)


def get_linguistic_intent_normalization_contract() -> LinguisticIntentNormalizationContract:
    """Return the immutable Stage 2F-E-B linguistic intent contract."""

    return _CONTRACT


def is_transitional_linguistic_scaffolding() -> bool:
    """Return True while deterministic aliases remain transitional scaffolding."""

    return (
        _CONTRACT.current_mechanism == CURRENT_MECHANISM
        and not _CONTRACT.final_nlp_layer
        and not _CONTRACT.smart_linguistic_support_available
        and not _CONTRACT.semantic_classification_available
        and not _CONTRACT.model_based_classification_available
    )


def contract_summary_lines() -> tuple[str, ...]:
    """Return stable human-readable contract summary lines."""

    return (
        f"{_CONTRACT.stage}: {_CONTRACT.name}",
        f"current mechanism: {_CONTRACT.current_mechanism}",
        f"classifier boundary: {_CONTRACT.classifier_boundary_module}",
        f"answer boundary: {_CONTRACT.answer_boundary_module}",
        "deterministic aliases are transitional scaffolding",
        "smart linguistic support is not implemented",
        "semantic classification is not implemented",
        "model-based classification is not implemented",
        "classification must not execute actions or run probes",
    )


def validate_linguistic_intent_contract() -> tuple[bool, tuple[str, ...]]:
    """Validate internal consistency of the contract constants."""

    errors: list[str] = []

    if _CONTRACT.stage != CONTRACT_STAGE:
        errors.append("stage mismatch")
    if _CONTRACT.name != CONTRACT_NAME:
        errors.append("name mismatch")
    if _CONTRACT.current_mechanism != CURRENT_MECHANISM:
        errors.append("current mechanism mismatch")
    if _CONTRACT.classifier_boundary_module != CLASSIFIER_BOUNDARY_MODULE:
        errors.append("classifier boundary mismatch")
    if _CONTRACT.answer_boundary_module != ANSWER_BOUNDARY_MODULE:
        errors.append("answer boundary mismatch")
    if _CONTRACT.final_nlp_layer:
        errors.append("contract must not claim final NLP layer")
    if _CONTRACT.smart_linguistic_support_available:
        errors.append("contract must not claim smart linguistic support")
    if _CONTRACT.semantic_classification_available:
        errors.append("contract must not claim semantic classification")
    if _CONTRACT.model_based_classification_available:
        errors.append("contract must not claim model-based classification")

    required_safety = {
        "classification must not execute actions",
        "classification must not run probes",
        "classification must not authorize execution",
    }
    missing_safety = required_safety - set(_CONTRACT.safety_invariants)
    for item in sorted(missing_safety):
        errors.append(f"missing safety invariant: {item}")

    return (not errors, tuple(errors))
