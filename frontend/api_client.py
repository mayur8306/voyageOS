import requests

BASE_URL = "http://127.0.0.1:8000"


class VoyageAPI:

    @staticmethod
    def chat(message):

        response = requests.post(

            f"{BASE_URL}/chat",

            json={

                "message": message

            }

        )

        response.raise_for_status()

        return response.json()

    @staticmethod
    def reset():

        requests.post(

            f"{BASE_URL}/reset"

        )