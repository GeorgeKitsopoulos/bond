#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

from ai_core import (
    BOND_ROOT,
    FILES,
    build_active_context,
    ensure_memory_dirs,
    get_changelog_path,
    get_memory_root,
    get_router_config_path,
    get_state_root,
    load_json,
    log_memory,
    tail_jsonl,
)
from ai_facts import (
    DEFAULT_PROFILE,
    ASSISTANT_NAME,
    answer_fact_query,
    choose_profile_config,
    detect_fact_query,
    extract_model_from_profile,
)
from ai_intent import classify_request
from ai_linguistics import normalize_action_text
from ai_action_contract import (
    ACTION_CHAT,
    CONTRACT_REASON_CONFIRMED_ACTION_NO_EXECUTABLE_STEPS,
    ACTION_CONFIRM_REQUIRED,
    ACTION_DRY_RUN,
    ACTION_EXECUTE,
    ACTION_REJECT,
    action_contract_to_log_meta,
    build_action_contract,
    build_confirmation_required_response,
    build_dry_run_response,
)
from ai_confirmation import (
    consume_pending_confirmation,
    create_pending_confirmation,
    parse_confirmation_request,
)
from ai_policy import (
    POLICY_MODE_ACTION,
    POLICY_MODE_ACTION_CHAIN,
    POLICY_MODE_CHAT,
    POLICY_MODE_CONFIRM_REQUIRED,
    POLICY_MODE_REJECT,
    build_policy_rejection_response,
    evaluate_request_policy,
    policy_to_log_meta,
)
from ai_parse_contract import (
    STATUS_PARTIAL_ACTION_CHAIN,
    STATUS_UNPARSED_ACTION,
    build_action_not_parsed_response,
    build_parse_contract,
    parse_contract_to_log_meta,
)
from ai_router import decision_to_log_meta, route_request

try:
    from ai_memory_query import query_memory
except Exception:
    query_memory = None

STATE_ROOT = get_state_root()
MEMORY_ROOT = get_memory_root()
ROUTER_CONFIG = get_router_config_path()
AI_EXEC_PATH = BOND_ROOT / "src" / "bond" / "ai_exec.py"

SYSTEM_SUMMARY = STATE_ROOT / "system_summary.txt"
CHANGELOG_PATH = get_changelog_path()
MAX_CHAIN_STEPS = 3
MEMORY_QUERY_MAX_ITEMS = 6
ACTIVE_CONTEXT_FALLBACK_LINES = 18
RECENT_CHANGE_DIRECT_LIMIT = 12

PROJECT_PRIORITY_HINTS = """
CURRENT PROJECT PRIORITIES
- The assistant identity shown to the user is Bond.
- The project is in the intelligence/retrieval phase, not the voice/UI/applet/package phase.
- The main bottleneck is grounded project-aware answering: using memory correctly instead of filling gaps with generic assistant talk.
- Current verified live behavior matters more than archive/history assumptions.
- Archive snapshots are for history, comparison, recovery context, and diffing; they are not automatic current truth.
- Prefer exact file/module names already present in the project over generic architecture advice.
- Prefer modifying existing files over proposing new subsystems.
- For implementation suggestions, stay aligned with this workflow: full file replacement, exact commands, compile checks, tests, then ai_change.py logging.
- Do not invent new folders, paths, snapshots, timers, jobs, services, or scripts unless the user explicitly asks to create them.
- Do not prioritize voice, Cinnamon applet, packaging, daemon mode, embeddings, or broad desktop integration unless the user explicitly redirects the project.
- Current direction after recent tightening: deterministic/script-first behavior, fact-first current-state retrieval, and stricter grounding for project-specific answers.
""".strip()

RECENT_CHANGE_PATTERNS = [
    r"\bwhat changed\b",
    r"\bwhat did we change\b",
    r"\brecent changes\b",
    r"\bmost recent\b",
    r"\blatest change\b",
    r"\brecently\b.*\bchange",
]

NEXT_STEP_PATTERNS = [
    r"\bwhat should we improve next\b",
    r"\bwhat should we do next\b",
    r"\bnext step\b",
    r"\bnext steps\b",
    r"\bwhat remains\b",
    r"\bwhat is the next priority\b",
    r"\bmake bond more like a real assistant\b",
]

ARCHIVE_POLICY_PATTERNS = [
    r"\bwhy do we avoid using the archive\b",
    r"\barchive as automatic current truth\b",
    r"\barchive as current truth\b",
    r"\bwhy .*archive.*current truth\b",
]

