# Knowledge Ingestion and Document Retrieval Design

## Scope and Purpose

This document is the canonical design specification for document knowledge ingestion and document-aware retrieval in the Bond system. It covers the full ingestion lifecycle, file change management, multimodal document handling, provenance tracking, retrieval architecture, and the explicit boundary between ingestion, memory, and model adaptation.

This document is explicitly separate from user memory and from learned model adaptation. Those domains are covered in [docs/MEMORY.md](MEMORY.md). The three domains must not be conflated:

- **Memory** is facts, preferences, corrections, and episodic operational state.
- **Knowledge** is documents, PDFs, screenshots, manuals, notes, and chunked corpora made retrievable.
- **Learning** is model adaptation, fine-tuning, and adapter-based behavior change.

---

## Current-State Reality

The current repository direction recognizes the need for document ingestion and document-aware retrieval. However, the following capabilities do not yet exist in the current implementation:

- A complete ingestion lifecycle with defined stages and validation.
- File lifecycle management including change detection, reindexing, and deletion propagation.
- A re-ingestion strategy for modified or updated source files.
- Semantic document retrieval over a chunk index.
- Strong provenance discipline at the chunk level.
- A first-class document store or chunk store.
- A multimodal document parsing path covering PDFs, scanned images, and screenshots.

This document defines the target architecture so that implementation proceeds toward a coherent design rather than accumulating ad hoc ingestion logic. Claims in this document describe the target. Claims about current state are explicitly marked as such.

---

## Core Separation

The risk of conflating memory, knowledge, and learning is high enough to warrant explicit definition of each domain and the failure modes that arise when they are mixed.

**Memory** covers structured facts about the system, user preferences, corrections to prior beliefs, and episodic records of recent operations. Memory records are typed, provenance-tracked, and managed through promotion gates. See [docs/MEMORY.md](MEMORY.md).

**Knowledge** covers the content of documents that have been ingested into the system. A knowledge record is a chunk of content extracted from a source file, linked to its provenance, indexed for retrieval, and served in response to queries about document content. Knowledge is not memory. An ingested document does not automatically produce facts.

**Learning** covers changes to model behavior through fine-tuning, prompt adaptation patterns, or local adapters. Learning is the only layer that actually changes what the model produces independent of retrieval context. Learning must be curated, versioned, and reversible. It is not a consequence of document ingestion.

Consequences of conflating these domains:

- **Over-training instead of retrieving.** If ingested documents are treated as training targets, the system attempts to encode content in model weights rather than retrieving it at inference time. This is expensive, unreliable, and non-reversible without re-training.
- **Storing document noise as facts.** If document chunks are promoted automatically into durable fact memory, low-quality, outdated, or contradictory document content contaminates the fact store.
- **Mixing logs with knowledge.** If operational logs are indexed alongside knowledge documents without stratum separation, retrieval conflates what the system did with what a document says.
- **Losing provenance.** If documents are parsed and their content is stored without source linkage, retrieved content cannot be verified, attributed, or updated when the source changes.

---

## Target Architecture Components

The target ingestion and retrieval architecture consists of the following components. Not all components exist in the current implementation. This section defines what must be built.

**Ingestion controller / orchestrator:** Manages the ingestion pipeline. Receives file detection events, coordinates stage execution, handles retry and failure quarantine, and emits ingestion metrics.

**Raw document store:** Stores original source files or references to them with their original content intact. Provides the ground truth for re-ingestion and hash-based change detection.

**Parsed content store:** Stores the output of document parsing per source file, including extracted text, structure metadata, page or section segmentation, modality annotations, and extraction method records.

**Metadata index:** Stores per-document and per-chunk metadata including source file path, document id, file hash at ingestion time, ingested_at timestamp, parser method, confidence, modality, and chunk references. Enables lifecycle management, stale detection, and change tracking.

**Embedding index / vector retrieval layer:** Stores vector embeddings of chunks for semantic or hybrid retrieval. Must support update of individual chunk embeddings when a source file changes, and deletion of chunk embeddings when a source file is removed.

**Retrieval interface:** Accepts natural-language or structured queries and executes retrieval across the chunk index. Applies source trust weighting, reranking, and multilingual alignment. Returns ranked chunks with full provenance.

**Candidate fact and correction promotion lane:** A gated pathway from document content to candidate durable facts or candidate corrections. Candidates require explicit approval before entering durable memory. See the Candidate Fact and Correction Promotion section.

