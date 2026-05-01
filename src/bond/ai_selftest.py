#!/usr/bin/env python3
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from ai_action_contract import (
    ACTION_CHAT,
    ACTION_CONFIRM_REQUIRED,
    ACTION_DRY_RUN,
    ACTION_EXECUTE,
    ACTION_REJECT,
    CONTRACT_REASON_CONFIRMED_ACTION_NO_EXECUTABLE_STEPS,
    CONTRACT_REASON_CONFIRMED_ACTION_EXECUTE,
    build_action_contract,
)
from ai_parse_contract import (
     STATUS_MIXED,
     STATUS_PARSED_ACTION,
     STATUS_PARSED_ACTION_CHAIN,
     STATUS_PARTIAL_ACTION_CHAIN,
     STATUS_UNPARSED_ACTION,
     build_parse_contract,
)
from ai_core import (
    BOND_ROOT,
    CONFIG_FILE,
    ensure_memory_dirs,
    get_changelog_path,
    get_memory_root,
    get_state_root,
    log_memory,
)
from ai_policy import (
    POLICY_MODE_ACTION,
    POLICY_MODE_ACTION_CHAIN,
    POLICY_MODE_CHAT,
    POLICY_MODE_CONFIRM_REQUIRED,
    POLICY_MODE_REJECT,
    evaluate_request_policy,
)
from ai_router import route_request
from ai_capabilities import (
    STATUS_PARTIAL,
    STATUS_PLANNED,
    STATUS_UNSUPPORTED,
    capability_status,
    get_capability,
    is_capability_available,
    list_capabilities,
    list_capability_dicts,
    validate_registry,
)

SRC_BOND = BOND_ROOT / "src" / "bond"
AI_RUN = SRC_BOND / "ai_run.py"
AI_EXEC = SRC_BOND / "ai_exec.py"
AI_CONFIRMATION = SRC_BOND / "ai_confirmation.py"
AI_PARSE_CONTRACT = SRC_BOND / "ai_parse_contract.py"
AI_WRAPPER = BOND_ROOT / "scripts" / "ai"
AI_MEMORY = SRC_BOND / "ai_memory.py"
AI_MEMORY_QUERY = SRC_BOND / "ai_memory_query.py"
AI_MEMORY_REFLECT = SRC_BOND / "ai_memory_reflect.py"
AI_MEMORY_ROTATE = SRC_BOND / "ai_memory_rotate.py"

MEMORY_ROOT = get_memory_root()
STATE_ROOT = get_state_root()
CHANGELOG_PATH = get_changelog_path()
FACTS_DIR = MEMORY_ROOT / "facts"
LOGS_DIR = MEMORY_ROOT / "logs"
STATE_DIR = MEMORY_ROOT / "state"
STATE_CONFIG_PATH = STATE_ROOT / "assistant_config.json"

EXPECTED_CONFIG_FILE = str(CONFIG_FILE)
TEST_ARCHIVE_ROOT = Path(os.environ.get("BOND_ARCHIVE_ROOT", "/tmp/bond-test-archive")).expanduser().resolve(strict=False)
TEST_ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)

# Automated selftests run action requests in dry-run mode to avoid opening GUI windows.
# Real GUI action execution should be checked manually with BOND_ACTION_DRY_RUN unset.
SELFTEST_ACTION_DRY_RUN = True

TEST_FACT_BUCKET = FACTS_DIR / "preferences.json"
TEST_ACTIONS_LOG = LOGS_DIR / "actions.jsonl"
TEST_REFLECTIONS_LOG = LOGS_DIR / "reflections.jsonl"
TEST_ARCHIVE_MAP = STATE_DIR / "archive_map.json"
PENDING_CONFIRMATION_PATH = STATE_ROOT / "confirmations" / "pending.json"

ACTIVE_SANITATION_PATHS = [
    SRC_BOND,
    BOND_ROOT / "deploy" / "systemd" / "user",
    BOND_ROOT / "README.md",
    BOND_ROOT / "ROADMAP.md",
    BOND_ROOT / "CHANGELOG.md",
    BOND_ROOT / "docs" / "DOCS_INDEX.md",
    BOND_ROOT / "docs" / "STATE.md",
    BOND_ROOT / "docs" / "CLEANUP_PLAN.md",
    BOND_ROOT / "docs" / "PUBLICATION_BOUNDARY.md",
]

ACTIVE_SANITATION_MARKERS = [
    "/home/" + "geo" + "rgek",
    "/" + "mnt/",
    "~/" + "AI",
    "~/" + "ai-router",
    "~/" + "bond",
    "AI-" + "Archive",
    "g" + "k-p" + "c",
    "geo" + "rgek",
]


@dataclass
class TestCase:
    name: str
    cmd: list[str]
    env: dict[str, str | None] | None = None
    expect_exit: int | None = 0
    stdout_contains: list[str] | None = None
    stdout_not_contains: list[str] | None = None


def selftest_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("BOND_ROOT", str(BOND_ROOT))
    env.setdefault("BOND_MEMORY_ROOT", str(MEMORY_ROOT))
    env.setdefault("BOND_STATE_ROOT", str(STATE_ROOT))
    env.setdefault("BOND_ARCHIVE_ROOT", str(TEST_ARCHIVE_ROOT))
    if SELFTEST_ACTION_DRY_RUN:
        env.setdefault("BOND_ACTION_DRY_RUN", "1")
    return env


def run_cmd(args: list[str], extra_env: dict[str, str | None] | None = None) -> subprocess.CompletedProcess:
    env = selftest_env()
    if extra_env:
        for key, value in extra_env.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
    return subprocess.run(args, text=True, capture_output=True, check=False, env=env)


def print_block(title: str, text: str) -> None:
    print(f"\n=== {title} ===")
    print(text.rstrip() if text.strip() else "(empty)")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def backup_file(path: Path) -> tuple[bool, str | None]:
    if not path.exists():
        return False, None
    return True, path.read_text(encoding="utf-8", errors="ignore")


