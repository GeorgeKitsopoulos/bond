# Memory System Specification

## Opening Diagnosis

Bond's memory system is not useless, but it is fundamentally shallow. The current implementation behaves more like a fact bucket combined with a recent activity log, a lightweight reflection stream, and heuristic ranking over a small set of local artifacts. That is a reasonable starting point but is far short of a coherent, reliable knowledge architecture.

Existing good instinct: live truth should outrank archived or historical records for current-state questions. This principle is correct and must be preserved and strengthened.

Existing weaknesses that this document addresses directly:

- Fact storage is schema-light and lacks provenance, confidence, and stale-handling discipline.
- Retrieval is still mostly lexical and heuristic. There is no semantic retrieval path for document knowledge.
- There is no first-class document knowledge layer. Ingested documents are not treated as a distinct memory stratum.
- There is no first-class correction memory. Corrections are handled, but not with the override authority they require.
- Provenance and confidence discipline is weak. Records do not carry enough metadata to enable proper trust ranking.
- Reflection is treated too much like evidence. It is not. Reflection is hypothesis and lesson, not verified fact.
- The system risks answering from stale or incidental operational logs when better sources exist or should exist.
- Memory and learning are easy to conflate. This document separates them explicitly.

---

## Core Memory Principles

These principles govern all memory design decisions. They are not aspirational. They define the required behavior.

**Live truth outranks stored recollection for current-state questions.** When a live probe can answer a current-state question, it beats any stored memory of that state, regardless of how recent the stored record is.

**Memory is typed, not one blob.** Different strata have different authority, different retrieval semantics, and different lifecycle rules. Treating all memory as one pool produces unreliable retrieval.

**Reflection is not evidence.** A reflection is a hypothesis, a lesson, or a heuristic derived from operational experience. It may influence caution or routing preferences. It must not be treated as verified fact about the world.

**Archive is history, not automatic current truth.** Archived records describe what was true at a past point in time. They are useful for comparison, recovery, and historical queries. They must not automatically override current durable facts.

**Retrieval must be selective and relevance-driven.** Ambient injection of all memory into every query is wasteful and increases contamination risk. Retrieval lanes must match the type of question being asked.

**Document knowledge is separate from durable fact memory.** An ingested document is not a fact. Its contents may eventually produce candidate facts through promotion, but the document and its chunks are a separate stratum with separate retrieval semantics.

**Ingestion is separate from model training and adaptation.** Placing a file into a knowledge folder causes it to be parsed, chunked, indexed, and made retrievable. It does not cause the model to be fine-tuned or adapted. These are explicitly different operations with different authority, reversibility, and lifecycle requirements. See [docs/KNOWLEDGE_INGESTION.md](KNOWLEDGE_INGESTION.md) for full ingestion design.

---

## Memory Strata

The memory system is divided into six strata. Each stratum has a defined purpose, authority level, and lifecycle rules. No stratum should be collapsed into another.

### Stratum 1: Live Truth Layer

**What it is:** The result of a real-time probe against the live system environment, executing a command, reading a live file, or querying a live API. Live truth is not stored memory. It is acquired on demand.

**Examples:** Output of `uname -a`, current working directory, live service status, current file content read directly from disk.

**Authority level:** Highest for current-state questions. A live probe beats any stored memory for a question about the current state of the environment.

**How it should be used:** When a current-state question can be answered by a live probe, issue the probe first. Use stored memory only as fallback when a probe is unavailable, rate-limited, or inappropriate.

**How it must not be used:** Live truth must not be treated as a substitute for durable fact storage. Probe results are ephemeral and can expire quickly because the state they describe may change. They should not be written into durable fact records without validation and provenance annotation.

---

### Stratum 2: Durable Fact Layer

**What it is:** Structured, validated facts about the system, the user, preferences, environment, and behavior that are intended to be stable over time. These are the canonical records that persist across sessions.

