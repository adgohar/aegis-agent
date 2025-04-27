import math
import streamlit as st
from folium import Tooltip
from folium.plugins import AntPath
from streamlit_folium import st_folium
import folium
from utils.api_client import fetch_supply_chain, fetch_assessed_events

st.title("Map & Supply Chain Visualization")
st.write("""
This page provides a geographic overview of your supply chain nodes (e.g., suppliers, factories)
and allows you to **load previously assessed events** for visualization. 
Typically, this is **Step 3** or **4** in the workflow:
1) Fetch or add events on the "Events & News" page,
2) Assess them on the "Assess Events" page,
3) Load them here to see locations where disruptions may occur.
""")

if "selected_supply_chain" not in st.session_state:
    st.error("No supply chain selected. Please select a supply chain in the sidebar.")
else:
    if (
        "supply_chain" not in st.session_state
        or st.session_state.supply_chain is None
        or st.session_state.supply_chain["id"] != st.session_state.selected_supply_chain["id"]
    ):
        try:
            st.session_state.supply_chain = fetch_supply_chain(st.session_state.selected_supply_chain["id"])
        except Exception as e:
            st.error(f"Error fetching supply chain: {e}")

if 'map_events' not in st.session_state:
    st.session_state.map_events = None
if 'map_events_source' not in st.session_state:
    st.session_state.map_events_source = None


def create_shape_marker(lat, lon, popup_content, tooltip_text, shape, color, size, folium_map):
    html_marker = f"""
    <div style="font-size: {size}; color: {color}; text-align: center; transform: translate(-50%, -50%);">
        {shape}
    </div>
    """
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_content, max_width=300),
        tooltip=tooltip_text,
        icon=folium.DivIcon(html=html_marker)
    ).add_to(folium_map)


NODE_COLORS = {
    "Supplier": "green",
    "Factory": "blue",
    "Distribution Center": "purple",
    "Port": "darkblue",
    "Customer": "orange",
    "Unknown": "gray"
}

NODE_SHAPES = {
    "Supplier": ("⬤", "12px"),
    "Factory": ("▲", "20px"),
    "Distribution Center": ("⬢", "22px"),
    "Port": ("◆", "26px"),
    "Customer": ("⬟", "18px"),
    "Unknown": ("■", "24px")
}


def add_supply_chain_nodes(supply_chain, folium_map):
    for node in supply_chain.get("nodes", []):
        location = node.get("location", {})
        if location and location.get("coordinates"):
            lat, lon = location["coordinates"]
            node_type = node.get("type", "Unknown")
            popup_content = (
                f"<b>{node['id']}</b><br>"
                f"Type: {node_type}<br>"
                f"Location: {location.get('city', 'N/A')}, {location.get('country', 'N/A')}"
            )
            shape, size = NODE_SHAPES.get(node_type, ("■", "24px"))
            color = NODE_COLORS.get(node_type, "gray")

            create_shape_marker(
                lat=lat,
                lon=lon,
                popup_content=popup_content,
                tooltip_text=f"Supply Chain Node: {node_type}",
                shape=shape,
                color=color,
                size=size,
                folium_map=folium_map
            )


def calculate_arc_coordinates(source, destination, num_points=50, arc_height=0.3):
    """
    Generate a set of points to create a curved line (arc) between two locations.
    """
    lat1, lon1 = math.radians(source[0]), math.radians(source[1])
    lat2, lon2 = math.radians(destination[0]), math.radians(destination[1])

    mid_lat = (lat1 + lat2) / 2
    mid_lon = (lon1 + lon2) / 2

    dx = lon2 - lon1
    dy = lat2 - lat1
    mid_lat += -arc_height * dx
    mid_lon += arc_height * dy

    arc_points = []
    for t in range(num_points + 1):
        fraction = t / num_points
        lat = (1 - fraction) * lat1 + fraction * lat2 + arc_height * (1 - fraction) * fraction * -dx
        lon = (1 - fraction) * lon1 + fraction * lon2 + arc_height * (1 - fraction) * fraction * dy
        arc_points.append([math.degrees(lat), math.degrees(lon)])

    return arc_points


