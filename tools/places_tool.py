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

        # Score and rank: prefer major attractions over generic ones
        scored_places = []
        PREMIUM_CATEGORIES = ["tourism.sights", "tourism.attraction", "entertainment.culture"]
        PREMIUM_KEYWORDS = ["temple", "museum", "castle", "palace", "shrine", "park", "garden",
                           "landmark", "monument", "unesco", "waterfall", "beach", "harbour",
                           "cathedral", "church", "mosque", "stadium", "tower", "bridge",
                           "square", "viewpoint", "observatory", "gallery", "theatre",
                           "aquarium", "zoo", "botanical", "national park", "heritage"]
        DEPRIORITIZE_KEYWORDS = ["statue", "memorial", "monument", "marker", "plaque", "bust",
                                "war memorial", "statue of", "monument to", "memorial to"]

        for place in all_places:
            props = place.get("properties", {})
            categories = props.get("categories", [])
            name = props.get("name", "")
            name_lower = name.lower()

            score = 0
            # Premium categories score higher
            for cat in categories:
                if cat in PREMIUM_CATEGORIES:
                    score += 10
            # Premium keywords add bonus
            for kw in PREMIUM_KEYWORDS:
                if kw in name_lower:
                    score += 15
                    break
            # Deprioritize generic POIs
            for kw in DEPRIORITIZE_KEYWORDS:
                if kw in name_lower:
                    score -= 20
                    break
            # Prefer named places
            if name and len(name) > 3:
                score += 5
            # Prefer English-named places
            if props.get("name:en"):
                score += 3

            scored_places.append({"score": score, "place": place, "props": props})

        # Sort by score descending, take top 8
        scored_places.sort(key=lambda x: x["score"], reverse=True)
        top_places = scored_places[:8]

        cleaned_places = []
        for item in top_places:
            props = item["props"]
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

            # Prefer English name
            place_name = props.get("name:en") or props.get("name") or f"Attraction in {destination}"

            cleaned_places.append({
                "name": place_name,
                "name:en": props.get("name:en", ""),
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