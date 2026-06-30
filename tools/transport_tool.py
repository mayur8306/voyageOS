import json
import logging

from langchain_core.messages import HumanMessage

from services.transport_service import TransportService
from utils.transport_parser import parse_transport

logger = logging.getLogger(__name__)


class TransportTool:

    def __init__(self, llm):

        self.transport = TransportService()
        self.llm = llm

    def execute(self, state):

        origin = state.trip.origin
        destination = state.trip.destination

        if not origin or not destination:

            return {
                "success": False,
                "message": "Origin or destination missing."
            }

        # ------------------------------------
        # Search Transport Information
        # ------------------------------------

        search = self.transport.search_transport(
            origin,
            destination
        )

        if not search["success"]:
            return search

        logger.debug(f"Raw transport search results for {origin} -> {destination}")

        # ------------------------------------
        # Parse Search Results into structured options
        # Pass origin/destination for route validation
        # ------------------------------------

        parsed_transport = parse_transport(
            search["data"],
            origin=origin,
            destination=destination
        )

        flight_opts = len(parsed_transport.get('flight', {}).get('options', []))
        train_opts = len(parsed_transport.get('train', {}).get('options', []))
        bus_opts = len(parsed_transport.get('bus', {}).get('options', []))
        logger.debug(f"Parsed transport options: {flight_opts} flight, {train_opts} train, {bus_opts} bus")

        # ------------------------------------
        # Ask LLM ONLY for Recommendation
        # ------------------------------------

        prompt = f"""
You are an expert travel consultant.

Below is already extracted transportation information with up to 3 options per mode.

{json.dumps(parsed_transport, indent=2)}

Your ONLY job is to recommend the best transport option.

Consider:
- Travel duration
- Price
- Available operators
- Practicality

DO NOT extract prices.
DO NOT extract duration.
DO NOT rewrite the transport information.

Return ONLY valid JSON.

{{
    "recommended_option": "",
    "reason": ""
}}
"""

        response = self.llm.invoke(
            [HumanMessage(content=prompt)]
        )

        content = response.content.strip()

        # Remove markdown if present

        if content.startswith("```json"):
            content = content.replace("```json", "", 1)

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        # Find JSON

        start = content.find("{")
        end = content.rfind("}")

        if start != -1 and end != -1:
            content = content[start:end + 1]

        try:

            recommendation = json.loads(content)

            recommendation.setdefault(
                "recommended_option",
                "Data unavailable"
            )

            recommendation.setdefault(
                "reason",
                "Data unavailable"
            )

            # ------------------------------------
            # Merge Recommendation into transport data
            # ------------------------------------

            parsed_transport["recommended_option"] = recommendation[
                "recommended_option"
            ]

            parsed_transport["reason"] = recommendation[
                "reason"
            ]

            logger.info(f"Transport recommendation: {parsed_transport['recommended_option']}")
            return {
                "success": True,
                "data": parsed_transport
            }

        except json.JSONDecodeError:

            logger.error("Failed to parse transport recommendation from LLM")
            return {

                "success": False,

                "message": "Unable to parse transport recommendation.",

                "raw_response": response.content

            }