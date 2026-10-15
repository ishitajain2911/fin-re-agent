import requests
import streamlit as st

API_URL = "http://localhost:8000"

def escape_dollars(text):
    return text.replace("$", "\\$")

def show_report(ticker, query, report):
    st.header(f"{ticker.upper()}: {query}")

    # --- confidence badge ---
    confidence = report["confidence"]                  # blank 2: which key?
    label = f"Confidence: {confidence.upper()}"
    if confidence == "high":
        st.success(label)
    elif confidence=="medium":                                         # blank 3
        st.warning(label)
    else:
        st.error(label)
    st.caption(escape_dollars(report["confidence_reason"]))           # small grey text under the badge

    # --- summary ---
    st.subheader("Summary")
    st.write(escape_dollars(report["summary"]))                                     

    # --- key findings ---
    st.subheader("Key findings")
    for finding in (report["key_findings"]):                
        st.markdown(f"- {escape_dollars(finding)}")                       

    # --- risks ---
    st.subheader("Risks")
    for risk in (report["risks"]):
        st.markdown(f"- {escape_dollars(risk)}")
    # --- caveats ---
    caveats =report["caveats"]
    if len(caveats)!=0:                                           
        with st.expander(f"Caveats ({len(caveats)})"):         
            for c in caveats:
                st.markdown(f"- {escape_dollars(c)}")

st.title("Financial Research Agent")

ticker = st.text_input("Ticker", value="MU")
query = st.text_input("Question", value="revenue growth")

# ---------- 1. Run research: fetch, then remember (don't show) ----------
if st.button("Run research"):
    with st.spinner("Researching... (a fresh run takes a few minutes)"):
        response = requests.post(
            f"{API_URL}/research",
            json={"ticker": ticker, "query": query},
            timeout=600,  # a fresh run is slow; requests waits forever by default
        )
    if response.status_code != 200:
        st.error(f"Backend error {response.status_code}: {response.text}")
        st.stop()

    report = response.json()
    st.session_state["current"] = (ticker, query, report)

# ---------- 2. Sidebar: history ----------
with st.sidebar:
    st.header("Past reports")
    history = requests.get(f"{API_URL}/reports").json()

    for i, item in enumerate(history):
        if item["ticker"] == "TEST":
            continue
        label = f"{item['ticker']}: {item['query']} ({item['created_at'][:10]})"
        if st.button(label, key=f"hist_{i}"):
            st.session_state["current"] = (item["ticker"], item["query"], item["report"])

# ---------- 3. The one place that shows a report ----------
current = st.session_state.get("current")
if current is not None:
    ticker_shown, query_shown, report_shown = current
    show_report(ticker_shown, query_shown, report_shown)
