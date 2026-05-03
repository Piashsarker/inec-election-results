"""Processor agent for OCR and data extraction.

This module provides the processor agent that handles OCR processing
and data extraction from result sheet images.

Requirements: 3.1, 3.2
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.agents.graph import AgentState, ProcessingStatus
from app.core.extractor.parser import ElectionDataExtractor, ExtractionResult
from app.core.ocr.engine import OCREngine, OCROrchestrationResult, OCROrchestrator

logger = logging.getLogger("inec_agent.agents.processor")


@dataclass
class ProcessingResult:
    """Result of processing a result sheet image.

    Attributes:
        success: Whether processing was successful
        ocr_result: OCR processing result
        extraction_result: Data extraction result
        error: Error message if processing failed
    """

    success: bool
    ocr_result: OCROrchestrationResult | None = None
    extraction_result: ExtractionResult | None = None
    error: str | None = None


class ProcessorAgent:
    """Agent for OCR processing and data extraction.

    This agent handles:
    - Image preprocessing for optimal OCR performance
    - OCR processing using Tesseract or GPT-4 Vision
    - Data extraction from OCR output
    - Confidence scoring and quality assessment

    Requirements: 3.1, 3.2
    """

    def __init__(
        self,
        quality_threshold: float = 0.7,
        openai_api_key: str | None = None,
        openai_model: str = "gpt-4o",
        tesseract_lang: str = "eng",
        enable_fallback: bool = True,
    ):
        """Initialize the processor agent.

        Args:
            quality_threshold: Threshold for OCR engine selection
            openai_api_key: OpenAI API key for GPT-4 Vision
            openai_model: OpenAI model to use
            tesseract_lang: Tesseract language code
            enable_fallback: Whether to enable fallback to alternative engine
        """
        self.ocr_orchestrator = OCROrchestrator(
            quality_threshold=quality_threshold,
            tesseract_lang=tesseract_lang,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            enable_fallback=enable_fallback,
        )

        self.extractor = ElectionDataExtractor()

        logger.info("ProcessorAgent initialized")

    async def process_image(
        self,
        image_path: str,
        engine: OCREngine = OCREngine.AUTO,
    ) -> ProcessingResult:
        """Process a result sheet image.

        This method performs OCR on the image and extracts structured
        election data from the OCR output.

        Args:
            image_path: Path to the result sheet image
            engine: OCR engine to use (AUTO for automatic selection)

        Returns:
            ProcessingResult with OCR and extraction results
        """
        logger.info(f"Processing image: {image_path}")

        try:
            # Verify file exists
            path = Path(image_path)
            if not path.exists():
                logger.error(f"Image file not found: {image_path}")
                return ProcessingResult(
                    success=False,
                    error=f"Image file not found: {image_path}",
                )

            # Perform OCR
            ocr_result = await self.ocr_orchestrator.process_async(
                image_path=path,
                engine=engine,
                extract_structured=True,
            )

            logger.info(
                f"OCR completed with {ocr_result.engine_used.value}, "
                f"confidence: {ocr_result.confidence:.2f}"
            )

            # Extract structured data
            if ocr_result.raw_ocr_result:
                # Use Tesseract OCR result
                extraction_result = self.extractor.extract(ocr_result.raw_ocr_result)
            elif ocr_result.extraction:
                # GPT-4 Vision already provides structured extraction
                # Convert to our ExtractionResult format
                extraction_result = self._convert_vision_extraction(ocr_result.extraction)
            else:
                # Fallback to text extraction
                extraction_result = self.extractor.extract_from_text(ocr_result.text)

            logger.info(
                f"Extraction completed: {len(extraction_result.party_votes)} parties, "
                f"confidence: {extraction_result.confidence:.2f}"
            )

            return ProcessingResult(
                success=True,
                ocr_result=ocr_result,
                extraction_result=extraction_result,
            )

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return ProcessingResult(
                success=False,
                error=str(e),
            )

    def process_image_sync(
        self,
        image_path: str,
        engine: OCREngine = OCREngine.AUTO,
    ) -> ProcessingResult:
        """Process a result sheet image synchronously.

        Args:
            image_path: Path to the result sheet image
            engine: OCR engine to use (AUTO for automatic selection)

        Returns:
            ProcessingResult with OCR and extraction results
        """
        logger.info(f"Processing image (sync): {image_path}")

        try:
            # Verify file exists
            path = Path(image_path)
            if not path.exists():
                logger.error(f"Image file not found: {image_path}")
                return ProcessingResult(
                    success=False,
                    error=f"Image file not found: {image_path}",
                )

            # Perform OCR
            ocr_result = self.ocr_orchestrator.process(
                image_path=path,
                engine=engine,
                extract_structured=True,
            )

            logger.info(
                f"OCR completed with {ocr_result.engine_used.value}, "
                f"confidence: {ocr_result.confidence:.2f}"
            )

            # Extract structured data
            if ocr_result.raw_ocr_result:
                extraction_result = self.extractor.extract(ocr_result.raw_ocr_result)
            elif ocr_result.extraction:
                extraction_result = self._convert_vision_extraction(ocr_result.extraction)
            else:
                extraction_result = self.extractor.extract_from_text(ocr_result.text)

            return ProcessingResult(
                success=True,
                ocr_result=ocr_result,
                extraction_result=extraction_result,
            )

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return ProcessingResult(
                success=False,
                error=str(e),
            )

    async def process_state(
        self,
        state: AgentState,
    ) -> AgentState:
        """Process the OCR and extraction steps for the workflow.

        This method is called by the LangGraph workflow to handle
        preprocessing, OCR, and extraction for downloaded images.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        logger.info(f"Processing images for job {state['job_id']}")

        # Check for downloaded images
        downloaded_images = state.get("downloaded_images", [])
        if not downloaded_images:
            state["errors"].append({
                "stage": "process",
                "message": "No downloaded images to process",
                "recoverable": False,
            })
            state["status"] = ProcessingStatus.FAILED.value
            return state

        # Process the first image (typically one per polling unit)
        image_info = downloaded_images[0]
        image_path = image_info.get("file_path")

        if not image_path:
            state["errors"].append({
                "stage": "process",
                "message": "No file path in downloaded image info",
                "recoverable": False,
            })
            state["status"] = ProcessingStatus.FAILED.value
            return state

        # Update status to preprocessing
        state["status"] = ProcessingStatus.PREPROCESSING.value

        # Process the image
        result = await self.process_image(image_path)

        if result.success:
            # Update state with OCR results
            state["status"] = ProcessingStatus.OCR_PROCESSING.value

            if result.ocr_result:
                state["ocr_results"] = {
                    "text": result.ocr_result.text,
                    "engine_used": result.ocr_result.engine_used.value,
                    "confidence": result.ocr_result.confidence,
                    "quality_score": result.ocr_result.quality_score.overall_score,
                    "preprocessing_applied": result.ocr_result.preprocessing_applied,
                    "fallback_used": result.ocr_result.fallback_used,
                }

            # Update state with extraction results
            state["status"] = ProcessingStatus.EXTRACTING.value

            if result.extraction_result:
                state["extracted_data"] = {
                    "party_votes": [
                        {
                            "party_name": pv.party_name,
                            "party_code": pv.party_code,
                            "votes": pv.votes,
                            "confidence": pv.confidence,
                        }
                        for pv in result.extraction_result.party_votes
                    ],
                    "summary": {
                        "accredited_voters": result.extraction_result.summary.accredited_voters,
                        "valid_votes": result.extraction_result.summary.valid_votes,
                        "rejected_votes": result.extraction_result.summary.rejected_votes,
                        "total_votes_cast": result.extraction_result.summary.total_votes_cast,
                    },
                    "confidence": result.extraction_result.confidence,
                    "warnings": result.extraction_result.warnings,
                    "polling_unit_name": result.extraction_result.polling_unit_name,
                    "ward_name": result.extraction_result.ward_name,
                    "lga_name": result.extraction_result.lga_name,
                    "state_name": result.extraction_result.state_name,
                }
        else:
            # Record error
            state["errors"].append({
                "stage": "process",
                "message": result.error or "Processing failed",
                "recoverable": True,
            })
            state["status"] = ProcessingStatus.FAILED.value

        return state

    def _convert_vision_extraction(self, vision_result: Any) -> ExtractionResult:
        """Convert GPT-4 Vision extraction to ExtractionResult format.

        Args:
            vision_result: Extraction result from GPT-4 Vision

        Returns:
            ExtractionResult in standard format
        """
        from app.core.extractor.parser import PartyVote, SummaryFields

        # Handle the case where vision_result is already an ExtractionResult-like object
        if hasattr(vision_result, 'parties'):
            conf = (
                vision_result.confidence
                if hasattr(vision_result, 'confidence')
                else 0.8
            )
            party_votes = [
                PartyVote(
                    party_name=p.get('name', ''),
                    party_code=p.get('code', ''),
                    votes=p.get('votes', 0),
                    confidence=conf,
                )
                for p in vision_result.parties
            ]

            summary = SummaryFields(
                accredited_voters=getattr(vision_result, 'accredited_voters', 0),
                valid_votes=getattr(vision_result, 'valid_votes', 0),
                rejected_votes=getattr(vision_result, 'rejected_votes', 0),
            )

            return ExtractionResult(
                party_votes=party_votes,
                summary=summary,
                confidence=getattr(vision_result, 'confidence', 0.8),
                raw_text=getattr(vision_result, 'raw_response', ''),
            )

        # Fallback for dictionary-like results
        return ExtractionResult(
            confidence=0.5,
            warnings=["Could not parse vision extraction result"],
        )

    def select_ocr_engine(self, quality_score: float) -> OCREngine:
        """Select appropriate OCR engine based on image quality.

        Args:
            quality_score: Image quality score (0-1)

        Returns:
            Selected OCR engine
        """
        if quality_score >= self.ocr_orchestrator.quality_threshold:
            return OCREngine.TESSERACT
        return OCREngine.GPT4_VISION

    def get_engine_status(self) -> dict[str, Any]:
        """Get status of available OCR engines.

        Returns:
            Dictionary with engine availability status
        """
        return self.ocr_orchestrator.get_engine_status()
