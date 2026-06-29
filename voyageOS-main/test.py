from utils.transport_parser import extract_prices, format_price_range

sample = """
Flight starts from ₹2843.

Economy ₹2938.

Train ₹320 - ₹3300.

Bus ₹700.
"""

prices = extract_prices(sample)

print(prices)

print(format_price_range(prices))