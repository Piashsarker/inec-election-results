"""Tests for election data extractor and validator."""

import pytest

from app.core.extractor.parser import (
    ElectionDataExtractor,
    ExtractionResult,
    PartyVote,
    SummaryFields,
)
from app.core.extractor.validator import (
    DataValidator,
    ValidationErrorType,
)


class TestPartyVote:
    """Tests for PartyVote dataclass."""

    def test_party_vote_creation(self):
        """Test creating a PartyVote."""
        pv = PartyVote(
            party_name="All Progressives Congress",
            party_code="APC",
            votes=150,
            confidence=0.9,
        )

        assert pv.party_name == "All Progressives Congress"
        assert pv.party_code == "APC"
        assert pv.votes == 150
        assert pv.confidence == 0.9


class TestSummaryFields:
    """Tests for SummaryFields dataclass."""

    def test_summary_fields_defaults(self):
        """Test SummaryFields default values."""
        summary = SummaryFields()

        assert summary.accredited_voters == 0
        assert summary.valid_votes == 0
        assert summary.rejected_votes == 0
        assert summary.total_votes_cast == 0


class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""

    def test_total_party_votes(self):
        """Test total party votes calculation."""
        result = ExtractionResult(
            party_votes=[
                PartyVote("APC", "APC", 100),
                PartyVote("PDP", "PDP", 80),
                PartyVote("LP", "LP", 50),
            ]
        )

        assert result.total_party_votes == 230

    def test_is_valid_true(self):
        """Test is_valid when result is valid."""
        result = ExtractionResult(
            party_votes=[PartyVote("APC", "APC", 100)],
            summary=SummaryFields(valid_votes=100),
        )

        assert result.is_valid is True

    def test_is_valid_false_no_parties(self):
        """Test is_valid when no parties."""
        result = ExtractionResult(
            party_votes=[],
            summary=SummaryFields(valid_votes=100),
        )

        assert result.is_valid is False

    def test_is_valid_false_no_valid_votes(self):
        """Test is_valid when no valid votes."""
        result = ExtractionResult(
            party_votes=[PartyVote("APC", "APC", 100)],
            summary=SummaryFields(valid_votes=0),
        )

        assert result.is_valid is False


