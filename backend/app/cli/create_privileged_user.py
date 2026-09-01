"""Create a LAWYER or ADMIN user. Not exposed over HTTP."""

from __future__ import annotations

import argparse
import sys

from sqlalchemy.exc import IntegrityError

from app.db.database import SessionLocal
from app.models.user import UserRole
from app.services import auth_service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a privileged NyaySetu user (LAWYER or ADMIN). Not a public API.",
    )
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--role", required=True, choices=["LAWYER", "ADMIN"])
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        if auth_service.get_user_by_email(db, args.email) is not None:
            print("A user with that email already exists.", file=sys.stderr)
            return 1
        user = auth_service.create_user(
            db,
            name=args.name,
            email=args.email,
            password=args.password,
            role=UserRole[args.role],
        )
        print(f"Created {user.role.value} user {user.email} ({user.id})")
        return 0
    except IntegrityError:
        print("A user with that email already exists.", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
