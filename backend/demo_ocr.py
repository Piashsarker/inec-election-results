#!/usr/bin/env python3
"""Demo script to download INEC result images and process with GPT-4 Vision OCR.

This script:
1. Downloads 4-5 sample result sheet images from INEC IREV portal
2. Processes each image with GPT-4 Vision OCR
3. Displays the extracted election results
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables from .env file in current directory
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)
print(f"Loading .env from: {env_path}")

from app.core.ocr.vision import ExtractionResult, GPT4VisionEngine

# Sample INEC result sheet URLs (publicly accessible images from IREV portal)
# These are direct image URLs from the INEC IREV system
SAMPLE_RESULT_URLS = [
    # Presidential 2023 - Lagos samples
    "https://inecelectionresults.ng/elections/63f8f25b594e164f8146a213/context/ward/state/25/lga/506/ward/5556/pu/89442",
    "https://inecelectionresults.ng/elections/63f8f25b594e164f8146a213/context/ward/state/25/lga/506/ward/5556/pu/89443",
]

# Alternative: Use direct image URLs if available
# For demo, we'll use placeholder images or download from IREV


async def download_sample_images(output_dir: Path, limit: int = 4) -> list[Path]:
    """Download sample result sheet images for demo.

    Since INEC IREV requires browser navigation, we'll create sample images
    or use publicly available election result images.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []

    # For demo purposes, let's check if we have any existing images
    existing_images = list(output_dir.glob("*.png")) + list(output_dir.glob("*.jpg"))
    if existing_images:
        print(f"Found {len(existing_images)} existing images in {output_dir}")
        return existing_images[:limit]

    print("No existing images found. Creating sample test images...")

    # Create sample test images with election data for OCR testing
    # In production, these would be downloaded from INEC IREV portal

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available. Please add sample images to ./data/result_sheets/")
        return []

    # Create sample election result images
    sample_data = [
        {
            "pu": "LAGOS/IKEJA/WARD 01/PU 001",
            "parties": [("APC", 245), ("PDP", 198), ("LP", 312), ("NNPP", 45)],
            "accredited": 850,
            "valid": 800,
            "rejected": 12,
        },
        {
            "pu": "LAGOS/IKEJA/WARD 01/PU 002",
            "parties": [("APC", 189), ("PDP", 267), ("LP", 198), ("NNPP", 32)],
            "accredited": 720,
            "valid": 686,
            "rejected": 8,
        },
        {
            "pu": "LAGOS/SURULERE/WARD 03/PU 005",
            "parties": [("APC", 156), ("PDP", 423), ("LP", 287), ("NNPP", 21)],
            "accredited": 920,
            "valid": 887,
            "rejected": 15,
        },
        {
            "pu": "LAGOS/ETI-OSA/WARD 02/PU 003",
            "parties": [("APC", 378), ("PDP", 145), ("LP", 456), ("NNPP", 67)],
            "accredited": 1100,
            "valid": 1046,
            "rejected": 22,
        },
    ]

    for i, data in enumerate(sample_data[:limit]):
        img_path = output_dir / f"sample_result_{i+1}.png"
        create_sample_result_image(img_path, data)
        downloaded.append(img_path)
        print(f"Created sample image: {img_path}")

    return downloaded


