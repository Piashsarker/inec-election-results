"""Extract Osun Governorship 2026 election results using Tesseract OCR (free/local).

Uses the project's TesseractEngine + ElectionDataExtractor to process
all downloaded result sheet images from IPETUMODU II ward.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.ocr.tesseract import TesseractEngine
from app.core.extractor.parser import ElectionDataExtractor


def main() -> None:
    """Process all downloaded result sheets with Tesseract OCR."""
    image_dir = Path(__file__).parent / "data" / "result_sheets" / "osun_governorship_2026"

    if not image_dir.exists():
        print(f"ERROR: Image directory not found: {image_dir}")
        return

    images = sorted(image_dir.glob("*.jpg"))
    print(f"Found {len(images)} result sheet images to process")
    print("=" * 80)

    # Initialize engines
    ocr_engine = TesseractEngine(lang="eng", config="--psm 6")
    extractor = ElectionDataExtractor(min_confidence=0.3, fuzzy_match=True)

    all_results: list[dict] = []

    for i, image_path in enumerate(images, 1):
        pu_code = "_".join(image_path.stem.split("_")[:4])
        pu_name = " ".join(image_path.stem.split("_")[4:])
        print(f"\n[{i}/{len(images)}] Processing: {image_path.name}")
        print(f"  PU Code: {pu_code.replace('_', '/')}")
        print(f"  PU Name: {pu_name}")

        try:
            # Step 1: Run OCR
            ocr_result = ocr_engine.extract_text(str(image_path))
            print(f"  OCR Confidence: {ocr_result.confidence:.1f}%")

            # Step 2: Extract structured data
            extraction = extractor.extract(ocr_result)

            if extraction.party_votes:
                print(f"  Extraction Confidence: {extraction.confidence:.0%}")
                print(f"  Accredited Voters: {extraction.summary.accredited_voters}")
                print(f"  Valid Votes: {extraction.summary.valid_votes}")
                print(f"  Rejected Votes: {extraction.summary.rejected_votes}")
                print(f"  Parties found: {len(extraction.party_votes)}")
                for pv in extraction.party_votes:
                    if pv.votes > 0:
                        print(f"    {pv.party_code:10s}: {pv.votes:>5}")

                if extraction.warnings:
                    for w in extraction.warnings:
                        print(f"  ⚠️  {w}")

                all_results.append({
                    "polling_unit_code": pu_code.replace("_", "/"),
                    "polling_unit_name": pu_name,
                    "file": image_path.name,
                    "ocr_confidence": round(ocr_result.confidence, 1),
                    "extraction_confidence": round(extraction.confidence, 3),
                    "accredited_voters": extraction.summary.accredited_voters,
                    "valid_votes": extraction.summary.valid_votes,
                    "rejected_votes": extraction.summary.rejected_votes,
                    "parties": [
                        {
                            "code": pv.party_code,
                            "name": pv.party_name,
                            "votes": pv.votes,
                        }
                        for pv in extraction.party_votes
                    ],
                    "warnings": extraction.warnings,
                    "ward_name": extraction.ward_name,
                    "lga_name": extraction.lga_name,
                    "state_name": extraction.state_name,
                })
            else:
                print("  ⚠️  No party votes extracted")
                # Store raw text for debugging
                all_results.append({
                    "polling_unit_code": pu_code.replace("_", "/"),
                    "polling_unit_name": pu_name,
                    "file": image_path.name,
                    "ocr_confidence": round(ocr_result.confidence, 1),
                    "extraction_confidence": 0.0,
                    "error": "no_party_votes_extracted",
                    "raw_text_preview": ocr_result.text[:500],
                })

        except Exception as e:
            print(f"  ❌ Error: {e}")
            all_results.append({
                "polling_unit_code": pu_code.replace("_", "/"),
                "polling_unit_name": pu_name,
                "file": image_path.name,
                "error": str(e),
            })

    # Print ward summary
    print("\n" + "=" * 80)
    print("WARD SUMMARY: IPETUMODU II — Osun Governorship 2026-08-15")
    print("=" * 80)

    party_totals: dict[str, int] = {}
    total_accredited = 0
    total_valid = 0
    total_rejected = 0
    successful = 0

    for r in all_results:
        if "error" not in r and r.get("extraction_confidence", 0) > 0:
            successful += 1
            total_accredited += r.get("accredited_voters", 0)
            total_valid += r.get("valid_votes", 0)
            total_rejected += r.get("rejected_votes", 0)
            for party in r.get("parties", []):
                code = party["code"]
                party_totals[code] = party_totals.get(code, 0) + party["votes"]

    print(f"\nSuccessfully processed: {successful}/{len(images)} polling units")
    print(f"Total Accredited Voters: {total_accredited:,}")
    print(f"Total Valid Votes: {total_valid:,}")
    print(f"Total Rejected Votes: {total_rejected:,}")
    print(f"\nParty Results (Ward Total):")
    print("-" * 40)

    for code, votes in sorted(party_totals.items(), key=lambda x: x[1], reverse=True):
        print(f"  {code:10s}: {votes:>6,}")

    # Save results to JSON
    output_path = image_dir / "results_tesseract.json"
    with open(output_path, "w") as f:
        json.dump(
            {
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
            },
            f,
            indent=2,
        )

    print(f"\nFull results saved to: {output_path}")


if __name__ == "__main__":
    main()
