# Bond Documentation Gap Analysis and Detailed Implementation Blueprint

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Scope

This document is a critical analysis of the current Bond repository and transcript-derived direction, plus a concrete implementation blueprint for the next serious documentation and project-management pass.

It is intentionally opinionated.

The goal is not to praise the current state.
The goal is to identify what is still under-specified, what is still missing, and what should be written into the repository so the repo can actually replace transcript dependence.

---

## Executive judgment

The repo is **better structured than before**, but it is still **under-documented in the places that matter most operationally**.

The project currently has a strong *doctrinal shell* and a weak *execution-grade documentation core*.

In plain terms:

- The docs are good at stating principles.
- They are weaker at specifying exact implementation contracts.
- The repo shape exists, but the project-management metadata in Gitea is almost empty.
- The current docs help an LLM understand intent, but they still do not let a new human or another agent execute the whole project with low ambiguity.
- The master plan is wide, but many sections still stop at “what” and do not reach “exactly how”.

That means the documentation has crossed the line from **transcript blob** to **document set**, but not yet to **true project operating system**.

---

## What is already solid

These parts are genuinely good and should be preserved:

1. **Repository-first direction**
   - The repo is clearly being treated as the canonical source tree.
   - Runtime/state separation has at least been recognized and partially implemented.

2. **Split docs for LLM readability**
   - Breaking the monolithic transcript into scoped docs was the right move.
   - The current set is easier for another LLM to follow than one giant historical transcript.

3. **Architecture philosophy**
   - The parse → classify → policy → execute separation is the right direction.
   - The insistence on capability honesty is exactly correct.

4. **Behavioral realism**
   - The transcript and term output are not pretending the assistant is further along than it is.
   - The failure evidence is strong and useful.

5. **Master-plan breadth**
   - The project already names the major end-state layers: package, CLI, service, applet, voice, optional MCP.
   - That is better than building blindly.

---

## What is still weak

### 1. README is too thin

Current README is a stub, not a serious front door.

What is missing:
- no architecture summary
- no supported / unsupported capability table
- no install modes
- no quickstart
- no development workflow
- no test commands section
- no screenshots / UI status
- no roadmap snapshot
- no repo status warning
- no “why Bond exists”
- no “what Bond is not”
- no “who this repo is for”
- no link map into docs
- no current state badge/checkpoint concept

Consequence:
- a new human lands in the repo and learns almost nothing operationally
- Gitea’s right-side repo description area is empty, making the repo look unmaintained
- the README does not function as either a user-facing or contributor-facing entry point

### 2. CHANGELOG is too shallow

The changelog is closer to a checkpoint note than a proper changelog.

What is missing:
- version discipline
- release headings
- date discipline
- scope segmentation (Added / Changed / Fixed / Deprecated / Removed / Security)
- links to matching issues/milestones
- clear distinction between repo changes and runtime/live experiments
- stable rule for when a change belongs in CHANGELOG versus docs/reports versus commit history

Consequence:
- the changelog cannot yet support release notes
- “what changed?” still depends too much on chat and transcript memory

### 3. ROADMAP is nearly empty

The file exists, but in its current state it is not useful enough.

What is missing:
- milestone names
- dependency order
- phase exit criteria
- issue-group mapping
- which phases are blocked by which earlier phases
- what is optional versus mandatory
- ownership of docs vs code work
- measurable deliverables

Consequence:
- the real roadmap currently lives in `docs/BOND_PROJECT_MASTER_PLAN.md`, while `ROADMAP.md` contributes almost nothing
- this split is okay only if ROADMAP becomes a concise roadmap index, which it currently is not

### 4. INSTALLATION is honest but transitional to a fault

The document is honest about instability, which is good.
But it still over-describes a setup path that you already know is not the intended final model.

What is missing:
- explicit distinction between:
  - developer install
  - local user install
  - future packaged install
- editable install guidance
- console entry point plan
- uninstall contract
- upgrade contract
- configuration precedence
- runtime directories and what is created where
- example `.env` or config bootstrapping
- service-install path versus CLI-only path
- clean statement of what is safe to delete

Consequence:
- the current installation doc tells the truth, but it still does not define the install lifecycle strongly enough

