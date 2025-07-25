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
    
    # Location input with better guidance
    st.subheader("Location")
    location_type = st.radio("Choose location type:", ["City Name", "Coordinates"])
    
    if location_type == "City Name":
        city_name = st.text_input("Enter city name (e.g., 'Kathmandu, Nepal' or 'New York, USA'):", 
                                value="Kathmandu, Nepal")
        st.caption("Tip: Try major cities for better results")
    else:
        col1, col2 = st.columns(2)
        with col1:
            lat = st.text_input("Latitude (e.g., 27.7172):", value="27.7172")
        with col2:
            lon = st.text_input("Longitude (e.g., 85.3240):", value="85.3240")
        city_name = f"{lat}, {lon}"
    
    st.subheader("Simulation Settings")
    num_vehicles = st.slider("Number of Vehicles", 10, 500, 100)
    
    # Add some helpful information
    with st.expander("ℹ️ Help"):
        st.write("""
        - For best results, use well-known city names or coordinates.
        - If a location isn't found, the system will default to Kathmandu, Nepal.
        - You can find coordinates using services like Google Maps (right-click → What's here?)
        """)

    if st.button("Start Real-time Traffic Monitoring"):
        with st.spinner(f"Loading real-time traffic data for {city_name}..."):
            try:
                st.session_state.graph = get_road_network(city_name.strip())
                st.session_state.running = True
                st.session_state.last_update = time.time()
                st.success("Successfully loaded traffic data!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.error("Could not load traffic data. Trying with default location...")
                try:
                    st.session_state.graph = get_road_network("27.7172, 85.3240")  # Kathmandu
                    st.session_state.running = True
                    st.session_state.last_update = time.time()
                    st.success("Successfully loaded default location (Kathmandu, Nepal).")
                except Exception as e2:
                    st.error("Failed to load default location. Please try again later.")
                    st.stop()
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
    # Main visualization columns
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("Live Traffic Map")
        map_placeholder = st.empty()
        
        # Add a legend for the map
        with st.expander("ℹ️ Map Legend"):
            col1_1, col1_2, col1_3, col1_4 = st.columns(4)
            with col1_1:
                st.markdown("""
                **Traffic Flow**
                - 🟢 Free flowing
                - 🟡 Light traffic
                - 🟠 Moderate
                - 🔴 Heavy traffic
                """)
            with col1_2:
                st.markdown("""
                **Line Thickness**
                - Thin: Low volume
                - Thick: High volume
                """)
            with col1_3:
                st.markdown("""
                **Intersections**
                - 🔵 Size indicates connectivity
                - Larger = more roads
                """)
            with col1_4:
                st.markdown("""
                **Traffic Lights**
                - 🟢 Green: Active phase
                - 🔴 Red: Inactive phase
                """)

    with col2:
        st.header("Live Metrics")
        
        # Traffic summary card
        with st.container():
            st.markdown("### Traffic Summary")
            
            # Calculate traffic metrics
            edges = list(st.session_state.graph.edges(data=True))
            if edges:
                congested_roads = sum(1 for _, _, data in edges if data.get('congestion', 0) > 0.5)
                total_roads = len(edges)
                congestion_percent = (congested_roads / total_roads) * 100 if total_roads > 0 else 0
                
                # Traffic health indicator
                if congestion_percent > 70:
                    traffic_status = "🔴 High Congestion"
                    status_color = "#ff4b4b"
                elif congestion_percent > 40:
                    traffic_status = "🟠 Moderate Traffic"
                    status_color = "#ffa500"
                else:
                    traffic_status = "🟢 Smooth Traffic"
                    status_color = "#2ecc71"
                
                st.markdown(f"""
                <div style='background-color:#f0f2f6; padding:15px; border-radius:10px; margin-bottom:15px;'>
                    <p style='font-size:16px; margin:0;'><strong>Network Status</strong></p>
                    <p style='font-size:24px; margin:5px 0; color:{status_color};'>{traffic_status}</p>
                    <p style='font-size:14px; margin:0;'>{congested_roads} of {total_roads} roads congested</p>
                    <div style='height:8px; background-color:#e0e0e0; border-radius:4px; margin:8px 0;'>
                        <div style='height:100%; width:{congestion_percent}%; background-color:{status_color}; border-radius:4px;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Simulation metrics
        with st.container():
            st.markdown("### Simulation Metrics")
            step_counter = st.empty()
            vehicle_counter = st.empty()
            avg_trip_time_counter = st.empty()
        
        # Signal states
        with st.container():
            st.markdown("### Signal States")
            signal_states_table = st.empty()
            
            # Add signal state legend
            st.caption("""
            **Signal States**
            - 🟢 Green: Active phase
            - 🔴 Red: Inactive phase
            - ⚪ Off: Signal not active
            
            *Hover over signals on the map for details*
            """)

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

        # Update traffic map with enhanced visualization
        with map_placeholder.container():
            # Create figure with larger size for better visibility
            fig = plot_traffic_graph(graph, figsize=(12, 10))
            
            # Add traffic signals to the map
            ax = fig.axes[0]
            if hasattr(sim, 'traffic_signals'):
                for signal_id, signal in sim.traffic_signals.items():
                    # Get the intersection node position
                    node_pos = (graph.nodes[signal.intersection_node]['x'], 
                              graph.nodes[signal.intersection_node]['y'])
                    
                    # Plot the traffic signal
                    signal_color = 'green' if signal.green_lane_index is not None else 'red'
                    ax.plot(node_pos[0], node_pos[1], 'o', 
                           markersize=15, 
                           markerfacecolor=signal_color,
                           markeredgecolor='white',
                           markeredgewidth=1.5,
                           alpha=0.9,
                           zorder=10)
                    
                    # Add signal ID as text
                    ax.text(node_pos[0], node_pos[1], str(signal_id), 
                           color='white', 
                           fontsize=8,
                           ha='center', 
                           va='center',
                           fontweight='bold')
            
            # Add a title with update time
            ax.set_title(f"Live Traffic - {time.strftime('%H:%M:%S')}", 
                        fontsize=12, pad=15, fontweight='bold')
            
            # Display the figure
            st.pyplot(fig, use_container_width=True)
            
            # Add a small caption with last update time
            st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Add a small note about the visualization
            st.caption("""
            💡 **Tip**: The map shows real-time traffic conditions. 
            - Thicker, redder lines indicate heavier traffic.
            - Blue circles represent intersections with traffic signals.
            """)

        # Control the loop speed
        time.sleep(2) # Refresh every 2 seconds