**Examples:** User's preferred shell, confirmed project paths, validated capability boundaries, persistent preferences, confirmed system facts.

**Authority level:** High for stable questions. Durable facts beat recent operational logs for stable configuration and preference questions.

**How it should be used:** Durable facts should be stored with full provenance, confidence scores, verification status, and stale-after timestamps. They should be updated when superseded by a correction or a newer confirmed probe. They must carry a `superseded_by` reference when replaced rather than being silently overwritten.

**How it must not be used:** Durable facts must not be used to answer current-state questions when a live probe is feasible. A durable fact that has passed its `stale_after` threshold must be treated as a candidate for re-verification, not as current ground truth. Incidental operational log entries must not be promoted automatically into durable facts without gated promotion.

---

### Stratum 3: Episodic Operational Memory

**What it is:** A time-ordered record of operational events: actions taken, conversations summarized, tasks completed, errors encountered, and short-term context carried across steps.

**Examples:** Recent chat logs, recent action logs, active context summaries, failure records.

**Authority level:** Low to moderate for stable truth. High for continuity questions about what happened recently.

**How it should be used:** Episodic memory supports continuity. It answers questions like "what did we just do" or "what failed in the last session." It informs routing and caution signals. It is appropriate for recent operational context retrieval.

**How it must not be used:** Episodic memory must not be used as the authoritative source for stable system state. A recent log entry does not override a durable fact for a stable configuration question. Episodic memory has no inherent truth authority beyond "this is what was observed or said at time T."

---

### Stratum 4: Document Knowledge Memory

**What it is:** Knowledge extracted from ingested documents, including PDFs, manuals, notes, screenshots, and any file placed into the knowledge corpus. This stratum is retrieval-first, not fact-first.

**Examples:** Chunked sections from a project manual, extracted text from a scanned diagram, indexed documentation pages.

**Authority level:** High for document-content questions when the source document is trusted and provenance is intact. Lower than durable facts for non-document-content questions.

**How it should be used:** Document Knowledge Memory is retrieved via semantic or hybrid search against the chunk index. Chunks are source-linked and versioned by file hash. Re-ingestion replaces stale chunks when the source file changes. Document knowledge retrieval must preserve modality and provenance, and must not flatten all extracted content into one undifferentiated text blob.

**How it must not be used:** Document chunks must not be treated as verified durable facts about the current live system. They represent the content of a document at ingestion time. They do not automatically produce durable facts. Candidate facts may be promoted from document content through gated promotion. Document knowledge is a separate stratum from durable fact memory.

See [docs/KNOWLEDGE_INGESTION.md](KNOWLEDGE_INGESTION.md) for the full ingestion lifecycle, chunk schemas, provenance tracking, and retrieval architecture.

---

### Stratum 5: Correction Memory

**What it is:** Explicit corrections to prior facts or assumptions, whether issued by the user, detected from system probes, or inferred from persistent conflicts.

**Examples:** "The assistant previously believed path X was the config dir; it is actually Y." "Capability Z was previously marked available; it is not."

**Authority level:** Highest for the domain it corrects. An explicit correction beats an older durable fact for the same domain.

**How it should be used:** Corrections must be stored as first-class records with references to the claims they override. They must influence future retrieval and routing. When a correction is present, the superseded fact must be marked with a `superseded_by` reference to the correction record. Correction records must propagate to retrieval ranking so that retrieval in the corrected domain returns the correction rather than the old fact.

**How it must not be used:** Corrections must not be treated as the same kind of record as durable facts. They require separate priority in retrieval and must not be silently merged into the fact record in a way that loses the correction history.

**Current state:** Correction memory exists in schema but is not yet first-class in retrieval or routing. This is an identified gap requiring explicit work.

---

### Stratum 6: Learned Model Adaptation Layer

**What it is:** Curated fine-tuning data, prompt adaptation patterns, or local adapter records that change model behavior for style, routing, format compliance, or behavioral correction. This is the only layer that represents true model learning.