def create_sample_result_image(path: Path, data: dict):
    """Create a sample election result sheet image for testing."""
    from PIL import Image, ImageDraw, ImageFont

    # Create larger image to avoid text overlap
    width, height = 900, 650
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Try to use a font, fall back to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        bold_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except Exception:
        font = ImageFont.load_default()
        title_font = font
        bold_font = font

    # Column positions with proper spacing
    col1_x = 30      # Party name
    col2_x = 320     # Party code
    col3_x = 500     # Votes

    # Draw header
    draw.rectangle([0, 0, width, 80], fill='#006400')
    draw.text((20, 15), "INDEPENDENT NATIONAL ELECTORAL COMMISSION", fill='white', font=title_font)
    draw.text((20, 45), "FORM EC8A - STATEMENT OF RESULT OF POLL", fill='white', font=font)

    # Draw polling unit info
    y = 100
    draw.text((30, y), f"Polling Unit: {data['pu']}", fill='black', font=font)
    y += 30
    draw.text((30, y), "Election: Presidential Election 2023", fill='black', font=font)
    y += 50

    # Draw table header with proper column spacing
    draw.rectangle([20, y, width-20, y+35], fill='#E0E0E0')
    draw.text((col1_x, y+8), "PARTY", fill='black', font=bold_font)
    draw.text((col2_x, y+8), "PARTY CODE", fill='black', font=bold_font)
    draw.text((col3_x, y+8), "VOTES IN FIGURES", fill='black', font=bold_font)
    y += 35

    # Draw party results with proper spacing
    party_names = {
        'APC': 'All Progressives Congress',
        'PDP': 'Peoples Democratic Party',
        'LP': 'Labour Party',
        'NNPP': 'New Nigeria Peoples Party',
    }

    for party_code, votes in data['parties']:
        draw.line([(20, y), (width-20, y)], fill='#CCCCCC')
        draw.text((col1_x, y+8), party_names.get(party_code, party_code), fill='black', font=font)
        draw.text((col2_x, y+8), party_code, fill='black', font=font)
        draw.text((col3_x, y+8), str(votes), fill='black', font=font)
        y += 35

    # Draw bottom line of table
    draw.line([(20, y), (width-20, y)], fill='#CCCCCC')

    # Draw totals section
    y += 30
    draw.line([(20, y), (width-20, y)], fill='black', width=2)
    y += 15
    draw.text((30, y), f"Total Accredited Voters: {data['accredited']}", fill='black', font=font)
    y += 28
    draw.text((30, y), f"Total Valid Votes: {data['valid']}", fill='black', font=font)
    y += 28
    draw.text((30, y), f"Total Rejected Votes: {data['rejected']}", fill='black', font=font)

    # Save image
    img.save(path)


async def process_with_gpt4_vision(image_path: Path, api_key: str) -> ExtractionResult:
    """Process a single image with GPT-4 Vision OCR."""
    engine = GPT4VisionEngine(api_key=api_key, model="gpt-4o")
    result = await engine.extract_async(image_path, verify=False)
    return result


def print_result(image_path: Path, result: ExtractionResult):
    """Pretty print extraction result."""
    print("\n" + "="*60)
    print(f"📄 Image: {image_path.name}")
    print("="*60)

    if not result.is_valid:
        print("❌ Extraction failed or low confidence")
        print(f"   Confidence: {result.confidence:.2%}")
        return

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


async def main():
    """Main demo function."""
    print("🇳🇬 INEC Election Results OCR Demo")
    print("="*60)

    # Check for API key - try environment first, then hardcoded for demo
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.strip() == "":
        # Fallback to hardcoded key for demo
        api_key = ""

    if not api_key:
        print("❌ Error: OPENAI_API_KEY not set in environment")
        print("   Please set it in backend/.env file")
        return

    print("✅ OpenAI API key found")

    # Setup output directory
    output_dir = Path("./data/result_sheets/demo")

    # Download/create sample images
    print("\n📥 Preparing sample images...")
    images = await download_sample_images(output_dir, limit=4)

    if not images:
        print("❌ No images available for processing")
        return

    print(f"\n🔍 Processing {len(images)} images with GPT-4 Vision OCR...")

    # Process each image
    all_results = []
    for image_path in images:
        try:
            print(f"\n⏳ Processing: {image_path.name}...")
            result = await process_with_gpt4_vision(image_path, api_key)
            print_result(image_path, result)
            all_results.append({
                "image": str(image_path),
                "result": result.to_dict()
            })
        except Exception as e:
            print(f"❌ Error processing {image_path.name}: {e}")

    # Save results to JSON
    results_file = output_dir / "ocr_results.json"
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
    print(f"   Results saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())
