# NyaySetu — Development Plan

Work is strictly **phase-by-phase**. Do not implement later phases until the current phase is accepted.

**Never:** fabricate experimental metrics, fake lawyers, fake laws/citations, or claim classifier accuracy without a real executed evaluation.

---

## Phase 0 — Architecture and repository skeleton (this task)

**Goal:** Empty app, documented design.

**Deliverables:**

- Directories: `docs/`, `frontend/`, `backend/`, `ml/`, `knowledge_base/`, `tests/`
- `docs/ARCHITECTURE.md`, `DATABASE_DESIGN.md`, `API_PLAN.md`, `DEVELOPMENT_PLAN.md`
- `README.md`, `.gitignore`, `.env.example`

**Exit criteria:** Documentation reviewed; no application runtime yet.

---

## Phase 1 — Backend foundation, database, authentication

**Goal:** A running FastAPI service with PostgreSQL and JWT roles.

**Includes:**

- Python project layout under `backend/`
- SQLAlchemy models + migrations matching `DATABASE_DESIGN.md` (subset: users, lawyer profiles, specializations)
- Register/login/refresh for client and lawyer; hashed passwords; `/auth/me`
- Role guards
- Pytest for auth and permission denials

**Excludes:** ML, LLM, RAG, messaging UI, fake seed lawyers.

---

## Phase 2 — Frontend shell and authenticated UI

**Goal:** Next.js app that can register, log in, and show role-specific empty dashboards.

**Includes:**

- Tailwind layout, disclaimer on all authenticated pages
- Client / lawyer registration and login
- Protected routes by role
- Typed API client using `NEXT_PUBLIC_API_BASE_URL` only

**Excludes:** Query analysis, RAG, full consultation chat.

**Verification:** Exercise login and route guards in the browser.

---

## Phase 3 — Lawyer profiles, specializations, admin verification

**Goal:** Lawyers can complete profiles; admins can verify; clients see only verified lawyers.

**Includes:**

- Specialization taxonomy (aligned with future ML labels)
- Profile and availability APIs + forms
- Admin verification endpoints and a simple admin UI
- No invented credentials in UI or API

---

## Phase 4 — NLP preprocessing and ML classification (research core)

**Goal:** Reproducible training/evaluation **on a real labeled dataset**.

**Includes:**

- spaCy preprocessing shared by train and infer
- TF-IDF + Multinomial Naive Bayes + Linear SVM
- Train/validation/test splits without leakage
- Scripts that write **executed** Accuracy, Precision, Recall, F1, confusion matrices
- Inference function used by the API only after artifacts exist
- Confidence bands and “needs clarification” behavior

**Excludes:** Invented scores; training on synthetic legal “statutes.”

If the dataset is not yet available, this phase stops at pipeline code + tests on a tiny **non-legal or placeholder-label** fixture only if the academic supervisor allows it—and results must be labeled as **not** the research evaluation. Prefer waiting for the real dataset.

---

## Phase 5 — Legal query API and clarification loop

**Goal:** Clients submit problems, receive category + confidence, answer clarifying questions.

**Includes:**

- `legal_queries`, `query_messages`, `classifications` persistence
- `/queries` endpoints from `API_PLAN.md`
- Frontend query + clarification UX
- Strong ownership checks (clients see only their queries)

**Excludes:** Full LLM essays until Phase 6.

---

## Phase 6 — Knowledge base and RAG + LLM explanation

**Goal:** Informational guidance grounded in **real, attributed** documents.

**Includes:**

- Admin CMS for knowledge documents
- Chunking + FAISS or Chroma index
- Backend-only LLM calls with retrieval context and anti-hallucination instructions
- Frontend guidance view with mandatory disclaimer
- Refusal path when retrieval is empty

**Excludes:** Unsourced citations; keys in the frontend.

---

## Phase 7 — Lawyer recommendation and consultation requests

**Goal:** Match verified lawyers to predicted category; request / accept / reject.

**Includes:**

- Recommendation service (verified + specialization + optional location)
- Consultation state machine
- Client and lawyer UIs for requests
- Empty-state when no lawyers match

---

## Phase 8 — Messaging and consultation history

**Goal:** Chat only after acceptance; history for both sides.

**Includes:**

- `messages` API and UI
- Closed consultations read-only
- Minimal logging of message bodies

---

## Phase 9 — Admin monitoring, hardening, tests, deployment

**Goal:** Production-shaped system.

**Includes:**

- Activity dashboard (aggregates only)
- Audit logs
- Security pass: CORS, secrets, IDOR tests, rate limiting on auth and LLM routes
- Pytest + frontend tests for critical flows
- Deploy frontend to Vercel, API to Render, managed PostgreSQL
- Privacy review of logs and LLM payloads

---

## Cross-cutting rules (all phases)

1. Informational positioning in UI and API.
2. No fabricated laws, cases, citations, lawyers, or metrics.
3. Secrets only in environment variables.
4. Stop at phase boundaries unless explicitly asked to continue.
5. For UI work, verify in the browser before calling the phase complete.

---

## Recommended next phase after this document set

**Phase 1 — Backend foundation, database, and authentication.**

That phase creates the FastAPI project, connects PostgreSQL, and implements users, roles, and JWT—without ML, LLM, or product UI beyond what is needed to test the API (optional minimal check via API client or later Phase 2).
