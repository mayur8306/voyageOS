# class BudgetTool:


#     def execute(self, state):

#         total_budget = state.trip.budget
#         if total_budget <= 0:

#             return {

#                 "success": False,

#                 "message": "Invalid budget."

#             }
#         trip_type = state.trip.trip_type.lower()

#         allocations = {

#             "honeymoon": {
#                 "hotel": 0.45,
#                 "transport": 0.20,
#                 "food": 0.15,
#                 "activities": 0.15,
#                 "emergency": 0.05
#             },

#             "family": {
#                 "hotel": 0.40,
#                 "transport": 0.20,
#                 "food": 0.20,
#                 "activities": 0.15,
#                 "emergency": 0.05
#             },

#             "solo": {
#                 "hotel": 0.30,
#                 "transport": 0.20,
#                 "food": 0.20,
#                 "activities": 0.25,
#                 "emergency": 0.05
#             },

#             "friends": {
#                 "hotel": 0.35,
#                 "transport": 0.20,
#                 "food": 0.20,
#                 "activities": 0.20,
#                 "emergency": 0.05
#             },

#             "business": {
#                 "hotel": 0.35,
#                 "transport": 0.30,
#                 "food": 0.20,
#                 "activities": 0.10,
#                 "emergency": 0.05
#             }

#         }

#         percentages = allocations.get(

#             trip_type,

#             allocations["family"]

#         )

#         breakdown = {}

#         for category, percentage in percentages.items():

#             breakdown[category] = {

#                 "percentage": int(percentage * 100),

#                 "amount": round(total_budget * percentage, 2)

#             }

#         return {

#             "success": True,

#             "data": {

#                 "total_budget": total_budget,

#                 "trip_type": state.trip.trip_type,

#                 "allocation": breakdown

#             }

#         }


import json


class BudgetTool:

    def execute(self, state):

        total_budget = state.trip.budget

        if total_budget <= 0:

            return {
                "success": False,
                "message": "Invalid budget."
            }

        print(f"\nCalculating budget for ₹{total_budget}")

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

        budget_data = {

            "total_budget": total_budget,

            "trip_type": state.trip.trip_type,

            "allocation": breakdown

        }

        print("\n========== BUDGET ==========")
        print(json.dumps(budget_data, indent=2))
        print("============================\n")

        return {

            "success": True,

            "data": budget_data

        }