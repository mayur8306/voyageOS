import requests


class HttpClient:

    @staticmethod
    def get(url, params=None, headers=None):
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

            return {
                "success": False,
                "message": str(e)
            }