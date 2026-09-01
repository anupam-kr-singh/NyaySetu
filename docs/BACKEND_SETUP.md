# NyaySetu backend setup (Phase 1)

## 1. Python version

Use **Python 3.11 or newer**. This project was developed against Python 3.11.

```powershell
python --version
```

## 2. Virtual environment

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Dependency installation

```powershell
pip install -r requirements.txt
```

## 4. Environment configuration

Copy the example file at the **repository root** (not inside `backend/` unless you prefer a local copy):

```powershell
cd ..
copy .env.example .env
```

Edit `.env` and set at least:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy URL, e.g. `postgresql+psycopg://USER:PASSWORD@127.0.0.1:5432/nyaysetu` |
| `JWT_SECRET` | Long random string (16+ characters). Never commit the real value. |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime, e.g. `30` |
| `CORS_ORIGINS` | Comma-separated browser origins, e.g. `http://localhost:3000` |
| `APP_ENV` | `development` enables `/api/dev/*` role-check routes |

Do not put LLM keys or production secrets in the frontend. `.env` is gitignored.

## 5. PostgreSQL setup

PostgreSQL must be running before migrations, tests, or the API (except a bare `/health` liveness check).

**Option A — Docker Compose** (from the repository root):

```powershell
docker compose up -d db
```

This starts PostgreSQL 16 on port `5432` with a **local development** user/database. Create `nyaysetu_test` for pytest if the init script did not (first container start only):

```powershell
docker compose exec db psql -U nyaysetu -d postgres -c "CREATE DATABASE nyaysetu_test;"
```

Ignore the error if `nyaysetu_test` already exists.

**Option B — local PostgreSQL**

1. Install PostgreSQL 16+.
2. Create a role and databases:

```sql
CREATE USER nyaysetu WITH PASSWORD 'choose-a-local-password';
CREATE DATABASE nyaysetu OWNER nyaysetu;
CREATE DATABASE nyaysetu_test OWNER nyaysetu;
```

3. Put the matching URL in `.env` as `DATABASE_URL`.

Tests use `TEST_DATABASE_URL` if set, otherwise:

`postgresql+psycopg://nyaysetu:nyaysetu_dev_only@127.0.0.1:5432/nyaysetu_test`

Override `TEST_DATABASE_URL` if your local credentials differ. Do not point tests at production.

## 6. Alembic commands

From `backend/` with the virtualenv active and `.env` loaded (Alembic reads `DATABASE_URL` via application settings):

```powershell
alembic upgrade head
alembic downgrade -1
alembic upgrade head
alembic current
```

Do not create production tables by hand. Phase 1’s only migration creates the `users` table.

## 7. Starting FastAPI

From `backend/`:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 8. Opening Swagger

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 9. Running Pytest

From `backend/`:

```powershell
pytest
```

PostgreSQL must be reachable. Tests apply migrations to the test database and truncate `users` between cases.

## 10. Troubleshooting

| Symptom | What to check |
|---------|----------------|
| `JWT_SECRET must be at least 16 characters` | Set `JWT_SECRET` in `.env` |
| connection refused / `could not translate host` | Postgres is not running, or `DATABASE_URL` host/port is wrong |
| `password authentication failed` | User/password in `DATABASE_URL` does not match the server |
| `database "nyaysetu" does not exist` | Create the database (section 5) |
| `relation "users" does not exist` | Run `alembic upgrade head` |
| CORS errors from a browser | Add the exact frontend origin to `CORS_ORIGINS` |
| 409 on register | Email already exists (emails are stored lowercase) |
| 401 on `/api/auth/me` | Missing/expired `Authorization: Bearer <token>` |
| `/api/dev/*` missing | `APP_ENV` is not `development` or `test` |

Public `POST /api/auth/register` always creates `CLIENT` users. Extra JSON fields such as `role` are rejected (422). Create `ADMIN` or `LAWYER` users only via:

```powershell
python -m app.cli.create_privileged_user --name "Name" --email you@example.com --password "local-password" --role ADMIN
```

(`--role` is `ADMIN` or `LAWYER`.)
