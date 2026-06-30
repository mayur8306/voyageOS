from agent.travel_agent import TravelAgent

agent = TravelAgent()

response = agent.chat(
    "Plan a honeymoon trip from Mumbai to Goa for 2 people with a budget of ₹80000"
)

print(response["status"])
print()
print(response["message"])