PROJECT_SPECIFIC_HINTS = [
    "bond",
    "archive",
    "live path",
    "current path",
    "router config",
    "profiles.json",
    "ai-run",
    "ai_run",
    "ai_memory_query",
    "ai_selftest",
    "ai_intent",
    "retrieval",
    "retention",
    "reflection",
    "memory query",
    "memory retrieval",
    "project",
    "canonical",
    "current state",
    "recent change",
    "what changed",
    "bottleneck",
    "next step",
    "next steps",
    "tests we use",
    "selftest",
]

GENERIC_DRIFT_PATTERNS = [
    r"\bdynamic nature\b",
    r"\bcontextual relevance\b",
    r"\bnlp capabilities\b",
    r"\buser interface enhancements\b",
    r"\bconversation history tracking\b",
    r"\btest_ai\.py\b",
    r"\bnlp_module\.py\b",
    r"\bvoice interface\b",
]


def load_router_profiles():
    return load_json(ROUTER_CONFIG, {})


def ask_ollama(model: str, prompt: str) -> str:
    proc = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        raise RuntimeError(err or f"ollama run failed with code {proc.returncode}")
    return (proc.stdout or "").strip()


def parse_manual_override(text: str) -> tuple[str | None, str]:
    m = re.match(r"^\s*@([A-Za-z0-9_-]+)\s+(.*)$", text.strip(), flags=re.S)
    if not m:
        return None, text
    profile = m.group(1).strip().lower()
    rest = m.group(2).strip()
    return profile, rest


def build_classifier_text_for_dry_run(text: str) -> str:
    stripped = text.lstrip()
    lowered = stripped.lower()

    for prefix in ("dry run ", "dry-run ", "preview only ", "simulate "):
        if lowered.startswith(prefix):
            return stripped[len(prefix):].lstrip()

    return text


def is_high_risk_command_like_text(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    if not normalized:
        return False

    command_start_patterns = [
        r"^(sudo|pkexec|doas)\b",
        r"^rm\s+-rf\b",
        r"^(mkfs|dd|chmod|chown|systemctl|reboot|shutdown|poweroff)\b",
    ]

    return any(re.search(pattern, normalized) for pattern in command_start_patterns)


def run_safe_action(text: str) -> tuple[bool, str]:
    normalized = normalize_action_text(text)

    proc = subprocess.run(
        [sys.executable, str(AI_EXEC_PATH), normalized],
        text=True,
        capture_output=True,
        check=False,
    )

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    if proc.returncode == 0:
        return True, stdout

    return False, stdout or stderr or "action execution failed"


def run_action_chain(
    steps: list[str],
    *,
    route_decision=None,
    policy_decision=None,
    action_contract=None,
) -> tuple[bool, list[dict], str]:
    if not steps:
        return False, [], "empty_action_chain"

    if len(steps) > MAX_CHAIN_STEPS:
        return False, [], f"too_many_steps: {len(steps)} > {MAX_CHAIN_STEPS}"

    results = []

    for index, step in enumerate(steps, start=1):
        ok, result = run_safe_action(step)
        item = {
            "step": index,
            "request": step,
            "ok": ok,
            "result": result,
        }
        results.append(item)

        log_memory(
            "actions" if ok else "failures",
            f"chain_step_{'ok' if ok else 'failed'}: {step}",
            {
                "assistant_name": ASSISTANT_NAME,
                "step": index,
                "total_steps": len(steps),
                "result": result,
                "route_decision": decision_to_log_meta(route_decision) if route_decision else None,
                "policy_decision": policy_to_log_meta(policy_decision) if policy_decision else None,
                "action_contract": action_contract_to_log_meta(action_contract) if action_contract else None,
            },
        )

        if not ok:
            summary = {
                "ok": False,
                "assistant": ASSISTANT_NAME,
                "failed_at_step": index,
                "steps": results,
            }
            return False, results, json.dumps(summary, ensure_ascii=False)

    summary = {
        "ok": True,
        "assistant": ASSISTANT_NAME,
        "steps": results,
    }
    return True, results, json.dumps(summary, ensure_ascii=False)




PROJECT_STATE_DIRECT_PATTERNS = [
    r"\bwhat changed\b",
    r"\bwhat did we change\b",
    r"\brecent changes\b",
    r"\bcurrent state\b",
    r"\bproject state\b",
    r"\bstatus of (the )?project\b",
    r"\bwhat happened\b",
    r"\bbottleneck\b",
    r"\btodo\b",
    r"\bnext steps\b",
    r"\bwhat should we improve next\b",
    r"\btests we use\b",
]
PROJECT_STATE_COMPONENT_HINTS = [
    "retention",
    "reflection",
    "retrieval",
    "workflow",
    "routing",
    "memory query",
    "memory retrieval",
    "memory retention",
    "project",
    "bond",
    "archive",
    "router",
    "ai_run",
    "ai_memory_query",
    "ai_selftest",
]
PROJECT_STATE_STATE_HINTS = [
    "change",
    "changed",
    "current",
    "status",
    "next",
    "why",
    "what happened",
    "bottleneck",
    "todo",
    "verify",
    "mismatch",
    "improve",
    "tests",
]



def profile_system_prompt(profile_cfg: dict) -> str:
    if not isinstance(profile_cfg, dict):
        return ""

    for key in ("system_prompt", "system", "prompt"):
        value = profile_cfg.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def load_system_summary() -> str:
    if not SYSTEM_SUMMARY.exists():
        return ""
    return SYSTEM_SUMMARY.read_text(encoding="utf-8", errors="ignore").strip()


def load_active_context_fallback(limit_lines: int = ACTIVE_CONTEXT_FALLBACK_LINES) -> str:
    path = FILES["active_context"]
    if not path.exists():
        return ""

    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        return ""

    lines = text.splitlines()
    if len(lines) <= limit_lines:
        return text

    return "\n".join(lines[:limit_lines]).strip()


def _matches_any_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.I) for pattern in patterns)


