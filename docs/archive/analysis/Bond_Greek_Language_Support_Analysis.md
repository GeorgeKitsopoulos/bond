# Bond Greek Language Support Analysis and Integration Plan

> Historical note: this document is preserved for design rationale or implementation history. It is not the current source of truth. Use the current docs and code for present behavior, paths, and project status.

## Document status

This document is a critical analysis and implementation-planning artifact for an LLM to use when deciding how to integrate **full Greek language support** into Bond.

It is intentionally:

- grounded in the current repository snapshot and current planning documents
- aligned with the existing Bond direction instead of restarting architecture from zero
- limited to **text-first Greek support** (no voice layer yet)
- written to be consumed by another LLM as a decision and planning input
- focused on understanding, normalization, context, memory, invocation, and GUI locales

This document is **not** a step-by-step execution guide.
It does **not** provide shell commands.
It does **not** redesign the separate brain/router strategy beyond what Greek support requires.

---

## Inputs used

### Repository snapshot and planning artifacts reviewed

This analysis is grounded in the current Bond snapshot and the already-written planning documents, especially the capability, packaging, and router/agent redesign materials.

Observed current-state signals include:

- repository docs already define Bond as a layered assistant with separate parsing, policy, execution, memory, and path concerns
- the master plan already lists **English and Greek invocation forms** as an intended direction
- current parsing code already includes limited Greek heuristics
- current system scan already captures locale-related user signals such as `~/.config/user-dirs.locale`
- current project state explicitly admits that parsing and capability honesty are not yet reliable enough

### External standards and official references reviewed

This plan is also informed by official references on:

- Unicode normalization and caseless comparison
- Python internationalization and localization support
- locale handling
- language tags and locale identifiers
- internationalization best practices

Those sources matter because Greek support is **not** just “add some translated keywords.”
It requires proper text normalization, locale separation, and message architecture.

---

## Executive conclusion

Bond is **not far away from Greek support conceptually**, but it is **far away architecturally**.

Right now the project has:

- a small amount of Greek-aware parsing
- a few Greek wake/action patterns
- some accent stripping
- some limited bilingual heuristics
- explicit intention in the docs to support English and Greek invocation

That is only an **entry-level compatibility layer**.

It is **not** yet:

- a bilingual assistant core
- a Greek-capable memory/retrieval system
- a robust multilingual normalization pipeline
- a locale-aware UI/message system
- a reliable invocation resolver across Greek and Latin input variants
- a Greek-aware intent, context, and response policy

The biggest trap to avoid is this:

> Do not treat Greek support as a translation patch.

If Bond simply adds more Greek regex patterns, the result will be fragile, inconsistent, and hard to scale.

The correct goal is:

> Make Bond language-aware at the parsing, normalization, memory, retrieval, response, and UI-message layers, while keeping capability logic language-agnostic underneath.

That distinction is critical.

---

## Critical reading of the current state

## What the current snapshot already gets right

### 1. The architecture docs already separate parsing from authority

This is the most important positive signal.

The architecture and state documents already describe Bond as a system where:

- parsing and normalization should be separate
- policy should decide what is allowed
- execution should sit behind controlled boundaries
- entry points should stay thin
- invocation normalization is a real architectural concern

That means Greek support can be added in the correct layer instead of smeared across the project.

### 2. The project already acknowledges English and Greek invocation direction

The master plan explicitly includes examples such as:

- `bond hey`
- `hey bond`
- `μποντ δώσε μου τα σημερινά νέα`

That matters because it means Greek support is not an afterthought. It is already part of intended product shape.

### 3. There is already some Greek handling in `ai_linguistics.py`

The current linguistics layer already includes:

- accent stripping through Unicode decomposition
- a small set of Bond variants including `μποντ`
- some Greek action-noise stripping
- a few Greek-to-English action normalizations such as “άνοιξε → open” and “δείξε → show”

This is useful, but only as evidence that the right direction has started.

### 4. There is already a place to capture locale-related environment truth

`ai_scan_system.py` already reads locale-related signals such as `~/.config/user-dirs.locale`.
That is small, but important: Bond already has a foothold for locale awareness instead of pretending locale does not exist.

---

## What is structurally weak right now

### 1. Greek support is currently heuristic, not architectural

The existing handling is essentially:

- accent stripping
- a tiny alias list
- regex replacements
- some Greek question/action patterns

