"""Development-only role checks. Not part of the product API."""

from fastapi import APIRouter

from app.core.dependencies import RequireAdmin, RequireClient, RequireLawyer

router = APIRouter(
    prefix="/dev",
    tags=["Development (role checks)"],
)


@router.get("/client", summary="Requires CLIENT role")
def client_only(user: RequireClient) -> dict[str, str]:
    return {"ok": "true", "role": user.role.value}


@router.get("/lawyer", summary="Requires LAWYER role")
def lawyer_only(user: RequireLawyer) -> dict[str, str]:
    return {"ok": "true", "role": user.role.value}


@router.get("/admin", summary="Requires ADMIN role")
def admin_only(user: RequireAdmin) -> dict[str, str]:
    return {"ok": "true", "role": user.role.value}
