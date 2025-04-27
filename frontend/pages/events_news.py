import streamlit as st
from utils.api_client import fetch_new_events
import requests
from datetime import date, timedelta
from smolagents import tool

ALL_RISK_CATEGORIES = [
    "Financial",
    "Geopolitical",
    "Technology",
    "Environmental",
    "Social",
    "Governance"
]

st.title("Events & News")
st.write("""
This page is **Step 1** of the workflow: Fetch new events from external news sources.
You can specify a detailed search query (using **OR** to combine terms), a date range (up to the last 30 days),
and the number of articles to fetch (1-100). Note that fetching around 10 articles may take approximately a minute.
These events will later be assessed on the "Assess Events" page.
""")

# Input for the query to fetch news about (full query with OR operators)
default_query = "supply chain issues AND (disruption OR delay OR crisis)"
query = st.text_input("Enter your search query:", value=default_query)

# Date range: Limit to the past 30 days.
today = date.today()
thirty_days_ago = today - timedelta(days=30)
date_range = st.date_input(
    "Select a date range (within the last 30 days):",
    value=(today - timedelta(days=7), today),  # default: last 7 days
    min_value=thirty_days_ago,
    max_value=today
)
# date_range returns a tuple (start_date, end_date)
from_date = date_range[0].strftime("%Y-%m-%d")
to_date = date_range[1].strftime("%Y-%m-%d")

# Slider for number of results
page_size = st.slider("Select number of articles to fetch:", min_value=1, max_value=100, value=10, step=1)

# Initialize session state for events and filters
if 'events' not in st.session_state:
    st.session_state.events = {}
if 'last_topic' not in st.session_state:
    st.session_state.last_topic = None
if 'selected_risk_categories' not in st.session_state:
    st.session_state.selected_risk_categories = ALL_RISK_CATEGORIES

@tool
def fetch_and_store_events(
        query: str,
        page_size: int,
        from_date: str,
        to_date: str
    ) -> str:
    """
    Fetch events and store in session_state.

    Args:
        query (str):     search query string
        page_size (int): number of articles to fetch
        from_date (str): start date YYYY-MM-DD
        to_date (str):   end date YYYY-MM-DD

    Returns:
        str: status message
    """
    try:
        data = fetch_new_events(query=query, page_size=page_size, from_date=from_date, to_date=to_date)
        events = data.get("events", [])

        st.session_state.events[query] = events
        st.session_state.last_topic = query

        st.success(f"Fetched {len(events)} events for query: {query}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching events: {e}")


if st.button("Fetch Events"):
    fetch_and_store_events(query=query, page_size=page_size, from_date=from_date, to_date=to_date)


def display_events(events):
    """Display the list of events."""
    if events:
        for event in events:
            st.subheader(f"[{event['title']}]({event['url']})")
            st.write(event.get("description", "No summary available."))
            st.write(
                f"**Source:** {event.get('source_name', 'Unknown')} | **Published At:** {event.get('timestamp', 'Unknown')}"
            )
            location = event.get("location", {})
            location_display = location.get("city") or location.get("region") or location.get(
                "country") or "Not specified"
            st.write(f"**Location:** {location_display}")
            risk_categories = event.get("risk_categories", [])
            if risk_categories:
                formatted_risks = [
                    f"{risk['class_name']}: {', '.join(risk.get('families', []))}" if risk.get("families") else risk[
                        "class_name"]
                    for risk in risk_categories
                ]
                st.write(f"**Risk Categories:** {' & '.join(formatted_risks)}")
            else:
                st.write("**Risk Categories:** Not categorized")
            st.write("---")
    else:
        st.info("No events found for the given query.")


def filter_events():
    """Filter events by selected risk categories."""
    if st.session_state.last_topic in st.session_state.events:
        return [
            event for event in st.session_state.events[st.session_state.last_topic]
            if any(risk["class_name"] in st.session_state.selected_risk_categories for risk in
                   event.get("risk_categories", []))
        ]
    return []


# Expandable filter panel
with st.expander("Filter Events", expanded=False):
    st.multiselect(
        "Select Risk Categories:",
        options=ALL_RISK_CATEGORIES,
        default=st.session_state.selected_risk_categories,
        key="selected_risk_categories"
    )

if st.session_state.events:
    filtered_events = [
        event for event in st.session_state.events.get(st.session_state.last_topic, [])
        if any(risk["class_name"] in st.session_state.selected_risk_categories for risk in
               event.get("risk_categories", []))
    ]
else:
    filtered_events = []

# Display events
if filtered_events:
    if st.session_state.selected_risk_categories == ALL_RISK_CATEGORIES:
        st.write(f"### Events for: {st.session_state.last_topic}")
    else:
        st.write(f"### Filtered Events for: {st.session_state.last_topic}")
    display_events(filtered_events)
else:
    if st.session_state.selected_risk_categories == ALL_RISK_CATEGORIES:
        st.info("No events available for the selected query.")
    else:
        st.info("No matching events found based on the selected filters.")
