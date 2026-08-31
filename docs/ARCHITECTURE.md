# NyaySetu — System Architecture

**Status:** Design only. No application code, models, database schema migrations, or LLM integration exist yet.

NyaySetu is an **AI-assisted informational and consultation platform**. It helps a person describe a legal problem in natural language, receive preliminary informational guidance, understand a likely legal domain, and find a suitable lawyer for professional consultation. It is **not** a lawyer, **not** a court, and **not** a substitute for qualified legal advice.

---

## 1. Overall system architecture

The system is a three-tier web application with a dedicated machine-learning and retrieval layer:

```
┌─────────────────────────────────────────────────────────────────┐
│  Client (browser)                                               │
│  Next.js + React + TypeScript + Tailwind CSS                    │
│  Role-aware UI: CLIENT | LAWYER | ADMINISTRATOR                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             │ JWT in Authorization header
┌────────────────────────────▼────────────────────────────────────┐
│  API (FastAPI)                                                  │
│  Auth, users, queries, consultations, messages, admin           │
│  Orchestrates NLP → ML classification → RAG → LLM explanation   │
│  Lawyer matching and consultation workflow                      │
└───────┬──────────────────┬──────────────────┬───────────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
 PostgreSQL          ml/ (sklearn)      knowledge_base/
 users, lawyers      TF-IDF + NB/SVM    curated documents
 queries, msgs       evaluation         FAISS or Chroma index
 consultations       artifacts only     (built in later phases)
```

**Request path for a legal query (target workflow):**

1. Authenticated client submits natural-language text.
2. Backend stores the query (access-controlled) and runs NLP preprocessing.
3. TF-IDF vectorization feeds Multinomial Naive Bayes and Linear SVM classifiers.
4. Confidence is assessed. If confidence is below a configurable threshold, the API returns clarifying questions instead of a category-backed explanation.
5. After a stable classification (or an explicit “insufficient information” outcome), the system retrieves relevant knowledge-base passages.
6. An LLM, called **only from the backend** with retrieved context, produces an informational explanation with mandatory disclaimers.
7. Lawyers whose verified specializations match the predicted domain are ranked and returned.
8. The client may request a consultation; a lawyer accepts or rejects; messaging is enabled only after acceptance.

The frontend never calls the LLM, never holds API keys, and never trains or loads ML models.

---

## 2. Frontend

**Stack:** Next.js (App Router intended), React, TypeScript, Tailwind CSS.

**Responsibilities:**

- Public marketing/info pages and a persistent legal-disclaimer banner.
- Registration and login for clients and lawyers; admin login (no public admin registration).
- Client: query composer, clarification Q&A, category/confidence display, informational guidance view, lawyer list/profile, consultation request and history, post-acceptance messaging.
- Lawyer: profile and specialization editor, availability, incoming requests, accept/reject, messaging, consultation history.
- Admin: user and lawyer management, verification queue, knowledge-base content management, activity monitoring.

**Constraints:**

- `NEXT_PUBLIC_*` variables may expose only the public API base URL.
- All privileged data is fetched through the backend with JWT.
- UI copy must state that outputs are informational and that no legal outcome is guaranteed.

Frontend source will live under `frontend/` in a later phase. This repository currently contains only a placeholder so the directory is tracked.

---

## 3. Backend

**Stack:** Python, FastAPI, Pydantic, SQLAlchemy, PostgreSQL.

**Responsibilities:**

- REST API under `/api/v1`.
- Request validation (Pydantic), persistence (SQLAlchemy), and authorization (role checks on every protected route).
- Orchestration of NLP, ML inference, retrieval, and LLM calls.
- Consultation lifecycle and messaging.
- Structured logging that **does not** dump full legal-query text by default (`LOG_QUERY_TEXT=false`).

**Module boundaries (planned, not implemented):**

| Area | Role |
|------|------|
| `backend/` API + domain services | HTTP, auth, business rules, DB |
| `ml/` | Preprocessing, TF-IDF, classifiers, evaluation scripts |
| `knowledge_base/` | Curated source documents and vector-index artifacts |

