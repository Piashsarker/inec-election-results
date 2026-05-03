"""Portal navigator for INEC IREV website.

This module provides navigation through the INEC portal hierarchy:
Election Type → State → LGA → Ward → Polling Unit

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import get_settings
from app.core.scraper.browser import BrowserManager

logger = logging.getLogger("inec_agent.scraper.navigator")


@dataclass
class ElectionType:
    """Represents an election type from the portal."""
    id: str
    name: str
    code: str


@dataclass
class State:
    """Represents a Nigerian state."""
    id: str
    name: str
    code: str


@dataclass
class LGA:
    """Represents a Local Government Area."""
    id: str
    name: str
    code: str
    state_id: str


@dataclass
class Ward:
    """Represents an electoral ward."""
    id: str
    name: str
    code: str
    lga_id: str


@dataclass
class PollingUnit:
    """Represents a polling unit."""
    id: str
    name: str
    code: str
    ward_id: str
    result_url: str | None = None


class NavigationError(Exception):
    """Raised when navigation fails."""

    def __init__(self, level: str, message: str, details: dict | None = None):
        self.level = level
        self.message = message
        self.details = details or {}
        super().__init__(f"Navigation error at {level}: {message}")


class PortalNavigator:
    """Navigates the INEC IREV portal hierarchy.

    This class provides methods to navigate through each level of the
    INEC portal hierarchy and extract available options.

    Requirements:
    - 1.1: Connect to INEC portal
    - 1.2: Retrieve election types
    - 1.3: Retrieve states for election type
    - 1.4: Retrieve LGAs for state
    - 1.5: Retrieve wards for LGA
    - 1.6: Retrieve polling units for ward
    - 1.8: Log navigation failures with details
    """

    def __init__(self, browser_manager: BrowserManager):
        """Initialize the portal navigator.

        Args:
            browser_manager: BrowserManager instance for web requests
        """
        self.browser = browser_manager
        self.settings = get_settings()
        self.base_url = self.settings.inec_portal_url

    async def get_election_types(self) -> list[ElectionType]:
        """Retrieve available election types from portal.

        Returns:
            List of ElectionType objects

        Raises:
            NavigationError: If retrieval fails
        """
        logger.info("Fetching election types from portal")

        try:
            result = await self.browser.fetch_with_retry(self.base_url)

            if not result.success:
                raise NavigationError(
                    "election_types",
                    f"Failed to load portal: HTTP {result.status}",
                )

            # Parse election types from page content
            # In production, this would parse the actual HTML
            # For now, return known Nigerian election types
            election_types = [
                ElectionType(id="1", name="Presidential Election", code="presidential"),
                ElectionType(id="2", name="Governorship Election", code="governorship"),
                ElectionType(id="3", name="Senatorial Election", code="senatorial"),
                ElectionType(id="4", name="House of Representatives", code="house_of_reps"),
                ElectionType(id="5", name="House of Assembly", code="house_of_assembly"),
            ]

            logger.info(f"Found {len(election_types)} election types")
            return election_types

        except Exception as e:
            logger.error(f"Failed to get election types: {e}")
            raise NavigationError("election_types", str(e))

    async def get_states(self, election_type: str) -> list[State]:
        """Retrieve states for a given election type.

        Args:
            election_type: Election type code

        Returns:
            List of State objects (36 states + FCT)

        Raises:
            NavigationError: If retrieval fails
        """
        logger.info(f"Fetching states for election type: {election_type}")

        try:
            url = f"{self.base_url}/{election_type}"
            result = await self.browser.fetch_with_retry(url)

            if not result.success:
                raise NavigationError(
                    "states",
                    f"Failed to load states: HTTP {result.status}",
                    {"election_type": election_type},
                )

            # Nigerian states (36 + FCT)
            states_data = [
                ("1", "Abia", "AB"), ("2", "Adamawa", "AD"), ("3", "Akwa Ibom", "AK"),
                ("4", "Anambra", "AN"), ("5", "Bauchi", "BA"), ("6", "Bayelsa", "BY"),
                ("7", "Benue", "BE"), ("8", "Borno", "BO"), ("9", "Cross River", "CR"),
                ("10", "Delta", "DE"), ("11", "Ebonyi", "EB"), ("12", "Edo", "ED"),
                ("13", "Ekiti", "EK"), ("14", "Enugu", "EN"), ("15", "FCT", "FC"),
                ("16", "Gombe", "GO"), ("17", "Imo", "IM"), ("18", "Jigawa", "JI"),
                ("19", "Kaduna", "KD"), ("20", "Kano", "KN"), ("21", "Katsina", "KT"),
                ("22", "Kebbi", "KB"), ("23", "Kogi", "KO"), ("24", "Kwara", "KW"),
                ("25", "Lagos", "LA"), ("26", "Nasarawa", "NA"), ("27", "Niger", "NI"),
                ("28", "Ogun", "OG"), ("29", "Ondo", "ON"), ("30", "Osun", "OS"),
                ("31", "Oyo", "OY"), ("32", "Plateau", "PL"), ("33", "Rivers", "RI"),
                ("34", "Sokoto", "SO"), ("35", "Taraba", "TA"), ("36", "Yobe", "YO"),
                ("37", "Zamfara", "ZA"),
            ]

            states = [State(id=s[0], name=s[1], code=s[2]) for s in states_data]
            logger.info(f"Found {len(states)} states")
            return states

        except NavigationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get states: {e}", extra={"election_type": election_type})
            raise NavigationError("states", str(e), {"election_type": election_type})

    async def get_lgas(self, election_type: str, state: str) -> list[LGA]:
        """Retrieve LGAs for a given state.

        Args:
            election_type: Election type code
            state: State code

        Returns:
            List of LGA objects

        Raises:
            NavigationError: If retrieval fails
        """
        logger.info(f"Fetching LGAs for state: {state}")

        try:
            url = f"{self.base_url}/{election_type}/{state}"
            result = await self.browser.fetch_with_retry(url)

            if not result.success:
                raise NavigationError(
                    "lgas",
                    f"Failed to load LGAs: HTTP {result.status}",
                    {"election_type": election_type, "state": state},
                )

            # Sample LGAs - in production would parse from HTML
            lgas = [
                LGA(id="1", name="Sample LGA 1", code="LGA1", state_id=state),
                LGA(id="2", name="Sample LGA 2", code="LGA2", state_id=state),
            ]

            logger.info(f"Found {len(lgas)} LGAs in {state}")
            return lgas

        except NavigationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get LGAs: {e}", extra={"state": state})
            raise NavigationError("lgas", str(e), {"election_type": election_type, "state": state})

    async def get_wards(self, election_type: str, state: str, lga: str) -> list[Ward]:
        """Retrieve wards for a given LGA.

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

        try:
            url = f"{self.base_url}/{election_type}/{state}/{lga}"
            result = await self.browser.fetch_with_retry(url)

            if not result.success:
                raise NavigationError(
                    "wards",
                    f"Failed to load wards: HTTP {result.status}",
                    {"election_type": election_type, "state": state, "lga": lga},
                )

            # Sample wards - in production would parse from HTML
            wards = [
                Ward(id="1", name="Sample Ward 1", code="WARD1", lga_id=lga),
                Ward(id="2", name="Sample Ward 2", code="WARD2", lga_id=lga),
            ]

            logger.info(f"Found {len(wards)} wards in {lga}")
            return wards

        except NavigationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get wards: {e}", extra={"lga": lga})
            raise NavigationError(
                "wards", str(e),
                {"election_type": election_type, "state": state, "lga": lga},
            )

    async def get_polling_units(
        self, election_type: str, state: str, lga: str, ward: str
    ) -> list[PollingUnit]:
        """Retrieve polling units for a given ward.

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

        try:
            url = f"{self.base_url}/{election_type}/{state}/{lga}/{ward}"
            result = await self.browser.fetch_with_retry(url)

            if not result.success:
                raise NavigationError(
                    "polling_units",
                    f"Failed to load polling units: HTTP {result.status}",
                    {"election_type": election_type, "state": state, "lga": lga, "ward": ward},
                )

            # Sample polling units - in production would parse from HTML
            polling_units = [
                PollingUnit(
                    id="1",
                    name="Sample PU 1",
                    code="PU001",
                    ward_id=ward,
                    result_url=f"{self.base_url}/results/pu001.png"
                ),
                PollingUnit(
                    id="2",
                    name="Sample PU 2",
                    code="PU002",
                    ward_id=ward,
                    result_url=f"{self.base_url}/results/pu002.png"
                ),
            ]

            logger.info(f"Found {len(polling_units)} polling units in {ward}")
            return polling_units

        except NavigationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get polling units: {e}", extra={"ward": ward})
            raise NavigationError(
                "polling_units",
                str(e),
                {"election_type": election_type, "state": state, "lga": lga, "ward": ward}
            )
