import json
import logging

from services.geoapify_service import GeoapifyService
from services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class WeatherTool:

    def __init__(self):

        self.geo = GeoapifyService()
        self.weather = WeatherService()

    def execute(self, state):

        destination = state.trip.destination

        if not destination:

            return {
                "success": False,
                "message": "Destination not available."
            }

        logger.info(f"Searching weather for: {destination}")

        location = self.geo.geocode(destination)

        if not location["success"]:
            return location

        latitude = location["data"]["latitude"]
        longitude = location["data"]["longitude"]

        weather = self.weather.get_current_weather(
            latitude,
            longitude
        )

        if not weather["success"]:
            logger.warning(f"Weather fetch failed for {destination}")
            return weather

        current = weather["data"]["current"]

        cleaned_weather = {

            "temperature": current.get("temperature_2m"),

            "feels_like": current.get("apparent_temperature"),

            "humidity": current.get("relative_humidity_2m"),

            "wind_speed": current.get("wind_speed_10m"),

            "precipitation": current.get("precipitation"),

            "condition": WeatherService.WEATHER_CODES.get(
                current.get("weather_code"),
                "Weather data available -- check local forecast"
            )

        }

        logger.info(f"Weather data retrieved for {destination}")
        return {

            "success": True,

            "data": cleaned_weather

        }