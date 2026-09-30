"""Extract Osun Governorship 2026 election results from downloaded result sheets.

Uses GPT-4 Vision to OCR and extract structured data from the IPETUMODU II ward.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.core.ocr.vision import GPT4VisionEngine


async def main():
    """Process all downloaded result sheets and extract election data."""
    image_dir = Path(__file__).parent / "data" / "result_sheets" / "osun_governorship_2026"

    if not image_dir.exists():
        print(f"ERROR: Image directory not found: {image_dir}")
        return

    images = sorted(image_dir.glob("*.jpg"))
    print(f"Found {len(images)} result sheet images to process")
    print("=" * 80)

    # Initialize GPT-4 Vision engine
    engine = GPT4VisionEngine(model="gpt-4o", temperature=0.0)

    all_results = []

    for i, image_path in enumerate(images, 1):
        pu_name = image_path.stem.replace("_", " ")
        print(f"\n[{i}/{len(images)}] Processing: {image_path.name}")
        print(f"  Polling Unit: {pu_name}")

        try:
            result = await engine.extract_async(str(image_path), verify=False)

            if result.is_valid:
                print(f"  ✅ Confidence: {result.confidence:.0%}")
                print(f"  Accredited Voters: {result.accredited_voters}")
                print(f"  Valid Votes: {result.valid_votes}")
                print(f"  Rejected Votes: {result.rejected_votes}")
                print(f"  Parties:")
                for party in result.parties:
                    if party.votes > 0:
                        print(f"    {party.code}: {party.votes}")

                all_results.append({
                    "polling_unit": image_path.stem,
                    "file": image_path.name,
                    **result.to_dict(),
                })
            else:
                print(f"  ⚠️  Low confidence extraction (confidence: {result.confidence:.0%})")
                all_results.append({
                    "polling_unit": image_path.stem,
                    "file": image_path.name,
                    "error": "low_confidence",
                    **result.to_dict(),
                })

        except Exception as e:
            print(f"  ❌ Error: {e}")
            all_results.append({
                "polling_unit": image_path.stem,
                "file": image_path.name,
                "error": str(e),
            })

    # Print summary
    print("\n" + "=" * 80)
    print("WARD SUMMARY: IPETUMODU II - Osun Governorship 2026-08-15")
    print("=" * 80)

    # Aggregate results across all PUs
    party_totals: dict[str, int] = {}
    total_accredited = 0
    total_valid = 0
    total_rejected = 0
    successful = 0

    for r in all_results:
        if "error" not in r or r.get("confidence", 0) >= 0.5:
            successful += 1
            total_accredited += r.get("accredited_voters", 0)
            total_valid += r.get("valid_votes", 0)
            total_rejected += r.get("rejected_votes", 0)
            for party in r.get("parties", []):
                code = party["code"]
                party_totals[code] = party_totals.get(code, 0) + party["votes"]

    print(f"\nProcessed: {successful}/{len(images)} polling units")
    print(f"Total Accredited Voters: {total_accredited:,}")
    print(f"Total Valid Votes: {total_valid:,}")
    print(f"Total Rejected Votes: {total_rejected:,}")
    print(f"\nParty Results (Ward Total):")
    print("-" * 40)

    # Sort parties by votes descending
    for code, votes in sorted(party_totals.items(), key=lambda x: x[1], reverse=True):
        print(f"  {code:10s}: {votes:>6,}")

    # Save full results to JSON
    output_path = image_dir / "results.json"
    with open(output_path, "w") as f:
        json.dump({
            "election": "Governorship",
            "date": "2026-08-15",
            "state": "OSUN",
            "lga": "IFE NORTH",
            "ward": "IPETUMODU II",
            "ward_code": "29/15/07",
            "polling_units_processed": successful,
            "polling_units_total": len(images),
            "total_accredited_voters": total_accredited,
            "total_valid_votes": total_valid,
            "total_rejected_votes": total_rejected,
            "party_totals": party_totals,
            "results": all_results,
        }, f, indent=2)

    print(f"\nFull results saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