### 5. ARCHITECTURE is conceptually strong but under-specified at interface level

The architecture doc names modules well.
But it still under-documents the interfaces between them.

What is missing:
- canonical data structures passed between parse, policy, and exec
- required fields for parse result objects
- policy decision schema
- execution result schema
- capability registry schema
- error taxonomy
- telemetry schema
- correction-ingestion schema
- boundaries on model calls vs deterministic calls

Consequence:
- another developer or LLM still has to infer too much
- architecture is descriptive, not yet contract-driven

### 6. BEHAVIOR_CONTRACT is necessary but still incomplete

It correctly defines many “must not” rules.
But it still lacks a full answer matrix for assistant behavior.

What is missing:
- exact handling rules for:
  - unsupported action
  - blocked dangerous action
  - ambiguous target
  - mixed-intent request
  - partial capability
  - question + imperative hybrids
  - wake word only
  - nonsense input
  - greeting only
  - uncertainty statements
- examples for Greek and bilingual prompts
- expected answer style for:
  - plain question
  - action refusal
  - action success
  - info request using probes
  - speculative request
- rules on when to ask clarifying questions versus reject versus answer partially

Consequence:
- behavior doctrine exists, but not as an executable contract suite specification

### 7. CURRENT_PATHS is useful but still transitional

This doc helps during migration, but it still reflects a halfway house.

What is missing:
- canonical directory map by deployment mode
- clear distinction between:
  - repository paths
  - runtime paths
  - config paths
  - archive paths
  - user-local cache/state paths
- path ownership table (“tracked”, “generated”, “user-editable”, “safe to delete”, “must persist”)
- XDG transition map
- install-time path resolution algorithm
- migration table from old `<legacy-runtime-root>` layout to repo/runtime layout

Consequence:
- it helps the current migration, but it does not yet define the end-state path contract clearly enough

### 8. TESTING is too high-level

Current testing docs correctly admit the limits of the 18 selftests.
That is good.
But the file still lacks the actual test architecture.

What is missing:
- test layers
- test directories and naming rules
- unit vs behavior vs regression vs smoke vs integration taxonomy
- command matrix
- CI target matrix
- fixture strategy
- mocked probe strategy
- golden-output strategy
- behavioral failure corpus based on the term output
- required pre-commit or pre-push checks

Consequence:
- testing doctrine exists, but testing implementation guidance is still sparse

### 9. STATE is too short

This file is not wrong.
It is just not sufficient.

What is missing:
- current checkpoint date
- current known working commands
- current known broken behaviors
- current highest-risk modules
- current blocker list
- current branch strategy
- current release readiness statement
- “what changed since last checkpoint”

Consequence:
- `STATE.md` does not yet function as a real status board

### 10. Master plan still has implementation holes

This is the big one.

The master plan is the best document in the set, but it still underspecifies many real implementation decisions.
The user’s criticism here is correct.

Where it is still too abstract:
- memory ingestion
- correction learning
- system probe layer
- capability registry schema
- parser output schema
- policy output schema
- telemetry implementation
- service IPC contract
- applet integration transport
- voice pipeline lifecycle
- release/versioning strategy
- packaging backend specifics
- uninstall/migration discipline
- issue decomposition

Consequence:
- it is a strong strategic doc, but not yet a build-grade blueprint

---

## Gitea state: currently underused

From the repo screens you supplied, Gitea currently shows:

- no repository description
- no issues
- no milestones
- no releases
- no wiki pages
- essentially no project-management metadata

That is a waste of the platform.

Gitea supports project-management and release features including issues, milestones, dependencies, due dates, assignments, and more. It also supports a wiki and releases. That means there is no technical reason to keep planning trapped in markdown files alone. citeturn424075view0

The mistake to avoid is the opposite extreme:
**do not move canonical engineering truth into the wiki.**
Keep canonical truth in-repo.
Use Gitea metadata to make the work navigable.

Correct split:
- **repo docs** = canonical truth
- **issues** = actionable work items
- **milestones** = grouped delivery checkpoints
- **releases** = versioned snapshots
- **wiki** = lightweight human-oriented overview / onboarding / FAQ, optionally mirrored from repo docs

---

## Critical conclusion

