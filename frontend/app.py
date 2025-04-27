import streamlit as st

st.logo("assets/Logo&name.svg", size="large")

overview_page = st.Page("pages/overview.py", title="Overview", icon="🏠")
events_news_page = st.Page("pages/events_news.py", title="Events & News", icon="📰")
assess_events_page = st.Page("pages/assess_events.py", title="Assess Events", icon="🔍")
map_page = st.Page("pages/map.py", title="Map", icon="🗺️")
risk_dashboard_page = st.Page("pages/risk_dashboard.py", title="Risk Dashboard", icon="📊")
agent_page = st.Page("pages/agent.py", title="Agent", icon="🤖")

pg = st.navigation([overview_page, agent_page, events_news_page, assess_events_page, map_page, risk_dashboard_page])

with st.sidebar:
    try:
        from utils.api_client import fetch_supply_chains, get_selected_supply_chain, set_selected_supply_chain

        supply_chains = fetch_supply_chains()
        supply_chain_names = {sc["id"]: sc["companyName"] for sc in supply_chains}

        if "selected_supply_chain" not in st.session_state:
            try:
                st.session_state.selected_supply_chain = get_selected_supply_chain()
            except Exception as e:
                st.warning(f"Error fetching selected supply chain: {e}")
                st.session_state.selected_supply_chain = None

        selected_supply_chain_id = st.selectbox(
            "Select Supply Chain",
            options=supply_chain_names.keys(),
            format_func=lambda x: supply_chain_names[x],
            index=list(supply_chain_names.keys()).index(
                st.session_state.selected_supply_chain["id"]
            ) if st.session_state.selected_supply_chain else 0
        )

        if selected_supply_chain_id != (
        st.session_state.selected_supply_chain["id"] if st.session_state.selected_supply_chain else None):
            try:
                set_selected_supply_chain(selected_supply_chain_id)
                st.session_state.selected_supply_chain = {
                    "id": selected_supply_chain_id,
                    "companyName": supply_chain_names[selected_supply_chain_id]
                }
                st.success(f"Supply chain '{supply_chain_names[selected_supply_chain_id]}' set as selected.")
            except Exception as e:
                st.error(f"Error setting selected supply chain: {e}")

    except Exception as e:
        st.error(f"Error loading supply chains: {e}")

pg.run()
