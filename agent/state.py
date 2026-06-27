from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class UserProfile:
    name: str = ""
    food_preference: str = ""
    travel_style: str = ""
    preferred_hotel: str = ""


@dataclass
class TripDetails:
    origin: str = ""
    destination: str = ""
    budget: float = 0.0
    travelers: int = 1
    trip_type: str = ""

    duration: int = 0      # NEW

    start_date: str = ""
    end_date: str = ""

@dataclass
class TravelState:

    # Chat History
    messages: List[Dict[str, str]] = field(default_factory=list)

    # User Preferences
    profile: UserProfile = field(default_factory=UserProfile)

    # Current Trip
    trip: TripDetails = field(default_factory=TripDetails)

    # Tool Outputs
    tool_results: Dict[str, Any] = field(default_factory=dict)

    # Uploaded PDFs
    uploaded_documents: List[str] = field(default_factory=list)

    # Retrieved Context
    rag_context: str = ""

    # Current Planner Step
    current_step: str = "start"

    # Errors
    errors: List[str] = field(default_factory=list)