Right now the documentation set is **good enough to brief an aligned LLM**, but **not yet strong enough to operate as the project’s full memory, contract, and build plan without the transcript**.

That is the real gap.

The next pass should not be “write more docs”.
It should be:

1. convert broad doctrine into exact contracts
2. convert vague plans into issue-grade deliverables
3. populate Gitea so the repo has visible working structure
4. define implementation details for every major subsystem
5. reduce transcript dependence aggressively

---

# Detailed implementation blueprint

## A. Repository metadata and Gitea population

## A1. Repository description

Set a real repo description in Gitea.

Recommended description:
> Local-first AI assistant for Linux Mint with guarded actions, deterministic system probes, structured memory, and repo-first architecture.

Why:
- short
- accurate
- not hype
- communicates the project’s real differentiator

## A2. Topics

Suggested topics/tags:
- ai-assistant
- local-first
- linux-mint
- python
- offline-ai
- system-automation
- memory-system
- deterministic-tools
- gitea
- cinnamon

## A3. Wiki strategy

Create the wiki, but keep it deliberately small.

Recommended first wiki pages:
1. `Home`
2. `Quick Start`
3. `Project Glossary`
4. `Architecture Snapshot`
5. `Status and Priorities`
6. `FAQ`

Rule:
- Wiki may summarize.
- Wiki must not become the deeper canonical source.
- Every wiki page should link back to the matching repo doc.

## A4. Issue labels

Create labels before issues.

Suggested label set:

### Area labels
- area:architecture
- area:parser
- area:policy
- area:execution
- area:memory
- area:probes
- area:docs
- area:packaging
- area:service
- area:applet
- area:voice
- area:tests
- area:gitea-workflow

### Type labels
- type:bug
- type:design
- type:feature
- type:docs
- type:refactor
- type:test
- type:chore

### Priority labels
- priority:P0
- priority:P1
- priority:P2
- priority:P3

### Status/risk labels
- status:blocked
- status:needs-spec
- status:ready
- status:in-progress
- status:needs-validation
- risk:safety
- risk:behavior
- risk:regression

## A5. Milestones

Recommended milestone structure:

### M0 — Repository and documentation hardening
Goal:
- README, roadmap, changelog, state, install, docs index, Gitea population

Exit criteria:
- repo front page no longer looks empty
- issues/milestones populated
- docs cover current reality better than transcript for repo structure

### M1 — Invocation and packaging baseline
Goal:
- remove hardcoded wrapper roots
- define editable install
- define console entry point
- define install/update/uninstall lifecycle

Exit criteria:
- `bond` command works from installed package or editable install
- wrapper drift removed

### M2 — Capability truth and policy gate
Goal:
- implement capability registry and formal policy gate

Exit criteria:
- unsupported actions described truthfully
- dangerous action handling centralized
- mixed-intent rules deterministic

### M3 — Parser and target resolution repair
Goal:
- eliminate guessy target mapping and lexical hijacking

Exit criteria:
- “open internet” no longer resolves to nonsense
- ambiguity behavior consistent
- bilingual/wake handling specified

### M4 — System probe layer and telemetry
Goal:
- move environment truth to deterministic probes
- add truthful timing and execution metadata

Exit criteria:
- current shell, cwd, packages, path, and environment answers come from probes
- telemetry fields exist and are documented

### M5 — Memory discipline and correction ingestion
Goal:
- formalize memory schemas and user correction pipeline

Exit criteria:
- correction entries stored separately and retrievable
- current-truth vs archive-truth clearly enforced

### M6 — Behavior test expansion
Goal:
- convert transcript failures into behavioral regression suite

Exit criteria:
- failure corpus exists
- behavior tests cover honesty, safety, ambiguity, mixed intent, lexical hijacks

### M7 — Optional service layer
Goal:
- define and implement user-level daemon mode

Exit criteria:
- user service documented and controlled through systemd user service

### M8 — Cinnamon applet baseline
Goal:
- minimal applet with status, text submission, recent response display, quick actions

Exit criteria:
- applet does not duplicate core logic
- applet talks over a defined boundary

### M9 — Offline voice layer
Goal:
- optional STT/TTS path with explicit enablement

Exit criteria:
- voice remains optional
- core text path remains primary and stable

## A6. Releases

