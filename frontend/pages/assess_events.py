import streamlit as st
import datetime

from components.event_edit_popup import edit_event_dialog
from utils.api_client import assess_unassessed_events, fetch_assessed_events, update_event

# Initialize session state for alerts
if 'alerts' not in st.session_state:
    st.session_state.alerts = None
if 'alerts_source' not in st.session_state:
    st.session_state.alerts_source = None

st.title("Assess Events")
st.write("""
This page allows you to **evaluate newly created events** (and see those that have already been assessed). 
It's typically **Step 2** of the workflow, following the "Events & News" page.

- **Load Existing Events**: Displays events that are **already** assessed for the current supply chain.
- **Fetch & Assess Unassessed Events**: Retrieves only **new** events from the database and runs a relevance 
  and risk assessment to classify them.
""")

# Ensure that a supply chain is selected
if 'selected_supply_chain' not in st.session_state or not st.session_state.selected_supply_chain:
    st.error("No supply chain selected. Please select a supply chain first.")
else:
    supply_chain_id = st.session_state.selected_supply_chain["id"]

# Automatically load assessed events when the page loads
if "alerts" not in st.session_state or st.session_state.alerts_source != "existing":
    try:
        assessed_events = fetch_assessed_events(supply_chain_id=supply_chain_id)
        if not assessed_events:
            st.info("No assessed events found for this supply chain.")
        else:
            st.session_state.alerts = assessed_events
            st.session_state.alerts_source = "existing"
    except Exception as e:
        st.error(f"Error loading existing events: {e}")

# Button: Fetch & assess new/unassessed events
if st.button("Fetch & Assess Unassessed Events"):
    try:
        unassessed_events = assess_unassessed_events(supply_chain_id=supply_chain_id)
        if not unassessed_events:
            st.info("No new unassessed events found. All events are already processed.")
        else:
            st.session_state.alerts = unassessed_events
            st.session_state.alerts_source = "unassessed"
            st.success("Fetched and assessed new events.")
    except Exception as e:
        st.error(f"Error fetching unassessed events: {e}")

# Define filter options
ALL_RISK_CATEGORIES = ["Financial", "Geopolitical", "Technology", "Environmental", "Social", "Governance"]
LIKELIHOOD_OPTIONS = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
IMPACT_OPTIONS = ["Insignificant", "Minor", "Moderate", "Major", "Catastrophic"]
RISK_LEVEL_OPTIONS = ["Low Risk", "Moderate Risk", "High Risk", "Extreme Risk"]

# Add an expandable filter panel including risk category, likelihood, impact, and overall risk level
with st.expander("Filter Events", expanded=False):
    st.multiselect(
        "Select Risk Categories:",
        options=ALL_RISK_CATEGORIES,
        default=st.session_state.get("selected_risk_categories", ALL_RISK_CATEGORIES),
        key="selected_risk_categories"
    )
    if 'selected_likelihood' not in st.session_state:
        st.session_state.selected_likelihood = LIKELIHOOD_OPTIONS
    if 'selected_impact' not in st.session_state:
        st.session_state.selected_impact = IMPACT_OPTIONS
    if 'selected_risk_levels' not in st.session_state:
        st.session_state.selected_risk_levels = RISK_LEVEL_OPTIONS

    st.multiselect(
        "Select Likelihood Ratings:",
        options=LIKELIHOOD_OPTIONS,
        default=st.session_state.selected_likelihood,
        key="selected_likelihood"
    )
    st.multiselect(
        "Select Impact Ratings:",
        options=IMPACT_OPTIONS,
        default=st.session_state.selected_impact,
        key="selected_impact"
    )
    st.multiselect(
        "Select Overall Risk Levels:",
        options=RISK_LEVEL_OPTIONS,
        default=st.session_state.selected_risk_levels,
        key="selected_risk_levels"
    )

sort_option = st.selectbox(
    "Sort events by:",
    ["Risk Score (high to low)", "Timestamp (newest first)", "Timestamp (oldest first)"]
)

reverse_likelihood = {
    0.001: "Rare",
    0.01: "Unlikely",
    0.1: "Possible",
    0.5: "Likely",
    0.9: "Almost Certain"
}
reverse_impact = {
    0.001: "Insignificant",
    0.01: "Minor",
    0.1: "Moderate",
    0.5: "Major",
    0.9: "Catastrophic"
}


def get_risk_level(score: float) -> str:
    if score < 0.10:
        return "Very Low Risk"
    elif score < 0.30:
        return "Low Risk"
    elif score < 0.55:
        return "Medium Risk"
    elif score < 0.75:
        return "High Risk"
    else:
        return "Extreme Risk"


risk_level_colors = {
    "Very Low Risk": "#3498DB",  # Blue
    "Low Risk": "#2ECC71",  # Green
    "Medium Risk": "#F1C40F",  # Yellow
    "High Risk": "#E67E22",  # Orange
    "Extreme Risk": "#C0392B"  # Dark Red
}

