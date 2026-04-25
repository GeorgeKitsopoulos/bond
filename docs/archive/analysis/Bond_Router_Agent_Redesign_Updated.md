# Bond Router & Agent Redesign (Final Unified Document – Local-First Architecture)

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Core Design Philosophy

This system is optimized for:

- Local execution (CPU-first, no GPU assumption)
- Low latency interaction
- High reliability through structure, not model size
- Lean-roster operation with no current heavyweight local tier

### Key Principle

> Performance comes from architecture, not model size.

Reality note: the current de facto local baseline roster is qwen2.5:3b-instruct, gemma2:2b, qwen2.5:7b-instruct, and nomic-embed-text:latest. qwen2.5:7b-instruct is the highest-capability local baseline currently available.

- 3B-4B-class tasks map to qwen2.5:3b-instruct for coordination and interaction
- ultra-light support and hygiene tasks may map to gemma2:2b
- mid/heavy local reasoning tasks map to qwen2.5:7b-instruct
- semantic retrieval and indexing use nomic-embed-text:latest

## System Goals

- Fast response for most interactions
- Deterministic behavior where possible
- Clear separation of responsibilities
- Safe system interaction
- Modular, replaceable components
- No hard dependency on heavyweight local inference

## High-Level Architecture

### Current pattern

User → Router (model) → Agent → Output

### Proposed pattern

User  
↓  
Deterministic Pre-Filter  
↓  
Bob (Structured Dispatcher)  
↓  
Policy Gate  
↓  
Specialist Agent  
↓  
Nick (Optional Output Refinement)

## Why the Current Router Feels Bad

The main problem is not only model quality. The real problem is architectural compression. The current setup pushes too many responsibilities into one routing step:

- understanding the user
- classifying the task
- estimating risk
- choosing the worker
- sometimes implicitly deciding policy
- sometimes implicitly shaping the final answer

That makes the router both slow and sloppy. A rough router usually fails in one of two ways:

1. it escalates too often, which kills speed
2. it stays small and routes badly, which kills reliability

The solution is not “just use a smarter router model.”  
The solution is to reduce what the router is responsible for.

## Core Design Correction

The small model should **not** be the sovereign brain of the whole assistant.

It should be the **coordinator of narrower specialists**.

That distinction matters because a 3B–4B model can work very well when asked to do limited structured delegation, but becomes unreliable when asked to:

- reason deeply under ambiguity
- choose dangerous system actions
- debug complex multi-file code changes
- decide between multiple partially-correct plans
- act as final authority on truth-sensitive questions

So the correct use of small models is not “make the whole assistant tiny.”  
It is “make the front layer tiny, strict, and disciplined.”

## Layer 1 — Deterministic Pre-Filter

### Purpose

Reduce unnecessary model usage and enforce baseline logic before any LLM is invoked.

### Responsibilities

- manual overrides
- hard rule detection
- read vs write detection
- system vs chat vs code vs web hints
- immediate high-risk flagging
- explicit privileged-intent detection

### Why this layer matters

There is no reason to waste model inference on obvious cases. If the input contains things like:

- shutdown
- reboot
- sudo
- rm -rf
- delete system file
- modify boot
- apt remove core package

then the system should not “wonder” what that means. It should mark it immediately as high risk and constrain the next stages.

### Example output

```json
{
  "force_agent": null,
  "risk_hint": "medium",
  "type_hint": "code"
}
```

## Layer 2 — Bob (Structured Dispatcher)

### Role

Bob is not the thinker.  
Bob is the structured dispatcher.

### Model Class

- 3B-4B-class tasks map to qwen2.5:3b-instruct

### Responsibilities

- normalize intent
- classify task type
- estimate confidence
- determine if tools are required
- recommend primary specialist
- optionally recommend secondary specialist
- request escalation when confidence is low or consequences are high

### Required output

Bob should always return strict structured output, never free-form prose.

Example:

```json
{
  "intent": "debug_python_script",
  "primary_agent": "james",
  "secondary_agents": ["nick"],
  "requires_tools": false,
  "risk_level": "low",
  "confidence": 0.84,
  "escalate": false
}
```

### Hard constraints

Bob must never:

- answer the user directly
- invent system facts
- execute tools
- bypass the policy layer
- become a long-form reasoning model