**Adaptation boundary and registry:** An explicit boundary that prevents document ingestion from automatically producing model adaptation records. Maintains a registry of active adaptations with source traceability.

---

## Ingestion Lifecycle

The ingestion pipeline is a numbered sequence of stages. Each stage must complete successfully before the next begins. Stage failures must be logged, quarantined, and retried or flagged for manual review.

1. **File detection.** The ingestion controller detects a new or changed file in the designated knowledge folder or receives an explicit ingestion request. Detection may be event-driven, hash-polling-based, or manually triggered in the current phase.

2. **Type classification.** The file is classified by MIME type, extension, and content sniffing. Classification determines which parsing path will be used. Classification failures must quarantine the file rather than attempting to parse with a default handler.

3. **Parsing by modality.** The file is parsed according to its classified modality. Native text extraction is preferred for formats that support it. OCR or visual interpretation is applied selectively for scanned or image-heavy content. Parsed output is stored in the parsed content store with method annotation.

4. **Normalization and enrichment.** Extracted text and structure are normalized to a consistent internal representation. Section boundaries, headings, table structures, and other structural signals are preserved where available. Metadata such as title, author, creation date, and source path are extracted or inferred.

5. **Chunking.** Normalized content is divided into retrieval units. Chunking strategy must respect natural boundaries such as sections, paragraphs, and pages rather than applying fixed character counts blindly. Chunks must retain context pointers including document id, section reference, and page or offset metadata.

6. **Embedding.** Each chunk is embedded using the active embedding model. Embeddings are stored in the embedding index with chunk id references. The embedding method and model version are recorded in chunk metadata.

7. **Indexing and metadata linking.** The chunk and its metadata are written to the metadata index and the embedding index. The document-level metadata index record is updated to reflect the completed ingestion. All chunk records include a reference to the source document record.

8. **Validation and exposure.** The ingested document is validated for completeness. Required metadata fields are checked. The document is marked as available in the retrieval interface. Validation failures must quarantine the document rather than exposing it with missing provenance.

---

## File Change and Reindexing Strategy

The ingestion system must handle the full lifecycle of source files, not only initial ingestion.

**Hash-based change detection.** Every ingested source file is stored with a cryptographic hash of its content at ingestion time. On subsequent detection events, the current hash is compared to the stored hash. If the hashes match, the file is already current and no reindexing is required. If the hashes differ, reindexing is triggered.

**Incremental reindexing.** When a source file changes, the prior chunk set for that document is marked stale and a fresh ingestion pipeline run is initiated. The new chunks replace the prior chunks in the embedding index. Prior chunks must not remain active in retrieval after a successful reindex of the same source.

**Deletion propagation.** When a source file is removed from the knowledge folder, all associated chunks, embeddings, and metadata records must be removed from the retrieval system. Orphaned chunks that reference a deleted source must not remain active in retrieval.

**Versioning and supersession.** Prior versions of a document's chunk set must be retained in the metadata index for provenance and history purposes. Active retrieval must serve only the current chunk set. The metadata index must record which chunk set version is active for each document.

**Stale-chunk prevention.** The ingestion controller must prevent scenarios in which a mix of current and prior-version chunks for the same document are simultaneously active in retrieval. Reindexing must be atomic with respect to the active chunk set.

**Duplicate prevention.** Files with identical content hashes that map to different paths must be detected and flagged. The system must not create redundant duplicate chunk sets for content that is physically identical.

Schema governance note: document manifests, parsed chunks, and embedding indexes require explicit schema versions.
Reindexing and migration paths must be rollback-aware so schema or index changes do not silently corrupt active retrieval.
See [docs/SCHEMAS.md](SCHEMAS.md) and [docs/SURVIVABILITY.md](SURVIVABILITY.md).

---

## Multimodal Handling

Document ingestion must support multiple content modalities. The handling strategy for each modality must be explicit.

**Native PDF text extraction.** For PDF files that contain extractable text layers, native text extraction is the preferred method. It produces the highest-fidelity text output and preserves structural metadata. OCR must not be applied to pages that have readable native text layers.

**Selective OCR for scans and image-heavy pages.** OCR should be applied only to pages or regions where native text extraction returns no content or very low confidence output. OCR text must be annotated with the extraction method so that downstream consumers know its origin and fidelity.

