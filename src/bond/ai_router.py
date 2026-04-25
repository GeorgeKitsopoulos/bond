#!/usr/bin/env python3
"""
Deterministic structured routing substrate for Bond.

This module classifies user requests and selects specialist profiles.
It does NOT call Ollama, execute tools, read/write memory, or import ai_run/ai_exec.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Route constants
# ---------------------------------------------------------------------------

ROUTE_STUART = "stuart"
ROUTE_BOB = "bob"
ROUTE_POLLY = "polly"
ROUTE_NICK = "nick"
ROUTE_JAMES = "james"
ROUTE_LILY = "lily"
ROUTE_TERMINATOR = "terminator"

# Bob is dispatcher metadata, not a final answering worker.
FINAL_AGENT_ROUTES: set[str] = {
    "stuart",
    "polly",
    "nick",
    "james",
    "lily",
    "terminator",
}

# ---------------------------------------------------------------------------
# RouterDecision dataclass
# ---------------------------------------------------------------------------

@dataclass
class RouterDecision:
    original_text: str
    normalized_text: str
    intent: str
    primary_agent: str
    secondary_agents: list[str]
    requires_tools: bool
    risk_level: str
    confidence: float
    escalate: bool
    reason: str
    matched_signals: list[str]

    def to_dict(self) -> dict:
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "intent": self.intent,
            "primary_agent": self.primary_agent,
            "secondary_agents": self.secondary_agents,
            "requires_tools": self.requires_tools,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "escalate": self.escalate,
            "reason": self.reason,
            "matched_signals": self.matched_signals,
        }


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def normalize_for_route(text: str) -> str:
    """Lowercase, collapse whitespace, preserve Greek text, strip edges only."""
    lowered = text.lower()
    collapsed = re.sub(r"[ \t\r\f\v]+", " ", lowered)
    return collapsed.strip()


def contains_any(text: str, phrases: list[str]) -> bool:
    """Return True if text contains any of the given phrases (case-insensitive)."""
    t = text.lower()
    return any(phrase.lower() in t for phrase in phrases)


def matches_any(text: str, patterns: list[str]) -> bool:
    """Return True if text matches any pattern via re.search (re.I)."""
    return any(re.search(p, text, re.I) for p in patterns)


def count_hits(text: str, phrases: list[str]) -> int:
    """Count how many phrases appear in text (case-insensitive)."""
    t = text.lower()
    return sum(1 for phrase in phrases if phrase.lower() in t)


# ---------------------------------------------------------------------------
# Risk detection
# ---------------------------------------------------------------------------

_HIGH_RISK_PHRASES = [
    "sudo",
    "pkexec",
    "doas",
    "rm -rf",
    "mkfs",
    "dd if=",
    "dd of=",
    "wipe",
    "format disk",
    "delete system",
    "delete root",
    "chmod -r 777 /",
    "chown -r",
    "systemctl disable",
    "systemctl mask",
    "reboot",
    "shutdown",
    "poweroff",
    "apt remove",
    "apt purge",
    "pacman -r",
    "dnf remove",
    "firewall disable",
    "ufw disable",
    # Greek
    "σβησε δισκο",
    "σβήσε δίσκο",
    "διαγραψε συστημα",
    "διέγραψε σύστημα",
    "κανε format",
    "κάνε format",
    "επανεκκινηση",
    "επανεκκίνηση",
    "τερματισμος",
    "τερματισμός",
]

_MEDIUM_RISK_PHRASES = [
    "install",
    "uninstall",
    "remove package",
    "delete file",
    "modify config",
    "edit config",
    "change service",
    "system service",
    "firewall",
    "permissions",
    "chmod",
    "chown",
    "apt install",
    "pacman -s",
    "dnf install",
    "flatpak install",
    # Greek
    "εγκαταστησε",
    "εγκατάστησε",
    "απεγκαταστησε",
    "απεγκατάστησε",
    "σβησε αρχειο",
    "σβήσε αρχείο",
    "αλλαξε config",
    "άλλαξε config",
    "δικαιωματα",
    "δικαιώματα",
]


def detect_risk(text: str) -> tuple[str, list[str]]:
    """
    Return (risk_level, matched_signals).
    risk_level is one of: "low", "medium", "high"
    """
    t = text.lower()

    high_signals = [phrase for phrase in _HIGH_RISK_PHRASES if phrase.lower() in t]
    if high_signals:
        return "high", high_signals

    medium_signals = [phrase for phrase in _MEDIUM_RISK_PHRASES if phrase.lower() in t]
    if medium_signals:
        return "medium", medium_signals

    return "low", []


# ---------------------------------------------------------------------------
# Signal lists for routing rules
# ---------------------------------------------------------------------------

_MEMORY_HYGIENE_SIGNALS = [
    "memory reflect",
    "reflect memory",
    "memory rotate",
    "rotate memory",
    "summarize memory",
    "clean memory",
    "memory cleanup",
    "compress logs",
    "summarize logs",
    "session summary",
    "summarize session",
    "μνημη",
    "μνήμη",
    "καθαρισε μνημη",
    "καθάρισε μνήμη",
]

_WRITING_SIGNALS = [
    "rewrite",
    "rephrase",
    "polish",
    "improve wording",
    "edit this text",
    "write an email",
    "draft email",
    "message",
    "social post",
    "caption",
    "announcement",
    "μεταφραση",
    "μετάφραση",
    "ξαναγραψε",
    "ξαναγράψε",
    "διορθωσε κειμενο",
    "διόρθωσε κείμενο",
]

_RESEARCH_SIGNALS = [
    "research",
    "investigate",
    "extract",
    "summarize file",
    "compare sources",
    "find in docs",
    "source",
    "sources",
    "cite",
    "citation",
    "evidence",
    "ψαξε",
    "ψάξε",
    "ερευνησε",
    "ερεύνησε",
    "πηγες",
    "πηγές",
    "τεκμηρια",
    "τεκμήρια",
]

_RESEARCH_TOOLS_SIGNALS = [
    "web",
    "online",
    "source",
    "sources",
    "cite",
    "citation",
    "docs",
    "file",
    "pdf",
    "official",
    "latest",
    "current",
    "recent",
]

_CODE_SIGNALS = [
    "code",
    "script",
    "python",
    "bash",
    "debug",
    "fix",
    "refactor",
    "implement",
    "architecture",
    "config",
    "router",
    "routing",
    "agent",
    "brain",
    "ai_run",
    "ai_core",
    "ai_router",
    "selftest",
    "compile",
    "validation",
    "prompt for copilot",
    "copilot",
    "repo",
    "git diff",
    "makefile",
    "linux",
    "terminal",
    "ollama",
    "bond project",
    "project state",
    "τεστ",
    "κωδικα",
    "κώδικα",
    "διορθωσε",
    "διόρθωσε",
    "υλοποιησε",
    "υλοποίησε",
]

_CODE_TOOLS_SIGNALS = [
    "run",
    "execute",
    "terminal",
    "command",
    "file",
    "repo",
    "git",
    "test",
    "compile",
    "validate",
]

_CODE_HIGH_CONFIDENCE_SIGNALS = [
    "bond project",
    "project state",
    "ai_run",
    "ai_core",
    "ai_router",
    "selftest",
    "routing",
    "router",
    "agent",
    "copilot",
    "repo",
    "git diff",
    "makefile",
    "ollama",
    "python",
    "bash",
    "script",
    "code",
    "debug",
    "implement",
    "refactor",
    "compile",
    "validation",
]

_CODE_SECONDARY_NICK_SIGNALS = [
    "prompt",
    "copilot",
    "documentation",
    "report",
    ".md",
    "markdown",
]

_PLANNING_SIGNALS = [
    "plan",
    "roadmap",
    "next steps",
    "break down",
    "strategy",
    "implementation plan",
    "σχεδιο",
    "σχέδιο",
    "πλανο",
    "πλάνο",
    "επομενα βηματα",
    "επόμενα βήματα",
]

_PLANNING_TECH_SIGNALS = [
    "implement",
    "architecture",
    "code",
    "script",
    "python",
    "bash",
    "router",
    "agent",
    "bond project",
    "ai_run",
    "selftest",
    "technical",
    "refactor",
    "build",
]

_GREETING_SIGNALS = [
    "hi",
    "hello",
    "hey",
    "bond",
    "μποντ",
    "μπόντ",
    "γεια",
    "τι κανεις",
    "τι κάνεις",
]


# ---------------------------------------------------------------------------
# Main routing function
# ---------------------------------------------------------------------------

def route_request(text: str) -> RouterDecision:
    """
    Deterministically classify user request and return a RouterDecision.
    Priority: empty > high_risk > memory_hygiene > writing > research >
              code/technical > planning > greeting/short > default
    """
    original_text = text
    normalized = normalize_for_route(text)

    # A. Empty or whitespace-only
    if not normalized:
        return RouterDecision(
            original_text=original_text,
            normalized_text=normalized,
            intent="empty",
            primary_agent=ROUTE_STUART,
            secondary_agents=[],
            requires_tools=False,
            risk_level="low",
            confidence=1.0,
            escalate=False,
            reason="empty_or_whitespace",
            matched_signals=[],
        )

    # B. High risk check
    risk_level, risk_signals = detect_risk(normalized)
    if risk_level == "high":
        return RouterDecision(
            original_text=original_text,
            normalized_text=normalized,
            intent="privileged_or_destructive_action",
            primary_agent=ROUTE_TERMINATOR,
            secondary_agents=[],
            requires_tools=True,
            risk_level="high",
            confidence=0.95,
            escalate=True,
            reason="high_risk_signal_detected",
            matched_signals=risk_signals,
        )

    # C. Memory hygiene
    if contains_any(normalized, _MEMORY_HYGIENE_SIGNALS):
        mem_risk, mem_signals = detect_risk(normalized)
        return RouterDecision(
            original_text=original_text,
            normalized_text=normalized,
            intent="memory_hygiene",
            primary_agent=ROUTE_LILY,
            secondary_agents=[],
            requires_tools=False,
            risk_level=mem_risk,
            confidence=0.88,
            escalate=(mem_risk == "high"),
            reason="memory_hygiene_signal",
            matched_signals=mem_signals,
        )

    # D. Writing/editing
    if contains_any(normalized, _WRITING_SIGNALS):
        w_risk, w_signals = detect_risk(normalized)
        return RouterDecision(
            original_text=original_text,
            normalized_text=normalized,
            intent="writing_or_formatting",
            primary_agent=ROUTE_NICK,
            secondary_agents=[],
            requires_tools=False,
            risk_level=w_risk,
            confidence=0.86,
            escalate=(w_risk == "high"),
            reason="writing_signal",
            matched_signals=w_signals,
        )

    # E. Research/extraction
    if contains_any(normalized, _RESEARCH_SIGNALS):
        r_risk, r_signals = detect_risk(normalized)
        requires_tools = contains_any(normalized, _RESEARCH_TOOLS_SIGNALS)
        return RouterDecision(
            original_text=original_text,
            normalized_text=normalized,
            intent="research_or_extraction",
            primary_agent=ROUTE_POLLY,
            secondary_agents=[],
            requires_tools=requires_tools,
            risk_level=r_risk,
            confidence=0.84,
            escalate=(r_risk == "high"),
            reason="research_signal",
            matched_signals=r_signals,
        )

    # F. Code/technical/project
    if contains_any(normalized, _CODE_SIGNALS):
        c_risk, c_signals = detect_risk(normalized)
        requires_tools = contains_any(normalized, _CODE_TOOLS_SIGNALS)
        secondary: list[str] = []
        if contains_any(normalized, _CODE_SECONDARY_NICK_SIGNALS):
            secondary = [ROUTE_NICK]
        high_conf = contains_any(normalized, _CODE_HIGH_CONFIDENCE_SIGNALS)
        confidence = 0.90 if high_conf else 0.82
        return RouterDecision(
            original_text=original_text,
            normalized_text=normalized,
            intent="technical_or_project_work",
            primary_agent=ROUTE_JAMES,
            secondary_agents=secondary,
            requires_tools=requires_tools,
            risk_level=c_risk,
            confidence=confidence,
            escalate=(c_risk == "high"),
            reason="code_technical_signal",
            matched_signals=c_signals,
        )

    # G. Planning
    if contains_any(normalized, _PLANNING_SIGNALS):
        p_risk, p_signals = detect_risk(normalized)
        is_technical = contains_any(normalized, _PLANNING_TECH_SIGNALS)
        if is_technical:
            return RouterDecision(
                original_text=original_text,
                normalized_text=normalized,
                intent="technical_planning",
                primary_agent=ROUTE_JAMES,
                secondary_agents=[],
                requires_tools=False,
                risk_level=p_risk,
                confidence=0.84,
                escalate=(p_risk == "high"),
                reason="technical_planning_signal",
                matched_signals=p_signals,
            )
        else:
            return RouterDecision(
                original_text=original_text,
                normalized_text=normalized,
                intent="general_planning",
                primary_agent=ROUTE_STUART,
                secondary_agents=[],
                requires_tools=False,
                risk_level=p_risk,
                confidence=0.76,
                escalate=(p_risk == "high"),
                reason="general_planning_signal",
                matched_signals=p_signals,
            )

    # H. Greeting / very short low-stakes
    word_count = len(normalized.split())
    if word_count <= 5:
        g_risk, g_signals = detect_risk(normalized)
        return RouterDecision(
            original_text=original_text,
            normalized_text=normalized,
            intent="simple_interaction",
            primary_agent=ROUTE_STUART,
            secondary_agents=[],
            requires_tools=False,
            risk_level=g_risk,
            confidence=0.80,
            escalate=(g_risk == "high"),
            reason="short_low_stakes",
            matched_signals=g_signals,
        )

    # I. Default
    d_risk, d_signals = detect_risk(normalized)
    return RouterDecision(
        original_text=original_text,
        normalized_text=normalized,
        intent="general_chat",
        primary_agent=ROUTE_STUART,
        secondary_agents=[],
        requires_tools=False,
        risk_level=d_risk,
        confidence=0.64,
        escalate=False,
        reason="default_low_stakes_chat",
        matched_signals=d_signals,
    )


def route_for_profile(text: str) -> str:
    """Return only the primary_agent string for a given request text."""
    return route_request(text).primary_agent


def decision_to_log_meta(decision: RouterDecision) -> dict:
    """Return a log-ready dict including dispatcher and router_version metadata."""
    meta = decision.to_dict()
    meta["dispatcher"] = "bob"
    meta["router_version"] = "stage2a_structured_deterministic"
    return meta