That is not robust bilingual understanding.
It is a small lexical patch set.

This approach fails once the user writes naturally in Greek with:

- inflection
- different word order
- mixed Greek and English
- Greek punctuation conventions
- Greeklish or partial transliteration
- casual fragments rather than imperative command phrases
- context carried across multiple turns

### 2. Invocation handling is under-modeled

The user requirement is not just “understand Greek.”
The user explicitly wants Bond to be invocable in many free-form ways such as:

- `hey bond`
- `Bond hey`
- `Τι κάνεις bond`
- `Μπόντ can you tell me the weather?`
- `Bond`
- `bond`
- `Μπόντ`
- `μποντ`

The current code only partially addresses this. It does not yet model invocation as a robust, standalone system with:

- address detection
- invocation-only utterance handling
- wake-token position tolerance
- script-insensitive alias matching
- punctuation-insensitive matching
- casefolded matching
- mixed-language invocation

### 3. The current normalization is too shallow for Greek

The current simplification logic strips accents and lowers case, which is a start, but Greek robustness needs more than that.

It still lacks a disciplined pipeline for:

- Unicode normalization policy
- casefold-first canonical comparison
- alias folding
- optional Greeklish mapping
- punctuation normalization
- token-preserving normalized forms for search versus intent
- separation between “display text” and “matching text”

This matters because Greek input is not just accented versus unaccented. Mixed forms, compatibility forms, punctuation variants, and transliterated variants all matter.

### 4. Memory and retrieval are not yet bilingual by design

Greek support that only works at immediate input parsing is not enough.

Bond also needs Greek support in:

- memory fact extraction
- memory query rewriting
- retrieval matching
- entity aliasing
- summarization context
- durable facts and preferences
- future GUI labels and stored user-facing texts

If Greek is added only to parsing, the assistant will understand the question but fail to retrieve relevant context or respond consistently.

### 5. GUI localization is not yet formalized

The user wants Greek locales for GUI.

That means the project needs a real i18n/l10n layer for user-facing strings, not hardcoded English text scattered through logic.

Right now there is no evidence of a proper catalog-based translation architecture.
Without that, GUI localization later will become a painful retrofit.

### 6. The project risks coupling language support to capability logic

This would be a serious mistake.

Capabilities such as:

- open file
- show weather
- inspect system state
- summarize document

must not become duplicated in English and Greek logic branches.
Only the **surface language layer** should vary.
The intent/capability layer underneath should remain language-agnostic.

---

## The correct design principle

Greek support should be integrated using this rule:

> Surface language should be multilingual.  
> Intent, capability, policy, and execution contracts should remain language-neutral.

In practical terms:

- the user may speak Greek, English, or mixed language
- Bond should normalize that into a stable internal representation
- internal capabilities should still be things like `open_uri`, `show_weather`, `query_memory`, `inspect_system_profile`
- responses and GUI text should then be rendered in the selected language/locale

This is the only scalable approach.

---

## What “full Greek support” should actually mean

The phrase “fully understand and incorporate Greek” needs precision.

It should mean all of the following:

### 1. Invocation support

Bond should recognize being addressed in Greek, English, or mixed forms.

### 2. Input understanding

Bond should correctly interpret Greek questions, requests, clarifications, and mixed-language utterances.

### 3. Context continuity

Once the conversation is in Greek, Bond should preserve that context and continue naturally.

### 4. Retrieval and memory grounding

Greek inputs should still retrieve relevant facts, logs, and context rather than missing because stored content or indexes are English-heavy.

### 5. Response generation policy

Bond should default to responding in the language implied by the active conversation context unless user policy says otherwise.

### 6. Locale-aware formatting

GUI and user-facing formatting should support Greek locale conventions where relevant.

### 7. Message catalog localization

User-visible interface strings should be localizable independently of business logic.

### 8. Honest fallback behavior

If Bond can understand Greek at one layer but not support a capability in Greek UI or locale formatting yet, it should state that cleanly rather than pretending.

---

## Important correction: Greek support is not one feature

It is a stack.

That stack has at least six layers:

1. invocation and address detection
2. text normalization and alias folding
3. language identification and mixed-language handling
4. intent/entity extraction into language-neutral capability contracts
5. bilingual memory/retrieval grounding
6. user-facing localization for responses and GUI

