from fastapi import FastAPI

from backend.schemas import ChatRequest, ChatResponse

from agent.travel_agent import TravelAgent
import traceback
from fastapi import HTTPException

app = FastAPI(
    title="VoyageAI",
    version="1.0"
)

agent = TravelAgent()


@app.get("/")
def home():

    return {

        "message": "VoyageAI Backend Running"

    }

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "agent": "VoyageAI",

        "version": "1.0"

    }



@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    try:
        response = agent.chat(request.message)

        return ChatResponse(
            response=response
        )

    except Exception as e:

        traceback.print_exc()   # <-- add this line

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/reset")
def reset():

    global agent

    agent = TravelAgent()

    return {

        "message": "Conversation Reset"

    }