**Examples:** Curated examples of preferred response format, routing behavior adjustments, style compliance corrections.

**Authority level:** Applies to behavior shaping, not to factual truth. Adaptation records do not override memory strata for truth questions.

**How it should be used:** Adaptation must be sparse, curated, versioned, and reversible. Each adaptation must be traceable to a source decision. Adaptation is appropriate only for stable behavioral patterns that are unlikely to change frequently. A registry of active adaptations must exist so that any adaptation can be identified and reversed.

**How it must not be used:** Arbitrary document ingestion must not automatically produce adaptation records. Fast-changing system state must not be expressed as adapter weights or fine-tuning data. The assumption of large-model infrastructure must not be embedded into this layer. The baseline design must remain compatible with the current lean local model set and treat larger models as optional future escalation, not baseline infrastructure. See [docs/KNOWLEDGE_INGESTION.md](KNOWLEDGE_INGESTION.md) for the explicit training boundary.

---

## Current Implementation Gaps

The current implementation is still weak in several important areas. This section documents those gaps honestly so that they can be addressed in priority order.

**Fact storage is schema-light.** Current fact records lack confidence, verification_status, stale_after, superseded_by, and provenance fields. The schema must be enriched.

**Retrieval is still mostly lexical and heuristic.** There is no semantic retrieval path for document knowledge. Ranking is based on simple ordering and type priority, not relevance scores or embedding similarity.

**`active_context.txt` is useful operationally but too lossy to be the central knowledge representation.** It provides useful session continuity but loses structure, provenance, and confidence information. It must not be treated as the primary memory surface.

**Reflection is fragile and must not be treated as verified truth.** The reflection mechanism produces useful heuristics but the current implementation does not enforce the distinction between hypothesis and evidence. This creates contamination risk.

**Archive handling is retention hygiene, not rich historical retrieval.** Current archive rotation manages file size and recency but does not provide queryable historical retrieval. Archive is currently useful for recovery and inspection but must not be treated as a rich historical knowledge store.

**Correction memory is not first-class yet.** Corrections are stored but do not yet have priority override behavior in retrieval. This is a known gap that must be addressed before correction memory can be relied upon.

**Document knowledge is not first-class yet.** There is no ingestion pipeline, no chunk store, no embedding index, and no semantic retrieval path for documents. The architecture calls for this layer but it has not been built.

**Memory and learning are too easy to conflate.** Without explicit documentation of the separation between ingestion, memory, and adaptation, operators may conflate them and produce incorrect system behavior. This document and [docs/KNOWLEDGE_INGESTION.md](KNOWLEDGE_INGESTION.md) together provide the canonical separation.

---

## Retrieval Lanes

Retrieval is not one generic operation. Different question types require different retrieval strategies. The five retrieval lanes below are the canonical paths. Retrieval logic must route to the correct lane rather than querying all sources indiscriminately.

### Lane 1: Live Truth Lookup

**When to use:** Questions about current system state, current configuration, current file content, current service status, or anything that requires ground truth about right now.

**Sources to prioritize:** Live probe execution. Durable facts as fallback when probing is unavailable.

**Must not override:** Nothing. Live truth is the highest-authority source for current-state questions.

---

### Lane 2: Durable Fact Lookup

**When to use:** Questions about stable configuration, user preferences, validated capability boundaries, or any domain where a curated fact record should exist.

**Sources to prioritize:** Correction memory first for the queried domain. Durable facts second. Episodic memory as fallback only when no durable fact exists.

**Must not override:** Live truth for current-state questions. Live truth always wins when a probe is possible.

---

### Lane 3: Recent Episodic Lookup

**When to use:** Questions about recent actions, recent failures, current task context, or conversational continuity within or across recent sessions.

**Sources to prioritize:** Recent action logs, recent chat logs, active context summary.