If any of these are skipped, “Greek support” will feel partial and fake.

---

## Current code-level diagnosis

## `ai_linguistics.py`

### Strengths

- already uses Unicode decomposition to remove accents
- already attempts simplified text matching
- already includes a small alias set for Bond
- already includes a few Greek action normalizations
- already includes some chain handling for Greek conjunctions

### Weaknesses

- alias inventory is extremely small
- no disciplined canonical invocation resolver
- no explicit casefold-based comparison strategy
- no Greeklish handling strategy
- no separation between:
  - normalized display-preserving form
  - intent-matching form
  - retrieval/search form
- action lexicon is too tiny and imperative-heavy
- no notion of dialogue acts beyond regex patterns

### Judgment

This file is the right place to start, but in current form it is not a Greek language layer. It is a lightweight preprocessing helper.

---

## `ai_intent.py`

### Strengths

- already contains some Greek question and directive patterns
- already supports mixed-intent detection logic
- already uses normalized text before classifying

### Weaknesses

- Greek coverage is shallow and command-like
- too dependent on fixed phrases
- likely weak on natural Greek question forms and colloquial variation
- not designed for multilingual confidence scoring
- not designed for mixed-language utterances inside one clause
- does not separate language-specific cue detection from language-neutral intent classes

### Judgment

This is good enough for prototype bilingual heuristics, but not for robust Greek conversation.

---

## `ai_run.py`

### Strengths

- central orchestration already exists
- current project priorities are explicitly encoded
- the project already cares about grounded behavior

### Weaknesses

- if Greek support is bolted on here, it will become a mess
- the orchestrator should consume normalized/intention-resolved inputs, not own multilingual heuristics

### Judgment

`ai_run.py` should not become the Greek support implementation site. It should remain a consumer of language-layer outputs.

---

## `ai_scan_system.py`

### Strengths

- already captures locale-adjacent environment data
- can be extended to detect language and locale truth for UI/runtime decisions

### Weaknesses

- currently captures only fragments of locale reality
- no normalized host locale profile yet
- no clear distinction between language preference and formatting locale
- no export of assistant-usable locale facts

### Judgment

This module should become the host-locale truth source, but not the place where user conversation language is decided.

---

## The real requirements behind the user examples

The examples the user gave are more informative than they look.

### Example family 1 — pure invocation tokens

- `Bond`
- `bond`
- `Μπόντ`
- `μποντ`

This requires:

- standalone invocation recognition
- case-insensitive and script-tolerant alias handling
- diacritic-insensitive matching
- exact-short-utterance handling
- proper behavior for address-only input

Bond should not treat these as unknown garbage.
It should interpret them as “assistant address / conversation open / prompt for follow-up.”

### Example family 2 — greeting around the name

- `hey bond`
- `Bond hey`

This requires:

- flexible token order
- greeting/address separation
- address token detection not tied to position
- support for inverted or casual phrasing

### Example family 3 — Greek question with English name

- `Τι κάνεις bond`

This requires:

- Greek question understanding
- embedded English alias recognition
- mixed-script tokenization
- response-language continuity

### Example family 4 — Greek alias with English request

- `Μπόντ can you tell me the weather?`

This requires:

- Greek alias recognition
- English request understanding
- mixed-language utterance handling
- address extraction separate from task extraction

That means the user is not asking for “Greek only.”
They are asking for a bilingual interaction model that tolerates real human mixing.

---

## Research-grounded design principles

## 1. Unicode normalization is mandatory

Unicode normalization is not optional decoration.
It is the baseline for stable text handling. The Unicode Standard defines normalized forms such as NFC, NFD, NFKC, and NFKD, and Python explicitly documents these normalization mechanisms. citeturn765834search0turn765834search2

Implication for Bond:

- all comparison-oriented text handling needs a consistent normalization policy
- display text and matching text must be separated conceptually
- ad-hoc lowercasing alone is not enough

## 2. Caseless matching should rely on casefold semantics, not simplistic lowercase logic

Python’s Unicode guidance explicitly distinguishes proper caseless comparison from naive lowercasing and documents `casefold()` as the relevant operation for language-insensitive matching. Unicode also notes that case folding is intended for comparison and identifier-like matching, not display transformation. citeturn765834search0turn765834search6

Implication for Bond:

- invocation aliases such as `Bond`, `bond`, `Μπόντ`, `μποντ` should go through a canonical matching pipeline
- user-visible text should not be mutated with comparison-oriented transforms
- invocation matching and retrieval matching should use stronger folding than response rendering

## 3. Internationalization and localization must be separated

W3C distinguishes internationalization from localization: i18n is building the system so it can support multiple locales; l10n is adapting it for a specific locale. Python’s i18n documentation and `gettext` support align with that separation. citeturn765834search1turn765834search9turn765834search11

Implication for Bond:

- Greek support in conversations is not the same thing as Greek GUI strings
- Bond needs an i18n-ready core plus Greek l10n resources
- hardcoded English UI text is technical debt

## 4. Locale identifiers and language tags should be explicit

W3C guidance on language tags and locale identifiers emphasizes that language/locale preferences should be explicitly represented rather than guessed loosely from content. citeturn765834search17

Implication for Bond:

- it should model language preference explicitly, not infer it fresh every turn without memory
- host locale, UI locale, and conversation language should be separate fields
- Greek conversation does not necessarily mean Greek host locale, and vice versa

## 5. Catalog-based message localization is the right long-term direction

Python’s `gettext` module exists specifically to let applications write source strings in one language and provide translated catalogs for runtime localization. citeturn765834search1

Implication for Bond:

- GUI text and reusable response templates should move toward catalog-backed localization
- this should happen before GUI surface area grows

---

## The language model that Bond should adopt internally

Bond needs a simple but explicit language-state model.

### Required distinct concepts

#### A. Host locale

Examples:
- `el_GR.UTF-8`
- `en_US.UTF-8`

This is about system formatting and default UI tendencies.

#### B. User preferred assistant language

Examples:
- `el`
- `en`
- `auto`

This is a user preference for how Bond should speak.

#### C. Active conversation language

Examples:
- `el`
- `en`
- `mixed`

This is derived from the live interaction and can switch.

#### D. GUI locale

Examples:
- `el_GR`
- `en_US`

This drives interface labels, menus, dialog text, and format strings.

#### E. Retrieval normalization language profile

This controls query normalization and alias expansion for search/memory.

Without this separation, Bond will become confused between:
- what the OS wants
- what the user wants
- what the current conversation is using
- what the GUI should display

---

## Recommended architecture for Greek support

## Layer 1 — Invocation and alias resolution

### Purpose

Resolve whether the user is addressing Bond, regardless of case, diacritics, script, token order, or mixed language.

### Requirements

- canonical alias registry for Bond
- support for:
  - `bond`
  - `Bond`
  - `μποντ`
  - `Μποντ`
  - `Μπόντ`
- optional support for Greeklish or transliterated variants only if explicitly desired and carefully bounded
- address-token detection anywhere in utterance
- invocation-only utterance handling
- distinction between:
  - address-only
  - address + greeting
  - address + task
  - address embedded in question

### Why first

Because if Bond cannot reliably tell when it is being addressed, all higher-level language support feels broken.

### Critical rule

Do not hardcode this as scattered string checks.
This must be a real alias resolver.

---

## Layer 2 — Canonical text normalization

### Purpose

Create stable comparison forms for multilingual text.

### Required outputs

For each user utterance, Bond should derive at least:

- raw text
- display-preserving normalized text
- matching/canonical text
- optional search-folded text

### Recommended normalization concepts

- Unicode normalization for canonical consistency
- casefold-based comparison
- punctuation simplification
- whitespace normalization
- Greek accent/tonos folding for matching only
- optional Greek-final-sigma handling through Unicode-aware normalization behavior
- alias folding tables
- mixed-script token preservation

### Critical caution

The normalization used for matching should not replace the original user text everywhere.
Over-normalization can degrade memory quality and user-facing output.

---

## Layer 3 — Language and mixed-language detection

### Purpose

Estimate whether the utterance is:

- Greek
- English
- mixed
- unknown/neutral

### Why this matters

Because Bond must decide:

- which parser hints to prioritize
- which response language to prefer
- how to expand queries for memory/retrieval
- which localized UI/messages to use

### Critical design choice

This should be **lightweight and practical**, not an overbuilt NLP research subsystem.

For Bond’s current phase, a pragmatic detector is enough if it can:

- detect Greek-script presence
- detect strong Greek cue words
- detect English cue words
- detect mixed sentences
- produce confidence plus fallback mode