def restore_file(path: Path, existed: bool, content: str | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if existed and content is not None:
        path.write_text(content, encoding="utf-8")
    else:
        if path.exists():
            path.unlink()


def append_temp_jsonl_entry(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_query_json(query: str) -> tuple[dict | None, subprocess.CompletedProcess]:
    proc = run_cmd(["python3", str(AI_MEMORY_QUERY), query, "--json"])
    try:
        payload = json.loads(proc.stdout) if proc.stdout.strip() else None
    except Exception:
        payload = None
    return payload, proc


def parse_stdout_json(stdout: str) -> dict | None:
    try:
        payload = json.loads((stdout or "").strip())
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def evaluate_case(case: TestCase) -> tuple[bool, dict]:
    proc = run_cmd(case.cmd, case.env)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    errors: list[str] = []

    if case.expect_exit is not None and proc.returncode != case.expect_exit:
        errors.append(f"expected exit {case.expect_exit}, got {proc.returncode}")

    for needle in case.stdout_contains or []:
        if needle not in stdout:
            errors.append(f"missing stdout text: {needle}")

    for needle in case.stdout_not_contains or []:
        if needle in stdout:
            errors.append(f"unexpected stdout text: {needle}")

    result = {
        "name": case.name,
        "ok": not errors,
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "errors": errors,
        "cmd": case.cmd,
    }
    return result["ok"], result


def build_core_test_cases() -> list[TestCase]:
    return [
        TestCase(
            name="fact_memory_root",
            cmd=["python3", str(AI_RUN), "where is the memory root"],
            expect_exit=0,
            stdout_contains=[str(MEMORY_ROOT)],
        ),
        TestCase(
            name="action_known_target_dry_run",
            cmd=["python3", str(AI_RUN), "open router config"],
            expect_exit=0,
            stdout_contains=[
                '"ok": true',
                '"dry_run": true',
                '"would_execute": false',
                '"reason": "environment_dry_run_enabled"',
            ],
        ),
        TestCase(
            name="action_known_target_in_editor_dry_run",
            cmd=["python3", str(AI_RUN), "open assistant config in editor"],
            expect_exit=0,
            stdout_contains=[
                '"ok": true',
                '"dry_run": true',
                '"would_execute": false',
                '"reason": "environment_dry_run_enabled"',
            ],
        ),
        TestCase(
            name="action_show_downloads_dry_run",
            cmd=["python3", str(AI_RUN), "show downloads"],
            expect_exit=0,
            stdout_contains=[
                '"ok": true',
                '"dry_run": true',
                '"would_execute": false',
                '"reason": "environment_dry_run_enabled"',
            ],
        ),
        TestCase(
            name="action_explicit_allowed_path_dry_run",
            cmd=[
                "python3",
                str(AI_RUN),
                f"open {EXPECTED_CONFIG_FILE} in editor",
            ],
            expect_exit=0,
            stdout_contains=[
                '"ok": true',
                '"dry_run": true',
                '"would_execute": false',
                '"reason": "environment_dry_run_enabled"',
            ],
        ),
        TestCase(
            name="action_blocked_system_path",
            cmd=["python3", str(AI_EXEC), "open /etc/passwd"],
            expect_exit=3,
            stdout_contains=['"ok": false', "blocked_path:"],
        ),
        TestCase(
            name="chain_success_dry_run",
            cmd=[
                "python3",
                str(AI_RUN),
                "open router config and open assistant config in editor",
            ],
            expect_exit=0,
            stdout_contains=[
                '"ok": true',
                '"dry_run": true',
                '"would_execute": false',
                '"reason": "environment_dry_run_enabled"',
                '"action_steps": [',
                '"open router config"',
                '"open assistant config in editor"',
            ],
        ),
        TestCase(
            name="chain_blocked_step_resolves_dry_run",
            cmd=[
                "python3",
                str(AI_RUN),
                "open router config and open /etc/passwd",
            ],
            expect_exit=0,
            stdout_contains=[
                '"ok": true',
                '"dry_run": true',
                '"would_execute": false',
                '"reason": "environment_dry_run_enabled"',
                '"open /etc/passwd"',
            ],
        ),
        TestCase(
            name="chain_too_many_steps_dry_run",
            cmd=[
                "python3",
                str(AI_RUN),
                f"open router config and open assistant config and open downloads and open {BOND_ROOT}",
            ],
            expect_exit=0,
            stdout_contains=[
                '"ok": true',
                '"dry_run": true',
                '"would_execute": false',
                '"reason": "environment_dry_run_enabled"',
                '"open downloads"',
            ],
        ),
        TestCase(
            name="policy_mixed_intent_rejected",
            cmd=[
                "python3",
                str(AI_RUN),
                "open router config and tell me what you are",
            ],
            expect_exit=4,
            stdout_contains=[
                '"ok": false',
                '"error": "mixed_intent_request"',
                '"requires_confirmation": false',
            ],
            stdout_not_contains=["unknown_or_missing_target"],
        ),
        TestCase(
            name="wrapper_fact",
            cmd=[str(AI_WRAPPER), "where is the memory root"],
            expect_exit=0,
            stdout_contains=[str(MEMORY_ROOT)],
        ),
        TestCase(
            name="action_dry_run_env_open_router_config",
            cmd=[
                "python3",
                str(AI_RUN),
                "open router config",
            ],
            env={
                "BOND_ACTION_DRY_RUN": "1",
            },
            expect_exit=0,
            stdout_contains=[
                '"ok": true',
                '"dry_run": true',
                '"would_execute": false',
                '"reason": "environment_dry_run_enabled"',
            ],
            stdout_not_contains=[
                "unknown_or_missing_target",
            ],
        ),
        TestCase(
            name="action_dry_run_explicit_open_router_config",
            cmd=[
                "python3",
                str(AI_RUN),
                "dry run open router config",
            ],
            env={
                "BOND_ACTION_DRY_RUN": None,
            },
            expect_exit=0,
            stdout_contains=[
                '"ok": true',
                '"dry_run": true',
                '"would_execute": false',
                '"reason": "explicit_dry_run_requested"',
            ],
            stdout_not_contains=[
                "unknown_or_missing_target",
            ],
        ),
        TestCase(
            name="action_high_risk_confirmation_required",
            cmd=[
                "python3",
                str(AI_RUN),
                "sudo rm -rf /",
            ],
            expect_exit=5,
            stdout_contains=[
                '"ok": false',
                '"error": "confirmation_required"',
                '"requires_confirmation": true',
                '"risk_level": "high"',
                '"confirmation_token":',
                '"confirm_command":',
                '"expires_in_seconds":',
                '"would_execute": false',
                '"dry_run": false',
            ],
            stdout_not_contains=[
                "unknown_or_missing_target",
            ],
        ),
    ]


def run_router_tests() -> list[dict]:
    results: list[dict] = []

    router_cases = [
        # A
        {
            "name": "router_greeting_to_stuart",
            "query": "hello bond",
            "expect_primary_agent": "stuart",
            "expect_risk_level": "low",
            "expect_requires_tools": None,
            "expect_escalate": None,
            "expect_secondary_contains": None,
        },
        # B
        {
            "name": "router_writing_to_nick",
            "query": "rewrite this email so it sounds cleaner",
            "expect_primary_agent": "nick",
            "expect_risk_level": None,
            "expect_requires_tools": None,
            "expect_escalate": None,
            "expect_secondary_contains": None,
        },
        # C
        {
            "name": "router_research_to_polly",
            "query": "research official ollama documentation and summarize sources",
            "expect_primary_agent": "polly",
            "expect_risk_level": None,
            "expect_requires_tools": True,
            "expect_escalate": None,
            "expect_secondary_contains": None,
        },
        # D
        {
            "name": "router_code_to_james",
            "query": "debug this python script and give validation commands",
            "expect_primary_agent": "james",
            "expect_risk_level": None,
            "expect_requires_tools": None,
            "expect_escalate": None,
            "expect_secondary_contains": None,
        },
        # E
        {
            "name": "router_memory_to_lily",
            "query": "summarize memory logs",
            "expect_primary_agent": "lily",
            "expect_risk_level": None,
            "expect_requires_tools": None,
            "expect_escalate": None,
            "expect_secondary_contains": None,
        },
        # F
        {
            "name": "router_dangerous_to_terminator",
            "query": "sudo rm -rf /",
            "expect_primary_agent": "terminator",
            "expect_risk_level": "high",
            "expect_requires_tools": None,
            "expect_escalate": True,
            "expect_secondary_contains": None,
        },
        # G
        {
            "name": "router_copilot_prompt_james_nick",
            "query": "give me a precise copilot prompt to modify ai_run.py",
            "expect_primary_agent": "james",
            "expect_risk_level": None,
            "expect_requires_tools": None,
            "expect_escalate": None,
            "expect_secondary_contains": "nick",
        },
    ]

    for case in router_cases:
        query = case["query"]
        errors: list[str] = []
        decision = None
        try:
            decision = route_request(query)
            if decision.primary_agent != case["expect_primary_agent"]:
                errors.append(
                    f"expected primary_agent={case['expect_primary_agent']!r}, got {decision.primary_agent!r}"
                )
            if case["expect_risk_level"] is not None and decision.risk_level != case["expect_risk_level"]:
                errors.append(
                    f"expected risk_level={case['expect_risk_level']!r}, got {decision.risk_level!r}"
                )
            if case["expect_requires_tools"] is not None and decision.requires_tools != case["expect_requires_tools"]:
                errors.append(
                    f"expected requires_tools={case['expect_requires_tools']!r}, got {decision.requires_tools!r}"
                )
            if case["expect_escalate"] is not None and decision.escalate != case["expect_escalate"]:
                errors.append(
                    f"expected escalate={case['expect_escalate']!r}, got {decision.escalate!r}"
                )
            if case["expect_secondary_contains"] is not None:
                if case["expect_secondary_contains"] not in decision.secondary_agents:
                    errors.append(
                        f"expected secondary_agents to contain {case['expect_secondary_contains']!r}, got {decision.secondary_agents!r}"
                    )
        except Exception as exc:
            errors.append(f"route_request raised exception: {exc}")

        results.append(
            {
                "name": case["name"],
                "ok": not errors,
                "returncode": 0,
                "stdout": json.dumps(decision.to_dict(), ensure_ascii=False) if decision else "",
                "stderr": "",
                "errors": errors,
                "cmd": ["route_request", query],
            }
        )

    return results


def run_selftest_mode_tests() -> list[dict]:
    results: list[dict] = []

    env = selftest_env()
    errors: list[str] = []
    if SELFTEST_ACTION_DRY_RUN and env.get("BOND_ACTION_DRY_RUN") != "1":
        errors.append("selftest_env did not enable BOND_ACTION_DRY_RUN=1")

    results.append(
        {
            "name": "selftest_action_mode_non_interactive",
            "ok": not errors,
            "returncode": 0,
            "stdout": json.dumps(
                {
                    "SELFTEST_ACTION_DRY_RUN": SELFTEST_ACTION_DRY_RUN,
                    "BOND_ACTION_DRY_RUN": env.get("BOND_ACTION_DRY_RUN"),
                },
                ensure_ascii=False,
            ),
            "stderr": "",
            "errors": errors,
            "cmd": ["selftest_env"],
        }
    )

    return results


def run_router_profile_tests() -> list[dict]:
    results: list[dict] = []
    profiles_path = BOND_ROOT / "config" / "router" / "profiles.json"

    errors: list[str] = []
    try:
        data = json.loads(profiles_path.read_text(encoding="utf-8"))
        profiles = data.get("profiles", {})

        required = {"stuart", "bob", "polly", "nick", "james", "lily", "terminator"}
        actual = set(profiles.keys())
        missing = required - actual
        if missing:
            errors.append(f"missing profiles: {sorted(missing)}")

        allowed_models = {
            "qwen2.5:3b-instruct",
            "gemma2:2b",
            "qwen2.5:7b-instruct",
        }
        forbidden_substrings = ["gpt" + "-oss", "20" + "b", "gemma" + "3"]

        for key, cfg in profiles.items():
            model = cfg.get("model", "")
            if model not in allowed_models:
                errors.append(f"profile {key!r} uses disallowed model: {model!r}")
            for forbidden in forbidden_substrings:
                if forbidden in model.lower():
                    errors.append(f"profile {key!r} model contains forbidden substring {forbidden!r}: {model!r}")

        raw = profiles_path.read_text(encoding="utf-8").lower()
        for forbidden in forbidden_substrings:
            if forbidden in raw:
                errors.append(f"profiles.json contains forbidden model reference: {forbidden!r}")

    except Exception as exc:
        errors.append(f"profile load/parse error: {exc}")

    results.append(
        {
            "name": "router_profile_model_validation",
            "ok": not errors,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "errors": errors,
            "cmd": ["validate", str(profiles_path)],
        }
    )
    return results


def run_policy_tests() -> list[dict]:
    results: list[dict] = []

    def _policy_result(name, text, gatekeeper_result, chain_steps=None):
        route_decision = route_request(text)
        policy = evaluate_request_policy(text, gatekeeper_result, chain_steps, route_decision)
        return route_decision, policy

    policy_cases = [
        {
            "name": "policy_chat_allowed",
            "text": "what is sudo rm -rf and why is it dangerous?",
            "gatekeeper_result": "chat",
            "chain_steps": None,
            "assertions": [
                ("mode", POLICY_MODE_CHAT),
                ("allowed", True),
                ("requires_confirmation", False),
            ],
        },
        {
            "name": "policy_mixed_rejected",
            "text": "open router config and tell me what you are",
            "gatekeeper_result": "mixed",
            "chain_steps": ["open router config"],
            "assertions": [
                ("mode", POLICY_MODE_REJECT),
                ("allowed", False),
                ("exit_code", 4),
            ],
        },
        {
            "name": "policy_safe_action_allowed",
            "text": "open router config",
            "gatekeeper_result": "pure_action",
            "chain_steps": None,
            "assertions": [
                ("mode", POLICY_MODE_ACTION),
                ("allowed", True),
            ],
        },
        {
            "name": "policy_safe_action_chain_allowed",
            "text": "open router config and open assistant config in editor",
            "gatekeeper_result": "pure_action",
            "chain_steps": ["open router config", "open assistant config in editor"],
            "assertions": [
                ("mode", POLICY_MODE_ACTION_CHAIN),
                ("allowed", True),
                ("action_steps_len", 2),
            ],
        },
        {
            "name": "policy_high_risk_action_confirmation_required",
            "text": "sudo rm -rf /",
            "gatekeeper_result": "pure_action",
            "chain_steps": None,
            "assertions": [
                ("mode", POLICY_MODE_CONFIRM_REQUIRED),
                ("allowed", False),
                ("requires_confirmation", True),
                ("exit_code", 5),
            ],
        },
    ]

    for case in policy_cases:
        errors: list[str] = []
        route_decision = None
        policy = None

        try:
            route_decision, policy = _policy_result(
                case["name"],
                case["text"],
                case["gatekeeper_result"],
                case["chain_steps"],
            )

            for field, expected in case["assertions"]:
                if field == "action_steps_len":
                    actual = len(policy.action_steps)
                else:
                    actual = getattr(policy, field)
                if actual != expected:
                    errors.append(f"expected {field}={expected!r}, got {actual!r}")
        except Exception as exc:
            errors.append(f"evaluate_request_policy raised exception: {exc}")

        payload = {
            "route": route_decision.to_dict() if route_decision else None,
            "policy": policy.to_dict() if policy else None,
        }

        results.append(
            {
                "name": case["name"],
                "ok": not errors,
                "returncode": 0,
                "stdout": json.dumps(payload, ensure_ascii=False),
                "stderr": "",
                "errors": errors,
                "cmd": ["evaluate_request_policy", case["text"]],
            }
        )

    return results


def run_action_contract_tests() -> list[dict]:
    results: list[dict] = []

    def _contract_result(
        name,
        text,
        gatekeeper_result,
        chain_steps=None,
        env_dry_run=None,
        confirmation_granted: bool = False,
    ):
        previous = os.environ.get("BOND_ACTION_DRY_RUN")
        try:
            if env_dry_run is None:
                os.environ.pop("BOND_ACTION_DRY_RUN", None)
            else:
                os.environ["BOND_ACTION_DRY_RUN"] = env_dry_run
            route_decision = route_request(text)
            policy = evaluate_request_policy(text, gatekeeper_result, chain_steps, route_decision)
            contract = build_action_contract(
                text,
                policy,
                route_decision,
                confirmation_granted=confirmation_granted,
            )
            return route_decision, policy, contract
        finally:
            if previous is None:
                os.environ.pop("BOND_ACTION_DRY_RUN", None)
            else:
                os.environ["BOND_ACTION_DRY_RUN"] = previous

    cases = [
        {
            "name": "contract_chat_no_execution",
            "text": "what is sudo rm -rf and why is it dangerous?",
            "gatekeeper_result": "chat",
            "chain_steps": None,
            "env_dry_run": None,
            "assertions": [
                ("mode", ACTION_CHAT),
                ("allowed_to_execute", False),
                ("dry_run", False),
            ],
        },
        {
            "name": "contract_safe_action_execute",
            "text": "open router config",
            "gatekeeper_result": "pure_action",
            "chain_steps": None,
            "env_dry_run": None,
            "assertions": [
                ("mode", ACTION_EXECUTE),
                ("allowed_to_execute", True),
                ("dry_run", False),
            ],
        },
        {
            "name": "contract_action_chain_execute",
            "text": "open router config and open assistant config in editor",
            "gatekeeper_result": "pure_action",
            "chain_steps": ["open router config", "open assistant config in editor"],
            "env_dry_run": None,
            "assertions": [
                ("mode", ACTION_EXECUTE),
                ("allowed_to_execute", True),
                ("action_steps_len", 2),
            ],
        },
        {
            "name": "contract_explicit_dry_run",
            "text": "dry run open router config",
            "gatekeeper_result": "pure_action",
            "chain_steps": None,
            "env_dry_run": None,
            "assertions": [
                ("mode", ACTION_DRY_RUN),
                ("allowed_to_execute", False),
                ("dry_run", True),
                ("reason", "explicit_dry_run_requested"),
            ],
        },
        {
            "name": "contract_env_dry_run",
            "text": "open router config",
            "gatekeeper_result": "pure_action",
            "chain_steps": None,
            "env_dry_run": "1",
            "assertions": [
                ("mode", ACTION_DRY_RUN),
                ("allowed_to_execute", False),
                ("dry_run", True),
                ("reason", "environment_dry_run_enabled"),
            ],
        },
        {
            "name": "contract_high_risk_confirm_required",
            "text": "sudo rm -rf /",
            "gatekeeper_result": "pure_action",
            "chain_steps": None,
            "env_dry_run": None,
            "assertions": [
                ("mode", ACTION_CONFIRM_REQUIRED),
                ("allowed_to_execute", False),
                ("requires_confirmation", True),
                ("exit_code", 5),
            ],
        },
        {
            "name": "contract_confirm_required_with_confirmation_granted",
            "text": "sudo rm -rf /",
            "gatekeeper_result": "pure_action",
            "chain_steps": None,
            "env_dry_run": None,
            "confirmation_granted": True,
            "assertions": [
                ("mode", ACTION_REJECT),
                ("allowed_to_execute", False),
                ("requires_confirmation", False),
                ("reason", CONTRACT_REASON_CONFIRMED_ACTION_NO_EXECUTABLE_STEPS),
            ],
        },
        {
            "name": "contract_policy_reject",
            "text": "open router config and tell me what you are",
            "gatekeeper_result": "mixed",
            "chain_steps": ["open router config"],
            "env_dry_run": None,
            "assertions": [
                ("mode", ACTION_REJECT),
                ("allowed_to_execute", False),
                ("exit_code", 4),
            ],
        },
    ]

    for case in cases:
        errors: list[str] = []
        route_decision = None
        policy = None
        contract = None

        try:
            route_decision, policy, contract = _contract_result(
                case["name"],
                case["text"],
                case["gatekeeper_result"],
                case["chain_steps"],
                case["env_dry_run"],
                confirmation_granted=bool(case.get("confirmation_granted", False)),
            )

            for field, expected in case["assertions"]:
                if field == "action_steps_len":
                    actual = len(contract.action_steps)
                else:
                    actual = getattr(contract, field)
                if actual != expected:
                    errors.append(f"expected {field}={expected!r}, got {actual!r}")
        except Exception as exc:
            errors.append(f"build_action_contract raised exception: {exc}")

        payload = {
            "route": route_decision.to_dict() if route_decision else None,
            "policy": policy.to_dict() if policy else None,
            "contract": contract.to_dict() if contract else None,
        }

        results.append(
            {
                "name": case["name"],
                "ok": not errors,
                "returncode": 0,
                "stdout": json.dumps(payload, ensure_ascii=False),
                "stderr": "",
                "errors": errors,
                "cmd": ["build_action_contract", case["text"]],
            }
        )

    return results


def run_capability_registry_tests() -> list[dict]:
    results: list[dict] = []

    def _record(name: str, errors: list[str], payload: dict) -> None:
        results.append(
            {
                "name": name,
                "ok": not errors,
                "returncode": 0,
                "stdout": json.dumps(payload, ensure_ascii=False),
                "stderr": "",
                "errors": errors,
                "cmd": ["capability_registry", name],
            }
        )

    validation_errors = validate_registry()
    caps = list_capabilities()
    errors: list[str] = []
    if validation_errors != []:
        errors.append(f"validate_registry returned errors: {validation_errors}")
    if len(caps) < 27:
        errors.append(f"expected at least 27 capabilities, got {len(caps)}")
    _record(
        "capability_registry_validates",
        errors,
        {
            "validation_errors": validation_errors,
            "capability_count": len(caps),
        },
    )

    required_names = {
        "open_known_target",
        "open_explicit_path",
        "query_model",
        "describe_capabilities",
        "timer",
        "clipboard",
        "apply_privileged_system_updates",
        "inspect_package_update_status",
        "inspect_storage_hygiene",
        "retrieve_document_knowledge",
        "ingest_knowledge_sources",
        "reindex_document_corpus",
    }
    names = {cap.name for cap in caps}
    missing = sorted(required_names - names)
    errors = []
    if missing:
        errors.append(f"missing required capability names: {missing}")
    _record(
        "capability_registry_required_entries_present",
        errors,
        {
            "required_count": len(required_names),
            "present_required_count": len(required_names - set(missing)),
            "missing": missing,
        },
    )

    checks = [
        (
            "open_known_target",
            True,
            STATUS_PARTIAL,
        ),
        (
            "query_model",
            True,
            STATUS_PARTIAL,
        ),
        (
            "describe_capabilities",
            True,
            STATUS_PARTIAL,
        ),
    ]
    errors = []
    for name, expected_available, expected_status in checks:
        actual_available = is_capability_available(name)
        actual_status = capability_status(name)
        if actual_available is not expected_available:
            errors.append(
                f"{name}: expected available={expected_available!r}, got {actual_available!r}"
            )
        if actual_status != expected_status:
            errors.append(f"{name}: expected status={expected_status!r}, got {actual_status!r}")
    _record(
        "capability_registry_partial_current_capabilities_are_available_with_caveats",
        errors,
        {
            "open_known_target": {
                "available": is_capability_available("open_known_target"),
                "status": capability_status("open_known_target"),
            },
            "query_model": {
                "available": is_capability_available("query_model"),
                "status": capability_status("query_model"),
            },
            "describe_capabilities": {
                "available": is_capability_available("describe_capabilities"),
                "status": capability_status("describe_capabilities"),
            },
        },
    )

    checks = [
        ("timer", False, STATUS_UNSUPPORTED),
        ("clipboard", False, STATUS_UNSUPPORTED),
        ("inspect_package_update_status", False, STATUS_PLANNED),
        ("retrieve_document_knowledge", False, STATUS_PLANNED),
    ]
    errors = []
    for name, expected_available, expected_status in checks:
        actual_available = is_capability_available(name)
        actual_status = capability_status(name)
        if actual_available is not expected_available:
            errors.append(
                f"{name}: expected available={expected_available!r}, got {actual_available!r}"
            )
        if actual_status != expected_status:
            errors.append(f"{name}: expected status={expected_status!r}, got {actual_status!r}")
    _record(
        "capability_registry_planned_and_unsupported_are_not_available",
        errors,
        {
            "timer": {
                "available": is_capability_available("timer"),
                "status": capability_status("timer"),
            },
            "clipboard": {
                "available": is_capability_available("clipboard"),
                "status": capability_status("clipboard"),
            },
            "inspect_package_update_status": {
                "available": is_capability_available("inspect_package_update_status"),
                "status": capability_status("inspect_package_update_status"),
            },
            "retrieve_document_knowledge": {
                "available": is_capability_available("retrieve_document_knowledge"),
                "status": capability_status("retrieve_document_knowledge"),
            },
        },
    )

    cap = get_capability("apply_privileged_system_updates")
    errors = []
    if cap is None:
        errors.append("apply_privileged_system_updates was missing")
    else:
        if cap.status != STATUS_PLANNED:
            errors.append(f"expected status={STATUS_PLANNED!r}, got {cap.status!r}")
        if cap.needs_elevated_lane is not True:
            errors.append(f"expected needs_elevated_lane=True, got {cap.needs_elevated_lane!r}")
        if cap.requires_confirmation is not True:
            errors.append(f"expected requires_confirmation=True, got {cap.requires_confirmation!r}")
        if cap.read_only is not False:
            errors.append(f"expected read_only=False, got {cap.read_only!r}")
    if is_capability_available("apply_privileged_system_updates") is not False:
        errors.append("apply_privileged_system_updates should not be available")
    _record(
        "capability_registry_privileged_updates_are_planned_only",
        errors,
        {
            "status": cap.status if cap else None,
            "needs_elevated_lane": cap.needs_elevated_lane if cap else None,
            "requires_confirmation": cap.requires_confirmation if cap else None,
            "read_only": cap.read_only if cap else None,
            "available": is_capability_available("apply_privileged_system_updates"),
        },
    )

    dicts = list_capability_dicts()
    errors = []
    if not all(isinstance(item, dict) for item in dicts):
        errors.append("list_capability_dicts should return list[dict]")
    for index, item in enumerate(dicts):
        for key in ("name", "class", "status", "execution_mode", "risk_level"):
            if key not in item:
                errors.append(f"entry {index} missing required key: {key}")
        if "capability_class" in item:
            errors.append(f"entry {index} leaked capability_class")
        if not isinstance(item.get("side_effects", []), list):
            errors.append(f"entry {index} side_effects must be list")
        if not isinstance(item.get("required_tools", []), list):
            errors.append(f"entry {index} required_tools must be list")
        if not isinstance(item.get("backends", {}), dict):
            errors.append(f"entry {index} backends must be dict")
    if get_capability("does_not_exist") is not None:
        errors.append("unknown capability should return None")
    if capability_status("does_not_exist") != STATUS_UNSUPPORTED:
        errors.append("unknown capability status should be unsupported")
    if is_capability_available("does_not_exist") is not False:
        errors.append("unknown capability should not be available")
    _record(
        "capability_registry_dict_schema_is_public_safe",
        errors,
        {
            "dict_count": len(dicts),
            "unknown": {
                "get_capability": get_capability("does_not_exist"),
                "status": capability_status("does_not_exist"),
                "available": is_capability_available("does_not_exist"),
            },
        },
    )

    return results


def run_parse_contract_tests() -> list[dict]:
    results: list[dict] = []

    contract_cases = [
        {
            "name": "parse_contract_single_action_parsed",
            "text": "open router config",
            "expect_status": STATUS_PARSED_ACTION,
            "expect_executable": True,
            "expect_unparsed": [],
            "expect_parsed_count": 1,
        },
        {
            "name": "parse_contract_action_chain_parsed",
            "text": "open router config and open assistant config in editor",
            "expect_status": STATUS_PARSED_ACTION_CHAIN,
            "expect_executable": True,
            "expect_unparsed": [],
            "expect_parsed_count": 2,
        },
        {
            "name": "parse_contract_single_action_unparsed",
            "text": "notify me",
            "expect_status": STATUS_UNPARSED_ACTION,
            "expect_executable": False,
            "expect_unparsed": ["notify me"],
            "expect_parsed_count": 0,
        },
        {
            "name": "parse_contract_partial_action_chain",
            "text": "open router config and notify me",
            "expect_status": STATUS_PARTIAL_ACTION_CHAIN,
            "expect_executable": False,
            "expect_unparsed": ["notify me"],
            "expect_parsed_count": 1,
        },
        {
            "name": "parse_contract_mixed_intent_remains_mixed",
            "text": "open router config and tell me what you are",
            "expect_status": STATUS_MIXED,
            "expect_executable": False,
            "expect_unparsed": [],
            "expect_parsed_count": 0,
        },
    ]

    for case in contract_cases:
        errors: list[str] = []
        contract = None

        try:
            contract = build_parse_contract(case["text"])

            if contract.status != case["expect_status"]:
                errors.append(f"expected status={case['expect_status']!r}, got {contract.status!r}")
            if contract.executable is not case["expect_executable"]:
                errors.append(f"expected executable={case['expect_executable']!r}, got {contract.executable!r}")
            if contract.unparsed_steps != case["expect_unparsed"]:
                errors.append(f"expected unparsed_steps={case['expect_unparsed']!r}, got {contract.unparsed_steps!r}")
            if len(contract.parsed_intents) != case["expect_parsed_count"]:
                errors.append(f"expected parsed_intents length={case['expect_parsed_count']!r}, got {len(contract.parsed_intents)!r}")
        except Exception as exc:
            errors.append(f"build_parse_contract raised exception: {exc}")

        results.append(
            {
                "name": case["name"],
                "ok": not errors,
                "returncode": 0,
                "stdout": json.dumps(contract.to_dict() if contract else {}, ensure_ascii=False),
                "stderr": "",
                "errors": errors,
                "cmd": ["build_parse_contract", case["text"]],
            }
        )

    integration_cases = [
        {
            "name": "parse_preflight_notify_me_rejected_before_executor",
            "cmd": ["python3", str(AI_RUN), "notify me"],
            "env": {"BOND_ACTION_DRY_RUN": None},
            "expect_exit": 3,
            "expect_error": "action_not_parsed",
            "must_not_contain": "no_safe_action_detected",
        },
        {
            "name": "parse_preflight_safe_single_action_dry_run_still_works",
            "cmd": ["python3", str(AI_RUN), "open router config"],
            "env": {"BOND_ACTION_DRY_RUN": "1"},
            "expect_exit": 0,
            "expect_ok": True,
            "expect_dry_run": True,
        },
        {
            "name": "parse_preflight_safe_action_chain_dry_run_still_works",
            "cmd": ["python3", str(AI_RUN), "open router config and open assistant config in editor"],
            "env": {"BOND_ACTION_DRY_RUN": "1"},
            "expect_exit": 0,
            "expect_ok": True,
            "expect_dry_run": True,
        },
        {
            "name": "parse_preflight_mixed_intent_still_rejected",
            "cmd": ["python3", str(AI_RUN), "open router config and tell me what you are"],
            "env": {"BOND_ACTION_DRY_RUN": None},
            "expect_exit": 4,
            "expect_error": "mixed_intent_request",
        },
        {
            "name": "parse_preflight_high_risk_still_confirmation_required",
            "cmd": ["python3", str(AI_RUN), "sudo rm -rf /"],
            "env": {"BOND_ACTION_DRY_RUN": None},
            "expect_exit": 5,
            "expect_error": "confirmation_required",
            "expect_confirmation_token": True,
        },
    ]

    for case in integration_cases:
        errors: list[str] = []
        proc = run_cmd(case["cmd"], case.get("env"))
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        payload = parse_stdout_json(stdout)

        if proc.returncode != case["expect_exit"]:
            errors.append(f"expected exit {case['expect_exit']}, got {proc.returncode}")

        if not isinstance(payload, dict):
            errors.append("stdout is not valid JSON")
        else:
            if "expect_error" in case and payload.get("error") != case["expect_error"]:
                errors.append(f"expected error={case['expect_error']!r}, got {payload.get('error')!r}")
            if "expect_ok" in case and payload.get("ok") is not case["expect_ok"]:
                errors.append(f"expected ok={case['expect_ok']!r}, got {payload.get('ok')!r}")
            if "expect_dry_run" in case and payload.get("dry_run") is not case["expect_dry_run"]:
                errors.append(f"expected dry_run={case['expect_dry_run']!r}, got {payload.get('dry_run')!r}")
            if case.get("expect_confirmation_token") and not payload.get("confirmation_token"):
                errors.append("expected confirmation_token in payload")

        forbidden = case.get("must_not_contain")
        if forbidden and forbidden in stdout:
            errors.append(f"stdout unexpectedly contained {forbidden!r}")

        results.append(
            {
                "name": case["name"],
                "ok": not errors,
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "errors": errors,
                "cmd": case["cmd"],
            }
        )

    return results


def run_confirmation_token_tests() -> list[dict]:
    results: list[dict] = []

    pending_existed, pending_before = backup_file(PENDING_CONFIRMATION_PATH)
    try:
        if PENDING_CONFIRMATION_PATH.exists():
            PENDING_CONFIRMATION_PATH.unlink()

        create_proc = run_cmd(["python3", str(AI_RUN), "sudo rm -rf /"])
        create_stdout = (create_proc.stdout or "").strip()
        create_stderr = (create_proc.stderr or "").strip()
        create_payload = parse_stdout_json(create_stdout)
        create_errors: list[str] = []
        token = ""

        if create_proc.returncode != 5:
            create_errors.append(f"expected exit 5, got {create_proc.returncode}")
        if not isinstance(create_payload, dict):
            create_errors.append("confirmation-required response is not valid JSON")
        else:
            token = str(create_payload.get("confirmation_token", "")).strip()
            if create_payload.get("error") != "confirmation_required":
                create_errors.append("expected error=confirmation_required")
            if not token:
                create_errors.append("missing confirmation_token")
            if not str(create_payload.get("confirm_command", "")).startswith("confirm "):
                create_errors.append("missing or invalid confirm_command")
            if not isinstance(create_payload.get("expires_in_seconds"), int):
                create_errors.append("missing expires_in_seconds integer")
            if create_payload.get("would_execute") is not False:
                create_errors.append("would_execute should be false for confirmation-required")
            if create_payload.get("dry_run") is not False:
                create_errors.append("dry_run should be false for confirmation-required")

        results.append(
            {
                "name": "confirmation_token_created_for_high_risk",
                "ok": not create_errors,
                "returncode": create_proc.returncode,
                "stdout": create_stdout,
                "stderr": create_stderr,
                "errors": create_errors,
                "cmd": ["python3", str(AI_RUN), "sudo rm -rf /"],
            }
        )

        invalid_proc = run_cmd(["python3", str(AI_RUN), "confirm WRONGTOKEN"])
        invalid_stdout = (invalid_proc.stdout or "").strip()
        invalid_stderr = (invalid_proc.stderr or "").strip()
        invalid_payload = parse_stdout_json(invalid_stdout)
        invalid_errors: list[str] = []
        if invalid_proc.returncode != 5:
            invalid_errors.append(f"expected exit 5, got {invalid_proc.returncode}")
        if not isinstance(invalid_payload, dict) or invalid_payload.get("error") != "confirmation_invalid":
            invalid_errors.append("expected confirmation_invalid error payload")

        results.append(
            {
                "name": "confirmation_token_invalid_fails",
                "ok": not invalid_errors,
                "returncode": invalid_proc.returncode,
                "stdout": invalid_stdout,
                "stderr": invalid_stderr,
                "errors": invalid_errors,
                "cmd": ["python3", str(AI_RUN), "confirm WRONGTOKEN"],
            }
        )

        expired_errors: list[str] = []
        if token:
            pending = read_json(PENDING_CONFIRMATION_PATH)
            if isinstance(pending, dict):
                pending["expires_at"] = 0
                pending["consumed"] = False
                PENDING_CONFIRMATION_PATH.parent.mkdir(parents=True, exist_ok=True)
                PENDING_CONFIRMATION_PATH.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")

            expired_proc = run_cmd(["python3", str(AI_RUN), f"confirm {token}"])
            expired_stdout = (expired_proc.stdout or "").strip()
            expired_stderr = (expired_proc.stderr or "").strip()
            expired_payload = parse_stdout_json(expired_stdout)

            if expired_proc.returncode != 5:
                expired_errors.append(f"expected exit 5, got {expired_proc.returncode}")
            if not isinstance(expired_payload, dict) or expired_payload.get("error") != "confirmation_expired":
                expired_errors.append("expected confirmation_expired error payload")
        else:
            expired_proc = subprocess.CompletedProcess([], 1, "", "")
            expired_stdout = ""
            expired_stderr = ""
            expired_errors.append("token creation failed; could not run expired-token test")

        results.append(
            {
                "name": "confirmation_token_expired_fails",
                "ok": not expired_errors,
                "returncode": expired_proc.returncode,
                "stdout": expired_stdout,
                "stderr": expired_stderr,
                "errors": expired_errors,
                "cmd": ["python3", str(AI_RUN), f"confirm {token}" if token else "confirm <missing-token>"],
            }
        )

        recreate_proc = run_cmd(["python3", str(AI_RUN), "sudo rm -rf /"])
        recreate_payload = parse_stdout_json((recreate_proc.stdout or "").strip())
        live_token = str((recreate_payload or {}).get("confirmation_token", "")).strip()

        no_step_confirm_errors: list[str] = []
        if recreate_proc.returncode != 5:
            no_step_confirm_errors.append(f"expected token recreate exit 5, got {recreate_proc.returncode}")
        if not live_token:
            no_step_confirm_errors.append("missing token for non-dry-run fail-closed confirmation test")

        if live_token:
            no_step_confirm_proc = run_cmd(
                ["python3", str(AI_RUN), f"confirm {live_token}"],
                {"BOND_ACTION_DRY_RUN": None},
            )
            no_step_confirm_stdout = (no_step_confirm_proc.stdout or "").strip()
            no_step_confirm_stderr = (no_step_confirm_proc.stderr or "").strip()
            no_step_confirm_payload = parse_stdout_json(no_step_confirm_stdout)

            if no_step_confirm_proc.returncode == 0:
                no_step_confirm_errors.append("confirmed empty-step action should fail closed with nonzero exit")
            if not isinstance(no_step_confirm_payload, dict):
                no_step_confirm_errors.append("confirmed empty-step fail-closed response is not JSON")
            else:
                if no_step_confirm_payload.get("ok") is not False:
                    no_step_confirm_errors.append("expected ok=false for confirmed empty-step fail-closed path")
                if no_step_confirm_payload.get("error") != "confirmed_action_no_executable_steps":
                    no_step_confirm_errors.append("expected confirmed_action_no_executable_steps error")
                if no_step_confirm_payload.get("would_execute") is not False:
                    no_step_confirm_errors.append("expected would_execute=false for confirmed empty-step fail-closed path")
                if no_step_confirm_payload.get("dry_run") is not False:
                    no_step_confirm_errors.append("expected dry_run=false for confirmed empty-step fail-closed path")

            pending_after_no_step_confirm = read_json(PENDING_CONFIRMATION_PATH)
            if not isinstance(pending_after_no_step_confirm, dict) or pending_after_no_step_confirm.get("consumed") is not True:
                no_step_confirm_errors.append("token was not marked consumed after non-dry-run confirmed fail-closed path")
        else:
            no_step_confirm_proc = subprocess.CompletedProcess([], 1, "", "")
            no_step_confirm_stdout = ""
            no_step_confirm_stderr = ""

        results.append(
            {
                "name": "confirmation_token_valid_no_steps_fail_closed",
                "ok": not no_step_confirm_errors,
                "returncode": no_step_confirm_proc.returncode,
                "stdout": no_step_confirm_stdout,
                "stderr": no_step_confirm_stderr,
                "errors": no_step_confirm_errors,
                "cmd": ["python3", str(AI_RUN), f"confirm {live_token}" if live_token else "confirm <missing-token>"],
            }
        )

        dry_recreate_proc = run_cmd(["python3", str(AI_RUN), "sudo rm -rf /"])
        dry_recreate_payload = parse_stdout_json((dry_recreate_proc.stdout or "").strip())
        dry_live_token = str((dry_recreate_payload or {}).get("confirmation_token", "")).strip()

        confirm_errors: list[str] = []
        if dry_recreate_proc.returncode != 5:
            confirm_errors.append(f"expected dry-run token recreate exit 5, got {dry_recreate_proc.returncode}")
        if not dry_live_token:
            confirm_errors.append("missing token for valid confirmation test")

        if dry_live_token:
            confirm_proc = run_cmd(
                ["python3", str(AI_RUN), f"confirm {dry_live_token}"],
                {"BOND_ACTION_DRY_RUN": "1"},
            )
            confirm_stdout = (confirm_proc.stdout or "").strip()
            confirm_stderr = (confirm_proc.stderr or "").strip()
            confirm_payload = parse_stdout_json(confirm_stdout)

            if confirm_proc.returncode != 0:
                confirm_errors.append(f"expected exit 0, got {confirm_proc.returncode}")
            if not isinstance(confirm_payload, dict):
                confirm_errors.append("valid confirmation dry-run response is not JSON")
            else:
                if confirm_payload.get("ok") is not True:
                    confirm_errors.append("confirmed dry-run did not return ok=true")
                if confirm_payload.get("dry_run") is not True:
                    confirm_errors.append("confirmed dry-run did not return dry_run=true")
                if confirm_payload.get("would_execute") is not False:
                    confirm_errors.append("confirmed dry-run did not return would_execute=false")
                if confirm_payload.get("reason") != "environment_dry_run_enabled":
                    confirm_errors.append("confirmed dry-run did not preserve environment dry-run reason")

            pending_after_confirm = read_json(PENDING_CONFIRMATION_PATH)
            if not isinstance(pending_after_confirm, dict) or pending_after_confirm.get("consumed") is not True:
                confirm_errors.append("token was not marked consumed after successful confirmation")
        else:
            confirm_proc = subprocess.CompletedProcess([], 1, "", "")
            confirm_stdout = ""
            confirm_stderr = ""

        results.append(
            {
                "name": "confirmation_token_valid_consumed_dry_run",
                "ok": not confirm_errors,
                "returncode": confirm_proc.returncode,
                "stdout": confirm_stdout,
                "stderr": confirm_stderr,
                "errors": confirm_errors,
                "cmd": ["python3", str(AI_RUN), f"confirm {dry_live_token}" if dry_live_token else "confirm <missing-token>"],
            }
        )

        reuse_errors: list[str] = []
        if dry_live_token:
            reuse_proc = run_cmd(
                ["python3", str(AI_RUN), f"confirm {dry_live_token}"],
                {"BOND_ACTION_DRY_RUN": "1"},
            )
            reuse_stdout = (reuse_proc.stdout or "").strip()
            reuse_stderr = (reuse_proc.stderr or "").strip()
            reuse_payload = parse_stdout_json(reuse_stdout)

            if reuse_proc.returncode != 5:
                reuse_errors.append(f"expected exit 5, got {reuse_proc.returncode}")
            if not isinstance(reuse_payload, dict) or reuse_payload.get("error") != "confirmation_consumed":
                reuse_errors.append("expected confirmation_consumed on token reuse")
        else:
            reuse_proc = subprocess.CompletedProcess([], 1, "", "")
            reuse_stdout = ""
            reuse_stderr = ""
            reuse_errors.append("token creation failed; could not run token reuse test")

        results.append(
            {
                "name": "confirmation_token_reuse_fails",
                "ok": not reuse_errors,
                "returncode": reuse_proc.returncode,
                "stdout": reuse_stdout,
                "stderr": reuse_stderr,
                "errors": reuse_errors,
                "cmd": ["python3", str(AI_RUN), f"confirm {dry_live_token}" if dry_live_token else "confirm <missing-token>"],
            }
        )
    finally:
        restore_file(PENDING_CONFIRMATION_PATH, pending_existed, pending_before)

    return results


def run_memory_tests() -> list[dict]:
    results: list[dict] = []

    errors: list[str] = []
    try:
        ensure_memory_dirs()
        log_memory(
            "events",
            "selftest_event_bucket",
            {"source": "ai_selftest", "kind": "events_bucket_validation"},
        )
    except Exception as exc:
        errors.append(str(exc))

    results.append(
        {
            "name": "memory_events_bucket_accepts_log",
            "ok": not errors,
            "returncode": 0,
            "stdout": "events bucket accepted log" if not errors else "",
            "stderr": "",
            "errors": errors,
            "cmd": [
                "log_memory",
                "events",
                "selftest_event_bucket",
            ],
        }
    )

    key = "selftest_temp_key"
    value = "selftest_temp_value"

    fact_existed, fact_before = backup_file(TEST_FACT_BUCKET)
    try:
        proc = run_cmd(
            [
                "python3",
                str(AI_MEMORY),
                "set",
                "preferences",
                key,
                value,
                "--source",
                "selftest",
            ]
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        errors = []

        if proc.returncode != 0:
            errors.append(f"expected exit 0, got {proc.returncode}")
        if f"stored preferences.{key} = {value}" not in stdout:
            errors.append("missing set confirmation in stdout")

        data = read_json(TEST_FACT_BUCKET)
        if not isinstance(data, dict):
            errors.append("preferences.json is not valid JSON object after set")
        else:
            item = data.get(key)
            if not isinstance(item, dict):
                errors.append("selftest fact key missing after set")
            else:
                if item.get("value") != value:
                    errors.append("stored fact value mismatch")
                if item.get("source") != "selftest":
                    errors.append("stored fact source mismatch")

        results.append(
            {
                "name": "memory_set_fact",
                "ok": not errors,
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "errors": errors,
                "cmd": ["python3", str(AI_MEMORY), "set", "preferences", key, value, "--source", "selftest"],
            }
        )
    finally:
        restore_file(TEST_FACT_BUCKET, fact_existed, fact_before)

    actions_existed, actions_before = backup_file(TEST_ACTIONS_LOG)
    try:
        proc = run_cmd(
            [
                "python3",
                str(AI_MEMORY),
                "log",
                "actions",
                "selftest log entry",
                "--meta",
                '{"source":"selftest"}',
            ]
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        errors = []

        if proc.returncode != 0:
            errors.append(f"expected exit 0, got {proc.returncode}")
        if "logged to actions" not in stdout:
            errors.append("missing log confirmation in stdout")

        content = read_text(TEST_ACTIONS_LOG)
        if "selftest log entry" not in content:
            errors.append("log entry text not found in actions log")
        if '"source": "selftest"' not in content and '"source":"selftest"' not in content:
            errors.append("log meta not found in actions log")

        results.append(
            {
                "name": "memory_append_log",
                "ok": not errors,
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "errors": errors,
                "cmd": ["python3", str(AI_MEMORY), "log", "actions", "selftest log entry", "--meta", '{"source":"selftest"}'],
            }
        )
    finally:
        restore_file(TEST_ACTIONS_LOG, actions_existed, actions_before)

    archive_map_existed, archive_map_before = backup_file(TEST_ARCHIVE_MAP)
    reflections_existed, reflections_before = backup_file(TEST_REFLECTIONS_LOG)
    try:
        if not TEST_REFLECTIONS_LOG.exists():
            TEST_REFLECTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
            TEST_REFLECTIONS_LOG.write_text("", encoding="utf-8")

        proc = run_cmd(["python3", str(AI_MEMORY_ROTATE)])
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        errors = []

        if proc.returncode != 0:
            errors.append(f"expected exit 0, got {proc.returncode}")
        if "memory rotation complete" not in stdout and "rotation skipped:" not in stdout:
            errors.append("unexpected rotate stdout")

        archive_map = read_json(TEST_ARCHIVE_MAP)
        if archive_map is not None and not isinstance(archive_map, dict):
            errors.append("archive_map.json is not a JSON object after rotation")

        results.append(
            {
                "name": "memory_rotate_runs",
                "ok": not errors,
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "errors": errors,
                "cmd": ["python3", str(AI_MEMORY_ROTATE)],
            }
        )
    finally:
        restore_file(TEST_ARCHIVE_MAP, archive_map_existed, archive_map_before)
        restore_file(TEST_REFLECTIONS_LOG, reflections_existed, reflections_before)

    actions_existed2, actions_before2 = backup_file(TEST_ACTIONS_LOG)
    reflections_existed2, reflections_before2 = backup_file(TEST_REFLECTIONS_LOG)
    try:
        append_temp_jsonl_entry(
            TEST_ACTIONS_LOG,
            {
                "ts": "2099-01-01T00:00:00+00:00",
                "message": "selftest action seed",
                "meta": {"source": "selftest"},
            },
        )

        if not TEST_REFLECTIONS_LOG.exists():
            TEST_REFLECTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
            TEST_REFLECTIONS_LOG.write_text("", encoding="utf-8")

        proc = run_cmd(["python3", str(AI_MEMORY_REFLECT)])
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        errors = []

        if proc.returncode != 0:
            errors.append(f"expected exit 0, got {proc.returncode}")

        allowed_markers = [
            "reflection complete:",
            "no useful lessons produced",
            "no recent logs to reflect on",
            "reflection skipped:",
            "not enough new events",
            "no new events since last reflection",
            "recent failure activity",
            "sufficient new events",
            "reflection disabled by config",
        ]
        if not any(marker in stdout for marker in allowed_markers):
            errors.append("unexpected reflect stdout")

        results.append(
            {
                "name": "memory_reflect_runs",
                "ok": not errors,
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "errors": errors,
                "cmd": ["python3", str(AI_MEMORY_REFLECT)],
            }
        )
    finally:
        restore_file(TEST_ACTIONS_LOG, actions_existed2, actions_before2)
        restore_file(TEST_REFLECTIONS_LOG, reflections_existed2, reflections_before2)

    archive_map_existed2, archive_map_before2 = backup_file(TEST_ARCHIVE_MAP)
    try:
        fake_archive_root = MEMORY_ROOT
        old_actions = fake_archive_root / "actions_2000-01-01T00-00-00+00-00.jsonl"
        new_actions = fake_archive_root / "actions_2099-01-01T00-00-00+00-00.jsonl"
        old_snap = fake_archive_root / "facts_snapshot_2000-01-01T00-00-00+00-00.json"
        new_snap = fake_archive_root / "facts_snapshot_2099-01-01T00-00-00+00-00.json"

        created_paths = [old_actions, new_actions, old_snap, new_snap]
        for p in created_paths:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("selftest", encoding="utf-8")

        TEST_ARCHIVE_MAP.parent.mkdir(parents=True, exist_ok=True)
        TEST_ARCHIVE_MAP.write_text(
            json.dumps(
                {
                    "actions": [str(old_actions), str(new_actions)],
                    "facts_snapshots": [str(old_snap), str(new_snap)],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        proc = run_cmd(["python3", str(AI_MEMORY_ROTATE)])
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        errors = []

        if proc.returncode != 0:
            errors.append(f"expected exit 0, got {proc.returncode}")
        if "memory rotation complete" not in stdout:
            errors.append("unexpected rotate stdout during retention test")

        archive_map = read_json(TEST_ARCHIVE_MAP)
        if not isinstance(archive_map, dict):
            errors.append("archive_map.json invalid after retention test")
        else:
            actions_entries = archive_map.get("actions", [])
            snapshot_entries = archive_map.get("facts_snapshots", [])
            if len(actions_entries) > 2:
                errors.append("actions archive list grew unexpectedly during retention test")
            if len(snapshot_entries) > 2:
                errors.append("facts snapshot list grew unexpectedly during retention test")

        for p in created_paths:
            if not p.exists():
                # pruning is allowed only for oldest beyond configured keep count
                pass

        results.append(
            {
                "name": "memory_retention_runs",
                "ok": not errors,
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "errors": errors,
                "cmd": ["python3", str(AI_MEMORY_ROTATE)],
            }
        )
    finally:
        restore_file(TEST_ARCHIVE_MAP, archive_map_existed2, archive_map_before2)
        for p in [
            MEMORY_ROOT / "actions_2000-01-01T00-00-00+00-00.jsonl",
            MEMORY_ROOT / "actions_2099-01-01T00-00-00+00-00.jsonl",
            MEMORY_ROOT / "facts_snapshot_2000-01-01T00-00-00+00-00.json",
            MEMORY_ROOT / "facts_snapshot_2099-01-01T00-00-00+00-00.json",
        ]:
            if p.exists():
                p.unlink()


    fact_existed3, fact_before3 = backup_file(TEST_FACT_BUCKET)
    actions_existed3, actions_before3 = backup_file(TEST_ACTIONS_LOG)
    changelog_existed3, changelog_before3 = backup_file(CHANGELOG_PATH)
    archive_map_existed3, archive_map_before3 = backup_file(TEST_ARCHIVE_MAP)
    try:
        TEST_FACT_BUCKET.parent.mkdir(parents=True, exist_ok=True)
        TEST_FACT_BUCKET.write_text(
            json.dumps(
                {
                    "retrieval_policy": {
                        "value": "confirmed facts outrank changelog and logs for current state",
                        "updated_at": "2099-01-01T00:00:00+00:00",
                        "source": "selftest_fact",
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        TEST_ACTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
        TEST_ACTIONS_LOG.write_text(
            json.dumps(
                {
                    "ts": "2099-01-01T00:00:00+00:00",
                    "message": "retrieval policy discussed in action log",
                    "meta": {"source": "selftest_log"},
                },
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

        CHANGELOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CHANGELOG_PATH.write_text(
            json.dumps(
                {
                    "ts": "2099-01-01T00:00:00+00:00",
                    "message": "recent retrieval policy change noted in changelog",
                    "files": [str(SRC_BOND / "ai_memory_query.py")],
                    "change_kind": "code",
                    "diff_preview": "retrieval policy adjusted",
                },
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

        TEST_ARCHIVE_MAP.parent.mkdir(parents=True, exist_ok=True)
        TEST_ARCHIVE_MAP.write_text(
            json.dumps(
                {"history": [str(MEMORY_ROOT / "archive" / "retrieval_policy_old.json")]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        payload, proc = read_query_json("what is the current retrieval policy")
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        errors = []

        if proc.returncode != 0:
            errors.append(f"expected exit 0, got {proc.returncode}")
        if not isinstance(payload, dict):
            errors.append("memory query did not return valid JSON payload")
        else:
            hits = payload.get("hits", [])
            if not hits:
                errors.append("memory query returned no hits")
            else:
                if hits[0].get("source_type") != "fact":
                    errors.append("top hit was not a fact for current-state retrieval query")

            summary = payload.get("evidence_summary", {})
            confirmed_current = summary.get("confirmed_current", [])
            if not confirmed_current:
                errors.append("confirmed_current summary is empty")
            if any("archive" in entry.lower() for entry in confirmed_current):
                errors.append("archive reference leaked into confirmed_current summary")

        results.append(
            {
                "name": "memory_query_prefers_fact_for_current_state",
                "ok": not errors,
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "errors": errors,
                "cmd": ["python3", str(AI_MEMORY_QUERY), "what is the current retrieval policy", "--json"],
            }
        )
    finally:
        restore_file(TEST_FACT_BUCKET, fact_existed3, fact_before3)
        restore_file(TEST_ACTIONS_LOG, actions_existed3, actions_before3)
        restore_file(CHANGELOG_PATH, changelog_existed3, changelog_before3)
        restore_file(TEST_ARCHIVE_MAP, archive_map_existed3, archive_map_before3)

    fact_existed4, fact_before4 = backup_file(TEST_FACT_BUCKET)
    changelog_existed4, changelog_before4 = backup_file(CHANGELOG_PATH)
    archive_map_existed4, archive_map_before4 = backup_file(TEST_ARCHIVE_MAP)
    try:
        TEST_FACT_BUCKET.parent.mkdir(parents=True, exist_ok=True)
        TEST_FACT_BUCKET.write_text(
            json.dumps(
                {
                    "router_config": {
                        "value": "~/project/config/router/profiles.json",
                        "updated_at": "2099-01-01T00:00:00+00:00",
                        "source": "selftest_fact",
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        CHANGELOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CHANGELOG_PATH.write_text(
            json.dumps(
                {
                    "ts": "2099-01-01T00:00:00+00:00",
                    "message": "router config changed in recent changelog entry",
                    "files": ["~/project/config/router/profiles.json"],
                    "change_kind": "code",
                    "diff_preview": "router config path updated",
                },
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

        TEST_ARCHIVE_MAP.parent.mkdir(parents=True, exist_ok=True)
        TEST_ARCHIVE_MAP.write_text(
            json.dumps(
                {"router_history": [str(MEMORY_ROOT / "archive" / "router_config_old.json")]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        payload, proc = read_query_json("what is my current router config path")
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        errors = []

        if proc.returncode != 0:
            errors.append(f"expected exit 0, got {proc.returncode}")
        if not isinstance(payload, dict):
            errors.append("memory query did not return valid JSON payload")
        else:
            summary = payload.get("evidence_summary", {})
            uncertainty = summary.get("uncertainty", [])
            if not any("historical clues" in entry for entry in uncertainty):
                errors.append("archive uncertainty warning missing for non-history query with archive hit")

            hits = payload.get("hits", [])
            if not hits:
                errors.append("memory query returned no hits")
            else:
                if hits[0].get("source_type") == "archive":
                    errors.append("archive incorrectly outranked current-state sources")

        results.append(
            {
                "name": "memory_query_demotes_archive_for_current_state",
                "ok": not errors,
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "errors": errors,
                "cmd": ["python3", str(AI_MEMORY_QUERY), "what is my current router config path", "--json"],
            }
        )
    finally:
        restore_file(TEST_FACT_BUCKET, fact_existed4, fact_before4)
        restore_file(CHANGELOG_PATH, changelog_existed4, changelog_before4)
        restore_file(TEST_ARCHIVE_MAP, archive_map_existed4, archive_map_before4)

    return results


def run_active_path_sanitation_tests() -> list[dict]:
    hits: list[str] = []

    for target in ACTIVE_SANITATION_PATHS:
        if not target.exists():
            continue

        if target.is_dir():
            files = [p for p in target.rglob("*") if p.is_file()]
        else:
            files = [target]

        for file_path in files:
            if "__pycache__" in file_path.parts:
                continue
            if file_path.suffix == ".pyc":
                continue

            text = file_path.read_text(encoding="utf-8", errors="ignore")
            for marker in ACTIVE_SANITATION_MARKERS:
                if marker in text:
                    rel = file_path.relative_to(BOND_ROOT)
                    hits.append(f"{rel}: contains '{marker}'")

    return [
        {
            "name": "active_scope_has_no_personal_path_markers",
            "ok": not hits,
            "returncode": 0 if not hits else 1,
            "stdout": "\n".join(hits),
            "stderr": "",
            "errors": hits,
            "cmd": ["internal:active_path_sanitation_scan"],
        }
    ]


def main() -> None:
    required = [
        AI_RUN,
        AI_EXEC,
        AI_CONFIRMATION,
        AI_PARSE_CONTRACT,
        AI_WRAPPER,
        AI_MEMORY,
        AI_MEMORY_QUERY,
        AI_MEMORY_REFLECT,
        AI_MEMORY_ROTATE,
    ]
    for path in required:
        if not path.exists():
            print(f"missing: {path}")
            raise SystemExit(2)

    passed = 0
    failed = 0

    for case in build_core_test_cases():
        ok, result = evaluate_case(case)
        if ok:
            passed += 1
            print(f"[PASS] {case.name}")
        else:
            failed += 1
            print(f"[FAIL] {case.name}")
            for err in result["errors"]:
                print(f"  - {err}")
            print_block("stdout", result["stdout"])
            print_block("stderr", result["stderr"])

    for result in run_router_tests():
        if result["ok"]:
            passed += 1
            print(f"[PASS] {result['name']}")
        else:
            failed += 1
            print(f"[FAIL] {result['name']}")
            for err in result["errors"]:
                print(f"  - {err}")
            print_block("stdout", result["stdout"])
            print_block("stderr", result["stderr"])

    for result in run_router_profile_tests():
        if result["ok"]:
            passed += 1
            print(f"[PASS] {result['name']}")
        else:
            failed += 1
            print(f"[FAIL] {result['name']}")
            for err in result["errors"]:
                print(f"  - {err}")
            print_block("stdout", result["stdout"])
            print_block("stderr", result["stderr"])

    for result in run_policy_tests():
        if result["ok"]:
            passed += 1
            print(f"[PASS] {result['name']}")
        else:
            failed += 1
            print(f"[FAIL] {result['name']}")
            for err in result["errors"]:
                print(f"  - {err}")
            print_block("stdout", result["stdout"])
            print_block("stderr", result["stderr"])

    for result in run_action_contract_tests():
        if result["ok"]:
            passed += 1
            print(f"[PASS] {result['name']}")
        else:
            failed += 1
            print(f"[FAIL] {result['name']}")
            for err in result["errors"]:
                print(f"  - {err}")
            print_block("stdout", result["stdout"])
            print_block("stderr", result["stderr"])

    for result in run_capability_registry_tests():
        if result["ok"]:
            passed += 1
            print(f"[PASS] {result['name']}")
        else:
            failed += 1
            print(f"[FAIL] {result['name']}")
            for err in result["errors"]:
                print(f"  - {err}")
            print_block("stdout", result["stdout"])
            print_block("stderr", result["stderr"])

    for result in run_parse_contract_tests():
        if result["ok"]:
            passed += 1
            print(f"[PASS] {result['name']}")
        else:
            failed += 1
            print(f"[FAIL] {result['name']}")
            for err in result["errors"]:
                print(f"  - {err}")
            print_block("stdout", result["stdout"])
            print_block("stderr", result["stderr"])

    for result in run_selftest_mode_tests():
        if result["ok"]:
            passed += 1
            print(f"[PASS] {result['name']}")
        else:
            failed += 1
            print(f"[FAIL] {result['name']}")
            for err in result["errors"]:
                print(f"  - {err}")
            print_block("stdout", result["stdout"])
            print_block("stderr", result["stderr"])

    for result in run_confirmation_token_tests():
        if result["ok"]:
            passed += 1
            print(f"[PASS] {result['name']}")
        else:
            failed += 1
            print(f"[FAIL] {result['name']}")
            for err in result["errors"]:
                print(f"  - {err}")
            print_block("stdout", result["stdout"])
            print_block("stderr", result["stderr"])

    for result in run_memory_tests():
        if result["ok"]:
            passed += 1
            print(f"[PASS] {result['name']}")
        else:
            failed += 1
            print(f"[FAIL] {result['name']}")
            for err in result["errors"]:
                print(f"  - {err}")
            print_block("stdout", result["stdout"])
            print_block("stderr", result["stderr"])

    for result in run_active_path_sanitation_tests():
        if result["ok"]:
            passed += 1
            print(f"[PASS] {result['name']}")
        else:
            failed += 1
            print(f"[FAIL] {result['name']}")
            for err in result["errors"]:
                print(f"  - {err}")
            print_block("stdout", result["stdout"])
            print_block("stderr", result["stderr"])

    summary = {
        "ok": failed == 0,
        "passed": passed,
        "failed": failed,
        "total": passed + failed,
    }

    print("\n=== summary ===")
    print(json.dumps(summary, ensure_ascii=False))

    if failed != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
