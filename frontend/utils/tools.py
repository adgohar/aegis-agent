from smolagents import tool
import streamlit as st
from utils.api_client import assess_unassessed_events, fetch_assessed_events


@tool
def assess_and_store_events() -> str:
    """
    Assess unassessed events for the given supply chain.

    Args:
        supply_chain_id (str): The ID of the supply chain to assess events for.

    Returns:
        str: Status message after assessing events.
    """
    try:
        # Ensure that a supply chain is selected
        if 'selected_supply_chain' not in st.session_state or not st.session_state.selected_supply_chain:
            st.error("No supply chain selected. Please select a supply chain first.")
        else:
            supply_chain_id = st.session_state.selected_supply_chain["id"]
        events = assess_unassessed_events(supply_chain_id=supply_chain_id)
        if not events:
            return "No new unassessed events found. All events are already assessed."
        
        st.session_state.alerts = events
        st.session_state.alerts_source = "unassessed"

        return f"✅ Assessed {len(events)} new events successfully."
    except Exception as e:
        return f"❌ Failed to assess events: {str(e)}"


@tool
def load_assessed_events_to_map() -> str:
    """
    Load assessed events to the map.

    Returns:
        str: Status message after loading events to the map.
    """
    if 'map_events_source' not in st.session_state:
        st.session_state.map_events_source = None
    if (
        st.session_state.map_events_source == "events"
        and st.session_state.map_events
        and st.session_state.selected_supply_chain["id"] == st.session_state.map_events.get("supply_chain_id")
    ):
        st.success("Using cached assessed events.")
    else:
        try:
            data = fetch_assessed_events(supply_chain_id=st.session_state.selected_supply_chain["id"])
            st.session_state.map_events = {
                "data": data,
                "supply_chain_id": st.session_state.selected_supply_chain["id"]
            }
            st.session_state.map_events_source = "events"
            st.success("Loaded assessed events and displayed them on the map.")
        except Exception as e:
            st.error(f"Error loading assessed events: {e}")