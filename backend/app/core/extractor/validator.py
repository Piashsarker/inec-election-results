"""Data validation for extracted election results.

This module provides validation of extracted election data to ensure
consistency and flag results that may need manual review.

Requirements: 3.6, 3.7, 3.8
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from app.core.extractor.parser import ExtractionResult


class ValidationErrorType(str, Enum):
    """Types of validation errors."""
    
    VOTE_SUM_MISMATCH = "vote_sum_mismatch"
    VOTES_EXCEED_ACCREDITED = "votes_exceed_accredited"
    NEGATIVE_VOTES = "negative_votes"
    MISSING_PARTIES = "missing_parties"
    MISSING_SUMMARY = "missing_summary"
    UNRECOGNIZED_PARTY = "unrecognized_party"
    DUPLICATE_PARTY = "duplicate_party"
    ZERO_VOTES = "zero_votes"
    IMPLAUSIBLE_VALUES = "implausible_values"


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    
    ERROR = "error"  # Must be flagged for review
    WARNING = "warning"  # Should be reviewed
    INFO = "info"  # Informational only


@dataclass
class ValidationError:
    """A validation error or warning.
    
    Attributes:
        error_type: Type of validation error
        field: Field that failed validation
        message: Human-readable error message
        severity: Severity level
        expected: Expected value (if applicable)
        actual: Actual value (if applicable)
    """
    
    error_type: ValidationErrorType
    field: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    expected: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of data validation.
    
    Attributes:
        is_valid: Whether the data passed all validation rules
        errors: List of validation errors
        warnings: List of validation warnings
        confidence: Adjusted confidence score after validation
        should_flag: Whether result should be flagged for manual review
        flag_reason: Reason for flagging (if applicable)
    """
    
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    confidence: float = 0.0
    should_flag: bool = False
    flag_reason: str = ""
    
    @property
    def all_issues(self) -> List[ValidationError]:
        """Get all errors and warnings."""
        return self.errors + self.warnings
    
    @property
    def error_count(self) -> int:
        """Get count of errors."""
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        """Get count of warnings."""
        return len(self.warnings)


