"""Navigator agent for portal navigation and image downloading.

This module provides the navigator agent that handles navigation through
the INEC portal hierarchy and downloading result sheet images.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.agents.graph import AgentState, ProcessingStatus
from app.core.scraper.browser import BrowserManager
from app.core.scraper.downloader import DownloadResult, ResultSheetDownloader
from app.core.scraper.navigator import (
    LGA,
    ElectionType,
    NavigationError,
    PollingUnit,
    PortalNavigator,
    State,
    Ward,
)

logger = logging.getLogger("inec_agent.agents.navigator")


@dataclass
class NavigationResult:
    """Result of a navigation operation.

    Attributes:
        success: Whether navigation was successful
        polling_unit: The polling unit navigated to
        download_result: Result of downloading the result sheet
        error: Error message if navigation failed
    """

    success: bool
    polling_unit: PollingUnit | None = None
    download_result: DownloadResult | None = None
    error: str | None = None


class NavigatorAgent:
    """Agent for navigating the INEC portal and downloading result sheets.

    This agent handles:
    - Navigation through the portal hierarchy (Election Type → State → LGA → Ward → PU)
    - Downloading result sheet images for polling units
    - Error handling and logging for navigation failures

    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1
    """

    def __init__(
        self,
        browser_manager: BrowserManager | None = None,
        storage_path: str | None = None,
    ):
        """Initialize the navigator agent.

        Args:
            browser_manager: Browser manager for web requests
            storage_path: Path to store downloaded result sheets
        """
        self.browser = browser_manager or BrowserManager()
        self.navigator = PortalNavigator(self.browser)
        self.downloader = ResultSheetDownloader(
            storage_path=storage_path,
            browser_manager=self.browser,
        )

        logger.info("NavigatorAgent initialized")

    async def get_election_types(self) -> list[ElectionType]:
        """Retrieve available election types from the portal.

        Returns:
            List of ElectionType objects

        Raises:
            NavigationError: If retrieval fails
        """
        logger.info("Fetching election types")
        return await self.navigator.get_election_types()

    async def get_states(self, election_type: str) -> list[State]:
        """Retrieve states for an election type.

        Args:
            election_type: Election type code

        Returns:
            List of State objects (36 states + FCT)

        Raises:
            NavigationError: If retrieval fails
        """
        logger.info(f"Fetching states for election type: {election_type}")
        return await self.navigator.get_states(election_type)

    async def get_lgas(self, election_type: str, state: str) -> list[LGA]:
        """Retrieve LGAs for a state.

        Args:
            election_type: Election type code
            state: State code

        Returns:
            List of LGA objects

        Raises:
            NavigationError: If retrieval fails
        """
        logger.info(f"Fetching LGAs for state: {state}")
        return await self.navigator.get_lgas(election_type, state)

    async def get_wards(self, election_type: str, state: str, lga: str) -> list[Ward]:
        """Retrieve wards for an LGA.

        Args:
            election_type: Election type code
            state: State code
            lga: LGA code

        Returns:
            List of Ward objects

        Raises:
            NavigationError: If retrieval fails
        """
        logger.info(f"Fetching wards for LGA: {lga}")
        return await self.navigator.get_wards(election_type, state, lga)

    async def get_polling_units(
        self,
        election_type: str,
        state: str,
        lga: str,
        ward: str,
    ) -> list[PollingUnit]:
        """Retrieve polling units for a ward.

        Args:
            election_type: Election type code
            state: State code
            lga: LGA code
            ward: Ward code

        Returns:
            List of PollingUnit objects with result URLs

        Raises:
            NavigationError: If retrieval fails
        """
        logger.info(f"Fetching polling units for ward: {ward}")
        return await self.navigator.get_polling_units(election_type, state, lga, ward)

    async def navigate_and_download(
        self,
        election_type: str,
        state: str,
        lga: str,
        ward: str,
        polling_unit: PollingUnit,
    ) -> NavigationResult:
        """Navigate to a polling unit and download its result sheet.

        This method combines navigation and download into a single operation,
        handling errors and logging appropriately.

        Args:
            election_type: Election type code
            state: State code
            lga: LGA code
            ward: Ward code
            polling_unit: Polling unit to process

        Returns:
            NavigationResult with download status
        """
        logger.info(
            f"Navigating to polling unit {polling_unit.id} "
            f"({election_type}/{state}/{lga}/{ward})"
        )

        try:
            # Check if polling unit has a result URL
            if not polling_unit.result_url:
                logger.warning(f"No result URL for polling unit {polling_unit.id}")
                return NavigationResult(
                    success=False,
                    polling_unit=polling_unit,
                    error="No result URL available",
                )

            # Download the result sheet
            download_result = await self.downloader.download(
                url=polling_unit.result_url,
                election_type=election_type,
                state=state,
                lga=lga,
                ward=ward,
                pu_id=polling_unit.id,
            )

            if download_result.success:
                logger.info(
                    f"Successfully downloaded result sheet for {polling_unit.id}: "
                    f"{download_result.file_path}"
                )
                return NavigationResult(
                    success=True,
                    polling_unit=polling_unit,
                    download_result=download_result,
                )
            else:
                logger.warning(
                    f"Failed to download result sheet for {polling_unit.id}: "
                    f"{download_result.error}"
                )
                return NavigationResult(
                    success=False,
                    polling_unit=polling_unit,
                    download_result=download_result,
                    error=download_result.error,
                )

        except NavigationError as e:
            logger.error(
                f"Navigation error for polling unit {polling_unit.id}: {e}",
                extra=e.details,
            )
            return NavigationResult(
                success=False,
                polling_unit=polling_unit,
                error=str(e),
            )

        except Exception as e:
            logger.error(
                f"Unexpected error navigating to polling unit {polling_unit.id}: {e}"
            )
            return NavigationResult(
                success=False,
                polling_unit=polling_unit,
                error=str(e),
            )

    async def process_state(
        self,
        state: AgentState,
    ) -> AgentState:
        """Process the navigate and download steps for the workflow.

        This method is called by the LangGraph workflow to handle
        navigation and downloading for a polling unit.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        logger.info(f"Processing navigation for job {state['job_id']}")

        # Update status
        state["status"] = ProcessingStatus.NAVIGATING.value

        # Get location info
        location = state["current_location"]
        polling_unit_data = state.get("polling_unit")

        if not polling_unit_data:
            state["errors"].append({
                "stage": "navigate",
                "message": "No polling unit specified",
                "recoverable": False,
            })
            state["status"] = ProcessingStatus.FAILED.value
            return state

        # Create PollingUnit object
        polling_unit = PollingUnit(
            id=polling_unit_data.get("id", ""),
            name=polling_unit_data.get("name", ""),
            code=polling_unit_data.get("code", ""),
            ward_id=location.get("ward", ""),
            result_url=polling_unit_data.get("result_url"),
        )

        # Navigate and download
        result = await self.navigate_and_download(
            election_type=location.get("election_type", ""),
            state=location.get("state", ""),
            lga=location.get("lga", ""),
            ward=location.get("ward", ""),
            polling_unit=polling_unit,
        )

        if result.success and result.download_result:
            # Update state with downloaded image info
            state["downloaded_images"].append({
                "file_path": result.download_result.file_path,
                "file_format": result.download_result.file_format.value if result.download_result.file_format else None,
                "file_size": result.download_result.file_size,
                "polling_unit_id": polling_unit.id,
                "download_attempts": result.download_result.attempts,
            })
            state["status"] = ProcessingStatus.DOWNLOADING.value
        else:
            # Record error
            state["errors"].append({
                "stage": "navigate",
                "message": result.error or "Navigation failed",
                "recoverable": True,
            })
            state["status"] = ProcessingStatus.FAILED.value

        return state

    async def discover_all_polling_units(
        self,
        election_type: str | None = None,
        target_state: str | None = None,
        target_lga: str | None = None,
        target_ward: str | None = None,
    ) -> list[dict[str, Any]]:
        """Discover all polling units matching the given criteria.

        This method navigates through the portal hierarchy to discover
        all polling units that match the specified filters.

        Args:
            election_type: Target election type (None = all)
            target_state: Target state (None = all)
            target_lga: Target LGA (None = all)
            target_ward: Target ward (None = all)

        Returns:
            List of polling unit dictionaries with location info
        """
        logger.info(
            f"Discovering polling units: election_type={election_type}, "
            f"state={target_state}, lga={target_lga}, ward={target_ward}"
        )

        polling_units = []

        # Get election types
        if election_type:
            election_types = [ElectionType(id="", name="", code=election_type)]
        else:
            election_types = await self.get_election_types()

        for et in election_types:
            et_code = et.code

            # Get states
            if target_state:
                states = [State(id="", name="", code=target_state)]
            else:
                try:
                    states = await self.get_states(et_code)
                except NavigationError as e:
                    logger.error(f"Failed to get states for {et_code}: {e}")
                    continue

            for state in states:
                state_code = state.code

                # Get LGAs
                if target_lga:
                    lgas = [LGA(id="", name="", code=target_lga, state_id=state_code)]
                else:
                    try:
                        lgas = await self.get_lgas(et_code, state_code)
                    except NavigationError as e:
                        logger.error(f"Failed to get LGAs for {state_code}: {e}")
                        continue

                for lga in lgas:
                    lga_code = lga.code

                    # Get wards
                    if target_ward:
                        wards = [Ward(id="", name="", code=target_ward, lga_id=lga_code)]
                    else:
                        try:
                            wards = await self.get_wards(et_code, state_code, lga_code)
                        except NavigationError as e:
                            logger.error(f"Failed to get wards for {lga_code}: {e}")
                            continue

                    for ward in wards:
                        ward_code = ward.code

                        # Get polling units
                        try:
                            pus = await self.get_polling_units(
                                et_code, state_code, lga_code, ward_code
                            )

                            for pu in pus:
                                polling_units.append({
                                    "election_type": et_code,
                                    "state": state_code,
                                    "lga": lga_code,
                                    "ward": ward_code,
                                    "polling_unit": {
                                        "id": pu.id,
                                        "name": pu.name,
                                        "code": pu.code,
                                        "result_url": pu.result_url,
                                    },
                                })

                        except NavigationError as e:
                            logger.error(f"Failed to get polling units for {ward_code}: {e}")
                            continue

        logger.info(f"Discovered {len(polling_units)} polling units")
        return polling_units

    def get_download_progress(self) -> dict[str, int]:
        """Get download progress statistics.

        Returns:
            Dictionary with total, completed, and failed counts
        """
        return self.downloader.get_progress()

    def reset_progress(self) -> None:
        """Reset download progress counters."""
        self.downloader.reset_progress()