**VLM or visual interpretation for image content.** For standalone images, screenshots, diagrams, and other visual content where neither native extraction nor OCR produces meaningful text, a visual language model interpretation may be used. Visual interpretation output must be stored with its modality annotation and must not be treated as equivalent to native-extracted text.

**Unified representation with modality preservation.** All extracted content is stored in the parsed content store using a unified internal schema. The schema must include a modality field that records whether the content came from native extraction, OCR, VLM interpretation, or other methods. This metadata must propagate to chunks.

**Prohibition on modality flattening.** OCR text, VLM description output, and native-extracted text are not equivalent in fidelity or reliability. The system must not flatten all three into one undifferentiated text blob. Retrieval consumers must be able to apply different confidence weights based on extraction method.

---

## Retrieval Quality System

Document knowledge retrieval must be a first-class retrieval lane, as described in [docs/MEMORY.md](MEMORY.md). The following requirements apply to the document retrieval subsystem.

**Semantic retrieval for document knowledge.** Retrieval over the document knowledge corpus must use embedding-based or hybrid search, not only lexical keyword matching. Semantic retrieval enables the system to return relevant chunks even when the query phrasing does not literally match the chunk text.

**Reranking.** An initial retrieval pass may return a wider candidate set. A reranking step must then reorder candidates by a combination of semantic relevance, source trust weight, recency, and modality confidence before presenting the final result set.

**Source trust weighting.** Not all document sources are equally trustworthy. Official system documentation, verified configuration references, and user-approved sources must be weighted higher than unverified or automatically collected documents. Source trust weights must be configurable and transparent.

**Multilingual retrieval alignment.** The system must not fail or degrade silently for queries or documents in languages other than the dominant training language of the embedding model. Multilingual retrieval alignment must be an explicit design consideration when selecting embedding models and chunking strategies.

**Source-grounded chunking.** Chunks must retain enough context to be interpretable in isolation. A chunk that consists of a single sentence stripped of all surrounding context and structure is a low-quality retrieval unit. Chunking must preserve section headings, entity context, and structural anchors where possible.

**Isolation from unrelated operational logs.** Document knowledge retrieval must be isolated from episodic operational memory. Retrieval over the document corpus must not be dominated by unrelated recent action logs or reflection records. Lane isolation as defined in [docs/MEMORY.md](MEMORY.md) must be enforced at the retrieval interface.

---

## Provenance and Trust Model

Every knowledge unit in the system must carry a full provenance record. The following fields are required on all chunk and document records.

```
source_file:          path to the originating source file
document_id:          unique identifier for the document in the document store
chunk_id:             unique identifier for this chunk
parser_method:        extraction method used ("native_pdf" | "ocr" | "vlm" | "plaintext" | etc.)
ingested_at:          ISO 8601 timestamp of when this chunk was ingested
file_hash:            cryptographic hash of the source file at ingestion time
confidence:           float 0.0–1.0 representing extraction quality
modality:             "text" | "ocr_text" | "vlm_description" | "structured" | etc.
transformation_steps: ordered list of processing stages applied to produce this chunk
source_page:          page number or section reference within the source document, if applicable
source_section:       section heading or structural anchor, if available
language:             detected language of the chunk content
warnings:             list of extraction warnings or quality flags encountered during ingestion
validation_state:     "valid" | "quarantined" | "stale" | "superseded"
```

These fields must propagate from the document-level metadata record to individual chunk records. A chunk without provenance is not a valid retrieval unit and must not be exposed through the retrieval interface.

---

## Ingestion Operations Control

The ingestion system must be operable, observable, and fault-tolerant. The following operational requirements apply.

**Ingestion queue.** Ingestion work items must be queued. Files detected for ingestion must enter the queue rather than being processed synchronously in the detection path. Queue depth must be observable.

**Retry logic.** Transient failures at any pipeline stage must trigger retry with backoff. The maximum retry count and backoff parameters must be configurable.

**Backpressure handling.** When the ingestion queue depth exceeds a threshold, new detection events should be held or rate-limited rather than causing unbounded memory growth in the queue.

**Failure quarantine.** Files that exhaust retry attempts without successful ingestion must be placed in a quarantine state. Quarantined files must be flagged for manual review and must not block the ingestion of other files.

**Ingestion logs and metrics.** Each ingestion run must produce a structured log record covering: file path, file hash, stages completed, stages failed, chunk count produced, duration, and final validation state. Aggregate metrics such as queue depth, ingestion rate, quarantine count, and reindex rate must be observable.