def _contains_any_phrase(text: str, phrases: list[str]) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in phrases)


def _count_phrase_hits(text: str, phrases: list[str]) -> int:
    lower = text.lower()
    return sum(1 for phrase in phrases if phrase in lower)


def is_project_state_query(user_text: str) -> bool:
    t = user_text.strip().lower()

    if _matches_any_pattern(t, PROJECT_STATE_DIRECT_PATTERNS):
        return True

    if _contains_any_phrase(t, ["ai_run", "ai_memory_query", "ai_selftest", "ai_intent", "bond"]):
        return True

    component_hits = _count_phrase_hits(t, PROJECT_STATE_COMPONENT_HINTS)
    state_hits = _count_phrase_hits(t, PROJECT_STATE_STATE_HINTS)

    return component_hits >= 1 and state_hits >= 1


def is_project_specific_query(user_text: str) -> bool:
    t = user_text.strip().lower()
    if is_project_state_query(t):
        return True
    return _contains_any_phrase(t, PROJECT_SPECIFIC_HINTS)


def is_recent_change_query(user_text: str) -> bool:
    return _matches_any_pattern(user_text.strip().lower(), RECENT_CHANGE_PATTERNS)


def is_next_step_query(user_text: str) -> bool:
    return _matches_any_pattern(user_text.strip().lower(), NEXT_STEP_PATTERNS)


def is_archive_policy_query(user_text: str) -> bool:
    return _matches_any_pattern(user_text.strip().lower(), ARCHIVE_POLICY_PATTERNS)


def summarize_memory_strength(memory_result: dict) -> dict:
    stats = memory_result.get("stats", {}) if isinstance(memory_result, dict) else {}
    hits = memory_result.get("hits", []) if isinstance(memory_result, dict) else []

    fact_hits = 0
    log_hits = 0
    archive_hits = 0
    changelog_hits = 0

    for item in hits:
        st = item.get("source_type")
        if st == "fact":
            fact_hits += 1
        elif st == "log":
            log_hits += 1
        elif st == "archive":
            archive_hits += 1
        elif st == "changelog":
            changelog_hits += 1

    strong = (fact_hits >= 1) or (log_hits >= 2) or (changelog_hits >= 2)
    moderate = strong or (log_hits >= 1) or (archive_hits >= 1) or (changelog_hits >= 1)

    return {
        "strong": strong,
        "moderate": moderate,
        "fact_hits": fact_hits,
        "log_hits": log_hits,
        "archive_hits": archive_hits,
        "changelog_hits": changelog_hits,
        "returned_hits": stats.get("returned_hits", len(hits)),
    }


def build_memory_context_for_request(user_text: str) -> tuple[str, dict]:
    if query_memory is None:
        fallback = load_active_context_fallback()
        return fallback, {
            "mode": "fallback_only",
            "stats": {"reason": "memory_query_import_failed"},
            "hits": [],
        }

    try:
        result = query_memory(user_text, max_items=MEMORY_QUERY_MAX_ITEMS)
        context = (result.get("context") or "").strip()
        if context:
            return context, result

        fallback = load_active_context_fallback()
        return fallback, {
            "mode": result.get("mode", "general"),
            "stats": {
                **(result.get("stats") or {}),
                "fallback_used": True,
                "reason": "empty_memory_hits",
            },
            "hits": result.get("hits", []),
        }
    except Exception as e:
        fallback = load_active_context_fallback()
        return fallback, {
            "mode": "fallback_only",
            "stats": {"reason": f"memory_query_error: {e}"},
            "hits": [],
        }


