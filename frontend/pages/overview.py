import streamlit as st

# Title and subtitle
st.title("Welcome to aegis")
st.write("**Empowering Proactive Supply Chain Risk Management**")

# Introduction
st.markdown(
    """
    In an interconnected global economy, geopolitical risks, from trade disputes to regional conflicts, can
    critically disrupt supply chains, causing costly delays and inefficiencies. Recent crises such as 
    the COVID-19 pandemic, Brexit, and the Russia-Ukraine conflict have underscored the need for more 
    **proactive** and **resilient** supply chain strategies.

    **aegis** is designed to help supply chain managers and decision-makers systematically 
    monitor, analyze, and anticipate disruptions **before** they escalate. Leveraging GPT-powered analysis, 
    it focuses on **geopolitical events** that may impact suppliers, transportation routes, and crucial 
    network nodes.
    """
)

# Overview of Workflow / Step-by-Step
st.header("How aegis Works")

st.markdown(
    """
    aegis offers **four main steps** to move from raw data collection to final risk scores:

    1. **Events & News**  
       Fetch events from external news sources. 
       This step gathers potential disruptions tied to keywords or topics of interest.

    2. **Assess Events**  
       Evaluate which events truly matter to the given network. aegis uses GPT-based relevance
       analysis to filter events and assign risk levels (likelihood, impact), storing only those events that could 
       disrupt the given supply chain.

    3. **Map & Supply Chain Visualization**  
       Overlay assessed events onto an interactive map of the supply chain. 
       Quickly spot potential trouble spots or critical links facing threats.

    4. **Risk Dashboard & Analysis**  
       Compute high-level Bayesian risk scores per category (e.g., Geopolitical, Financial, etc.) 
       and visualize them in a radar or bar chart. This gives an **overall** picture of 
       the supply chain’s health and where vulnerabilities may lie.
    """
)