**Must not override:** Durable facts for stable configuration or preference questions. Episodic records are low-authority for stable truth.

---

### Lane 4: Document Knowledge Retrieval

**When to use:** Questions that require content from ingested documents, such as referencing a manual, searching a knowledge corpus, or looking up a procedure from an indexed file.

**Sources to prioritize:** Semantic or hybrid search over the chunk index. Source-grounded chunks ranked by relevance and source trust weight.

**Must not override:** Durable facts for factual system-state questions. Document chunks provide document content, not live system state.

---

### Lane 5: Archive and History Lookup

**When to use:** Historical queries, recovery scenarios, comparison of past and present state, or investigation of past events.

**Sources to prioritize:** Archive files, historical log segments, prior reflection records.

**Must not override:** Current durable facts. Archive records are history, not current truth. Archive retrieval must be opt-in and query-driven, not ambient.

---

## Ranking Rules

When multiple sources are available for a query, the following ranking rules apply. These rules are explicit and must not be overridden by convenience.

1. **Live probe beats stored memory for current-state questions.** If the question is about the present state of the system and a probe is feasible, the probe answer ranks above any stored record.

2. **Explicit correction beats older fact.** If a correction record exists for the domain being queried, it takes priority over the durable fact it supersedes.

3. **Durable fact beats incidental recent log for stable questions.** For questions about stable configuration or preferences, a curated durable fact record outranks recent operational log entries.

4. **Strong source-grounded document chunk beats unrelated recent log.** For knowledge questions, a well-sourced document chunk from the knowledge corpus outranks an unrelated operational log entry.

5. **Source-grounded chunk beats reflection for knowledge questions.** Reflection is hypothesis. A document chunk with intact provenance is a better source for knowledge content than a reflection.

6. **Reflection may influence caution, not truth.** A reflection may correctly inform routing preferences or risk assessments. It must not be treated as a factual claim about the system or the world.

7. **Archive should be opt-in and query-driven, not ambient.** Archive records must not be injected into every retrieval operation. They are relevant only when a historical query is explicitly issued.

---

## Schemas

The following schemas define the canonical structure for durable memory records. These are the minimum required fields. Implementations must not omit the provenance, confidence, or lifecycle fields.

### Durable Fact Schema

```
id:                  unique identifier
kind:                "fact"
subject:             entity the fact describes
predicate:           relationship or attribute
value:               the fact content
source_type:         "probe" | "user_statement" | "document" | "system_config" | "inference"
source_ref:          reference to originating source (file path, log id, document id, etc.)
confidence:          float 0.0–1.0
verification_status: "verified" | "unverified" | "stale" | "superseded"
created_at:          ISO 8601 timestamp
updated_at:          ISO 8601 timestamp
stale_after:         ISO 8601 timestamp or null
superseded_by:       id of correction or replacement record, or null
bucket:              logical durable-fact grouping such as preferences | environment | workflows | aliases
key:                 stable key within the bucket
language:            language of the fact content where relevant
aliases:             list of equivalent names or entity aliases where relevant
supporting_documents:list of supporting document ids or chunk refs
contradictions:      list of known conflicting record ids, if any
derived_from:        source record ids when the fact was derived rather than directly asserted
modality:            optional modality marker when the fact originated from document/image extraction
notes:               free-form implementation or trust note
```

These enrichment fields are canonical target fields even if the current implementation does not yet persist all of them. Document-backed facts must preserve traceability to supporting documents and chunks. Contradictions and derivation links exist to reduce silent contamination and overconfident truth-ranking.

### Correction Schema

