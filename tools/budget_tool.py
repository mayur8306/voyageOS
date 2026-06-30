import json
import logging

logger = logging.getLogger(__name__)


class BudgetTool:

    def execute(self, state):

        total_budget = state.trip.budget

        if total_budget <= 0:

            return {
                "success": False,
                "message": "Invalid budget."
            }

        logger.info(f"Calculating budget for INR {total_budget}")

        trip_type = state.trip.trip_type.lower()

        allocations = {
            "honeymoon": {
                "hotel": 0.45,
                "transport": 0.20,
                "food": 0.15,
                "activities": 0.15,
                "emergency": 0.05
            },
            "family": {
                "hotel": 0.40,
                "transport": 0.20,
                "food": 0.20,
                "activities": 0.15,
                "emergency": 0.05
            },
            "solo": {
                "hotel": 0.30,
                "transport": 0.20,
                "food": 0.20,
                "activities": 0.25,
                "emergency": 0.05
            },
            "friends": {
                "hotel": 0.35,
                "transport": 0.20,
                "food": 0.20,
                "activities": 0.20,
                "emergency": 0.05
            },
            "business": {
                "hotel": 0.35,
                "transport": 0.30,
                "food": 0.20,
                "activities": 0.10,
                "emergency": 0.05
            }
        }

        percentages = allocations.get(
            trip_type,
            allocations["family"]
        )

        breakdown = {}

        for category, percentage in percentages.items():

            breakdown[category] = {
                "percentage": int(percentage * 100),
                "amount": round(total_budget * percentage, 2)
            }

        # Add contextual guidance fields (no new calculations, just interpretation)
        hotel_budget = breakdown.get("hotel", {})
        activities_budget = breakdown.get("activities", {})
        food_budget = breakdown.get("food", {})
        transport_budget = breakdown.get("transport", {})

        # Budget feasibility check
        feasibility_issues = []
        suggestions = []

        # Check if transport alone exceeds budget
        if transport_budget.get("amount", 0) < 5000:
            feasibility_issues.append("Transport budget is very low for most destinations")
            suggestions.append("Consider train or bus instead of flight")

        # Check if hotel budget is reasonable
        if hotel_budget.get("amount", 0) < 2000:
            feasibility_issues.append("Accommodation budget may be too low for comfortable stays")
            suggestions.append("Consider budget hotels or hostels")

        # Check if activities budget is reasonable
        if activities_budget.get("amount", 0) < 1000:
            feasibility_issues.append("Activities budget is limited")
            suggestions.append("Focus on free or low-cost attractions")

        # Overall feasibility
        is_feasible = len(feasibility_issues) == 0
        feasibility_status = "Budget appears realistic for the trip" if is_feasible else "Budget may require adjustments"

        budget_data = {
            "total_budget": total_budget,
            "trip_type": state.trip.trip_type,
            "allocation": breakdown,
            "context": {
                "hotel_budget_note": (
                    f"INR {hotel_budget.get('amount', 0):.0f} allocated for accommodation "
                    f"({hotel_budget.get('percentage', 0)}% of total)"
                ),
                "activities_budget_note": (
                    f"INR {activities_budget.get('amount', 0):.0f} available for activities "
                    f"and sightseeing"
                ),
                "food_budget_note": (
                    f"INR {food_budget.get('amount', 0):.0f} set aside for meals and dining"
                ),
                "transport_budget_note": (
                    f"INR {transport_budget.get('amount', 0):.0f} reserved for transport "
                    f"({transport_budget.get('percentage', 0)}% of total)"
                ),
                "budget_tier": (
                    "luxury" if total_budget > 200000
                    else "premium" if total_budget > 100000
                    else "moderate" if total_budget > 50000
                    else "budget"
                ),
                "per_person_budget": round(total_budget / max(state.trip.travelers, 1), 2),
                "feasibility": {
                    "is_feasible": is_feasible,
                    "status": feasibility_status,
                    "issues": feasibility_issues,
                    "suggestions": suggestions
                }
            }
        }

        logger.info("Budget calculation completed")
        return {
            "success": True,
            "data": budget_data
        }