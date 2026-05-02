#!/usr/bin/env python3
"""Demo script to process INEC result images with Tesseract OCR.

This script:
1. Uses existing sample result sheet images
2. Processes each image with Tesseract OCR
3. Extracts and parses election data
4. Displays the extracted results
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Warning: pytesseract or PIL not available")


@dataclass
class PartyVoteResult:
    """Vote result for a single political party."""
    name: str
    code: str
    votes: int
    confidence: float = 1.0


@dataclass
class ExtractionResult:
    """Result of OCR data extraction."""
    parties: list[PartyVoteResult] = field(default_factory=list)
    accredited_voters: int = 0
    valid_votes: int = 0
    rejected_votes: int = 0
    confidence: float = 0.0
    raw_text: str = ""

    @property
    def total_party_votes(self) -> int:
        return sum(p.votes for p in self.parties)

    @property
    def is_valid(self) -> bool:
        return len(self.parties) > 0 and self.confidence >= 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "parties": [
                {"name": p.name, "code": p.code, "votes": p.votes, "confidence": p.confidence}
                for p in self.parties
            ],
            "accredited_voters": self.accredited_voters,
            "valid_votes": self.valid_votes,
            "rejected_votes": self.rejected_votes,
            "confidence": self.confidence,
        }


class TesseractOCREngine:
    """Tesseract OCR engine for election result extraction."""

    # Nigerian political parties - patterns handle OCR artifacts
    PARTY_PATTERNS = {
        'APC': r'(?:All\s*Progressives?\s*Congress|APC|Congres.?BC|Progressive.*Congress)',
        'PDP': r'(?:Peoples?\s*Democratic\s*Party|PDP|Paf.?DP|Democratic.*Party)',
        'LP': r'(?:Labour\s*Party|LP\b)',
        'NNPP': r'(?:New\s*Nigeria\s*Peoples?\s*Party|NNPP|Paity.?PP|Nigeria.*Peoples)',
        'APGA': r'(?:All\s*Progressives?\s*Grand\s*Alliance|APGA)',
        'ADC': r'(?:African\s*Democratic\s*Congress|ADC)',
        'SDP': r'(?:Social\s*Democratic\s*Party|SDP)',
        'YPP': r'(?:Young\s*Progressives?\s*Party|YPP)',
    }

    def __init__(self, lang: str = "eng", config: str = "--psm 6"):
        self.lang = lang
        self.config = config

    def extract(self, image_path: Path) -> ExtractionResult:
        """Extract election data from image using Tesseract."""
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract not available")

        # Load and preprocess image
        image = Image.open(image_path)

        # Run OCR
        raw_text = pytesseract.image_to_string(image, lang=self.lang, config=self.config)

        # Parse the extracted text
        result = self._parse_text(raw_text)
        result.raw_text = raw_text

        return result

    def _parse_text(self, text: str) -> ExtractionResult:
        """Parse OCR text to extract election data."""
        result = ExtractionResult()
        lines = text.split('\n')

        # Extract party votes
        for line in lines:
            for code, pattern in self.PARTY_PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    # Try to find vote count in the same line
                    numbers = re.findall(r'\b(\d{1,6})\b', line)
                    if numbers:
                        votes = int(numbers[-1])  # Take last number as votes
                        party_name = self._get_party_name(code)
                        result.parties.append(PartyVoteResult(
                            name=party_name,
                            code=code,
                            votes=votes,
                            confidence=0.8
                        ))
                    break

        # Extract totals
        for line in lines:
            line_lower = line.lower()
            numbers = re.findall(r'\b(\d{1,6})\b', line)

            if 'accredited' in line_lower and numbers:
                result.accredited_voters = int(numbers[-1])
            elif 'valid' in line_lower and 'vote' in line_lower and numbers:
                result.valid_votes = int(numbers[-1])
            elif 'rejected' in line_lower and numbers:
                result.rejected_votes = int(numbers[-1])

        # Calculate confidence
        if result.parties:
            result.confidence = 0.7 if len(result.parties) >= 3 else 0.5

        return result

    def _get_party_name(self, code: str) -> str:
        """Get full party name from code."""
        names = {
            'APC': 'All Progressives Congress',
            'PDP': 'Peoples Democratic Party',
            'LP': 'Labour Party',
            'NNPP': 'New Nigeria Peoples Party',
            'APGA': 'All Progressives Grand Alliance',
            'ADC': 'African Democratic Congress',
            'SDP': 'Social Democratic Party',
            'YPP': 'Young Progressives Party',
        }
        return names.get(code, code)


def print_result(image_path: Path, result: ExtractionResult):
    """Pretty print extraction result."""
    print("\n" + "="*60)
    print(f"📄 Image: {image_path.name}")
    print("="*60)

    if not result.is_valid:
        print("⚠️  Low confidence extraction")

    print(f"✅ Confidence: {result.confidence:.2%}")
    print("\n📊 Party Results:")
    print("-"*40)

    for party in sorted(result.parties, key=lambda p: p.votes, reverse=True):
        print(f"   {party.code:6} ({party.name[:25]:25}): {party.votes:,} votes")

    print("-"*40)
    print(f"   Total Party Votes: {result.total_party_votes:,}")
    print("\n📈 Summary:")
    print(f"   Accredited Voters: {result.accredited_voters:,}")
    print(f"   Valid Votes:       {result.valid_votes:,}")
    print(f"   Rejected Votes:    {result.rejected_votes:,}")

    # Show raw OCR text (truncated)
    if result.raw_text:
        print("\n📝 Raw OCR Text (first 500 chars):")
        print("-"*40)
        print(result.raw_text[:500])


def main():
    """Main demo function."""
    print("🇳🇬 INEC Election Results - Tesseract OCR Demo")
    print("="*60)

    # Check for Tesseract
    if not TESSERACT_AVAILABLE:
        print("❌ Error: pytesseract or PIL not installed")
        print("   Install with: pip install pytesseract pillow")
        return

    # Check if tesseract binary is available
    try:
        pytesseract.get_tesseract_version()
        print("✅ Tesseract OCR is available")
    except Exception as e:
        print(f"❌ Tesseract binary not found: {e}")
        print("   Install with: brew install tesseract")
        print("\n   Falling back to simulated OCR for demo...")
        run_simulated_demo()
        return

    # Find sample images
    demo_dir = Path("./data/result_sheets/demo")
    if not demo_dir.exists():
        print(f"❌ Demo directory not found: {demo_dir}")
        print("   Run demo_ocr.py first to create sample images")
        return

    images = list(demo_dir.glob("*.png"))
    if not images:
        print("❌ No sample images found")
        return

    print(f"\n🔍 Processing {len(images)} images with Tesseract OCR...")

    # Initialize engine
    engine = TesseractOCREngine()

    # Process each image
    all_results = []
    for image_path in images:
        try:
            print(f"\n⏳ Processing: {image_path.name}...")
            result = engine.extract(image_path)
            print_result(image_path, result)
            all_results.append({
                "image": str(image_path),
                "result": result.to_dict()
            })
        except Exception as e:
            print(f"❌ Error processing {image_path.name}: {e}")

    # Save results
    results_file = demo_dir / "tesseract_ocr_results.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n💾 Results saved to: {results_file}")

    # Summary
    print("\n" + "="*60)
    print("📊 DEMO SUMMARY")
    print("="*60)
    print(f"   Images processed: {len(all_results)}")
    successful = sum(1 for r in all_results if r["result"]["confidence"] > 0.5)
    print(f"   Successful extractions: {successful}")


def run_simulated_demo():
    """Run a simulated demo when Tesseract is not available."""
    print("\n🔄 Running simulated OCR demo...")

    # Simulated results based on the sample images we created
    simulated_results = [
        {
            "image": "sample_result_1.png",
            "polling_unit": "LAGOS/IKEJA/WARD 01/PU 001",
            "parties": [
                {"name": "Labour Party", "code": "LP", "votes": 312},
                {"name": "All Progressives Congress", "code": "APC", "votes": 245},
                {"name": "Peoples Democratic Party", "code": "PDP", "votes": 198},
                {"name": "New Nigeria Peoples Party", "code": "NNPP", "votes": 45},
            ],
            "accredited_voters": 850,
            "valid_votes": 800,
            "rejected_votes": 12,
        },
        {
            "image": "sample_result_2.png",
            "polling_unit": "LAGOS/IKEJA/WARD 01/PU 002",
            "parties": [
                {"name": "Peoples Democratic Party", "code": "PDP", "votes": 267},
                {"name": "Labour Party", "code": "LP", "votes": 198},
                {"name": "All Progressives Congress", "code": "APC", "votes": 189},
                {"name": "New Nigeria Peoples Party", "code": "NNPP", "votes": 32},
            ],
            "accredited_voters": 720,
            "valid_votes": 686,
            "rejected_votes": 8,
        },
        {
            "image": "sample_result_3.png",
            "polling_unit": "LAGOS/SURULERE/WARD 03/PU 005",
            "parties": [
                {"name": "Peoples Democratic Party", "code": "PDP", "votes": 423},
                {"name": "Labour Party", "code": "LP", "votes": 287},
                {"name": "All Progressives Congress", "code": "APC", "votes": 156},
                {"name": "New Nigeria Peoples Party", "code": "NNPP", "votes": 21},
            ],
            "accredited_voters": 920,
            "valid_votes": 887,
            "rejected_votes": 15,
        },
        {
            "image": "sample_result_4.png",
            "polling_unit": "LAGOS/ETI-OSA/WARD 02/PU 003",
            "parties": [
                {"name": "Labour Party", "code": "LP", "votes": 456},
                {"name": "All Progressives Congress", "code": "APC", "votes": 378},
                {"name": "Peoples Democratic Party", "code": "PDP", "votes": 145},
                {"name": "New Nigeria Peoples Party", "code": "NNPP", "votes": 67},
            ],
            "accredited_voters": 1100,
            "valid_votes": 1046,
            "rejected_votes": 22,
        },
    ]

    print(f"\n🔍 Processing {len(simulated_results)} sample results...")

    for data in simulated_results:
        print("\n" + "="*60)
        print(f"📄 Image: {data['image']}")
        print(f"📍 Polling Unit: {data['polling_unit']}")
        print("="*60)
        print("✅ Confidence: 95%")
        print("\n📊 Party Results:")
        print("-"*40)

        total_votes = 0
        for party in sorted(data['parties'], key=lambda p: p['votes'], reverse=True):
            print(f"   {party['code']:6} ({party['name'][:25]:25}): {party['votes']:,} votes")
            total_votes += party['votes']

        print("-"*40)
        print(f"   Total Party Votes: {total_votes:,}")
        print("\n📈 Summary:")
        print(f"   Accredited Voters: {data['accredited_voters']:,}")
        print(f"   Valid Votes:       {data['valid_votes']:,}")
        print(f"   Rejected Votes:    {data['rejected_votes']:,}")

    # Save results
    demo_dir = Path("./data/result_sheets/demo")
    demo_dir.mkdir(parents=True, exist_ok=True)
    results_file = demo_dir / "simulated_ocr_results.json"
    with open(results_file, "w") as f:
        json.dump(simulated_results, f, indent=2)

    print("\n" + "="*60)
    print("📊 DEMO SUMMARY")
    print("="*60)
    print(f"   Images processed: {len(simulated_results)}")
    print(f"   Successful extractions: {len(simulated_results)}")
    print(f"   Results saved to: {results_file}")

    # Aggregate totals
    total_apc = sum(next((p['votes'] for p in r['parties'] if p['code'] == 'APC'), 0) for r in simulated_results)
    total_pdp = sum(next((p['votes'] for p in r['parties'] if p['code'] == 'PDP'), 0) for r in simulated_results)
    total_lp = sum(next((p['votes'] for p in r['parties'] if p['code'] == 'LP'), 0) for r in simulated_results)
    total_nnpp = sum(next((p['votes'] for p in r['parties'] if p['code'] == 'NNPP'), 0) for r in simulated_results)

    print("\n📊 AGGREGATED RESULTS (4 Polling Units)")
    print("="*60)
    print(f"   LP:   {total_lp:,} votes")
    print(f"   PDP:  {total_pdp:,} votes")
    print(f"   APC:  {total_apc:,} votes")
    print(f"   NNPP: {total_nnpp:,} votes")
    print(f"   TOTAL: {total_apc + total_pdp + total_lp + total_nnpp:,} votes")


if __name__ == "__main__":
    main()
