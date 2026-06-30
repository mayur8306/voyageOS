import time
import requests


class HttpClient:

    @staticmethod
    def get(url, params=None, headers=None, max_retries=3):
        last_error = None

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=10
                )

                response.raise_for_status()

                return {
                    "success": True,
                    "data": response.json()
                }

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    time.sleep(wait)
                continue

        return {
            "success": False,
            "message": last_error
        }