TRANSPORT_COLORS = {
    "Sea": "blue",
    "Rail": "red",
    "Air": "green",
    "Road": "orange",
    "Unknown": "gray"
}


def add_supply_chain_edges(supply_chain, folium_map):
    node_locations = {
        node["id"]: node["location"]["coordinates"]
        for node in supply_chain.get("nodes", [])
        if node.get("location", {}).get("coordinates")
    }

    for edge in supply_chain.get("edges", []):
        source = edge.get("source")
        destination = edge.get("destination")

        if source in node_locations and destination in node_locations:
            source_coords = node_locations[source]
            destination_coords = node_locations[destination]
            arc_points = calculate_arc_coordinates(source_coords, destination_coords, arc_height=0.3)

            transport_mode = edge.get('transportMode', 'Unknown')
            color = TRANSPORT_COLORS.get(transport_mode, "gray")

            path = AntPath(
                locations=arc_points,
                color=color,
                weight=2.5,
                opacity=0.8,
                dash_array=[10, 20],
                pulse_color="white"
            )
            path.add_child(Tooltip(transport_mode))
            path.add_to(folium_map)


def add_events_to_map(events_data, folium_map):
    events = events_data.get("data", []) if isinstance(events_data, dict) else events_data
    for event in events:
        location = event.get("location", {})
        if location and location.get("coordinates"):
            lat, lon = location["coordinates"]
            title = event.get("title", "No Title")
            description = event.get("description", "No description available.")
            popup_content = f"<b>{title}</b><br>{description}"

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"Event: {title}",
                icon=folium.Icon(color="red", icon="circle")
            ).add_to(folium_map)


# Single button for loading events (already assessed)
if st.button("Load Assessed Events"):
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

# Initialize the map
m = folium.Map(location=[0, 0], zoom_start=2)

# Add supply chain nodes and edges to the map
if st.session_state.get("supply_chain"):
    add_supply_chain_nodes(st.session_state.supply_chain, m)
    add_supply_chain_edges(st.session_state.supply_chain, m)

# Add events to the map
if st.session_state.map_events:
    add_events_to_map(st.session_state.map_events, m)
else:
    st.info("No events loaded yet. Click the button above to load assessed events.")

# Display the map
st_folium(m, width=700, height=500)

st.markdown(
    """
    <div style="
        background-color: white;
        border: 2px solid gray;
        border-radius: 5px;
        padding: 10px;
        font-size: 14px;
        width: 250px;
        margin-top: 10px;
    ">
        <b>Legend</b><br>
        <i style="color: green;">⬤ Supplier</i><br>
        <i style="color: blue;">▲ Factory</i><br>
        <i style="color: purple;">⬢ Distribution Center</i><br>
        <i style="color: darkblue;">◆ Port</i><br>
        <i style="color: orange;">⬟ Customer</i><br>
        <i style="color: gray;">■ Unknown</i><br>
        <span style="display: inline-flex; align-items: center;">
            <span style="width: 20px; height: 0; border-top: 2px dashed blue; margin-right: 5px;"></span>
            <i style="color: blue;">Sea Route</i>
        </span><br>
        <span style="display: inline-flex; align-items: center;">
            <span style="width: 20px; height: 0; border-top: 2px dashed orange; margin-right: 5px;"></span>
            <i style="color: orange;">Road Route</i>
        </span><br>
        <span style="display: inline-flex; align-items: center;">
            <span style="width: 20px; height: 0; border-top: 2px dashed green; margin-right: 5px;"></span>
            <i style="color: green;">Air Route</i>
        </span><br>
        <span style="display: inline-flex; align-items: center;">
            <span style="width: 20px; height: 0; border-top: 2px dashed red; margin-right: 5px;"></span>
            <i style="color: red;">Rail Route</i>
        </span><br>
        <i style="color: red;">⬤ Event</i>
    </div>
    """,
    unsafe_allow_html=True
)
