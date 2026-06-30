import json
import logging

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from utils.config import Config

from agent.state import TravelState
from agent.planner import Planner
from agent.tool_manager import ToolManager
from agent.prompts import SYSTEM_PROMPT
from agent.constants import TOOL_ORDER

from tools.budget_tool import BudgetTool
from tools.weather_tool import WeatherTool
from tools.places_tool import PlacesTool
from tools.hotel_tool import HotelTool
from tools.transport_tool import TransportTool
from utils.formatters import (
    format_trip,
    format_budget,
    format_weather,
    format_transport,
    format_hotels,
    format_places
)

logger = logging.getLogger(__name__)


class TravelAgent:

    def __init__(self):

        self.state = TravelState()

        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            groq_api_key=Config.GROQ_API_KEY,
            temperature=0.2
        )

        self.planner = Planner(self.llm)

        self.tool_manager = ToolManager()

        self._register_tools()

    # -------------------------------------
    # Register All Tools
    # -------------------------------------

    def _register_tools(self):

        self.tool_manager.register_tool(
            "budget",
            BudgetTool()
        )

        self.tool_manager.register_tool(
            "weather",
            WeatherTool()
        )

        self.tool_manager.register_tool(
            "places",
            PlacesTool()
        )

        self.tool_manager.register_tool(
            "hotel",
            HotelTool()
        )

        self.tool_manager.register_tool(
            "transport",
            TransportTool(self.llm)
        )


    # -------------------------------------
    # Execute All Tools
    # -------------------------------------

    def execute_tools(self):

        tool_results = {}

        for tool_name in TOOL_ORDER:

            logger.info(f"Executing tool: {tool_name}")

            result = self.tool_manager.execute(
                tool_name,
                state=self.state
            )

            if result.get("success"):

                tool_results[tool_name] = result.get("data")
                logger.info(f"Tool {tool_name} completed successfully")

            else:

                # Store empty result instead of error object
                # This prevents formatters from crashing
                if tool_name in ["places", "hotel"]:
                    tool_results[tool_name] = []
                elif tool_name == "transport":
                    tool_results[tool_name] = {}
                else:
                    tool_results[tool_name] = {}

                logger.warning(f"Tool {tool_name} failed: {result.get('message')}")

        self.state.tool_results = tool_results

        return tool_results

    # -------------------------------------
    # Build Prompt
    # -------------------------------------

    def build_prompt(self):

        trip = self.state.trip

        budget = self.state.tool_results.get("budget", {})
        weather = self.state.tool_results.get("weather", {})
        hotels = self.state.tool_results.get("hotel", [])
        places = self.state.tool_results.get("places", [])
        transport = self.state.tool_results.get("transport", {})

        trip_text = format_trip(trip)
        budget_text = format_budget(budget)
        weather_text = format_weather(weather)
        transport_text = format_transport(transport)
        hotel_text = format_hotels(hotels)
        places_text = format_places(places)

        prompt = f"""
{SYSTEM_PROMPT}

VERIFIED TOOL OUTPUTS

The following information has been collected from external sources.
It is candidate data, not final recommendations.

CURATE these results carefully:
- Remove poor-quality transport options (unrealistic durations, wrong routes)
- Remove generic POIs and keep only famous attractions
- Select the best hotels and make each explanation unique
- Never blindly repeat every tool output — use your judgment

{trip_text}

{budget_text}

{weather_text}

{transport_text}

{hotel_text}

{places_text}

INSTRUCTIONS

Generate a premium travel itinerary using ONLY the verified tool outputs above.

Follow all rules in the system prompt carefully:

- CURATE transport options: remove invalid durations and wrong routes
- Present Flight, Train, and Bus each as separate sections with their options — no comparison table
- State the recommended transport after all mode sections
- Write weather as one paragraph of practical advice — not raw bullet points
- Select only the BEST hotels — make each explanation unique and specific
- Select only the BEST attractions — remove generic POIs, keep famous ones
- Use budget values exactly — never modify them
- Include the Budget Feasibility section after budget allocation
- Build a realistic day-wise itinerary with logical geographic flow
- If more attractions than days, create "Other Places Worth Exploring" section
- Generate weather-appropriate packing, local tips, and safety advice
- Generate ALL sections in the correct order — never stop mid-section
- NEVER output placeholders like "Attraction 1", "Hotel 2", "Option 3", "Unknown"

The final response must read like a premium travel guide written by a professional travel consultant.
"""

        return prompt

    def generate_response(self):

        prompt = self.build_prompt()

        logger.info("Generating itinerary with LLM")

        response = self.llm.invoke(
            [HumanMessage(content=prompt)]
        )

        assistant_message = response.content

        self.state.messages.append(
            {
                "role": "assistant",
                "content": assistant_message
            }
        )

        logger.info("Itinerary generated successfully")
        return assistant_message

    # -------------------------------------
    # Main Chat Method
    # -------------------------------------

    def chat(self, user_input: str):

        logger.info("Starting LangGraph workflow")

        planner_result = self.planner.run(
            self.state,
            user_input
        )

        # Need more information
        if planner_result["status"] == "collecting_information":

            logger.info("Collecting additional information from user")
            return {

                "success": True,

                "status": "collecting_information",

                "message": planner_result["message"]

            }

        # Execute all tools
        logger.info("Executing all tools")
        self.execute_tools()

        # Generate final travel plan
        logger.info("Generating final itinerary")
        final_response = self.generate_response()

        logger.info("Workflow completed successfully")

        return {

            "success": True,

            "status": "completed",

            "message": final_response,

            "tool_results": self.state.tool_results

        }