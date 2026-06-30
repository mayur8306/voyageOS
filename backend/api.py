"""FastAPI backend for VoyageOS."""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agent.voyageos_assistant import VoyageOSAssistant

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VoyageOS API",
    description="AI Travel Assistant API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize assistant (singleton)
assistant = VoyageOSAssistant()

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    status: str
    response: str
    session_id: str
    sources: Optional[list] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "VoyageOS API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    try:
        # Check RAG status
        rag_sources = assistant.get_rag_sources()
        rag_doc_count = assistant.rag_pipeline.get_document_count()
        
        return {
            "status": "healthy",
            "rag": {
                "initialized": assistant.rag_pipeline.is_ingested,
                "sources": len(rag_sources),
                "documents": rag_doc_count
            },
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "degraded",
            "error": str(e)
        }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    
    Accepts user message and returns AI response.
    Automatically detects intent and routes to appropriate handler.
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")
        
        # Use existing session or create new one
        if request.session_id and request.session_id != assistant.session_id:
            # Load the session
            assistant.load_session(request.session_id)
        
        # Process message
        result = assistant.process_message(request.message)
        
        logger.info(f"Response generated with status: {result.get('status')}")
        
        return ChatResponse(
            status=result.get("status", "completed"),
            response=result.get("response", ""),
            session_id=result.get("session_id", assistant.session_id),
            sources=result.get("sources")
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/sessions")
async def get_sessions(limit: int = 20):
    """Get recent conversation sessions."""
    try:
        sessions = assistant.get_recent_sessions(limit=limit)
        return {
            "status": "success",
            "sessions": sessions
        }
    except Exception as e:
        logger.error(f"Failed to get sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 50):
    """Get conversation history for a session."""
    try:
        history = assistant.conversation_history.get_session_history(session_id, limit)
        return {
            "status": "success",
            "session_id": session_id,
            "history": history
        }
    except Exception as e:
        logger.error(f"Failed to get history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/sessions/{session_id}/trips")
async def get_session_trips(session_id: str):
    """Get trip history for a session."""
    try:
        trips = assistant.trip_history.get_session_trips(session_id)
        return {
            "status": "success",
            "session_id": session_id,
            "trips": trips
        }
    except Exception as e:
        logger.error(f"Failed to get trips: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/rag/sources")
async def get_rag_sources():
    """Get available RAG document sources."""
    try:
        sources = assistant.get_rag_sources()
        doc_count = assistant.rag_pipeline.get_document_count()
        return {
            "status": "success",
            "sources": sources,
            "document_count": doc_count
        }
    except Exception as e:
        logger.error(f"Failed to get RAG sources: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/rag/reload")
async def reload_rag():
    """Reload RAG documents."""
    try:
        success = assistant.rag_pipeline.ingest_documents(force_reload=True)
        return {
            "status": "success" if success else "error",
            "message": "RAG documents reloaded" if success else "Failed to reload"
        }
    except Exception as e:
        logger.error(f"Failed to reload RAG: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)