def _shorten(text: str, limit: int = 220) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _hit_timestamp(hit: dict) -> str:
    for key in ("updated_at", "ts"):
        value = str(hit.get(key) or "").strip()
        if value:
            return value
    return ""


def _hit_line(hit: dict) -> str:
    st = hit.get("source_type")
    if st == "fact":
        bucket = hit.get("bucket", "fact")
        key = hit.get("key", "")
        value = hit.get("text", "")
        return f"fact {bucket}.{key}: {_shorten(value)}"
    if st == "changelog":
        text = hit.get("text", "")
        files = hit.get("files", []) or []
        if files:
            return f"changelog: {_shorten(text)} | files: {', '.join(files[:3])}"
        return f"changelog: {_shorten(text)}"
    if st == "log":
        kind = hit.get("kind", "log")
        text = hit.get("text", "")
        return f"{kind}: {_shorten(text)}"
    if st == "archive":
        path = hit.get("path", "")
        return f"archive: {_shorten(path)}"
    return _shorten(hit.get("text", ""))


def _top_hits(memory_result: dict, limit: int = 3, prefer: tuple[str, ...] | None = None) -> list[dict]:
    hits = memory_result.get("hits", []) if isinstance(memory_result, dict) else []
    ordered = list(hits)
    if prefer:
        rank = {name: idx for idx, name in enumerate(prefer)}
        ordered = sorted(
            ordered,
            key=lambda item: (rank.get(item.get("source_type"), 999), -float(item.get("score", 0.0))),
        )
    return ordered[:limit]


def _direct_recent_change_hits(user_text: str, limit: int = 5) -> list[dict]:
    if not CHANGELOG_PATH.exists():
        return []

    query_tokens = set(re.findall(r"[a-zA-Z0-9_./-]+", user_text.lower()))
    noise = {
        "what", "changed", "most", "recent", "recently", "latest", "in", "the", "of", "to", "bond", "s",
        "behavior", "did", "we", "our", "is", "was",
    }
    query_tokens = {tok for tok in query_tokens if tok not in noise}
    if not query_tokens:
        query_tokens = {"retrieval", "memory"}

    entries = tail_jsonl(CHANGELOG_PATH, limit=RECENT_CHANGE_DIRECT_LIMIT)
    scored = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        message = " ".join(str(entry.get(key, "")) for key in ("message", "summary", "change_kind", "diff_preview")).lower()
        files = " ".join(str(x) for x in entry.get("files", [])).lower()
        haystack = f"{message} {files}"
        overlap = sum(1 for tok in query_tokens if tok in haystack)
        if overlap <= 0:
            continue
        ts = str(entry.get("ts", ""))
        scored.append((overlap, ts, entry))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    out = []
    for _, _, entry in scored[:limit]:
        out.append(
            {
                "source_type": "changelog",
                "ts": str(entry.get("ts", "")),
                "text": str(entry.get("message", "") or entry.get("summary", "")).strip(),
                "files": [str(x) for x in entry.get("files", [])],
                "change_kind": str(entry.get("change_kind", "")).strip(),
            }
        )
    return out


