# Greek Language Support and Localization

This document defines Bond's text-first Greek and mixed-language support plan. Voice is explicitly out of scope until the text path is stable.

## Current diagnosis

Bond already has some Greek-aware heuristics and the master plan already mentions English and Greek invocation forms. This is useful but not enough. Current Greek support is partial and heuristic, not yet a bilingual architecture.

## Core rule

Bond should become multilingual at the surface, language-neutral in internal capability contracts, and locale-aware in user-facing presentation.

Greek support must not become a pile of regex patches.

## Required language layers

### 1. Invocation and alias resolution

Bond must recognize being addressed through English, Greek, and mixed forms, including:

- `bond`
- `Bond`
- `Μπόντ`
- `μποντ`
- `hey bond`
- `Bond hey`
- `Τι κάνεις bond`
- `Μπόντ can you tell me the weather?`

The invocation resolver must distinguish address-only, address plus greeting, address plus task, and address embedded in a sentence.

### 2. Canonical text normalization

Bond needs separate representations for:

- raw user text;
- display-preserving normalized text;
- canonical matching text;
- search/retrieval folded text.

Matching should use Unicode-aware normalization, casefold semantics, punctuation normalization, Greek tonos folding for matching only, and mixed-script token preservation.

### 3. Language and mixed-language detection

Bond should classify utterances as `el`, `en`, `mixed`, or `unknown` with confidence. Mixed must be first-class because the user intentionally mixes Greek and English.

### 4. Intent and entity resolution into language-neutral contracts

Greek and English inputs must converge into the same internal capability contracts. Do not duplicate capabilities by language.

### 5. Bilingual memory and retrieval grounding

Memory records need language hints, normalized retrieval forms, alias/entity keys, and original text preservation. Greek queries should retrieve relevant Greek and English stored knowledge when semantically appropriate.

### 6. Response-language policy

Bond should normally respond in the language of the latest substantive user turn unless an explicit user preference overrides it. It should handle mixed-language sessions without forced translation.

### 7. GUI locale and message catalogs

Future GUI/user-facing strings should be localizable through message resources. GUI locale, host locale, active conversation language, and preferred response language are distinct fields.

## Language state model

Required distinct fields:

- `host_locale`
- `ui_locale`
- `preferred_response_language`
- `active_conversation_language`
- `utterance_language`
- `retrieval_normalization_profile`

Do not infer UI locale from every utterance.

## Data structures to define later

### Invocation result

```yaml
addressed_to_bond: true
alias_matched: "μποντ"
invocation_only: false
invocation_position: "middle"
greeting_present: true
residual_text: "τι κάνεις"
```

### Language profile

```yaml
ui_locale: "el_GR"
preferred_response_language: "auto"
active_conversation_language: "mixed"
supported_input_languages: ["en", "el"]
supported_ui_locales: ["en_US", "el_GR"]
```

## What not to do

- Do not patch Greek support with regex alone.
- Do not translate internal capability names into Greek.
- Do not infer UI locale from every utterance.
- Do not over-normalize stored content.
- Do not make Greek support depend on voice-first assumptions.
- Do not couple Greek support to Linux-only assumptions.

## Implementation phases

1. Build normalization, alias registry, language-state object, and host locale profile.
2. Harden bilingual invocation and address-only handling.
3. Expand Greek intent/entity understanding into language-neutral outcomes.
4. Add bilingual memory and retrieval grounding.
5. Introduce GUI locale/message catalog structure.
6. Add acceptance tests and regression tests.

## Acceptance criteria

Serious Greek support requires:

- robust English/Greek/mixed invocation;
- useful Greek input classification;
- mixed-language utterance handling;
- response-language continuity;
- bilingual memory grounding;
- locale separation;
- GUI localization readiness;
- honest fallback when something is partial.

## Current implementation status

Greek support is partial. Bond must not claim full Greek support until the acceptance criteria above are implemented and tested.

## Cross references

- `docs/ARCHITECTURE.md`
- `docs/BEHAVIOR_CONTRACT.md`
- `docs/MEMORY.md`
- `docs/PROBES.md`
- `docs/TESTING.md`
- `docs/CAPABILITIES.md`