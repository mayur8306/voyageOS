import json
import logging

from services.geoapify_service import GeoapifyService

logger = logging.getLogger(__name__)


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

        # Use only supported Geoapify Places API v2 categories
        categories = [
            "tourism.sights",
            "tourism.attraction",
            "entertainment.culture",
            "leisure.park"
        ]

        all_places = []
        seen_names = set()

        for category in categories:
            places = self.geo.search_places(
                latitude,
                longitude,
                category,
                limit=5
            )

            if not places["success"]:
                logger.warning(f"Category {category} failed: {places.get('message', 'Unknown error')}")
                continue

            for place in places["data"]:
                props = place.get("properties", {})
                name = props.get("name", "")

                # Skip unnamed results
                if not name:
                    continue

                # Skip obvious non-tourist entities
                name_lower = name.lower()
                skip_keywords = [
                    "parking", "toilet", "restroom", "atm", "gas station",
                    "petrol", "pharmacy", "hospital", "clinic", "dentist",
                    "police", "fire", "school", "college", "university",
                    "office", "bank", "supermarket", "grocery", "mall"
                ]
                if any(kw in name_lower for kw in skip_keywords):
                    continue

                # Deduplicate by name
                if name in seen_names:
                    continue
                seen_names.add(name)

                all_places.append(place)

        if not all_places:
            logger.warning(f"No tourist attractions found for {destination} after trying {len(categories)} categories")
            return {
                "success": False,
                "message": "No tourist attractions found for this destination."
            }

        CATEGORY_INFO = {
            "tourism.sights": {
                "description": "Popular tourist sight worth visiting.",
                "best_time": "Daytime",
                "visit_duration": "1-2 hours"
            },
            "tourism.attraction": {
                "description": "Popular tourist attraction.",
                "best_time": "Daytime",
                "visit_duration": "1-2 hours"
            },
            "entertainment.culture": {
                "description": "Cultural entertainment venue.",
                "best_time": "Evening",
                "visit_duration": "2-3 hours"
            },
            "leisure.park": {
                "description": "Public park offering green space and recreational activities.",
                "best_time": "Morning or Late Afternoon",
                "visit_duration": "1-2 hours"
            }
        }

        cleaned_places = []

        for place in all_places[:10]:
            props = place.get("properties", {})
            categories = props.get("categories", [])

            # Find the most specific category match
            category = "Unknown"
            for cat in reversed(categories):
                if cat in CATEGORY_INFO:
                    category = cat
                    break
            if category == "Unknown" and categories:
                category = categories[-1]

            extra = CATEGORY_INFO.get(
                category,
                {
                    "description": "Popular tourist attraction worth visiting.",
                    "best_time": "Daytime",
                    "visit_duration": "1 hour"
                }
            )

            place_name = props.get("name")
            if not place_name:
                place_name = f"Attraction in {destination}"

            cleaned_places.append({
                "name": place_name,
                "address": props.get("formatted", "Address not available"),
                "category": category,
                "description": extra["description"],
                "best_time": extra["best_time"],
                "visit_duration": extra["visit_duration"],
                "latitude": props.get("lat"),
                "longitude": props.get("lon")
            })

        logger.info(f"Found {len(cleaned_places)} attractions for {destination}")
        return {
            "success": True,
            "data": cleaned_places
        }