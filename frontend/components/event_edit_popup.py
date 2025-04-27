import streamlit as st

from utils.api_client import delete_event

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


# Updated color mapping for overall risk level tags.
risk_level_colors = {
    "Very Low Risk": "#3498DB",  # Blue
    "Low Risk": "#2ECC71",  # Green
    "Medium Risk": "#F1C40F",  # Yellow
    "High Risk": "#E67E22",  # Orange
    "Extreme Risk": "#C0392B"  # Dark Red
}

# Define dropdown options for Likelihood and Impact
LIKELIHOOD_OPTIONS = {
    "Rare (0.001)": 0.001,
    "Unlikely (0.01)": 0.01,
    "Possible (0.1)": 0.1,
    "Likely (0.5)": 0.5,
    "Almost Certain (0.9)": 0.9
}

IMPACT_OPTIONS = {
    "Insignificant (0.001)": 0.001,
    "Minor (0.01)": 0.01,
    "Moderate (0.1)": 0.1,
    "Major (0.5)": 0.5,
    "Catastrophic (0.9)": 0.9
}

ALL_RISK_CATEGORIES = {
    "Financial": [
        "Economic Outlook", "Economic Variables", "Market Crisis", "Trading Environment",
        "Company Outlook", "Competition", "Counterparty"
    ],
    "Geopolitical": [
        "Business Environment (Country Risk)", "Corruption & Crime", "Government Business Policy",
        "Change in Government", "Political Violence", "Interstate Conflict"
    ],
    "Technology": [
        "Disruptive Technology", "Cyber", "Critical Infrastructure", "Industrial Accident"
    ],
    "Environmental": [
        "Extreme Weather", "Geophysical", "Space", "Climate Change",
        "Environmental Degradation", "Natural Resource Deficiency", "Food Security"
    ],
    "Social": [
        "Socioeconomic Trends", "Human Capital", "Brand Perception", "Sustainable Living",
        "Health Trends", "Infectious Disease"
    ],
    "Governance": [
        "Non-Compliance", "Litigation", "Strategic Performance", "Management Performance",
        "Business Model Deficiencies", "Pension Management", "Products & Services"
    ]
}


@st.dialog("Edit Event", width="large")
def edit_event_dialog(event):
    st.write(f"### Editing Event: {event.get('title', 'Unnamed Event')}")
    editable_event = event.copy()

    editable_event["title"] = st.text_input("Event Title", event.get("title", ""))
    editable_event["description"] = st.text_area("Event Description", event.get("description", ""))

    # Risk category selection
    current_risks = event.get("risk_categories", [])
    current_classes = [risk["class_name"] for risk in current_risks]
    current_families = {
        risk["class_name"]: risk.get("families", []) for risk in current_risks
    }
    # Step 1: Select Risk Classes
    selected_classes = st.multiselect("Select Risk Classes", ALL_RISK_CATEGORIES.keys(), default=current_classes)
    # Step 2: Select Families for each chosen class
    selected_families = {}
    for class_name in selected_classes:
        available_families = ALL_RISK_CATEGORIES[class_name]
        previously_selected_families = current_families.get(class_name, [])
        selected_families[class_name] = st.multiselect(f"Select Families for {class_name}", available_families,
                                                       default=previously_selected_families)
    # Update the editable event with the new risk classification
    editable_event["risk_categories"] = [{"class_name": cls, "families": selected_families[cls]} for cls in
                                         selected_classes]

    # **Is Relevant Checkbox**
    is_relevant_default = event.get("risk_assessment", {}).get("is_relevant", True)
    editable_event.setdefault("risk_assessment", {})["is_relevant"] = st.checkbox("Is this event relevant?",
                                                                                  value=is_relevant_default)

    # **Only show risk assessment fields if the event is relevant**
    if editable_event["risk_assessment"]["is_relevant"]:
        # Likelihood and Impact selection (side by side)
        col1, col2 = st.columns(2)
        with col1:
            likelihood_label = next((k for k, v in LIKELIHOOD_OPTIONS.items() if
                                     v == event.get("risk_assessment", {}).get("likelihood", 0.1)), "Possible (0.1)")
            selected_likelihood = st.selectbox("Likelihood", options=LIKELIHOOD_OPTIONS.keys(),
                                               index=list(LIKELIHOOD_OPTIONS.keys()).index(likelihood_label))
            likelihood_value = LIKELIHOOD_OPTIONS[selected_likelihood]

        with col2:
            impact_label = next(
                (k for k, v in IMPACT_OPTIONS.items() if v == event.get("risk_assessment", {}).get("impact", 0.1)),
                "Moderate (0.1)")
            selected_impact = st.selectbox("Impact", options=IMPACT_OPTIONS.keys(),
                                           index=list(IMPACT_OPTIONS.keys()).index(impact_label))
            impact_value = IMPACT_OPTIONS[selected_impact]

        # Compute Risk Score
        raw_risk = likelihood_value + impact_value
        normalized_risk = (raw_risk - 0.002) / (1.8 - 0.002)  # (raw_risk - 0.002) / 1.798
        editable_event["risk_assessment"]["likelihood"] = likelihood_value
        editable_event["risk_assessment"]["impact"] = impact_value
        editable_event["risk_assessment"]["risk_score"] = normalized_risk

        # Determine the risk level
        overall_risk_level = get_risk_level(normalized_risk)
        overall_color = risk_level_colors.get(overall_risk_level, "gray")

        # Display calculated risk score with color-coded tag
        st.markdown(
            f"""
            <div style="
                display: inline-block;
                background-color: {overall_color};
                padding: 6px 12px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                text-align: center;
            ">
                {overall_risk_level} ({normalized_risk:.3f})
            </div>
            """,
            unsafe_allow_html=True
        )

        # Editable reason field
        editable_event["risk_assessment"]["reason"] = st.text_area("Risk Assessment Reason",
                                                                   event.get("risk_assessment", {}).get("reason", ""))

        # Buttons: Save, Delete, Cancel (Aligned in three columns)
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("Save Changes"):
                st.session_state["edited_event"] = editable_event
                st.rerun()  # Close the dialog and refresh the app

        with col2:
            if st.button("🗑️ Delete Event", help="Permanently remove this event", key="delete_event_button"):
                if st.session_state.get("confirm_delete") is None:
                    st.session_state["confirm_delete"] = event["id"]  # Store ID to confirm deletion

            # Show confirmation dialog if the button was clicked
            if st.session_state.get("confirm_delete") == event["id"]:
                st.warning("Are you sure you want to delete this event?", icon="⚠️")

                col_del1, col_del2 = st.columns(2)
                with col_del1:
                    if st.button("Yes, Delete", key="confirm_delete_button"):
                        delete_event(event)  # Call API to delete event
                        st.session_state["edited_event"] = None  # Close dialog
                        st.session_state["confirm_delete"] = None  # Reset confirmation state
                        st.success("Event deleted successfully!")
                        st.rerun()  # Refresh the page

                with col_del2:
                    if st.button("Cancel", key="cancel_delete_button"):
                        st.session_state["confirm_delete"] = None  # Reset confirmation state

        with col3:
            if st.button("Cancel"):
                st.rerun()  # Close the dialog without saving
