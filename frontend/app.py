"""VoyageOS Streamlit Frontend with RAG and Memory."""

import streamlit as st
import sys
from pathlib import Path
import json
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agent.voyageos_assistant import VoyageOSAssistant
from memory.database import Database

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="VoyageOS - AI Travel Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        text-align: right;
    }
    .assistant-message {
        background-color: #f5f5f5;
        text-align: left;
    }
    .source-citation {
        font-size: 0.85rem;
        color: #666;
        font-style: italic;
    }
    .status-indicator {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .status-collecting {
        background-color: #fff3cd;
        color: #856404;
    }
    .status-ready {
        background-color: #d4edda;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'assistant' not in st.session_state:
        with st.spinner("Initializing VoyageOS..."):
            st.session_state.assistant = VoyageOSAssistant()
            rag_success = st.session_state.assistant.initialize_rag()
            
            if not rag_success:
                st.warning("⚠️ Knowledge base initialization failed. Travel knowledge features may be limited.")
    
    # Maintain separate chat histories for each page
    if 'planner_chat' not in st.session_state:
        st.session_state.planner_chat = []
    if 'knowledge_chat' not in st.session_state:
        st.session_state.knowledge_chat = []
    if 'history_chat' not in st.session_state:
        st.session_state.history_chat = []
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Trip Planner'


def get_current_chat():
    """Get the chat history for the current page."""
    if st.session_state.current_page == "🏠 Trip Planner":
        return st.session_state.planner_chat
    elif st.session_state.current_page == "📚 Travel Knowledge":
        return st.session_state.knowledge_chat
    else:
        return []


def set_current_chat(messages):
    """Set the chat history for the current page."""
    if st.session_state.current_page == "🏠 Trip Planner":
        st.session_state.planner_chat = messages
    elif st.session_state.current_page == "📚 Travel Knowledge":
        st.session_state.knowledge_chat = messages


def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        st.title("✈️ VoyageOS")
        st.markdown("---")
        
        # Navigation
        st.session_state.current_page = st.radio(
            "Navigation",
            ["🏠 Trip Planner", "📚 Travel Knowledge", "🕘 Chat History", "ℹ️ About"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # RAG Status
        st.subheader("📚 Knowledge Base")
        try:
            sources = st.session_state.assistant.get_rag_sources()
            doc_count = st.session_state.assistant.rag_pipeline.get_document_count()
            rag_status = st.session_state.assistant.rag_pipeline.get_status()
            
            if rag_status.get('error'):
                st.error("❌ Knowledge base unavailable")
                st.caption(f"Error: {rag_status['error']}")
            elif doc_count > 0:
                st.success(f"✅ {doc_count} documents loaded")
                with st.expander("View Documents"):
                    for source in sources:
                        st.text(f"📄 {source}")
            else:
                st.warning("⚠️ No documents loaded")
        except Exception as e:
            st.error("❌ Knowledge base unavailable")
            logger.error(f"Error loading RAG status: {str(e)}")
        
        st.markdown("---")
        
        # Session info
        st.subheader("Session Info")
        st.text(f"Session ID: {st.session_state.assistant.session_id[:8]}...")
        
        # Show current state
        state = st.session_state.assistant.state
        state_labels = {
            "idle": "💤 Idle",
            "collecting_trip": "📝 Collecting Trip Details",
            "itinerary_ready": "✅ Itinerary Ready",
            "modifying_trip": "🔄 Modifying Trip"
        }
        st.text(f"Status: {state_labels.get(state, state)}")
        
        # Show current trip summary if available (using safe attribute access)
        current_trip = st.session_state.assistant.current_trip
        if current_trip and hasattr(current_trip, 'destination') and current_trip.destination:
            st.markdown("---")
            st.subheader("Current Trip")
            
            # Safe attribute access with defaults
            st.markdown(f"**📍 Destination:** {getattr(current_trip, 'destination', 'N/A')}")
            st.markdown(f"**🛫 Origin:** {getattr(current_trip, 'origin', '') or 'Not set'}")
            st.markdown(f"**📅 Duration:** {getattr(current_trip, 'duration', 0)} days")
            st.markdown(f"**👥 Travelers:** {getattr(current_trip, 'travelers', 0)}")
            st.markdown(f"**💰 Budget:** ₹{getattr(current_trip, 'budget', 0):,.0f}")
            st.markdown(f"**🎯 Trip Type:** {getattr(current_trip, 'trip_type', '') or 'Not set'}")
            
            # Safe list access
            hotel_list = getattr(current_trip, 'hotels', [])
            attraction_list = getattr(current_trip, 'attractions', [])
            
            if hotel_list:
                st.markdown(f"**🏨 Hotels:** {len(hotel_list)} options")
            if attraction_list:
                st.markdown(f"**🎭 Attractions:** {len(attraction_list)} places")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Chat"):
                current_chat = get_current_chat()
                current_chat.clear()
                st.rerun()
        
        with col2:
            if st.button("Reset Trip"):
                st.session_state.assistant.state = st.session_state.assistant.STATE_IDLE
                st.session_state.assistant.current_trip = st.session_state.assistant.current_trip.__class__()
                st.rerun()


def render_trip_planner():
    """Render trip planner page."""
    st.markdown('<div class="main-header">🏠 Trip Planner</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Plan your perfect trip with AI</div>', unsafe_allow_html=True)
    
    # Show status indicator
    state = st.session_state.assistant.state
    if state == "collecting_trip":
        st.markdown('<div class="status-indicator status-collecting">📝 Collecting trip details...</div>', unsafe_allow_html=True)
    elif state == "itinerary_ready":
        st.markdown('<div class="status-indicator status-ready">✅ Itinerary ready - Ask follow-up questions</div>', unsafe_allow_html=True)
    
    # Display chat history
    messages = get_current_chat()
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Plan your trip..."):
        # Add user message
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            status_placeholder = st.empty()
            try:
                # Show progressive status updates during processing
                status_placeholder.info("🧠 Understanding your trip...")
                result = st.session_state.assistant.process_message(prompt)
                status_placeholder.empty()
                response = result.get("response", "I couldn't process that request.")
                st.markdown(response)
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                status_placeholder.empty()
                response = "I apologize, but I encountered an error. Please try again."
                st.markdown(response)
        
        # Add assistant message
        messages.append({"role": "assistant", "content": response})
        
        # Rerun to update status indicator
        st.rerun()
    
    # Show PDF download button if PDF was generated (outside input block to persist across reruns)
    current_trip = st.session_state.assistant.current_trip
    if current_trip and hasattr(current_trip, 'pdf_path') and current_trip.pdf_path:
        try:
            import os
            pdf_path = current_trip.pdf_path
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                
                filename = os.path.basename(pdf_path)
                st.download_button(
                    label="📥 Download Trip PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    key=f"pdf_download_{st.session_state.assistant.session_id}"
                )
        except Exception as e:
            logger.error(f"Error displaying PDF download: {str(e)}")


def render_travel_knowledge():
    """Render travel knowledge assistant page."""
    st.markdown('<div class="main-header">📚 Travel Knowledge Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask about visas, passports, customs, and more</div>', unsafe_allow_html=True)
    
    # Check RAG status
    rag_status = st.session_state.assistant.rag_pipeline.get_status()
    if rag_status.get('error'):
        st.error("❌ Knowledge base is currently unavailable. Please try again later.")
    elif rag_status.get('document_count', 0) == 0:
        st.warning("⚠️ No travel documents loaded. Please add PDFs to the data/ directory.")
    else:
        st.info(f"💡 Ask me about travel documents, visa requirements, customs procedures, airport processes, and more! ({rag_status['document_count']} documents loaded)")
    
    # Display chat history
    messages = get_current_chat()
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                st.markdown('<div class="source-citation">📚 Sources: ' + ', '.join(message["sources"]) + '</div>', unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("Ask about travel..."):
        # Add user message
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                try:
                    result = st.session_state.assistant.process_message(prompt)
                    # Extract only the response text from the dictionary
                    if isinstance(result, dict):
                        response = result.get("response", "I couldn't process that request.")
                        sources = result.get("sources", [])
                    else:
                        response = str(result)
                        sources = []
                    # Display only the response text, not the entire dictionary
                    st.markdown(response)
                    if sources:
                        st.markdown('<div class="source-citation">📚 Sources: ' + ', '.join(sources) + '</div>', unsafe_allow_html=True)
                except Exception as e:
                    logger.error(f"Error processing knowledge query: {str(e)}")
                    response = "I apologize, but I couldn't process your question. Please try again."
                    st.markdown(response)
                    sources = []
        
        # Add assistant message (store only the response text, not the entire dictionary)
        messages.append({
            "role": "assistant",
            "content": response,
            "sources": sources
        })


def render_chat_history():
    """Render chat history page."""
    st.markdown('<div class="main-header">🕘 Chat History</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">View and manage your previous conversations</div>', unsafe_allow_html=True)
    
    # Get recent sessions
    try:
        sessions = st.session_state.assistant.get_recent_sessions(limit=20)
        
        if not sessions:
            st.info("No previous conversations found.")
            return
        
        for session in sessions:
            with st.expander(f"Session {session['session_id'][:8]}... - {session['message_count']} messages"):
                st.text(f"Last activity: {session['last_activity']}")
                st.text(f"Messages: {session['message_count']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Load Session", key=f"load_{session['session_id']}"):
                        # Load session
                        result = st.session_state.assistant.load_session(session['session_id'])
                        
                        if result and result.get('success'):
                            # Load conversation into planner chat
                            history = result.get('history', [])
                            st.session_state.planner_chat = []
                            for msg in reversed(history):
                                st.session_state.planner_chat.append({
                                    "role": "user",
                                    "content": msg['user_message']
                                })
                                st.session_state.planner_chat.append({
                                    "role": "assistant",
                                    "content": msg['assistant_message']
                                })
                            
                            # Navigate to Trip Planner page
                            st.session_state.current_page = "🏠 Trip Planner"
                            
                            # Show success message
                            has_trip = result.get('has_trip', False)
                            if has_trip:
                                st.success(f"✅ Session loaded! Trip to {st.session_state.assistant.current_trip.destination} restored. You can now ask follow-up questions.")
                            else:
                                st.info("📝 Session loaded! No trip found in this session.")
                            
                            st.rerun()
                        else:
                            error = result.get('error', 'Unknown error') if result else 'Unknown error'
                            st.error(f"Failed to load session: {error}")
                
                with col2:
                    if st.button(f"Delete Session", key=f"delete_{session['session_id']}"):
                        st.session_state.assistant.conversation_history.delete_session(session['session_id'])
                        st.rerun()
    
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")


def render_about():
    """Render about page."""
    st.markdown('<div class="main-header">ℹ️ About VoyageOS</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ## VoyageOS - AI Travel Assistant
    
    VoyageOS is a comprehensive AI-powered travel assistant that combines trip planning 
    with travel knowledge management.
    
    ### Features
    
    - **Trip Planning**: Plan complete itineraries with hotels, attractions, transport, and budget
    - **Travel Knowledge**: Ask questions about visas, passports, customs, and travel regulations
    - **Conversation Memory**: All conversations are saved for future reference
    - **Smart Follow-ups**: Modify previous trips without re-entering all details
    - **State Management**: Remembers context throughout the conversation
    
    ### Architecture
    
    - **Backend**: FastAPI with LangGraph workflow
    - **Frontend**: Streamlit with multi-page navigation
    - **LLM**: Groq (Llama 3.1)
    - **APIs**: Geoapify, DuckDuckGo, Open-Meteo
    - **RAG**: ChromaDB with sentence-transformers
    - **Database**: SQLite for conversation and trip history
    
    ### Tools
    
    - Weather Tool (Open-Meteo)
    - Hotel Tool (Geoapify)
    - Places Tool (Geoapify)
    - Transport Tool (DuckDuckGo)
    - Budget Tool (Custom)
    - PDF Generator (fpdf2)
    
    ### Technology Stack
    
    - Python 3.8+
    - LangChain & LangGraph
    - ChromaDB
    - Sentence-Transformers
    - SQLite
    - Streamlit
    - FastAPI
    - Groq API
    """)


def main():
    """Main application entry point."""
    initialize_session_state()
    render_sidebar()
    
    # Route to appropriate page
    if st.session_state.current_page == "🏠 Trip Planner":
        render_trip_planner()
    elif st.session_state.current_page == "📚 Travel Knowledge":
        render_travel_knowledge()
    elif st.session_state.current_page == "🕘 Chat History":
        render_chat_history()
    elif st.session_state.current_page == "ℹ️ About":
        render_about()


if __name__ == "__main__":
    main()