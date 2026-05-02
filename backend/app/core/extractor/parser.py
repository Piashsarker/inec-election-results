"""Election data extraction from OCR output.

This module provides parsing and extraction of structured election data
from OCR text output. It uses pattern matching to identify political
party names and their corresponding vote counts.

Requirements: 3.2, 3.3, 3.4, 3.5
"""
from __future__ import annotations


import re
from dataclasses import dataclass, field

from app.core.ocr.tesseract import OCRResult


@dataclass
class PartyVote:
    """Vote count for a political party.
    
    Attributes:
        party_name: Full party name
        party_code: Party abbreviation/code
        votes: Number of votes
        confidence: Confidence in extraction (0-1)
        raw_text: Original text that was parsed
    """

    party_name: str
    party_code: str
    votes: int
    confidence: float = 1.0
    raw_text: str = ""


@dataclass
class SummaryFields:
    """Summary fields from election result sheet.
    
    Attributes:
        accredited_voters: Total number of accredited voters
        valid_votes: Total number of valid votes
        rejected_votes: Total number of rejected/invalid votes
        total_votes_cast: Total votes cast (if available)
    """

    accredited_voters: int = 0
    valid_votes: int = 0
    rejected_votes: int = 0
    total_votes_cast: int = 0


@dataclass
class ExtractionResult:
    """Result of election data extraction.
    
    Attributes:
        party_votes: List of party vote counts
        summary: Summary fields (accredited, valid, rejected)
        polling_unit_name: Name of polling unit (if found)
        polling_unit_code: Code of polling unit (if found)
        ward_name: Ward name (if found)
        lga_name: LGA name (if found)
        state_name: State name (if found)
        election_type: Type of election (if found)
        confidence: Overall extraction confidence (0-1)
        warnings: List of extraction warnings
        raw_text: Original OCR text
    """

    party_votes: list[PartyVote] = field(default_factory=list)
    summary: SummaryFields = field(default_factory=SummaryFields)
    polling_unit_name: str = ""
    polling_unit_code: str = ""
    ward_name: str = ""
    lga_name: str = ""
    state_name: str = ""
    election_type: str = ""
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)
    raw_text: str = ""

    @property
    def total_party_votes(self) -> int:
        """Calculate sum of all party votes."""
        return sum(pv.votes for pv in self.party_votes)

    @property
    def is_valid(self) -> bool:
        """Check if extraction appears valid."""
        return len(self.party_votes) > 0 and self.summary.valid_votes > 0


