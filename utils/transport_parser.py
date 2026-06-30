import re
import logging

logger = logging.getLogger(__name__)

AIRLINES = [
    "Air India",
    "Air India Express",
    "IndiGo",
    "Akasa Air",
    "SpiceJet",
    "Alliance Air",
    "Vistara"
]

TRAIN_OPERATORS = [
    "Indian Railways",
    "Konkan Railway"
]

BUS_OPERATORS = [
    "RedBus",
    "IntrCity SmartBus",
    "Zing Bus",
    "KTCL",
    "Kadamba Transport Corporation Limited",
    "Naik Tours & Travels"
]

BOOKING_SOURCES = [
    "MakeMyTrip",
    "IRCTC",
    "ixigo",
    "EaseMyTrip",
    "Cleartrip",
    "Yatra",
    "Goibibo",
    "Paytm",
    "Amazon",
    "Booking.com",
    "Agoda",
    "redBus",
    "Abhibus",
    "IntrCity",
    "FlixBus",
    "Trainman",
    "Confirmtkt",
    "12Go",
    "Rome2rio"
]

# Realistic duration ranges in minutes
DURATION_RANGES = {
    "flight": (60, 480),      # 1-8 hours
    "train": (300, 3600),     # 5-60 hours
    "bus": (240, 4200)        # 4-70 hours
}


def unique(items):
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def find_booking_source(text):
    """Extract booking platform name from text."""
    lower = text.lower()
    for source in BOOKING_SOURCES:
        if source.lower() in lower:
            return source
    # Try to extract domain-like name from URL
    urls = re.findall(r"https?://(?:www\.)?([^/\s]+)", text)
    for url in urls:
        parts = url.split(".")
        if parts[0] != "www" and len(parts) > 1:
            return parts[0].title()
    return None


def find_operators(text, operator_list):
    found = []
    lower = text.lower()
    for operator in operator_list:
        if operator.lower() in lower:
            found.append(operator)
    return unique(found)


def extract_prices(text):
    """
    Extract all prices from a text.

    Example:
    INR 2843
    INR 320
    INR 2,400
    INR 700 - INR 3000
    """
    pattern = r"(?:Rs\.|INR|₹)\s*([\d,]+)"
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    prices = []
    for price in matches:
        try:
            prices.append(int(price.replace(",", "")))
        except ValueError:
            continue
    return sorted(list(set(prices)))


def format_price_range(prices):
    if not prices:
        return "Price data unavailable from web search"
    if len(prices) == 1:
        return f"₹{prices[0]}"
    return f"₹{prices[0]} - ₹{prices[-1]}"


def extract_duration_minutes(text):
    """
    Extract duration and convert to minutes for validation.
    Returns (duration_string, minutes) or (None, None).
    """
    patterns = [
        (r"\d+\s*hr[s]?\s*(\d+)\s*min[s]?", lambda m: int(m.group(1)) + int(m.group(0).split('hr')[0]) * 60),
        (r"\d+\s*hour[s]?\s*(\d+)\s*minute[s]?", lambda m: int(m.group(1)) + int(m.group(0).split('hour')[0]) * 60),
        (r"\d+h\s*(\d+)m", lambda m: int(m.group(0).split('h')[0]) * 60 + int(m.group(1))),
        (r"\d+\s*hr[s]?", lambda m: int(m.group(0).split('hr')[0]) * 60),
        (r"\d+\s*hour[s]?", lambda m: int(m.group(0).split('hour')[0]) * 60),
        (r"\d+h", lambda m: int(m.group(0).split('h')[0]) * 60),
    ]

    for pattern, converter in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                minutes = converter(match)
                return match.group(0), minutes
            except (ValueError, IndexError):
                continue

    return None, None


def extract_duration(text):
    """Extract duration string (legacy function)."""
    duration_str, _ = extract_duration_minutes(text)
    return duration_str


def validate_duration(duration_str, mode):
    """
    Validate if duration is realistic for the transport mode.
    Returns True if valid, False if clearly impossible.
    """
    if not duration_str:
        return True  # No data to validate

    _, minutes = extract_duration_minutes(duration_str)
    if minutes is None:
        return True  # Could not parse, allow it

    min_ok, max_ok = DURATION_RANGES.get(mode, (0, 999999))
    if minutes < min_ok or minutes > max_ok:
        logger.warning(f"Unrealistic {mode} duration: {duration_str} ({minutes} min)")
        return False

    return True


