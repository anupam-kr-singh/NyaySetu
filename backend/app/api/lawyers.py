from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.core.dependencies import DbSession, RequireLawyer
from app.models.lawyer import LawyerProfile, Specialization
from app.schemas.lawyer import LawyerProfilePublic, LawyerProfileUpdate, SpecializationSet

router = APIRouter(prefix="/lawyers", tags=["Lawyers"])

@router.get("/me", response_model=LawyerProfilePublic)
def read_my_profile(user: RequireLawyer, db: DbSession):
    profile = db.scalar(select(LawyerProfile).where(LawyerProfile.user_id == user.id))
    if profile is None: raise HTTPException(404, "Lawyer profile not found")
    return profile

@router.put("/me", response_model=LawyerProfilePublic)
def update_my_profile(payload: LawyerProfileUpdate, user: RequireLawyer, db: DbSession):
    profile = db.scalar(select(LawyerProfile).where(LawyerProfile.user_id == user.id))
    if profile is None: raise HTTPException(404, "Lawyer profile not found")
    for field, value in payload.model_dump(exclude_unset=True).items(): setattr(profile, field, value)
    db.commit(); db.refresh(profile); return profile

@router.put("/me/specializations", response_model=LawyerProfilePublic)
def replace_my_specializations(payload: SpecializationSet, user: RequireLawyer, db: DbSession):
    if len(set(payload.specialization_ids)) != len(payload.specialization_ids): raise HTTPException(422, "Specializations must be unique")
    profile = db.scalar(select(LawyerProfile).where(LawyerProfile.user_id == user.id))
    if profile is None: raise HTTPException(404, "Lawyer profile not found")
    items = list(db.scalars(select(Specialization).where(Specialization.id.in_(payload.specialization_ids)))) if payload.specialization_ids else []
    if len(items) != len(payload.specialization_ids): raise HTTPException(422, "Unknown specialization")
    profile.specializations = items; db.commit(); db.refresh(profile); return profile
