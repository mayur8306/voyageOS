import requests
import logging

from utils.config import Config

logger = logging.getLogger(__name__)


class GeoapifyService:

    BASE_URL = "https://api.geoapify.com/v2"

    # Primary tourist cities for countries (for international destination handling)
    COUNTRY_PRIMARY_CITIES = {
        "japan": "Tokyo",
        "france": "Paris",
        "italy": "Rome",
        "usa": "New York",
        "united states": "New York",
        "australia": "Sydney",
        "spain": "Madrid",
        "uk": "London",
        "united kingdom": "London",
        "germany": "Berlin",
        "thailand": "Bangkok",
        "singapore": "Singapore",
        "dubai": "Dubai",
        "uae": "Dubai",
        "canada": "Toronto",
        "switzerland": "Zurich",
        "netherlands": "Amsterdam",
        "turkey": "Istanbul",
        "egypt": "Cairo",
        "greece": "Athens"
    }

    # Valid Geoapify category prefixes
    VALID_CATEGORIES = {
        "tourism",
        "entertainment",
        "leisure",
        "heritage",
        "accommodation"
    }

    def __init__(self):

        self.api_key = Config.GEOAPIFY_API_KEY

    def _validate_category(self, category):
        """Validate that category follows Geoapify format."""
        if not category:
            return False
        # Category should be like "tourism.sights" or "tourism.attraction"
        parts = category.split(".")
        if len(parts) >= 2 and parts[0] in self.VALID_CATEGORIES:
            return True
        return False

    def geocode(self, location_name):

        if not location_name:
            return {
                "success": False,
                "message": "Location name is required."
            }

        # Check if it's a country name - use primary tourist city
        location_lower = location_name.lower().strip()
        if location_lower in self.COUNTRY_PRIMARY_CITIES:
            primary_city = self.COUNTRY_PRIMARY_CITIES[location_lower]
            logger.info(f"Country destination detected: {location_name} → using {primary_city}")
            location_name = primary_city

        url = f"{self.BASE_URL}/geocode/search"

        params = {
            "text": location_name,
            "apiKey": self.api_key,
            "limit": 1
        }

        try:

            response = requests.get(url, params=params, timeout=10)

            response.raise_for_status()

            data = response.json()

            if data.get("features"):

                feature = data["features"][0]
                coords = feature["geometry"]["coordinates"]
                properties = feature["properties"]

                logger.info(f"Geocoded: {location_name} → {properties.get('city', 'Unknown')}")

                return {
                    "success": True,
                    "data": {
                        "latitude": coords[1],
                        "longitude": coords[0],
                        "formatted": properties.get("formatted", location_name),
                        "city": properties.get("city", location_name),
                        "country": properties.get("country", "")
                    }
                }

            else:

                return {
                    "success": False,
                    "message": f"Location not found: {location_name}"
                }

        except requests.exceptions.RequestException as e:

            logger.error(f"Geocoding error: {str(e)}")
            return {
                "success": False,
                "message": f"Geocoding failed: {str(e)}"
            }

    def search_places(self, latitude, longitude, category, limit=10):

        if not self._validate_category(category):
            logger.warning(f"Invalid category format: {category}")
            return {
                "success": False,
                "message": f"Invalid category format: {category}"
            }

        url = f"{self.BASE_URL}/places"

        params = {
            "categories": category,
            "filter": f"circle:{longitude},{latitude},50000",
            "limit": limit,
            "apiKey": self.api_key
        }

        try:

            response = requests.get(
                url,
                params=params,
                timeout=10
            )

            if response.status_code != 200:

                logger.error("=" * 80)
                logger.error("Geoapify Request Failed (search_places)")
                logger.error(f"Status : {response.status_code}")
                logger.error(f"URL    : {response.url}")
                logger.error(f"Params : {params}")
                logger.error(f"Headers: {dict(response.headers)}")
                logger.error(f"Body:\n{response.text}")
                logger.error("=" * 80)

                try:
                    error = response.json()
                    message = error.get("message", response.text)
                except Exception:
                    message = response.text

                return {
                    "success": False,
                    "message": message
                }

            data = response.json()

            return {
                "success": True,
                "data": data.get("features", [])
            }

        except Exception as e:

            logger.exception("Geoapify search_places exception")

            return {
                "success": False,
                "message": str(e)
            }

    def search_hotels(self, latitude, longitude, limit=10):

        url = f"{self.BASE_URL}/places"

        params = {
            "categories": "accommodation.hotel",
            "filter": f"circle:{longitude},{latitude},10000",
            "limit": limit,
            "apiKey": self.api_key
        }

        try:

            response = requests.get(
                url,
                params=params,
                timeout=10
            )

            if response.status_code != 200:

                logger.error("=" * 80)
                logger.error("Geoapify Request Failed (search_hotels)")
                logger.error(f"Status : {response.status_code}")
                logger.error(f"URL    : {response.url}")
                logger.error(f"Params : {params}")
                logger.error(f"Headers: {dict(response.headers)}")
                logger.error(f"Body:\n{response.text}")
                logger.error("=" * 80)

                try:
                    error = response.json()
                    message = error.get("message", response.text)
                except Exception:
                    message = response.text

                return {
                    "success": False,
                    "message": message
                }

            data = response.json()

            return {
                "success": True,
                "data": data.get("features", [])
            }

        except Exception as e:

            logger.exception("Geoapify search_hotels exception")

            return {
                "success": False,
                "message": str(e)
            }