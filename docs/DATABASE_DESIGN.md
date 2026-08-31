# NyaySetu — Database Design (Proposed)

**Status:** Logical design only. No tables, ORM models, or migrations have been created.

**Engine (planned):** PostgreSQL  
**Access (planned):** SQLAlchemy 2.x  

All timestamps are stored in UTC. Identifiers are UUIDs unless noted.

---

## 1. Entity overview

| Entity | Purpose |
|--------|---------|
| `users` | Account identity, credentials, role |
| `lawyer_profiles` | Professional profile for users with role LAWYER |
| `specializations` | Canonical legal domains (taxonomy) |
| `lawyer_specializations` | Many-to-many: lawyer ↔ specialization |
| `lawyer_availability` | When a lawyer can take consultations |
| `lawyer_verifications` | Admin verification history for a lawyer |
| `legal_queries` | Client problem statements and conversation context |
| `query_messages` | Clarification Q&A turns on a query |
| `classifications` | ML (and optional human) category results for a query |
| `knowledge_documents` | Curated legal-information sources |
| `knowledge_chunks` | Retrievable passages derived from documents |
| `consultations` | Request/accept/reject lifecycle between client and lawyer |
| `messages` | Client–lawyer chat after acceptance |
| `admin_audit_logs` | Sensitive admin actions |

---

## 2. Relationships (logical)

```
users 1 ────── 0..1 lawyer_profiles
users 1 ────── *   legal_queries          (as client)
users 1 ────── *   consultations          (as client)
users 1 ────── *   admin_audit_logs       (actor)

lawyer_profiles 1 ── * lawyer_specializations * ── 1 specializations
lawyer_profiles 1 ── * lawyer_availability
lawyer_profiles 1 ── * lawyer_verifications
lawyer_profiles 1 ── * consultations              (as lawyer)

legal_queries 1 ──── * query_messages
legal_queries 1 ──── * classifications
legal_queries 0..1 ── * consultations             (optional link)

knowledge_documents 1 ── * knowledge_chunks

consultations 1 ── * messages
consultations * ── 1 users                 (client)
consultations * ── 1 lawyer_profiles
```

---

## 3. Roles and `users`

**Role enum:** `client` | `lawyer` | `administrator`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `email` | CITEXT unique | Login identifier |
| `password_hash` | TEXT | Argon2/bcrypt; never store plaintext |
| `full_name` | TEXT | Display name |
| `role` | ENUM | See above |
| `is_active` | BOOLEAN | Soft disable |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**Rules:**

- One user row per account. A lawyer is a `users` row with `role = lawyer` plus a `lawyer_profiles` row.
- Administrators are not created via public registration.
- Email uniqueness is global across roles.

---

## 4. Lawyers and specializations

### 4.1 `lawyer_profiles`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `user_id` | UUID FK unique → `users.id` | One profile per lawyer user |
| `bar_registration_number` | TEXT | Stored as provided; **not** auto-verified by ML |
| `bio` | TEXT | Professional summary |
| `jurisdiction` | TEXT | e.g. state / high court region |
| `city` | TEXT | Optional location for matching |
| `years_of_experience` | INTEGER | Nullable; must be user-supplied |
| `consultation_fee_note` | TEXT | Optional; not a payment integration in v1 |
| `verification_status` | ENUM | `unsubmitted` \| `pending` \| `verified` \| `rejected` |
| `is_accepting_requests` | BOOLEAN | Master availability flag |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

Credentials shown to clients must come from this table (and verification), never from an LLM.

### 4.2 `specializations`

Canonical labels aligned with ML category names where possible (e.g. criminal, family, property, labour, consumer). Exact taxonomy is frozen when the labeled dataset is chosen.

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `slug` | TEXT unique | Stable machine key |
| `name` | TEXT | Display name |
| `description` | TEXT | Optional |

### 4.3 `lawyer_specializations`

| Column | Type | Notes |
|--------|------|--------|
| `lawyer_profile_id` | UUID FK | |
| `specialization_id` | UUID FK | |
| PK | composite | `(lawyer_profile_id, specialization_id)` |

### 4.4 `lawyer_availability`

Simple weekly windows; not a full calendar product in v1.

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `lawyer_profile_id` | UUID FK | |
| `weekday` | SMALLINT | 0–6 |
| `start_time` | TIME | Local time; timezone documented in profile later if needed |
| `end_time` | TIME | |

---

## 5. Admin / verification information

### 5.1 `lawyer_verifications`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `lawyer_profile_id` | UUID FK | |
| `admin_user_id` | UUID FK → `users.id` | Must have role administrator |
| `decision` | ENUM | `approved` \| `rejected` |
| `notes` | TEXT | Internal; not shown as “AI verified” |
| `created_at` | TIMESTAMPTZ | |