The API should treat `ml/` as a library (load a trained artifact at inference time). Training and evaluation run as offline jobs, never as part of a user request.

---

## 4. Machine learning pipeline

Research requirement: **text preprocessing → TF-IDF → Multinomial Naive Bayes and Linear SVM → evaluation with executed metrics**.

**Training (offline, later phase, only with a real labeled dataset):**

1. Load labeled legal-query examples (category labels).
2. Preprocess (see NLP pipeline).
3. Fit a TF-IDF vectorizer on the training split only (no test leakage).
4. Train Multinomial Naive Bayes and Linear SVM (e.g. `LinearSVC` or `SGDClassifier` with hinge loss, documented at implementation time).
5. Evaluate on a held-out test set.
6. Persist vectorizer + models as artifacts (gitignored).
7. Record **actual** Accuracy, Precision, Recall, F1, and confusion matrices in a results document. **Do not fabricate numbers.** Until a real dataset is run, no accuracy claims are made.

**Inference (online, later phase):**

1. Preprocess the user query with the same pipeline as training.
2. Transform with the persisted TF-IDF vectorizer.
3. Obtain class probabilities or decision scores from both models (or from the selected production model after comparison).
4. Map scores to a confidence band (e.g. low / medium / high) using thresholds chosen from validation data, not from guesswork.
5. If confidence is low, trigger clarifying questions instead of a firm category.

Production may use one primary classifier after comparison; both models remain part of the research write-up.

---

## 5. NLP pipeline

**Library:** spaCy (plus standard Unicode/normalization).

**Planned steps (applied consistently in train and infer):**

1. Language detection / assumption (project language policy to be fixed when the dataset is chosen; likely English and/or Hindi—do not mix tokenizers without documenting it).
2. Lowercasing where appropriate for the chosen language.
3. Whitespace and punctuation normalization.
4. Tokenization and lemmatization via spaCy.
5. Stop-word handling appropriate to legal text (do not over-strip terms of art).
6. Removal of emails, phone numbers, and other identifiers before logging or sending text to third-party LLM APIs where feasible (privacy).

Clarifying questions are generated from missing slots (parties, location/jurisdiction, dates, type of harm, pending proceedings) when classification confidence is low or required entities are absent. Question templates will be designed later; they must not invent facts.

---

## 6. LLM and RAG pipeline

**Purpose:** Turn a classified query plus retrieved passages into a cautious, informational explanation.

**Retrieval:**

- Curated documents live in `knowledge_base/` (statutes summaries, procedure explainers, jurisdiction notes—**only real, attributed sources** when content is added).
- Documents are chunked and embedded; vectors stored in **FAISS or Chroma** (choice locked in the RAG implementation phase based on deployment constraints).
- Retrieval is filtered by predicted legal category and jurisdiction when those fields are known.

**Generation:**

- The backend builds a prompt that includes: user question (redacted as needed), predicted category, confidence, retrieved chunks with source identifiers, and a hard system instruction: informational only; no fabricated laws, citations, cases, or credentials; no definitive legal conclusions without support in the retrieved text.
- If retrieval returns nothing relevant, the LLM must say so and recommend consulting a lawyer—not invent law.
- LLM API keys stay in server environment variables only.

**Safety overlay (product rules, not optional):**

- Every AI response includes a disclaimer that the output is informational and not legal advice.
- The system does not claim to be a lawyer and does not guarantee outcomes.
- Citations and case names appear only if present in retrieved, stored sources.

---

## 7. Database

**Engine:** PostgreSQL (managed instance in production).

Logical entities (see `docs/DATABASE_DESIGN.md` for attributes and relationships):

- Users and roles
- Lawyer profiles, specializations, availability, verification
- Legal queries, classifications, clarification turns
- Knowledge-base documents and (optionally) chunk metadata
- Consultations and messages
- Admin audit of verification and content changes