class ElectionDataExtractor:
    """Extracts structured election data from OCR output.
    
    This class parses OCR text to identify:
    - Political party names and codes
    - Vote counts for each party
    - Summary fields (accredited voters, valid votes, rejected votes)
    - Location information (polling unit, ward, LGA, state)
    
    Requirements: 3.2, 3.3, 3.4, 3.5
    """

    # Known Nigerian political parties with regex patterns
    PARTY_PATTERNS: dict[str, str] = {
        "APC": r"(?:APC|All\s*Progressives?\s*Congress)",
        "PDP": r"(?:PDP|Peoples?\s*Democratic\s*Party)",
        "LP": r"(?:LP|Labour\s*Party)",
        "NNPP": r"(?:NNPP|New\s*Nigeria\s*Peoples?\s*Party)",
        "APGA": r"(?:APGA|All\s*Progressives?\s*Grand\s*Alliance)",
        "ADC": r"(?:ADC|African\s*Democratic\s*Congress)",
        "SDP": r"(?:SDP|Social\s*Democratic\s*Party)",
        "YPP": r"(?:YPP|Young\s*Progressives?\s*Party)",
        "ZLP": r"(?:ZLP|Zenith\s*Labour\s*Party)",
        "AA": r"(?:AA|Action\s*Alliance)",
        "AAC": r"(?:AAC|African\s*Action\s*Congress)",
        "ADP": r"(?:ADP|Action\s*Democratic\s*Party)",
        "APP": r"(?:APP|All\s*Peoples?\s*Party)",
        "BP": r"(?:BP|Boot\s*Party)",
        "NRM": r"(?:NRM|National\s*Rescue\s*Movement)",
        "PRP": r"(?:PRP|Peoples?\s*Redemption\s*Party)",
        "ACCORD": r"(?:ACCORD|Accord\s*Party)",
    }

    # Full party names for lookup
    PARTY_NAMES: dict[str, str] = {
        "APC": "All Progressives Congress",
        "PDP": "Peoples Democratic Party",
        "LP": "Labour Party",
        "NNPP": "New Nigeria Peoples Party",
        "APGA": "All Progressives Grand Alliance",
        "ADC": "African Democratic Congress",
        "SDP": "Social Democratic Party",
        "YPP": "Young Progressives Party",
        "ZLP": "Zenith Labour Party",
        "AA": "Action Alliance",
        "AAC": "African Action Congress",
        "ADP": "Action Democratic Party",
        "APP": "All Peoples Party",
        "BP": "Boot Party",
        "NRM": "National Rescue Movement",
        "PRP": "Peoples Redemption Party",
        "ACCORD": "Accord Party",
    }

    # Patterns for summary fields
    ACCREDITED_PATTERNS = [
        r"(?:accredited\s*voters?|total\s*accredited|no\.?\s*of\s*accredited)[:\s]*(\d+)",
        r"(\d+)\s*(?:accredited\s*voters?)",
    ]

    VALID_VOTES_PATTERNS = [
        r"(?:valid\s*votes?|total\s*valid)[:\s]*(\d+)",
        r"(\d+)\s*(?:valid\s*votes?)",
    ]

    REJECTED_PATTERNS = [
        r"(?:rejected\s*votes?|invalid\s*votes?|rejected/invalid)[:\s]*(\d+)",
        r"(\d+)\s*(?:rejected|invalid)\s*votes?",
    ]

    def __init__(
        self,
        min_confidence: float = 0.5,
        fuzzy_match: bool = True,
    ):
        """Initialize election data extractor.
        
        Args:
            min_confidence: Minimum confidence threshold for extraction
            fuzzy_match: Whether to use fuzzy matching for party names
        """
        self.min_confidence = min_confidence
        self.fuzzy_match = fuzzy_match

        # Compile regex patterns
        self._compiled_party_patterns = {
            code: re.compile(pattern, re.IGNORECASE)
            for code, pattern in self.PARTY_PATTERNS.items()
        }

    def extract(self, ocr_result: OCRResult) -> ExtractionResult:
        """Extract election data from OCR result.
        
        Steps:
        1. Identify table regions in text
        2. Extract party names using pattern matching
        3. Extract vote counts adjacent to party names
        4. Extract summary fields (accredited, valid, rejected)
        5. Calculate confidence score
        
        Args:
            ocr_result: OCR result with extracted text
            
        Returns:
            ExtractionResult with structured election data
        """
        text = ocr_result.text
        result = ExtractionResult(raw_text=text)

        # Extract party votes
        result.party_votes = self._extract_party_votes(text)

        # Extract summary fields
        result.summary = self._extract_summary_fields(text)

        # Extract location information
        self._extract_location_info(text, result)

        # Calculate confidence
        result.confidence = self._calculate_confidence(result, ocr_result)

        # Add warnings for potential issues
        self._add_warnings(result)

        return result

    def extract_from_text(self, text: str) -> ExtractionResult:
        """Extract election data from raw text.
        
        Args:
            text: Raw OCR text
            
        Returns:
            ExtractionResult with structured election data
        """
        result = ExtractionResult(raw_text=text)

        # Extract party votes
        result.party_votes = self._extract_party_votes(text)

        # Extract summary fields
        result.summary = self._extract_summary_fields(text)

        # Extract location information
        self._extract_location_info(text, result)

        # Calculate basic confidence
        result.confidence = self._calculate_basic_confidence(result)

        # Add warnings
        self._add_warnings(result)

        return result

    def _extract_party_votes(self, text: str) -> list[PartyVote]:
        """Extract party names and vote counts from text.
        
        Args:
            text: OCR text
            
        Returns:
            List of PartyVote objects
        """
        party_votes = []
        lines = text.split("\n")

        for line in lines:
            # Try to find party code and vote count in line
            party_vote = self._parse_party_line(line)
            if party_vote:
                party_votes.append(party_vote)

        # If no votes found with line parsing, try pattern matching
        if not party_votes:
            party_votes = self._extract_with_patterns(text)

        return party_votes

    def _parse_party_line(self, line: str) -> PartyVote | None:
        """Parse a single line for party and vote count.
        
        Args:
            line: Single line of text
            
        Returns:
            PartyVote if found, None otherwise
        """
        line = line.strip()
        if not line:
            return None

        # Look for party code in line
        for code, pattern in self._compiled_party_patterns.items():
            match = pattern.search(line)
            if match:
                # Look for number after party name
                vote_match = re.search(
                    r"(?:" + pattern.pattern + r")\s*[:\-]?\s*(\d+)",
                    line,
                    re.IGNORECASE,
                )

                if vote_match:
                    votes = int(vote_match.group(1))
                    return PartyVote(
                        party_name=self.PARTY_NAMES.get(code, code),
                        party_code=code,
                        votes=votes,
                        confidence=0.9,
                        raw_text=line,
                    )

                # Look for number anywhere in line after party
                remaining = line[match.end():]
                numbers = re.findall(r"\d+", remaining)
                if numbers:
                    votes = int(numbers[0])
                    return PartyVote(
                        party_name=self.PARTY_NAMES.get(code, code),
                        party_code=code,
                        votes=votes,
                        confidence=0.7,
                        raw_text=line,
                    )

        return None

    def _extract_with_patterns(self, text: str) -> list[PartyVote]:
        """Extract party votes using regex patterns on full text.
        
        Args:
            text: Full OCR text
            
        Returns:
            List of PartyVote objects
        """
        party_votes = []

        for code, pattern in self._compiled_party_patterns.items():
            # Find all occurrences of party with nearby numbers
            matches = re.finditer(
                pattern.pattern + r"\s*[:\-]?\s*(\d+)",
                text,
                re.IGNORECASE,
            )

            for match in matches:
                votes = int(match.group(1))
                party_votes.append(PartyVote(
                    party_name=self.PARTY_NAMES.get(code, code),
                    party_code=code,
                    votes=votes,
                    confidence=0.8,
                    raw_text=match.group(0),
                ))

        # Remove duplicates (keep highest vote count for each party)
        seen = {}
        for pv in party_votes:
            if pv.party_code not in seen or pv.votes > seen[pv.party_code].votes:
                seen[pv.party_code] = pv

        return list(seen.values())

    def _extract_summary_fields(self, text: str) -> SummaryFields:
        """Extract summary fields from text.
        
        Args:
            text: OCR text
            
        Returns:
            SummaryFields with extracted values
        """
        summary = SummaryFields()

        # Extract accredited voters
        for pattern in self.ACCREDITED_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                summary.accredited_voters = int(match.group(1))
                break

        # Extract valid votes
        for pattern in self.VALID_VOTES_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                summary.valid_votes = int(match.group(1))
                break

        # Extract rejected votes
        for pattern in self.REJECTED_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                summary.rejected_votes = int(match.group(1))
                break

        # Calculate total votes cast if not found
        if summary.valid_votes > 0 and summary.rejected_votes >= 0:
            summary.total_votes_cast = summary.valid_votes + summary.rejected_votes

        return summary

    def _extract_location_info(self, text: str, result: ExtractionResult) -> None:
        """Extract location information from text.
        
        Args:
            text: OCR text
            result: ExtractionResult to update
        """
        # Polling unit patterns
        pu_patterns = [
            r"polling\s*unit[:\s]*([^\n]+)",
            r"PU[:\s]*([^\n]+)",
            r"unit\s*name[:\s]*([^\n]+)",
        ]

        for pattern in pu_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.polling_unit_name = match.group(1).strip()
                break

        # Ward patterns
        ward_patterns = [
            r"ward[:\s]*([^\n]+)",
            r"registration\s*area[:\s]*([^\n]+)",
            r"RA[:\s]*([^\n]+)",
        ]

        for pattern in ward_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.ward_name = match.group(1).strip()
                break

        # LGA patterns
        lga_patterns = [
            r"(?:LGA|local\s*government)[:\s]*([^\n]+)",
        ]

        for pattern in lga_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.lga_name = match.group(1).strip()
                break

        # State patterns
        state_patterns = [
            r"state[:\s]*([^\n]+)",
        ]

        for pattern in state_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result.state_name = match.group(1).strip()
                break

    def _calculate_confidence(
        self,
        result: ExtractionResult,
        ocr_result: OCRResult,
    ) -> float:
        """Calculate overall extraction confidence.
        
        Args:
            result: Extraction result
            ocr_result: Original OCR result
            
        Returns:
            Confidence score (0-1)
        """
        factors = []

        # OCR confidence
        factors.append(ocr_result.normalized_confidence)

        # Party extraction confidence
        if result.party_votes:
            avg_party_conf = sum(
                pv.confidence for pv in result.party_votes
            ) / len(result.party_votes)
            factors.append(avg_party_conf)
        else:
            factors.append(0.0)

        # Summary fields completeness
        summary_score = 0.0
        if result.summary.accredited_voters > 0:
            summary_score += 0.33
        if result.summary.valid_votes > 0:
            summary_score += 0.34
        if result.summary.rejected_votes >= 0:
            summary_score += 0.33
        factors.append(summary_score)

        # Vote sum validation
        if result.party_votes and result.summary.valid_votes > 0:
            party_sum = result.total_party_votes
            diff = abs(party_sum - result.summary.valid_votes)
            tolerance = 2
            if diff <= tolerance:
                factors.append(1.0)
            else:
                # Penalize based on difference
                penalty = min(diff / result.summary.valid_votes, 1.0)
                factors.append(1.0 - penalty)

        return sum(factors) / len(factors) if factors else 0.0

    def _calculate_basic_confidence(self, result: ExtractionResult) -> float:
        """Calculate basic confidence without OCR result.
        
        Args:
            result: Extraction result
            
        Returns:
            Confidence score (0-1)
        """
        factors = []

        # Party extraction
        if result.party_votes:
            avg_party_conf = sum(
                pv.confidence for pv in result.party_votes
            ) / len(result.party_votes)
            factors.append(avg_party_conf)
        else:
            factors.append(0.0)

        # Summary fields
        summary_score = 0.0
        if result.summary.accredited_voters > 0:
            summary_score += 0.33
        if result.summary.valid_votes > 0:
            summary_score += 0.34
        if result.summary.rejected_votes >= 0:
            summary_score += 0.33
        factors.append(summary_score)

        return sum(factors) / len(factors) if factors else 0.0

    def _add_warnings(self, result: ExtractionResult) -> None:
        """Add warnings for potential extraction issues.
        
        Args:
            result: ExtractionResult to update
        """
        # Check for missing parties
        if not result.party_votes:
            result.warnings.append("No party votes extracted")

        # Check for missing summary fields
        if result.summary.accredited_voters == 0:
            result.warnings.append("Accredited voters not found")

        if result.summary.valid_votes == 0:
            result.warnings.append("Valid votes not found")

        # Check vote sum
        if result.party_votes and result.summary.valid_votes > 0:
            party_sum = result.total_party_votes
            diff = abs(party_sum - result.summary.valid_votes)
            if diff > 2:
                result.warnings.append(
                    f"Vote sum mismatch: party total ({party_sum}) != "
                    f"valid votes ({result.summary.valid_votes})"
                )

        # Check for unreasonable values
        if result.summary.valid_votes > result.summary.accredited_voters > 0:
            result.warnings.append(
                "Valid votes exceed accredited voters"
            )
