#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from ai_core import (
    FACT_BUCKETS,
    FILES,
    ensure_memory_dirs,
    get_changelog_path,
    load_fact_bucket,
    load_json,
    tail_jsonl,
)

CHANGELOG_PATH = get_changelog_path()

DEFAULT_MAX_ITEMS = 8
DEFAULT_RECENT_LOG_LIMIT = 200
DEFAULT_CHANGELOG_LIMIT = 80
DEFAULT_ARCHIVE_PREVIEW_LIMIT = 20

FACT_BASE_WEIGHT = 100.0
CHANGELOG_BASE_WEIGHT = 78.0
LOG_BASE_WEIGHT = 58.0
REFLECTION_BASE_WEIGHT = 50.0
ARCHIVE_BASE_WEIGHT = 14.0

FACT_TRUTH_BOOST = 14.0
CHANGELOG_WITH_FACT_PENALTY = 12.0
LOG_WITH_FACT_PENALTY = 10.0
ARCHIVE_NON_HISTORY_PENALTY = 18.0

MODE_FACT = "fact_lookup"
MODE_WORKFLOW = "workflow_lookup"
MODE_RECENT = "recent_context"
MODE_TROUBLE = "troubleshooting"
MODE_IDENTITY = "identity_preferences"
MODE_HISTORY = "history_lookup"
MODE_GENERAL = "general"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "for", "from", "how",
    "i", "in", "is", "it", "me", "my", "of", "on", "or", "the", "to", "we", "what",
    "when", "where", "which", "who", "why", "with", "you", "your",
    "am", "was", "were", "have", "has", "had", "tell", "show", "find",
    "μου", "το", "τη", "την", "τι", "τις", "τα", "των", "στο", "στη", "στην",
    "σε", "και", "να", "για", "πως", "πώς", "που", "πού", "ποιο", "ποια", "ποιον",
    "ποιοι", "ποιες", "με", "απο", "από", "εχω", "έχω", "ειναι", "είναι",
    "δειξε", "δείξε", "πες", "βρες", "θελω", "θέλω",
    "recent", "current", "latest",
}

TROUBLE_HINTS = {
    "fail", "failed", "failure", "broken", "broke", "error", "issue", "problem",
    "timeout", "crash", "debug", "debugging", "fix", "stuck", "skip", "skipped",
    "prune", "rotation", "reflect", "retention",
    "σφαλμα", "σφάλμα", "λαθος", "λάθος", "προβλημα", "πρόβλημα", "κολλησε",
    "έσπασε", "σπασμενο", "σπασμένο", "διορθωσε", "διόρθωσε",
}

RECENT_HINTS = {
    "recent", "latest", "last", "current", "now", "today", "yesterday",
    "προσφατο", "πρόσφατο", "τελευταιο", "τελευταίο", "τωρα", "τώρα", "σημερα", "σήμερα",
    "χθες", "τωρινο", "τωρινό",
}

HISTORY_HINTS = {
    "before", "older", "history", "archive", "archived", "past", "previous",
    "πριν", "παλιο", "παλιό", "ιστορικο", "ιστορικό", "αρχειο", "αρχείο", "παλιοτερα", "παλιότερα",
}

WORKFLOW_HINTS = {
    "workflow", "process", "routine", "pipeline", "policy", "backup", "retention",
    "reflection", "rotate", "rotation", "changelog", "test", "selftest", "gate",
    "flow", "steps", "milestone", "phase", "retrieval", "ranking", "memory", "query",
    "ροη", "ροή", "διαδικασια", "διαδικασία", "πολιτικη", "πολιτική",
}

IDENTITY_HINTS = {
    "prefer", "preference", "editor", "browser", "terminal", "mail", "file manager",
    "assistant name", "bond", "alias", "path", "second drive", "archive root",
    "προτιμηση", "προτίμηση", "ονομα", "όνομα", "διαδρομη", "διαδρομή", "δισκος", "δίσκος",
}

