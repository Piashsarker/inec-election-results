"""GPT-4 Vision integration for complex document understanding.

This module provides GPT-4 Vision API integration for extracting
election data from complex, handwritten, or low-quality result sheet
images where traditional OCR may struggle.

Requirements: 3.1, 3.2
"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

try:
    from openai import AsyncOpenAI, OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class PartyVoteResult:
    """Vote result for a single political party.

    Attributes:
        name: Full party name
        code: Party abbreviation/code (e.g., APC, PDP)
        votes: Number of votes received
        confidence: Confidence in this extraction (0-1)
    """

    name: str
    code: str
    votes: int
    confidence: float = 1.0


@dataclass
class ExtractionResult:
    """Result of GPT-4 Vision data extraction.

    Attributes:
        parties: List of party vote results
        accredited_voters: Total number of accredited voters
        valid_votes: Total number of valid votes
        rejected_votes: Total number of rejected/invalid votes
        confidence: Overall confidence score (0-1)
        raw_response: Raw API response text
        metadata: Additional extracted metadata
    """

    parties: list[PartyVoteResult] = field(default_factory=list)
    accredited_voters: int = 0
    valid_votes: int = 0
    rejected_votes: int = 0
    confidence: float = 0.0
    raw_response: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_party_votes(self) -> int:
        """Calculate sum of all party votes."""
        return sum(p.votes for p in self.parties)

    @property
    def is_valid(self) -> bool:
        """Check if extraction appears valid."""
        return (
            len(self.parties) > 0 and
            self.valid_votes > 0 and
            self.confidence >= 0.5
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "parties": [
                {
                    "name": p.name,
                    "code": p.code,
                    "votes": p.votes,
                    "confidence": p.confidence,
                }
                for p in self.parties
            ],
            "accredited_voters": self.accredited_voters,
            "valid_votes": self.valid_votes,
            "rejected_votes": self.rejected_votes,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class GPT4VisionEngine:
    """GPT-4 Vision for complex/handwritten document understanding.

    This engine uses OpenAI's GPT-4 Vision model to extract election
    data from result sheet images. It's particularly effective for:
    - Handwritten documents
    - Low-quality scans
    - Complex layouts
    - Documents where traditional OCR fails

    Requirements: 3.1, 3.2
    """

    # Extraction prompt for Nigerian election result sheets
    EXTRACTION_PROMPT = (
        """Analyze this Nigerian election result sheet image """
        """and extract the following information:

1. All political party names and their abbreviations (codes)
2. Vote count for each party (numeric values only)
3. Total accredited voters
4. Total valid votes
5. Total rejected/invalid votes

Common Nigerian political parties include:
- APC (All Progressives Congress)
- PDP (Peoples Democratic Party)
- LP (Labour Party)
- NNPP (New Nigeria Peoples Party)
- APGA (All Progressives Grand Alliance)
- ADC (African Democratic Congress)
- SDP (Social Democratic Party)
- YPP (Young Progressives Party)
- ZLP (Zenith Labour Party)
- AA (Action Alliance)

Return the data as valid JSON in this exact format:
{
    "parties": [
        {"name": "Full Party Name", "code": "CODE", "votes": 0}
    ],
    "accredited_voters": 0,
    "valid_votes": 0,
    "rejected_votes": 0,
    "confidence": 0.0
}

Rules:
- Only include parties that have vote counts visible in the image
- Use 0 for any values that cannot be clearly read
- Set confidence between 0.0 and 1.0 based on image clarity and your certainty
- If you cannot read the document at all, set confidence to 0.0
- Return ONLY the JSON, no additional text"""
    )

    VERIFICATION_PROMPT = """Verify the following extracted election data against the image:

{extracted_data}

Check:
1. Are all party names and codes correct?
2. Are all vote counts accurate?
3. Do the totals match what's shown in the image?
4. Is there any data in the image that was missed?

