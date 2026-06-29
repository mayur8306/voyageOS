def format_budget(budget):

    allocation = budget.get("allocation", {})

    text = f"""
==============================
BUDGET
==============================

Total Budget: ₹{budget.get("total_budget")}

Trip Type: {budget.get("trip_type")}

Allocation

"""

    for category, info in allocation.items():

        text += (
            f"- {category.title()}: "
            f"{info['percentage']}% "
            f"(₹{info['amount']})\n"
        )

    return text


def format_weather(weather):

    return f"""
==============================
WEATHER
==============================

Temperature: {weather.get("temperature")}°C

Feels Like: {weather.get("feels_like")}°C

Humidity: {weather.get("humidity")}%

Wind Speed: {weather.get("wind_speed")}

Condition: {weather.get("condition")}

Precipitation: {weather.get("precipitation")}
"""

def format_transport(transport):

    flight = transport.get("flight", {})
    train = transport.get("train", {})
    bus = transport.get("bus", {})

    return f"""
==============================
TRANSPORT
==============================

Flight

Duration:
{flight.get("duration")}

Price:
{flight.get("price_range")}

Operators:
{", ".join(flight.get("operators", []))}

--------------------------------

Train

Duration:
{train.get("duration")}

Price:
{train.get("price_range")}

Operators:
{", ".join(train.get("operators", []))}

--------------------------------

Bus

Duration:
{bus.get("duration")}

Price:
{bus.get("price_range")}

Operators:
{", ".join(bus.get("operators", []))}

--------------------------------

Recommended

{transport.get("recommended_option")}

Reason

{transport.get("reason")}
"""

def format_hotels(hotels):

    text = """
==============================
HOTELS
==============================

"""

    for i, hotel in enumerate(hotels, start=1):

        text += f"""
Hotel {i}

Name:
{hotel["name"]}

Address:
{hotel["address"]}

Recommended For:
{hotel["recommended_for"]}

Description:
{hotel["description"]}

--------------------------------

"""

    return text

def format_places(places):

    text = """
==============================
ATTRACTIONS
==============================

"""

    for i, place in enumerate(places, start=1):

        text += f"""
Attraction {i}

Name:
{place["name"]}

Category:
{place["category"]}

Description:
{place["description"]}

Best Time:
{place["best_time"]}

Visit Duration:
{place["visit_duration"]}

Address:
{place["address"]}

--------------------------------

"""

    return text

def format_trip(trip):

    return f"""
==============================
TRIP DETAILS
==============================

Origin:
{trip.origin}

Destination:
{trip.destination}

Travelers:
{trip.travelers}

Trip Type:
{trip.trip_type}

Budget:
₹{trip.budget}

Duration:
{trip.duration}
"""