"""Initial schema for INEC Election Results Agent.

Revision ID: 001
Revises: 
Create Date: 2024-01-01

Requirements: 4.1, 4.6

This migration creates all tables for the INEC Election Results Agent:
- Geographic hierarchy: states, lgas, wards, polling_units
- Election data: election_types, political_parties, election_results, party_results
- Job management: scraping_jobs, job_logs, flagged_results
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all tables with indexes and constraints."""

    # ===========================================
    # Geographic Hierarchy Tables
    # ===========================================

    # States table
    op.create_table(
        "states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
        sa.Column("total_lgas", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_states_name", "states", ["name"])

    # LGAs table
    op.create_table(
        "lgas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "state_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("states.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("total_wards", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_lgas_state", "lgas", ["state_id"])
    op.create_unique_constraint("uq_lga_state_code", "lgas", ["state_id", "code"])

    # Wards table
    op.create_table(
        "wards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lga_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lgas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("total_polling_units", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_wards_lga", "wards", ["lga_id"])
    op.create_unique_constraint("uq_ward_lga_code", "wards", ["lga_id", "code"])

    # Polling Units table
    op.create_table(
        "polling_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ward_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("wards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("delimitation", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_polling_units_ward", "polling_units", ["ward_id"])
    op.create_unique_constraint(
        "uq_polling_unit_ward_code", "polling_units", ["ward_id", "code"]
    )

    # ===========================================
    # Election Data Tables
    # ===========================================

    # Election Types table
    op.create_table(
        "election_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("code", sa.String(30), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Political Parties table
    op.create_table(
        "political_parties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Election Results table
    op.create_table(
        "election_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "election_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("election_types.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "polling_unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("polling_units.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("accredited_voters", sa.Integer(), nullable=False, default=0),
        sa.Column("valid_votes", sa.Integer(), nullable=False, default=0),
        sa.Column("rejected_votes", sa.Integer(), nullable=False, default=0),
        sa.Column("confidence_score", sa.Numeric(3, 2), default=0.00),
        sa.Column("source_image_path", sa.String(500), nullable=True),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_election_results_type", "election_results", ["election_type_id"])
    op.create_index("idx_election_results_pu", "election_results", ["polling_unit_id"])
    op.create_unique_constraint(
        "uq_election_result_type_pu",
        "election_results",
        ["election_type_id", "polling_unit_id"],
    )

    # Party Results table
    op.create_table(
        "party_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "election_result_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("election_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "party_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("political_parties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("vote_count", sa.Integer(), nullable=False, default=0),
        sa.Column("percentage", sa.Numeric(5, 2), default=0.00),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_party_results_election", "party_results", ["election_result_id"])
    op.create_index("idx_party_results_party", "party_results", ["party_id"])
    op.create_unique_constraint(
        "uq_party_result_election_party",
        "party_results",
        ["election_result_id", "party_id"],
    )

    # ===========================================
    # Job Management Tables
    # ===========================================

    # Scraping Jobs table
    op.create_table(
        "scraping_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, default="queued"),
        sa.Column("election_type", sa.String(50), nullable=True),
        sa.Column("target_state", sa.String(100), nullable=True),
        sa.Column("target_lga", sa.String(100), nullable=True),
        sa.Column("target_ward", sa.String(100), nullable=True),
        sa.Column("total_polling_units", sa.Integer(), nullable=False, default=0),
        sa.Column("processed_count", sa.Integer(), nullable=False, default=0),
        sa.Column("success_count", sa.Integer(), nullable=False, default=0),
        sa.Column("failed_count", sa.Integer(), nullable=False, default=0),
        sa.Column("last_processed_pu", sa.String(100), nullable=True),
        sa.Column("checkpoint_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_scraping_jobs_status", "scraping_jobs", ["status"])

    # Job Logs table
    op.create_table(
        "job_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scraping_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("level", sa.String(10), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_job_logs_job", "job_logs", ["job_id"])

    # Flagged Results table
    op.create_table(
        "flagged_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "election_result_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("election_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("review_notes", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_flagged_results_election", "flagged_results", ["election_result_id"])
    op.create_index("idx_flagged_results_status", "flagged_results", ["status"])


def downgrade() -> None:
    """Drop all tables in reverse order."""
    # Job management tables
    op.drop_table("flagged_results")
    op.drop_table("job_logs")
    op.drop_table("scraping_jobs")

    # Election data tables
    op.drop_table("party_results")
    op.drop_table("election_results")
    op.drop_table("political_parties")
    op.drop_table("election_types")

    # Geographic hierarchy tables
    op.drop_table("polling_units")
    op.drop_table("wards")
    op.drop_table("lgas")
    op.drop_table("states")
