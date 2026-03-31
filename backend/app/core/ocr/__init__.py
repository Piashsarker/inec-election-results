"""OCR and image processing components."""

from app.core.ocr.preprocessing import (
    ImageFormat,
    ImagePreprocessor,
    ProcessedImage,
    QualityScore,
)
from app.core.ocr.tesseract import (
    OCRResult,
    Table,
    TableCell,
    TesseractEngine,
    TextBlock,
)
from app.core.ocr.vision import (
    ExtractionResult as VisionExtractionResult,
    GPT4VisionEngine,
    PartyVoteResult,
)
from app.core.ocr.engine import (
    OCREngine,
    OCROrchestrationResult,
    OCROrchestrator,
)

__all__ = [
    # Preprocessing
    "ImageFormat",
    "ImagePreprocessor",
    "ProcessedImage",
    "QualityScore",
    # Tesseract
    "OCRResult",
    "Table",
    "TableCell",
    "TesseractEngine",
    "TextBlock",
    # GPT-4 Vision
    "VisionExtractionResult",
    "GPT4VisionEngine",
    "PartyVoteResult",
    # Orchestration
    "OCREngine",
    "OCROrchestrationResult",
    "OCROrchestrator",
]
