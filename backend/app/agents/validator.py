"""Validator agent for data validation and flagging.

This module provides the validator agent that handles validation of
extracted election data and flagging results for manual review.

Requirements: 3.6, 3.7, 3.8
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.agents.graph import AgentState, ProcessingStatus
from app.core.extractor.parser import ExtractionResult, PartyVote, SummaryFields
from app.core.extractor.validator import (
    DataValidator,
    ValidationError,
    ValidationErrorType,
    ValidationResult,
    ValidationSeverity,
)

logger = logging.getLogger("inec_agent.agents.validator")


@dataclass
class FlaggedResult:
    """A result flagged for manual review.
    
    Attributes:
        polling_unit_id: Polling unit identifier
        reason: Reason for flagging
        errors: List of validation errors
        warnings: List of validation warnings
        confidence: Confidence score
        extracted_data: The extracted data that was flagged
    """
    
    polling_unit_id: str
    reason: str
    errors: List[ValidationError]
    warnings: List[ValidationError]
    confidence: float
    extracted_data: Optional[Dict[str, Any]] = None


class ValidatorAgent:
    """Agent for validating extracted election data.
    
    This agent handles:
    - Cross-field validation (vote sums, totals)
    - Confidence scoring
    - Anomaly detection
    - Flagging results for manual review
    
    Requirements: 3.6, 3.7, 3.8
    """
    
    def __init__(
        self,
        vote_sum_tolerance: int = 2,
        min_confidence: float = 0.5,
        flag_on_warning: bool = False,
    ):
        """Initialize the validator agent.
        
        Args:
            vote_sum_tolerance: Tolerance for vote sum validation (±votes)
            min_confidence: Minimum confidence to not flag
            flag_on_warning: Whether to flag results with warnings
        """
        self.validator = DataValidator(
            vote_sum_tolerance=vote_sum_tolerance,
            min_confidence=min_confidence,
            flag_on_warning=flag_on_warning,
        )
        
        self.min_confidence = min_confidence
        self.flag_on_warning = flag_on_warning
        
        # Track flagged results
        self._flagged_results: List[FlaggedResult] = []
        
        logger.info("ValidatorAgent initialized")
    
    def validate(self, extraction_result: ExtractionResult) -> ValidationResult:
        """Validate extracted election data.
        
        Validation rules:
        1. Sum of party votes ≈ valid votes (within tolerance)
        2. Valid votes + rejected votes ≤ accredited voters
        3. All vote counts are non-negative
        4. Party names are recognized
        5. No duplicate parties
        
        Args:
            extraction_result: Extraction result to validate
            
        Returns:
            ValidationResult with errors, warnings, and confidence
        """
        logger.info("Validating extraction result")
        return self.validator.validate(extraction_result)
    
    def validate_from_dict(self, extracted_data: Dict[str, Any]) -> ValidationResult:
        """Validate extracted data from dictionary format.
        
        Args:
            extracted_data: Extracted data dictionary
            
        Returns:
            ValidationResult with errors, warnings, and confidence
        """
        # Convert dictionary to ExtractionResult
        extraction_result = self._dict_to_extraction_result(extracted_data)
        return self.validate(extraction_result)
    
    async def flag_for_review(
        self,
        polling_unit_id: str,
        reason: str,
        validation_result: ValidationResult,
        extracted_data: Optional[Dict[str, Any]] = None,
    ) -> FlaggedResult:
        """Flag a result for manual review.
        
        Args:
            polling_unit_id: Polling unit identifier
            reason: Reason for flagging
            validation_result: Validation result
            extracted_data: The extracted data
            
        Returns:
            FlaggedResult object
        """
        logger.info(f"Flagging result for polling unit {polling_unit_id}: {reason}")
        
        flagged = FlaggedResult(
            polling_unit_id=polling_unit_id,
            reason=reason,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            confidence=validation_result.confidence,
            extracted_data=extracted_data,
        )
        
        self._flagged_results.append(flagged)
        
        return flagged
    
    async def process_state(
        self,
        state: AgentState,
    ) -> AgentState:
        """Process the validation step for the workflow.
        
        This method is called by the LangGraph workflow to handle
        validation of extracted data.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with validation results
        """
        logger.info(f"Validating data for job {state['job_id']}")
        
        # Update status
        state["status"] = ProcessingStatus.VALIDATING.value
        
        # Check for extracted data
        extracted_data = state.get("extracted_data")
        if not extracted_data:
            state["errors"].append({
                "stage": "validate",
                "message": "No extracted data to validate",
                "recoverable": False,
            })
            state["status"] = ProcessingStatus.FAILED.value
            return state
        
        # Validate the extracted data
        validation_result = self.validate_from_dict(extracted_data)
        
        # Update state with validation results
        state["validation_results"] = {
            "is_valid": validation_result.is_valid,
            "errors": [
                {
                    "error_type": e.error_type.value,
                    "field": e.field,
                    "message": e.message,
                    "severity": e.severity.value,
                    "expected": e.expected,
                    "actual": e.actual,
                }
                for e in validation_result.errors
            ],
            "warnings": [
                {
                    "error_type": w.error_type.value,
                    "field": w.field,
                    "message": w.message,
                    "severity": w.severity.value,
                    "expected": w.expected,
                    "actual": w.actual,
                }
                for w in validation_result.warnings
            ],
            "confidence": validation_result.confidence,
            "should_flag": validation_result.should_flag,
            "flag_reason": validation_result.flag_reason,
            "error_count": validation_result.error_count,
            "warning_count": validation_result.warning_count,
        }
        
        # Log validation outcome
        if validation_result.is_valid:
            logger.info(
                f"Validation passed with confidence {validation_result.confidence:.2f}"
            )
        else:
            logger.warning(
                f"Validation failed: {validation_result.error_count} errors, "
                f"{validation_result.warning_count} warnings"
            )
        
        # Flag if needed
        if validation_result.should_flag:
            polling_unit = state.get("polling_unit", {})
            polling_unit_id = polling_unit.get("id", "unknown")
            
            await self.flag_for_review(
                polling_unit_id=polling_unit_id,
                reason=validation_result.flag_reason,
                validation_result=validation_result,
                extracted_data=extracted_data,
            )
        
        return state
    
    def should_flag(
        self,
        extraction_result: ExtractionResult,
        validation_result: ValidationResult,
    ) -> tuple[bool, str]:
        """Determine if a result should be flagged for manual review.
        
        Args:
            extraction_result: Extraction result
            validation_result: Validation result
            
        Returns:
            Tuple of (should_flag, reason)
        """
        reasons = []
        
        # Flag if there are validation errors
        if validation_result.errors:
            reasons.append(f"{len(validation_result.errors)} validation error(s)")
        
        # Flag if confidence is too low
        if validation_result.confidence < self.min_confidence:
            reasons.append(f"Low confidence ({validation_result.confidence:.2f})")
        
        # Flag if no party votes extracted
        if not extraction_result.party_votes:
            reasons.append("No party votes extracted")
        
        # Flag if OCR couldn't read the result sheet
        if not extraction_result.raw_text.strip():
            reasons.append("OCR could not read result sheet")
        
        # Optionally flag on warnings
        if self.flag_on_warning and validation_result.warnings:
            reasons.append(f"{len(validation_result.warnings)} warning(s)")
        
        if reasons:
            return True, "; ".join(reasons)
        
        return False, ""
    
    def get_flagged_results(self) -> List[FlaggedResult]:
        """Get all flagged results.
        
        Returns:
            List of FlaggedResult objects
        """
        return self._flagged_results.copy()
    
    def get_flagged_count(self) -> int:
        """Get count of flagged results.
        
        Returns:
            Number of flagged results
        """
        return len(self._flagged_results)
    
    def clear_flagged_results(self) -> None:
        """Clear the list of flagged results."""
        self._flagged_results.clear()
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results.
        
        Returns:
            Dictionary with validation statistics
        """
        total_flagged = len(self._flagged_results)
        
        # Count by reason
        reason_counts: Dict[str, int] = {}
        for flagged in self._flagged_results:
            reason = flagged.reason
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        # Count by error type
        error_type_counts: Dict[str, int] = {}
        for flagged in self._flagged_results:
            for error in flagged.errors:
                error_type = error.error_type.value
                error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        return {
            "total_flagged": total_flagged,
            "by_reason": reason_counts,
            "by_error_type": error_type_counts,
        }
    
    def _dict_to_extraction_result(self, data: Dict[str, Any]) -> ExtractionResult:
        """Convert dictionary to ExtractionResult.
        
        Args:
            data: Extracted data dictionary
            
        Returns:
            ExtractionResult object
        """
        # Convert party votes
        party_votes = []
        for pv_data in data.get("party_votes", []):
            party_votes.append(PartyVote(
                party_name=pv_data.get("party_name", ""),
                party_code=pv_data.get("party_code", ""),
                votes=pv_data.get("votes", 0),
                confidence=pv_data.get("confidence", 1.0),
            ))
        
        # Convert summary
        summary_data = data.get("summary", {})
        summary = SummaryFields(
            accredited_voters=summary_data.get("accredited_voters", 0),
            valid_votes=summary_data.get("valid_votes", 0),
            rejected_votes=summary_data.get("rejected_votes", 0),
            total_votes_cast=summary_data.get("total_votes_cast", 0),
        )
        
        return ExtractionResult(
            party_votes=party_votes,
            summary=summary,
            polling_unit_name=data.get("polling_unit_name", ""),
            ward_name=data.get("ward_name", ""),
            lga_name=data.get("lga_name", ""),
            state_name=data.get("state_name", ""),
            confidence=data.get("confidence", 0.0),
            warnings=data.get("warnings", []),
        )
