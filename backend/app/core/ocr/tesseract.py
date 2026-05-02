"""Tesseract OCR engine for high-quality printed documents.

This module provides Tesseract OCR integration for extracting text
from election result sheet images. It's optimized for clean, printed
documents and returns confidence scores with results.

Requirements: 3.1
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

try:
    import pytesseract
    from pytesseract import Output
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


@dataclass
class TextBlock:
    """A block of text extracted from an image.

    Attributes:
        text: The extracted text content
        confidence: Confidence score (0-100)
        x: X coordinate of bounding box
        y: Y coordinate of bounding box
        width: Width of bounding box
        height: Height of bounding box
        level: Tesseract hierarchy level (1=page, 2=block, 3=para, 4=line, 5=word)
        block_num: Block number within the page
        line_num: Line number within the block
        word_num: Word number within the line
    """

    text: str
    confidence: float
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    level: int = 5
    block_num: int = 0
    line_num: int = 0
    word_num: int = 0


@dataclass
class TableCell:
    """A cell in an extracted table.

    Attributes:
        text: Cell text content
        row: Row index (0-based)
        col: Column index (0-based)
        confidence: Confidence score (0-100)
        x: X coordinate
        y: Y coordinate
        width: Cell width
        height: Cell height
    """

    text: str
    row: int
    col: int
    confidence: float = 0.0
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


@dataclass
class Table:
    """An extracted table from the image.

    Attributes:
        cells: List of table cells
        rows: Number of rows
        cols: Number of columns
        x: X coordinate of table bounding box
        y: Y coordinate of table bounding box
        width: Table width
        height: Table height
    """

    cells: list[TableCell] = field(default_factory=list)
    rows: int = 0
    cols: int = 0
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    def get_cell(self, row: int, col: int) -> TableCell | None:
        """Get cell at specified row and column."""
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None

    def to_list(self) -> list[list[str]]:
        """Convert table to 2D list of strings."""
        result = [["" for _ in range(self.cols)] for _ in range(self.rows)]
        for cell in self.cells:
            if 0 <= cell.row < self.rows and 0 <= cell.col < self.cols:
                result[cell.row][cell.col] = cell.text
        return result


@dataclass
class OCRResult:
    """Result of OCR text extraction.

    Attributes:
        text: Full extracted text
        blocks: List of text blocks with positions and confidence
        confidence: Average confidence score (0-100)
        tables: List of extracted tables
        language: Language used for OCR
        engine: OCR engine identifier
    """

    text: str
    blocks: list[TextBlock] = field(default_factory=list)
    confidence: float = 0.0
    tables: list[Table] = field(default_factory=list)
    language: str = "eng"
    engine: str = "tesseract"

    @property
    def normalized_confidence(self) -> float:
        """Get confidence normalized to 0-1 range."""
        return self.confidence / 100.0

    def get_lines(self) -> list[str]:
        """Get text split into lines."""
        return [line.strip() for line in self.text.split("\n") if line.strip()]

    def get_words(self) -> list[TextBlock]:
        """Get word-level blocks."""
        return [b for b in self.blocks if b.level == 5]


class TesseractEngine:
    """Tesseract OCR engine for high-quality printed documents.

    This engine is optimized for clean, printed election result sheets.
    It provides text extraction with confidence scores and basic table
    detection capabilities.

    Requirements: 3.1
    """

    # Page segmentation modes
    PSM_AUTO = 3  # Fully automatic page segmentation
    PSM_SINGLE_BLOCK = 6  # Assume a single uniform block of text
    PSM_SINGLE_LINE = 7  # Treat the image as a single text line
    PSM_SPARSE_TEXT = 11  # Sparse text with OSD
    PSM_SPARSE_TEXT_OSD = 12  # Sparse text with OSD

    def __init__(
        self,
        lang: str = "eng",
        config: str = "--psm 6",
        tesseract_cmd: str | None = None,
    ):
        """Initialize Tesseract OCR engine.

        Args:
            lang: Tesseract language code (e.g., 'eng', 'eng+fra')
            config: Tesseract configuration options
            tesseract_cmd: Path to tesseract executable (optional)

        Raises:
            RuntimeError: If Tesseract is not available
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError(
                "pytesseract is not installed. "
                "Install with: pip install pytesseract"
            )

        self.lang = lang
        self.config = config

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract_text(self, image: np.ndarray | str | Path) -> OCRResult:
        """Extract text from image using Tesseract.

        Args:
            image: Image as numpy array or path to image file

        Returns:
            OCRResult with extracted text and confidence scores
        """
        # Load image if path provided
        if isinstance(image, (str, Path)):
            import cv2
            image = cv2.imread(str(image))
            if image is None:
                raise ValueError(f"Failed to load image: {image}")

        # Get detailed OCR data
        data = pytesseract.image_to_data(
            image,
            lang=self.lang,
            config=self.config,
            output_type=Output.DICT,
        )

        # Parse Tesseract output
        blocks = self._parse_tesseract_output(data)

        # Get full text
        full_text = pytesseract.image_to_string(
            image,
            lang=self.lang,
            config=self.config,
        )

        # Calculate average confidence (excluding -1 values)
        confidences = [b.confidence for b in blocks if b.confidence >= 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return OCRResult(
            text=full_text.strip(),
            blocks=blocks,
            confidence=avg_confidence,
            language=self.lang,
            engine="tesseract",
        )

    def extract_text_with_boxes(
        self,
        image: np.ndarray | str | Path,
    ) -> OCRResult:
        """Extract text with bounding box information.

        Args:
            image: Image as numpy array or path to image file

        Returns:
            OCRResult with text blocks including position data
        """
        return self.extract_text(image)

    def extract_tables(
        self,
        image: np.ndarray | str | Path,
        min_rows: int = 2,
        min_cols: int = 2,
    ) -> list[Table]:
        """Extract tabular data from result sheets.

        Uses line detection and text positioning to identify
        table structures in the image.

        Args:
            image: Image as numpy array or path to image file
            min_rows: Minimum rows to consider as table
            min_cols: Minimum columns to consider as table

        Returns:
            List of extracted tables
        """
        import cv2

        # Load image if path provided
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))
            if image is None:
                raise ValueError(f"Failed to load image: {image}")

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Detect horizontal and vertical lines
        horizontal_lines = self._detect_lines(gray, horizontal=True)
        vertical_lines = self._detect_lines(gray, horizontal=False)

        # Find table regions from line intersections
        tables = self._find_table_regions(
            gray, horizontal_lines, vertical_lines, min_rows, min_cols
        )

        # Extract text for each table cell
        for table in tables:
            self._extract_table_text(image, table)

        return tables

    def _parse_tesseract_output(self, data: dict) -> list[TextBlock]:
        """Parse Tesseract output dictionary into TextBlock objects.

        Args:
            data: Tesseract output dictionary

        Returns:
            List of TextBlock objects
        """
        blocks = []
        n_boxes = len(data["text"])

        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = float(data["conf"][i])

            # Skip empty text or very low confidence
            if not text or conf < 0:
                continue

            block = TextBlock(
                text=text,
                confidence=conf,
                x=int(data["left"][i]),
                y=int(data["top"][i]),
                width=int(data["width"][i]),
                height=int(data["height"][i]),
                level=int(data["level"][i]),
                block_num=int(data["block_num"][i]),
                line_num=int(data["line_num"][i]),
                word_num=int(data["word_num"][i]),
            )
            blocks.append(block)

        return blocks

    def _detect_lines(
        self,
        gray: np.ndarray,
        horizontal: bool = True,
        min_length: int = 100,
    ) -> list[tuple]:
        """Detect horizontal or vertical lines in image.

        Args:
            gray: Grayscale image
            horizontal: True for horizontal lines, False for vertical
            min_length: Minimum line length to detect

        Returns:
            List of line coordinates (x1, y1, x2, y2)
        """
        import cv2

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=100,
            minLineLength=min_length,
            maxLineGap=10,
        )

        if lines is None:
            return []

        result = []
        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Check if line is horizontal or vertical
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))

            if horizontal and angle < 10:  # Near horizontal
                result.append((x1, y1, x2, y2))
            elif not horizontal and (angle > 80 or angle < -80):  # Near vertical
                result.append((x1, y1, x2, y2))

        return result

    def _find_table_regions(
        self,
        gray: np.ndarray,
        horizontal_lines: list[tuple],
        vertical_lines: list[tuple],
        min_rows: int,
        min_cols: int,
    ) -> list[Table]:
        """Find table regions from detected lines.

        Args:
            gray: Grayscale image
            horizontal_lines: List of horizontal line coordinates
            vertical_lines: List of vertical line coordinates
            min_rows: Minimum rows for valid table
            min_cols: Minimum columns for valid table

        Returns:
            List of Table objects with cell positions
        """
        if len(horizontal_lines) < min_rows + 1 or len(vertical_lines) < min_cols + 1:
            return []

        # Sort lines by position
        h_lines = sorted(set(
            (line[1] + line[3]) // 2 for line in horizontal_lines
        ))
        v_lines = sorted(set(
            (line[0] + line[2]) // 2 for line in vertical_lines
        ))

        # Filter lines that are too close together
        h_lines = self._filter_close_lines(h_lines, min_gap=20)
        v_lines = self._filter_close_lines(v_lines, min_gap=30)

        if len(h_lines) < min_rows + 1 or len(v_lines) < min_cols + 1:
            return []

        # Create table from grid
        rows = len(h_lines) - 1
        cols = len(v_lines) - 1

        cells = []
        for r in range(rows):
            for c in range(cols):
                cell = TableCell(
                    text="",
                    row=r,
                    col=c,
                    x=v_lines[c],
                    y=h_lines[r],
                    width=v_lines[c + 1] - v_lines[c],
                    height=h_lines[r + 1] - h_lines[r],
                )
                cells.append(cell)

        table = Table(
            cells=cells,
            rows=rows,
            cols=cols,
            x=v_lines[0],
            y=h_lines[0],
            width=v_lines[-1] - v_lines[0],
            height=h_lines[-1] - h_lines[0],
        )

        return [table]

    def _filter_close_lines(
        self,
        lines: list[int],
        min_gap: int = 20,
    ) -> list[int]:
        """Filter out lines that are too close together.

        Args:
            lines: Sorted list of line positions
            min_gap: Minimum gap between lines

        Returns:
            Filtered list of line positions
        """
        if not lines:
            return []

        filtered = [lines[0]]
        for line in lines[1:]:
            if line - filtered[-1] >= min_gap:
                filtered.append(line)

        return filtered

    def _extract_table_text(
        self,
        image: np.ndarray,
        table: Table,
    ) -> None:
        """Extract text for each cell in a table.

        Args:
            image: Source image
            table: Table object with cell positions
        """
        for cell in table.cells:
            # Extract cell region
            x1 = max(0, cell.x)
            y1 = max(0, cell.y)
            x2 = min(image.shape[1], cell.x + cell.width)
            y2 = min(image.shape[0], cell.y + cell.height)

            if x2 <= x1 or y2 <= y1:
                continue

            cell_image = image[y1:y2, x1:x2]

            # Extract text from cell
            try:
                text = pytesseract.image_to_string(
                    cell_image,
                    lang=self.lang,
                    config="--psm 7",  # Single line mode for cells
                ).strip()

                # Get confidence
                data = pytesseract.image_to_data(
                    cell_image,
                    lang=self.lang,
                    config="--psm 7",
                    output_type=Output.DICT,
                )

                confidences = [
                    float(c) for c in data["conf"] if float(c) >= 0
                ]

                cell.text = text
                cell.confidence = (
                    sum(confidences) / len(confidences) if confidences else 0.0
                )
            except Exception:
                cell.text = ""
                cell.confidence = 0.0

    def get_supported_languages(self) -> list[str]:
        """Get list of supported Tesseract languages.

        Returns:
            List of language codes
        """
        try:
            langs = pytesseract.get_languages()
            return langs
        except Exception:
            return ["eng"]

    def is_available(self) -> bool:
        """Check if Tesseract is available and working.

        Returns:
            True if Tesseract is available
        """
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
