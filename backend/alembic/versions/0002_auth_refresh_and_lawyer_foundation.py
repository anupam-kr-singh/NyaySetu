"""Add refresh tokens and lawyer foundation tables."""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_auth_refresh_lawyer"
down_revision: Union[str, Sequence[str], None] = "0001_create_users"
branch_labels = depends_on = None

verification_status = postgresql.ENUM("UNSUBMITTED", "PENDING", "VERIFIED", "REJECTED", name="lawyer_verification_status", create_type=False)

def upgrade() -> None:
    verification_status.create(op.get_bind(), checkfirst=True)
    op.create_table("refresh_tokens", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False, unique=True), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_table("specializations", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("slug", sa.String(100), nullable=False, unique=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("description", sa.Text()))
    op.create_table("lawyer_profiles", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True), sa.Column("bar_registration_number", sa.String(200)), sa.Column("bio", sa.Text()), sa.Column("jurisdiction", sa.String(200)), sa.Column("city", sa.String(120)), sa.Column("years_of_experience", sa.Integer()), sa.Column("consultation_fee_note", sa.String(500)), sa.Column("verification_status", verification_status, nullable=False, server_default="UNSUBMITTED"), sa.Column("is_accepting_requests", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.CheckConstraint("years_of_experience IS NULL OR years_of_experience >= 0", name="ck_lawyer_profiles_years_nonnegative"))
    op.create_table("lawyer_specializations", sa.Column("lawyer_profile_id", sa.Uuid(), sa.ForeignKey("lawyer_profiles.id", ondelete="CASCADE"), primary_key=True), sa.Column("specialization_id", sa.Uuid(), sa.ForeignKey("specializations.id", ondelete="RESTRICT"), primary_key=True))

def downgrade() -> None:
    op.drop_table("lawyer_specializations"); op.drop_table("lawyer_profiles"); op.drop_table("specializations"); op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens"); op.drop_table("refresh_tokens"); verification_status.drop(op.get_bind(), checkfirst=True)