def validate_route(result_text, origin, destination, mode):
    """
    Validate that the search result actually refers to the requested route.
    Returns True if the route appears to match, False otherwise.
    """
    text_lower = result_text.lower()
    origin_lower = origin.lower()
    dest_lower = destination.lower()

    # Check if both origin and destination appear in the result
    has_origin = origin_lower in text_lower
    has_dest = dest_lower in text_lower

    if not has_origin or not has_dest:
        logger.debug(f"Route mismatch in {mode} result: expected {origin} → {destination}")
        return False

    return True


def clean_text(text):
    return " ".join(text.split())


def extract_options(results, operator_list, mode, origin=None, destination=None):
    """
    Extract up to 3 distinct transport options from search results.

    Each DuckDuckGo result is a separate search snippet that may represent
    a different booking option. Returns only options with verified data.

    Validates:
    - Durations against realistic ranges for the mode
    - Route matches (origin and destination in result text)
    """
    seen_names = set()
    options = []

    for result in results:
        title = result.get("title", "")
        body = result.get("body", "")
        href = result.get("href", "")
        combined = title + "\n" + body

        # Validate route if origin/destination provided
        if origin and destination:
            if not validate_route(combined, origin, destination, mode):
                continue

        # Extract real data from this search snippet only
        operators_found = find_operators(combined, operator_list)
        duration_str, duration_minutes = extract_duration_minutes(combined)
        prices = extract_prices(combined)
        booking_source = find_booking_source(title + " " + href)

        # Validate duration if found
        if duration_str and not validate_duration(duration_str, mode):
            logger.info(f"Skipping {mode} option with invalid duration: {duration_str}")
            continue

        # Determine the option name from real data only
        name = None
        if operators_found:
            name = operators_found[0]
        elif duration_str:
            name = "Option"

        # Skip if we have nothing real to report
        if not name and not duration_str and not prices:
            continue

        if not name:
            name = "Available service"

        # Deduplicate by name
        if name in seen_names:
            continue
        seen_names.add(name)

        options.append({
            "name": name,
            "booking_source": booking_source or "Not specified",
            "booking_url": href if href else None,
            "duration": duration_str if duration_str else "Duration could not be verified from available sources",
            "price": format_price_range(prices) if prices else "Price could not be verified from available sources",
            "operators": operators_found if operators_found else ["Not specified"]
        })

        if len(options) >= 3:
            break

    logger.info(f"Extracted {len(options)} {mode} options from {len(results)} search results")
    return options


def extract_transport_info(results, operator_list, mode, origin=None, destination=None):
    """
    Extract both a summary and up to 3 individual options.

    Summary uses ALL results combined.
    Options are extracted per-search-result for distinct choices.
    """
    text = clean_text(results_to_text(results))
    prices = extract_prices(text)

    # Validate summary duration
    summary_duration, _ = extract_duration_minutes(text)
    if summary_duration and not validate_duration(summary_duration, mode):
        summary_duration = "Duration could not be verified from available sources"

    options = extract_options(results, operator_list, mode, origin, destination)

    # Collect all booking sources from results
    all_sources = []
    for r in results:
        src = find_booking_source(r.get("title", "") + " " + r.get("href", ""))
        if src and src not in all_sources:
            all_sources.append(src)

    summary = {
        "duration": summary_duration or "Duration data unavailable from web search",
        "price_range": format_price_range(prices),
        "operators": find_operators(text, operator_list),
        "sources": len(results),
        "found": len(results) > 0,
        "booking_sources": all_sources if all_sources else ["Not specified"]
    }

    return {
        "summary": summary,
        "options": options
    }


def results_to_text(results):
    text = ""
    for result in results:
        text += result.get("title", "")
        text += "\n"
        text += result.get("body", "")
        text += "\n"
        text += result.get("href", "")
        text += "\n"
    return text


def parse_transport(data, origin=None, destination=None):
    return {
        "flight": extract_transport_info(
            data.get("flight", []),
            AIRLINES,
            "flight",
            origin,
            destination
        ),
        "train": extract_transport_info(
            data.get("train", []),
            TRAIN_OPERATORS,
            "train",
            origin,
            destination
        ),
        "bus": extract_transport_info(
            data.get("bus", []),
            BUS_OPERATORS,
            "bus",
            origin,
            destination
        )
    }