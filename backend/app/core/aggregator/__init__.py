"""Vote aggregation components.

This module provides the aggregation service for election results.
"""

from app.core.aggregator.service import (
    AggregationResult,
    AggregationService,
    PartyAggregation,
)

__all__ = [
    "AggregationResult",
    "AggregationService",
    "PartyAggregation",
]
