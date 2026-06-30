import json
import logging

from services.geoapify_service import GeoapifyService

logger = logging.getLogger(__name__)


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

        logger.info(f"Searching hotels for: {destination}")

        location = self.geo.geocode(destination)

        if not location["success"]:
            return location

        latitude = location["data"]["latitude"]
        longitude = location["data"]["longitude"]

        hotels = self.geo.search_hotels(
            latitude=latitude,
            longitude=longitude,
            limit=15
        )

        if not hotels["success"]:
            logger.warning(f"Hotel search failed for {destination}")
            return hotels

        # Score and rank hotels
        scored_hotels = []

        for hotel in hotels.get("data", []):
            props = hotel.get("properties", {})
            name = props.get("name", "")
            categories = props.get("categories", [])
            categories_str = " ".join(categories).lower()

            # Calculate a quality score (higher = better)
            score = 0

            # Prefer named hotels over generic entries
            if name and len(name) > 3:
                score += 10

            # Prefer accommodation.hotel category specifically
            if "accommodation.hotel" in categories_str:
                score += 20
            elif "accommodation" in categories_str:
                score += 10

            # Penalize generic or non-hotel categories
            if "accommodation.hostel" in categories_str:
                score -= 5
            if "accommodation.guest_house" in categories_str:
                score -= 2

            # Prefer results with complete address
            if props.get("formatted"):
                score += 5

            # Prefer results with contact info
            if props.get("contact", {}).get("phone"):
                score += 3
            if props.get("contact", {}).get("website"):
                score += 2

            scored_hotels.append({
                "score": score,
                "name": name,
                "address": props.get("formatted", ""),
                "latitude": props.get("lat"),
                "longitude": props.get("lon"),
                "categories": categories,
                "contact": props.get("contact", {})
            })

        # Sort by score descending, take top 10
        scored_hotels.sort(key=lambda h: h["score"], reverse=True)
        top_hotels = scored_hotels[:10]

        cleaned_hotels = []

        for hotel in top_hotels:
            name = hotel["name"] or f"Hotel near {destination}"
            address = hotel["address"] or "Address not available"

            cleaned_hotels.append({
                "name": name,
                "address": address,
                "latitude": hotel["latitude"],
                "longitude": hotel["longitude"],
                "hotel_type": "Hotel",
                "trip_type": state.trip.trip_type,
                "destination": destination
            })

        logger.info(f"Found {len(cleaned_hotels)} hotels for {destination}")
        return {
            "success": True,
            "data": cleaned_hotels
        }