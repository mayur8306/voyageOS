import re


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



def unique(items):

    seen = set()

    result = []

    for item in items:

        if item not in seen:

            seen.add(item)

            result.append(item)

    return result


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
    ₹2843
    INR 320
    ₹ 2,400
    ₹700 - ₹3000
    """

    pattern = r"(?:₹|INR)\s*([\d,]+)"

    matches = re.findall(pattern, text, flags=re.IGNORECASE)

    prices = []

    for price in matches:

        try:
            prices.append(
                int(price.replace(",", ""))
            )
        except ValueError:
            continue

    return sorted(list(set(prices)))


def format_price_range(prices):

    if not prices:
        return "Unknown"

    if len(prices) == 1:
        return f"₹{prices[0]}"

    return f"₹{prices[0]} - ₹{prices[-1]}"



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


def extract_duration(text):


    patterns = [

        r"\d+\s*hr[s]?\s*\d+\s*min[s]?",

        r"\d+\s*hour[s]?\s*\d+\s*minute[s]?",

        r"\d+h\s*\d+m",

        r"\d+\s*hr[s]?",

        r"\d+\s*hour[s]?",

        r"\d+h"

    ]
    durations = []

    for pattern in patterns:

        durations.extend(
            re.findall(
                pattern,
                text,
                flags=re.IGNORECASE
            )
        )

    if durations:

        return durations[0]

    return "Unknown"


def clean_text(text):

    return " ".join(text.split())



def extract_transport_info(
    results,
    operator_list
):

    text = clean_text(
        results_to_text(results)
    )


    prices = extract_prices(text)

    return {

        "duration": extract_duration(text),

        "price_range": format_price_range(prices),

        "operators": find_operators(
            text,
            operator_list
        ),

        "sources": len(results),

        "raw_text": text,

        "found": len(results) > 0

    }

def parse_transport(data):

    return {

        "flight": extract_transport_info(

            data.get("flight", []),

            AIRLINES

        ),

        "train": extract_transport_info(

            data.get("train", []),

            TRAIN_OPERATORS

        ),

        "bus": extract_transport_info(

            data.get("bus", []),

            BUS_OPERATORS

        )

    }



