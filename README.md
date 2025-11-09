# 1) Goal (one sentence)

Take up to 2 adult + up to 2 child photos and metadata, produce a stylized children’s picture book (PDF/EPUB) whose characters are visually consistent with the input photos using **textual character descriptions** extracted by a vision-capable LLM.

---

# 2) Inputs & constraints (what the system must accept)

* Up to 4 images (≤2 adults, ≤2 children), uploaded by the user (or URL).
* For each person: `name`, `declared_age` (int), `role` (`adult`/`child`).
* `style` (predefined descriptor set, e.g., “gentle watercolor”, not trademark names).
* `target_age` (enum: `<1`, `1`, `2`, `3`).
* `num_pages` ∈ {4, 8, 12, 16} (divisible by 4).
* `theme` (string — story guiding motif: stars, dinos, princess, etc.).
* Explicit parental/guardian consent required for minors before processing.

---

# 3) High-level components (minimal set)

1. **Frontend / Client** — UI or API client to upload photos + metadata and retrieve deliveries.
2. **API / Orchestrator (FastAPI)** — accepts requests, validates input, stores metadata, enqueues jobs, exposes status & download endpoints.
3. **Object Storage (S3)** — store uploaded images temporarily and final book assets (PDFs, thumbnails).
4. **Relational DB (Postgres)** — metadata: books, persons, jobs, consents, asset pointers.
5. **Task Queue + Workers (Celery/Redis)** — run background pipeline tasks.
6. **Vision LLM service** — image→structured character JSON (the detailed descriptor schema you defined). Can be a cloud API (vision-capable LLM) or a hosted model.
7. **Planner LLM service** — text LLM that ingests characters + theme + constraints and produces page-by-page plan (text + image prompts).
8. **Image generation service** — SDXL or API image generator that consumes page prompts to create illustrations.
9. **Renderer** — compose text + images into printable PDF/EPUB (HTML → PDF or native renderer).
10. **Admin / Review UI** — show extracted character JSON for user verification if confidence is low.
11. **Monitoring & Logging** — health, tracing, job metrics, error tracking.

---

# 4) Compact dataflow (simplified)

```
[User] -> (upload images + metadata + consent) -> [API]
     API -> store metadata & images -> enqueue job -> [Worker]
Worker:
  1) call Vision LLM -> produce Character JSON -> save
  2) if confidence low -> mark pending_review -> notify user
  3) call Planner LLM (characters + theme + pages) -> page plan JSON
  4) for each page: call Image Generator with (sketch_prompt + render_instructions + style + page action)
  5) assemble images + texts -> Renderer -> output PDF/EPUB -> store in S3
API -> notify user + provide download link
```

---

# 5) Minimal API surface (conceptual)

* `POST /books` — upload photos + metadata + consent; returns `book_id` (queued).
* `GET /books/{id}` — job status, progress, location of generated assets.
* `GET /books/{id}/download` — download final PDF/EPUB.
* `GET /books/{id}/descriptions` — view or edit extracted character JSON (for manual corrections).
* `POST /consent` — record guardian consent (signed/checkbox + metadata).

---

# 6) Data model (essentials)

* **Book**: id, owner, title, num_pages, target_age, theme, style, status, created_at.
* **PersonDescription**: id, book_id, name, declared_age, role, description_json (the detailed descriptor), confidence, created_at.
* **Asset**: id, book_id, type (page_image, cover, pdf), s3_path.
* **ConsentRecord**: id, book_id, signer_name, timestamp, agreement_text_hash.

---

# 7) Key design decisions & rationale (keep it simple)

1. **Text-first approach** — extract *detailed* character JSON from images and reuse textual descriptions for all styles and pages. Rationale: simpler, cheaper, editable, privacy-friendlier.
2. **Confidence gating** — if `confidence_overall < 0.6`, require user review/edit of the JSON. Prevents hallucinated micro-features.
3. **Stateless workers, persistent storage** — workers should be idempotent; everything needed for retry stored in S3/DB.
4. **Style descriptors, not copyrighted names** — present user-friendly named presets (e.g., “Classic Soft Watercolor”) but implement with descriptive style tokens under the hood.
5. **Delete images early** — after descriptions are extracted and consent logged, delete raw photos by default to reduce privacy risk. Keep option to retain if user opts-in.
6. **Cache Character JSON** — reuse same descriptions across variants or future books to save processing/cost.