### Why Bob can be small

A small model can do this well if:

- the output schema is tight
- the task categories are stable
- the pre-filter removes obvious edge cases
- the policy gate catches dangerous ambiguity

This is exactly where a 3B–4B model is viable.

## Layer 3 — Policy Gate

### Role

Policy Gate is more important than the router.

The router says what seems appropriate.  
The policy gate decides what is allowed.

### Responsibilities

- validate Bob’s output
- apply execution policy
- require confirmation for dangerous operations
- reject undefined actions
- constrain tool scope
- force safer fallbacks
- route privileged actions into Terminator

### Behavior

- low risk → proceed
- medium risk → proceed with limits and logging
- high risk → require confirmation and/or escalation
- undefined or contradictory → reject and re-route

### Important design principle

Policy should be as deterministic as possible.  
Do not let the model define its own safety boundaries in real time.

## Agent Roster (Reworked)

The names can stay because they are useful for mental mapping, but each agent must be defined by **responsibility contract**, not personality.

## Stuart — Front Interaction Layer

### Purpose

Fast conversational handling for low-stakes interaction.

### Model Class

- 3B–4B

### Handles

- simple Q&A
- clarifications
- conversational continuity
- short rewrites
- small text transformations

### Must not handle

- system authority
- coding authority
- privileged decisions
- factual claims requiring tools or retrieval unless already provided

### Notes

Stuart should make Bond feel responsive.  
He should not pretend to be the whole assistant.

## Bob — Dispatcher

Already defined above.  
Bob is the coordinator, not the final mind.

## Polly — Research Agent

### Purpose

Research, retrieval synthesis, source-grounded summaries.

### Model Class

- mid/heavy local reasoning maps to qwen2.5:7b-instruct

### Handles

- web or document investigation
- extraction from sources
- synthesis of findings
- evidence-first summaries
- source comparison

### Rules

- accuracy over elegance
- uncertainty must be surfaced
- source conflict must be preserved, not smoothed over

### Why Polly should be mid-sized

Research is often too context-sensitive for a small 3B front model.

qwen2.5:7b-instruct is the correct local center of gravity here.

## Nick — Editor / Output Formatter

### Purpose

Turn raw specialist output into clear user-facing form.

### Model Class

- mid/heavy local reasoning maps to qwen2.5:7b-instruct

### Handles

- rewriting
- restructuring
- summarization
- style harmonization
- markdown polishing
- final readability pass

### Important rule

Nick should often be the **last pass**, not the main worker.

That keeps the other agents free to think in structured or technical terms without polluting the final answer format.

## James — Builder / Technical Agent

### Purpose

Code reasoning, debugging, architecture thinking, technical troubleshooting.

### Model Class

- mid/heavy local reasoning maps to qwen2.5:7b-instruct

### Handles

- code generation
- code review
- bug isolation
- design reasoning
- system troubleshooting analysis
- repo-level logic work

### Must not do directly

- privileged execution
- destructive system action
- unreviewed shell authority

### Critical correction

This role does **not** require a heavyweight local tier when work is decomposed well and validated externally.

That is the main design shift.

A well-scaffolded qwen2.5:7b-instruct technical flow can do most serious home-lab work if:

- context is curated
- tasks are broken down
- outputs are verified
- execution is gated

## Lily — Memory Agent

### Purpose

Memory shaping, memory cleanup, memory summarization.

### Model Class

- ultra-light support/hygiene tasks may map to gemma2:2b

### Handles

- summarizing sessions
- extracting durable facts
- filtering junk
- compressing logs
- preparing memory inserts

### Goal

Prevent memory pollution.

Lily is a hygiene layer, not a reasoning layer.

### Why Lily should stay small

Memory curation should be cheap and consistent.  
You do not need a large model to decide that a transient debug error should not become a permanent user fact.

## Terminator — Privileged Execution Layer

### Critical redefinition

Terminator should not mean “dangerous model.”  
That framing is wrong.

Terminator should mean:

**controlled privileged execution pipeline**

That means the danger is not in the model itself.  
The danger is in the permission scope of the lane.

### Responsibilities

- command validation
- permission enforcement
- bounded execution
- confirmation requirements
- refusal of undefined or overly broad actions
- audit/log hooks
- safety constraints before any real action occurs