SQLAlchemy models and Alembic migrations are **out of scope for this phase**.

---

## 8. Authentication and authorization

**Authentication:**

- Email + password registration for CLIENT and LAWYER.
- Passwords hashed with a modern KDF (Argon2 preferred; bcrypt acceptable if Argon2 is unavailable in the deployment image).
- JWT access tokens (short-lived) and refresh tokens (longer-lived, stored hashed server-side if revocation is required).
- Administrator accounts are provisioned, not self-registered.

**Authorization:**

| Role | Access |
|------|--------|
| CLIENT | Own profile, own queries, own consultations and messages |
| LAWYER | Own profile, incoming requests for self, own consultations and messages |
| ADMINISTRATOR | User/lawyer management, verification, knowledge-base CMS, activity monitors |

Every API route that reads or writes personal or legal-query data must check **role and resource ownership**. IDOR (accessing another user’s query by UUID) is treated as a first-class threat.

---

## 9. Lawyer recommendation

**Inputs:** Predicted legal category, optional jurisdiction/location from the query or profile, lawyer verification status, declared specializations, and availability.

**Rules:**

- Only **verified** lawyers are recommended to clients.
- Matching is primarily specialization ↔ predicted category (plus optional location).
- Ranking may later include completeness of profile and availability; **no fabricated ratings or credentials**.
- If no verified lawyer matches, return an empty list with an honest message—do not invent lawyers.

Recommendation is a backend service; the frontend only displays API results.

---

## 10. Consultation workflow

```
CLIENT submits request for a verified lawyer
        → CONSULTATION status: pending
LAWYER accepts → status: accepted → messaging unlocked
LAWYER rejects → status: rejected → no messaging
Either party (or admin, for abuse) may later close → status: closed
```

**Invariants:**

- A consultation request requires an authenticated client and a verified lawyer.
- Messages are stored only for consultations in `accepted` or `closed` (read-only when closed).
- Lawyers never see other lawyers’ client messages.
- Clients never see other clients’ consultations.

---

## 11. Security and privacy

Legal queries may contain highly sensitive facts. Architecture constraints:

| Control | Design |
|---------|--------|
| Transport | HTTPS in production; CORS limited to the frontend origin |
| Secrets | Environment variables; `.env` gitignored; `.env.example` has placeholders only |
| Authn/Authz | JWT + hashed passwords + RBAC + ownership checks |
| Database | Parameterized SQL via SQLAlchemy; least-privilege DB user |
| Logging | Default: no raw query bodies, no tokens, no passwords |
| LLM | Server-side only; minimize PII in prompts; no keys in the browser |
| Frontend | No ML weights, no admin secrets, no LLM keys |
| Files | Uploads (if added later) scanned/size-limited and not publicly enumerable |

This phase does not implement these controls; later phases must not weaken them.

---

## 12. Deployment architecture

| Component | Target |
|-----------|--------|
| Frontend | Vercel (Next.js) |
| Backend | Render (FastAPI / Uvicorn) |
| Database | Managed PostgreSQL |
| ML artifacts | Packaged with the backend image or loaded from object storage; not trained at request time |
| Vector index | Built offline; loaded by the backend process (or a small sidecar later if needed) |
| Secrets | Platform env vars on Vercel (public URL only) and Render (all secrets) |

Local development uses `localhost` for Next.js and FastAPI plus a local or containerized PostgreSQL. Production URLs and credentials are never committed.

---

## 13. Testing (planned)

- **Backend / ML:** Pytest for API contracts, authz, consultation state machine, preprocessing, and (when a dataset exists) evaluation harnesses that write real metrics.
- **Frontend:** Framework-appropriate tests (React Testing Library and/or Playwright) in a later phase.

No tests are implemented in this phase.

---

## 14. Out of scope for the current repository state

Not created in this task: application source, npm/Python dependency lockfiles beyond documentation, fake lawyers, fake statutes, trained models, LLM calls, database tables, or any claimed experimental accuracy.
