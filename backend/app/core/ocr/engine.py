"""OCR orchestration engine for election result extraction.

This module provides the main OCR orchestration using GPT-4 Vision as the
primary engine for all image processing. GPT-4 Vision handles both
high-quality and low-quality images with superior accuracy for election
result sheets, which often contain handwritten corrections and mixed fonts.

Requirements: 3.1
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import numpy as np

from app.core.ocr.preprocessing import ImagePreprocessor, ProcessedImage, QualityScore
from app.core.ocr.vision import ExtractionResult, GPT4VisionEngine

logger = logging.getLogger(__name__)


class OCREngine(StrEnum):
    """Available OCR engines."""

    GPT4_VISION = "gpt4_vision"
    # AUTO is kept for API compatibility — always resolves to GPT4_VISION
    AUTO = "auto"


@dataclass
class OCROrchestrationResult:
    """Result from OCR orchestration.

    Attributes:
        text: Raw response text from GPT-4 Vision
        extraction: Structured extraction result from GPT-4 Vision
        engine_used: OCR engine used (always GPT4_VISION)
        quality_score: Image quality assessment
        preprocessing_applied: List of preprocessing steps applied
        fallback_used: Always False (no fallback needed with GPT-4 Vision)
    """

    text: str
    extraction: ExtractionResult | None
    engine_used: OCREngine
    quality_score: QualityScore
    preprocessing_applied: list[str]
    fallback_used: bool = False

    @property
    def confidence(self) -> float:
        """Get overall confidence score."""
        if self.extraction:
            return self.extraction.confidence
        return 0.0

    @property
    def is_successful(self) -> bool:
        """Check if extraction was successful."""
        if self.extraction:
            return self.extraction.is_valid
        return bool(self.text.strip())


class OCROrchestrator:
    """Orchestrates OCR processing using GPT-4 Vision.

    GPT-4 Vision is used for all images regardless of quality, providing
    superior accuracy for election result sheets that contain handwritten
    figures, mixed fonts, stamps, and low-quality scans.

    Requirements: 3.1
    """

    def __init__(
        self,
        openai_api_key: str | None = None,
        openai_model: str = "gpt-4o",
        preprocess_images: bool = True,
        # Kept for API compatibility but no longer used for engine selection
        quality_threshold: float = 0.7,
        enable_fallback: bool = False,
        tesseract_lang: str = "eng",
        tesseract_config: str = "--psm 6",
    ):
        """Initialize OCR orchestrator.

        Args:
            openai_api_key: OpenAI API key for GPT-4 Vision
            openai_model: OpenAI model to use (default: gpt-4o)
            preprocess_images: Whether to preprocess images before OCR
            quality_threshold: Kept for API compatibility (unused)
            enable_fallback: Kept for API compatibility (unused)
            tesseract_lang: Kept for API compatibility (unused)
            tesseract_config: Kept for API compatibility (unused)
        """
        self.quality_threshold = quality_threshold
        self.enable_fallback = False  # GPT-4 Vision is the only engine
        self.preprocess_images = preprocess_images

        # Initialize preprocessor (still useful for quality assessment metadata)
        self.preprocessor = ImagePreprocessor(quality_threshold=quality_threshold)

        # Initialize GPT-4 Vision engine (lazy)
        self._gpt4_vision: GPT4VisionEngine | None = None
        self._openai_api_key = openai_api_key
        self._openai_model = openai_model

    @property
    def gpt4_vision(self) -> GPT4VisionEngine:
        """Get or create GPT-4 Vision engine instance."""
        if self._gpt4_vision is None:
            self._gpt4_vision = GPT4VisionEngine(
                api_key=self._openai_api_key,
                model=self._openai_model,
            )
        return self._gpt4_vision

    def process(
        self,
        image_path: str | Path,
        engine: OCREngine = OCREngine.AUTO,
        extract_structured: bool = True,
    ) -> OCROrchestrationResult:
        """Process image with GPT-4 Vision OCR.

        Args:
            image_path: Path to the image file
            engine: Ignored — always uses GPT-4 Vision
            extract_structured: Whether to extract structured data

        Returns:
            OCROrchestrationResult with extracted data
        """
        image_path = Path(image_path)

        # Preprocess image and assess quality (metadata only — GPT-4 Vision
        # handles the actual reading regardless of quality score)
        if self.preprocess_images:
            processed = self.preprocessor.preprocess(image_path)
        else:
            import cv2
            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            quality_score = self.preprocessor.assess_quality(image)
            processed = ProcessedImage(
                image=image,
                original_path=str(image_path),
                quality_score=quality_score,
                preprocessing_applied=[],
                deskew_angle=0.0,
            )

        logger.info(
            f"Processing {image_path.name} with GPT-4 Vision "
            f"(quality: {processed.quality_score.overall_score:.2f})"
        )

        return self._run_gpt4_vision(image_path, processed)

    async def process_async(
        self,
        image_path: str | Path,
        engine: OCREngine = OCREngine.AUTO,
        extract_structured: bool = True,
    ) -> OCROrchestrationResult:
        """Process image asynchronously with GPT-4 Vision OCR.

        Args:
            image_path: Path to the image file
            engine: Ignored — always uses GPT-4 Vision
            extract_structured: Whether to extract structured data

        Returns:
            OCROrchestrationResult with extracted data
        """
        image_path = Path(image_path)

        if self.preprocess_images:
            processed = self.preprocessor.preprocess(image_path)
        else:
            import cv2
            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            quality_score = self.preprocessor.assess_quality(image)
            processed = ProcessedImage(
                image=image,
                original_path=str(image_path),
                quality_score=quality_score,
                preprocessing_applied=[],
                deskew_angle=0.0,
            )

        logger.info(
            f"Processing {image_path.name} with GPT-4 Vision (async) "
            f"(quality: {processed.quality_score.overall_score:.2f})"
        )

        return await self._run_gpt4_vision_async(image_path, processed)

    def process_array(
        self,
        image: np.ndarray,
        engine: OCREngine = OCREngine.AUTO,
        extract_structured: bool = True,
    ) -> OCROrchestrationResult:
        """Process numpy array image with GPT-4 Vision OCR.

        Args:
            image: Image as numpy array
            engine: Ignored — always uses GPT-4 Vision
            extract_structured: Whether to extract structured data

        Returns:
            OCROrchestrationResult with extracted data
        """
        if self.preprocess_images:
            processed = self.preprocessor.preprocess_array(image)
        else:
            quality_score = self.preprocessor.assess_quality(image)
            processed = ProcessedImage(
                image=image,
                original_path=None,
                quality_score=quality_score,
                preprocessing_applied=[],
                deskew_angle=0.0,
            )

        text = ""
        extraction = None
        try:
            extraction = self.gpt4_vision.extract_from_array(processed.image)
            text = extraction.raw_response
        except Exception as e:
            logger.error(f"GPT-4 Vision array processing failed: {e}")

        return OCROrchestrationResult(
            text=text,
            extraction=extraction,
            engine_used=OCREngine.GPT4_VISION,
            quality_score=processed.quality_score,
            preprocessing_applied=processed.preprocessing_applied,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_gpt4_vision(
        self, image_path: Path, processed: ProcessedImage
    ) -> OCROrchestrationResult:
        """Run GPT-4 Vision synchronously."""
        text = ""
        extraction = None
        try:
            extraction = self.gpt4_vision.extract(image_path)
            text = extraction.raw_response
        except Exception as e:
            logger.error(f"GPT-4 Vision processing failed for {image_path.name}: {e}")

        return OCROrchestrationResult(
            text=text,
            extraction=extraction,
            engine_used=OCREngine.GPT4_VISION,
            quality_score=processed.quality_score,
            preprocessing_applied=processed.preprocessing_applied,
        )

    async def _run_gpt4_vision_async(
        self, image_path: Path, processed: ProcessedImage
    ) -> OCROrchestrationResult:
        """Run GPT-4 Vision asynchronously."""
        text = ""
        extraction = None
        try:
            extraction = await self.gpt4_vision.extract_async(image_path)
            text = extraction.raw_response
        except Exception as e:
            logger.error(f"GPT-4 Vision async processing failed for {image_path.name}: {e}")

        return OCROrchestrationResult(
            text=text,
            extraction=extraction,
            engine_used=OCREngine.GPT4_VISION,
            quality_score=processed.quality_score,
            preprocessing_applied=processed.preprocessing_applied,
        )

    def get_engine_status(self) -> dict:
        """Get status of available OCR engines.

        Returns:
            Dictionary with engine availability status
        """
        status: dict = {
            "gpt4_vision": {
                "available": False,
                "model": self._openai_model,
            },
        }

        try:
            if self.gpt4_vision.is_available():
                status["gpt4_vision"]["available"] = True
        except Exception:
            pass

        return status
