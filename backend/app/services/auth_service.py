"""Authentication and user persistence. Passwords and hashes are never logged."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import RefreshToken, User, UserRole
from app.models.lawyer import LawyerProfile
from app.core.security import hash_refresh_token


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalize_email(email)))


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    role: UserRole = UserRole.CLIENT,
    is_active: bool = True,
) -> User:
    user = User(
        name=name.strip(),
        email=normalize_email(email),
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_lawyer_user(db: Session, *, name: str, email: str, password: str) -> User:
    """Create the LAWYER account and its required empty profile atomically."""
    user = User(name=name.strip(), email=normalize_email(email), password_hash=hash_password(password), role=UserRole.LAWYER)
    db.add(user)
    db.flush()
    db.add(LawyerProfile(user_id=user.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user


def store_refresh_token(db: Session, *, token_id: UUID, user_id: UUID, token: str, expires_at: datetime) -> None:
    db.add(RefreshToken(id=token_id, user_id=user_id, token_hash=hash_refresh_token(token), expires_at=expires_at))
    db.commit()


def valid_refresh_token(db: Session, *, token_id: UUID, token: str, user_id: UUID) -> bool:
    record = db.get(RefreshToken, token_id)
    return bool(record and record.user_id == user_id and record.token_hash == hash_refresh_token(token) and record.revoked_at is None and record.expires_at > datetime.now(UTC))


def revoke_refresh_token(db: Session, *, token_id: UUID) -> None:
    record = db.get(RefreshToken, token_id)
    if record is not None and record.revoked_at is None:
        record.revoked_at = datetime.now(UTC)
        db.commit()