if st.session_state.alerts:
    filtered_events = [
        event for event in st.session_state.alerts
        if event.get("risk_assessment") is not None
           and event["risk_assessment"].get("is_relevant")
           and any(risk["class_name"] in st.session_state.selected_risk_categories
                   for risk in event.get("risk_categories", []))
           and (reverse_likelihood.get(event["risk_assessment"].get("likelihood"), str(event["risk_assessment"].get("likelihood"))) in st.session_state.selected_likelihood)
           and (reverse_impact.get(event["risk_assessment"].get("impact"), str(event["risk_assessment"].get("impact"))) in st.session_state.selected_impact)
           and (get_risk_level(event["risk_assessment"].get("risk_score", 0)) in st.session_state.selected_risk_levels)
    ]

    if sort_option == "Risk Score (high to low)":
        filtered_events = sorted(filtered_events, key=lambda e: e["risk_assessment"].get("risk_score", 0), reverse=True)
    elif sort_option == "Timestamp (newest first)":
        filtered_events = sorted(
            filtered_events,
            key=lambda e: datetime.datetime.fromisoformat(e["timestamp"].replace("Z", "")).date(),
            reverse=True
        )
    elif sort_option == "Timestamp (oldest first)":
        filtered_events = sorted(
            filtered_events,
            key=lambda e: datetime.datetime.fromisoformat(e["timestamp"].replace("Z", "")).date()
        )
else:
    filtered_events = []

# Display filtered events
if filtered_events:
    if st.session_state.selected_risk_categories == ALL_RISK_CATEGORIES:
        st.write(f"### Events for: {st.session_state.alerts_source.capitalize()}")
    else:
        st.write(f"### Filtered Events for: {st.session_state.alerts_source.capitalize()}")
    st.write("---")
    for event in filtered_events:
        risk_assessment = event["risk_assessment"]
        title = event["title"]
        description = event.get("description", "No description available.")
        source = event.get("source_name", "Unknown")
        try:
            dt = datetime.datetime.fromisoformat(event["timestamp"].replace("Z", ""))
            formatted_date = dt.strftime("%d/%m/%Y")
        except Exception as e:
            formatted_date = event["timestamp"]

        url = event.get("url", "#")
        likelihood = risk_assessment["likelihood"]
        impact = risk_assessment["impact"]
        reason = risk_assessment["reason"]
        stored_risk = risk_assessment.get("risk_score", 0)
        overall_risk_level = get_risk_level(stored_risk)

        st.subheader(f"[{title}]({url})")

        risk_categories = event.get("risk_categories", [])
        if risk_categories:
            formatted_risks = [
                f"{risk['class_name']}" + (f": {', '.join(risk.get('families', []))}" if risk.get("families") else "")
                for risk in risk_categories
            ]
            st.markdown(f"**Risk Categories:** {', '.join(formatted_risks)}")
        else:
            st.markdown("**Risk Categories:** Not categorized")

        st.write(f"**Description:** {description}")

        likelihood_label = reverse_likelihood.get(likelihood, f"{likelihood}")
        impact_label = reverse_impact.get(impact, f"{impact}")

        likelihood_colors = {
            "Rare": "#3498DB",
            "Unlikely": "#2ECC71",
            "Possible": "#F1C40F",
            "Likely": "#E67E22",
            "Almost Certain": "#C0392B"
        }
        impact_colors = {
            "Insignificant": "#3498DB",
            "Minor": "#2ECC71",
            "Moderate": "#F1C40F",
            "Major": "#E67E22",
            "Catastrophic": "#C0392B"
        }

        color_likelihood = likelihood_colors.get(likelihood_label, "gray")
        color_impact = impact_colors.get(impact_label, "gray")

        likelihood_tag = f"""<span style="
            background-color: {color_likelihood};
            padding: 4px 8px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
        ">{likelihood_label}</span>"""
        impact_tag = f"""<span style="
            background-color: {color_impact};
            padding: 4px 8px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
        ">{impact_label}</span>"""

        overall_color = risk_level_colors.get(overall_risk_level, "gray")
        overall_tag = f"""<span style="
            background-color: {overall_color};
            padding: 4px 8px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
        ">{overall_risk_level}</span>"""

        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
              <div>
                <strong>Likelihood:</strong> {likelihood_tag} &emsp; <strong>Impact:</strong> {impact_tag}
              </div>
              <div>
                <strong>Risk Level:</strong> {overall_tag}
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(f"*{reason}*")

        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            st.write(f"**Source:** {source} &emsp; **Published At:** {formatted_date}")
        with col2:
            with st.container():
                if st.button("✏️ Edit", key=f"edit_{event['id']}"):
                    edit_event_dialog(event)

        st.write("---")
else:
    if st.session_state.selected_risk_categories == ALL_RISK_CATEGORIES:
        st.info("No events available for the selected query.")
    else:
        st.info("No matching events found based on the selected filters.")


if "edited_event" in st.session_state:
    updated_event = st.session_state.pop("edited_event")

    if updated_event is not None:
        update_event(updated_event)
        st.success(f"Event '{updated_event['title']}' updated successfully!")

    try:
        assessed_events = fetch_assessed_events(supply_chain_id=supply_chain_id)
        if not assessed_events:
            st.info("No assessed events found for this supply chain.")
        else:
            st.session_state.alerts = assessed_events
            st.session_state.alerts_source = "existing"
            st.rerun()
    except Exception as e:
        st.error(f"Error reloading events: {e}")