Return corrections as JSON in the same format, or return the original if correct.
Include a "verification_notes" field with any observations."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        max_tokens: int = 1000,
        temperature: float = 0.0,
    ):
        """Initialize GPT-4 Vision engine.

        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
            model: OpenAI model to use (gpt-4-vision-preview or gpt-4o)
            max_tokens: Maximum tokens for API response
            temperature: Model temperature (0.0 for deterministic output)

        Raises:
            RuntimeError: If OpenAI library is not available
        """
        if not OPENAI_AVAILABLE:
            raise RuntimeError(
                "openai library is not installed. "
                "Install with: pip install openai"
            )

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Initialize clients
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.async_client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

    def extract(
        self,
        image_path: str | Path,
        verify: bool = False,
    ) -> ExtractionResult:
        """Extract election data from image using GPT-4 Vision.

        Args:
            image_path: Path to the result sheet image
            verify: Whether to run verification pass

        Returns:
            ExtractionResult with extracted election data
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Encode image to base64
        base64_image = self._encode_image(image_path)

        # Make API request
        response = self._call_vision_api(base64_image, self.EXTRACTION_PROMPT)

        # Parse response
        result = self._parse_response(response)

        # Optional verification pass
        if verify and result.confidence > 0.3:
            result = self._verify_extraction(base64_image, result)

        return result

    async def extract_async(
        self,
        image_path: str | Path,
        verify: bool = False,
    ) -> ExtractionResult:
        """Extract election data asynchronously.

        Args:
            image_path: Path to the result sheet image
            verify: Whether to run verification pass

        Returns:
            ExtractionResult with extracted election data
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Encode image to base64
        base64_image = self._encode_image(image_path)

        # Make async API request
        response = await self._call_vision_api_async(
            base64_image, self.EXTRACTION_PROMPT
        )

        # Parse response
        result = self._parse_response(response)

        # Optional verification pass
        if verify and result.confidence > 0.3:
            result = await self._verify_extraction_async(base64_image, result)

        return result

    def extract_from_array(
        self,
        image: np.ndarray,
        verify: bool = False,
    ) -> ExtractionResult:
        """Extract election data from numpy array image.

        Args:
            image: Image as numpy array
            verify: Whether to run verification pass

        Returns:
            ExtractionResult with extracted election data
        """
        # Encode numpy array to base64
        base64_image = self._encode_array(image)

        # Make API request
        response = self._call_vision_api(base64_image, self.EXTRACTION_PROMPT)

        # Parse response
        result = self._parse_response(response)

        # Optional verification pass
        if verify and result.confidence > 0.3:
            result = self._verify_extraction(base64_image, result)

        return result

    def _encode_image(self, image_path: Path) -> str:
        """Encode image file to base64 string.

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")

    def _encode_array(self, image: np.ndarray) -> str:
        """Encode numpy array image to base64 string.

        Args:
            image: Image as numpy array

        Returns:
            Base64 encoded image string
        """
        import cv2

        # Encode as JPEG
        _, buffer = cv2.imencode(".jpg", image)
        return base64.standard_b64encode(buffer).decode("utf-8")

    def _get_image_media_type(self, image_path: Path) -> str:
        """Get media type for image file.

        Args:
            image_path: Path to image file

        Returns:
            Media type string (e.g., 'image/jpeg')
        """
        suffix = image_path.suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(suffix, "image/jpeg")

    def _call_vision_api(self, base64_image: str, prompt: str) -> str:
        """Call GPT-4 Vision API synchronously.

        Args:
            base64_image: Base64 encoded image
            prompt: Extraction prompt

        Returns:
            API response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"GPT-4 Vision API error: {e}")
            raise

    async def _call_vision_api_async(
        self, base64_image: str, prompt: str
    ) -> str:
        """Call GPT-4 Vision API asynchronously.

        Args:
            base64_image: Base64 encoded image
            prompt: Extraction prompt

        Returns:
            API response text
        """
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"GPT-4 Vision API error: {e}")
            raise

    def _parse_response(self, response: str) -> ExtractionResult:
        """Parse GPT-4 Vision API response into ExtractionResult.

        Args:
            response: Raw API response text

        Returns:
            ExtractionResult with parsed data
        """
        result = ExtractionResult(raw_response=response)

        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response.strip()
            if json_str.startswith("```"):
                # Remove markdown code block
                lines = json_str.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block:
                        json_lines.append(line)
                json_str = "\n".join(json_lines)

            data = json.loads(json_str)

            # Parse parties
            for party_data in data.get("parties", []):
                party = PartyVoteResult(
                    name=party_data.get("name", ""),
                    code=party_data.get("code", ""),
                    votes=int(party_data.get("votes", 0)),
                    confidence=float(party_data.get("confidence", 1.0)),
                )
                result.parties.append(party)

            # Parse totals
            result.accredited_voters = int(data.get("accredited_voters", 0))
            result.valid_votes = int(data.get("valid_votes", 0))
            result.rejected_votes = int(data.get("rejected_votes", 0))
            result.confidence = float(data.get("confidence", 0.0))

            # Store any additional metadata
            for key in data:
                if key not in {
                    "parties", "accredited_voters", "valid_votes",
                    "rejected_votes", "confidence"
                }:
                    result.metadata[key] = data[key]

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            result.confidence = 0.0
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            result.confidence = 0.0

        return result

    def _verify_extraction(
        self,
        base64_image: str,
        result: ExtractionResult,
    ) -> ExtractionResult:
        """Verify and potentially correct extraction results.

        Args:
            base64_image: Base64 encoded image
            result: Initial extraction result

        Returns:
            Verified/corrected ExtractionResult
        """
        prompt = self.VERIFICATION_PROMPT.format(
            extracted_data=json.dumps(result.to_dict(), indent=2)
        )

        try:
            response = self._call_vision_api(base64_image, prompt)
            verified = self._parse_response(response)

            # Use verified result if it has higher confidence
            if verified.confidence >= result.confidence:
                return verified

        except Exception as e:
            logger.warning(f"Verification failed: {e}")

        return result

    async def _verify_extraction_async(
        self,
        base64_image: str,
        result: ExtractionResult,
    ) -> ExtractionResult:
        """Verify extraction results asynchronously.

        Args:
            base64_image: Base64 encoded image
            result: Initial extraction result

        Returns:
            Verified/corrected ExtractionResult
        """
        prompt = self.VERIFICATION_PROMPT.format(
            extracted_data=json.dumps(result.to_dict(), indent=2)
        )

        try:
            response = await self._call_vision_api_async(base64_image, prompt)
            verified = self._parse_response(response)

            # Use verified result if it has higher confidence
            if verified.confidence >= result.confidence:
                return verified

        except Exception as e:
            logger.warning(f"Verification failed: {e}")

        return result

    def is_available(self) -> bool:
        """Check if GPT-4 Vision API is available.

        Returns:
            True if API is accessible
        """
        try:
            # Make a minimal test request
            self.client.models.list()
            return True
        except Exception:
            return False