Do not create fake releases yet.
But do prepare the release structure.

Gitea supports releases; use them only when there is a meaningful checkpoint, not as decorative emptiness. citeturn424075view0

Recommended early tags/releases:
- `v0.1.0-docs-foundation`
- `v0.2.0-cli-baseline`
- `v0.3.0-policy-core`
- `v0.4.0-probe-and-memory-contracts`

## A7. Issue templates

Create issue templates for:
- bug report
- design/spec proposal
- docs gap
- behavior regression
- implementation task

---

## B. README redesign

The README should be rewritten into these sections:

1. **What Bond is**
2. **What Bond is not**
3. **Current state**
4. **Key design principles**
5. **Current capabilities**
6. **Known limitations**
7. **Quickstart**
8. **Developer setup**
9. **Project layout**
10. **Documentation map**
11. **Milestones / roadmap**
12. **Contributing workflow**
13. **Safety philosophy**
14. **License / status**

Add a capability table like this:

| Capability | State | Notes |
|---|---|---|
| Natural language CLI | Partial | Current behavior still inconsistent |
| Safe deterministic open actions | Partial | Known-target actions exist; ambiguity still weak |
| System probes | Partial | Must be expanded and centralized |
| Memory retrieval | Partial | Better on project facts than on general assistant behavior |
| Correction learning | Planned | Schema and ingestion path not complete |
| Voice | Planned | Later optional layer |
| Cinnamon applet | Planned | Not immediate |
| Package install / CLI entry point | Partial | Transitional wrappers still present |

Do not let the README pretend the project is polished.
But also do not leave it skeletal.

---

## C. Packaging and CLI implementation details

Current `pyproject.toml` is not enough.
The Python Packaging User Guide strongly recommends a `[build-system]` table and uses `[project]` for package metadata. Console commands are best exposed as `console_scripts` entry points rather than ad hoc wrappers. citeturn424075view1turn424075view2

### C1. Packaging backend

Use:
- setuptools initially
- src layout stays
- editable install during development
- wheel later when needed

Recommended shape:
- `[build-system]` with setuptools and wheel
- `[project]` with metadata
- `[project.scripts]`
  - `bond = "bond.cli:main"`
  - `bond-selftest = "bond.ai_selftest:main"` only if a clean `main()` exists
  - `bond-scan-system = "bond.ai_scan_system:main"` if matured

### C2. CLI entrypoint architecture

Create a real `bond/cli.py`:
- parse argv
- normalize interactive vs one-shot mode
- call orchestrator
- support subcommands later

Initial CLI modes:
- `bond "hello"`
- `bond ask "what model are you using"`
- `bond run "open downloads"` (optional later, only if semantics justify it)
- `bond selftest`
- `bond scan-system`

Do **not** keep Bash wrappers as final architecture.
They can remain transitional helpers only.

### C3. Install modes

Document three install modes:

1. **Developer editable install**
   - `pip install -e .`
   - best for active repo work

2. **Local user install**
   - package installed into virtualenv or pipx-like isolated environment
   - exposes `bond` on path

3. **Future packaged install**
   - deb/flatpak/other later
   - explicitly not current

### C4. Update lifecycle

Document:
- pull repo
- update venv/dependencies
- rerun smoke tests
- restart service if enabled

### C5. Uninstall lifecycle

Document:
- remove installed package / venv
- remove optional user service
- remove optional runtime dirs if user explicitly wants to delete state
- preserve or archive memory by default

---

## D. Architecture contracts: exact schemas

This is one of the biggest missing pieces.

## D1. Parse result schema

Define a canonical dataclass or typed dict.

Example fields:
- `raw_text: str`
- `normalized_text: str`
- `wake_invoked: bool`
- `language_hint: Literal["en","el","mixed","unknown"]`
- `intent_candidates: list[str]`
- `action_candidates: list[ActionCandidate]`
- `question_candidates: list[QuestionCandidate]`
- `explicit_paths: list[str]`
- `named_targets: list[str]`
- `ambiguity_flags: list[str]`
- `safety_flags: list[str]`
- `noise_flags: list[str]`

### ActionCandidate
- `verb`
- `object_text`
- `target_label`
- `is_explicit_path`
- `confidence`
- `source_span`
- `modifiers`

