def _safe(val, suffix=""):
    if val is None:
        return None
    return f"{val}{suffix}"


def _format_operators(operators):
    if not operators:
        return None
    if not isinstance(operators, (list, tuple)):
        return str(operators)
    return ", ".join(str(op) for op in operators)


def _format_mode_options(options, mode_label):
    """Format up to 3 transport options into individual option blocks."""
    if not options:
        return None

    lines = []
    for i, opt in enumerate(options, start=1):
        if not isinstance(opt, dict):
            continue
        name = opt.get("name")
        duration = opt.get("duration")
        price = opt.get("price")
        operators = _format_operators(opt.get("operators"))
        booking_source = opt.get("booking_source")
        booking_url = opt.get("booking_url")

        # Skip options with no real data
        if not name and not duration and not price:
            continue

        lines.append(f"  Option {i}: {name or 'Unnamed option'}")
        if duration:
            lines.append(f"    Duration: {duration}")
        if price:
            lines.append(f"    Price: {price}")
        if operators:
            lines.append(f"    Operator: {operators}")
        if booking_source:
            lines.append(f"    Booking Source: {booking_source}")
        if booking_url:
            lines.append(f"    Booking URL: {booking_url}")
        lines.append("")

    if not lines:
        return None
    return "\n".join(lines)


def _format_mode_section(mode_key, transport, mode_label, emoji):
    """Format a single transport mode section (Flight, Train, or Bus)."""
    if not isinstance(transport, dict):
        return None
    
    mode_data = transport.get(mode_key, {})
    if not isinstance(mode_data, dict):
        return None
    
    summary = mode_data.get("summary", {})
    options = mode_data.get("options", [])

    if not summary.get("found"):
        return None

    text = f"""
{emoji} {mode_label.upper()} OPTIONS

"""

    # Summary line
    duration = summary.get("duration")
    price_range = summary.get("price_range")
    operators = _format_operators(summary.get("operators"))
    booking_sources = summary.get("booking_sources", [])

    if duration:
        text += f"Best Duration: {duration}\n"
    if price_range:
        text += f"Price Range: {price_range}\n"
    if operators:
        text += f"Operators: {operators}\n"
    if booking_sources:
        text += f"Booking Sources: {', '.join(booking_sources)}\n"

    text += "\n"

    # Individual options
    options_text = _format_mode_options(options, mode_label)
    if options_text:
        text += options_text
    else:
        text += "  No individual options could be verified.\n"

    text += "---\n"

    return text


def format_budget(budget):

    if not isinstance(budget, dict):
        return None

    allocation = budget.get("allocation", {})

    total = budget.get("total_budget")
    total_str = f"INR {total}" if total is not None else None

    context = budget.get("context", {})
    budget_tier = context.get("budget_tier")
    per_person = context.get("per_person_budget")
    feasibility = context.get("feasibility", {})

    text = """
BUDGET
==============================

"""

    if total_str:
        text += f"Total Budget: {total_str}\n"
    if budget.get("trip_type"):
        text += f"Trip Type: {budget.get('trip_type')}\n"
    if budget_tier:
        text += f"Budget Tier: {budget_tier}\n"
    if per_person:
        text += f"Per Person Budget: INR {per_person}\n"

    text += "\nAllocation:\n\n"

    if isinstance(allocation, dict):
        for category, info in allocation.items():
            if isinstance(info, dict):
                percentage = info.get('percentage')
                amount = info.get('amount')
                if percentage and amount:
                    text += f"- {category.title()}: {percentage}% (INR {amount})\n"

    # Context notes
    if isinstance(context, dict):
        notes = []
        for key in ["hotel_budget_note", "activities_budget_note", "food_budget_note", "transport_budget_note"]:
            note = context.get(key)
            if note:
                notes.append(f"- {note}")
        if notes:
            text += "\n" + "\n".join(notes) + "\n"

    # Budget feasibility
    if isinstance(feasibility, dict) and feasibility:
        is_feasible = feasibility.get("is_feasible", True)
        status = feasibility.get("status")
        issues = feasibility.get("issues", [])
        suggestions = feasibility.get("suggestions", [])

        text += f"""
BUDGET FEASIBILITY

Status: {"✓" if is_feasible else "⚠"} {status or "Budget assessment completed"}
"""

        if issues:
            text += "\nConcerns:\n"
            for issue in issues:
                if isinstance(issue, str):
                    text += f"- {issue}\n"

        if suggestions:
            text += "\nSuggestions:\n"
            for suggestion in suggestions:
                if isinstance(suggestion, str):
                    text += f"- {suggestion}\n"

    return text


