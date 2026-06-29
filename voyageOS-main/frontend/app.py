import streamlit as st
from api_client import VoyageAPI

st.set_page_config(
    page_title="VoyageOS",
    page_icon="✈️",
    layout="wide"
)

# ---------------- Sidebar ---------------- #

with st.sidebar:
    st.title("✈️ VoyageOS")
    st.markdown("### AI Travel Planner")
    st.markdown("---")

    if st.button("🔄 New Conversation"):
        VoyageAPI.reset()
        st.session_state.messages = []
        st.session_state.last_status = None
        st.rerun()

    st.markdown("---")
    st.info(
        """
VoyageOS can help you plan:
- 🌍 Destinations
- ✈️ Transport
- 🏨 Hotels
- 🌤 Weather
- 💰 Budget
- 📍 Attractions
"""
    )

# ---------------- Main Page ---------------- #

st.title("✈️ VoyageOS")
st.caption("Your AI Powered Travel Planning Assistant")

# Initialize robust session arrays for application tracking
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_status" not in st.session_state:
    st.session_state.last_status = None

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
prompt = st.chat_input("Where would you like to travel?")

if prompt:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Planning your trip..."):
            try:
                response = VoyageAPI.chat(prompt)
                
                # Safely parse nested backend keys matching ChatResponse schema
                inner_resp = response.get("response", {})
                assistant_reply = inner_resp.get("message", "No response received.")
                tool_results = inner_resp.get("tool_results", {})
                current_status = inner_resp.get("status", None)
                
                # Cache execution status state globally in the session environment
                st.session_state.last_status = current_status

            except Exception as e:
                assistant_reply = f"❌ Connection Error:\n\n{e}"
                tool_results = {}
                st.session_state.last_status = "error"

        st.markdown(assistant_reply)


# Render the downloadable component when agent switches over to a finished state 
if st.session_state.last_status == "completed":
    st.markdown("---")
    st.markdown("### 📥 Document Export Strategy")
    
    download_endpoint_url = "http://127.0.0.1:8000/download-pdf"
    
    st.markdown(
        f'<a href="{download_endpoint_url}" target="_blank">'
        '<button style="background-color: #0284c7; color: white; border: none; padding: 12px 24px; '
        'border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; font-size: 14px;">'
        '📄 Download Complete Verified Travel Itinerary (PDF)'
        '</button></a>',
        unsafe_allow_html=True  # <-- FIXED TYPO HERE (Removed 'ed')
    )