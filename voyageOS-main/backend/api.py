from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from backend.schemas import ChatRequest, ChatResponse
from agent.travel_agent import TravelAgent
from utils.pdf_generator import PDFGenerator
import traceback
import os

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
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/download-pdf")
def download_pdf():
    """
    Compiles the live runtime memory state snapshot of the active TravelAgent 
    into a structured, downloadable PDF binary stream.
    """
    try:
        # Verify that information collection has occurred and we have a valid target destination
        if not agent.state.trip.destination:
            raise HTTPException(
                status_code=400,
                detail="No finalized travel data available to compile a PDF document. Please plan a trip first."
            )

        # Assemble the data payload snapshot matching the fields in TravelState
        snapshot_payload = {
            "trip_details": {
                "destination": agent.state.trip.destination,
                "origin": agent.state.trip.origin,
                "budget": agent.state.trip.budget,
                "travelers": agent.state.trip.travelers,
                "trip_type": agent.state.trip.trip_type,
                "duration": agent.state.trip.duration
            },
            "tool_results": agent.state.tool_results,
            # Grabs the final generated travel itinerary response text from the message history stack
            "message": agent.state.messages[-1]["content"] if agent.state.messages else "No active plan text found."
        }

        # Create a safe, clean string for the file name destination
        safe_dest_name = agent.state.trip.destination.replace(" ", "_")
        filename = f"VoyageOS_{safe_dest_name}_Plan.pdf"
        local_target_path = f"downloads/{filename}"

        # Compile and generate the document locally via our helper utility
        PDFGenerator.create_itinerary_pdf(snapshot_payload, local_target_path)

        # Confirm file writing was fully executed onto the persistent disk space, then stream it
        if os.path.exists(local_target_path):
            return FileResponse(
                path=local_target_path,
                filename=filename,
                media_type="application/pdf"
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to write compiled PDF file asset onto the workspace storage disk."
            )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"PDF Compilation Pipeline Failure: {str(e)}"
        )


@app.post("/reset")
def reset():
    global agent
    agent = TravelAgent()
    return {
        "message": "Conversation Reset"
    }