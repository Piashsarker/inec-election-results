"""LangGraph workflow definition for election data processing.

This module defines the agent state and LangGraph workflow for processing
election results from the INEC portal.

Requirements: 1.1, 2.1, 3.1, 4.2
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

logger = logging.getLogger("inec_agent.agents.graph")


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    NAVIGATING = "navigating"
    DOWNLOADING = "downloading"
    PREPROCESSING = "preprocessing"
    OCR_PROCESSING = "ocr_processing"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    STORING = "storing"
    FLAGGING = "flagging"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class LocationInfo:
    election_type: str = ""
    state: str = ""
    lga: str = ""
    ward: str = ""
    polling_unit_id: str = ""
    polling_unit_name: str = ""


@dataclass
class DownloadedImage:
    file_path: str
    file_format: str
    file_size: int
    polling_unit_id: str
    download_attempts: int = 1


@dataclass
class ProcessingError:
    stage: str
    message: str
    details: dict[str, Any] | None = None
    recoverable: bool = True


class AgentState(TypedDict):
    """State shared across all agents in the LangGraph workflow."""

    job_id: str
    current_location: dict[str, str]
    polling_unit: dict[str, Any] | None
    downloaded_images: list[dict[str, Any]]
    ocr_results: dict[str, Any] | None
    extracted_data: dict[str, Any] | None
    validation_results: dict[str, Any] | None
    errors: list[dict[str, Any]]
    status: str
    metadata: dict[str, Any]


def create_initial_state(
    job_id: str,
    election_type: str = "",
    state: str = "",
    lga: str = "",
    ward: str = "",
) -> AgentState:
    return AgentState(
        job_id=job_id,
        current_location={
            "election_type": election_type,
            "state": state,
            "lga": lga,
            "ward": ward,
            "polling_unit_id": "",
            "polling_unit_name": "",
        },
        polling_unit=None,
        downloaded_images=[],
        ocr_results=None,
        extracted_data=None,
        validation_results=None,
        errors=[],
        status=ProcessingStatus.PENDING.value,
        metadata={},
    )


# ── Node implementations ───────────────────────────────────────────────────────
# Each node delegates to the appropriate agent class.  Agents are imported
# lazily inside the node to avoid circular imports and to keep startup fast.

async def navigate_node(state: AgentState) -> AgentState:
    """Navigate to the polling unit and download the result sheet image."""
    logger.info(f"Navigate+Download node: job {state['job_id']}")
    from app.agents.navigator import NavigatorAgent
    agent = NavigatorAgent()
    return await agent.process_state(state)


async def download_node(state: AgentState) -> AgentState:
    """Pass-through — download is combined with navigate above."""
    logger.info(f"Download node: job {state['job_id']}")
    state["status"] = ProcessingStatus.DOWNLOADING.value
    return state


async def preprocess_node(state: AgentState) -> AgentState:
    """Preprocess + OCR + extract — handled by ProcessorAgent."""
    logger.info(f"OCR/Extract node: job {state['job_id']}")
    from app.agents.processor import ProcessorAgent
    from app.config import get_settings
    settings = get_settings()
    agent = ProcessorAgent(
        openai_api_key=settings.openai.api_key,
        openai_model=settings.openai.model,
    )
    return await agent.process_state(state)


async def ocr_node(state: AgentState) -> AgentState:
    """Pass-through — OCR is handled in preprocess_node."""
    state["status"] = ProcessingStatus.OCR_PROCESSING.value
    return state


async def extract_node(state: AgentState) -> AgentState:
    """Pass-through — extraction is handled in preprocess_node."""
    state["status"] = ProcessingStatus.EXTRACTING.value
    return state


async def validate_node(state: AgentState) -> AgentState:
    """Validate extracted election data."""
    logger.info(f"Validate node: job {state['job_id']}")
    from app.agents.validator import ValidatorAgent
    agent = ValidatorAgent()
    return await agent.process_state(state)


async def store_node(state: AgentState) -> AgentState:
    """Persist validated election data to the database."""
    logger.info(f"Store node: job {state['job_id']}")
    state["status"] = ProcessingStatus.STORING.value

    extracted = state.get("extracted_data")
    downloaded = state.get("downloaded_images", [])
    if not extracted or not downloaded:
        state["status"] = ProcessingStatus.COMPLETED.value
        return state

    try:
        import decimal

        from sqlalchemy import select

        from app.config import get_settings
        from app.db.session import get_async_session
        from app.models.election import ElectionResult, PartyResult

        settings = get_settings()  # noqa: F841  (kept for future env access)
        location = state["current_location"]
        pu_data = state.get("polling_unit", {}) or {}
        image_info = downloaded[0]

        # Resolve the polling_unit DB row by code
        async for session in get_async_session():
            from app.models.election import ElectionType, PoliticalParty
            from app.models.geography import PollingUnit

            # Look up polling unit
            pu_result = await session.execute(
                select(PollingUnit).where(PollingUnit.code == pu_data.get("code", ""))
            )
            pu = pu_result.scalar_one_or_none()

            # Look up election type
            et_result = await session.execute(
                select(ElectionType).where(
                    ElectionType.code == location.get("election_type", "")
                )
            )
            et = et_result.scalar_one_or_none()

            if not pu or not et:
                logger.warning(
                    f"Cannot store — polling unit or election type not found "
                    f"(pu_code={pu_data.get('code')}, et_code={location.get('election_type')})"
                )
                state["status"] = ProcessingStatus.COMPLETED.value
                return state

            summary = extracted.get("summary", {})
            confidence = extracted.get("confidence", 0.0)

            # Upsert ElectionResult
            existing = await session.execute(
                select(ElectionResult).where(
                    ElectionResult.election_type_id == et.id,
                    ElectionResult.polling_unit_id == pu.id,
                )
            )
            er = existing.scalar_one_or_none()

            storage_url = image_info.get("storage_url") or image_info.get("file_path", "")

            if er is None:
                er = ElectionResult(
                    id=uuid.uuid4(),
                    election_type_id=et.id,
                    polling_unit_id=pu.id,
                    accredited_voters=summary.get("accredited_voters", 0),
                    valid_votes=summary.get("valid_votes", 0),
                    rejected_votes=summary.get("rejected_votes", 0),
                    confidence_score=decimal.Decimal(str(round(confidence, 2))),
                    source_image_path=storage_url[:500] if storage_url else None,
                )
                session.add(er)
                await session.flush()
            else:
                er.accredited_voters = summary.get("accredited_voters", er.accredited_voters)
                er.valid_votes = summary.get("valid_votes", er.valid_votes)
                er.rejected_votes = summary.get("rejected_votes", er.rejected_votes)
                er.confidence_score = decimal.Decimal(str(round(confidence, 2)))
                if storage_url:
                    er.source_image_path = storage_url[:500]

            # Upsert PartyResults
            total_votes = sum(
                pv.get("votes", 0) for pv in extracted.get("party_votes", [])
            ) or 1

            for pv in extracted.get("party_votes", []):
                party_code = pv.get("party_code", "").upper()
                if not party_code:
                    continue

                # Get or create party
                party_res = await session.execute(
                    select(PoliticalParty).where(PoliticalParty.code == party_code)
                )
                party = party_res.scalar_one_or_none()
                if party is None:
                    party = PoliticalParty(
                        id=uuid.uuid4(),
                        code=party_code,
                        name=pv.get("party_name", party_code),
                    )
                    session.add(party)
                    await session.flush()

                votes = pv.get("votes", 0)
                pct = decimal.Decimal(str(round((votes / total_votes) * 100, 2)))

                pr_res = await session.execute(
                    select(PartyResult).where(
                        PartyResult.election_result_id == er.id,
                        PartyResult.party_id == party.id,
                    )
                )
                pr = pr_res.scalar_one_or_none()
                if pr is None:
                    session.add(PartyResult(
                        id=uuid.uuid4(),
                        election_result_id=er.id,
                        party_id=party.id,
                        vote_count=votes,
                        percentage=pct,
                    ))
                else:
                    pr.vote_count = votes
                    pr.percentage = pct

            await session.commit()
            logger.info(
                f"Stored result for PU {pu.code} — "
                f"{len(extracted.get('party_votes', []))} parties, "
                f"confidence={confidence:.2f}"
            )
            state["metadata"]["db_result_id"] = str(er.id)
            break  # only one session iteration needed

    except Exception as exc:
        logger.error(f"Store node error: {exc}", exc_info=True)
        state["errors"].append({"stage": "store", "message": str(exc), "recoverable": False})

    state["status"] = ProcessingStatus.COMPLETED.value
    return state


async def flag_node(state: AgentState) -> AgentState:
    """Flag the result for manual review and still persist it."""
    logger.info(f"Flag node: job {state['job_id']}")
    state["status"] = ProcessingStatus.FLAGGING.value

    # Store what we have even if validation failed — the FlaggedResult
    # record will point reviewers to it.
    state = await store_node(state)

    validation = state.get("validation_results") or {}
    result_id = state.get("metadata", {}).get("db_result_id")

    if result_id:
        try:
            from sqlalchemy import select

            from app.config import get_settings  # noqa: F401
            from app.db.session import get_async_session
            from app.models.election import ElectionResult
            from app.models.job import FlaggedResult

            async for session in get_async_session():
                er_res = await session.execute(
                    select(ElectionResult).where(
                        ElectionResult.id == uuid.UUID(result_id)
                    )
                )
                er = er_res.scalar_one_or_none()
                if er:
                    errors = validation.get("errors", [])
                    reason = "; ".join(errors) if errors else "Low confidence or validation failed"
                    session.add(FlaggedResult(
                        id=uuid.uuid4(),
                        election_result_id=er.id,
                        reason=reason[:500],
                        status="pending",
                    ))
                    await session.commit()
                break
        except Exception as exc:
            logger.error(f"Flag node DB error: {exc}", exc_info=True)

    state["status"] = ProcessingStatus.COMPLETED.value
    return state


def should_store_or_flag(state: AgentState) -> str:
    validation_results = state.get("validation_results")
    if validation_results is None:
        return "flag"
    if (
        validation_results.get("is_valid", False)
        and not validation_results.get("should_flag", True)
    ):
        return "store"
    return "flag"


def create_agent_graph() -> StateGraph:
    """Compile and return the full processing workflow."""
    workflow = StateGraph(AgentState)

    workflow.add_node("navigate", navigate_node)
    workflow.add_node("download", download_node)
    workflow.add_node("preprocess", preprocess_node)
    workflow.add_node("ocr", ocr_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("store", store_node)
    workflow.add_node("flag", flag_node)

    workflow.add_edge("navigate", "download")
    workflow.add_edge("download", "preprocess")
    workflow.add_edge("preprocess", "ocr")
    workflow.add_edge("ocr", "extract")
    workflow.add_edge("extract", "validate")
    workflow.add_conditional_edges(
        "validate", should_store_or_flag, {"store": "store", "flag": "flag"}
    )
    workflow.add_edge("store", END)
    workflow.add_edge("flag", END)

    workflow.set_entry_point("navigate")
    return workflow.compile()


_compiled_graph = None


def get_agent_graph() -> StateGraph:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_agent_graph()
    return _compiled_graph