### Output example

```yaml
language_state:
  utterance_language: mixed
  confidence: 0.88
  contains_greek_script: true
  contains_latin_script: true
  preferred_response_language: el
```

### Why mixed must be first-class

Because the user explicitly wants forms like:
- Greek alias + English request
- English alias + Greek question

If Bond only supports a single-language assumption, it will misclassify these.

---

## Layer 4 — Intent/entity resolution into language-neutral contracts

### Purpose

Map Greek or mixed-language user input into the same internal capability contracts used by English.

### Example

All of these should converge toward the same capability:

- `show me the weather`
- `δείξε μου τον καιρό`
- `τι καιρό έχει`
- `Μπόντ can you tell me the weather?`

Internal contract:
```yaml
intent: weather_query
capability: get_weather
entities:
  location: implicit_current
```

### Design principle

Do not translate Greek sentences into English prose and then parse them naively.
Instead, resolve them into structured internal intent objects.

### Why this matters

That keeps:
- policy
- capability truth
- tool routing
- execution
language-neutral.

---

## Layer 5 — Bilingual memory and retrieval support

### Purpose

Ensure Greek input still retrieves relevant project or personal context.

### Required behavior

- Greek user queries should retrieve Greek-stored memories
- Greek user queries should also retrieve relevant English-stored memories when semantically equivalent
- English queries should still find Greek-stored content when relevant
- durable aliases should exist for stable entities

### Practical implications

Bond likely needs:

- alias-aware memory keys
- normalized search forms
- bilingual entity mapping for common durable concepts
- language metadata attached to memory items
- separation between stored original text and search-normalized text

### Critical warning

If the system stores only raw strings and searches only one normalized form, Greek support will feel shallow even if immediate parsing improves.

---

## Layer 6 — Response-language and dialogue policy

### Purpose

Decide how Bond should respond.

### Required rules

Bond should track:

- user preference if explicitly set
- active conversation language
- whether the user switched language mid-thread
- whether the request asks for output in a specific language

### Recommended default

- respond in the language of the latest substantive user turn
- preserve bilingual mode if the user is mixing naturally
- do not forcibly translate everything to English
- allow user preference to override auto behavior

### Why needed

Because Greek support is not only about understanding input. It is about interaction continuity.

---

## Layer 7 — GUI locale and message catalogs

### Purpose

Support Greek interface strings independently of internal logic.

### Required architecture

- user-facing strings extracted from code paths where possible
- translation catalogs or equivalent message-resource structure
- explicit locale selection
- fallback locale behavior
- no hardcoded English labels in GUI-facing surfaces where localization is intended

### Recommended direction

A catalog-based i18n model is the correct long-term path for Python applications, and `gettext` is the standard built-in foundation for that category of work. citeturn765834search1turn765834search9

### Important distinction

CLI and internal logs do not need identical localization policy.
GUI-facing text should be localized first.
Developer-facing diagnostics can remain English-first if desired.

---

## What Bond must support for Greek invocation specifically

This deserves its own explicit contract.

## Invocation requirements

Bond should support all of the following as valid address forms:

### Address-only
- `bond`
- `Bond`
- `μποντ`
- `Μποντ`
- `Μπόντ`

### Address + greeting
- `hey bond`
- `Bond hey`
- `γεια bond`
- `γεια σου bond`
- `μποντ γεια`

### Address embedded in request
- `Τι κάνεις bond`
- `bond τι κάνεις`
- `Μπόντ can you tell me the weather?`
- `can you tell me the weather, bond?`

### Address + no task yet
- user says `Bond`
- Bond should respond with a conversational-opening behavior rather than an error

## Required internal outcomes

The invocation resolver should output something like:

```yaml
address_state:
  addressed_to_bond: true
  alias_matched: "μποντ"
  invocation_only: false
  invocation_position: "middle"
  greeting_present: true
  residual_text: "τι κάνεις"
```

This is much stronger than a boolean “contains bond variant.”

---

## Recommended data structures

## 1. Alias registry

Bond should maintain a formal alias registry for assistant names and invocation variants.

Example concept:

```yaml
assistant_aliases:
  canonical_name: "bond"
  invocation_aliases:
    - "bond"
    - "μποντ"
    - "μποντ;"
    - "μποντ?"
    - "μποντ"
  matching_rules:
    casefold: true
    strip_diacritics_for_match: true
    punctuation_insensitive: true
```

