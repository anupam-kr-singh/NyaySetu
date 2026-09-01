# NyaySetu backend (Phase 1)

FastAPI service for authentication, authorization, rotating refresh tokens, and lawyer-profile foundations.

This backend is **not** a lawyer and does not provide legal advice. Later phases add ML, RAG, and consultations.

## Quick start

See [docs/BACKEND_SETUP.md](../docs/BACKEND_SETUP.md) for full instructions.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# configure ../.env then:
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

`POST /api/auth/register` creates CLIENT users; `POST /api/auth/register/lawyer` creates a LAWYER user and empty profile. Administrators remain CLI-provisioned. Refresh/logout endpoints are `/api/auth/refresh` and `/api/auth/logout`.

```powershell
python -m app.cli.create_privileged_user --name "Admin" --email admin@example.com --password "your-local-password" --role ADMIN
```

Do not use this CLI to invent production lawyer profiles.
