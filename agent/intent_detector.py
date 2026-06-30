"""Intent detection for VoyageOS."""

import logging
import re
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class IntentDetector:
    """Detect user intent: trip planning, travel knowledge, follow-up, or general."""

    # Keywords for each intent category
    TRIP_PLANNING_KEYWORDS = [
        "plan", "trip", "itinerary", "budget", "visit", "travel to",
        "weekend trip", "vacation", "holiday", "tour", "journey",
        "goa", "mumbai", "delhi", "bangalore", "chennai", "kolkata",
        "hyderabad", "pune", "jaipur", "agra", "varanasi", "kerala",
        "rajasthan", "himachal", "uttarakhand", "goa", "andaman",
        "japan", "thailand", "singapore", "dubai", "europe", "usa",
        "book", "reserve", "hotel", "flight", "train", "bus"
    ]

    TRAVEL_KNOWLEDGE_KEYWORDS = [
        "passport", "visa", "immigration", "customs", "travel insurance",
        "airport", "duty free", "foreign currency", "packing",
        "travel regulations", "transit visa", "schengen", "embassy",
        "travel document", "vaccination", "health insurance",
        "travel advisory", "entry requirements", "visa on arrival",
        "e-visisa", "tourist visa", "business visa", "work permit"
    ]

    GENERAL_TRAVEL_KEYWORDS = [
        "travel etiquette", "jet lag", "international roaming",
        "difference between", "what is", "how to", "tips for",
        "best time", "weather", "climate", "culture", "customs",
        "language", "currency", "money", "exchange rate",
        "safety", "security", "emergency", "health", "food",
        "cuisine", "shopping", "market", "transport", "getting around"
    ]

    FOLLOW_UP_KEYWORDS = [
        "which hotel", "which attraction", "recommend", "replace",
        "increase budget", "decrease budget", "reduce budget",
        "change", "modify", "update", "instead of", "alternative",
        "skip", "remove", "add", "best", "cheapest", "luxury",
        "family version", "adventure version", "move", "day 1",
        "day 2", "day 3", "sightseeing"
    ]

    def detect_intent(self, user_message: str, has_trip_context: bool = False) -> Tuple[str, float]:
        """
        Detect user intent from message.
        
        Args:
            user_message: User's message
            has_trip_context: Whether there's an active trip in context
            
        Returns:
            Tuple of (intent, confidence)
            Intent can be: "trip_planning", "travel_knowledge", "follow_up", "general"
        """
        message_lower = user_message.lower()
        
        # Check for follow-up first (if there's trip context)
        if has_trip_context:
            follow_up_score = self._calculate_keyword_score(message_lower, self.FOLLOW_UP_KEYWORDS)
            if follow_up_score > 0.3:
                return "follow_up", min(follow_up_score, 1.0)
        
        # Check for trip planning
        trip_planning_score = self._calculate_keyword_score(message_lower, self.TRIP_PLANNING_KEYWORDS)
        if trip_planning_score > 0.2:
            return "trip_planning", min(trip_planning_score, 1.0)
        
        # Check for travel knowledge (document-based)
        travel_knowledge_score = self._calculate_keyword_score(message_lower, self.TRAVEL_KNOWLEDGE_KEYWORDS)
        if travel_knowledge_score > 0.2:
            return "travel_knowledge", min(travel_knowledge_score, 1.0)
        
        # Check for general travel questions
        general_travel_score = self._calculate_keyword_score(message_lower, self.GENERAL_TRAVEL_KEYWORDS)
        if general_travel_score > 0.2:
            return "general", min(general_travel_score, 1.0)
        
        # Default to general if unclear
        return "general", 0.5

    def _calculate_keyword_score(self, text: str, keywords: list) -> float:
        """Calculate relevance score based on keyword matches."""
        if not text or not keywords:
            return 0.0
        
        matches = 0
        for keyword in keywords:
            if keyword in text:
                matches += 1
        
        # Normalize score (0 to 1)
        score = matches / len(keywords) if keywords else 0
        return min(score * 5, 1.0)  # Amplify score but cap at 1.0

    def is_travel_related(self, user_message: str) -> bool:
        """
        Check if message is travel-related.
        
        Args:
            user_message: User's message
            
        Returns:
            True if travel-related, False otherwise
        """
        message_lower = user_message.lower()
        
        all_keywords = (
            self.TRIP_PLANNING_KEYWORDS +
            self.TRAVEL_KNOWLEDGE_KEYWORDS +
            self.GENERAL_TRAVEL_KEYWORDS +
            self.FOLLOW_UP_KEYWORDS
        )
        
        for keyword in all_keywords:
            if keyword in message_lower:
                return True
        
        return False

    def get_intent_description(self, intent: str) -> str:
        """Get human-readable description of intent."""
        descriptions = {
            "trip_planning": "Planning a new trip",
            "travel_knowledge": "Asking about travel documents/regulations",
            "follow_up": "Modifying previous trip",
            "general": "General travel question"
        }
        return descriptions.get(intent, "Unknown intent")