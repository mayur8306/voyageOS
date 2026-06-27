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

if "messages" not in st.session_state:
    st.session_state.messages = []

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

                assistant_reply = response["response"]["message"]

                tool_results = response["response"].get(
                    "tool_results",
                    {}
                )

            except Exception as e:

                assistant_reply = f"❌ Error:\n\n{e}"

                tool_results = {}

        st.markdown(assistant_reply)

        if tool_results:

            with st.expander("🔧 Developer Mode - Tool Outputs"):

                st.json(tool_results)