Parser rule:
- parser may extract
- parser may normalize
- parser may not approve

## D2. Policy decision schema

Example:
- `status: Literal["approved","rejected","clarify","unsupported","blocked","mixed"]`
- `action_class`
- `reason_code`
- `user_message`
- `approved_target`
- `approved_command`
- `risk_level`
- `requires_confirmation`
- `telemetry_tags`

### Suggested reason codes
- `unknown_target`
- `ambiguous_target`
- `unsupported_capability`
- `blocked_path`
- `dangerous_action`
- `mixed_intent_request`
- `missing_probe`
- `requires_confirmation`
- `not_implemented`

## D3. Execution result schema

Example:
- `ok: bool`
- `action_class`
- `executor`
- `started_at`
- `ended_at`
- `duration_ms`
- `stdout`
- `stderr`
- `exit_code`
- `artifact_paths`
- `user_summary`
- `probe_used`
- `side_effects`

## D4. Capability registry schema

Implement a central capability registry.

Each capability entry should define:
- `name`
- `category`
- `status` (`supported`, `partial`, `planned`, `blocked`)
- `execution_mode` (`deterministic`, `probe`, `llm-only`, `none`)
- `risk_level`
- `requires_confirmation`
- `required_tools`
- `notes`
- `test_ids`

Examples:
- `open_known_target`
- `open_explicit_allowed_path`
- `query_current_shell`
- `query_current_directory`
- `query_weather`
- `timer`
- `notification`
- `screenshot`
- `clipboard_read`
- `wifi_connect`

This registry should power:
- self-description
- policy decisions
- docs tables
- test expectations

---

## E. System probe layer: detailed implementation

Right now this area is under-planned.

## E1. Probe design principle

System facts must come from deterministic probes, not from the model.

Probe outputs should be:
- structured
- cacheable when appropriate
- timestamped
- attributable to commands or APIs

## E2. Probe categories

### Environment probes
- current shell
- cwd
- PATH
- username
- hostname
- desktop session
- distro/version
- XDG paths

### Package/tool probes
- installed package inventory
- command availability (`shutil.which`, `command -v`)
- Python version
- Ollama availability
- Docker availability
- systemd availability
- app availability

### Runtime assistant probes
- current assistant config
- router profile path
- model roster
- active/default model
- memory roots
- archive root

### Session/device probes
- audio sink state
- Bluetooth state
- network interface status
- battery/power state
- display/session type

## E3. Probe module structure

Recommended files:
- `bond/probes/base.py`
- `bond/probes/environment.py`
- `bond/probes/packages.py`
- `bond/probes/runtime.py`
- `bond/probes/session.py`
- `bond/probes/models.py`

Each probe returns a typed result:
- `ok`
- `source`
- `timestamp`
- `data`
- `errors`

## E4. Probe registry

Maintain a registry mapping user-facing info requests to probes:
- “what shell am I using” -> `environment.current_shell`
- “what is my current directory” -> `environment.cwd`
- “what packages are installed” -> `packages.installed`
- “what model are you using” -> `runtime.active_model`

## E5. Probe safety

Not every shell command should be allowed.
Create approved probe wrappers rather than raw command pass-through.

---

## F. Memory system: detailed implementation

The transcript is correct that “improve memory” is too vague.
This must be broken down.

## F1. Memory record types

Define explicit record classes:

1. **Fact**
   - stable current truth
2. **Log**
   - event record
3. **Correction**
   - user-supplied correction to a previous assistant statement or stored fact
4. **Reflection**
   - synthesized summary
5. **Archive entry**
   - rotated historical record

## F2. Fact schema

Suggested fields:
- `id`
- `timestamp`
- `subject`
- `predicate`
- `object`
- `scope`
- `confidence`
- `source_kind`
- `source_ref`
- `current_truth: bool`
- `tags`

## F3. Correction schema

This is missing today and should be added.

Suggested fields:
- `id`
- `timestamp`
- `user_text`
- `corrected_claim`
- `replacement_claim`
- `domain`
- `applies_to` (fact ids / topics / capability names)
- `verification_state` (`user-asserted`, `verified`, `disputed`)
- `use_priority`

This matters because a user correction is not always the same as a globally verified fact.

