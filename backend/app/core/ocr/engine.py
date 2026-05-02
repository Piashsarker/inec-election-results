"""OCR orchestration engine for election result extraction.

This module provides the main OCR orchestration that coordinates between
different OCR engines (Tesseract and GPT-4 Vision) based on image quality
assessment. It implements intelligent engine selection and fallback logic.

Requirements: 3.1
"""
from __future__ import annotations


import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np

from app.core.ocr.preprocessing import ImagePreprocessor, ProcessedImage, QualityScore
from app.core.ocr.tesseract import OCRResult, TesseractEngine
from app.core.ocr.vision import ExtractionResult, GPT4VisionEngine

logger = logging.getLogger(__name__)


class OCREngine(str, Enum):
    """Available OCR engines."""

    TESSERACT = "tesseract"
    GPT4_VISION = "gpt4_vision"
    AUTO = "auto"


@dataclass
class OCROrchestrationResult:
    """Result from OCR orchestration.
    
    Attributes:
        text: Extracted text (from Tesseract)
        extraction: Structured extraction result (from GPT-4 Vision or parsed)
        engine_used: Which OCR engine was used
        quality_score: Image quality assessment
        preprocessing_applied: List of preprocessing steps applied
        fallback_used: Whether fallback engine was used
        raw_ocr_result: Raw OCR result from Tesseract (if used)
    """

    text: str
    extraction: ExtractionResult | None
    engine_used: OCREngine
    quality_score: QualityScore
    preprocessing_applied: list[str]
    fallback_used: bool = False
    raw_ocr_result: OCRResult | None = None

    @property
    def confidence(self) -> float:
        """Get overall confidence score."""
        if self.extraction:
            return self.extraction.confidence
        if self.raw_ocr_result:
            return self.raw_ocr_result.normalized_confidence
        return 0.0

    @property
    def is_successful(self) -> bool:
        """Check if extraction was successful."""
        if self.extraction:
            return self.extraction.is_valid
        return bool(self.text.strip())


