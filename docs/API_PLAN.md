# NyaySetu — API Plan

**Status:** Phase 1 implemented subset. The canonical backend prefix is `/api`.

**Base URL:** `/api`
**Format:** JSON  
**Auth:** `Authorization: Bearer <access_token>` unless marked public.

Every authenticated response that includes AI-generated text should also include a stable disclaimer field, for example:

`disclaimer`: “This information is for general understanding only. It is not legal advice, does not create a lawyer–client relationship, and does not guarantee any legal outcome. Consult a qualified lawyer for advice about your situation.”

---

## Conventions

| Item | Plan |
|------|------|
| Errors | `{ "detail": "...", "code": "..." }` |
| Pagination | `?page=&page_size=` with `{ items, total, page, page_size }` |
| IDs | UUID strings |
| Roles | `client`, `lawyer`, `administrator` |

**HTTP mapping:** 401 unauthenticated, 403 forbidden (wrong role or not owner), 404 not found (no leakage of other users’ resources), 409 conflict (e.g. duplicate pending consultation), 422 validation.

---

## 1. Health

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/health` | Public | Liveness for Render |

---

## 2. Authentication

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/auth/register` | Public | Create client account |
| POST | `/auth/register/lawyer` | Public | Create lawyer user + empty profile |
| POST | `/auth/login` | Public | Issue rotating access + refresh tokens |
| POST | `/auth/refresh` | Refresh token | New access token |
| POST | `/auth/logout` | Authenticated | Revoke refresh token if stored |
| GET | `/auth/me` | Authenticated | Current user + role |

**Not public:** administrator registration.

---

## 3. Users (self)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| PATCH | `/users/me` | Any role | Update display name (not role) |
| PATCH | `/users/me/password` | Any role | Change password |

---

## 4. Lawyer profiles

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/lawyers` | Not implemented | Lawyer listing/matching is Phase 3+ |
| GET | `/lawyers/{id}` | Not implemented | Public profile rules await verification workflow |
| GET | `/lawyers/me` | Lawyer | Own profile including unverified fields |
| PUT | `/lawyers/me` | Lawyer | Bio, jurisdiction, city, experience, accepting flag |
| PUT | `/lawyers/me/specializations` | Lawyer | Replace specialization set |
| GET | `/lawyers/me/availability` | Lawyer | List windows |
| PUT | `/lawyers/me/availability` | Lawyer | Replace weekly availability |
| POST | `/lawyers/me/verification-request` | Not implemented | Verification is Phase 3 |

Clients never receive bar numbers unless product policy later allows it; default is to hide registration numbers from public profile payloads.

---

## 5. Legal queries and AI assistant

Orchestrates NLP → classification → optional clarification → retrieval → LLM explanation. Implementation is later; this is the intended surface.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/queries` | Client | Create query with `problem_text` |
| GET | `/queries` | Client | Own query list |
| GET | `/queries/{id}` | Client (owner), admin | Detail + latest classification + messages |
| POST | `/queries/{id}/clarify` | Client (owner) | Submit answers to clarifying questions |
| POST | `/queries/{id}/analyze` | Client (owner) | Run or re-run classification + confidence |
| POST | `/queries/{id}/guidance` | Client (owner) | RAG + LLM informational explanation |
| GET | `/queries/{id}/recommendations` | Client (owner) | Verified lawyers for predicted category |

**Analyze response (planned fields):** `predicted_category`, `confidence`, `confidence_band`, `model_name`, `needs_clarification`, `clarifying_questions[]`.

If `needs_clarification` is true, `guidance` should refuse to invent a full legal analysis until clarification is done or the user explicitly continues with low confidence (product flag to decide in implementation).

---

## 6. Knowledge base (admin write; retrieval is internal)

Public clients do not browse raw documents in v1 unless a later phase adds a library UI. Retrieval is used inside `/queries/{id}/guidance`.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/admin/knowledge-documents` | Admin | List documents |
| POST | `/admin/knowledge-documents` | Admin | Create (unpublished by default) |
| GET | `/admin/knowledge-documents/{id}` | Admin | Read |
| PATCH | `/admin/knowledge-documents/{id}` | Admin | Update body/metadata/publish flag |
| DELETE | `/admin/knowledge-documents/{id}` | Admin | Soft or hard delete (decide at impl) |
| POST | `/admin/knowledge-documents/{id}/reindex` | Admin | Rebuild chunks/vectors for that doc |

---

## 7. Consultations

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/consultations` | Client | Request: `lawyer_id`, optional `legal_query_id`, `client_note` |
| GET | `/consultations` | Client or lawyer | Own consultations; filter by status |
| GET | `/consultations/{id}` | Parties or admin | Detail |
| POST | `/consultations/{id}/accept` | Lawyer (assignee) | `pending` → `accepted` |
| POST | `/consultations/{id}/reject` | Lawyer (assignee) | `pending` → `rejected` |
| POST | `/consultations/{id}/close` | Client, lawyer, or admin | → `closed` |

---

## 8. Messages (post-acceptance)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/consultations/{id}/messages` | Parties or admin | Chronological history |
| POST | `/consultations/{id}/messages` | Parties; status must be `accepted` | Send message |

---

## 9. Administration

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/admin/users` | Admin | List users; filter by role/active |
| PATCH | `/admin/users/{id}` | Admin | Activate/deactivate; never set arbitrary passwords in logs |
| GET | `/admin/lawyers` | Admin | All lawyer profiles including unverified |
| POST | `/admin/lawyers/{id}/verify` | Admin | Approve + verification row |
| POST | `/admin/lawyers/{id}/reject-verification` | Admin | Reject + notes |
| GET | `/admin/activity` | Admin | Aggregates: user counts, query counts, consultation statuses (no raw query dumps) |
| GET | `/admin/audit-logs` | Admin | Audit trail |

---

## 10. API groups summary

| Group | Prefix | Primary roles |
|-------|--------|----------------|
| Health | `/health` | Public |
| Auth | `/auth` | Public + all |
| Users | `/users` | All authenticated |
| Lawyers | `/lawyers` | Client, lawyer, admin |
| Queries / AI | `/queries` | Client |
| Consultations | `/consultations` | Client, lawyer |
| Messages | `/consultations/{id}/messages` | Consultation parties |
| Admin | `/admin` | Administrator |

---

## 11. Explicit non-goals for the API (v1)

- Payment processing
- Video hearings
- Court filing
- Unauthenticated LLM proxy
- Endpoints that return fabricated citations or “guaranteed” outcomes
- Training or uploading ML datasets through the public API