**Explicit validation state.** Every document and chunk in the system must carry an explicit validation_state field as defined in the provenance schema. Retrieval must only serve chunks with validation_state of "valid".

---

## Storage Architecture

The following storage components are required. Each must be implemented as a distinct store with its own access interface.

**Raw document store.** Stores original source files or content-addressed references. Used as the ground truth for re-ingestion and hash comparison. Must support content-addressed retrieval, deletion, and versioning.

**Parsed content store.** Stores structured parser output per document, including extracted text, structural metadata, modality annotations, and per-page or per-section segmentation. Must support update on reindex and deletion when a source is removed.

**Embedding index.** Stores vector embeddings per chunk. Must support insert, update, and delete operations at the chunk level. Must support approximate nearest neighbor retrieval with filtering by metadata fields such as source trust weight, modality, and validation state.

**Metadata index.** Stores the full provenance and lifecycle metadata for each document and chunk. Must support queries by document id, source file path, file hash, validation state, and ingestion timestamp.

The architecture must support:

- Fast retrieval under query load.
- Atomic updates to the active chunk set during reindexing.
- Clean deletion propagation when source files are removed.
- Scaling to a larger document corpus over time.
- History and supersession tracking so that prior chunk set versions are retained for provenance even after reindexing.

---

## Drop-Folder Semantics

This section defines the canonical behavior for the "drop files into a folder so the AI can learn" interaction pattern. This is a mandatory specification.

**Default behavior is ingestion and retrieval, not immediate model training.** When a user places a file into the designated knowledge folder, the default action is: detect the file, classify it, parse it, chunk it, embed it, index it, and make it retrievable with provenance. The file does not become training data. The model is not fine-tuned or adapted as a result of the file being placed in the folder.

**The ingestion pipeline is the default response to a knowledge folder event.** The complete pipeline described in the Ingestion Lifecycle section is the correct and intended response. No shortcut that skips provenance tracking, validation, or chunk indexing is acceptable as the default behavior.

**Current phase may use manual or batch-triggered ingestion.** In the current implementation phase, the ingestion pipeline may be triggered manually or in batch rather than by a continuous file watcher. This is an acceptable interim implementation. However, the architecture must explicitly support a designated watched knowledge folder in a later phase. The target behavior is automatic detection on file placement.

**Knowledge files do not become training data by default.** A document placed in the knowledge folder is an ingestion target. It is not a fine-tuning corpus. Promotion of document content into durable facts requires gated promotion as described in [docs/MEMORY.md](MEMORY.md). Promotion of document content into model adaptation data requires explicit curation decisions as described in the Training Boundary section below.

---

## Candidate Fact and Correction Promotion

Ingested document content may contain information that is relevant to the durable fact store. The following rules govern how document content may influence durable memory.

Document chunks are not durable facts. A statement found in an ingested document is document content, not a system fact. It must not be automatically written into the durable fact store.

Document content may produce candidate facts or candidate corrections. The ingestion pipeline or a downstream analysis step may identify statements in document content that are candidates for promotion to durable facts or corrections. These candidates must be stored as candidate records with clear provenance linking back to the source chunk.

Promotion from candidate to durable record requires explicit gating. The promotion gates defined in [docs/MEMORY.md](MEMORY.md) apply to document-sourced candidates as they do to all other promotion candidates. Repeated confirmation, trusted-source origin, explicit user approval, or stability over time are required before a candidate becomes a durable record.

Promotion must not be automated without human oversight in the current phase. Until the gated promotion mechanism is robust and validated, document-sourced candidate facts must require explicit user approval.

---

## Training Boundary

The following rules govern the relationship between document ingestion and model training or adaptation.

**Arbitrary PDFs, images, and manuals are not the default fine-tuning target.** The documents placed in the knowledge folder are intended for retrieval. They are not curriculum for fine-tuning runs. Fine-tuning or adapter-based adaptation is a separate, explicitly-triggered operation with its own data preparation and curation requirements.

**Training is only for behavior, style, routing, and format compliance after curation.** If adaptation occurs, it should address stable behavioral patterns such as response format compliance, routing preferences, or style alignment. It must not attempt to encode fast-changing system state, document content, or operational log patterns into model weights.

**Fast-changing system state must not be expressed as adapter weights or fine-tuning data.** System state changes faster than adaptation cycles. Attempting to learn current system state through fine-tuning produces outdated, unreliable model behavior. System state must be handled through live probes and durable fact memory, not model adaptation.