### Model size

- default execution-planning model should remain moderate
- qwen2.5:7b-instruct is enough for many cases
- there is no current local heavyweight rescue model to lean on

### Important implication

Terminator is primarily a system design construct, not a model selection.

## Heavyweight Local Tier Assumption (Outdated)

Outdated references to a 20B/heavyweight local rescue tier should not be treated as active planning guidance.

Current reality is that the available local roster tops out at qwen2.5:7b-instruct.

Escalation under current constraints is primarily architectural and procedural:

- stricter decomposition
- additional retrieval and context curation
- tighter validation loops
- multi-pass specialist flow
- stronger policy discipline and tool contracts

Escalation should not mean “hand it to a bigger local model,” because that tier is not currently present.

## Updated Model Strategy

### Desired workload distribution

- Stuart → qwen2.5:3b-instruct
- Bob → qwen2.5:3b-instruct
- Polly → qwen2.5:7b-instruct
- Nick → qwen2.5:7b-instruct
- James → qwen2.5:7b-instruct
- Lily → gemma2:2b (or qwen2.5:3b-instruct when needed)
- Terminator → controlled execution lane using moderate models first
- retrieval/indexing path → nomic-embed-text:latest

### Practical interpretation

This means:

- most user interactions stay fast
- most real work stays within manageable local inference
- the system remains portable across normal home hardware
- no current heavyweight local model tier is assumed as hidden fallback

## Is the 3B Category Viable?

### Yes, but only in a disciplined role

3B–4B is viable for:

- routing
- interaction
- schema generation
- intent normalization
- light memory work
- low-stakes chat
- simple transformations

3B–4B is not viable as the universal decision-maker for:

- privileged operations
- deep technical planning
- serious coding authority
- ambiguous truth-critical research
- multi-step execution planning under risk

### Final answer to the 3B question

A 3B model is a good solution **for the front of the system**.  
It is not a good solution **for the whole system**.

That distinction must remain explicit in the design document.

## Why Smaller Models Can Still Work Well

This is the part many people get wrong.

Small models become useful not because they suddenly become genius-level, but because the architecture reduces the burden placed on them.

They perform much better when:

- the task is narrow
- the output is structured
- policy is externalized
- deterministic layers remove obvious noise
- they do not have to also be judge, executor, and explainer

That is why the architecture matters more than the benchmark.

## Key Design Rules

### 1. No overloaded agents

Each agent should have:

- one core mission
- narrow allowed actions
- clear forbidden actions
- predictable output format

### 2. Structured outputs wherever possible

Do not let routing depend on vibes and prose.  
Use schemas.

### 3. Deterministic before probabilistic

If a rule can be hard-coded safely, do that first.

### 4. Escalation must be rare

Escalation is not a feature to show off.  
It is a sign that ordinary paths were insufficient.

Under the current roster, escalation is architectural and procedural first: decompose the task more strictly, improve retrieval/context curation, add validation passes, and tighten specialist contracts before assuming model-size relief.

### 5. Final output should be separated from task execution

The model that solves the problem does not always need to be the model that speaks to the user.

### 6. Privileged action must never be “just another agent”

Execution with elevated consequence is a separate lane.

## Final Recommended Interpretation of the Roster

- **Stuart** → fast conversational shell
- **Bob** → structured dispatcher
- **Polly** → research and retrieval
- **Nick** → editor and final formatter
- **James** → builder, coder, technical problem-solver
- **Lily** → memory hygiene and compression
- **Terminator** → privileged execution pipeline, not merely a model
- **Model escalation path** → architectural/procedural hardening under the existing roster, not a heavyweight local handoff

## Final Conclusion

The redesign should not aim for “a smarter router.”

It should aim for:

- a smaller router with less responsibility
- a stronger policy layer
- narrower specialist contracts
- rare escalation
- moderate models doing most of the real work
- no current heavyweight local model tier assumed as rescue path

The correct summary is:

> The 3B/4B model is not the brain of Bond.  
> It is the coordinator of a tightly-controlled specialist system.

If that principle is respected, then the system can be:

- fast enough for normal interaction
- strong enough for real work
- portable enough for ordinary home hardware
- safe enough to scale without becoming chaotic