## F4. Retrieval ranking

Define ranking rules explicitly:

For **current-state questions**:
1. verified current facts
2. unverified current facts
3. relevant corrections
4. recent logs
5. reflections
6. archive

For **history questions**:
1. logs
2. archive
3. reflections
4. facts if they describe dated states

## F5. Correction ingestion flow

When user says:
- “what you said was wrong”
- “remember this instead”
- “that is outdated”
- “the correct path is…”

Pipeline:
1. detect correction intent
2. extract old claim / new claim if possible
3. prompt for clarification only if extraction is insufficient
4. write correction record
5. optionally update linked fact if high confidence
6. mark stale fact superseded, not silently deleted
7. surface correction in future retrieval where relevant

## F6. User-supplied learning drop folder

Detailed plan:
- create an ingestion directory for intentional learning files
- separate it from automatic runtime memory
- maintain manifest of ingested files
- require explicit ingest action or scheduled batch job
- record provenance for each derived fact

This is much better than pretending all files in the environment should be learned automatically.

---

## G. Action parsing and policy: detailed implementation

## G1. Action classes

Formalize these:

- `informational_probe`
- `safe_known_action`
- `safe_explicit_path_action`
- `ambiguous_action`
- `unsupported_action`
- `blocked_action`
- `dangerous_action`
- `mixed_intent`
- `pure_conversation`
- `wake_only`
- `nonsense_or_low_signal`

## G2. Mixed-intent rule

Do not rely on vibe.

Policy:
- if request contains more than one independent imperative or action+question combo that would require separate handling, either:
  - reject with a split instruction, or
  - in future, support structured multi-step execution explicitly
- until then, default to rejection with explanation

## G3. Clarification rule

Use clarification only when:
- exactly one key ambiguity blocks a safe likely-intended action
- the action is otherwise supported and safe

Reject instead when:
- multiple ambiguities
- dangerous domain
- unsupported capability
- mixed intent

## G4. Dangerous actions

Document explicit classes:
- delete/remove/erase
- kill/process termination
- shutdown/reboot
- chmod/chown/write to system paths
- network reconfiguration
- package installs/removals
- clipboard exfiltration
- screenshots/recording without explicit supported implementation

Each dangerous class needs:
- default policy
- confirmation rule
- current support state
- future enablement conditions

---

## H. Natural language and Greek support

This area needs real planning, not just “add Greek later”.

## H1. Invocation normalization

Create a dedicated normalization layer for:
- `bond`
- `Bond`
- `BOND`
- `hey bond`
- `μποντ`
- `Μποντ`
- `ΜΠΟΝΤ`
- `Μπόντ`

Normalize repeated invocations:
- `bond bond open downloads`

Strip wake forms without destroying meaning.

## H2. Language resources

Keep these outside the orchestrator:
- wake words
- common verbs
- common target synonyms
- greeting sets
- small-talk patterns
- rejection phrasing
- clarification templates

Separate files:
- `bond/lang/en.py`
- `bond/lang/el.py`
- `bond/lang/common.py`

## H3. Greek target aliases

Document mappings such as:
- λήψεις -> downloads
- επιφάνεια εργασίας -> desktop
- αρχική / σπίτι -> home
- ρυθμίσεις -> settings

These must not live as hidden heuristics inside `ai_run.py`.

## H4. Nonsense / low-signal handling

Examples:
- “test”
- “path test”
- “memory test”
- “this is only a test”

Policy:
- do not hijack into project mode
- answer minimally or ask what the user wants
- only enter project/testing mode when syntax clearly indicates it

---

## I. Telemetry and “thinking time”

This requirement is valid, but it must not turn into fake reasoning theater.

## I1. Telemetry fields

For each response track:
- `received_at`
- `response_started_at`
- `response_finished_at`
- `total_latency_ms`
- `probe_time_ms`
- `model_time_ms`
- `execution_time_ms`
- `path_taken` (`conversation`, `probe`, `action`, `memory`, `mixed`)
- `model_name`
- `used_memory`
- `used_probe`
- `used_execution`

## I2. User-visible output

Optional compact user-facing footer or structured verbose mode:
- `Mode: probe`
- `Model: qwen2.5:7b-instruct`
- `Latency: 842 ms`
- `Probe time: 40 ms`

