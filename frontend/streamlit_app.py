"""
streamlit_app.py
-------------------
A simple web UI for the AI Meeting Intelligence System.

Run with:
    streamlit run frontend/streamlit_app.py

Make sure the FastAPI backend is already running on http://localhost:8000
(see backend/main.py) - this UI just calls that API.
"""

import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Meeting Intelligence System", layout="wide")
st.title("🧠 AI Meeting Intelligence System")
st.caption("Upload a recorded meeting and get an automatic summary, decisions, "
           "action items, calendar invite, and email — all AI-generated.")

tab1, tab2, tab3 = st.tabs(["📤 Upload Meeting", "📚 Past Meetings", "❓ Ask About Past Meetings"])

# ---------------- TAB 1: Upload & Process ----------------
with tab1:
    st.subheader("Upload a recorded meeting")
    title = st.text_input("Meeting title", "Product Sync Meeting")
    attendee_emails = st.text_input("Attendee emails (comma separated, optional)", "")
    uploaded_file = st.file_uploader(
        "Upload audio or video file", type=["mp3", "wav", "m4a", "mp4"]
    )

    if uploaded_file and st.button("Process Meeting", type="primary"):
        with st.spinner("Transcribing and analyzing the meeting... this can take a minute"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            data = {"title": title, "attendee_emails": attendee_emails}
            response = requests.post(f"{API_URL}/process-meeting", files=files, data=data)

        if response.status_code == 200:
            result = response.json()
            st.success("Meeting processed successfully!")

            st.markdown("### 📝 Summary")
            st.write(result["summary"])

            st.markdown("### ✅ Decisions")
            if result["decisions"]:
                for d in result["decisions"]:
                    st.write(f"- {d.get('description')}")
            else:
                st.write("No explicit decisions detected.")

            st.markdown("### 📌 Action Items")
            if result["action_items"]:
                df = pd.DataFrame(result["action_items"])
                st.dataframe(df, use_container_width=True)
            else:
                st.write("No action items detected.")

            st.markdown("### 📅 Follow-up Meeting")
            st.json(result["followup_meeting"])
            if result.get("calendar_result"):
                st.json(result["calendar_result"])

            st.markdown("### 📧 Generated Email")
            st.code(result["email_body"])

            with st.expander("View full raw transcript"):
                st.write(result["transcript"])
        else:
            st.error(f"Something went wrong: {response.text}")

# ---------------- TAB 2: Past Meetings ----------------
with tab2:
    st.subheader("All processed meetings")
    if st.button("Refresh list"):
        st.rerun()
    try:
        meetings = requests.get(f"{API_URL}/meetings").json()
        for m in meetings:
            with st.expander(f"{m['title']} — {m['date']}"):
                st.write(m["summary"])
                if st.button("View full details", key=f"details-{m['id']}"):
                    details = requests.get(f"{API_URL}/meetings/{m['id']}").json()
                    st.json(details)
    except Exception as e:
        st.warning("Could not load meetings. Is the backend running?")

# ---------------- TAB 3: RAG Q&A ----------------
with tab3:
    st.subheader("Ask a question about any past meeting")
    question = st.text_input("e.g. 'Did we discuss Kubernetes before?'")
    if st.button("Ask") and question:
        with st.spinner("Searching past meetings..."):
            response = requests.post(f"{API_URL}/ask", data={"question": question})
        if response.status_code == 200:
            st.write(response.json()["answer"])
        else:
            st.error("Something went wrong.")
