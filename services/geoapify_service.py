import requests
import logging

from utils.config import Config

logger = logging.getLogger(__name__)


class GeoapifyService:

    # Geoapify uses different API versions for different services
    GEOCODE_BASE_URL = "https://api.geoapify.com/v1"
    PLACES_BASE_URL = "https://api.geoapify.com/v2"

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

    # Official Geoapify Places API v2 categories
    # Reference: https://apidocs.geoapify.com/docs/places/#categories
    VALID_PLACES_CATEGORIES = {
        # Tourism
        "tourism.sights",
        "tourism.attraction",
        "tourism.museum",
        "tourism.castle",
        "tourism.ruins",
        "tourism.archaeological_site",
        "tourism.lighthouse",
        "tourism.manor",
        "tourism.monument",
        # Entertainment & Culture
        "entertainment.culture",
        "entertainment.culture.theatre",
        "entertainment.culture.gallery",
        # Leisure
        "leisure.park",
        "leisure.playground",
        "leisure.sports_centre",
        # Heritage
        "heritage",
        "heritage.site",
        # Accommodation
        "accommodation",
        "accommodation.hotel",
        "accommodation.guest_house",
        "accommodation.hostel",
        "accommodation.resort",
        "accommodation.motel"
    }

    def __init__(self):

        self.api_key = Config.GEOAPIFY_API_KEY

    def _validate_category(self, category):
        """Validate that category follows Geoapify format."""
        if not category:
            return False
        # Category should be like "tourism.sights" or "tourism.attraction"
        parts = category.split(".")
        if len(parts) >= 2 and parts[0] in self.VALID_PLACES_CATEGORIES:
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

        # Use v1 endpoint for geocoding
        url = f"{self.GEOCODE_BASE_URL}/geocode/search"

        params = {
            "text": location_name,
            "apiKey": self.api_key,
            "limit": 1
        }

        try:

            response = requests.get(url, params=params, timeout=30)

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
        """
        Search for places using Geoapify Places API v2.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            category: Geoapify category (e.g., 'tourism.sights')
            limit: Maximum number of results
            
        Returns:
            Dict with success status and data
        """
        # Use v2 endpoint for places
        url = f"{self.PLACES_BASE_URL}/places"

        # Geoapify v2 uses 'circle' filter with lon,lat format
        params = {
            "categories": category,
            "filter": f"circle:{longitude},{latitude},50000",
            "limit": limit,
            "apiKey": self.api_key
        }

        try:

            response = requests.get(url, params=params, timeout=30)
            
            # Log full details on failure
            if response.status_code != 200:
                logger.error("=" * 80)
                logger.error("Geoapify Request Failed - search_places")
                logger.error(f"Status: {response.status_code}")
                logger.error(f"URL: {response.url}")
                logger.error(f"Params: {params}")
                logger.error(f"Headers: {dict(response.headers)}")
                logger.error(f"Body: {response.text}")
                logger.error("=" * 80)
                
                # Extract actual error message
                try:
                    error_data = response.json()
                    message = error_data.get("message", response.text)
                except Exception:
                    message = response.text
                
                return {
                    "success": False,
                    "message": f"Geoapify error: {message}"
                }
            
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "data": data.get("features", [])
            }

        except requests.exceptions.RequestException as e:

            logger.error(f"Places search error: {str(e)}")
            return {
                "success": False,
                "message": f"Places search failed: {str(e)}"
            }

    def search_hotels(self, latitude, longitude, limit=10):
        """
        Search for hotels using Geoapify Places API v2.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            limit: Maximum number of results
            
        Returns:
            Dict with success status and data
        """
        logger.info(f"[Geoapify.search_hotels] ENTRY: latitude={latitude}, longitude={longitude}, limit={limit}, search_radius=10000m")
        
        # Use v2 endpoint for places
        url = f"{self.PLACES_BASE_URL}/places"

        # Use official accommodation categories
        categories = (
            "accommodation,"
            "accommodation.hotel,"
            "accommodation.hostel,"
            "accommodation.guest_house"
        )
        logger.info(f"[Geoapify.search_hotels] categories being searched: {categories}")
                
        # Geoapify v2 uses 'circle' filter with lon,lat format
        params = {
            "categories": categories,
            "filter": f"circle:{longitude},{latitude},10000",
            "limit": limit,
            "apiKey": self.api_key
        }
        
        logger.info(f"[Geoapify.search_hotels] REQUEST: url={url}, params={params}")

        try:

            response = requests.get(url, params=params, timeout=30)
            logger.info(f"[Geoapify.search_hotels] HTTP status code: {response.status_code}")
            
            # Log full details on failure
            if response.status_code != 200:
                logger.error("=" * 80)
                logger.error("Geoapify Request Failed - search_hotels")
                logger.error(f"Status: {response.status_code}")
                logger.error(f"URL: {response.url}")
                logger.error(f"Params: {params}")
                logger.error(f"Headers: {dict(response.headers)}")
                logger.error(f"Body: {response.text}")
                logger.error("=" * 80)
                
                # Extract actual error message
                try:
                    error_data = response.json()
                    message = error_data.get("message", response.text)
                except Exception:
                    message = response.text
                
                logger.info(f"[Geoapify.search_hotels] RETURNING failure (status != 200): success=False, message='{message}'")
                return {
                    "success": False,
                    "message": f"Geoapify error: {message}"
                }
            
            response.raise_for_status()
            data = response.json()
            logger.info(f"[Geoapify.search_hotels] Raw response body (first 500 chars): {str(data)[:500]}")
            
            features = data.get("features", [])
            logger.info(f"[Geoapify.search_hotels] Features count in raw response: {len(features)}")

            logger.info(f"[Geoapify.search_hotels] RETURNING success: success=True, hotels_count={len(features)}")
            return {
                "success": True,
                "data": features
            }

        except requests.exceptions.RequestException as e:

            logger.error(f"Hotel search error: {str(e)}")
            logger.info(f"[Geoapify.search_hotels] RETURNING failure (exception): success=False, error='{str(e)}'")
            return {
                "success": False,
                "message": f"Hotel search failed: {str(e)}"
            }