```
id:                  unique identifier
kind:                "correction"
domain:              subject area or fact domain being corrected
original_claim_id:   id of the fact or assumption being superseded (if known)
original_claim_text: human-readable summary of the prior claim
corrected_claim:     the corrected content
source_type:         "user_explicit" | "probe_conflict" | "document_conflict" | "inferred"
source_ref:          reference to originating source
confidence:          float 0.0–1.0
applies_to:          list of fact ids, domains, or routing contexts affected
created_at:          ISO 8601 timestamp
reason:              short explanation for why the correction was introduced
updated_at:          ISO 8601 timestamp
priority:            correction precedence level for ranking conflicts
status:              "active" | "superseded" | "withdrawn" | "draft"
correction_of:       explicit linkage to corrected fact/correction record lineage
supporting_documents:list of supporting document ids or chunk refs
```

Corrections remain first-class records, not inline edits to fact records. Correction history must remain visible through `correction_of`, `original_claim_id`, and `superseded_by` relationships. Correction priority exists because some corrections are explicit user overrides while others are lower-confidence inferred conflicts.

### Episodic Event Schema

```
id:                  unique identifier
kind:                "action" | "chat_turn" | "failure" | "reflection"
session_id:          identifier of the session in which the event occurred
summary:             short human-readable description
detail_ref:          reference to full log record or file path
outcome:             "success" | "failure" | "partial" | "unknown"
created_at:          ISO 8601 timestamp
tags:                list of topic or capability tags
ts:                  normalized event timestamp for ordering and joins
structured_payload:  structured event payload for downstream analysis
severity:            "low" | "medium" | "high" | "critical" | "n/a"
references:          related record ids, document ids, or chunk refs
capability:          capability identifier associated with the event, if any
```

Episodic records are continuity artifacts, not durable truth. Richer event metadata exists to support later promotion, retrieval filtering, and failure-pattern analysis without promoting raw logs to facts.

### Archive and History Metadata Schema

```
id:                  unique identifier
kind:                "archive_record"
original_record_id:  id of the record that was archived
record_type:         the stratum type of the archived record
archived_at:         ISO 8601 timestamp
reason:              "rotation" | "superseded" | "manual" | "retention_policy"
retrieval_path:      file path or storage reference to the archived content
summary:             short human-readable description of what was archived
references:          related record ids, fact ids, correction ids, or chunk refs
source_summary:      concise source provenance summary for archived content
validation_state:    "valid" | "partial" | "unverified" | "invalid"
```

For document and chunk schemas, see [docs/KNOWLEDGE_INGESTION.md](KNOWLEDGE_INGESTION.md).

## Schema versioning and migration

Memory stores require explicit schema versions and versioned migrations.
Durable facts and correction records must not silently break due to schema drift in retrieval, ranking, or policy paths.
See [docs/SCHEMAS.md](SCHEMAS.md) and [docs/SURVIVABILITY.md](SURVIVABILITY.md).

## Language metadata and bilingual retrieval

Memory records should preserve original text, include a language hint, and maintain a normalized retrieval form for matching.
Entity resolution should support alias/entity keys so Greek and English references can map to shared internal targets when semantically appropriate.
Bilingual retrieval should allow Greek ↔ English retrieval when relevant while avoiding over-normalization of stored facts.

---

## Promotion Rules

Logs and ingested documents may produce candidate facts or candidate corrections. Promotion from candidate to durable record is gated and must not happen automatically without one of the following conditions being met:

- **Repeated confirmation:** The same fact or pattern appears across multiple independent sources over time.
- **Trusted-source origin:** The record originates from a probe result, a verified system config, or an explicit user statement with high confidence.
- **Explicit user approval:** The user explicitly approves the promotion of a candidate fact into durable memory.
- **Stability over time:** The candidate has been consistently observed without contradiction over a defined period.

Transient noise, incidental log entries, and partial observations must not be promoted into durable memory. The promotion mechanism must enforce these gates. Uncontrolled promotion is a primary contamination risk.

---

## Reflection and Archive Rules

### Reflection Rules

Reflections are hypotheses and lessons derived from operational experience. They are not evidence. The following rules apply to all reflection records:

