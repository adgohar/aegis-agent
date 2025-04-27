import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

from components.charts import (
    create_overall_risk_donut_chart,
    create_broad_risk_donut_chart,
    create_risk_subcategory_wordcloud,
    flatten_events
)
from components.risk_matrix import render_risk_matrix
from utils.api_client import (
    fetch_bayesian_risk_scores,
    fetch_stored_bayesian_risk_scores,
    fetch_assessed_events
)

st.title("Risk Dashboard & Analysis")

# Automatically fetch and create charts from stored events on page load
try:
    events = fetch_assessed_events(supply_chain_id=1)
    if not events:
        st.info("No assessed events found.")
    else:
        df_events = flatten_events(events)

        # Create Chart 1: Donut Chart by Overall Risk Level
        risk_level_colors = {
            "Very Low Risk": "#3498DB",
            "Low Risk": "#2ECC71",
            "Medium Risk": "#F1C40F",
            "High Risk": "#E67E22",
            "Extreme Risk": "#C0392B"
        }
        fig1 = create_overall_risk_donut_chart(df_events, risk_level_colors)

        # Create Chart 2: Donut Chart by Broad Risk Category
        ALL_RISK_CATEGORIES = ["Financial", "Geopolitical", "Technology", "Environmental", "Social", "Governance"]
        fig2 = create_broad_risk_donut_chart(df_events, ALL_RISK_CATEGORIES)

        # Create Chart 3: Word Cloud for Risk Subcategories
        fig_wc = create_risk_subcategory_wordcloud(events, df_events)

        # Display the two donut charts side by side
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            st.plotly_chart(fig2, use_container_width=True)

        # Display the word cloud below the donut charts
        if fig_wc is not None:
            st.write("### Risk Subcategory Word Cloud")
            st.pyplot(fig_wc, use_container_width=True)
        else:
            st.info("No risk subcategory data available for the word cloud.")
except Exception as e:
    st.error(f"Error fetching and displaying charts: {e}")


# Fetch stored Bayesian risk scores on page load
score_data = None
try:
    result = fetch_stored_bayesian_risk_scores()
    if "message" in result:
        st.warning(result["message"])
    else:
        score_data = result.get("risk_scores", {})
except Exception as e:
    st.error(f"Failed to fetch stored risk scores: {str(e)}")


if st.button("Update Graphics"):
    try:
        result = fetch_bayesian_risk_scores()
        if "message" in result:
            st.warning(result["message"])
        else:
            st.success("Successfully computed and saved new risk scores.")
            score_data = result.get("risk_scores", {})
    except Exception as e:
        st.error(f"Failed to compute and display new risk scores: {str(e)}")


# Only display charts if we have data
if score_data:
    df = pd.DataFrame(list(score_data.items()), columns=["Category", "Score"])
    df["Score"] = df["Score"].round(2)

    st.write("### Geopolitical Risk Scores")

    # 1) Spider (Radar) Chart
    fig_radar = px.line_polar(
        df, r="Score", theta="Category", line_close=True, range_r=[0, 1], hover_name="Category",
        hover_data=["Score"], markers=True
    )
    fig_radar.update_traces(fill="toself", hoveron="points+fills")
    config = {"modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"
    ]}
    st.plotly_chart(fig_radar, use_container_width=True, config=config)

    # 2) Bar Chart
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Category", sort=None),
            y=alt.Y("Score", scale=alt.Scale(domain=[0, 1])),
            color=alt.Color(
                "Score:Q",
                scale=alt.Scale(
                    domain=[0, 0.10, 0.10, 0.30, 0.30, 0.55, 0.55, 0.75, 0.75, 1],
                    range=[
                        "#3498DB", "#3498DB", "#2ECC71", "#2ECC71", "#F1C40F", "#F1C40F",
                        "#E67E22", "#E67E22", "#C0392B", "#C0392B"
                    ]
                ),
                legend=alt.Legend(title="Risk Score")
            ),
            tooltip=["Category", alt.Tooltip("Score:Q", format=".2f")]
        )
        .properties(width=800, height=400)
    )
    st.altair_chart(chart, use_container_width=True)

else:
    st.write("No risk scores to display yet.")

st.write("### Risk Matrix")
render_risk_matrix()

st.write("### Risk Scale Legend")
st.markdown(
    """
    - <span style="color:#3498DB;">■</span> **Very Low Risk:** normalized risk < 0.10  
    - <span style="color:#2ECC71;">■</span> **Low Risk:** 0.10 ≤ normalized risk < 0.30  
    - <span style="color:#F1C40F;">■</span> **Medium Risk:** 0.30 ≤ normalized risk < 0.55  
    - <span style="color:#E67E22;">■</span> **High Risk:** 0.55 ≤ normalized risk < 0.75  
    - <span style="color:#C0392B;">■</span> **Extreme Risk:** normalized risk ≥ 0.75  
    """,
    unsafe_allow_html=True
)