class DataValidator:
    """Validates extracted election data for consistency.
    
    This validator checks:
    1. Sum of party votes ≈ valid votes (within tolerance)
    2. Valid votes + rejected votes ≤ accredited voters
    3. All vote counts are non-negative
    4. Party names are recognized
    5. No duplicate parties
    
    Results that fail critical validation are flagged for manual review.
    
    Requirements: 3.6, 3.7, 3.8
    """
    
    # Tolerance for vote sum validation (±2 votes for rounding)
    VOTE_SUM_TOLERANCE = 2
    
    # Minimum number of parties expected
    MIN_PARTIES = 1
    
    # Maximum reasonable votes per polling unit
    MAX_REASONABLE_VOTES = 5000
    
    # Known party codes for validation
    KNOWN_PARTIES = {
        "APC", "PDP", "LP", "NNPP", "APGA", "ADC", "SDP", "YPP",
        "ZLP", "AA", "AAC", "ADP", "APP", "BP", "NRM", "PRP", "ACCORD",
    }
    
    def __init__(
        self,
        vote_sum_tolerance: int = 2,
        min_confidence: float = 0.5,
        flag_on_warning: bool = False,
    ):
        """Initialize data validator.
        
        Args:
            vote_sum_tolerance: Tolerance for vote sum validation
            min_confidence: Minimum confidence to not flag
            flag_on_warning: Whether to flag results with warnings
        """
        self.vote_sum_tolerance = vote_sum_tolerance
        self.min_confidence = min_confidence
        self.flag_on_warning = flag_on_warning
    
    def validate(self, result: ExtractionResult) -> ValidationResult:
        """Validate extracted election data.
        
        Validation rules:
        1. Sum of party votes ≈ valid votes (within tolerance)
        2. Valid votes + rejected votes ≤ accredited voters
        3. All vote counts are non-negative
        4. Party names are recognized
        5. No duplicate parties
        
        Args:
            result: Extraction result to validate
            
        Returns:
            ValidationResult with errors, warnings, and confidence
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []
        
        # Validate vote sum
        vote_sum_error = self._validate_vote_sum(result)
        if vote_sum_error:
            if vote_sum_error.severity == ValidationSeverity.ERROR:
                errors.append(vote_sum_error)
            else:
                warnings.append(vote_sum_error)
        
        # Validate totals
        totals_error = self._validate_totals(result)
        if totals_error:
            errors.append(totals_error)
        
        # Validate non-negative votes
        negative_errors = self._validate_non_negative(result)
        errors.extend(negative_errors)
        
        # Validate party names
        party_warnings = self._validate_party_names(result)
        warnings.extend(party_warnings)
        
        # Check for duplicate parties
        duplicate_error = self._validate_no_duplicates(result)
        if duplicate_error:
            errors.append(duplicate_error)
        
        # Check for missing data
        missing_warnings = self._validate_completeness(result)
        warnings.extend(missing_warnings)
        
        # Check for implausible values
        implausible_warnings = self._validate_plausibility(result)
        warnings.extend(implausible_warnings)
        
        # Calculate adjusted confidence
        confidence = self._calculate_confidence(result, errors, warnings)
        
        # Determine if should flag
        should_flag, flag_reason = self._should_flag(
            result, errors, warnings, confidence
        )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            confidence=confidence,
            should_flag=should_flag,
            flag_reason=flag_reason,
        )
    
    def _validate_vote_sum(
        self, result: ExtractionResult
    ) -> Optional[ValidationError]:
        """Validate that party votes sum to valid votes.
        
        Args:
            result: Extraction result
            
        Returns:
            ValidationError if validation fails, None otherwise
        """
        if not result.party_votes:
            return None
        
        if result.summary.valid_votes == 0:
            return None
        
        party_sum = result.total_party_votes
        valid_votes = result.summary.valid_votes
        diff = abs(party_sum - valid_votes)
        
        if diff > self.vote_sum_tolerance:
            # Determine severity based on difference magnitude
            if diff > valid_votes * 0.1:  # More than 10% difference
                severity = ValidationSeverity.ERROR
            else:
                severity = ValidationSeverity.WARNING
            
            return ValidationError(
                error_type=ValidationErrorType.VOTE_SUM_MISMATCH,
                field="party_votes",
                message=(
                    f"Sum of party votes ({party_sum}) does not match "
                    f"valid votes ({valid_votes}), difference: {diff}"
                ),
                severity=severity,
                expected=str(valid_votes),
                actual=str(party_sum),
            )
        
        return None
    
    def _validate_totals(
        self, result: ExtractionResult
    ) -> Optional[ValidationError]:
        """Validate that total votes don't exceed accredited voters.
        
        Args:
            result: Extraction result
            
        Returns:
            ValidationError if validation fails, None otherwise
        """
        if result.summary.accredited_voters == 0:
            return None
        
        total_votes = result.summary.valid_votes + result.summary.rejected_votes
        
        if total_votes > result.summary.accredited_voters:
            return ValidationError(
                error_type=ValidationErrorType.VOTES_EXCEED_ACCREDITED,
                field="totals",
                message=(
                    f"Total votes ({total_votes}) exceed "
                    f"accredited voters ({result.summary.accredited_voters})"
                ),
                severity=ValidationSeverity.ERROR,
                expected=f"<= {result.summary.accredited_voters}",
                actual=str(total_votes),
            )
        
        return None
    
    def _validate_non_negative(
        self, result: ExtractionResult
    ) -> List[ValidationError]:
        """Validate that all vote counts are non-negative.
        
        Args:
            result: Extraction result
            
        Returns:
            List of ValidationErrors for negative values
        """
        errors = []
        
        # Check party votes
        for pv in result.party_votes:
            if pv.votes < 0:
                errors.append(ValidationError(
                    error_type=ValidationErrorType.NEGATIVE_VOTES,
                    field=f"party_votes.{pv.party_code}",
                    message=f"Negative vote count for {pv.party_code}: {pv.votes}",
                    severity=ValidationSeverity.ERROR,
                    expected=">= 0",
                    actual=str(pv.votes),
                ))
        
        # Check summary fields
        if result.summary.accredited_voters < 0:
            errors.append(ValidationError(
                error_type=ValidationErrorType.NEGATIVE_VOTES,
                field="accredited_voters",
                message=f"Negative accredited voters: {result.summary.accredited_voters}",
                severity=ValidationSeverity.ERROR,
            ))
        
        if result.summary.valid_votes < 0:
            errors.append(ValidationError(
                error_type=ValidationErrorType.NEGATIVE_VOTES,
                field="valid_votes",
                message=f"Negative valid votes: {result.summary.valid_votes}",
                severity=ValidationSeverity.ERROR,
            ))
        
        if result.summary.rejected_votes < 0:
            errors.append(ValidationError(
                error_type=ValidationErrorType.NEGATIVE_VOTES,
                field="rejected_votes",
                message=f"Negative rejected votes: {result.summary.rejected_votes}",
                severity=ValidationSeverity.ERROR,
            ))
        
        return errors
    
    def _validate_party_names(
        self, result: ExtractionResult
    ) -> List[ValidationError]:
        """Validate that party names are recognized.
        
        Args:
            result: Extraction result
            
        Returns:
            List of ValidationErrors for unrecognized parties
        """
        warnings = []
        
        for pv in result.party_votes:
            if pv.party_code.upper() not in self.KNOWN_PARTIES:
                warnings.append(ValidationError(
                    error_type=ValidationErrorType.UNRECOGNIZED_PARTY,
                    field=f"party_votes.{pv.party_code}",
                    message=f"Unrecognized party code: {pv.party_code}",
                    severity=ValidationSeverity.WARNING,
                ))
        
        return warnings
    
    def _validate_no_duplicates(
        self, result: ExtractionResult
    ) -> Optional[ValidationError]:
        """Validate that there are no duplicate parties.
        
        Args:
            result: Extraction result
            
        Returns:
            ValidationError if duplicates found, None otherwise
        """
        seen = set()
        duplicates = []
        
        for pv in result.party_votes:
            code = pv.party_code.upper()
            if code in seen:
                duplicates.append(code)
            seen.add(code)
        
        if duplicates:
            return ValidationError(
                error_type=ValidationErrorType.DUPLICATE_PARTY,
                field="party_votes",
                message=f"Duplicate party entries: {', '.join(duplicates)}",
                severity=ValidationSeverity.ERROR,
            )
        
        return None
    
    def _validate_completeness(
        self, result: ExtractionResult
    ) -> List[ValidationError]:
        """Validate that required data is present.
        
        Args:
            result: Extraction result
            
        Returns:
            List of ValidationErrors for missing data
        """
        warnings = []
        
        if not result.party_votes:
            warnings.append(ValidationError(
                error_type=ValidationErrorType.MISSING_PARTIES,
                field="party_votes",
                message="No party votes extracted",
                severity=ValidationSeverity.WARNING,
            ))
        
        if result.summary.accredited_voters == 0:
            warnings.append(ValidationError(
                error_type=ValidationErrorType.MISSING_SUMMARY,
                field="accredited_voters",
                message="Accredited voters not found",
                severity=ValidationSeverity.WARNING,
            ))
        
        if result.summary.valid_votes == 0:
            warnings.append(ValidationError(
                error_type=ValidationErrorType.MISSING_SUMMARY,
                field="valid_votes",
                message="Valid votes not found",
                severity=ValidationSeverity.WARNING,
            ))
        
        return warnings
    
    def _validate_plausibility(
        self, result: ExtractionResult
    ) -> List[ValidationError]:
        """Validate that values are plausible.
        
        Args:
            result: Extraction result
            
        Returns:
            List of ValidationErrors for implausible values
        """
        warnings = []
        
        # Check for unreasonably high values
        if result.summary.accredited_voters > self.MAX_REASONABLE_VOTES:
            warnings.append(ValidationError(
                error_type=ValidationErrorType.IMPLAUSIBLE_VALUES,
                field="accredited_voters",
                message=(
                    f"Unusually high accredited voters: "
                    f"{result.summary.accredited_voters}"
                ),
                severity=ValidationSeverity.WARNING,
            ))
        
        # Check for all-zero party votes
        if result.party_votes and all(pv.votes == 0 for pv in result.party_votes):
            warnings.append(ValidationError(
                error_type=ValidationErrorType.ZERO_VOTES,
                field="party_votes",
                message="All party votes are zero",
                severity=ValidationSeverity.WARNING,
            ))
        
        return warnings
    
    def _calculate_confidence(
        self,
        result: ExtractionResult,
        errors: List[ValidationError],
        warnings: List[ValidationError],
    ) -> float:
        """Calculate adjusted confidence score.
        
        Args:
            result: Extraction result
            errors: List of validation errors
            warnings: List of validation warnings
            
        Returns:
            Adjusted confidence score (0-1)
        """
        base_confidence = result.confidence
        
        # Penalize for errors
        error_penalty = len(errors) * 0.15
        
        # Smaller penalty for warnings
        warning_penalty = len(warnings) * 0.05
        
        adjusted = base_confidence - error_penalty - warning_penalty
        return max(0.0, min(1.0, adjusted))
    
    def _should_flag(
        self,
        result: ExtractionResult,
        errors: List[ValidationError],
        warnings: List[ValidationError],
        confidence: float,
    ) -> tuple[bool, str]:
        """Determine if result should be flagged for manual review.
        
        Args:
            result: Extraction result
            errors: List of validation errors
            warnings: List of validation warnings
            confidence: Adjusted confidence score
            
        Returns:
            Tuple of (should_flag, reason)
        """
        reasons = []
        
        # Flag if there are errors
        if errors:
            reasons.append(f"{len(errors)} validation error(s)")
        
        # Flag if confidence is too low
        if confidence < self.min_confidence:
            reasons.append(f"Low confidence ({confidence:.2f})")
        
        # Optionally flag on warnings
        if self.flag_on_warning and warnings:
            reasons.append(f"{len(warnings)} warning(s)")
        
        # Flag if no party votes extracted
        if not result.party_votes:
            reasons.append("No party votes extracted")
        
        if reasons:
            return True, "; ".join(reasons)
        
        return False, ""
