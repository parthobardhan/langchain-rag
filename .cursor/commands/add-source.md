# Add Source

Add a new document **source type** (raw text, PDF, image, audio, …) to a RAG app
generated from this scaffold. This is the most common extension engineers make — and
the naive version ("just add a loader branch") is wrong, because the scaffold embeds
with a single text model (`voyage-4-lite`) into a single Atlas index with fixed
`numDimensions`. Each modality forces a different embedding model and, sometimes, a
different index architecture.

The command's job is to **route the modality to the right Voyage model, decide the
chunking, and decide the index/data impact** — then plan the edit. It plans first and
implements only on approval.

Voyage model reference: https://www.mongodb.com/docs/voyageai/models/

## 1. Classify the source and pick the Voyage model

Do not assume `voyage-4-lite`. Route by what the content actually *is*:

| Source | Embed with | Chunk? | Notes |
|--------|-----------|--------|-------|
| Raw text, Markdown | `voyage-4-lite` (default) — or `voyage-4` / `voyage-4-large` for higher quality | ✅ size + overlap | Current scaffold default; one text index |
| Long docs needing chunk-aware context | `voyage-context-3` (120K ctx, chunk-contextual) | ✅ | Better recall on large structured docs |
| Source code | `voyage-code-3` | ✅ (code-aware splitting) | Use when the corpus is code, not prose |
| **PDF — text-layer, prose-heavy** | extract text → `voyage-4-lite` | ✅ size + overlap | Cheapest path; loses layout/tables |
| **PDF — layout/tables/figures/slides/scanned** | per-page image → `voyage-multimodal-3.5` | ❌ (page is the unit) | No OCR needed; preserves visual structure |
| **Image** | `voyage-multimodal-3.5` (direct) | ❌ images don't chunk | Forces the shared-space decision (§3) |
| **Audio** | ❌ no Voyage audio model | ✅ on the transcript | Must transcribe first (§2), *then* it's text |

Finance/legal corpora have domain models (`voyage-finance-2`, `voyage-law-2`, 1024-only)
— mention them if the corpus clearly fits.

## 2. Audio (and scanned PDF) need a pre-stage, not a loader

There is **no Voyage audio embedding model**. "Add audio" is really "add a transcription
pre-stage": ASR (e.g. Whisper) → text → existing text chunking + embedding. Same shape
for scanned PDFs if you choose the text path instead of multimodal (OCR → text).

Consequence: this introduces a dependency **outside the approved stack** (LangChain +
MongoDB + Voyage + OpenAI). Flag it for explicit approval; do not add it silently.
Route the transcription/OCR step into `ingestion/loader.py` so what reaches
`pipeline.py` is already `Document` text — the rest of the pipeline stays unchanged.

## 3. The index decision — one embedding space per index

This is the easy-to-miss judgment and the reason multimodal sources aren't a loader tweak:

- **A query and the stored vectors must come from the same model/space.** You cannot
  embed images with `voyage-multimodal-3.5` and query with `voyage-4-lite` — they live in
  different spaces and won't match. The scaffold embeds the *query* in
  `retrieval/vector_store.py::get_embeddings`; that model must match whatever indexed the data.
- **`numDimensions` must match the model's `output_dimension`.** `voyage-4-lite` defaults
  to 1024; `voyage-multimodal-3` is 1024-only; `voyage-multimodal-3.5` supports
  256/512/1024/2048. The index field in `scripts/create_vector_index.py`, the
  `voyage_embedding_dimensions` setting, and the model must all agree, or retrieval returns nothing.

So when a source needs a *different* model than the rest of the corpus, pick one:

- **(a) Promote the whole app to the multimodal model** — text + images share one space,
  one index. Simplest unified retrieval; re-embed and re-ingest existing text.
- **(b) Caption/describe the non-text source to text** — stays on the existing text model
  and index; cheapest; loses fidelity.
- **(c) Separate collection + index + retrieval path** for the new modality, with its own
  model; combine at query time (multi-retriever). Most flexible, most code.

State which you're choosing and why. (a) and (c) both require index work + re-ingestion.

## 4. Chunking decisions (text-bearing sources)

Only text-bearing content chunks; images and per-page PDF embeddings do not.

- Tunables live in `Settings` (`chunk_size`, `chunk_overlap`) and feed
  `pipeline.py::split_documents` via `RecursiveCharacterTextSplitter`. Do not hard-code.
- Defaults (1000 / 200) suit prose. Adjust by content: tight, factual text → smaller
  chunks; transcripts with timestamps → split on utterance boundaries; PDFs with tables →
  larger overlap or layout-aware splitting so rows aren't severed.
- If you change chunking for *existing* sources, existing vectors are stale → re-ingest.

## 5. Where the code changes land

| Step | File | Change |
|------|------|--------|
| Recognize the new type | `ingestion/loader.py` | extend `SUPPORTED_EXTENSIONS`; add a load branch returning `Document`s with `metadata["source"]` (and any pre-stage: ASR/OCR/caption) |
| Chunking (text sources) | `ingestion/pipeline.py` / `config.py` | reuse `split_documents`; add a tunable only if the type needs different params |
| Embedding model / image embeds | `retrieval/vector_store.py` | if the model changes, update `get_embeddings`; multimodal image embedding is a different API than text and may need a multimodal-capable wrapper |
| Index | `scripts/create_vector_index.py` | only if `numDimensions` changes or a new filter/collection is needed → recreate + wait Active |
| Settings | `config.py` | new model / dimensions / chunk fields, typed and defaulted |
| Tests | `tests/unit/` | parse a fixture of the new type → assert `Document` + `metadata["source"]`; assert chunk count/shape. Mock embeddings — no live keys |

CLI rarely changes: `ingest` already takes a path. Keep modality logic in `loader.py`, not `cli.py`.

## 6. Output

1. **Source + chosen Voyage model** and why (with the rejected alternatives).
2. **Pre-stage?** transcription/OCR/caption — and the approval flag if it adds a dep.
3. **Index decision** — (a)/(b)/(c) from §3, with re-ingest / recreate-index implications.
4. **Chunking** — params and rationale, or "no chunking (image/page unit)".
5. **File-by-file plan** (table above) and the **failing unit test to write first**.
6. **Ordered steps** — test → loader → (pipeline/config) → run `pytest tests/unit` → ingest a sample → query to verify.

Stop for approval before implementing.

## Hard nos (without explicit approval)

- Embedding a source with a model that differs from the query model on the same index
  (silent retrieval failure)
- Adding ASR/OCR/captioning deps outside LangChain + MongoDB + Voyage + OpenAI silently
- Modality/parsing logic in `cli.py`
- `langchain_classic`, `LLMChain`, `.run(...)`; non-LCEL chains
