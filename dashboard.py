import streamlit as st
from streamlit.components.v1 import html
import pandas as pd
import time
import os
from road_network import get_road_network, get_edge_midpoints, update_graph_with_traffic
from simulation import Simulation
from visualization import plot_traffic_graph

def add_watermark():
    """Adds a subtle watermark to the bottom right of the page"""
    watermark = """
    <style>
        .watermark {
            position: fixed;
            bottom: 10px;
            right: 10px;
            color: rgba(0, 0, 0, 0.1);
            font-size: 24px;
            font-weight: bold;
            pointer-events: none;
            transform: rotate(-15deg);
            z-index: 1000;
            user-select: none;
        }
    </style>
    <div class="watermark">Navdeep</div>
    """
    st.markdown(watermark, unsafe_allow_html=True)

st.set_page_config(layout="wide")
st.title("AI-Powered Traffic Management Dashboard")

# --- Session State Initialization ---
def init_session_state():
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'simulation' not in st.session_state:
        st.session_state.simulation = None
    if 'graph' not in st.session_state:
        st.session_state.graph = None
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    if 'last_update' not in st.session_state:
        st.session_state.last_update = 0

init_session_state()

# --- Sidebar Controls ---
with st.sidebar:
    st.header("System Controls")
    # Using the provided API key by default
    st.session_state.api_key = "tEZ8WgFXLuAuDjHmB3AB5y89ue31PsGL"
    city_name = st.text_input("City Name", "Patan, Nepal")
    num_vehicles = st.slider("Number of Vehicles", 10, 500, 100)

    if st.button("Start Real-time Traffic Monitoring"):
        with st.spinner(f"Loading real-time traffic data for {city_name}..."):
            st.session_state.graph = get_road_network(city_name)
            sim = Simulation(st.session_state.graph, num_vehicles)
            
            # Load pre-trained Q-tables for all signals
            q_tables_dir = "q_tables"
            for signal_id, signal in sim.traffic_signals.items():
                q_table_path = os.path.join(q_tables_dir, f"q_table_{signal_id}.json")
                signal.agent.load_q_table(q_table_path)
            
            st.session_state.simulation = sim
            st.session_state.running = True
            st.session_state.last_update = time.time()
        st.success("Real-time traffic monitoring is now active. The system is now displaying live traffic data.")

    if st.button("Stop"):
        st.session_state.running = False
        st.info("Simulation stopped.")

# --- Watermark ---
add_watermark()

# --- Main Dashboard Layout ---
if not st.session_state.running:
    st.info("Please initialize the simulation using the controls in the sidebar.")
else:
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("Live Traffic Map")
        map_placeholder = st.empty()

    with col2:
        st.header("Live Metrics")
        step_counter = st.empty()
        vehicle_counter = st.empty()
        avg_trip_time_counter = st.empty()
        st.header("Signal States")
        signal_states_table = st.empty()

    # --- Live Update Loop ---
    while st.session_state.running:
        sim = st.session_state.simulation
        graph = st.session_state.graph

        # Refresh real-world traffic data every 60 seconds
        if time.time() - st.session_state.last_update > 60:
            with st.spinner('Fetching latest traffic data from TomTom API...'):
                midpoints = get_edge_midpoints(graph)
                update_graph_with_traffic(graph, midpoints, st.session_state.api_key)
                st.session_state.last_update = time.time()

        # Advance simulation by one step
        sim_data = sim.step()

        # Update metrics
        step_counter.metric("Simulation Step", f"{sim_data['step']:,}")
        vehicle_counter.metric("Active Vehicles", f"{sim_data['active_vehicles']:,}")
        avg_trip_time_counter.metric("Avg. Trip Time (steps)", f"{sim_data['avg_trip_time']:.2f}")

        # Update signal states table
        signal_df = pd.DataFrame(
            sim_data["signal_states"].items(),
            columns=['Intersection ID', 'Green Lane']
        ).set_index('Intersection ID')
        signal_states_table.dataframe(signal_df)

        # Update traffic map
        fig = plot_traffic_graph(graph)
        map_placeholder.pyplot(fig)

        # Control the loop speed
        time.sleep(2) # Refresh every 2 seconds
