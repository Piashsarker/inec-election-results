#!/usr/bin/env python3
"""Local poller that scrapes INEC IREV portal and pushes results to cloud backend.

This script runs on your local machine with Playwright/browser capabilities
and submits scraped election results to the deployed backend API.

Usage:
    export BACKEND_URL="https://your-app.onrender.com"
    export API_KEY="your-secret-key"
    python local_poller.py --election presidential --state lagos
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")

# Add app to path for imports
sys.path.insert(0, str(Path(__file__).parent))


class CloudAPIClient:
    """Client for communicating with the cloud backend API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def health_check(self) -> bool:
        """Check if backend is reachable."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health", timeout=10)
                return response.status_code == 200
            except Exception as e:
                print(f"❌ Backend health check failed: {e}")
                return False

    async def submit_result(self, result: dict) -> dict:
        """Submit a single polling unit result to the backend."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/results",
                json=result,
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

    async def submit_batch(self, results: list[dict]) -> dict:
        """Submit multiple results in a batch."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/results/batch",
                json={"results": results},
                headers=self.headers,
                timeout=60,
            )
            response.raise_for_status()
            return response.json()

    async def create_job(self, job_config: dict) -> dict:
        """Create a new scraping job on the backend."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/jobs",
                json=job_config,
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

    async def update_job_status(self, job_id: str, status: str, progress: float = 0) -> dict:
        """Update job status on the backend."""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/api/v1/jobs/{job_id}",
                json={"status": status, "progress": progress},
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()


class LocalScraper:
    """Local scraper that uses Playwright to scrape INEC portal."""

    def __init__(self):
        self.results = []

    async def scrape_election(
        self,
        election_type: str,
        state: str | None = None,
        lga: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Scrape election results from INEC portal.

        Args:
            election_type: Type of election (presidential, gubernatorial, etc.)
            state: Target state (optional)
            lga: Target LGA (optional)
            limit: Maximum number of polling units to scrape

        Returns:
            List of extracted results
        """
        print(f"🔍 Starting scrape: {election_type}")
        if state:
            print(f"   State: {state}")
        if lga:
            print(f"   LGA: {lga}")
        print(f"   Limit: {limit} polling units")

        try:
            from app.core.ocr.engine import OCREngine
            from app.core.scraper.browser import BrowserManager
            from app.core.scraper.downloader import ResultSheetDownloader
            from app.core.scraper.navigator import PortalNavigator

            # Initialize components
            async with BrowserManager() as browser:
                navigator = PortalNavigator(browser)
                downloader = ResultSheetDownloader()
                ocr = OCREngine()

                # Navigate to election
                await navigator.navigate_to_election(election_type)

                if state:
                    await navigator.select_state(state)

                if lga:
                    await navigator.select_lga(lga)

                # Get polling units
                polling_units = await navigator.get_polling_units(limit=limit)

                results = []
                for i, pu in enumerate(polling_units):
                    print(f"   Processing {i+1}/{len(polling_units)}: {pu['name']}")

                    # Download result sheet
                    image_path = await downloader.download(pu["image_url"])

                    # Extract data with OCR
                    extraction = await ocr.extract(image_path)

                    if extraction.is_valid:
                        result = {
                            "polling_unit_code": pu["code"],
                            "polling_unit_name": pu["name"],
                            "state": pu.get("state", state),
                            "lga": pu.get("lga", lga),
                            "ward": pu.get("ward"),
                            "election_type": election_type,
                            "parties": [
                                {"code": p.code, "name": p.name, "votes": p.votes}
                                for p in extraction.parties
                            ],
                            "accredited_voters": extraction.accredited_voters,
                            "valid_votes": extraction.valid_votes,
                            "rejected_votes": extraction.rejected_votes,
                            "confidence": extraction.confidence,
                            "scraped_at": datetime.utcnow().isoformat(),
                        }
                        results.append(result)
                    else:
                        print(f"   ⚠️ Low confidence extraction for {pu['name']}")

                return results

        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("   Running in demo mode with sample data...")
            return self._get_demo_results(election_type, state, limit)

    def _get_demo_results(self, election_type: str, state: str, limit: int) -> list[dict]:
        """Generate demo results for testing."""
        demo_results = []
        for i in range(min(limit, 4)):
            demo_results.append({
                "polling_unit_code": f"PU-{i+1:04d}",
                "polling_unit_name": f"Demo Polling Unit {i+1}",
                "state": state or "Lagos",
                "lga": "Demo LGA",
                "ward": f"Ward {i+1}",
                "election_type": election_type,
                "parties": [
                    {"code": "APC", "name": "All Progressives Congress", "votes": 200 + i * 50},
                    {"code": "PDP", "name": "Peoples Democratic Party", "votes": 180 + i * 30},
                    {"code": "LP", "name": "Labour Party", "votes": 250 + i * 40},
                    {"code": "NNPP", "name": "New Nigeria Peoples Party", "votes": 50 + i * 10},
                ],
                "accredited_voters": 800 + i * 100,
                "valid_votes": 680 + i * 80,
                "rejected_votes": 10 + i * 2,
                "confidence": 0.85,
                "scraped_at": datetime.utcnow().isoformat(),
            })
        return demo_results


async def main():
    """Main entry point for local poller."""
    parser = argparse.ArgumentParser(description="INEC Election Results Local Poller")
    parser.add_argument("--election", "-e", default="presidential", help="Election type")
    parser.add_argument("--state", "-s", help="Target state")
    parser.add_argument("--lga", "-l", help="Target LGA")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Max polling units")
    parser.add_argument("--dry-run", action="store_true", help="Don't submit to backend")
    args = parser.parse_args()

    print("🇳🇬 INEC Election Results - Local Poller")
    print("=" * 50)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Key: {'***' + API_KEY[-4:] if API_KEY else 'NOT SET'}")
    print()

    # Initialize API client
    api_client = CloudAPIClient(BACKEND_URL, API_KEY)

    # Health check
    if not args.dry_run:
        print("🔗 Checking backend connection...")
        if await api_client.health_check():
            print("✅ Backend is reachable")
        else:
            print("❌ Cannot reach backend. Check BACKEND_URL and try again.")
            return

    # Initialize scraper
    scraper = LocalScraper()

    # Run scraping
    print()
    results = await scraper.scrape_election(
        election_type=args.election,
        state=args.state,
        lga=args.lga,
        limit=args.limit,
    )

    print()
    print(f"📊 Scraped {len(results)} results")

    if not results:
        print("No results to submit")
        return

    # Submit to backend
    if args.dry_run:
        print("\n🔍 Dry run - not submitting to backend")
        print(json.dumps(results[:2], indent=2))
    else:
        print("\n📤 Submitting results to backend...")
        try:
            response = await api_client.submit_batch(results)
            print(f"✅ Submitted {len(results)} results")
            print(f"   Response: {response}")
        except httpx.HTTPStatusError as e:
            print(f"❌ Failed to submit: {e.response.status_code}")
            print(f"   {e.response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
