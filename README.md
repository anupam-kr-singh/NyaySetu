# NyaySetu

**AI-Assisted Legal Guidance and Lawyer Consultation System** (final-year project)

NyaySetu is a planned web platform where a person can describe a legal problem in natural language, receive **preliminary informational guidance**, see a **predicted legal category** with **confidence**, and find **verified lawyers** for professional consultation. Lawyers can join, maintain a profile, and respond to consultation requests. Administrators verify lawyers and manage knowledge-base content.

This software is an **informational and consultation aid**. It is **not** a lawyer, **not** a replacement for a qualified advocate, and **does not** guarantee legal outcomes. It must not invent laws, citations, case names, or lawyer credentials.

---

## Current status

**Architecture and documentation only.** The application is not implemented yet. There is no trained model, no database schema in production, no LLM integration, and **no experimental accuracy to report**.

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
backend/          FastAPI app (not created yet)
ml/               Training and evaluation (not created yet)
knowledge_base/   Curated sources and indexes (empty)
tests/            Automated tests (not created yet)
```

---

## Documentation

- [System architecture](docs/ARCHITECTURE.md)
- [Development plan](docs/DEVELOPMENT_PLAN.md)
- [Database design](docs/DATABASE_DESIGN.md)
- [API plan](docs/API_PLAN.md)

Copy `.env.example` to `.env` when implementation begins. Never commit secrets. Never put LLM API keys in frontend code.

---

## Next step

See **Phase 1** in `docs/DEVELOPMENT_PLAN.md`: backend foundation, PostgreSQL, and authentication. Do not skip ahead to ML training or LLM integration.