class TestElectionDataExtractor:
    """Tests for ElectionDataExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return ElectionDataExtractor()

    def test_extract_party_votes_simple(self, extractor):
        """Test extracting party votes from simple text."""
        text = """
        APC: 150
        PDP: 120
        LP: 80
        """

        result = extractor.extract_from_text(text)

        assert len(result.party_votes) >= 3

        # Check APC
        apc = next((p for p in result.party_votes if p.party_code == "APC"), None)
        assert apc is not None
        assert apc.votes == 150

    def test_extract_party_votes_with_full_names(self, extractor):
        """Test extracting party votes with full party names."""
        text = """
        All Progressives Congress: 200
        Peoples Democratic Party: 150
        Labour Party: 100
        """

        result = extractor.extract_from_text(text)

        assert len(result.party_votes) >= 3

    def test_extract_summary_fields(self, extractor):
        """Test extracting summary fields."""
        text = """
        Accredited Voters: 500
        Valid Votes: 450
        Rejected Votes: 20
        """

        result = extractor.extract_from_text(text)

        assert result.summary.accredited_voters == 500
        assert result.summary.valid_votes == 450
        assert result.summary.rejected_votes == 20

    def test_extract_summary_fields_variations(self, extractor):
        """Test extracting summary fields with different formats."""
        text = """
        Total Accredited: 300
        Total Valid: 280
        Invalid Votes: 15
        """

        result = extractor.extract_from_text(text)

        assert result.summary.accredited_voters == 300
        assert result.summary.valid_votes == 280
        assert result.summary.rejected_votes == 15

    def test_extract_complete_result(self, extractor):
        """Test extracting complete election result."""
        text = """
        POLLING UNIT: Test Unit 001
        WARD: Test Ward
        LGA: Test LGA
        STATE: Test State

        APC: 150
        PDP: 120
        LP: 80
        NNPP: 30

        Accredited Voters: 400
        Valid Votes: 380
        Rejected Votes: 10
        """

        result = extractor.extract_from_text(text)

        assert len(result.party_votes) >= 4
        assert result.summary.accredited_voters == 400
        assert result.summary.valid_votes == 380
        assert result.summary.rejected_votes == 10

    def test_extract_handles_empty_text(self, extractor):
        """Test extraction with empty text."""
        result = extractor.extract_from_text("")

        assert len(result.party_votes) == 0
        assert result.summary.valid_votes == 0

    def test_warnings_added_for_missing_data(self, extractor):
        """Test that warnings are added for missing data."""
        text = "Some random text without election data"

        result = extractor.extract_from_text(text)

        assert len(result.warnings) > 0


class TestDataValidator:
    """Tests for DataValidator class."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return DataValidator(vote_sum_tolerance=2)

    def test_validate_valid_result(self, validator):
        """Test validation of valid result."""
        result = ExtractionResult(
            party_votes=[
                PartyVote("APC", "APC", 150),
                PartyVote("PDP", "PDP", 120),
                PartyVote("LP", "LP", 80),
            ],
            summary=SummaryFields(
                accredited_voters=400,
                valid_votes=350,
                rejected_votes=20,
            ),
            confidence=0.9,
        )

        validation = validator.validate(result)

        assert validation.is_valid is True
        assert len(validation.errors) == 0

    def test_validate_vote_sum_mismatch(self, validator):
        """Test validation catches vote sum mismatch."""
        result = ExtractionResult(
            party_votes=[
                PartyVote("APC", "APC", 150),
                PartyVote("PDP", "PDP", 120),
            ],
            summary=SummaryFields(
                accredited_voters=400,
                valid_votes=300,  # Sum is 270, mismatch of 30
                rejected_votes=20,
            ),
            confidence=0.9,
        )

        validation = validator.validate(result)

        # Should have vote sum mismatch error or warning
        all_issues = validation.errors + validation.warnings
        vote_sum_issues = [
            e for e in all_issues
            if e.error_type == ValidationErrorType.VOTE_SUM_MISMATCH
        ]
        assert len(vote_sum_issues) > 0

    def test_validate_votes_exceed_accredited(self, validator):
        """Test validation catches votes exceeding accredited."""
        result = ExtractionResult(
            party_votes=[
                PartyVote("APC", "APC", 200),
                PartyVote("PDP", "PDP", 150),
            ],
            summary=SummaryFields(
                accredited_voters=300,
                valid_votes=350,  # Exceeds accredited
                rejected_votes=20,
            ),
            confidence=0.9,
        )

        validation = validator.validate(result)

        assert validation.is_valid is False
        votes_exceed = [
            e for e in validation.errors
            if e.error_type == ValidationErrorType.VOTES_EXCEED_ACCREDITED
        ]
        assert len(votes_exceed) > 0

    def test_validate_negative_votes(self, validator):
        """Test validation catches negative votes."""
        result = ExtractionResult(
            party_votes=[
                PartyVote("APC", "APC", -50),  # Negative
                PartyVote("PDP", "PDP", 100),
            ],
            summary=SummaryFields(
                accredited_voters=200,
                valid_votes=50,
                rejected_votes=10,
            ),
            confidence=0.9,
        )

        validation = validator.validate(result)

        assert validation.is_valid is False
        negative_errors = [
            e for e in validation.errors
            if e.error_type == ValidationErrorType.NEGATIVE_VOTES
        ]
        assert len(negative_errors) > 0

    def test_validate_duplicate_parties(self, validator):
        """Test validation catches duplicate parties."""
        result = ExtractionResult(
            party_votes=[
                PartyVote("APC", "APC", 100),
                PartyVote("APC", "APC", 50),  # Duplicate
                PartyVote("PDP", "PDP", 80),
            ],
            summary=SummaryFields(
                accredited_voters=300,
                valid_votes=230,
                rejected_votes=10,
            ),
            confidence=0.9,
        )

        validation = validator.validate(result)

        assert validation.is_valid is False
        duplicate_errors = [
            e for e in validation.errors
            if e.error_type == ValidationErrorType.DUPLICATE_PARTY
        ]
        assert len(duplicate_errors) > 0

    def test_validate_unrecognized_party_warning(self, validator):
        """Test validation warns about unrecognized parties."""
        result = ExtractionResult(
            party_votes=[
                PartyVote("Unknown Party", "XYZ", 100),
                PartyVote("APC", "APC", 80),
            ],
            summary=SummaryFields(
                accredited_voters=200,
                valid_votes=180,
                rejected_votes=10,
            ),
            confidence=0.9,
        )

        validation = validator.validate(result)

        unrecognized = [
            w for w in validation.warnings
            if w.error_type == ValidationErrorType.UNRECOGNIZED_PARTY
        ]
        assert len(unrecognized) > 0

    def test_validate_missing_parties_warning(self, validator):
        """Test validation warns about missing parties."""
        result = ExtractionResult(
            party_votes=[],
            summary=SummaryFields(
                accredited_voters=200,
                valid_votes=180,
                rejected_votes=10,
            ),
            confidence=0.5,
        )

        validation = validator.validate(result)

        missing = [
            w for w in validation.warnings
            if w.error_type == ValidationErrorType.MISSING_PARTIES
        ]
        assert len(missing) > 0

    def test_validate_should_flag_on_errors(self, validator):
        """Test that results with errors are flagged."""
        result = ExtractionResult(
            party_votes=[
                PartyVote("APC", "APC", -50),  # Error: negative
            ],
            summary=SummaryFields(
                accredited_voters=200,
                valid_votes=50,
                rejected_votes=10,
            ),
            confidence=0.9,
        )

        validation = validator.validate(result)

        assert validation.should_flag is True
        assert len(validation.flag_reason) > 0

    def test_validate_should_flag_low_confidence(self, validator):
        """Test that low confidence results are flagged."""
        result = ExtractionResult(
            party_votes=[
                PartyVote("APC", "APC", 100),
            ],
            summary=SummaryFields(
                accredited_voters=200,
                valid_votes=100,
                rejected_votes=10,
            ),
            confidence=0.3,  # Low confidence
        )

        validation = validator.validate(result)

        assert validation.should_flag is True

    def test_validate_tolerance_within_range(self, validator):
        """Test vote sum within tolerance passes."""
        result = ExtractionResult(
            party_votes=[
                PartyVote("APC", "APC", 100),
                PartyVote("PDP", "PDP", 80),
            ],
            summary=SummaryFields(
                accredited_voters=200,
                valid_votes=181,  # Sum is 180, diff is 1 (within tolerance)
                rejected_votes=10,
            ),
            confidence=0.9,
        )

        validation = validator.validate(result)

        vote_sum_errors = [
            e for e in validation.errors
            if e.error_type == ValidationErrorType.VOTE_SUM_MISMATCH
        ]
        assert len(vote_sum_errors) == 0

    def test_validation_result_properties(self, validator):
        """Test ValidationResult properties."""
        result = ExtractionResult(
            party_votes=[PartyVote("APC", "APC", 100)],
            summary=SummaryFields(valid_votes=100),
            confidence=0.9,
        )

        validation = validator.validate(result)

        assert isinstance(validation.error_count, int)
        assert isinstance(validation.warning_count, int)
        assert isinstance(validation.all_issues, list)
