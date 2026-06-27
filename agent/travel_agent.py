import json

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from utils.config import Config

from agent.state import TravelState
from agent.planner import Planner
from agent.tool_manager import ToolManager
from agent.prompts import SYSTEM_PROMPT

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

        tool_order = [
            "budget",
            "weather",
            "places",
            "hotel",
            "transport"
        ]

        for tool_name in tool_order:

            result = self.tool_manager.execute(
                tool_name,
                state=self.state
            )

            if result.get("success"):

                tool_results[tool_name] = result.get("data")

            else:

                tool_results[tool_name] = {

                    "error": result.get(
                        "message",
                        "Unknown Error"
                    )
                }

        print("\n========== COMPLETE TOOL RESULTS ==========")
        print(json.dumps(tool_results, indent=2))
        print("===========================================\n")

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

    ====================================================
    VERIFIED TOOL OUTPUTS
    ====================================================

    The following information has already been collected,
    validated and formatted by VoyageOS.

    Treat every section below as factual.

    {trip_text}

    {budget_text}

    {weather_text}

    {transport_text}

    {hotel_text}

    {places_text}

    ====================================================
    YOUR TASK
    ====================================================

    Create a premium travel itinerary using ONLY the
    verified information above.

    STRICT RULES

    1. Never invent hotels.

    2. Never invent attractions.

    3. Never invent transport information.

    4. Never invent weather information.

    5. Never invent prices.

    6. Never invent budget values.

    7. Use ALL transport modes provided.

    8. Create a markdown transport comparison table.

    Columns:

    | Mode | Duration | Price Range | Operators |

    Include every available mode.

    9. After the table create

    ### ⭐ Recommended Transport

    Use ONLY the recommended option already provided.

    Do not change it.

    10. Recommend ONLY the hotels listed.

    11. Explain why each hotel is suitable.

    12. Use EVERY attraction exactly once.

    13. Explain why each attraction is worth visiting.

    14. Build a realistic day-wise itinerary.

    15. Schedule attractions according to their best
    visiting time whenever available.

    16. If there are fewer attractions than trip days,
    fill remaining days with:

    • Local food exploration

    • Shopping

    • Beach / Leisure

    • Relaxation

    • Cultural experiences

    Do NOT invent new tourist attractions.

    17. Use the budget allocation exactly.

    18. Use the weather while planning.

    19. Create a packing checklist based on weather.

    20. Create local travel tips.

    21. Create safety advice.

    22. Never output:

    Unknown

    Not Available

    N/A

    None

    ====================================================
    OUTPUT FORMAT
    ====================================================

    Return beautiful Markdown.

    The response must contain these sections
    in this order.

    # 🌍 Trip Overview

    Short introduction.

    ---

    ## 📊 Trip Summary

    Create a table with

    | Destination | Travelers | Budget | Duration | Trip Type |

    ---

    ## 🚆 Transport Comparison

    Create a markdown table

    | Mode | Duration | Price Range | Operators |

    Include Flight, Train and Bus whenever available.

    Then create

    ### ⭐ Recommended Transport

    Explain why it was selected.

    ---

    ## 🌤️ Weather Overview

    Summarize the weather.

    Explain how it affects the trip.

    ---

    ## 🏨 Hotel Recommendations

    For every hotel include

    • Name

    • Address

    • Why Recommended

    ---

    ## 🗺️ Attractions

    For every attraction include

    • Name

    • Category

    • Description

    • Best Visiting Time

    • Suggested Duration

    • Why Visit

    ---

    ## 💰 Budget Allocation

    Create a markdown table.

    ---

    ## 📅 Day-wise Itinerary

    One section per day.

    Use every attraction exactly once.

    Do not repeat attractions.

    ---

    ## 🎒 Packing Checklist

    Bulleted list.

    ---

    ## 📍 Local Tips

    Bulleted list.

    ---

    ## 🛡️ Safety Tips

    Bulleted list.

    ====================================================

    The itinerary should read like a premium travel
    guide written by a professional travel consultant.
    """

        print("\n========== FINAL PROMPT ==========")
        print(prompt)
        print("==================================\n")

        return prompt



    def generate_response(self):

        prompt = self.build_prompt()

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

        return assistant_message
    


        # -------------------------------------
    # Main Chat Method
    # -------------------------------------

    def chat(self, user_input: str):

        planner_result = self.planner.run(
            self.state,
            user_input
        )

        # Need more information
        if planner_result["status"] == "collecting_information":

            return {

                "success": True,

                "status": "collecting_information",

                "message": planner_result["message"]

            }

        # Execute all tools
        self.execute_tools()
        print("\n========== COMPLETE TOOL RESULTS ==========")

        print(
            json.dumps(
                self.state.tool_results,
                indent=2
            )
        )

        print("===========================================\n")
        # Generate final travel plan
        final_response = self.generate_response()

        return {

            "success": True,

            "status": "completed",

            "message": final_response,

            "tool_results": self.state.tool_results

        }