- A reflection must never be ranked above a durable fact or a live probe result for a truth question.
- A reflection may be used to adjust routing preferences, flag potential risks, or surface patterns for human review.
- Reflections must be stored with explicit `kind: "reflection"` and must not be mixed into the durable fact or correction strata.
- The reflection generation mechanism is fragile in the current implementation. Reflections must be treated as low-confidence heuristic outputs until a more robust generation and validation process exists.

### Archive Rules

- Archive records describe what was true or what happened at a prior point in time.
- Archive retrieval is opt-in and query-driven. Archive records must not be injected into ambient retrieval for current-state or stable-state questions.
- Archive rotation is a retention hygiene function. It manages log size and recency. It is not a rich historical retrieval system.
- Future work should improve archive retrieval quality, but current documentation must not overstate what the archive currently provides. The archive is useful for recovery, inspection, and historical comparison. It is not a queryable knowledge base today.

---

## Evaluation Criteria

Memory quality must be evaluated against the following criteria. These criteria apply to both design review and runtime behavior assessment.

**Retrieval relevance:** Does the retrieval lane return records that are genuinely relevant to the question asked? Is irrelevant episodic or archive content excluded from stable-state queries?

**Truth discipline:** Does the system correctly prioritize live probes over stored memory for current-state questions? Does correction memory override superseded facts? Does reflection stay out of truth rankings?

**Contamination resistance:** Is it possible for a transient log entry, an unvalidated reflection, or stale archived content to contaminate the answer to a current-state or stable-state question?

**Provenance quality:** Do stored records carry sufficient source_type, source_ref, confidence, and verification_status information to allow a reader or downstream system to assess trustworthiness?

**Deletion and update behavior:** When a record is superseded or deleted, is the supersession properly recorded? Are stale records flagged rather than silently serving as current truth?

**Adaptation reversibility:** Can any learned model adaptation be identified, traced to its source decision, and reversed without affecting other adaptation records?

---

## Phased Evolution

The memory system must evolve in the following order. Later phases depend on the foundations built in earlier phases.

**Phase 1 — Formalize memory ontology.** Implement the enriched schemas defined in this document. Add provenance, confidence, verification_status, stale_after, and superseded_by to all durable fact records, along with entity scope and aliases, supporting document links, contradiction tracking, richer correction metadata, and richer episodic event metadata. Formalize correction memory as first-class.

**Phase 2 — Build document knowledge memory.** Implement the ingestion pipeline, chunk store, and provenance tracking defined in [docs/KNOWLEDGE_INGESTION.md](KNOWLEDGE_INGESTION.md). This is a prerequisite for all subsequent document-aware retrieval work.

**Phase 3 — Add semantic retrieval.** Replace or augment lexical retrieval with embedding-based or hybrid retrieval for document knowledge. Extend to durable fact retrieval as the fact corpus grows.

**Phase 4 — Add fact and correction promotion.** Implement gated promotion from episodic logs and document chunks into candidate durable facts. Add the promotion gates described in the Promotion Rules section.

**Phase 5 — Improve historical and archive retrieval.** Build queryable archive access beyond the current rotation and file-inspection model.

**Phase 6 — Add curated local adaptation.** Only after Phases 1 through 5 are stable, introduce curated fine-tuning or adapter-based model adaptation. Adaptation must be sparse, versioned, and reversible.

---

## Cross References

- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — System architecture and component boundaries
- [docs/KNOWLEDGE_INGESTION.md](KNOWLEDGE_INGESTION.md) — Document ingestion lifecycle, chunk schemas, provenance, and retrieval architecture
- [docs/BOND_PROJECT_MASTER_PLAN.md](BOND_PROJECT_MASTER_PLAN.md) — Overall project direction and priorities
- [ROADMAP.md](../ROADMAP.md) — Sequenced roadmap and milestone tracking
- [docs/STATE.md](STATE.md) — Current system state and active context conventions
- [docs/TESTING.md](TESTING.md) — Testing strategy and evaluation approach