class OCROrchestrator:
    """Orchestrates OCR processing with intelligent engine selection.
    
    This class coordinates between Tesseract and GPT-4 Vision engines,
    selecting the appropriate engine based on image quality assessment.
    It also handles preprocessing and fallback logic.
    
    Engine Selection Logic:
    - High quality images (score >= threshold) -> Tesseract (faster, cheaper)
    - Low quality/handwritten images -> GPT-4 Vision (better understanding)
    - If primary engine fails -> Fallback to alternative engine
    
    Requirements: 3.1
    """

    def __init__(
        self,
        quality_threshold: float = 0.7,
        tesseract_lang: str = "eng",
        tesseract_config: str = "--psm 6",
        openai_api_key: str | None = None,
        openai_model: str = "gpt-4o",
        enable_fallback: bool = True,
        preprocess_images: bool = True,
    ):
        """Initialize OCR orchestrator.
        
        Args:
            quality_threshold: Threshold for high/low quality classification
            tesseract_lang: Tesseract language code
            tesseract_config: Tesseract configuration options
            openai_api_key: OpenAI API key for GPT-4 Vision
            openai_model: OpenAI model to use
            enable_fallback: Whether to enable fallback to alternative engine
            preprocess_images: Whether to preprocess images before OCR
        """
        self.quality_threshold = quality_threshold
        self.enable_fallback = enable_fallback
        self.preprocess_images = preprocess_images

        # Initialize preprocessor
        self.preprocessor = ImagePreprocessor(quality_threshold=quality_threshold)

        # Initialize engines (lazy loading)
        self._tesseract: TesseractEngine | None = None
        self._gpt4_vision: GPT4VisionEngine | None = None

        # Engine configuration
        self._tesseract_lang = tesseract_lang
        self._tesseract_config = tesseract_config
        self._openai_api_key = openai_api_key
        self._openai_model = openai_model

    @property
    def tesseract(self) -> TesseractEngine:
        """Get or create Tesseract engine instance."""
        if self._tesseract is None:
            self._tesseract = TesseractEngine(
                lang=self._tesseract_lang,
                config=self._tesseract_config,
            )
        return self._tesseract

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
        """Process image with OCR orchestration.
        
        Args:
            image_path: Path to the image file
            engine: Which OCR engine to use (AUTO for automatic selection)
            extract_structured: Whether to extract structured data
            
        Returns:
            OCROrchestrationResult with extracted data
        """
        image_path = Path(image_path)

        # Preprocess image
        if self.preprocess_images:
            processed = self.preprocessor.preprocess(image_path)
        else:
            # Load image without preprocessing
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

        # Determine which engine to use
        if engine == OCREngine.AUTO:
            engine = self._select_engine(processed.quality_score)

        logger.info(
            f"Processing {image_path.name} with {engine.value} "
            f"(quality: {processed.quality_score.overall_score:.2f})"
        )

        # Process with selected engine
        result = self._process_with_engine(
            processed, image_path, engine, extract_structured
        )

        # Fallback if primary engine fails
        if (
            self.enable_fallback and
            not result.is_successful and
            engine != OCREngine.AUTO
        ):
            fallback_engine = self._get_fallback_engine(engine)
            logger.info(f"Falling back to {fallback_engine.value}")

            fallback_result = self._process_with_engine(
                processed, image_path, fallback_engine, extract_structured
            )

            if fallback_result.is_successful:
                fallback_result.fallback_used = True
                return fallback_result

        return result

    async def process_async(
        self,
        image_path: str | Path,
        engine: OCREngine = OCREngine.AUTO,
        extract_structured: bool = True,
    ) -> OCROrchestrationResult:
        """Process image asynchronously with OCR orchestration.
        
        Args:
            image_path: Path to the image file
            engine: Which OCR engine to use (AUTO for automatic selection)
            extract_structured: Whether to extract structured data
            
        Returns:
            OCROrchestrationResult with extracted data
        """
        image_path = Path(image_path)

        # Preprocess image
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

        # Determine which engine to use
        if engine == OCREngine.AUTO:
            engine = self._select_engine(processed.quality_score)

        logger.info(
            f"Processing {image_path.name} with {engine.value} "
            f"(quality: {processed.quality_score.overall_score:.2f})"
        )

        # Process with selected engine
        result = await self._process_with_engine_async(
            processed, image_path, engine, extract_structured
        )

        # Fallback if primary engine fails
        if (
            self.enable_fallback and
            not result.is_successful and
            engine != OCREngine.AUTO
        ):
            fallback_engine = self._get_fallback_engine(engine)
            logger.info(f"Falling back to {fallback_engine.value}")

            fallback_result = await self._process_with_engine_async(
                processed, image_path, fallback_engine, extract_structured
            )

            if fallback_result.is_successful:
                fallback_result.fallback_used = True
                return fallback_result

        return result

    def process_array(
        self,
        image: np.ndarray,
        engine: OCREngine = OCREngine.AUTO,
        extract_structured: bool = True,
    ) -> OCROrchestrationResult:
        """Process numpy array image with OCR orchestration.
        
        Args:
            image: Image as numpy array
            engine: Which OCR engine to use (AUTO for automatic selection)
            extract_structured: Whether to extract structured data
            
        Returns:
            OCROrchestrationResult with extracted data
        """
        # Preprocess image
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

        # Determine which engine to use
        if engine == OCREngine.AUTO:
            engine = self._select_engine(processed.quality_score)

        # Process with selected engine
        return self._process_array_with_engine(
            processed, engine, extract_structured
        )

    def _select_engine(self, quality_score: QualityScore) -> OCREngine:
        """Select OCR engine based on image quality.
        
        Args:
            quality_score: Image quality assessment
            
        Returns:
            Selected OCR engine
        """
        if quality_score.overall_score >= self.quality_threshold:
            return OCREngine.TESSERACT
        return OCREngine.GPT4_VISION

    def _get_fallback_engine(self, primary: OCREngine) -> OCREngine:
        """Get fallback engine for the given primary engine.
        
        Args:
            primary: Primary OCR engine
            
        Returns:
            Fallback OCR engine
        """
        if primary == OCREngine.TESSERACT:
            return OCREngine.GPT4_VISION
        return OCREngine.TESSERACT

    def _process_with_engine(
        self,
        processed: ProcessedImage,
        image_path: Path,
        engine: OCREngine,
        extract_structured: bool,
    ) -> OCROrchestrationResult:
        """Process image with specified engine.
        
        Args:
            processed: Preprocessed image
            image_path: Original image path
            engine: OCR engine to use
            extract_structured: Whether to extract structured data
            
        Returns:
            OCROrchestrationResult
        """
        text = ""
        extraction = None
        raw_ocr_result = None

        try:
            if engine == OCREngine.TESSERACT:
                # Use Tesseract for text extraction
                raw_ocr_result = self.tesseract.extract_text(processed.image)
                text = raw_ocr_result.text

            elif engine == OCREngine.GPT4_VISION:
                # Use GPT-4 Vision for structured extraction
                if extract_structured:
                    extraction = self.gpt4_vision.extract(image_path)
                    text = extraction.raw_response
                else:
                    # Just get text without structured extraction
                    extraction = self.gpt4_vision.extract(image_path)
                    text = extraction.raw_response

        except Exception as e:
            logger.error(f"OCR processing failed with {engine.value}: {e}")

        return OCROrchestrationResult(
            text=text,
            extraction=extraction,
            engine_used=engine,
            quality_score=processed.quality_score,
            preprocessing_applied=processed.preprocessing_applied,
            raw_ocr_result=raw_ocr_result,
        )

    async def _process_with_engine_async(
        self,
        processed: ProcessedImage,
        image_path: Path,
        engine: OCREngine,
        extract_structured: bool,
    ) -> OCROrchestrationResult:
        """Process image with specified engine asynchronously.
        
        Args:
            processed: Preprocessed image
            image_path: Original image path
            engine: OCR engine to use
            extract_structured: Whether to extract structured data
            
        Returns:
            OCROrchestrationResult
        """
        text = ""
        extraction = None
        raw_ocr_result = None

        try:
            if engine == OCREngine.TESSERACT:
                # Tesseract is synchronous, run in thread pool
                import asyncio
                loop = asyncio.get_event_loop()
                raw_ocr_result = await loop.run_in_executor(
                    None, self.tesseract.extract_text, processed.image
                )
                text = raw_ocr_result.text

            elif engine == OCREngine.GPT4_VISION:
                # Use async GPT-4 Vision
                if extract_structured:
                    extraction = await self.gpt4_vision.extract_async(image_path)
                    text = extraction.raw_response
                else:
                    extraction = await self.gpt4_vision.extract_async(image_path)
                    text = extraction.raw_response

        except Exception as e:
            logger.error(f"OCR processing failed with {engine.value}: {e}")

        return OCROrchestrationResult(
            text=text,
            extraction=extraction,
            engine_used=engine,
            quality_score=processed.quality_score,
            preprocessing_applied=processed.preprocessing_applied,
            raw_ocr_result=raw_ocr_result,
        )

    def _process_array_with_engine(
        self,
        processed: ProcessedImage,
        engine: OCREngine,
        extract_structured: bool,
    ) -> OCROrchestrationResult:
        """Process numpy array with specified engine.
        
        Args:
            processed: Preprocessed image
            engine: OCR engine to use
            extract_structured: Whether to extract structured data
            
        Returns:
            OCROrchestrationResult
        """
        text = ""
        extraction = None
        raw_ocr_result = None

        try:
            if engine == OCREngine.TESSERACT:
                raw_ocr_result = self.tesseract.extract_text(processed.image)
                text = raw_ocr_result.text

            elif engine == OCREngine.GPT4_VISION:
                if extract_structured:
                    extraction = self.gpt4_vision.extract_from_array(processed.image)
                    text = extraction.raw_response
                else:
                    extraction = self.gpt4_vision.extract_from_array(processed.image)
                    text = extraction.raw_response

        except Exception as e:
            logger.error(f"OCR processing failed with {engine.value}: {e}")

        return OCROrchestrationResult(
            text=text,
            extraction=extraction,
            engine_used=engine,
            quality_score=processed.quality_score,
            preprocessing_applied=processed.preprocessing_applied,
            raw_ocr_result=raw_ocr_result,
        )

    def get_engine_status(self) -> dict:
        """Get status of available OCR engines.
        
        Returns:
            Dictionary with engine availability status
        """
        status = {
            "tesseract": {
                "available": False,
                "languages": [],
            },
            "gpt4_vision": {
                "available": False,
            },
        }

        try:
            if self.tesseract.is_available():
                status["tesseract"]["available"] = True
                status["tesseract"]["languages"] = self.tesseract.get_supported_languages()
        except Exception:
            pass

        try:
            if self.gpt4_vision.is_available():
                status["gpt4_vision"]["available"] = True
        except Exception:
            pass

        return status