def format_weather(weather):

    if not isinstance(weather, dict):
        return None

    temp = _safe(weather.get("temperature"), "°C")
    feels_like = _safe(weather.get("feels_like"), "°C")
    humidity = _safe(weather.get("humidity"), "%")
    wind_speed = _safe(weather.get("wind_speed"))
    condition = weather.get("condition")
    precipitation = _safe(weather.get("precipitation"))

    text = """
WEATHER
==============================

"""

    if condition:
        text += f"Condition: {condition}\n"
    if temp:
        text += f"Temperature: {temp}\n"
    if feels_like:
        text += f"Feels Like: {feels_like}\n"
    if humidity:
        text += f"Humidity: {humidity}\n"
    if wind_speed:
        text += f"Wind Speed: {wind_speed}\n"
    if precipitation:
        text += f"Precipitation: {precipitation}\n"

    return text


def format_transport(transport):

    if not isinstance(transport, dict):
        return None

    text = """
TRANSPORT
==============================

"""

    # Flight section
    flight_section = _format_mode_section("flight", transport, "Flight", "✈")
    if flight_section:
        text += flight_section

    # Train section
    train_section = _format_mode_section("train", transport, "Train", "🚆")
    if train_section:
        text += train_section

    # Bus section
    bus_section = _format_mode_section("bus", transport, "Bus", "🚌")
    if bus_section:
        text += bus_section

    # Recommendation
    recommended = transport.get("recommended_option")
    reason = transport.get("reason")

    if recommended or reason:
        text += """
RECOMMENDATION

"""
        if recommended:
            text += f"Recommended Option: {recommended}\n"
        if reason:
            text += f"Reason: {reason}\n"

    return text


def format_hotels(hotels):

    if not hotels or not isinstance(hotels, list):
        return None

    text = """
HOTELS
==============================

"""

    for i, hotel in enumerate(hotels, start=1):
        if not isinstance(hotel, dict):
            continue
            
        name = hotel.get("name")
        address = hotel.get("address")
        trip_type = hotel.get("trip_type")
        destination = hotel.get("destination")

        if not name:
            continue

        text += f"""
### {name}

"""
        if address:
            text += f"Address: {address}\n"
        if trip_type and destination:
            text += f"\nWhy this fits your trip: [LLM will generate unique explanation based on {trip_type} trip to {destination}]\n"
        text += "\n"

    return text if text.strip() else None


def format_places(places):

    if not places or not isinstance(places, list):
        return None

    text = """
ATTRACTIONS
==============================

"""

    for i, place in enumerate(places, start=1):
        if not isinstance(place, dict):
            continue
            
        name = place.get("name")
        category = place.get("category")
        description = place.get("description")
        best_time = place.get("best_time")
        visit_duration = place.get("visit_duration")
        address = place.get("address")

        if not name:
            continue

        text += f"""
### {name} -- {category or 'Attraction'}

"""
        if description:
            text += f"Description: {description}\n"
        if best_time:
            text += f"Best time to visit: {best_time}\n"
        if visit_duration:
            text += f"Suggested duration: {visit_duration}\n"
        if address:
            text += f"Address: {address}\n"
        text += "\n"

    return text if text.strip() else None


def format_trip(trip):

    if not hasattr(trip, 'origin'):
        return None

    text = """
TRIP DETAILS
==============================

"""

    if trip.origin:
        text += f"Origin: {trip.origin}\n"
    if trip.destination:
        text += f"Destination: {trip.destination}\n"
    if hasattr(trip, 'travelers') and trip.travelers and trip.travelers > 0:
        text += f"Travelers: {trip.travelers}\n"
    if trip.trip_type:
        text += f"Trip Type: {trip.trip_type}\n"
    if hasattr(trip, 'budget') and trip.budget and trip.budget > 0:
        text += f"Budget: INR {trip.budget}\n"
    if hasattr(trip, 'duration') and trip.duration and trip.duration > 0:
        text += f"Duration: {trip.duration} days\n"

    return text