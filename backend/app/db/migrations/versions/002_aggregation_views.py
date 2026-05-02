"""Create aggregation SQL views for ward and LGA level vote aggregation.

Revision ID: 002
Revises: 001
Create Date: 2024-01-02

Requirements: 5.1, 5.2

This migration creates SQL views for aggregating election results:
- ward_aggregation: Aggregates votes by party at ward level
- lga_aggregation: Aggregates votes by party at LGA level
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create aggregation views for ward and LGA levels."""

    # ===========================================
    # Ward-level aggregation view
    # ===========================================
    # Aggregates votes by party at ward level:
    # - Groups by ward_id, election_type_id, party_id
    # - Sums vote_count across all polling units in the ward
    # - Calculates percentage of total valid votes
    # - Counts total polling units, processed polling units, flagged results

    op.execute("""
        CREATE VIEW ward_aggregation AS
        WITH ward_totals AS (
            SELECT 
                w.id AS ward_id,
                er.election_type_id,
                SUM(er.valid_votes) AS total_valid_votes,
                COUNT(DISTINCT er.polling_unit_id) AS processed_polling_units,
                COUNT(DISTINCT fr.election_result_id) AS flagged_results
            FROM wards w
            JOIN polling_units pu ON pu.ward_id = w.id
            LEFT JOIN election_results er ON er.polling_unit_id = pu.id
            LEFT JOIN flagged_results fr ON fr.election_result_id = er.id
            GROUP BY w.id, er.election_type_id
        )
        SELECT 
            w.id AS ward_id,
            w.name AS ward_name,
            w.code AS ward_code,
            l.id AS lga_id,
            l.name AS lga_name,
            s.id AS state_id,
            s.name AS state_name,
            et.id AS election_type_id,
            et.code AS election_type,
            et.name AS election_type_name,
            pp.id AS party_id,
            pp.code AS party_code,
            pp.name AS party_name,
            COALESCE(SUM(pr.vote_count), 0) AS total_votes,
            CASE 
                WHEN wt.total_valid_votes > 0 
                THEN ROUND((COALESCE(SUM(pr.vote_count), 0)::NUMERIC / wt.total_valid_votes) * 100, 2)
                ELSE 0.00
            END AS vote_percentage,
            w.total_polling_units AS total_polling_units,
            COALESCE(wt.processed_polling_units, 0) AS processed_polling_units,
            COALESCE(wt.flagged_results, 0) AS flagged_results
        FROM wards w
        JOIN lgas l ON w.lga_id = l.id
        JOIN states s ON l.state_id = s.id
        JOIN polling_units pu ON pu.ward_id = w.id
        JOIN election_results er ON er.polling_unit_id = pu.id
        JOIN election_types et ON er.election_type_id = et.id
        JOIN party_results pr ON pr.election_result_id = er.id
        JOIN political_parties pp ON pr.party_id = pp.id
        JOIN ward_totals wt ON wt.ward_id = w.id AND wt.election_type_id = et.id
        GROUP BY 
            w.id, w.name, w.code, w.total_polling_units,
            l.id, l.name,
            s.id, s.name,
            et.id, et.code, et.name,
            pp.id, pp.code, pp.name,
            wt.total_valid_votes, wt.processed_polling_units, wt.flagged_results
    """)

    # ===========================================
    # LGA-level aggregation view
    # ===========================================
    # Aggregates votes by party at LGA level:
    # - Groups by lga_id, election_type_id, party_id
    # - Sums vote_count across all wards in the LGA
    # - Calculates percentage of total valid votes
    # - Counts total polling units, processed polling units, flagged results

    op.execute("""
        CREATE VIEW lga_aggregation AS
        WITH lga_totals AS (
            SELECT 
                l.id AS lga_id,
                er.election_type_id,
                SUM(er.valid_votes) AS total_valid_votes,
                COUNT(DISTINCT er.polling_unit_id) AS processed_polling_units,
                COUNT(DISTINCT fr.election_result_id) AS flagged_results
            FROM lgas l
            JOIN wards w ON w.lga_id = l.id
            JOIN polling_units pu ON pu.ward_id = w.id
            LEFT JOIN election_results er ON er.polling_unit_id = pu.id
            LEFT JOIN flagged_results fr ON fr.election_result_id = er.id
            GROUP BY l.id, er.election_type_id
        ),
        lga_polling_unit_counts AS (
            SELECT 
                l.id AS lga_id,
                SUM(w.total_polling_units) AS total_polling_units
            FROM lgas l
            JOIN wards w ON w.lga_id = l.id
            GROUP BY l.id
        )
        SELECT 
            l.id AS lga_id,
            l.name AS lga_name,
            l.code AS lga_code,
            s.id AS state_id,
            s.name AS state_name,
            et.id AS election_type_id,
            et.code AS election_type,
            et.name AS election_type_name,
            pp.id AS party_id,
            pp.code AS party_code,
            pp.name AS party_name,
            COALESCE(SUM(pr.vote_count), 0) AS total_votes,
            CASE 
                WHEN lt.total_valid_votes > 0 
                THEN ROUND((COALESCE(SUM(pr.vote_count), 0)::NUMERIC / lt.total_valid_votes) * 100, 2)
                ELSE 0.00
            END AS vote_percentage,
            COALESCE(lpuc.total_polling_units, 0) AS total_polling_units,
            COALESCE(lt.processed_polling_units, 0) AS processed_polling_units,
            COALESCE(lt.flagged_results, 0) AS flagged_results
        FROM lgas l
        JOIN states s ON l.state_id = s.id
        JOIN wards w ON w.lga_id = l.id
        JOIN polling_units pu ON pu.ward_id = w.id
        JOIN election_results er ON er.polling_unit_id = pu.id
        JOIN election_types et ON er.election_type_id = et.id
        JOIN party_results pr ON pr.election_result_id = er.id
        JOIN political_parties pp ON pr.party_id = pp.id
        JOIN lga_totals lt ON lt.lga_id = l.id AND lt.election_type_id = et.id
        LEFT JOIN lga_polling_unit_counts lpuc ON lpuc.lga_id = l.id
        GROUP BY 
            l.id, l.name, l.code,
            s.id, s.name,
            et.id, et.code, et.name,
            pp.id, pp.code, pp.name,
            lt.total_valid_votes, lt.processed_polling_units, lt.flagged_results,
            lpuc.total_polling_units
    """)


def downgrade() -> None:
    """Drop aggregation views."""
    op.execute("DROP VIEW IF EXISTS lga_aggregation")
    op.execute("DROP VIEW IF EXISTS ward_aggregation")
