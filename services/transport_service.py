from ddgs import DDGS

class TransportService:

    def search_transport(self, origin, destination):

        with DDGS() as ddgs:

            flight_results = list(
                ddgs.text(
                    f"{origin} to {destination} flight duration airfare airlines",
                    max_results=3
                )
            )

            train_results = list(
                ddgs.text(
                    f"{origin} to {destination} train duration fare operators",
                    max_results=3
                )
            )

            bus_results = list(
                ddgs.text(
                    f"{origin} to {destination} bus duration fare operators",
                    max_results=3
                )
            )

        return {

            "success": True,

            "data": {

                "flight": flight_results,

                "train": train_results,

                "bus": bus_results

            }

        }