### Why formal registry matters

Because the user’s examples are not fixed command phrases.
They are natural address variations.

---

## 2. Language profile object

Bond should maintain a language profile in runtime state.

Example:

```yaml
language_profile:
  ui_locale: "el_GR"
  preferred_response_language: "auto"
  active_conversation_language: "mixed"
  supported_input_languages:
    - "en"
    - "el"
  supported_ui_locales:
    - "en_US"
    - "el_GR"
```

---

## 3. Message catalogs

Conceptually:

- core user-facing strings
- GUI labels
- reusable response templates
- confirmation prompts
- unsupported-feature explanations
- onboarding/help text

All of these should be localizable independently of logic.

---

## 4. Memory language metadata

Each durable memory item should ideally carry:

- original text
- language hint
- normalized retrieval form
- aliases/entity keys if applicable

Without this, Greek memory retrieval will remain weak.

---

## What not to do

## 1. Do not patch Greek support with more regex alone

That might produce a short demo improvement, but it will not create robust Greek conversation support.

## 2. Do not translate internal capability names into Greek

Internal capability contracts should remain stable and language-neutral.

## 3. Do not infer UI locale from every utterance

Conversation language and GUI locale are related but not identical.

## 4. Do not over-normalize stored content

Keep original text.
Use normalized forms for matching and retrieval, not as the sole stored representation.

## 5. Do not make Greek support depend on voice-first assumptions

The user explicitly wants no voice work yet.
Text-first support must stand on its own.

## 6. Do not couple Greek support to Linux-only assumptions

GUI locale and text handling should be portable even if Bond is Linux-first today.

---

## Recommended implementation phases

These phases are about Greek language support and localization only.
They do not re-plan router or packaging work.

## Phase 1 — Build the language foundation

### Goal

Create the minimum architecture required for serious Greek support.

### Deliverables

- canonical text normalization policy
- invocation alias registry
- language-state object
- host locale profile export
- separation of:
  - raw text
  - canonical matching text
  - response/display text

### Why first

Without this, all later Greek work becomes regex debt.

### Expected result

Bond can robustly detect that it is being addressed and can safely classify input as Greek, English, or mixed.

---

## Phase 2 — Harden bilingual invocation and basic conversational handling

### Goal

Make Bond reliably usable in Greek and mixed-language conversational entry points.

### Deliverables

- address-only utterance handling
- greeting/address/task decomposition
- mixed-language invocation resolution
- conversation-open behavior for bare invocations
- response-language continuity rules

### Why second

This gives the user visible improvement immediately.

### Expected result

The examples:

- `Bond`
- `Μπόντ`
- `Τι κάνεις bond`
- `Μπόντ can you tell me the weather?`

all behave sensibly.

---

## Phase 3 — Expand Greek intent and entity understanding

### Goal

Move from keyword Greek to actual practical Greek intent support.

### Deliverables

- Greek question cues expanded beyond a tiny regex set
- Greek request and clarification patterns
- mixed-language clause handling
- language-neutral intent objects
- better ambiguity handling in Greek

### Why third

Invocation alone is not enough.
Bond must also understand the request reliably.

### Expected result

Greek becomes a real supported input language, not just a wake word language.

---

## Phase 4 — Add bilingual memory and retrieval grounding

### Goal

Ensure Greek interaction is grounded in retained context.

### Deliverables

- language metadata for memory items
- normalized retrieval forms
- bilingual alias/entity mapping where appropriate
- query expansion rules for Greek ↔ English durable concepts
- response continuity when retrieved context is in another language

### Why fourth

Without retrieval support, Greek conversation will still feel shallow during multi-turn use.

### Expected result

Greek questions can still benefit from existing English-heavy project memory and vice versa.

---

## Phase 5 — Introduce proper UI/GUI localization structure

### Goal

Prepare Bond for Greek GUI surfaces without scattering translations in logic.

### Deliverables

- localizable message resource architecture
- Greek locale resources
- English fallback resources
- explicit locale selection policy
- formatting rules for locale-sensitive user-facing output

### Why fifth

The user explicitly wants Greek locales for GUI.
That should be implemented cleanly rather than retrofitted later under pressure.

### Expected result

