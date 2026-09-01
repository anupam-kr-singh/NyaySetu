"""Public authentication routes. Registration always creates CLIENT users."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.dependencies import DbSession, RequireAuth
from uuid import UUID
import jwt
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token
from app.models.user import UserRole
from app.schemas.user import (
    TokenResponse,
    RefreshTokenRequest,
    UserLoginRequest,
    UserPublic,
    UserRegisterRequest,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a client account",
    description=(
        "Creates a CLIENT user. Role cannot be set through this endpoint. "
        "Administrators and lawyers are not created by public registration."
    ),
)
def register(payload: UserRegisterRequest, db: DbSession) -> UserPublic:
    if auth_service.get_user_by_email(db, payload.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    try:
        user = auth_service.create_user(
            db,
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role=UserRole.CLIENT,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from None
    return UserPublic.model_validate(user)


@router.post("/register/lawyer", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_lawyer(payload: UserRegisterRequest, db: DbSession) -> UserPublic:
    if auth_service.get_user_by_email(db, payload.email) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    try:
        user = auth_service.create_lawyer_user(db, name=payload.name, email=payload.email, password=payload.password)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from None
    return UserPublic.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Returns a JWT access token for an active user.",
)
def login(payload: UserLoginRequest, db: DbSession) -> TokenResponse:
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
        )
    access_token = create_access_token(subject=user.id, role=user.role.value)
    refresh_token, token_id, expires_at = create_refresh_token(subject=user.id, role=user.role.value)
    auth_service.store_refresh_token(db, token_id=token_id, user_id=user.id, token=refresh_token, expires_at=expires_at)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshTokenRequest, db: DbSession) -> TokenResponse:
    try:
        claims = decode_refresh_token(payload.refresh_token)
        user_id, token_id = UUID(str(claims["sub"])), UUID(str(claims["jti"]))
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token") from None
    user = auth_service.get_user_by_id(db, user_id)
    if user is None or not user.is_active or not auth_service.valid_refresh_token(db, token_id=token_id, token=payload.refresh_token, user_id=user_id):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    auth_service.revoke_refresh_token(db, token_id=token_id)
    access_token = create_access_token(subject=user.id, role=user.role.value)
    refresh_token, new_id, expires_at = create_refresh_token(subject=user.id, role=user.role.value)
    auth_service.store_refresh_token(db, token_id=new_id, user_id=user.id, token=refresh_token, expires_at=expires_at)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshTokenRequest, current_user: RequireAuth, db: DbSession) -> None:
    try:
        claims = decode_refresh_token(payload.refresh_token)
        token_id = UUID(str(claims["jti"]))
        if UUID(str(claims["sub"])) != current_user.id:
            raise ValueError
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token") from None
    auth_service.revoke_refresh_token(db, token_id=token_id)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Current user",
    description="Requires a valid Bearer access token.",
)
def read_me(current_user: RequireAuth) -> UserPublic:
    return UserPublic.model_validate(current_user)
