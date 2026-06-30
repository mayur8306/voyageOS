import json

from langchain_core.messages import HumanMessage
from agent.state import TravelState


class Planner:
    """
    Planner is responsible for:

    1. Extracting structured information from user input
    2. Updating TravelState
    3. Checking missing trip information
    4. Asking the next required question

    It DOES NOT call tools.
    It DOES NOT generate itineraries.
    """

    REQUIRED_FIELDS = [
        "origin",
        "destination",
        "budget",
        "travelers",
        "trip_type",
        "duration",
    ]

    def __init__(self, llm):
        self.llm = llm

    # --------------------------------------------------
    # Extract Information
    # --------------------------------------------------

    def extract_information(self, state: TravelState, user_input: str):

        prompt = f"""
You are an expert travel information extraction assistant.

Extract all travel planning information from the user's message.

Return ONLY valid JSON.

Schema:

{{
    "origin": "",
    "destination": "",
    "budget": 0,
    "travelers": 0,
    "trip_type": "",
    "duration": 0
}}

Rules:

- Origin is the departure city.
- Destination is the destination city.
- Budget must be a number only (in INR, Indian Rupees).
- Travelers must be an integer.
- Duration must be the number of days only (integer).
- Trip type must be one of: honeymoon, family, solo, friends, business
- If the trip type is "solo", travelers should be 1.
- If any information is missing, leave it empty or 0.
- IMPORTANT: If user provides just a number like "5" or "5 days" or "five days", 
  and the current missing field is duration, extract it as duration=5.
- If user says "solo" or "alone", extract trip_type="solo" and travelers=1.
- Return ONLY valid JSON.
- Do not explain anything.

Current missing fields: {self.get_missing_fields(state)}

User Message:

{user_input}
"""

        response = self.llm.invoke(
            [HumanMessage(content=prompt)]
        )

        content = response.content.strip()

        if content.startswith("```json"):
            content = content.replace("```json", "", 1)

        if content.startswith("```"):
            content = content.replace("```", "", 1)

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        try:

            data = json.loads(content)

            if data.get("origin"):
                state.trip.origin = data["origin"]

            if data.get("destination"):
                state.trip.destination = data["destination"]

            if data.get("budget"):
                state.trip.budget = float(data["budget"])

            if data.get("travelers"):
                state.trip.travelers = int(data["travelers"])

            if data.get("trip_type"):
                state.trip.trip_type = data["trip_type"]

            if data.get("duration"):
                state.trip.duration = int(data["duration"])

            # Safety fallback
            if (
                state.trip.trip_type
                and state.trip.trip_type.lower() == "solo"
                and (state.trip.travelers is None or state.trip.travelers == 0)
            ):
                state.trip.travelers = 1

        except Exception as e:

            state.errors.append(str(e))

        state.messages.append(
            {
                "role": "user",
                "content": user_input
            }
        )

    # --------------------------------------------------
    # Check Missing Fields
    # --------------------------------------------------

    def get_missing_fields(self, state: TravelState):

        missing = []

        if not state.trip.origin:
            missing.append("origin")

        if not state.trip.destination:
            missing.append("destination")

        # Safe comparison with None check
        if state.trip.budget is None or state.trip.budget <= 0:
            missing.append("budget")

        # Safe comparison with None check
        if state.trip.travelers is None or state.trip.travelers <= 0:
            missing.append("travelers")

        if not state.trip.trip_type:
            missing.append("trip_type")

        # Safe comparison with None check
        if state.trip.duration is None or state.trip.duration <= 0:
            missing.append("duration")

        return missing

    # --------------------------------------------------
    # Ask Next Question
    # --------------------------------------------------

    def ask_next_question(self, missing_fields):

        questions = {

            "origin":
                "Which city will you be travelling from?",

            "destination":
                "Do you already have a destination in mind, or would you like me to suggest one?",

            "budget":
                "What is your approximate travel budget?",

            "travelers":
                "How many people will be travelling?",

            "trip_type":
                "What type of trip are you planning? (Honeymoon, Family, Solo, Friends, Business)",

            "duration":
                "How many days are you planning to travel?"
        }

        return questions[missing_fields[0]]

    # --------------------------------------------------
    # Main Planner
    # --------------------------------------------------

    def run(self, state: TravelState, user_input: str):

        self.extract_information(state, user_input)

        missing = self.get_missing_fields(state)

        if missing:

            return {
                "status": "collecting_information",
                "message": self.ask_next_question(missing),
                "missing_fields": missing
            }

        state.current_step = "planning"

        return {
            "status": "ready",
            "message": "All required information collected. Ready to start travel planning.",
            "missing_fields": []
        }