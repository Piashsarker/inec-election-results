"""LangGraph workflow definition for election data processing.

This module defines the agent state and LangGraph workflow for processing
election results from the INEC portal.

Requirements: 1.1, 2.1, 3.1, 4.2
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.core.extractor.parser import ExtractionResult
from app.core.extractor.validator import ValidationResult
from app.core.ocr.engine import OCROrchestrationResult
from app.core.scraper.downloader import DownloadResult
from app.core.scraper.navigator import PollingUnit

logger = logging.getLogger("inec_agent.agents.graph")


class ProcessingStatus(str, Enum):
    """Status of the processing workflow."""
    
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
    """Current location in the portal hierarchy."""
    
    election_type: str = ""
    state: str = ""
    lga: str = ""
    ward: str = ""
    polling_unit_id: str = ""
    polling_unit_name: str = ""


@dataclass
class DownloadedImage:
    """Information about a downloaded result sheet image."""
    
    file_path: str
    file_format: str
    file_size: int
    polling_unit_id: str
    download_attempts: int = 1


@dataclass
class ProcessingError:
    """Error that occurred during processing."""
    
    stage: str
    message: str
    details: Optional[Dict[str, Any]] = None
    recoverable: bool = True


class AgentState(TypedDict):
    """State shared across agents in the LangGraph workflow.
    
    This TypedDict defines the state that flows through the workflow,
    containing all information needed for processing election results.
    
    Attributes:
        job_id: Unique identifier for the scraping job
        current_location: Current position in portal hierarchy
        polling_unit: Current polling unit being processed
        downloaded_images: List of downloaded result sheet images
        ocr_results: OCR processing results
        extracted_data: Extracted election data
        validation_results: Data validation results
        errors: List of errors encountered during processing
        status: Current processing status
        metadata: Additional metadata for the workflow
    """
    
    # Job identification
    job_id: str
    
    # Navigation state
    current_location: Dict[str, str]
    polling_unit: Optional[Dict[str, Any]]
    
    # Processing results
    downloaded_images: List[Dict[str, Any]]
    ocr_results: Optional[Dict[str, Any]]
    extracted_data: Optional[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]]
    
    # Error tracking
    errors: List[Dict[str, Any]]
    
    # Workflow status
    status: str
    
    # Additional metadata
    metadata: Dict[str, Any]


def create_initial_state(
    job_id: str,
    election_type: str = "",
    state: str = "",
    lga: str = "",
    ward: str = "",
) -> AgentState:
    """Create initial agent state for a new workflow.
    
    Args:
        job_id: Unique job identifier
        election_type: Target election type
        state: Target state
        lga: Target LGA
        ward: Target ward
        
    Returns:
        Initial AgentState
    """
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


# Node functions for the workflow

async def navigate_node(state: AgentState) -> AgentState:
    """Navigate to the polling unit in the portal.
    
    This node handles navigation through the INEC portal hierarchy
    to reach the target polling unit.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with navigation results
    """
    logger.info(f"Navigate node: Processing job {state['job_id']}")
    
    state["status"] = ProcessingStatus.NAVIGATING.value
    
    # Navigation is handled by NavigatorAgent
    # This node updates state to indicate navigation is complete
    
    return state


async def download_node(state: AgentState) -> AgentState:
    """Download result sheet image for the polling unit.
    
    This node handles downloading the result sheet image from
    the INEC portal.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with download results
    """
    logger.info(f"Download node: Processing job {state['job_id']}")
    
    state["status"] = ProcessingStatus.DOWNLOADING.value
    
    # Download is handled by NavigatorAgent
    # This node updates state with downloaded image info
    
    return state


async def preprocess_node(state: AgentState) -> AgentState:
    """Preprocess the downloaded image for OCR.
    
    This node handles image preprocessing including grayscale conversion,
    deskewing, noise removal, and contrast enhancement.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with preprocessing results
    """
    logger.info(f"Preprocess node: Processing job {state['job_id']}")
    
    state["status"] = ProcessingStatus.PREPROCESSING.value
    
    # Preprocessing is handled by ProcessorAgent
    
    return state


async def ocr_node(state: AgentState) -> AgentState:
    """Perform OCR on the preprocessed image.
    
    This node handles OCR processing using either Tesseract or
    GPT-4 Vision based on image quality.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with OCR results
    """
    logger.info(f"OCR node: Processing job {state['job_id']}")
    
    state["status"] = ProcessingStatus.OCR_PROCESSING.value
    
    # OCR is handled by ProcessorAgent
    
    return state


async def extract_node(state: AgentState) -> AgentState:
    """Extract structured data from OCR results.
    
    This node handles parsing OCR output to extract party names,
    vote counts, and summary fields.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with extracted data
    """
    logger.info(f"Extract node: Processing job {state['job_id']}")
    
    state["status"] = ProcessingStatus.EXTRACTING.value
    
    # Extraction is handled by ProcessorAgent
    
    return state


async def validate_node(state: AgentState) -> AgentState:
    """Validate extracted election data.
    
    This node handles data validation including vote sum validation,
    totals validation, and confidence scoring.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with validation results
    """
    logger.info(f"Validate node: Processing job {state['job_id']}")
    
    state["status"] = ProcessingStatus.VALIDATING.value
    
    # Validation is handled by ValidatorAgent
    
    return state


async def store_node(state: AgentState) -> AgentState:
    """Store validated election data in the database.
    
    This node handles persisting the extracted and validated
    election data to the database.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state after storage
    """
    logger.info(f"Store node: Processing job {state['job_id']}")
    
    state["status"] = ProcessingStatus.STORING.value
    
    # Storage is handled by the orchestrator
    
    state["status"] = ProcessingStatus.COMPLETED.value
    
    return state


async def flag_node(state: AgentState) -> AgentState:
    """Flag result for manual review.
    
    This node handles flagging results that failed validation
    or have low confidence scores.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state after flagging
    """
    logger.info(f"Flag node: Processing job {state['job_id']}")
    
    state["status"] = ProcessingStatus.FLAGGING.value
    
    # Flagging is handled by ValidatorAgent
    
    state["status"] = ProcessingStatus.COMPLETED.value
    
    return state


def should_store_or_flag(state: AgentState) -> str:
    """Determine whether to store or flag the result.
    
    This conditional edge function checks validation results
    to determine the next step in the workflow.
    
    Args:
        state: Current agent state
        
    Returns:
        "store" if validation passed, "flag" otherwise
    """
    validation_results = state.get("validation_results")
    
    if validation_results is None:
        logger.warning("No validation results found, flagging for review")
        return "flag"
    
    is_valid = validation_results.get("is_valid", False)
    should_flag = validation_results.get("should_flag", True)
    
    if is_valid and not should_flag:
        logger.info("Validation passed, storing result")
        return "store"
    else:
        logger.info(f"Validation failed or flagged, reason: {validation_results.get('flag_reason', 'unknown')}")
        return "flag"


def create_agent_graph() -> StateGraph:
    """Create the LangGraph workflow for election data processing.
    
    This function creates a StateGraph with nodes for each processing
    step and edges defining the workflow flow.
    
    Workflow:
    1. navigate -> download -> preprocess -> ocr -> extract -> validate
    2. validate -> store (if valid) or flag (if invalid)
    3. store/flag -> END
    
    Returns:
        Compiled StateGraph workflow
    """
    # Create the workflow graph
    workflow = StateGraph(AgentState)
    
    # Add nodes for each processing step
    workflow.add_node("navigate", navigate_node)
    workflow.add_node("download", download_node)
    workflow.add_node("preprocess", preprocess_node)
    workflow.add_node("ocr", ocr_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("store", store_node)
    workflow.add_node("flag", flag_node)
    
    # Add sequential edges for the main processing flow
    workflow.add_edge("navigate", "download")
    workflow.add_edge("download", "preprocess")
    workflow.add_edge("preprocess", "ocr")
    workflow.add_edge("ocr", "extract")
    workflow.add_edge("extract", "validate")
    
    # Add conditional edges for validation routing
    workflow.add_conditional_edges(
        "validate",
        should_store_or_flag,
        {
            "store": "store",
            "flag": "flag",
        }
    )
    
    # Add terminal edges
    workflow.add_edge("store", END)
    workflow.add_edge("flag", END)
    
    # Set the entry point
    workflow.set_entry_point("navigate")
    
    # Compile and return the workflow
    return workflow.compile()


# Convenience function to get a compiled graph instance
_compiled_graph = None


def get_agent_graph() -> StateGraph:
    """Get or create the compiled agent graph.
    
    Returns:
        Compiled StateGraph workflow (cached)
    """
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_agent_graph()
    return _compiled_graph