Bond can present user-facing interface text in Greek consistently.

---

## Phase 6 — Quality hardening and acceptance thresholds

### Goal

Prevent shallow “looks bilingual” regressions.

### Deliverables

- bilingual normalization tests
- invocation matrix tests
- mixed-language input tests
- memory retrieval tests across Greek and English
- GUI locale fallback tests
- regression criteria for adding future languages later

### Why last

Because language support without tests will rot quickly.

---

## Recommended priority order

If the goal is practical usefulness quickly, the order should be:

1. invocation alias resolver
2. canonical normalization policy
3. language-state tracking
4. mixed-language intent handling
5. response-language policy
6. bilingual memory/retrieval support
7. GUI locale/message catalog layer
8. broader Greek lexical coverage and polish

This order is better than “translate the GUI first.”
The core understanding layer matters more.

---

## Acceptance criteria for serious Greek support

Bond should not claim strong Greek support until all of the following are true.

### Invocation truth
- Bond reliably recognizes Greek, English, and mixed invocation variants.

### Input understanding
- Common Greek questions and requests are classified correctly at a useful rate.

### Mixed-language robustness
- Greek and English can coexist in the same utterance without breaking parsing.

### Response continuity
- Bond responds in Greek when the conversation is in Greek, unless overridden.

### Memory grounding
- Greek interaction can retrieve relevant prior context rather than behaving statelessly.

### Locale separation
- host locale, conversation language, and GUI locale are separate and explicit.

### GUI readiness
- user-facing interface strings can be localized without editing core logic.

### Fallback honesty
- unsupported or partial Greek areas are stated honestly.

If these criteria are not met, Bond should describe its Greek support as **partial** rather than full.

---

## Specific recommendations for the current codebase

## 1. Evolve `ai_linguistics.py` into a real language-preprocessing module

It should own:

- canonical normalization
- alias resolution
- script-aware matching support
- punctuation folding policy
- address extraction primitives

It should not remain just a bag of regex replacements.

## 2. Separate invocation resolution from intent classification

Being addressed is not the same as being given an action.
This should be a first-class distinction.

## 3. Keep `ai_intent.py` focused on language-neutral outcome classes

Greek-specific cue handling can feed it, but it should emit internal intent classes that do not care whether the input was English or Greek.

## 4. Add explicit language state to runtime/session context

This should include:
- preferred response language
- current conversation language
- UI locale
- host locale snapshot

## 5. Add language metadata and normalized search forms to memory storage

Otherwise Greek support will stall at single-turn chat.

## 6. Add a dedicated localization layer for GUI/user-facing strings

Do this before GUI surface area grows.

## 7. Keep logs and developer diagnostics separate from user-facing localization policy

Not every internal message needs Greek.
But all user-facing interaction that claims Greek locale support should be localizable.

---

## Final strategic judgment

Bond should integrate Greek support as a **core language layer**, not a cosmetic patch.

The right summary is:

> Bond should become bilingual at the surface, language-neutral in its internal contracts, and locale-aware in its user-facing presentation.

That means:

- invocation must become alias-driven and script-tolerant
- text matching must become Unicode-disciplined
- mixed-language inputs must become first-class citizens
- memory and retrieval must stop being effectively mono-language
- GUI strings must move toward real localization resources
- conversation language, preferred response language, and host locale must stop being conflated

If this is done correctly, Greek support will strengthen the whole assistant architecture, not just add a second language.

If it is done lazily, it will create brittle regex debt and false confidence.

---

## Final recommendation

For Bond’s current phase, Greek support should be treated as a dedicated workstream with this actual objective:

> Build a text-first multilingual surface layer for Bond, with robust Greek invocation, Greek/mixed-language understanding, bilingual retrieval grounding, and Greek GUI localization readiness, while preserving a language-agnostic internal capability core.

That is the correct interpretation of the requirement.

---

## Official source notes informing this analysis

- Python Unicode HOWTO on normalization and caseless comparison. citeturn765834search0
- Python `gettext` documentation for internationalization/localization message catalogs. citeturn765834search1
- Unicode Standard Annex #15 on normalization forms. citeturn765834search2
- W3C guidance on internationalization versus localization. citeturn765834search11
- W3C guidance on language tags and locale identifiers. citeturn765834search17
- Python internationalization and locale documentation. citeturn765834search5turn765834search9