Updating `lawyer_profiles.verification_status` is always accompanied by a verification row (and an audit log).

### 5.2 `admin_audit_logs`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `actor_user_id` | UUID FK | |
| `action` | TEXT | e.g. `user.disable`, `kb.document.update` |
| `target_type` | TEXT | |
| `target_id` | UUID | |
| `metadata` | JSONB | No passwords; avoid full query text |
| `created_at` | TIMESTAMPTZ | |

---

## 6. Legal queries and classifications

### 6.1 `legal_queries`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `client_user_id` | UUID FK → `users.id` | Owner |
| `title` | TEXT | Optional short label |
| `problem_text` | TEXT | Sensitive; access only by owner, assigned lawyer (if consultation), admin |
| `jurisdiction_hint` | TEXT | Optional, from user or clarification |
| `status` | ENUM | `draft` \| `needs_clarification` \| `classified` \| `answered` \| `archived` |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### 6.2 `query_messages`

Clarifying questions from the system and answers from the client (not lawyer chat).

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `legal_query_id` | UUID FK | |
| `author` | ENUM | `system` \| `client` |
| `body` | TEXT | |
| `created_at` | TIMESTAMPTZ | |

### 6.3 `classifications`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `legal_query_id` | UUID FK | |
| `model_name` | TEXT | e.g. `multinomial_nb`, `linear_svm` |
| `predicted_category` | TEXT | Must match specialization/taxonomy slugs |
| `confidence` | NUMERIC | Probability or calibrated score; nullable if model has no probability |
| `confidence_band` | ENUM | `low` \| `medium` \| `high` \| `unknown` |
| `label_source` | ENUM | `model` \| `admin_override` |
| `raw_scores` | JSONB | Optional per-class scores for research |
| `created_at` | TIMESTAMPTZ | |

A query may have multiple classification rows (both models, or re-runs after clarification). The API selects the current row by latest `created_at` or an explicit `is_current` flag added at implementation time.

---

## 7. Knowledge-base documents

### 7.1 `knowledge_documents`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `title` | TEXT | |
| `source_name` | TEXT | Attribution; required |
| `source_url` | TEXT | Optional |
| `jurisdiction` | TEXT | |
| `category_slug` | TEXT | Aligns with specializations |
| `body` | TEXT | Informational content only; no fake citations |
| `is_published` | BOOLEAN | Draft vs live retrieval |
| `updated_by_admin_id` | UUID FK | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**No fabricated statutes or cases.** Unpublished documents are excluded from RAG.

### 7.2 `knowledge_chunks`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `document_id` | UUID FK | |
| `chunk_index` | INTEGER | |
| `text` | TEXT | Passage sent to the LLM as context |
| `embedding_ref` | TEXT | ID in FAISS/Chroma; vector itself may live outside Postgres |

---

## 8. Consultations and messages

### 8.1 `consultations`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `client_user_id` | UUID FK | |
| `lawyer_profile_id` | UUID FK | |
| `legal_query_id` | UUID FK nullable | Optional context from AI session |
| `status` | ENUM | `pending` \| `accepted` \| `rejected` \| `closed` |
| `client_note` | TEXT | Request message |
| `lawyer_response_note` | TEXT | Optional reject/accept note |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

**Uniqueness (recommended):** at most one `pending` consultation per `(client_user_id, lawyer_profile_id, legal_query_id)` to prevent spam duplicates.

### 8.2 `messages` (lawyer–client)

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID PK | |
| `consultation_id` | UUID FK | |
| `sender_user_id` | UUID FK | Must be the client or the lawyer user on that consultation |
| `body` | TEXT | |
| `created_at` | TIMESTAMPTZ | |

Insert allowed only when `consultations.status = accepted`. After `closed`, reads remain allowed for history; writes are forbidden.

---

## 9. Indexing and integrity (planned)

- Unique: `users.email`, `lawyer_profiles.user_id`, `specializations.slug`.
- Foreign keys with `ON DELETE` policies decided at migration time (prefer restrict on users with legal data; cascade only for dependent child rows such as chunks).
- Indexes: `legal_queries.client_user_id`, `consultations.lawyer_profile_id` + `status`, `messages.consultation_id`, `classifications.legal_query_id`.
- Row-level security is optional later; application-layer authorization is mandatory regardless.

---

## 10. Privacy notes for data at rest

- `problem_text`, `query_messages.body`, and `messages.body` are sensitive. Backups and admin tools must treat them as confidential.
- Do not store LLM API keys in the database.
- Do not log full `problem_text` in `admin_audit_logs.metadata` by default.

This document does not create tables. Implementation belongs to a later development phase.
