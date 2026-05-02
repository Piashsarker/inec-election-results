---
inclusion: fileMatch
fileMatchPattern: "backend/app/core/ocr/**,backend/app/core/extractor/**,backend/app/agents/**"
---

# Machine Learning & OCR Layer

## Architecture
- **OCR Engines**: Tesseract (local) + OpenAI Vision API (cloud fallback)
- **Image Processing**: OpenCV (cv2) + Pillow
- **AI Agent**: LangGraph state machine with LangChain
- **Extraction**: Structured data parsing from OCR text

## Project Structure
```
backend/app/
├── core/
│   ├── ocr/
│   │   ├── engine.py           # OCR engine selector (quality-based routing)
│   │   ├── preprocessing.py    # Image preprocessing (deskew, denoise, threshold)
│   │   ├── tesseract.py        # Tesseract OCR wrapper
│   │   └── vision.py           # OpenAI Vision API wrapper
│   └── extractor/
│       ├── parser.py           # Structured data extraction from OCR text
│       └── validator.py        # Result validation (vote totals, ranges)
├── agents/
│   ├── graph.py                # LangGraph state machine definition
│   ├── orchestrator.py         # Main orchestrator agent
│   ├── navigator.py            # INEC portal navigation agent
│   ├── processor.py            # Image processing agent
│   ├── validator.py            # Result validation agent
│   └── pool.py                 # Agent pool management
```

## OCR Pipeline
1. **Preprocessing** (`preprocessing.py`):
   - Grayscale conversion
   - Noise reduction (Gaussian blur, bilateral filter)
   - Deskewing (Hough transform)
   - Adaptive thresholding (Otsu's method)
   - Border removal and cropping

2. **Engine Selection** (`engine.py`):
   - Quality assessment of preprocessed image
   - If quality > threshold → Tesseract (fast, free)
   - If quality < threshold → OpenAI Vision (accurate, paid)
   - Fallback chain: Tesseract → Vision → manual flag

3. **Tesseract** (`tesseract.py`):
   - Config: `--psm 6` (uniform block of text)
   - Language: English
   - Returns: `OCRResult` with text + confidence

4. **OpenAI Vision** (`vision.py`):
   - Model: gpt-4-vision-preview
   - Structured prompt for election result extraction
   - Returns: parsed JSON with party results

## Data Extraction (extractor/)
- `parser.py`: Regex-based extraction of party names, codes, vote counts
- `validator.py`: Validates extracted data:
  - Vote counts are non-negative integers
  - Total votes ≤ accredited voters
  - Party percentages sum to ~100%
  - Confidence scoring based on extraction quality

## LangGraph Agent System (agents/)
- **State**: `AgentState` TypedDict with messages, results, status
- **Graph**: StateGraph with nodes for each agent role
- **Orchestrator**: Coordinates the full pipeline
- **Navigator**: Handles INEC portal page navigation
- **Processor**: Manages OCR + extraction
- **Validator**: Cross-checks results for anomalies

## Key Data Types
```python
@dataclass
class OCRResult:
    text: str
    confidence: float
    engine: str  # "tesseract" or "vision"

@dataclass  
class ExtractionResult:
    party_results: list[dict]  # {party_name, party_code, vote_count}
    accredited_voters: int
    valid_votes: int
    rejected_votes: int
    confidence_score: float
```

## Configuration
- `OCR_QUALITY_THRESHOLD` (0.7) - Route to Vision below this
- `OCR_CONFIDENCE_THRESHOLD` (0.8) - Flag results below this
- `OPENAI_API_KEY` - Required for Vision API
- `OPENAI_MODEL` - Default: gpt-4-vision-preview

## Dependencies
- pytesseract, Pillow, opencv-python-headless
- openai, langgraph, langchain, langchain-openai
