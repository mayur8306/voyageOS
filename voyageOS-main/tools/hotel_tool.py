# import json

# from services.geoapify_service import GeoapifyService


# class HotelTool:

#     def __init__(self):
#         self.geo = GeoapifyService()

#     def execute(self, state):

#         destination = state.trip.destination
#         print(f"\nSearching hotels for: {destination}")
#         if not destination:
#             return {
#                 "success": False,
#                 "message": "Destination not available."
#             }

#         location = self.geo.geocode(destination)

#         if not location["success"]:
#             return location

#         latitude = location["data"]["latitude"]
#         longitude = location["data"]["longitude"]

#         hotels = self.geo.search_hotels(
#             latitude=latitude,
#             longitude=longitude,
#             limit=10
#         )

#         print("\n========== RAW HOTELS ==========")
#         print(hotels)
#         print("================================\n")

#         if not hotels["success"]:
#             return hotels


#         cleaned_hotels = []

#         for hotel in hotels["data"]:

#             props = hotel.get("properties", {})

#             cleaned_hotels.append({

#                 "name": props.get("name", "Unknown Hotel"),

#                 "address": props.get("formatted", "Not Available"),

#                 "latitude": props.get("lat"),

#                 "longitude": props.get("lon"),

#                 "hotel_type": "Hotel",

#                 "recommended_for": state.trip.trip_type,

#                 "description": f"Suitable accommodation for a {state.trip.trip_type.lower()} trip."

#             })

#         print("\n========== PARSED HOTELS ==========")
#         print(json.dumps(cleaned_hotels, indent=2))
#         print("===================================\n")       
        
#         return {

#             "success": True,

#             "data": cleaned_hotels

#         }




import json

from services.geoapify_service import GeoapifyService


class HotelTool:

    def __init__(self):

        self.geo = GeoapifyService()

    def execute(self, state):

        destination = state.trip.destination

        if not destination:

            return {
                "success": False,
                "message": "Destination not available."
            }

        print(f"\nSearching hotels for: {destination}")

        location = self.geo.geocode(destination)

        if not location["success"]:
            return location

        latitude = location["data"]["latitude"]
        longitude = location["data"]["longitude"]

        hotels = self.geo.search_hotels(
            latitude=latitude,
            longitude=longitude,
            limit=10
        )

        print("\n========== RAW HOTELS FROM GEOAPIFY ==========")
        print(json.dumps(hotels, indent=2))
        print("==============================================\n")

        if not hotels["success"]:
            return hotels

        cleaned_hotels = []

        for hotel in hotels.get("data", []):

            props = hotel.get("properties", {})

            cleaned_hotels.append({

                "name": props.get("name", "Unknown Hotel"),

                "address": props.get("formatted", "Not Available"),

                "latitude": props.get("lat"),

                "longitude": props.get("lon"),

                "hotel_type": "Hotel",

                "recommended_for": state.trip.trip_type,

                "description": (
                    f"Suitable accommodation for a "
                    f"{state.trip.trip_type.lower()} trip."
                )

            })

        print("\n========== CLEANED HOTELS ==========")
        print(json.dumps(cleaned_hotels, indent=2))
        print(f"\nTotal Hotels Returned: {len(cleaned_hotels)}")
        print("====================================\n")

        return {

            "success": True,

            "data": cleaned_hotels

        }