import json

from langchain_core.messages import HumanMessage

from services.transport_service import TransportService
from utils.transport_parser import parse_transport


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

        print("\n========== RAW SEARCH RESULTS ==========")
        print(json.dumps(search["data"], indent=2))
        print("========================================\n")

        # ------------------------------------
        # Parse Search Results
        # ------------------------------------

        parsed_transport = parse_transport(
            search["data"]
        )

        print("\n========== PARSED TRANSPORT ==========")
        print(json.dumps(parsed_transport, indent=2))
        print("======================================\n")

        # ------------------------------------
        # Ask LLM ONLY for Recommendation
        # ------------------------------------

        prompt = f"""
You are an expert travel consultant.

Below is already extracted transportation information.

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
                "Unknown"
            )

            recommendation.setdefault(
                "reason",
                "Unknown"
            )

            # ------------------------------------
            # Merge Recommendation
            # ------------------------------------

            parsed_transport["recommended_option"] = recommendation[
                "recommended_option"
            ]

            parsed_transport["reason"] = recommendation[
                "reason"
            ]

            print("\n========== FINAL TRANSPORT ==========")
            print(json.dumps(parsed_transport, indent=2))
            print("=====================================\n")

            return {
                "success": True,
                "data": parsed_transport
            }

        except json.JSONDecodeError:

            print("\n========== RAW LLM RESPONSE ==========")
            print(response.content)
            print("======================================\n")

            return {

                "success": False,

                "message": "Unable to parse transport recommendation.",

                "raw_response": response.content

            }