def _dedupe_recent_hits(hits: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for hit in hits:
        label = _hit_line(hit)
        norm = re.sub(r"\s+", " ", label.strip().lower())
        norm = re.sub(r"^changelog:\s*", "", norm)
        if norm in seen:
            continue
        seen.add(norm)
        deduped.append(hit)
    return deduped


def build_archive_policy_answer() -> str:
    return (
        "We avoid using the archive as automatic current truth because archive snapshots are history and comparison material, not the live verified state.\n\n"
        "Current verified behavior, latest applied files, and passing tests outrank archive/history. The archive is still useful for diffing, recovery, and tracing change history, but it should not silently override current live truth."
    )


def build_next_step_answer() -> str:
    return (
        "The next improvement should be grounded project-aware answering in ai_run.py, not new features.\n\n"
        "Priority order:\n"
        "1. Keep Bond anchored to project memory for Bond/project questions instead of drifting into generic AI-consultant answers.\n"
        "2. Keep using deterministic/script-first paths where possible.\n"
        "3. Expand behavior audits for project-state, recent-change, and next-step prompts before adding anything like voice, UI, applet, packaging, or embeddings."
    )


def build_recent_change_answer(user_text: str, memory_result: dict) -> str | None:
    direct_hits = _direct_recent_change_hits(user_text, limit=5)
    hits = direct_hits or _top_hits(memory_result, limit=5, prefer=("changelog", "fact", "log", "archive"))
    deduped = _dedupe_recent_hits(hits)

    if not deduped:
        return None

    lines = []
    for hit in deduped[:3]:
        ts = _hit_timestamp(hit)
        label = _hit_line(hit)
        if ts:
            lines.append(f"- {ts}: {label}")
        else:
            lines.append(f"- {label}")

    summary_bits = []
    lowered = user_text.lower()
    labels = " ".join(_hit_line(hit).lower() for hit in deduped[:3])

    if "retrieval" in lowered or "memory retrieval" in lowered:
        if "confirmed current facts outrank changelog" in labels or "fact-first current-state retrieval" in labels:
            summary_bits.append(
                "Bond now treats confirmed current facts as higher-priority than changelog, logs, and archive when answering current-state questions."
            )
        if "selftests" in labels:
            summary_bits.append(
                "The memory query selftests were also extended to verify fact-first current-state retrieval and archive demotion on non-history queries."
            )

    if summary_bits:
        return "\n\n".join([
            " ".join(summary_bits),
            "Most recent relevant grounded changes:\n" + "\n".join(lines),
        ])

    return "Most recent relevant changes I can ground from memory:\n" + "\n".join(lines)


def build_grounded_project_fallback(user_text: str, memory_result: dict) -> str:
    hits = _top_hits(memory_result, limit=3, prefer=("fact", "changelog", "log", "archive"))
    if hits:
        lines = [f"- {_hit_line(hit)}" for hit in hits]
        return (
            "I do not have enough strong project memory to answer that confidently without risking generic filler. "
            "Here is the closest grounded context I do have:\n" + "\n".join(lines)
        )
    return (
        "I do not have enough grounded project memory to answer that safely. "
        "I would rather say that directly than fill the gap with generic assistant talk."
    )


def maybe_build_direct_project_answer(user_text: str, memory_result: dict) -> str | None:
    t = user_text.strip().lower()
    strength = summarize_memory_strength(memory_result)

    if is_archive_policy_query(t):
        return build_archive_policy_answer()

    if is_next_step_query(t):
        return build_next_step_answer()

    if is_recent_change_query(t):
        recent = build_recent_change_answer(user_text, memory_result)
        if recent:
            return recent
        return build_grounded_project_fallback(user_text, memory_result)

    if is_project_specific_query(t) and not strength["moderate"]:
        return build_grounded_project_fallback(user_text, memory_result)

    return None


def build_answer_protocol(user_text: str, memory_result: dict) -> str:
    strength = summarize_memory_strength(memory_result)
    project_state = is_project_state_query(user_text)
    project_specific = is_project_specific_query(user_text)

    protocol = [
        "ANSWER PROTOCOL",
        "- Use the SYSTEM SUMMARY and RELEVANT MEMORY as the primary project-specific sources.",
        "- Prefer retrieved facts and logs over generic best practices.",
        "- Never invent file paths, snapshot ids, timestamps, archive entries, timers, jobs, services, or scripts.",
        "- Never claim a project change happened unless it is supported by the provided memory context.",
        "- If the request asks about Bond, project state, recent changes, next steps, tests, bottlenecks, or TODOs, stay tightly anchored to named files/modules and retrieved memory.",
        "- For project-specific questions, if the retrieved memory is not enough, say that directly. Do not fill gaps with generic assistant advice.",
        "- Do not output generic consultant filler such as abstract NLP upgrades, vague UI ideas, sample modules, or imaginary test files unless the retrieved memory clearly supports them.",
        "- Do not propose voice, Cinnamon applet, packaging, daemon mode, embeddings, or broad desktop integration unless the user explicitly asks for them.",
        "- For testing requests, prefer concrete tests against existing files/modules over generic sample scripts.",
    ]

    if project_specific:
        protocol.append("- This is a Bond/project-specific request. Stay inside Bond/project reality and its known files and priorities.")

    if project_state and not strength["strong"]:
        protocol.append("- Memory evidence is weak for this project-state request. Say that directly and avoid pretending you know more than the retrieved context shows.")
    elif project_state and strength["moderate"]:
        protocol.append("- Memory evidence is partial. Answer with what is supported, then explicitly separate any uncertainty.")
    elif project_state and strength["strong"]:
        protocol.append("- Memory evidence is strong enough to answer concretely from retrieved context. Lead with the concrete retrieved items first.")

    protocol.append("- If relevant memory is missing, say what is missing instead of filling the gap with speculation.")
    protocol.append("- Keep the answer practical and specific. Use short lists only when they improve clarity.")

    return "\n".join(protocol)


def build_model_prompt(
    profile_cfg: dict,
    user_text: str,
    memory_context: str,
    memory_result: dict,
    route_decision=None,
    policy_decision=None,
    action_contract=None,
) -> str:
    if memory_result is None:
        memory_result = {}

    system_summary = load_system_summary()
    role_prompt = profile_system_prompt(profile_cfg)
    answer_protocol = build_answer_protocol(user_text, memory_result)

    if route_decision is not None:
        routing_context = json.dumps(decision_to_log_meta(route_decision), ensure_ascii=False, indent=2)
    else:
        routing_context = "(manual profile override or unavailable)"

    if policy_decision is not None:
        policy_context = json.dumps(policy_to_log_meta(policy_decision), ensure_ascii=False, indent=2)
    else:
        policy_context = "(unavailable)"

    if action_contract is not None:
        action_contract_context = json.dumps(action_contract_to_log_meta(action_contract), ensure_ascii=False, indent=2)
    else:
        action_contract_context = "(unavailable)"

    return f"""
You are an internal local AI worker operating under the single user-facing assistant identity '{ASSISTANT_NAME}'.

IDENTITY RULES
- Never reveal internal worker names, route names, profile ids, or model names unless the user explicitly asks about internal architecture.
- The visible assistant name is always '{ASSISTANT_NAME}'.

PROFILE DIRECTIVE
{role_prompt or "You are a clear and practical assistant. Give grounded answers without unnecessary verbosity."}

PROJECT PRIORITIES
{PROJECT_PRIORITY_HINTS}

ROUTING CONTEXT
{routing_context}

POLICY CONTEXT
{policy_context}

ACTION CONTRACT CONTEXT
{action_contract_context}

{answer_protocol}

SYSTEM SUMMARY
{system_summary or "(none)"}

RELEVANT MEMORY
{memory_context or "(none)"}

USER REQUEST
{user_text}
""".strip()


def looks_like_generic_drift(reply: str) -> bool:
    text = reply.strip().lower()
    if not text:
        return False
    return _matches_any_pattern(text, GENERIC_DRIFT_PATTERNS)


def main():
    ensure_memory_dirs()
    build_active_context()

    if len(sys.argv) < 2:
        print("usage: ai_run.py <request>")
        raise SystemExit(1)

    raw_text = " ".join(sys.argv[1:]).strip()
    if not raw_text:
        print("empty request")
        raise SystemExit(1)

    confirmation_granted = False
    confirmation_token = parse_confirmation_request(raw_text)
    if confirmation_token:
        ok, pending, reason = consume_pending_confirmation(confirmation_token)
        if not ok or pending is None:
            log_memory(
                "failures",
                f"confirmation_token_{reason}: {confirmation_token}",
                {
                    "assistant_name": ASSISTANT_NAME,
                    "token": confirmation_token,
                    "error": reason,
                },
            )
            build_active_context()
            print(
                json.dumps(
                    {
                        "ok": False,
                        "assistant": ASSISTANT_NAME,
                        "error": reason,
                        "detail": "Confirmation token validation failed.",
                        "requires_confirmation": True,
                    },
                    ensure_ascii=False,
                )
            )
            raise SystemExit(5)

        original_text = str(pending.get("original_text", "")).strip()
        if not original_text:
            log_memory(
                "failures",
                f"confirmation_token_invalid_payload: {confirmation_token}",
                {
                    "assistant_name": ASSISTANT_NAME,
                    "token": confirmation_token,
                    "error": "confirmation_invalid",
                },
            )
            build_active_context()
            print(
                json.dumps(
                    {
                        "ok": False,
                        "assistant": ASSISTANT_NAME,
                        "error": "confirmation_invalid",
                        "detail": "Confirmation payload is invalid.",
                        "requires_confirmation": True,
                    },
                    ensure_ascii=False,
                )
            )
            raise SystemExit(5)

        raw_text = original_text
        confirmation_granted = True
        log_memory(
            "events",
            f"confirmation_token_consumed: {confirmation_token}",
            {
                "assistant_name": ASSISTANT_NAME,
                "token": confirmation_token,
                "original_text": original_text,
            },
        )

    override_profile, text = parse_manual_override(raw_text)
    profiles = load_router_profiles()

    route_decision = route_request(text)

    classifier_text = build_classifier_text_for_dry_run(text)
    gatekeeper_result, chain_steps = classify_request(classifier_text)
    if gatekeeper_result in {"unknown", "pure_question"} and route_decision.risk_level == "high":
        if is_high_risk_command_like_text(text):
            gatekeeper_result = "pure_action"
            chain_steps = None

    parse_contract = build_parse_contract(classifier_text, gatekeeper_result, chain_steps)
    parse_contract_meta = parse_contract_to_log_meta(parse_contract)

    high_risk_confirmation_candidate = (
        gatekeeper_result == "pure_action"
        and route_decision.risk_level == "high"
        and is_high_risk_command_like_text(text)
    )

    if (
        parse_contract.status in {STATUS_UNPARSED_ACTION, STATUS_PARTIAL_ACTION_CHAIN}
        and not high_risk_confirmation_candidate
    ):
        log_memory(
            "failures",
            f"action_not_parsed: {text}",
            {
                "assistant_name": ASSISTANT_NAME,
                "route_decision": decision_to_log_meta(route_decision),
                "parse_contract": parse_contract_meta,
                "confirmation_granted": confirmation_granted,
            },
        )
        build_active_context()
        print(json.dumps(build_action_not_parsed_response(parse_contract, ASSISTANT_NAME), ensure_ascii=False))
        raise SystemExit(3)

    policy_decision = evaluate_request_policy(
        text,
        gatekeeper_result,
        chain_steps,
        route_decision,
        override_profile=override_profile,
    )
    action_contract = build_action_contract(
        text,
        policy_decision,
        route_decision,
        confirmation_granted=confirmation_granted,
    )

    if action_contract.mode == ACTION_CONFIRM_REQUIRED:
        pending = create_pending_confirmation(
            original_text=text,
            risk_level=action_contract.risk_level,
            action_steps=action_contract.action_steps,
            reason=action_contract.reason,
        )
        log_memory(
            "failures",
            f"action_confirmation_required: {text}",
            {
                "assistant_name": ASSISTANT_NAME,
                "route_decision": decision_to_log_meta(route_decision),
                "policy_decision": policy_to_log_meta(policy_decision),
                "action_contract": action_contract_to_log_meta(action_contract),
                   "parse_contract": parse_contract_meta,
            },
        )
        log_memory(
            "events",
            f"confirmation_token_created: {text}",
            {
                "assistant_name": ASSISTANT_NAME,
                "token": pending.get("token"),
                "expires_at": pending.get("expires_at"),
                "expires_in_seconds": pending.get("expires_in_seconds"),
                "risk_level": action_contract.risk_level,
                "action_steps": action_contract.action_steps,
            },
        )
        build_active_context()
        response = build_confirmation_required_response(action_contract, ASSISTANT_NAME)
        response["confirmation_token"] = pending.get("token")
        response["expires_at"] = pending.get("expires_at")
        response["expires_in_seconds"] = pending.get("expires_in_seconds")
        response["confirm_command"] = f"confirm {pending.get('token')}"
        response["would_execute"] = False
        response["dry_run"] = False
        print(json.dumps(response, ensure_ascii=False))
        raise SystemExit(action_contract.exit_code)

    if action_contract.mode == ACTION_REJECT:
        if action_contract.reason == CONTRACT_REASON_CONFIRMED_ACTION_NO_EXECUTABLE_STEPS:
            log_memory(
                "failures",
                f"confirmed_action_no_executable_steps: {text}",
                {
                    "assistant_name": ASSISTANT_NAME,
                    "route_decision": decision_to_log_meta(route_decision),
                    "policy_decision": policy_to_log_meta(policy_decision),
                    "action_contract": action_contract_to_log_meta(action_contract),
                    "parse_contract": parse_contract_meta,
                },
            )
            build_active_context()
            print(
                json.dumps(
                    {
                        "ok": False,
                        "assistant": ASSISTANT_NAME,
                        "error": "confirmed_action_no_executable_steps",
                        "detail": "Confirmation was valid, but no safe executable action was parsed.",
                        "requires_confirmation": False,
                        "would_execute": False,
                        "dry_run": False,
                    },
                    ensure_ascii=False,
                )
            )
            raise SystemExit(action_contract.exit_code)

        log_memory(
            "failures",
            f"policy_rejected: {text}",
            {
                "assistant_name": ASSISTANT_NAME,
                "route_decision": decision_to_log_meta(route_decision),
                "policy_decision": policy_to_log_meta(policy_decision),
                "action_contract": action_contract_to_log_meta(action_contract),
                "parse_contract": parse_contract_meta,
            },
        )
        build_active_context()
        print(json.dumps(build_policy_rejection_response(policy_decision, ASSISTANT_NAME), ensure_ascii=False))
        raise SystemExit(action_contract.exit_code)

    if action_contract.mode == ACTION_DRY_RUN:
        log_memory(
            "events",
            f"action_dry_run: {text}",
            {
                "assistant_name": ASSISTANT_NAME,
                "route_decision": decision_to_log_meta(route_decision),
                "policy_decision": policy_to_log_meta(policy_decision),
                "action_contract": action_contract_to_log_meta(action_contract),
                "parse_contract": parse_contract_meta,
            },
        )
        build_active_context()
        print(json.dumps(build_dry_run_response(action_contract, ASSISTANT_NAME), ensure_ascii=False))
        return

    fact_spec = detect_fact_query(text)
    if fact_spec:
        answer = answer_fact_query(fact_spec, profiles)
        if answer is not None:
            log_memory(
                "chats",
                f"fact_answer: {text}",
                {
                    "answer": answer,
                    "fact_spec": fact_spec,
                    "assistant_name": ASSISTANT_NAME,
                    "route_decision": decision_to_log_meta(route_decision),
                    "policy_decision": policy_to_log_meta(policy_decision),
                    "action_contract": action_contract_to_log_meta(action_contract),
                    "parse_contract": parse_contract_meta,
                },
            )
            build_active_context()
            print(answer)
            return

    if action_contract.mode == ACTION_EXECUTE:
        if policy_decision.mode == POLICY_MODE_ACTION_CHAIN:
            ok, _, result = run_action_chain(
                policy_decision.action_steps,
                route_decision=route_decision,
                policy_decision=policy_decision,
                action_contract=action_contract,
            )
            build_active_context()
            print(result)
            if ok:
                return
            raise SystemExit(3)

        ok, result = run_safe_action(text)
        build_active_context()
        print(result)
        if ok:
            return
        raise SystemExit(3)

    if override_profile:
        chosen = override_profile
    else:
        chosen = route_decision.primary_agent

    profile_cfg = choose_profile_config(chosen, profiles)
    if profile_cfg is None:
        chosen = DEFAULT_PROFILE
        profile_cfg = choose_profile_config(chosen, profiles) or {}

    model = extract_model_from_profile(profile_cfg)
    memory_context, memory_result = build_memory_context_for_request(text)

    direct_answer = maybe_build_direct_project_answer(text, memory_result)
    if direct_answer:
        log_memory(
            "chats",
            f"direct_project_answer: {text}",
            {
                "profile": chosen,
                "model": model,
                "override": bool(override_profile),
                "assistant_name": ASSISTANT_NAME,
                "memory_mode": memory_result.get("mode"),
                "memory_stats": memory_result.get("stats", {}),
                "memory_strength": summarize_memory_strength(memory_result),
                "route_decision": decision_to_log_meta(route_decision) if route_decision else None,
                "policy_decision": policy_to_log_meta(policy_decision),
                "action_contract": action_contract_to_log_meta(action_contract) if action_contract else None,
            },
        )
        build_active_context()
        print(direct_answer)
        return

    prompt = build_model_prompt(
        profile_cfg,
        text,
        memory_context,
        memory_result,
        route_decision,
        policy_decision,
        action_contract,
    )

    try:
        reply = ask_ollama(model, prompt)
    except Exception as e:
        log_memory(
            "failures",
            f"model_run_failed: {text}",
            {
                "profile": chosen,
                "model": model,
                "error": str(e),
                "assistant_name": ASSISTANT_NAME,
                "memory_mode": memory_result.get("mode"),
                "memory_stats": memory_result.get("stats", {}),
                "route_decision": decision_to_log_meta(route_decision) if route_decision else None,
                "policy_decision": policy_to_log_meta(policy_decision),
                "action_contract": action_contract_to_log_meta(action_contract) if action_contract else None,
            },
        )
        build_active_context()
        print(f"model error: {e}")
        raise SystemExit(2)

    if is_project_specific_query(text) and looks_like_generic_drift(reply):
        reply = build_grounded_project_fallback(text, memory_result)

    log_memory(
        "chats",
        f"chat_route: {text}",
        {
            "profile": chosen,
            "model": model,
            "override": bool(override_profile),
            "router_config": str(ROUTER_CONFIG),
            "assistant_name": ASSISTANT_NAME,
            "memory_mode": memory_result.get("mode"),
            "memory_stats": memory_result.get("stats", {}),
            "memory_strength": summarize_memory_strength(memory_result),
            "route_decision": decision_to_log_meta(route_decision) if route_decision else None,
            "policy_decision": policy_to_log_meta(policy_decision),
            "action_contract": action_contract_to_log_meta(action_contract) if action_contract else None,
        },
    )
    build_active_context()

    print(reply)


if __name__ == "__main__":
    main()

