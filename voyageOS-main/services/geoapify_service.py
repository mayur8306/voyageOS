from utils.http_client import HttpClient
from utils.config import Config


class GeoapifyService:

    BASE_URL = "https://api.geoapify.com/v1"

    def __init__(self):
        self.api_key = Config.GEOAPIFY_API_KEY

    # -------------------------------------------------------
    # Convert city into Latitude & Longitude
    # -------------------------------------------------------

    def geocode(self, city: str):

        response = HttpClient.get(

            f"{self.BASE_URL}/geocode/search",

            params={
                "text": city,
                "apiKey": self.api_key
            }

        )

        if not response["success"]:
            return response

        features = response["data"].get("features", [])

        if not features:
            return {
                "success": False,
                "message": "City not found."
            }

        coordinates = features[0]["geometry"]["coordinates"]

        return {

            "success": True,

            "data": {

                "longitude": coordinates[0],

                "latitude": coordinates[1]

            }

        }

    # -------------------------------------------------------
    # Search Nearby Places
    # -------------------------------------------------------

    def search_places(
        self,
        latitude,
        longitude,
        categories,
        limit=10
    ):

        response = HttpClient.get(

            "https://api.geoapify.com/v2/places",

            params={

                "categories": categories,

                "filter": f"circle:{longitude},{latitude},10000",

                "limit": limit,

                "apiKey": self.api_key

            }

        )

        if not response["success"]:
            return response

        return {

            "success": True,

            "data": response["data"].get("features", [])

        }
        
        

    def search_hotels(
        self,
        latitude,
        longitude,
        limit=10
    ):
        return self.search_places(
            latitude=latitude,
            longitude=longitude,
            categories="accommodation.hotel",
            limit=limit
        )