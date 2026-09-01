from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.lawyer import VerificationStatus

class LawyerProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bar_registration_number: str | None = Field(default=None, max_length=200)
    bio: str | None = None
    jurisdiction: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=120)
    years_of_experience: int | None = Field(default=None, ge=0)
    consultation_fee_note: str | None = Field(default=None, max_length=500)
    is_accepting_requests: bool | None = None

class SpecializationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; slug: str; name: str; description: str | None

class SpecializationSet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    specialization_ids: list[UUID]

class LawyerProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; user_id: UUID; bar_registration_number: str | None; bio: str | None; jurisdiction: str | None; city: str | None; years_of_experience: int | None; consultation_fee_note: str | None; verification_status: VerificationStatus; is_accepting_requests: bool; specializations: list[SpecializationPublic]