Do not show hidden chain-of-thought.
Do show truthful timings.

## I3. Logging

Use structured logging, not free-text dumps.
The master plan is right to prefer structured logging here.

---

## J. Service and IPC layer

This also needs concrete definition.

A user-level systemd service is a sensible direction for an optional always-on mode because systemd service units are the standard way to supervise long-running processes on Linux. systemd’s own documentation defines `.service` units as the way to describe and supervise processes, and user manager instances exist for per-user services. citeturn437286search1turn437286search5

## J1. Service purpose

Only add a daemon when it solves a real problem:
- warm model/router state
- faster repeated interactions
- applet integration
- shared memory/session state
- background ingestion

## J2. IPC boundary options

Prefer this order:
1. local Unix socket
2. localhost HTTP only if necessary
3. DBus only if there is a strong desktop integration reason

For now:
- Unix socket is simpler and tighter

## J3. Service responsibilities

- accept structured request
- return structured response
- own session cache
- expose health check
- expose telemetry
- optionally expose last-response summary for applet

## J4. Service docs needed

Create a dedicated `docs/SERVICE.md` covering:
- why service mode exists
- how to start/stop/status it
- runtime files it creates
- socket path
- failure modes
- when not to use it

---

## K. Cinnamon applet: detailed implementation

The master plan correctly keeps this later, but it still needs sharper definition.

## K1. Applet scope

Applet should do only:
- show status
- submit short text commands
- show recent answer/result
- expose a few safe quick actions
- surface notifications/errors

Applet should **not**:
- duplicate parsing logic
- duplicate capability registry
- duplicate memory logic

## K2. Applet transport

Preferred:
- call CLI for simple mode first
- later talk to service socket if daemon exists

## K3. Applet states

- idle
- processing
- success
- action completed
- blocked/rejected
- degraded/offline

## K4. Applet docs needed

Create `docs/APPLET.md` with:
- responsibilities
- UI state model
- transport boundary
- packaging / deployment notes
- what data is cached locally

---

## L. Voice layer: detailed implementation

The current docs are directionally okay, but still too high-level.

## L1. Voice must stay optional

This is essential.
Text path must remain canonical.

## L2. Voice pipeline

Suggested flow:
1. wake detection or push-to-talk
2. local STT
3. text normalization
4. standard Bond text pipeline
5. response text
6. optional TTS rendering

## L3. Components

The current preference for local STT/TTS such as Vosk and Piper is reasonable, but document them as provisional implementation choices, not sacred truths, until benchmarked on the target machine. Use offline-first criteria: resource use, latency, language quality, packaging pain, and Greek/English support. citeturn424075view1

## L4. Voice docs needed

Create `docs/VOICE.md` with:
- enable/disable model
- runtime footprint expectations
- hotword strategy
- device permissions
- fallback behavior when unavailable

---

## M. Aider workflow integration

Aider already supports strong git integration and uses a repository map to understand the codebase, which means your move toward repo-first docs and smaller modules directly helps it. Aider’s own docs also recommend adding only the files relevant to the current change, not dumping everything into context. citeturn424075view4turn424075view5turn424075view6

## M1. What to document for aider

Create `docs/AIDER_WORKFLOW.md` with:
- how to start aider in this repo
- which files to add for common task types
- no-bypass workflow rules
- validation commands after each change
- commit discipline
- rollback rules
- when to use `/architect` versus direct edit mode
- how to treat docs updates alongside code changes

## M2. Strict file selection guidance

Document task bundles, e.g.:
- parser work -> `ai_action_parse.py`, `ai_action_policy.py`, relevant tests, behavior contract doc
- memory work -> memory files, master plan section, testing doc
- packaging work -> `pyproject.toml`, CLI file, installation doc, Makefile, tests

This prevents the “LLM sees everything and edits randomly” problem.

## M3. Dirty tree discipline

Given aider’s git behavior, document whether auto-commits are allowed in this repo and when to disable them. Aider can auto-commit its edits and also has knobs like `--no-auto-commits` and `--no-dirty-commits`, so your repo policy should choose deliberately instead of leaving this implicit. citeturn424075view4

---

## N. Testing architecture: concrete plan

## N1. Test layers