**Large-model dependence must not be assumed for the baseline.** The ingestion and retrieval architecture must not require a large hosted model as baseline infrastructure. The system must be designed to function with the current lean local model set. Larger models are treated as optional future escalation capability for tasks that genuinely require them, not as the default retrieval or parsing backend.

**Adaptation must be sparse, curated, versioned, and reversible.** Every active adaptation record must be traceable to the decision that produced it. Any adaptation must be reversible without affecting other adaptation records. The adaptation registry as described in [docs/MEMORY.md](MEMORY.md) must be maintained.

---

## Evaluation Criteria

The ingestion and retrieval system must be evaluated against the following criteria continuously during development and operation.

**Retrieval relevance.** Do queries return chunks that are genuinely relevant to the question? Is the ranking order defensible given source trust weights and semantic similarity scores?

**Provenance visibility.** Can every returned chunk be traced back to its source file, extraction method, ingestion timestamp, and validation state? Are these fields visible to the retrieval consumer?

**Reindex and update correctness.** When a source file changes, are stale chunks correctly replaced? Do old chunks become inaccessible in retrieval after a successful reindex?

**Deletion propagation.** When a source file is removed, are all associated chunks, embeddings, and metadata records removed from active retrieval?

**Contamination resistance.** Is it possible for a document-sourced chunk to be served as a durable system fact without explicit promotion? Is it possible for an unrelated operational log entry to appear in document knowledge retrieval results?

**Doc chunk ranking quality.** Are higher-quality chunks ranked above lower-quality chunks given equivalent semantic relevance? Do modality confidence levels influence ranking appropriately?

**Multilingual retrieval quality.** Does retrieval degrade gracefully for non-dominant-language content? Are multilingual queries matched to relevant chunks in the correct language?

---

## Priority Order

Implementation of the knowledge ingestion system must follow this priority order. Later items must not be attempted before earlier items are stable.

1. **Ingestion pipeline.** Implement the full numbered pipeline from file detection through validation and exposure. All stages must produce structured logs and carry provenance.

2. **Semantic retrieval.** Implement embedding-based or hybrid retrieval over the chunk index. Replace or augment lexical-only retrieval for document knowledge queries.

3. **Provenance tracking.** Ensure all chunk and document records carry the full provenance schema defined in this document. Retrieval must not expose chunks with incomplete provenance.

4. **Multimodal support.** Add modality-specific parsing paths for PDFs with native text, scanned documents requiring OCR, and image content requiring visual interpretation. Apply modality annotations throughout.

5. **Reindexing and versioning.** Implement hash-based change detection, incremental reindexing, deletion propagation, and stale-chunk prevention.

6. **Promotion discipline.** Implement the gated candidate fact and correction promotion lane with explicit approval requirements.

7. **Curated local adaptation.** Only after the above are stable, introduce any curated model adaptation workflow. Adaptation must not begin until the document knowledge and memory layers are reliable enough to make adaptation genuinely necessary rather than a workaround for retrieval deficiencies.

---

## Documentation Review Declaration

Reviewed and aligned against:

- [docs/STATE.md](STATE.md)
- [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/BEHAVIOR_CONTRACT.md](BEHAVIOR_CONTRACT.md)
- [docs/CURRENT_PATHS.md](CURRENT_PATHS.md)
- [docs/TESTING.md](TESTING.md)
- [docs/INSTALLATION.md](INSTALLATION.md)
- [docs/BOND_PROJECT_MASTER_PLAN.md](BOND_PROJECT_MASTER_PLAN.md)
- [docs/PLANNING_INTERFACE.md](PLANNING_INTERFACE.md)

External planning context has been explicitly supplied in the authoring prompt for this document. No external issue or milestone context beyond what is documented here has been assumed.

---

## Cross References

- [docs/MEMORY.md](MEMORY.md) — Memory system specification, strata, retrieval lanes, and promotion rules
- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — System architecture and component boundaries
- [docs/BOND_PROJECT_MASTER_PLAN.md](BOND_PROJECT_MASTER_PLAN.md) — Overall project direction and priorities
- [ROADMAP.md](../ROADMAP.md) — Sequenced roadmap and milestone tracking
- [docs/STATE.md](STATE.md) — Current system state and active context conventions
- [docs/TESTING.md](TESTING.md) — Testing strategy and evaluation approach
