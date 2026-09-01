# NyaySetu

**AI-Assisted Legal Guidance and Lawyer Consultation System** (final-year project)

NyaySetu is a planned web platform where a person can describe a legal problem in natural language, receive **preliminary informational guidance**, see a **predicted legal category** with **confidence**, and find **verified lawyers** for professional consultation. Lawyers can join, maintain a profile, and respond to consultation requests. Administrators verify lawyers and manage knowledge-base content.

This software is an **informational and consultation aid**. It is **not** a lawyer, **not** a replacement for a qualified advocate, and **does not** guarantee legal outcomes. It must not invent laws, citations, case names, or lawyer credentials.

---

## Current status

**Phase 1 (backend foundation) is implemented:** FastAPI, PostgreSQL, Alembic, JWT auth, and role checks. There is no trained model, no LLM integration, and **no experimental accuracy to report**.

Setup: [docs/BACKEND_SETUP.md](docs/BACKEND_SETUP.md) and [backend/README.md](backend/README.md).

---

## Intended workflow

User → legal query → NLP preprocessing → TF-IDF → ML classification (Multinomial Naive Bayes and Linear SVM) → confidence check → clarifying questions if needed → knowledge retrieval → LLM explanation (RAG) → lawyer recommendation → consultation request → lawyer consultation.

---

## Planned stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL |
| ML | scikit-learn (TF-IDF, Naive Bayes, Linear SVM) |
| NLP | spaCy |
| Retrieval | FAISS or Chroma |
| Auth | JWT, password hashing, role-based access |
| Deploy | Vercel (frontend), Render (backend), managed PostgreSQL |

---

## Roles

- **Client** — submit queries, receive informational guidance, request consultations, message a lawyer after acceptance  
- **Lawyer** — profile, specializations, availability, accept/reject requests, message clients  
- **Administrator** — users, lawyer verification, knowledge base, monitoring  

---

## Repository layout

```
docs/             Architecture and plans
frontend/         Next.js app (not created yet)
backend/          FastAPI app (Phase 1: auth + health)
ml/               Training and evaluation (not created yet)
knowledge_base/   Curated sources and indexes (empty)
tests/            Reserved (backend tests live in backend/tests/)
```

---

## Documentation

- [System architecture](docs/ARCHITECTURE.md)
- [Development plan](docs/DEVELOPMENT_PLAN.md)
- [Database design](docs/DATABASE_DESIGN.md)
- [API plan](docs/API_PLAN.md)

Copy `.env.example` to `.env` and follow [docs/BACKEND_SETUP.md](docs/BACKEND_SETUP.md). Never commit secrets. Never put LLM API keys in frontend code.

### Backend (Phase 1)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
pytest
```

PostgreSQL must be running. `docker compose up -d db` from the repo root starts a local development database.

---

## Next step

See **Phase 2** in `docs/DEVELOPMENT_PLAN.md` (frontend shell). Do not start ML, LLM, or RAG until that work is requested.