Define these explicitly:

1. **Static validation**
   - compile/import
2. **Unit tests**
   - parser helpers, policy helpers, path utils
3. **Behavior tests**
   - user prompt -> expected structured response class
4. **Probe tests**
   - probe output schemas
5. **Integration tests**
   - CLI + orchestrator + selected probes
6. **Smoke tests**
   - minimum working path for local install
7. **Golden regression corpus**
   - exact failures from term output

## N2. Failure corpus

Build tests from the supplied failures:
- `open internet`
- `start a timer`
- `read my clipboard`
- `print my path`
- `show my current directory`
- `yes open it`
- `path test`
- `test notification: 123`

These should become named behavior tests.

## N3. Documentation mapping

Every major behavior rule in `BEHAVIOR_CONTRACT.md` should reference:
- at least one test id
- or an explicit TODO saying it lacks a test

Without that, the contract remains prose only.

---

## O. Release, versioning, and changelog discipline

## O1. Versioning

Use semantic-ish versioning, but keep it practical:
- 0.x while architecture is fluid
- tag only meaningful checkpoints

## O2. Changelog format

Use:
- Added
- Changed
- Fixed
- Deprecated
- Removed
- Security

Keep runtime experiments out unless they changed tracked project behavior.

## O3. Release notes

Each release should summarize:
- new capabilities
- changed contracts
- migration notes
- known limitations
- test status

---

## P. Exact new docs to add

These are the missing documents I would add next:

1. `docs/DOCS_INDEX.md`
2. `docs/CAPABILITIES.md`
3. `docs/SCHEMAS.md`
4. `docs/SERVICE.md`
5. `docs/APPLET.md`
6. `docs/VOICE.md`
7. `docs/AIDER_WORKFLOW.md`
8. `docs/GITEA_PROJECT_MANAGEMENT.md`
9. `docs/RELEASE_PROCESS.md`
10. `docs/MEMORY.md`
11. `docs/PROBES.md`

This is the shortest realistic list that closes the main documentation holes.

---

## Q. Exact issue breakdown to create now

Create these first issues:

1. Rewrite README into real repo front door
2. Define repo description, topics, labels, milestones, and issue templates
3. Add packaging metadata and real console entry point plan
4. Specify parse/policy/exec schemas in docs and code stubs
5. Create capability registry spec and initial table
6. Create system probe registry and deterministic probe contract
7. Define memory record schemas and correction-ingestion flow
8. Convert transcript failures into behavior regression suite
9. Add docs index and cross-link matrix
10. Define install/update/uninstall lifecycle
11. Define optional user service architecture and IPC boundary
12. Define applet transport contract
13. Define Greek invocation normalization layer and bilingual language resources
14. Define telemetry schema and truthful timing output
15. Rework CHANGELOG/ROADMAP/STATE into operational documents

Each one should link back to a milestone and carry area/type/priority labels.

---

## R. Order of attack

The right order is:

### Step 1
Repo front door and project metadata
- README
- repo description
- labels
- milestones
- issue templates
- roadmap/status cleanup

### Step 2
Contract docs
- capabilities
- schemas
- probes
- memory
- install lifecycle
- release process

### Step 3
Code-facing structural specs
- CLI entry point
- capability registry skeleton
- parse/policy/exec data models
- probe registry skeleton

### Step 4
Behavior regression conversion
- turn term-output failures into tests

### Step 5
Later integration docs
- service
- applet
- voice

This order matters because otherwise you will design implementation against blurry contracts.

---

## Final judgment

The repo is no longer empty-minded.
But it is still **under-specified where software becomes real**.

The biggest remaining weakness is not lack of intelligence.
It is lack of explicit contracts.

The next documentation phase should therefore aim to make the repo able to answer all of these without needing chat history:

- What is Bond?
- What works now?
- What is intentionally unsupported?
- How do I install it?
- How do I update it?
- How do I remove it?
- How does parse/policy/exec communicate?
- What exactly is a capability?
- What exactly is a correction?
- What exactly is a probe?
- What is the next milestone?
- Which issue owns which change?
- How do I run aider safely here?
- What does a release mean?
- What are the behavior tests proving?

Until the repo can answer those by itself, the transcript is still carrying too much weight.
