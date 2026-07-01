"""Main VoyageOS Assistant integrating planner, RAG, and memory."""

import json
import logging
import uuid
import re
from typing import Dict, Optional, List, Any
from agent.travel_agent import TravelAgent
from agent.intent_detector import IntentDetector
from rag.rag_pipeline import RAGPipeline
from memory.database import Database
from memory.history import ConversationHistory, TripHistory

logger = logging.getLogger(__name__)


class DayPlan:
    """Structured day itinerary."""
    
    def __init__(self, day_number: int = 0, content: str = ""):
        self.day_number = day_number
        self.content = content
    
    def to_dict(self) -> Dict:
        return {
            'day_number': self.day_number,
            'content': self.content
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DayPlan':
        day = cls()
        day.day_number = data.get('day_number', 0)
        day.content = data.get('content', '')
        return day


class CurrentTrip:
    """Canonical trip data structure - single source of truth."""
    
    def __init__(self):
        self.origin: str = ""
        self.destination: str = ""
        self.budget: float = 0.0
        self.duration: int = 0
        self.travelers: int = 0
        self.trip_type: str = ""
        self.weather: Dict = {}
        self.transport: Dict = {}
        self.hotels: List[Dict] = []
        self.attractions: List[Dict] = []
        self.budget_breakdown: Dict = {}
        self.day_plans: List[DayPlan] = []
        self.packing_list: str = ""
        self.local_tips: str = ""
        self.safety_tips: str = ""
        self.itinerary_markdown: str = ""
        self.generated_at: str = ""
        self.pdf_path: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'origin': self.origin,
            'destination': self.destination,
            'budget': self.budget,
            'duration': self.duration,
            'travelers': self.travelers,
            'trip_type': self.trip_type,
            'weather': self.weather,
            'transport': self.transport,
            'hotels': self.hotels,
            'attractions': self.attractions,
            'budget_breakdown': self.budget_breakdown,
            'day_plans': [day.to_dict() for day in self.day_plans],
            'packing_list': self.packing_list,
            'local_tips': self.local_tips,
            'safety_tips': self.safety_tips,
            'itinerary_markdown': self.itinerary_markdown,
            'generated_at': self.generated_at,
            'pdf_path': self.pdf_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CurrentTrip':
        """Create from dictionary."""
        trip = cls()
        trip.origin = data.get('origin', '')
        trip.destination = data.get('destination', '')
        trip.budget = data.get('budget', 0.0)
        trip.duration = data.get('duration', 0)
        trip.travelers = data.get('travelers', 0)
        trip.trip_type = data.get('trip_type', '')
        trip.weather = data.get('weather', {})
        trip.transport = data.get('transport', {})
        trip.hotels = data.get('hotels', [])
        trip.attractions = data.get('attractions', [])
        trip.budget_breakdown = data.get('budget_breakdown', {})
        trip.day_plans = [DayPlan.from_dict(d) for d in data.get('day_plans', [])]
        trip.packing_list = data.get('packing_list', '')
        trip.local_tips = data.get('local_tips', '')
        trip.safety_tips = data.get('safety_tips', '')
        trip.itinerary_markdown = data.get('itinerary_markdown', '')
        trip.generated_at = data.get('generated_at', '')
        trip.pdf_path = data.get('pdf_path', '')
        return trip


class VoyageOSAssistant:
    """Main assistant class combining trip planning and travel knowledge."""

    # Assistant states
    STATE_IDLE = "idle"
    STATE_COLLECTING_TRIP = "collecting_trip"
    STATE_ITINERARY_READY = "itinerary_ready"
    STATE_MODIFYING_TRIP = "modifying_trip"
    STATE_AWAITING_CONFIRMATION = "awaiting_confirmation"

    # Follow-up intents (mutually exclusive)
    FOLLOW_UP_HOTEL_RECOMMENDATION = "hotel_recommendation"
    FOLLOW_UP_HOTEL_REPLACEMENT = "hotel_replacement"
    FOLLOW_UP_HOTEL_DETAILS = "hotel_details"
    FOLLOW_UP_SHOW_HOTELS = "show_hotels"
    FOLLOW_UP_ANOTHER_HOTEL = "another_hotel"
    FOLLOW_UP_ATTRACTION_RECOMMENDATION = "attraction_recommendation"
    FOLLOW_UP_ATTRACTION_REPLACEMENT = "attraction_replacement"
    FOLLOW_UP_SHOW_ATTRACTIONS = "show_attractions"
    FOLLOW_UP_ANOTHER_ATTRACTION = "another_attraction"
    FOLLOW_UP_TRANSPORT_RECOMMENDATION = "transport_recommendation"
    FOLLOW_UP_ANOTHER_TRANSPORT = "another_transport"
    FOLLOW_UP_EXPLAIN_LAST = "explain_last"
    FOLLOW_UP_WEATHER = "weather"
    FOLLOW_UP_BUDGET_UPDATE = "budget_update"
    FOLLOW_UP_DURATION_UPDATE = "duration_update"
    FOLLOW_UP_TRAVELER_UPDATE = "traveler_update"
    FOLLOW_UP_TRIP_TYPE_UPDATE = "trip_type_update"
    FOLLOW_UP_SHOW_DAY = "show_day"
    FOLLOW_UP_REPLACE_DAY = "replace_day"
    FOLLOW_UP_PACKING = "packing"
    FOLLOW_UP_LOCAL_TIPS = "local_tips"
    FOLLOW_UP_SUMMARY = "summary"
    FOLLOW_UP_DOWNLOAD_PDF = "download_pdf"

    # Pending actions
    PENDING_NONE = None
    PENDING_REGENERATE_BUDGET = "regenerate_budget"
    PENDING_REGENERATE_DURATION = "regenerate_duration"
    PENDING_REPLACE_DAY = "replace_day"
    PENDING_REPLACE_HOTEL = "replace_hotel"
    PENDING_REPLACE_TRANSPORT = "replace_transport"
    PENDING_REPLACE_ATTRACTION = "replace_attraction"

    def __init__(self):
        """Initialize VoyageOS assistant with all components."""
        self.session_id = str(uuid.uuid4())
        
        # Initialize components
        self.travel_agent = TravelAgent()
        self.intent_detector = IntentDetector()
        self.rag_pipeline = RAGPipeline()
        
        # Initialize database
        self.database = Database()
        self.conversation_history = ConversationHistory(self.database)
        self.trip_history = TripHistory(self.database)
        
        # Conversation state
        self.state = self.STATE_IDLE
        self.current_trip = CurrentTrip()  # Canonical trip object
        self.pending_action = self.PENDING_NONE
        self.last_recommendation = None  # Track last recommendation for follow-up "why?"
        self.travel_context = {}  # Store nationality, purpose, etc. for Travel Knowledge
        
        logger.info(f"VoyageOS Assistant initialized with session {self.session_id}")

    def process_message(self, user_message: str) -> Dict:
        """
        Process user message with state-aware routing.
        
        Args:
            user_message: User's input message
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Check if awaiting confirmation
            if self.state == self.STATE_AWAITING_CONFIRMATION:
                return self._handle_confirmation(user_message)
            
            # STATE MACHINE: Route based on current state
            if self.state == self.STATE_COLLECTING_TRIP:
                return self._handle_collecting_trip(user_message)
            elif self.state == self.STATE_ITINERARY_READY:
                return self._handle_itinerary_ready(user_message)
            elif self.state == self.STATE_MODIFYING_TRIP:
                return self._handle_modifying_trip(user_message)
            else:  # STATE_IDLE
                return self._handle_idle(user_message)
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            error_response = "I apologize, but I encountered an unexpected error. Please try again."
            self._save_conversation(user_message, error_response)
            return {
                "status": "error",
                "response": error_response,
                "session_id": self.session_id
            }

    def _regenerate_itinerary(self) -> Dict:
        """Re-run travel agent with current trip data to regenerate itinerary."""
        try:
            import time
            start_time = time.time()
            logger.info("[Regeneration] START")
            
            # Reset agent state to prevent context bleed (fixes Groq 413)
            self.travel_agent.state.messages = []
            self.travel_agent.state.tool_results = {}
            self._sync_trip_to_agent()
            
            # Build minimal prompt with ONLY trip parameters — no tool results, no chat history
            prompt = f"""You are VoyageOS, a premium travel consultant. Generate a complete travel itinerary.

TRIP PARAMETERS:
- Origin: {self.current_trip.origin}
- Destination: {self.current_trip.destination}
- Duration: {self.current_trip.duration} days
- Budget: ₹{self.current_trip.budget:,.0f}
- Travelers: {self.current_trip.travelers}
- Trip Type: {self.current_trip.trip_type}

Generate a premium, day-wise itinerary with:
- Budget allocation
- Hotel recommendations (3-5 best options)
- Attraction recommendations (5-8 best options)
- Transport options
- Weather-appropriate packing list
- Local tips
- Safety advice

Write in a professional travel guide style. Use markdown formatting."""
            
            prompt_tokens = len(prompt.split())
            logger.info(f"[Regeneration] Prompt built: ~{prompt_tokens} words, ~{int(prompt_tokens * 1.3)} tokens")
            
            # Call LLM directly with minimal prompt — bypass build_prompt() to avoid huge context
            llm_start = time.time()
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            llm_time = time.time() - llm_start
            logger.info(f"[Regeneration] LLM response received in {llm_time:.2f}s")
            
            assistant_message = response.content
            
            # Build minimal result dict for _complete_trip_planning
            result = {
                "status": "completed",
                "message": assistant_message,
                "tool_results": {}  # Will be populated by _complete_trip_planning from CurrentTrip
            }
            
            # Reuse existing tool results from CurrentTrip instead of re-running tools
            if self.current_trip.hotels or self.current_trip.attractions or self.current_trip.transport or self.current_trip.weather:
                logger.info("[Regeneration] Reusing existing tool results from CurrentTrip")
                result["tool_results"] = {
                    "hotel": self.current_trip.hotels,
                    "places": self.current_trip.attractions,
                    "transport": self.current_trip.transport,
                    "weather": self.current_trip.weather,
                    "budget": self.current_trip.budget_breakdown
                }
            
            self._complete_trip_planning(result)
            
            total_time = time.time() - start_time
            logger.info(f"[Regeneration] COMPLETE in {total_time:.2f}s")
            
            return {
                "status": "completed",
                "response": assistant_message,
                "session_id": self.session_id
            }
        except Exception as e:
            logger.error(f"Regeneration failed: {str(e)}", exc_info=True)
            self.state = self.STATE_ITINERARY_READY
            return {
                "status": "completed",
                "response": "I encountered an error while regenerating. Please try again.",
                "session_id": self.session_id
            }

    def _handle_confirmation(self, user_message: str) -> Dict:
        """Handle yes/no confirmations."""
        message_lower = user_message.lower()
        
        # Check for affirmative responses
        if any(word in message_lower for word in ["yes", "yeah", "yep", "sure", "okay", "go ahead", "proceed", "y", "generate"]):
            if self.pending_action in (self.PENDING_REGENERATE_BUDGET, self.PENDING_REGENERATE_DURATION):
                self.pending_action = self.PENDING_NONE
                return self._regenerate_itinerary()
            else:
                self.state = self.STATE_ITINERARY_READY
                self.pending_action = self.PENDING_NONE
                response = "Great! Let me know if you need anything else."
                self._save_conversation(user_message, response)
                return {
                    "status": "completed",
                    "response": response,
                    "session_id": self.session_id
                }
        else:
            self.state = self.STATE_ITINERARY_READY
            self.pending_action = self.PENDING_NONE
            response = "No problem! Let me know if you'd like to make any other changes."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }

    def _handle_idle(self, user_message: str) -> Dict:
        """Handle messages when assistant is idle."""
        logger.info("State: IDLE - Running intent detection")
        
        # Check if travel-related
        if not self.intent_detector.is_travel_related(user_message):
            response = (
                "I'm designed specifically to help with travel planning, destinations, visas, "
                "transportation, itineraries, and travel knowledge. I can't assist with programming, "
                "math, or other non-travel topics. Please ask me about travel!"
            )
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        # Detect intent
        intent, confidence = self.intent_detector.detect_intent(user_message)
        logger.info(f"Detected intent: {intent} (confidence: {confidence:.2f})")
        
        # Route based on intent
        if intent == "trip_planning":
            return self._start_trip_planning(user_message)
        elif intent == "travel_knowledge":
            return self._handle_travel_knowledge(user_message)
        elif intent == "follow_up":
            # Try to load previous trip from SQLite
            self._load_trip_from_history()
            if self.current_trip and self.current_trip.destination:
                self.state = self.STATE_ITINERARY_READY
                return self._handle_itinerary_ready(user_message)
            else:
                response = "I don't have a previous trip to reference. Would you like to plan a new trip?"
                self._save_conversation(user_message, response)
                return {
                    "status": "completed",
                    "response": response,
                    "session_id": self.session_id
                }
        else:  # general
            return self._handle_general_travel(user_message)

    def _start_trip_planning(self, user_message: str) -> Dict:
        """Start trip planning flow."""
        logger.info("Starting trip planning")
        
        # Reset state
        self.state = self.STATE_COLLECTING_TRIP
        self.current_trip = CurrentTrip()
        self.pending_action = self.PENDING_NONE
        
        # Initialize travel agent state
        self.travel_agent.state.trip.origin = None
        self.travel_agent.state.trip.destination = None
        self.travel_agent.state.trip.budget = None
        self.travel_agent.state.trip.duration = None
        self.travel_agent.state.trip.travelers = None
        self.travel_agent.state.trip.trip_type = None
        
        # Process with planner to extract initial info
        result = self.travel_agent.chat(user_message)
        
        # Update current trip with extracted info
        self._sync_trip_from_agent()
        
        # If planner needs more info, it will return collecting_information
        if result.get("status") == "collecting_information":
            self._save_conversation(user_message, result["message"])
            return {
                "status": "collecting_information",
                "response": result["message"],
                "session_id": self.session_id
            }
        else:
            # Trip completed
            self._complete_trip_planning(result)
            return {
                "status": "completed",
                "response": result["message"],
                "session_id": self.session_id
            }

    def _handle_collecting_trip(self, user_message: str) -> Dict:
        """Handle messages while collecting trip details."""
        logger.info("State: COLLECTING_TRIP - Continuing planner flow")
        
        # Feed message directly to planner
        result = self.travel_agent.chat(user_message)
        
        # Update current trip with extracted info
        self._sync_trip_from_agent()
        
        # Check if trip is complete
        if result.get("status") == "completed":
            self._complete_trip_planning(result)
            return {
                "status": "completed",
                "response": result["message"],
                "session_id": self.session_id
            }
        else:
            # Still collecting
            self._save_conversation(user_message, result["message"])
            return {
                "status": "collecting_information",
                "response": result["message"],
                "session_id": self.session_id
            }

    def _sync_trip_from_agent(self):
        """Sync CurrentTrip from TravelAgent state."""
        self.current_trip.origin = self.travel_agent.state.trip.origin or ""
        self.current_trip.destination = self.travel_agent.state.trip.destination or ""
        self.current_trip.budget = self.travel_agent.state.trip.budget or 0.0
        self.current_trip.duration = self.travel_agent.state.trip.duration or 0
        self.current_trip.travelers = self.travel_agent.state.trip.travelers or 0
        self.current_trip.trip_type = self.travel_agent.state.trip.trip_type or ""
    
    def _sync_trip_to_agent(self):
        """Sync CurrentTrip to TravelAgent state."""
        try:
            self.travel_agent.state.trip.origin = self.current_trip.origin if self.current_trip.origin else None
            self.travel_agent.state.trip.destination = self.current_trip.destination if self.current_trip.destination else None
            self.travel_agent.state.trip.budget = self.current_trip.budget if self.current_trip.budget > 0 else None
            self.travel_agent.state.trip.duration = self.current_trip.duration if self.current_trip.duration > 0 else None
            self.travel_agent.state.trip.travelers = self.current_trip.travelers if self.current_trip.travelers > 0 else None
            self.travel_agent.state.trip.trip_type = self.current_trip.trip_type if self.current_trip.trip_type else None
            logger.info(f"Synced trip to agent state: {self.current_trip.destination}")
        except Exception as e:
            logger.error(f"Failed to sync trip to agent: {str(e)}")

    def _complete_trip_planning(self, result: Dict):
        """Complete trip planning and save to history."""
        logger.info("Trip planning completed")
        
        # Extract structured data from tool results
        tool_results = result.get("tool_results", {})
        
        # Log what we received for debugging
        logger.info(f"Tool results keys: {list(tool_results.keys()) if tool_results else 'None'}")
        
        # Update current trip with tool data
        self.current_trip.weather = self._extract_weather(tool_results.get('weather', {}))
        self.current_trip.transport = self._extract_transport(tool_results.get('transport', {}))
        self.current_trip.hotels = self._extract_hotels(tool_results.get('hotel', []))
        self.current_trip.attractions = self._extract_attractions(tool_results.get('places', []))
        self.current_trip.budget_breakdown = self._extract_budget(tool_results.get('budget', {}))
        self.current_trip.itinerary_markdown = result["message"]
        self.current_trip.generated_at = str(uuid.uuid4())
        
        # Parse day itinerary from markdown
        self.current_trip.day_plans = self._parse_days_from_itinerary(result["message"])
        
        # Extract packing, tips, safety from markdown
        self._extract_additional_info(result["message"])
        
        # VALIDATE: Ensure CurrentTrip is properly populated
        self._validate_current_trip()
        
        # Save to SQLite
        self._save_trip_to_history()
        
        # Generate PDF automatically
        self._generate_trip_pdf()
        
        # Update state
        self.state = self.STATE_ITINERARY_READY

    def _validate_current_trip(self):
        """Validate that CurrentTrip has been properly populated."""
        logger.info("Validating CurrentTrip...")
        
        # Log what we have
        logger.info(f"Hotels stored: {len(self.current_trip.hotels)}")
        logger.info(f"Attractions stored: {len(self.current_trip.attractions)}")
        logger.info(f"Day plans stored: {len(self.current_trip.day_plans)}")
        logger.info(f"Transport stored: {'Yes' if self.current_trip.transport else 'No'}")
        logger.info(f"Weather stored: {'Yes' if self.current_trip.weather else 'No'}")
        
        # Validation checks
        warnings = []
        
        if len(self.current_trip.hotels) == 0:
            warnings.append("No hotels found in tool results")
        
        if len(self.current_trip.attractions) == 0:
            warnings.append("No attractions found in tool results")
        
        if len(self.current_trip.day_plans) == 0:
            warnings.append("No day plans parsed from itinerary")
        
        if not self.current_trip.transport:
            warnings.append("No transport information found")
        
        if not self.current_trip.weather:
            warnings.append("No weather information found")
        
        if warnings:
            logger.warning("CurrentTrip validation issues:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
            logger.warning("Itinerary was generated but structured data may be incomplete")

    def _generate_trip_pdf(self):
        """Generate PDF from current trip data."""
        try:
            from utils.pdf_generator import PDFGenerator
            import os
            from datetime import datetime
            
            # Create filename: VoyageOS_<destination>_Plan.pdf
            destination = self.current_trip.destination or "Trip"
            # Sanitize destination for filename (remove special chars, replace spaces with underscores)
            safe_destination = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in destination)
            safe_destination = safe_destination.replace(' ', '_').replace('-', '_')
            
            filename = f"VoyageOS_{safe_destination}_Plan.pdf"
            file_path = os.path.join("downloads", filename)
            
            # Ensure downloads directory exists
            os.makedirs("downloads", exist_ok=True)
            
            # Prepare state data for PDF generator
            state_data = {
                "trip_details": {
                    "origin": self.current_trip.origin,
                    "destination": self.current_trip.destination,
                    "budget": self.current_trip.budget,
                    "duration": self.current_trip.duration,
                    "travelers": self.current_trip.travelers,
                    "trip_type": self.current_trip.trip_type
                },
                "tool_results": {
                    "budget": self.current_trip.budget_breakdown
                },
                "message": self.current_trip.itinerary_markdown
            }
            
            # Generate PDF
            pdf_path = PDFGenerator.create_itinerary_pdf(state_data, file_path)
            
            # Store PDF path in current trip for reference
            self.current_trip.pdf_path = pdf_path
            
            logger.info(f"PDF generated successfully: {pdf_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {str(e)}", exc_info=True)
            # Don't fail the entire trip planning if PDF generation fails
            self.current_trip.pdf_path = None

    def _extract_weather(self, weather_data: Dict) -> Dict:
        """Extract weather information."""
        if not weather_data:
            return {}
        return {
            'temperature': weather_data.get('temperature', 'N/A'),
            'condition': weather_data.get('condition', 'N/A'),
            'humidity': weather_data.get('humidity', 'N/A'),
            'wind_speed': weather_data.get('wind_speed', 'N/A')
        }

    def _extract_transport(self, transport_data: Dict) -> Dict:
        """Extract transport options."""
        if not transport_data:
            return {}
        
        options = {}
        for mode in ['flight', 'train', 'bus']:
            if mode in transport_data and transport_data[mode]:
                mode_data = transport_data[mode]
                if isinstance(mode_data, dict) and mode_data.get('summary', {}).get('found'):
                    options[mode] = {
                        'available': True,
                        'duration': mode_data.get('summary', {}).get('duration', 'N/A'),
                        'price_range': mode_data.get('summary', {}).get('price_range', 'N/A'),
                        'operators': mode_data.get('summary', {}).get('operators', [])
                    }
        
        return options

    def _extract_hotels(self, hotels_data: List) -> List[Dict]:
        """Extract hotel list."""
        if not hotels_data or not isinstance(hotels_data, list):
            logger.warning(f"Hotels data is empty or not a list: {type(hotels_data)}")
            return []
        
        extracted = []
        for hotel in hotels_data[:5]:  # Top 5 hotels
            if isinstance(hotel, dict):
                # Prefer English name, fall back to local name
                name = hotel.get('name:en') or hotel.get('name', 'Unknown Hotel')
                extracted.append({
                    'name': name,
                    'address': hotel.get('address', 'Address not available'),
                    'price': hotel.get('price', 'N/A'),
                    'rating': hotel.get('rating', 'N/A')
                })
        
        logger.info(f"Extracted {len(extracted)} hotels from tool results")
        return extracted

    def _extract_attractions(self, places_data: List) -> List[Dict]:
        """Extract attraction list."""
        if not places_data or not isinstance(places_data, list):
            logger.warning(f"Places data is empty or not a list: {type(places_data)}")
            return []
        
        extracted = []
        for place in places_data[:10]:  # Top 10 attractions
            if isinstance(place, dict):
                # Prefer English name, fall back to local name
                name = place.get('name:en') or place.get('name', 'Unknown Attraction')
                extracted.append({
                    'name': name,
                    'category': place.get('category', 'Attraction'),
                    'description': place.get('description', ''),
                    'address': place.get('address', '')
                })
        
        logger.info(f"Extracted {len(extracted)} attractions")
        return extracted

    def _extract_budget(self, budget_data: Dict) -> Dict:
        """Extract budget breakdown."""
        if not budget_data:
            return {}
        
        allocation = budget_data.get('allocation', {})
        return {
            'total_budget': budget_data.get('total_budget', 0),
            'budget_tier': budget_data.get('context', {}).get('budget_tier', ''),
            'allocation': allocation
        }

    def _parse_days_from_itinerary(self, markdown: str) -> List[DayPlan]:
        """Parse individual days from itinerary markdown."""
        days = []
        lines = markdown.split('\n')
        current_day_lines = []
        current_day_num = 0
        day_number_word_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        
        for line in lines:
            # Check for day header — support: "Day 1", "Day 1 —", "Day One", "DAY 1", "Day 1:", "## Day 1"
            day_match = re.search(r'(?:^|#+\s*)(?:Day|DAY|day)\s*[:\s]*(\d+|[Oo]ne|[Tt]wo|[Tt]hree|[Ff]our|[Ff]ive)', line)
            if day_match:
                day_raw = day_match.group(1)
                # Try numeric first, then word
                try:
                    new_day_num = int(day_raw)
                except ValueError:
                    new_day_num = day_number_word_map.get(day_raw.lower(), 0)
                # Save previous day
                if current_day_lines and current_day_num > 0:
                    days.append(DayPlan(
                        day_number=current_day_num,
                        content='\n'.join(current_day_lines)
                    ))
                # Start new day
                current_day_num = new_day_num
                current_day_lines = [line]
            elif current_day_num > 0:
                current_day_lines.append(line)
        
        # Save last day
        if current_day_lines and current_day_num > 0:
            days.append(DayPlan(
                day_number=current_day_num,
                content='\n'.join(current_day_lines)
            ))
        
        logger.info(f"Parsed {len(days)} day plans from itinerary")
        return days

    def _extract_additional_info(self, markdown: str):
        """Extract packing, tips, safety from markdown."""
        sections = {
            'packing_list': r'PACKING LIST(.*?)(?=##|\Z)',
            'local_tips': r'LOCAL TIPS(.*?)(?=##|\Z)',
            'safety_tips': r'SAFETY TIPS(.*?)(?=##|\Z)'
        }
        
        for key, pattern in sections.items():
            match = re.search(pattern, markdown, re.IGNORECASE | re.DOTALL)
            if match:
                setattr(self.current_trip, key, match.group(1).strip())

    def _handle_itinerary_ready(self, user_message: str) -> Dict:
        """Handle messages when itinerary is ready."""
        logger.info("State: ITINERARY_READY - Checking for follow-up or new query")
        
        # Ensure we have current trip loaded
        if not self.current_trip or not self.current_trip.destination:
            self._load_trip_from_history()
        
        if not self.current_trip or not self.current_trip.destination:
            # No trip context, treat as new query
            return self._handle_idle(user_message)
        
        # Check if this is a follow-up question
        follow_up_type = self._detect_follow_up_type(user_message)
        
        if follow_up_type:
            logger.info(f"Detected follow-up: {follow_up_type}")
            return self._handle_follow_up(user_message, follow_up_type)
        else:
            # Not a follow-up, check if it's a new trip planning request
            intent, confidence = self.intent_detector.detect_intent(user_message)
            
            if intent == "trip_planning" and confidence > 0.3:
                # Start new trip
                logger.info("Starting new trip planning")
                self.state = self.STATE_COLLECTING_TRIP
                self.current_trip = CurrentTrip()
                self.pending_action = self.PENDING_NONE
                return self._start_trip_planning(user_message)
            elif intent == "travel_knowledge":
                # RAG question
                return self._handle_travel_knowledge(user_message)
            elif intent == "general":
                # General travel question
                return self._handle_general_travel(user_message)
            else:
                # Unclear - treat as general question
                return self._handle_general_travel(user_message)

    def _detect_follow_up_type(self, user_message: str) -> Optional[str]:
        """
        Detect follow-up type from user message.
        Returns None if not a follow-up, otherwise returns the follow-up type.
        """
        message_lower = user_message.lower()
        
        if not self.current_trip or not self.current_trip.destination:
            return None
        
        # "Why?" / "Tell me more" / "Explain" — use last recommendation if available
        if self.last_recommendation:
            explain_phrases = [
                "why", "tell me more", "explain", "why this", "why that",
                "why would you", "is it worth", "is it good", "would you recommend",
                "should i", "what makes it", "tell me about it", "more details",
                "why first", "why visit", "why stay", "why recommend",
                "how expensive", "is it suitable", "would you stay"
            ]
            if any(phrase in message_lower for phrase in explain_phrases):
                return self.FOLLOW_UP_EXPLAIN_LAST
        
        # Hotel-related
        if any(phrase in message_lower for phrase in ["which hotel", "recommend hotel", "best hotel", "suggest hotel"]):
            return self.FOLLOW_UP_HOTEL_RECOMMENDATION
        if any(phrase in message_lower for phrase in ["another hotel", "different hotel", "other hotel", "next hotel"]):
            return self.FOLLOW_UP_ANOTHER_HOTEL
        if any(phrase in message_lower for phrase in ["replace hotel", "change hotel", "different hotel", "another hotel"]):
            return self.FOLLOW_UP_HOTEL_REPLACEMENT
        if any(phrase in message_lower for phrase in ["why this hotel", "tell me about hotel", "hotel details", "explain hotel"]):
            return self.FOLLOW_UP_HOTEL_DETAILS
        if any(phrase in message_lower for phrase in ["show all hotel", "list hotel", "all hotels"]):
            return self.FOLLOW_UP_SHOW_HOTELS
        
        # Attraction-related
        if any(phrase in message_lower for phrase in ["which attraction", "which place", "recommend attraction", "best attraction", "visit first", "attraction should"]):
            return self.FOLLOW_UP_ATTRACTION_RECOMMENDATION
        if any(phrase in message_lower for phrase in ["another attraction", "different attraction", "other attraction", "next attraction", "another place", "different place"]):
            return self.FOLLOW_UP_ANOTHER_ATTRACTION
        if any(phrase in message_lower for phrase in ["replace attraction", "change attraction", "different attraction"]):
            return self.FOLLOW_UP_ATTRACTION_REPLACEMENT
        if any(phrase in message_lower for phrase in ["show all attraction", "list attraction", "all attractions", "show attractions"]):
            return self.FOLLOW_UP_SHOW_ATTRACTIONS
        
        # Transport
        if any(phrase in message_lower for phrase in ["which transport", "best transport", "recommend transport", "how to travel", "transport option"]):
            return self.FOLLOW_UP_TRANSPORT_RECOMMENDATION
        if any(phrase in message_lower for phrase in ["another transport", "different transport", "other transport", "next transport"]):
            return self.FOLLOW_UP_ANOTHER_TRANSPORT
        
        # Weather
        if any(phrase in message_lower for phrase in ["weather", "temperature", "rain", "forecast"]):
            return self.FOLLOW_UP_WEATHER
        
        # Budget
        if any(phrase in message_lower for phrase in ["increase budget", "decrease budget", "reduce budget", "budget to", "budget becomes", "make it cheaper", "make it expensive"]):
            return self.FOLLOW_UP_BUDGET_UPDATE
        
        # Duration
        if any(phrase in message_lower for phrase in ["increase duration", "decrease duration", "reduce duration", "extend trip", "more days", "less days"]):
            return self.FOLLOW_UP_DURATION_UPDATE
        
        # Travelers
        if any(phrase in message_lower for phrase in ["more people", "less people", "add traveler", "remove traveler", "people travelling"]):
            return self.FOLLOW_UP_TRAVELER_UPDATE
        
        # Trip type
        if any(phrase in message_lower for phrase in ["make it family", "make it solo", "make it honeymoon", "make it friends", "change trip type", "make it a family"]):
            return self.FOLLOW_UP_TRIP_TYPE_UPDATE
        
        # Travel Knowledge — check BEFORE day detection to prevent misrouting
        travel_knowledge_keywords = [
            "visa", "passport", "airport", "boarding", "check-in", "check in",
            "security", "immigration", "customs", "currency", "cash", "atm",
            "sim", "insurance", "vaccination", "documents", "packing",
            "travel tips", "airport arrival", "power adapter", "entry requirements",
            "language", "local transport", "baggage", "luggage", "duty free",
            "terminal", "gate", "transit", "connecting flight"
        ]
        if any(kw in message_lower for kw in travel_knowledge_keywords):
            return self.FOLLOW_UP_PACKING  # Will be routed to travel knowledge in handle_follow_up
        
        # Show specific day — strict detection only
        # Must explicitly reference "show", "what", "today", "tomorrow" with "day"/"dya"/"itinerary"
        day_intent = False
        if "tomorrow" in message_lower and "day" not in message_lower:
            day_intent = True
        elif "today" in message_lower and "itinerary" in message_lower:
            day_intent = True
        elif "show" in message_lower and ("day" in message_lower or "dya" in message_lower):
            day_intent = True
        elif "what" in message_lower and ("day" in message_lower or "dya" in message_lower) and "plan" in message_lower:
            day_intent = True
        elif any(phrase in message_lower for phrase in ["second day", "third day", "first day", "fourth day", "fifth day"]):
            # Word-based days are always explicit day references
            day_intent = True
        elif re.search(r'(?:day|dya)\s*(\d+)', message_lower) and not any(
            w in message_lower for w in ["trip", "stay", "duration", "plan", "budget", "travel"]
        ):
            # "day 2" or "dya 2" — but NOT "3 day trip", "stay 5 days", etc.
            day_intent = True
        
        if day_intent:
            return self.FOLLOW_UP_SHOW_DAY
        
        # Replace day
        if any(phrase in message_lower for phrase in ["replace day", "change day", "modify day"]):
            return self.FOLLOW_UP_REPLACE_DAY
        
        # Packing
        if any(phrase in message_lower for phrase in ["packing", "what to pack", "pack list"]):
            return self.FOLLOW_UP_PACKING
        
        # Local tips
        if any(phrase in message_lower for phrase in ["local tips", "tips", "advice", "recommendations"]):
            return self.FOLLOW_UP_LOCAL_TIPS
        
        # Summary
        if any(phrase in message_lower for phrase in ["summary", "overview", "recap", "brief"]):
            return self.FOLLOW_UP_SUMMARY
        
        # Download PDF
        if any(phrase in message_lower for phrase in ["download", "pdf", "export", "save"]):
            return self.FOLLOW_UP_DOWNLOAD_PDF
        
        return None

    def _handle_follow_up(self, user_message: str, follow_up_type: str) -> Dict:
        """Handle follow-up questions using stored trip data."""
        logger.info(f"Handling follow-up: {follow_up_type}")
        
        try:
            # Route to specific handler
            if follow_up_type == self.FOLLOW_UP_HOTEL_RECOMMENDATION:
                return self._handle_hotel_recommendation(user_message)
            elif follow_up_type == self.FOLLOW_UP_HOTEL_REPLACEMENT:
                return self._handle_hotel_replacement(user_message)
            elif follow_up_type == self.FOLLOW_UP_HOTEL_DETAILS:
                return self._handle_hotel_details(user_message)
            elif follow_up_type == self.FOLLOW_UP_SHOW_HOTELS:
                return self._handle_show_hotels(user_message)
            elif follow_up_type == self.FOLLOW_UP_ANOTHER_HOTEL:
                return self._handle_another_hotel(user_message)
            elif follow_up_type == self.FOLLOW_UP_ATTRACTION_RECOMMENDATION:
                return self._handle_attraction_recommendation(user_message)
            elif follow_up_type == self.FOLLOW_UP_ATTRACTION_REPLACEMENT:
                return self._handle_attraction_replacement(user_message)
            elif follow_up_type == self.FOLLOW_UP_SHOW_ATTRACTIONS:
                return self._handle_show_attractions(user_message)
            elif follow_up_type == self.FOLLOW_UP_ANOTHER_ATTRACTION:
                return self._handle_another_attraction(user_message)
            elif follow_up_type == self.FOLLOW_UP_TRANSPORT_RECOMMENDATION:
                return self._handle_transport_recommendation(user_message)
            elif follow_up_type == self.FOLLOW_UP_ANOTHER_TRANSPORT:
                return self._handle_another_transport(user_message)
            elif follow_up_type == self.FOLLOW_UP_EXPLAIN_LAST:
                return self._handle_explain_last(user_message)
            elif follow_up_type == self.FOLLOW_UP_WEATHER:
                return self._handle_weather_info(user_message)
            elif follow_up_type == self.FOLLOW_UP_BUDGET_UPDATE:
                return self._handle_budget_update(user_message)
            elif follow_up_type == self.FOLLOW_UP_DURATION_UPDATE:
                return self._handle_duration_update(user_message)
            elif follow_up_type == self.FOLLOW_UP_SHOW_DAY:
                return self._handle_show_day(user_message)
            elif follow_up_type == self.FOLLOW_UP_REPLACE_DAY:
                return self._handle_replace_day(user_message)
            elif follow_up_type == self.FOLLOW_UP_PACKING:
                # Route travel knowledge keywords to Travel Knowledge handler
                travel_kw = ["visa", "passport", "airport", "boarding", "check-in", "check in",
                            "security", "immigration", "customs", "currency", "cash", "atm",
                            "sim", "insurance", "vaccination", "documents",
                            "travel tips", "airport arrival", "power adapter", "entry requirements",
                            "language", "local transport", "baggage", "luggage", "duty free",
                            "terminal", "gate", "transit", "connecting flight"]
                if any(kw in user_message.lower() for kw in travel_kw):
                    return self._handle_travel_knowledge(user_message)
                return self._handle_packing_info(user_message)
            elif follow_up_type == self.FOLLOW_UP_LOCAL_TIPS:
                return self._handle_local_tips(user_message)
            elif follow_up_type == self.FOLLOW_UP_SUMMARY:
                return self._handle_trip_summary(user_message)
            else:
                # Generic follow-up - use LLM with context
                return self._handle_generic_follow_up(user_message)
                
        except Exception as e:
            logger.error(f"Error in follow-up handling: {str(e)}", exc_info=True)
            error_response = "I couldn't process that follow-up. Could you try rephrasing or regenerate the trip?"
            self._save_conversation(user_message, error_response)
            return {
                "status": "completed",
                "response": error_response,
                "session_id": self.session_id
            }

    def _handle_another_hotel(self, user_message: str) -> Dict:
        """Recommend next hotel from stored options."""
        if not self.current_trip.hotels or len(self.current_trip.hotels) < 2:
            response = "I don't have another hotel recommendation at this time. The current hotel is my top suggestion for your trip."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        # Find next hotel after the current recommendation
        current_idx = 0
        if self.last_recommendation and self.last_recommendation.get("type") == "hotel":
            current_name = self.last_recommendation.get("data", {}).get("name", "")
            for i, h in enumerate(self.current_trip.hotels):
                if h.get("name") == current_name:
                    current_idx = i
                    break
        
        next_idx = (current_idx + 1) % len(self.current_trip.hotels)
        hotel = self.current_trip.hotels[next_idx]
        self.last_recommendation = {"type": "hotel", "data": hotel}
        
        name = hotel.get('name', 'Unknown Hotel')
        address = hotel.get('address', 'Address not available')
        
        prompt = f"""You are VoyageOS, a premium travel consultant. Recommend an alternative hotel.

Use ONLY the factual data below. You may improve wording and personalize, but do NOT invent details.

HOTEL DATA:
- Name: {name}
- Address: {address}

TRIP CONTEXT:
- Destination: {self.current_trip.destination}
- Budget: ₹{self.current_trip.budget:,.0f}
- Travelers: {self.current_trip.travelers}
- Trip Type: {self.current_trip.trip_type}

Write a concise, professional alternative hotel recommendation (3-5 sentences) with this structure:
1. Hotel name and area
2. Why it could be a good alternative
3. What makes it different from the previous recommendation
4. Who it might suit better

Be conversational but professional."""
        
        try:
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            answer = response.content
        except Exception:
            answer = f"**{name}** is another excellent option.\n\n📍 {address}\n\nThis alternative offers a different experience while still fitting your {self.current_trip.trip_type} trip and budget of ₹{self.current_trip.budget:,.0f}."
        
        self._save_conversation(user_message, answer)
        return {
            "status": "completed",
            "response": answer,
            "session_id": self.session_id
        }

    def _handle_another_attraction(self, user_message: str) -> Dict:
        """Recommend next attraction from stored options."""
        if not self.current_trip.attractions or len(self.current_trip.attractions) < 2:
            response = "I don't have another attraction recommendation at this time. The current attraction is my top suggestion for your trip."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        # Find next attraction after the current recommendation
        current_idx = 0
        if self.last_recommendation and self.last_recommendation.get("type") == "attraction":
            current_name = self.last_recommendation.get("data", {}).get("name", "")
            for i, p in enumerate(self.current_trip.attractions):
                if p.get("name") == current_name:
                    current_idx = i
                    break
        
        next_idx = (current_idx + 1) % len(self.current_trip.attractions)
        place = self.current_trip.attractions[next_idx]
        self.last_recommendation = {"type": "attraction", "data": place}
        
        name = place.get('name', 'Unknown Attraction')
        category = place.get('category', 'Attraction')
        description = place.get('description', '')
        
        prompt = f"""You are VoyageOS, a premium travel consultant. Recommend an alternative attraction.

Use ONLY the factual data below. You may improve wording and personalize, but do NOT invent details.

ATTRACTION DATA:
- Name: {name}
- Category: {category}
- Description: {description}

TRIP CONTEXT:
- Destination: {self.current_trip.destination}
- Trip Type: {self.current_trip.trip_type}

Write a concise, professional alternative attraction recommendation (3-5 sentences) with this structure:
1. Attraction name and what it is
2. Why it could be a good alternative
3. What makes it different from the previous recommendation
4. Best time to visit

Be conversational but professional."""
        
        try:
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            answer = response.content
        except Exception:
            answer = f"## {name}\n\n**Category:** {category}\n\n"
            if description:
                answer += f"{description}\n\n"
            answer += f"This is another great option for your {self.current_trip.trip_type} trip to {self.current_trip.destination}."
        
        self._save_conversation(user_message, answer)
        return {
            "status": "completed",
            "response": answer,
            "session_id": self.session_id
        }

    def _handle_another_transport(self, user_message: str) -> Dict:
        """Recommend next transport option from stored data."""
        if not self.current_trip.transport:
            response = "Transport information is not available for this trip."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        # Find next available mode after the current recommendation
        available_modes = [mode for mode, data in self.current_trip.transport.items() if data.get('available')]
        if not available_modes:
            response = "No other transport options are available for this trip."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        current_mode = None
        if self.last_recommendation and self.last_recommendation.get("type") == "transport":
            current_mode = self.last_recommendation.get("data", {}).get("mode")
        
        # Find next mode in list
        next_mode = None
        if current_mode and current_mode in available_modes:
            current_idx = available_modes.index(current_mode)
            next_idx = (current_idx + 1) % len(available_modes)
            next_mode = available_modes[next_idx]
        else:
            next_mode = available_modes[0]
        
        best_data = self.current_trip.transport.get(next_mode, {})
        self.last_recommendation = {"type": "transport", "data": {"mode": next_mode, "details": best_data}}
        
        prompt = f"""You are VoyageOS, a premium travel consultant. Recommend an alternative transport option.

Use ONLY the factual data below. Do NOT invent details.

TRANSPORT DATA:
- Recommended Mode: {next_mode}
- Duration: {best_data.get('duration', 'N/A')}
- Price Range: {best_data.get('price_range', 'N/A')}
- Operators: {best_data.get('operators', [])}

TRIP CONTEXT:
- Origin: {self.current_trip.origin}
- Destination: {self.current_trip.destination}
- Budget: ₹{self.current_trip.budget:,.0f}
- Trip Type: {self.current_trip.trip_type}

Write a concise transport recommendation (3-5 sentences) with:
1. Recommended mode and why
2. Travel time and estimated cost
3. Key advantages
4. Trade-offs to consider

Be practical and honest."""
        
        try:
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            answer = response.content
        except Exception:
            emoji = {'flight': '✈️', 'train': '🚆', 'bus': '🚌'}.get(next_mode, '🚗')
            answer = f"## Alternative Transport\n\n"
            answer += f"**Recommended:** {emoji} {next_mode.title()}\n\n"
            answer += f"**Route:** {self.current_trip.origin} → {self.current_trip.destination}\n"
            answer += f"**Travel Time:** {best_data.get('duration', 'N/A')}\n"
            answer += f"**Estimated Price:** {best_data.get('price_range', 'N/A')}\n\n"
            answer += f"This option offers a different balance for your {self.current_trip.trip_type} trip."
        
        self._save_conversation(user_message, answer)
        return {
            "status": "completed",
            "response": answer,
            "session_id": self.session_id
        }

    def _handle_explain_last(self, user_message: str) -> Dict:
        """Explain the last recommendation using LLM with structured data (no hallucination)."""
        if not self.last_recommendation:
            response = "I don't have a recent recommendation to explain. Try asking for a hotel, attraction, or transport recommendation first."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        rec = self.last_recommendation
        rec_type = rec.get("type", "item")
        data = rec.get("data", {})
        
        # Build a structured prompt with ONLY factual data — LLM may improve wording but NOT invent facts
        prompt = f"""You are VoyageOS, a premium travel consultant. The user is asking about a previously recommended {rec_type}.

USER'S QUESTION: {user_message}

Below is the EXACT factual data from the trip plan. Do NOT invent any information that is not provided below. You may improve wording, summarize, and personalize the explanation — but do NOT add fictional details.

TRIP CONTEXT:
- Destination: {self.current_trip.destination}
- Origin: {self.current_trip.origin}
- Duration: {self.current_trip.duration} days
- Budget: ₹{self.current_trip.budget:,.0f}
- Travelers: {self.current_trip.travelers}
- Trip Type: {self.current_trip.trip_type}

RECOMMENDED {rec_type.upper()} DATA:
{json.dumps(data, indent=2)}

INSTRUCTIONS:
1. Answer the user's question naturally and conversationally.
2. Use ONLY the data provided above — do not invent names, prices, ratings, or locations.
3. If the user asks something the data cannot answer, say so honestly.
4. Keep the response concise (3-6 sentences) and professional.
5. Relate the recommendation back to why it suits THIS specific trip (trip type, budget, group size)."""
        
        try:
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            answer = response.content
        except Exception as e:
            logger.error(f"LLM error in explain_last: {str(e)}")
            # Fallback: use stored data directly
            name = data.get('name', 'this option')
            answer = f"**{name}** was recommended for your {self.current_trip.trip_type} trip to {self.current_trip.destination}. It fits your budget of ₹{self.current_trip.budget:,.0f} and is well-suited for {self.current_trip.travelers} traveler(s)."
        
        self._save_conversation(user_message, answer)
        return {
            "status": "completed",
            "response": answer,
            "session_id": self.session_id
        }

    def _handle_hotel_recommendation(self, user_message: str) -> Dict:
        """Recommend a hotel from stored options using LLM for professional wording."""
        if not self.current_trip.hotels:
            response = "I couldn't find hotel information from the previous itinerary. Could you regenerate the trip?"
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        hotel = self.current_trip.hotels[0]
        self.last_recommendation = {"type": "hotel", "data": hotel}
        
        name = hotel.get('name', 'Unknown Hotel')
        address = hotel.get('address', 'Address not available')
        
        # Use LLM for professional wording with structured data only
        prompt = f"""You are VoyageOS, a premium travel consultant. Recommend a hotel to the user.

Use ONLY the factual data below. You may improve wording and personalize, but do NOT invent details.

HOTEL DATA:
- Name: {name}
- Address: {address}

TRIP CONTEXT:
- Destination: {self.current_trip.destination}
- Budget: ₹{self.current_trip.budget:,.0f}
- Travelers: {self.current_trip.travelers}
- Trip Type: {self.current_trip.trip_type}

Write a concise, professional hotel recommendation (4-6 sentences) with this structure:
1. Hotel name and area
2. Why it suits THIS specific trip
3. Location highlights
4. Budget fit
5. Who it's best for

Use emojis sparingly. Be conversational but professional."""
        
        try:
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            answer = response.content
        except Exception:
            # Fallback if LLM fails
            answer = f"🏨 **{name}**\n\n📍 {address}\n\nI recommend this hotel for your {self.current_trip.trip_type} trip to {self.current_trip.destination}. It fits your budget of ₹{self.current_trip.budget:,.0f} and is well-suited for {self.current_trip.travelers} traveler(s). The location provides a great base for exploring the city."
        
        self._save_conversation(user_message, answer)
        return {
            "status": "completed",
            "response": answer,
            "session_id": self.session_id
        }

    def _handle_show_hotels(self, user_message: str) -> Dict:
        """Show all hotels."""
        if not self.current_trip.hotels:
            response = "I couldn't find hotel information from the previous itinerary."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        response = f"## Hotels in {self.current_trip.destination}\n\n"
        for i, hotel in enumerate(self.current_trip.hotels, 1):
            response += f"**{i}. {hotel.get('name', 'Unknown')}**\n"
            response += f"📍 {hotel.get('address', 'N/A')}\n\n"
        
        self._save_conversation(user_message, response)
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_hotel_replacement(self, user_message: str) -> Dict:
        """Handle hotel replacement request."""
        response = "I'll help you find a different hotel. Let me search for alternative options..."
        self._save_conversation(user_message, response)
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_hotel_details(self, user_message: str) -> Dict:
        """Provide details about a specific hotel."""
        if not self.current_trip.hotels:
            response = "I couldn't find hotel information from the previous itinerary."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        hotel = self.current_trip.hotels[0]
        self.last_recommendation = {"type": "hotel", "data": hotel}
        name = hotel.get('name', 'Unknown Hotel')
        address = hotel.get('address', 'Address not available')
        
        response = f"**{name}**\n\n"
        response += f"📍 {address}\n\n"
        response += f"This hotel was recommended for your {self.current_trip.trip_type} trip "
        response += f"because it fits your budget of ₹{self.current_trip.budget:,.0f} "
        response += f"and provides good value for {self.current_trip.travelers} traveler(s)."
        
        self._save_conversation(user_message, response)
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_attraction_recommendation(self, user_message: str) -> Dict:
        """Recommend an attraction from stored options using LLM for professional wording."""
        if not self.current_trip.attractions:
            response = "I couldn't find attraction information from the previous itinerary. Could you regenerate the trip?"
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        place = self.current_trip.attractions[0]
        self.last_recommendation = {"type": "attraction", "data": place}
        
        name = place.get('name', 'Unknown Attraction')
        category = place.get('category', 'Attraction')
        description = place.get('description', '')
        
        prompt = f"""You are VoyageOS, a premium travel consultant. Recommend an attraction to the user.

Use ONLY the factual data below. You may improve wording and personalize, but do NOT invent details.

ATTRACTION DATA:
- Name: {name}
- Category: {category}
- Description: {description}

TRIP CONTEXT:
- Destination: {self.current_trip.destination}
- Trip Type: {self.current_trip.trip_type}

Write a concise, professional attraction recommendation (4-6 sentences) with this structure:
1. Attraction name and what it is
2. Why visit it first on this trip
3. Best time to visit
4. Suggested duration
5. Nearby experiences if applicable

Be conversational but professional. Use emojis sparingly."""
        
        try:
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            answer = response.content
        except Exception:
            answer = f"## {name}\n\n**Category:** {category}\n\n"
            if description:
                answer += f"{description}\n\n"
            answer += f"This is a top attraction in {self.current_trip.destination} for your {self.current_trip.trip_type} trip. "
            answer += "Visit early in the morning (around 9 AM) to avoid crowds. Plan for 2–3 hours."
        
        self._save_conversation(user_message, answer)
        return {
            "status": "completed",
            "response": answer,
            "session_id": self.session_id
        }

    def _handle_show_attractions(self, user_message: str) -> Dict:
        """Show all attractions."""
        if not self.current_trip.attractions:
            response = "I couldn't find attraction information from the previous itinerary."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        response = f"## Attractions in {self.current_trip.destination}\n\n"
        for i, place in enumerate(self.current_trip.attractions, 1):
            response += f"**{i}. {place.get('name', 'Unknown')}**\n"
            response += f"Category: {place.get('category', 'N/A')}\n\n"
        
        self._save_conversation(user_message, response)
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_attraction_replacement(self, user_message: str) -> Dict:
        """Handle attraction replacement request."""
        response = "I'll help you find alternative attractions. Let me search for different options..."
        self._save_conversation(user_message, response)
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_transport_recommendation(self, user_message: str) -> Dict:
        """Provide transport recommendation from stored data."""
        if not self.current_trip.transport:
            response = "Transport information is not available for this trip."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        # Determine if international trip
        is_international = False
        origin_country = self.current_trip.origin.lower()
        dest_country = self.current_trip.destination.lower()
        # Simple heuristic: if destination is a known country name or different from origin
        known_countries = ["japan", "france", "italy", "usa", "australia", "spain", "uk", "germany", 
                          "thailand", "singapore", "dubai", "uae", "canada", "switzerland", 
                          "netherlands", "turkey", "egypt", "greece", "china", "brazil", "vietnam"]
        if any(c in dest_country for c in known_countries):
            is_international = True
        
        # Find best option: prefer flight for international, otherwise pick best available
        best_mode = None
        best_data = None
        
        # Priority order
        if is_international:
            priority = ['flight', 'train', 'bus']
        else:
            priority = ['flight', 'train', 'bus']
        
        for mode in priority:
            if mode in self.current_trip.transport and self.current_trip.transport[mode].get('available'):
                best_mode = mode
                best_data = self.current_trip.transport[mode]
                break
        
        # If no priority match, take any available
        if not best_mode:
            for mode, data in self.current_trip.transport.items():
                if data.get('available'):
                    best_mode = mode
                    best_data = data
                    break
        
        self.last_recommendation = {"type": "transport", "data": {"mode": best_mode, "details": best_data}}
        
        prompt = f"""You are VoyageOS, a premium travel consultant. Recommend a transport option.

Use ONLY the factual data below. Do NOT invent details.

TRANSPORT DATA:
- Recommended Mode: {best_mode or 'None'}
- Duration: {best_data.get('duration', 'N/A') if best_data else 'N/A'}
- Price Range: {best_data.get('price_range', 'N/A') if best_data else 'N/A'}
- Operators: {best_data.get('operators', []) if best_data else []}

TRIP CONTEXT:
- Origin: {self.current_trip.origin}
- Destination: {self.current_trip.destination}
- Budget: ₹{self.current_trip.budget:,.0f}
- Trip Type: {self.current_trip.trip_type}
- International Trip: {'Yes' if is_international else 'No'}

Write a concise transport recommendation (3-5 sentences) with:
1. Recommended mode and why
2. Travel time and estimated cost
3. Key advantages
4. Trade-offs to consider

Be practical and honest. If the trip is international, explain why flight is the practical choice."""
        
        try:
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            answer = response.content
        except Exception:
            if best_mode and best_data:
                emoji = {'flight': '✈️', 'train': '🚆', 'bus': '🚌'}.get(best_mode, '🚗')
                answer = f"## Transport Recommendation\n\n"
                answer += f"**Recommended:** {emoji} {best_mode.title()}\n\n"
                answer += f"**Route:** {self.current_trip.origin} → {self.current_trip.destination}\n"
                answer += f"**Travel Time:** {best_data.get('duration', 'N/A')}\n"
                answer += f"**Estimated Price:** {best_data.get('price_range', 'N/A')}\n\n"
                if is_international and best_mode == 'flight':
                    answer += f"For an international trip to {self.current_trip.destination}, flying is the most practical option."
                else:
                    answer += f"This option offers the best balance for your {self.current_trip.trip_type} trip."
            else:
                answer = "No specific transport mode could be recommended. Check the full itinerary for available options."
        
        self._save_conversation(user_message, answer)
        return {
            "status": "completed",
            "response": answer,
            "session_id": self.session_id
        }

    def _handle_weather_info(self, user_message: str) -> Dict:
        """Provide weather information from stored trip."""
        if not self.current_trip.weather:
            response = "Weather information is not available for this trip."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        temp = self.current_trip.weather.get('temperature', 'N/A')
        condition = self.current_trip.weather.get('condition', 'N/A')
        humidity = self.current_trip.weather.get('humidity', 'N/A')
        
        response = f"Weather in {self.current_trip.destination}:\n\n"
        response += f"🌡️ Temperature: {temp}°C\n"
        response += f"☁️ Condition: {condition}\n"
        response += f"💧 Humidity: {humidity}%\n\n"
        response += "Pack accordingly and check the forecast closer to your travel date."
        
        self._save_conversation(user_message, response)
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_budget_update(self, user_message: str) -> Dict:
        """Handle budget update request."""
        # Extract new budget from message
        budget_match = re.search(r'(\d+)', user_message)
        if not budget_match:
            response = "What would you like to update the budget to?"
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        new_budget = float(budget_match.group(1))
        old_budget = self.current_trip.budget
        self.current_trip.budget = new_budget
        
        response = f"I've updated your budget from ₹{old_budget:,.0f} to ₹{new_budget:,.0f}.\n\n"
        response += "This change affects:\n"
        response += "- Budget allocation across categories\n"
        response += "- Hotel recommendations\n"
        response += "- Transport options\n\n"
        response += "Would you like me to regenerate the itinerary with the new budget?"
        
        self.state = self.STATE_AWAITING_CONFIRMATION
        self.pending_action = self.PENDING_REGENERATE_BUDGET
        self._save_conversation(user_message, response)
        self._save_trip_to_history()
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_duration_update(self, user_message: str) -> Dict:
        """Handle duration update request."""
        # Extract new duration from message
        duration_match = re.search(r'(\d+)\s*day', user_message)
        if not duration_match:
            response = "How many days would you like the trip to be?"
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        new_duration = int(duration_match.group(1))
        old_duration = self.current_trip.duration
        self.current_trip.duration = new_duration
        
        response = f"I've updated your trip duration from {old_duration} days to {new_duration} days.\n\n"
        response += "This change affects:\n"
        response += "- Daily itinerary schedule\n"
        response += "- Budget allocation\n"
        response += "- Activity planning\n\n"
        response += "Would you like me to regenerate the itinerary with the new duration?"
        
        self.state = self.STATE_AWAITING_CONFIRMATION
        self.pending_action = self.PENDING_REGENERATE_DURATION
        self._save_conversation(user_message, response)
        self._save_trip_to_history()
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_show_day(self, user_message: str) -> Dict:
        """Show a specific day from the itinerary - ONLY that day."""
        message_lower = user_message.lower()
        day_num = None
        
        # Handle "tomorrow" → day 2
        if "tomorrow" in message_lower:
            day_num = 2
        else:
            # Try "day X" or "dya X" pattern
            day_match = re.search(r'(?:day|dya)\s*(\d+)', message_lower)
            if day_match:
                day_num = int(day_match.group(1))
            else:
                # Try word-based: "second day", "first day", etc.
                word_map = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
                for word, num in word_map.items():
                    if word in message_lower and "day" in message_lower:
                        day_num = num
                        break
        
        if day_num is None:
            response = "Which day would you like to see? Try 'Show Day 2', 'day two', or 'show dya 2'."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "session_id": self.session_id
            }
        
        # Find the requested day
        requested_day = None
        for day_plan in self.current_trip.day_plans:
            if day_plan.day_number == day_num:
                requested_day = day_plan
                break
        
        if requested_day:
            response = f"## {requested_day.content}"
        else:
            response = f"I couldn't find Day {day_num} in the itinerary. "
            response += f"The trip is {self.current_trip.duration} days long."
        
        self._save_conversation(user_message, response)
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_replace_day(self, user_message: str) -> Dict:
        """Handle day replacement request."""
        response = "I'll help you replace that day. Let me create a new schedule for that day..."
        self._save_conversation(user_message, response)
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_packing_info(self, user_message: str) -> Dict:
        """Provide packing information."""
        if self.current_trip.packing_list:
            response = f"## Packing List for {self.current_trip.destination}\n\n{self.current_trip.packing_list}"
        else:
            response = "Packing information is not available for this trip. Would you like me to generate packing suggestions?"
        
        self._save_conversation(user_message, response)
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_local_tips(self, user_message: str) -> Dict:
        """Provide local tips."""
        if self.current_trip.local_tips:
            response = f"## Local Tips for {self.current_trip.destination}\n\n{self.current_trip.local_tips}"
        else:
            response = "Local tips are not available for this trip."
        
        self._save_conversation(user_message, response)
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_trip_summary(self, user_message: str) -> Dict:
        """Provide trip summary."""
        response = f"## Trip Summary\n\n"
        response += f"**Destination:** {self.current_trip.destination}\n"
        response += f"**Origin:** {self.current_trip.origin}\n"
        response += f"**Duration:** {self.current_trip.duration} days\n"
        response += f"**Travelers:** {self.current_trip.travelers}\n"
        response += f"**Trip Type:** {self.current_trip.trip_type}\n"
        response += f"**Budget:** ₹{self.current_trip.budget:,.0f}\n\n"
        
        if self.current_trip.hotels:
            response += f"**Hotels:** {len(self.current_trip.hotels)} options found\n"
        if self.current_trip.attractions:
            response += f"**Attractions:** {len(self.current_trip.attractions)} places to visit\n"
        if self.current_trip.day_plans:
            response += f"**Itinerary:** {len(self.current_trip.day_plans)} days planned\n"
        
        self._save_conversation(user_message, response)
        return {
            "status": "completed",
            "response": response,
            "session_id": self.session_id
        }

    def _handle_generic_follow_up(self, user_message: str) -> Dict:
        """Handle generic follow-up with LLM."""
        prompt = f"""
You are VoyageOS, a travel assistant. The user has an existing trip plan.

Current Trip:
- Destination: {self.current_trip.destination}
- Origin: {self.current_trip.origin}
- Duration: {self.current_trip.duration} days
- Budget: ₹{self.current_trip.budget:,.0f}
- Travelers: {self.current_trip.travelers}
- Trip Type: {self.current_trip.trip_type}
- Hotels: {len(self.current_trip.hotels)} options
- Attractions: {len(self.current_trip.attractions)} places

User Question: {user_message}

Provide a helpful response based on the trip context. If you don't have the information, say so.
"""
        
        try:
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            answer = response.content
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            answer = "I apologize, but I couldn't generate a response. Please try again."
        
        self._save_conversation(user_message, answer)
        return {
            "status": "completed",
            "response": answer,
            "session_id": self.session_id
        }

    def _handle_modifying_trip(self, user_message: str) -> Dict:
        """Handle trip modification requests."""
        logger.info("State: MODIFYING_TRIP")
        return self._handle_follow_up(user_message, "modify_general")

    def _handle_travel_knowledge(self, user_message: str) -> Dict:
        """Handle travel knowledge questions using RAG + LLM general knowledge."""
        logger.info("Handling travel knowledge request")
        
        # Extract and store travel context from user message
        msg_lower = user_message.lower()
        nationality_keywords = ["indian", "american", "british", "australian", "canadian", "japanese",
                               "chinese", "french", "german", "italian", "spanish", "brazilian",
                               "russian", "korean", "singaporean", "malaysian", "thai", "vietnamese"]
        for kw in nationality_keywords:
            if kw in msg_lower:
                self.travel_context["nationality"] = kw.capitalize()
                break
        purpose_keywords = {"tourism": "tourism", "business": "business", "visit": "tourism",
                           "work": "business", "holiday": "tourism", "vacation": "tourism",
                           "study": "education", "conference": "business"}
        for word, purpose in purpose_keywords.items():
            if word in msg_lower:
                self.travel_context["purpose"] = purpose
                break
        # Extract duration
        dur_match = re.search(r'(\d+)\s*(day|night|week)', msg_lower)
        if dur_match:
            self.travel_context["duration"] = dur_match.group(1)
        # Extract destination from current trip
        if self.current_trip and self.current_trip.destination:
            self.travel_context["destination"] = self.current_trip.destination
        
        try:
            # Query RAG pipeline
            rag_result = self.rag_pipeline.query(user_message, n_results=5)
            
            # Build context string from stored travel_context
            context_parts = []
            if self.travel_context.get("nationality"):
                context_parts.append(f"Nationality: {self.travel_context['nationality']}")
            if self.travel_context.get("destination"):
                context_parts.append(f"Destination: {self.travel_context['destination']}")
            if self.travel_context.get("purpose"):
                context_parts.append(f"Purpose: {self.travel_context['purpose']}")
            if self.travel_context.get("duration"):
                context_parts.append(f"Duration: {self.travel_context['duration']}")
            user_context = "\n".join(context_parts) if context_parts else "No specific context provided."
            
            if rag_result.get("has_answer") and rag_result.get("context"):
                # Generate response using RAG context + LLM
                response = self._generate_rag_response(user_message, rag_result, user_context)
                sources = rag_result.get("sources", [])
                if sources:
                    response += "\n\n*Answer based on travel documents*"
            else:
                # No relevant documents found — use LLM general travel knowledge with context
                logger.info("No RAG context found, using LLM general knowledge")
                response = self._generate_general_travel_response(user_message, user_context)
                sources = []
            
            self._save_conversation(user_message, response)
            
            return {
                "status": "completed",
                "response": response,
                "sources": sources,
                "session_id": self.session_id
            }
        except Exception as e:
            logger.error(f"Error in travel knowledge: {str(e)}", exc_info=True)
            # Friendly fallback
            response = "I apologize, but I couldn't process your question. Please try again."
            self._save_conversation(user_message, response)
            return {
                "status": "completed",
                "response": response,
                "sources": [],
                "session_id": self.session_id
            }

    def _handle_general_travel(self, user_message: str) -> Dict:
        """Handle general travel questions using LLM knowledge."""
        logger.info("Handling general travel question")
        
        prompt = f"""
You are VoyageOS, a travel knowledge assistant.

Answer the following travel-related question using your general knowledge.

User Question: {user_message}

Instructions:
- Provide a helpful, accurate answer
- Keep it concise (3-5 sentences)
- Focus on practical travel advice
- If you're unsure, say so

Answer:
"""
        
        try:
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            answer = response.content
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            answer = "I apologize, but I couldn't generate a response. Please try again."
        
        self._save_conversation(user_message, answer)
        
        return {
            "status": "completed",
            "response": answer,
            "session_id": self.session_id
        }

    def _generate_rag_response(self, question: str, rag_result: Dict, user_context: str = "") -> str:
        """Generate response using RAG context."""
        from rag.prompts import TRAVEL_KNOWLEDGE_PROMPT
        
        context = rag_result["context"]
        sources = rag_result["sources"]
        
        # Build enhanced prompt with user context
        context_section = f"User Context:\n{user_context}\n\n" if user_context and user_context != "No specific context provided." else ""
        
        prompt = f"""You are VoyageOS, a travel knowledge assistant. Answer the user's question using the provided document excerpts and your general knowledge.

{context_section}Document Context:
{context}

User Question: {question}

Instructions:
- Answer using information from the documents AND your general travel knowledge
- If the documents contain relevant information, prioritize it
- If the documents don't cover the topic, use your general knowledge
- Provide a comprehensive, well-structured answer
- Use bullet points for lists
- Keep it practical and actionable
- Never make up information you're unsure about

Answer:"""
        
        try:
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            answer = response.content
            
            # Append sources if available
            if sources:
                answer += "\n\n**Sources:**\n"
                for source in sources:
                    answer += f"- {source}\n"
            
            return answer
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {str(e)}")
            return "I apologize, but I couldn't process your question. Please try again."

    def _generate_general_travel_response(self, question: str, user_context: str = "") -> str:
        """Generate response using LLM general travel knowledge when RAG finds nothing."""
        logger.info("Generating general travel response with LLM")
        
        # Build context string
        context_section = f"\nUser Context:\n{user_context}\n" if user_context and user_context != "No specific context provided." else ""
        
        prompt = f"""You are VoyageOS, a comprehensive travel knowledge assistant. Answer the following travel question using your general knowledge.

{context_section}
User Question: {question}

Instructions:
- Provide a comprehensive, well-structured answer covering all relevant aspects
- Include practical advice on: travel documents, visa, passport validity, insurance, currency, SIM/internet, power adapter, weather preparation, medicines, packing, airport arrival, security checks, immigration, customs, local etiquette, emergency contacts
- Use bullet points for lists
- Keep it concise but thorough (aim for 10-15 sentences total)
- Focus on practical, actionable advice
- If you're unsure about specific details, say so
- Never make up information

Answer:"""
        
        try:
            response = self.travel_agent.llm.invoke([{"role": "user", "content": prompt}])
            answer = response.content
            return answer
        except Exception as e:
            logger.error(f"Failed to generate general travel response: {str(e)}")
            return "I apologize, but I couldn't generate a response. Please try again."

    def _load_trip_from_history(self):
        """Load latest trip from SQLite into CurrentTrip."""
        try:
            trip_data = self.trip_history.get_latest_trip(self.session_id)
            if trip_data:
                self.current_trip = CurrentTrip.from_dict(trip_data)
                logger.info(f"Loaded trip from history: {self.current_trip.destination}")
            else:
                self.current_trip = CurrentTrip()
        except Exception as e:
            logger.error(f"Failed to load trip from history: {str(e)}")

    def _save_trip_to_history(self):
        """Save current trip to SQLite."""
        try:
            trip_dict = self.current_trip.to_dict()
            self.trip_history.save_trip(self.session_id, trip_dict, self.current_trip.itinerary_markdown)
            logger.info(f"Saved trip to history: {self.current_trip.destination}")
        except Exception as e:
            logger.error(f"Failed to save trip to history: {str(e)}")

    def _save_conversation(self, user_message: str, assistant_message: str):
        """Save conversation to history."""
        try:
            self.conversation_history.add_message(self.session_id, user_message, assistant_message)
        except Exception as e:
            logger.error(f"Failed to save conversation: {str(e)}")

    def get_conversation_history(self, limit: int = 50) -> list:
        """Get conversation history for current session."""
        return self.conversation_history.get_session_history(self.session_id, limit)

    def get_trip_history(self) -> list:
        """Get trip history for current session."""
        return self.trip_history.get_session_trips(self.session_id)

    def get_recent_sessions(self, limit: int = 20) -> list:
        """Get recent sessions."""
        return self.conversation_history.get_recent_sessions(limit)

    def load_session(self, session_id: str):
        """Load a previous session."""
        try:
            # Update session ID FIRST
            self.session_id = session_id
            
            # Load conversation history
            history = self.conversation_history.get_session_history(session_id, limit=50)
            
            # Load latest trip for this session
            trip_data = self.trip_history.get_latest_trip(session_id)
            if trip_data:
                self.current_trip = CurrentTrip.from_dict(trip_data)
                logger.info(f"Loaded trip from history: {self.current_trip.destination}")
            else:
                # No trip found, reset current trip
                self.current_trip = CurrentTrip()
                logger.info("No trip found in history for this session")
            
            # Restore state
            if self.current_trip and self.current_trip.destination:
                self.state = self.STATE_ITINERARY_READY
            else:
                self.state = self.STATE_IDLE
            
            # Restore pending action
            self.pending_action = self.PENDING_NONE
            
            # Sync trip data to travel agent state
            self._sync_trip_to_agent()
            
            logger.info(f"Successfully loaded session: {session_id}")
            return {
                "success": True,
                "session_id": session_id,
                "history": history,
                "has_trip": bool(self.current_trip and self.current_trip.destination),
                "state": self.state
            }
        except Exception as e:
            logger.error(f"Failed to load session: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def initialize_rag(self) -> bool:
        """Initialize RAG system by ingesting documents."""
        return self.rag_pipeline.ingest_documents()

    def get_rag_sources(self) -> list:
        """Get available RAG document sources."""
        return self.rag_pipeline.get_sources()

    def close(self):
        """Cleanup resources."""
        self.database.close()