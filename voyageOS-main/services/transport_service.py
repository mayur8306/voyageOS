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



















# class TransportService:

#     def search_transport(self, origin: str, destination: str):

#         query = (
#             f"{origin} to {destination} "
#             "flight duration airfare train duration "
#             "bus fare operators travel options"
#         )

#         with DDGS() as ddgs:

#             flight_results = list(
#                 ddgs.text(
#                     f"{origin} to {destination} flight duration airfare airlines",
#                     max_results=3
#                 )
#             )

#             train_results = list(
#                 ddgs.text(
#                     f"{origin} to {destination} train duration fare operators",
#                     max_results=3
#                 )
#             )

#             bus_results = list(
#                 ddgs.text(
#                     f"{origin} to {destination} bus duration fare operators",
#                     max_results=3
#                 )
#             )

#         combined_text = ""

#         transport_results = {
#             "Flight": flight_results,
#             "Train": train_results,
#             "Bus": bus_results
#         }

#         for mode, results in transport_results.items():

#             combined_text += f"\n========== {mode.upper()} ==========\n"

#             for i, result in enumerate(results, start=1):

#                 combined_text += f"""
#         Result {i}

#         Title:
#         {result.get("title")}

#         Summary:
#         {result.get("body")}

#         Source:
#         {result.get("href")}

#         ------------------------------------
#         """


#         return {

#             "success": True,

#             "data": combined_text

#         }