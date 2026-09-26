from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException, status


class ADRIEException(HTTPException):
    """Base custom exception for the ADRIE application."""

    def __init__(self, status_code: int, detail: Any, entity_id: Optional[UUID] = None):
        """Initialize the ADRIEException."""
        super().__init__(status_code=status_code, detail=detail)
        self.entity_id = entity_id # Store entity_id


class MissionNotFoundException(ADRIEException):
    """Raised when a specified mission ID is not found."""

    def __init__(self, entity_id: UUID): # Changed from mission_id to entity_id for consistency
        """Initialize the MissionNotFoundException."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission with ID {entity_id} not found.",
            entity_id=entity_id # Pass entity_id to base class
        )

class VictimNotFoundException(ADRIEException):
    """Raised when a specified victim ID is not found."""

    def __init__(self, entity_id: UUID):
        """Initialize the VictimNotFoundException."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Victim with ID {entity_id} not found.",
            entity_id=entity_id # Pass entity_id to base class
        )

class AgentNotFoundException(ADRIEException):
    """Raised when a specified agent ID is not found."""

    def __init__(self, entity_id: UUID):
        """Initialize the AgentNotFoundException."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {entity_id} not found.",
            entity_id=entity_id # Pass entity_id to base class
        )

class MissionConflictException(ADRIEException):
    """Raised when an attempt is made to create a mission with an existing ID."""

    def __init__(self, mission_id: UUID):
        """Initialize the MissionConflictException."""
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Mission with ID {mission_id} already exists. "
                "Please choose a different ID or reset."
            ),
            entity_id=mission_id # Pass mission_id to base class
        )


class ServiceInitializationException(ADRIEException):
    """Raised when a service fails to initialize correctly."""

    def __init__(self, service_name: str, detail: Any = "Initialization failed."):
        """Initialize the ServiceInitializationException."""
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service '{service_name}' failed to initialize: {detail}",
        )


class PlanningException(ADRIEException):
    """Raised for errors during the planning process."""

    def __init__(self, detail: Any):
        """Initialize the PlanningException."""
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Planning failed: {detail}",
        )


class ExplanationNotImplementedException(ADRIEException):
    """Raised when an explanation type is requested but not implemented."""

    def __init__(self, explanation_type: str):
        """Initialize the ExplanationNotImplementedException."""
        super().__init__(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Explanation type '{explanation_type}' not fully implemented yet.",
        )


class MetricsCalculationException(ADRIEException):
    """Raised when there is an error during metrics calculation."""

    def __init__(self, detail: Any):
        """Initialize the MetricsCalculationException."""
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics calculation failed: {detail}",
        )


class InvalidExplanationRequestException(ADRIEException):
    """Raised when an explanation request is invalid (e.g., missing decision_id)."""

    def __init__(self, detail: Any):
        """Initialize the InvalidExplanationRequestException."""
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid explanation request: {detail}",
        )