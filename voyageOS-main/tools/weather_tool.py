# import json

# from services.geoapify_service import GeoapifyService
# from services.weather_service import WeatherService


# class WeatherTool:

#     def __init__(self):

#         self.geo = GeoapifyService()
#         self.weather = WeatherService()

#     def execute(self, state):

#         destination = state.trip.destination

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

#         weather = self.weather.get_current_weather(

#             latitude,

#             longitude

#         )
#         print(f"\nSearching weather for: {destination}")

#         print("\n========== RAW WEATHER ==========")
#         print(json.dumps(weather, indent=2))
#         print("================================\n")

#         if not weather["success"]:

#             return weather

#         current = weather["data"]["current"]

#         return {

#             "success": True,

#             "data": {

#                 "temperature": current.get("temperature_2m"),

#                 "feels_like": current.get("apparent_temperature"),

#                 "humidity": current.get("relative_humidity_2m"),

#                 "wind_speed": current.get("wind_speed_10m"),

#                 "precipitation": current.get("precipitation"),

#                 "condition": WeatherService.WEATHER_CODES.get(
#                     current.get("weather_code"),
#                     "Unknown"
#                 )

#             }

#         }



import json

from services.geoapify_service import GeoapifyService
from services.weather_service import WeatherService


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

        print(f"\nSearching weather for: {destination}")

        location = self.geo.geocode(destination)

        if not location["success"]:
            return location

        latitude = location["data"]["latitude"]
        longitude = location["data"]["longitude"]

        weather = self.weather.get_current_weather(
            latitude,
            longitude
        )

        print("\n========== RAW WEATHER ==========")
        print(json.dumps(weather, indent=2))
        print("=================================\n")

        if not weather["success"]:
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
                "Unknown"
            )

        }

        print("\n========== CLEANED WEATHER ==========")
        print(json.dumps(cleaned_weather, indent=2))
        print("=====================================\n")

        return {

            "success": True,

            "data": cleaned_weather

        }