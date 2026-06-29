import json

from services.geoapify_service import GeoapifyService


class PlacesTool:

    def __init__(self):

        self.geo = GeoapifyService()

    def execute(self, state):

        destination = state.trip.destination

        if not destination:

            return {

                "success": False,

                "message": "Destination not available."

            }

        location = self.geo.geocode(destination)

        if not location["success"]:

            return location

        latitude = location["data"]["latitude"]
        longitude = location["data"]["longitude"]

        places = self.geo.search_places(

            latitude,

            longitude,

            "tourism.sights",

            limit=10

        )

        print("\n========== RAW PLACES FROM GEOAPIFY ==========")
        print(json.dumps(places, indent=2))
        print("==============================================\n")

        if not places["success"]:

            return places


        CATEGORY_INFO = {

            "tourism.sights.ruines": {
                "description": "Historic ruins showcasing the cultural heritage of the region.",
                "best_time": "Morning or Evening",
                "visit_duration": "1-2 hours"
            },

            "tourism.sights.archaeological_site": {
                "description": "Ancient archaeological site with historical importance.",
                "best_time": "Morning",
                "visit_duration": "1-2 hours"
            },

            "tourism.sights.manor": {
                "description": "Historic manor known for its architecture and heritage.",
                "best_time": "Morning or Late Afternoon",
                "visit_duration": "1 hour"
            }

        }
        cleaned_places = []

        for place in places["data"]:

            props = place.get("properties", {})
            categories = props.get("categories", [])

            category = categories[-1] if categories else "Unknown"

            extra = CATEGORY_INFO.get(
                category,
                {
                    "description": "Popular tourist attraction.",
                    "best_time": "Daytime",
                    "visit_duration": "1 hour"
                }
            )

            cleaned_places.append({

                "name": props.get("name", "Unknown"),
                "address": props.get("formatted", "Not Available"),
                "category": category,
                "description": extra["description"],
                "best_time": extra["best_time"],
                "visit_duration": extra["visit_duration"],
                "latitude": props.get("lat"),
                "longitude": props.get("lon")

            })
        print("\n========== CLEANED PLACES ==========")
        print(json.dumps(cleaned_places, indent=2))
        print("====================================\n")

        return {

            "success": True,

            "data": cleaned_places

        }   