PROJECT_CHANGE_HINTS = {
    "change", "changed", "recently", "retention", "reflect", "reflection", "rotate",
    "rotation", "retrieval", "query", "selftest", "changelog",
    "αλλαξαμε", "άλλαξαμε", "αλλαγη", "αλλαγή", "προσφατα", "πρόσφατα",
}

EXPLICIT_CURRENT_STATE_HINTS = {
    "current", "currently", "now", "latest", "actual", "real", "live", "confirmed",
    "current_state", "current-state", "state", "truth",
    "τωρα", "τώρα", "σημερα", "σήμερα", "τρεχον", "τρέχον", "τωρινο", "τωρινό",
    "πραγματικο", "πραγματικό", "επιβεβαιωμενο", "επιβεβαιωμένο", "κατασταση", "κατάσταση",
}


def _parse_ts(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _iso_or_blank(value: str | None) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _compact_text(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except Exception:
            return str(value)
    if value is None:
        return ""
    return str(value).strip()


def _tokenize(text: str) -> list[str]:
    if not isinstance(text, str):
        return []
    raw = re.findall(r"[A-Za-z0-9_./:-]+|[Α-Ωα-ωάέήίόύώϊϋΐΰ0-9_./:-]+", text.lower())
    tokens = []
    for token in raw:
        t = token.strip("._-:/")
        if len(t) < 2:
            continue
        if t in STOPWORDS:
            continue
        tokens.append(t)
    return tokens


def _unique_keep_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def infer_query_mode(query: str, tokens: list[str] | None = None) -> str:
    tokens = tokens or _tokenize(query)
    token_set = set(tokens)
    q = query.lower()

    if token_set & TROUBLE_HINTS:
        return MODE_TROUBLE
    if token_set & HISTORY_HINTS:
        return MODE_HISTORY
    if token_set & RECENT_HINTS:
        return MODE_RECENT
    if token_set & WORKFLOW_HINTS:
        return MODE_WORKFLOW
    if token_set & IDENTITY_HINTS or "bond" in q:
        return MODE_IDENTITY
    if any(word in q for word in ["what is", "where is", "which", "τι ", "που ", "ποιο"]):
        return MODE_FACT
    return MODE_GENERAL


def _overlap_score(query_tokens: list[str], haystack: str) -> tuple[float, list[str]]:
    if not haystack:
        return 0.0, []

    h = haystack.lower()
    matched = []
    score = 0.0

    for token in query_tokens:
        if token in h:
            matched.append(token)
            score += 1.0

    return score, matched


def _recency_bonus(ts_value: str, mode: str) -> float:
    dt = _parse_ts(ts_value)
    if dt is None:
        return 0.0

    age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
    if age_hours < 0:
        age_hours = 0.0

    if age_hours <= 6:
        bonus = 14.0
    elif age_hours <= 24:
        bonus = 11.0
    elif age_hours <= 72:
        bonus = 8.0
    elif age_hours <= 168:
        bonus = 4.0
    else:
        bonus = 1.0

    if mode == MODE_HISTORY:
        bonus *= 0.35
    elif mode in {MODE_RECENT, MODE_WORKFLOW}:
        bonus *= 1.25

    return bonus


def _fact_record(bucket: str, key: str, item) -> dict:
    if isinstance(item, dict) and "value" in item:
        value = item.get("value")
        updated_at = item.get("updated_at", "")
        source = item.get("source", "")
    else:
        value = item
        updated_at = ""
        source = ""

    return {
        "bucket": bucket,
        "key": key,
        "value": value,
        "updated_at": _iso_or_blank(updated_at),
        "source": _compact_text(source),
        "text": _compact_text(value),
    }


def _log_record(kind: str, item: dict) -> dict:
    meta = item.get("meta", {}) if isinstance(item.get("meta"), dict) else {}
    return {
        "kind": kind,
        "ts": _iso_or_blank(item.get("ts", "")),
        "message": _compact_text(item.get("message", "")),
        "meta": meta,
        "meta_text": _compact_text(meta),
    }


def _changelog_record(item: dict) -> dict:
    files = item.get("files", []) if isinstance(item.get("files"), list) else []
    msg = _compact_text(item.get("message", ""))
    ts = _iso_or_blank(item.get("ts", ""))
    change_kind = _compact_text(item.get("change_kind", ""))
    diff_preview = _compact_text(item.get("diff_preview", ""))

    return {
        "ts": ts,
        "message": msg,
        "files": [str(x) for x in files],
        "files_text": " ".join(str(x) for x in files),
        "change_kind": change_kind,
        "diff_preview": diff_preview,
    }


def _archive_entries(archive_map: dict) -> list[dict]:
    out = []
    if not isinstance(archive_map, dict):
        return out

    for key, value in archive_map.items():
        if isinstance(value, list):
            for path in value:
                out.append({"group": str(key), "path": _compact_text(path)})
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, list):
                    for path in sub_value:
                        out.append({"group": f"{key}.{sub_key}", "path": _compact_text(path)})
                else:
                    out.append({"group": f"{key}.{sub_key}", "path": _compact_text(sub_value)})
        else:
            out.append({"group": str(key), "path": _compact_text(value)})

    return out


def _source_weight_for_fact(bucket: str, key: str, mode: str) -> float:
    weight = FACT_BASE_WEIGHT

    if mode in {MODE_IDENTITY, MODE_FACT} and bucket in {"preferences", "environment", "aliases"}:
        weight += 12.0

    if mode == MODE_WORKFLOW and bucket == "workflows":
        weight += 16.0

    if key in {"editor", "browser", "terminal", "mail", "file_manager", "second_drive", "archive_root"}:
        weight += 8.0

    if key in {"retention", "reflection", "rotation", "memory", "retrieval"}:
        weight += 6.0

    return weight


def _source_weight_for_log(kind: str, mode: str) -> float:
    if kind == "actions":
        weight = LOG_BASE_WEIGHT
    elif kind == "failures":
        weight = LOG_BASE_WEIGHT - 2.0
    elif kind == "chats":
        weight = LOG_BASE_WEIGHT - 6.0
    else:
        weight = REFLECTION_BASE_WEIGHT

    if mode == MODE_TROUBLE and kind == "failures":
        weight += 18.0
    if mode == MODE_WORKFLOW and kind in {"reflections", "chats"}:
        weight += 8.0
    if mode == MODE_RECENT and kind in {"actions", "failures", "chats"}:
        weight += 5.0

    return weight


def _source_weight_for_changelog(mode: str) -> float:
    weight = CHANGELOG_BASE_WEIGHT
    if mode in {MODE_WORKFLOW, MODE_RECENT, MODE_HISTORY}:
        weight += 8.0
    return weight


def _source_weight_for_archive(mode: str) -> float:
    weight = ARCHIVE_BASE_WEIGHT
    if mode == MODE_HISTORY:
        weight += 16.0
    return weight


def _project_change_bonus(query_tokens: list[str], haystack: str) -> float:
    token_set = set(query_tokens)
    matched = token_set & PROJECT_CHANGE_HINTS
    if not matched:
        return 0.0

    bonus = 0.0
    h = haystack.lower()
    for token in matched:
        if token in h:
            bonus += 2.0

    if any(key in h for key in ["keep_log_archives", "keep_fact_snapshots", "archive_map", "ai_memory_query.py", "ai_run.py", "ai_intent.py", "ai_selftest.py"]):
        bonus += 3.0

    return bonus



def _wants_current_truth(query: str, query_tokens: list[str], mode: str) -> bool:
    token_set = set(query_tokens)
    if mode == MODE_HISTORY:
        return False
    if token_set & EXPLICIT_CURRENT_STATE_HINTS:
        return True

    q = query.lower()
    cues = [
        "what is", "what's", "where is", "which is", "current", "current state",
        "live path", "real path", "confirmed", "actual", "right now",
        "τι ειναι", "τι είναι", "που ειναι", "πού είναι", "ποιο ειναι", "ποιο είναι",
        "τρεχουσα κατασταση", "τρέχουσα κατάσταση", "πραγματικη κατασταση", "πραγματική κατάσταση",
    ]
    return any(cue in q for cue in cues)


def _apply_truth_priority(query: str, query_tokens: list[str], mode: str, hits: list[dict]) -> list[dict]:
    if not hits:
        return hits

    wants_current_truth = _wants_current_truth(query, query_tokens, mode)
    has_fact_hits = any(item.get("source_type") == "fact" for item in hits)

    adjusted = []
    for item in hits:
        st = item.get("source_type")
        adjusted_item = dict(item)
        score = float(item.get("score", 0.0))

        if st == "fact":
            if mode != MODE_HISTORY:
                score += FACT_TRUTH_BOOST
            if wants_current_truth:
                score += 8.0
        elif st == "changelog":
            if has_fact_hits and mode != MODE_HISTORY:
                score -= CHANGELOG_WITH_FACT_PENALTY
            if wants_current_truth:
                score -= 6.0
            if mode == MODE_WORKFLOW:
                score += 4.0
        elif st == "log":
            if has_fact_hits and mode in {MODE_FACT, MODE_IDENTITY, MODE_GENERAL, MODE_RECENT, MODE_WORKFLOW}:
                score -= LOG_WITH_FACT_PENALTY
            if wants_current_truth:
                score -= 5.0
            if mode == MODE_TROUBLE and item.get("kind") == "failures":
                score += 4.0
        elif st == "archive":
            if mode != MODE_HISTORY:
                score -= ARCHIVE_NON_HISTORY_PENALTY
            if wants_current_truth:
                score -= 8.0
            if mode == MODE_HISTORY:
                score += 6.0

        adjusted_item["score"] = round(score, 2)
        adjusted.append(adjusted_item)

    return sorted(adjusted, key=lambda x: x.get("score", 0.0), reverse=True)


def _score_fact(query: str, query_tokens: list[str], mode: str, record: dict) -> dict | None:
    haystack = " ".join([record["bucket"], record["key"], record["text"], record["source"]]).strip()
    overlap, matched = _overlap_score(query_tokens, haystack)

    phrase_bonus = 0.0
    q = query.lower()
    if record["key"].lower() in q:
        phrase_bonus += 12.0
    if record["bucket"].lower() in q:
        phrase_bonus += 6.0

    if overlap <= 0 and phrase_bonus <= 0:
        return None

    score = _source_weight_for_fact(record["bucket"], record["key"], mode)
    score += overlap * 8.0
    score += phrase_bonus
    score += _project_change_bonus(query_tokens, haystack)
    score += _recency_bonus(record["updated_at"], mode)

    return {
        "source_type": "fact",
        "bucket": record["bucket"],
        "key": record["key"],
        "score": round(score, 2),
        "matched_tokens": matched,
        "updated_at": record["updated_at"],
        "source": record["source"],
        "text": record["text"],
        "raw": record,
    }


def _score_log(query_tokens: list[str], mode: str, record: dict) -> dict | None:
    haystack = " ".join([record["kind"], record["message"], record["meta_text"]]).strip()
    overlap, matched = _overlap_score(query_tokens, haystack)
    if overlap <= 0:
        return None

    score = _source_weight_for_log(record["kind"], mode)
    score += overlap * 6.0
    score += _project_change_bonus(query_tokens, haystack)
    score += _recency_bonus(record["ts"], mode)

    if record["kind"] == "failures" and mode == MODE_TROUBLE:
        score += 8.0
    if record["kind"] == "actions" and mode in {MODE_WORKFLOW, MODE_RECENT}:
        score += 4.0

    return {
        "source_type": "log",
        "kind": record["kind"],
        "score": round(score, 2),
        "matched_tokens": matched,
        "ts": record["ts"],
        "text": record["message"],
        "meta": record["meta"],
        "raw": record,
    }


def _score_changelog(query_tokens: list[str], mode: str, record: dict) -> dict | None:
    haystack = " ".join(
        [
            record["message"],
            record["files_text"],
            record["change_kind"],
            record["diff_preview"],
        ]
    ).strip()

    overlap, matched = _overlap_score(query_tokens, haystack)
    if overlap <= 0:
        return None

    score = _source_weight_for_changelog(mode)
    score += overlap * 7.0
    score += _project_change_bonus(query_tokens, haystack)
    score += _recency_bonus(record["ts"], mode)

    if any(name in haystack.lower() for name in ["ai_memory_query.py", "ai_run.py", "ai_intent.py", "ai_selftest.py"]):
        score += 5.0

    return {
        "source_type": "changelog",
        "score": round(score, 2),
        "matched_tokens": matched,
        "ts": record["ts"],
        "text": record["message"],
        "files": record["files"],
        "change_kind": record["change_kind"],
        "raw": record,
    }


def _score_archive(query_tokens: list[str], mode: str, record: dict) -> dict | None:
    haystack = f"{record['group']} {record['path']}".strip()
    overlap, matched = _overlap_score(query_tokens, haystack)
    if overlap <= 0:
        return None

    score = _source_weight_for_archive(mode)
    score += overlap * 4.0

    return {
        "source_type": "archive",
        "group": record["group"],
        "score": round(score, 2),
        "matched_tokens": matched,
        "path": record["path"],
        "raw": record,
    }


def _dedupe_hits(hits: list[dict]) -> list[dict]:
    seen = set()
    out = []

    for item in sorted(hits, key=lambda x: x.get("score", 0.0), reverse=True):
        st = item.get("source_type")

        if st == "fact":
            key = ("fact", item.get("bucket"), item.get("key"))
        elif st == "log":
            key = ("log", item.get("kind"), item.get("ts"), item.get("text"))
        elif st == "changelog":
            key = ("changelog", item.get("ts"), item.get("text"))
        else:
            key = ("archive", item.get("group"), item.get("path"))

        if key in seen:
            continue
        seen.add(key)
        out.append(item)

    return out


def _trim_hits_by_type(hits: list[dict], max_items: int) -> list[dict]:
    out = []
    counts = {
        "fact": 0,
        "log": 0,
        "changelog": 0,
        "archive": 0,
    }

    fact_cap = max(4, (max_items + 1) // 2)
    log_cap = 2 if max_items <= 6 else 3
    changelog_cap = 2 if max_items <= 6 else 3
    archive_cap = 1 if max_items <= 8 else 2

    for item in hits:
        if len(out) >= max_items:
            break

        st = item["source_type"]

        if st == "fact" and counts["fact"] >= fact_cap:
            continue
        if st == "log" and counts["log"] >= log_cap:
            continue
        if st == "changelog" and counts["changelog"] >= changelog_cap:
            continue
        if st == "archive" and counts["archive"] >= archive_cap:
            continue

        counts[st] += 1
        out.append(item)

    return out


def _render_fact_hit(item: dict) -> str:
    suffix = []
    if item.get("updated_at"):
        suffix.append(f"updated={item['updated_at']}")
    if item.get("source"):
        suffix.append(f"source={item['source']}")
    tail = f" [{' | '.join(suffix)}]" if suffix else ""
    return f"- FACT {item['bucket']}.{item['key']} = {item['text']}{tail}"


def _render_log_hit(item: dict) -> str:
    prefix = item.get("kind", "log").upper()
    ts = item.get("ts", "")
    meta = item.get("meta") or {}
    meta_tail = ""
    if meta:
        meta_tail = f" | meta={json.dumps(meta, ensure_ascii=False, sort_keys=True)}"
    return f"- {prefix} {ts}: {item.get('text', '')}{meta_tail}"


def _render_changelog_hit(item: dict) -> str:
    files = item.get("files", []) or []
    file_tail = f" | files={', '.join(files)}" if files else ""
    kind_tail = f" | kind={item.get('change_kind', '')}" if item.get("change_kind") else ""
    return f"- CHANGE {item.get('ts', '')}: {item.get('text', '')}{kind_tail}{file_tail}"


def _render_archive_hit(item: dict) -> str:
    return f"- ARCHIVE {item.get('group', '')}: {item.get('path', '')}"


def _hit_brief(item: dict) -> str:
    st = item.get("source_type")
    if st == "fact":
        return f"{item.get('bucket')}.{item.get('key')} = {item.get('text')}"
    if st == "changelog":
        files = item.get("files", []) or []
        if files:
            return f"{item.get('text')} (files: {', '.join(files)})"
        return item.get("text", "")
    if st == "log":
        return item.get("text", "")
    return item.get("path", "")


def build_evidence_summary(query: str, mode: str, hits: list[dict]) -> dict:
    confirmed_current = []
    recent_changes = []
    relevant_logs = []
    archive_refs = []
    uncertainty = []

    for item in hits:
        st = item.get("source_type")
        brief = _hit_brief(item)

        if st == "fact" and len(confirmed_current) < 4:
            confirmed_current.append(brief)
        elif st == "changelog" and len(recent_changes) < 3:
            recent_changes.append(brief)
        elif st == "log" and len(relevant_logs) < 3:
            relevant_logs.append(brief)
        elif st == "archive" and len(archive_refs) < 2:
            archive_refs.append(brief)

    if not confirmed_current:
        uncertainty.append("No strong structured fact hit for confirmed current state.")
    if mode in {MODE_WORKFLOW, MODE_RECENT, MODE_GENERAL} and not recent_changes:
        uncertainty.append("No strong changelog hit found for recent implementation changes.")
    if not relevant_logs:
        uncertainty.append("No strong recent log/reflection hit found.")
    if archive_refs and mode != MODE_HISTORY:
        uncertainty.append("Archive references are historical clues, not automatic current truth.")

    return {
        "confirmed_current": confirmed_current,
        "known_facts": confirmed_current,
        "recent_changes": recent_changes,
        "relevant_logs": relevant_logs,
        "archive_refs": archive_refs,
        "uncertainty": uncertainty,
    }


def render_memory_context(result: dict) -> str:
    lines = []
    lines.append("MEMORY QUERY CONTEXT")
    lines.append(f"- mode: {result.get('mode', MODE_GENERAL)}")
    lines.append(f"- query: {result.get('query', '')}")
    lines.append(f"- tokens: {', '.join(result.get('tokens', [])) or 'none'}")
    lines.append("")

    summary = result.get("evidence_summary", {})

    lines.append("CONFIRMED CURRENT")
    facts = summary.get("confirmed_current", summary.get("known_facts", []))
    if facts:
        for item in facts:
            lines.append(f"- {item}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("RECENT CHANGES")
    changes = summary.get("recent_changes", [])
    if changes:
        for item in changes:
            lines.append(f"- {item}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("RELEVANT LOGS")
    logs = summary.get("relevant_logs", [])
    if logs:
        for item in logs:
            lines.append(f"- {item}")
    else:
        lines.append("- none")

    archive_refs = summary.get("archive_refs", [])
    if archive_refs:
        lines.append("")
        lines.append("ARCHIVE REFERENCES")
        for item in archive_refs:
            lines.append(f"- {item}")

    uncertainty = summary.get("uncertainty", [])
    if uncertainty:
        lines.append("")
        lines.append("UNCERTAINTY")
        for item in uncertainty:
            lines.append(f"- {item}")

    lines.append("")
    lines.append("MATCHES")
    hits = result.get("hits", [])
    if not hits:
        lines.append("- none")
    else:
        for item in hits:
            if item["source_type"] == "fact":
                lines.append(_render_fact_hit(item))
            elif item["source_type"] == "log":
                lines.append(_render_log_hit(item))
            elif item["source_type"] == "changelog":
                lines.append(_render_changelog_hit(item))
            else:
                lines.append(_render_archive_hit(item))

    return "\n".join(lines)


def query_memory(
    query: str,
    max_items: int = DEFAULT_MAX_ITEMS,
    recent_log_limit: int = DEFAULT_RECENT_LOG_LIMIT,
    changelog_limit: int = DEFAULT_CHANGELOG_LIMIT,
    archive_preview_limit: int = DEFAULT_ARCHIVE_PREVIEW_LIMIT,
) -> dict:
    ensure_memory_dirs()

    tokens = _unique_keep_order(_tokenize(query))
    mode = infer_query_mode(query, tokens)

    fact_hits = []
    for bucket in FACT_BUCKETS:
        data = load_fact_bucket(bucket)
        if not isinstance(data, dict):
            continue
        for key, item in data.items():
            record = _fact_record(bucket, str(key), item)
            scored = _score_fact(query, tokens, mode, record)
            if scored:
                fact_hits.append(scored)

    log_hits = []
    for kind in ("actions", "failures", "chats", "reflections"):
        entries = tail_jsonl(FILES[kind], recent_log_limit)
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            record = _log_record(kind, entry)
            scored = _score_log(tokens, mode, record)
            if scored:
                log_hits.append(scored)

    changelog_hits = []
    changelog_entries = tail_jsonl(CHANGELOG_PATH, changelog_limit) if CHANGELOG_PATH.exists() else []
    for entry in changelog_entries:
        if not isinstance(entry, dict):
            continue
        record = _changelog_record(entry)
        scored = _score_changelog(tokens, mode, record)
        if scored:
            changelog_hits.append(scored)

    archive_hits = []
    archive_map = load_json(FILES["archive_map"], {})
    archive_entries = _archive_entries(archive_map)[:archive_preview_limit]
    for entry in archive_entries:
        scored = _score_archive(tokens, mode, entry)
        if scored:
            archive_hits.append(scored)

    hits = _dedupe_hits(fact_hits + changelog_hits + log_hits + archive_hits)
    hits = _apply_truth_priority(query, tokens, mode, hits)
    hits = _trim_hits_by_type(hits, max_items)
    evidence_summary = build_evidence_summary(query, mode, hits)

    result = {
        "query": query,
        "mode": mode,
        "tokens": tokens,
        "stats": {
            "fact_hits": len(fact_hits),
            "changelog_hits": len(changelog_hits),
            "log_hits": len(log_hits),
            "archive_hits": len(archive_hits),
            "returned_hits": len(hits),
        },
        "hits": hits,
        "evidence_summary": evidence_summary,
    }
    result["context"] = render_memory_context(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Bond memory without modifying state")
    parser.add_argument("query", help="Query text used to retrieve relevant memory")
    parser.add_argument("--json", action="store_true", help="Print raw JSON result")
    parser.add_argument("--max-items", type=int, default=DEFAULT_MAX_ITEMS)
    parser.add_argument("--recent-log-limit", type=int, default=DEFAULT_RECENT_LOG_LIMIT)
    parser.add_argument("--changelog-limit", type=int, default=DEFAULT_CHANGELOG_LIMIT)
    parser.add_argument("--archive-preview-limit", type=int, default=DEFAULT_ARCHIVE_PREVIEW_LIMIT)
    args = parser.parse_args()

    result = query_memory(
        query=args.query,
        max_items=max(1, args.max_items),
        recent_log_limit=max(20, args.recent_log_limit),
        changelog_limit=max(10, args.changelog_limit),
        archive_preview_limit=max(1, args.archive_preview_limit),
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(result["context"])


if __name__ == "__main__":
    main()