---

# 8) Privacy, security & legal (must-haves)

* **Consent**: explicit guardian consent for minors; log signature/timestamp and link to image hash.
* **Encryption**: HTTPS in transit; SSE for S3 at rest.
* **Minimal retention default**: keep raw images 7–30 days, allow immediate deletion on demand. Descriptive JSON treated as personal data — protect accordingly.
* **No model training without opt-in**: do not use user photos or descriptions to fine-tune models unless the user explicitly opts in and signs a waiver.
* **Moderation**: automatically run uploaded images through a moderation pipeline (nudity, abuse flags) and block if flagged.
* **Avoid copyrighted style names**: recommend “evocative descriptors” rather than exact copyrighted references.

---

# 9) Non-functional requirements

* **Latency**: job-based (background). Quick feedback must be immediate: initial job accepted, description preview within ~1–5 minutes (depending on LLM). Don’t promise times exactly — provide progress states.
* **Throughput**: design workers to parallelize per page image generation. Cache repeated character descriptions.
* **Reliability**: idempotent tasks; retry with backoff for transient API failures.
* **Cost control**: cache and reuse character descriptions; reuse images where unchanged; batch LLM calls where sensible.

---

# 10) MVP (what to build first — minimal scope)

1. API endpoints for upload + status + download.
2. Vision LLM integration that returns the **detailed character JSON** (mocked OK for local dev).
3. Planner LLM that returns page-by-page JSON (text + image prompt).
4. Simple image generation via a single API (or mocked images for the MVP).
5. HTML → PDF renderer to assemble one simple 4-page book.
6. Consent recording & one moderation check.
7. UI to preview and edit the character descriptions if confidence is low.

MVP excludes: print ordering, user accounts (optional), advanced style editor, multi-language support.

---

# 11) Execution roadmap (phased)

* **Phase 0 — Design & compliance**: finalize descriptor schema & consent wording, pick LLM/image providers.
* **Phase 1 — Core API + Vision LLM**: implement `POST /books`, character descriptor extraction, DB storage, basic UI for review.
* **Phase 2 — Planner + Renderer**: story planner, page prompts, HTML templates, PDF export.
* **Phase 3 — Image generation & refinement**: wire image API, iterate prompt engineering, incorporate render_instructions.
* **Phase 4 — QA & privacy review**: test with consenting users, verify likeness, review retention & moderation.
* **Phase 5 — Scale & polish**: caching, cost optimizations, optional features.

---

# 12) Key risks & mitigations

* **Hallucinated micro-features** — use confidence scores + user verification UI.
* **Privacy breach (children’s photos)** — strict consent, delete images early, encrypt storage.
* **Legal (style/copyright)** — avoid direct style copying; use descriptive style tokens. Consult counsel if commercializing heavily stylized likenesses.
* **Cost of image generation** — cache, reuse character descriptions, batch operations, limit resolution for previews.
* **Model availability / latency** — design for pluggable providers and retries.

---

# 13) Ops & scale notes (simple)

* Run web + worker as containers; use a managed Redis and Postgres for reliability.
* Prefer managed LLM/image APIs for MVP to reduce ops; consider self-hosted SDXL later if volume justifies GPU infra.
* Monitor usage and set rate limits / quotas per user to avoid runaway costs.

---

# 14) Decision checklist (what you should decide next)

1. Which vision-LLM provider (cloud API that accepts images) will you use for descriptor extraction?
2. Which image generation approach for final art: cloud API (fast MVP) or self-hosted SDXL (control, cost at scale)?
3. Retention policy for raw images (days) and whether to allow optional long retention.
4. Do you require mandatory human review for low-confidence descriptors, or auto-proceed?
5. Minimum viable styles preset list for MVP (3–5 styles).