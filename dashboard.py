import streamlit as st
from streamlit.components.v1 import html
import pandas as pd
import time
import os
import logging
from road_network import get_road_network, get_edge_midpoints, update_graph_with_traffic
from simulation import Simulation
from visualization import plot_traffic_graph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    if 'error_count' not in st.session_state:
        st.session_state.error_count = 0

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
        
        # Validate coordinates
        try:
            lat_val = float(lat)
            lon_val = float(lon)
            if not (-90 <= lat_val <= 90):
                st.error("Latitude must be between -90 and 90")
                city_name = "27.7172, 85.3240"  # Default
            elif not (-180 <= lon_val <= 180):
                st.error("Longitude must be between -180 and 180")
                city_name = "27.7172, 85.3240"  # Default
            else:
                city_name = f"{lat}, {lon}"
        except ValueError:
            st.error("Please enter valid numeric coordinates")
            city_name = "27.7172, 85.3240"  # Default
    
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
                # Reset error count
                st.session_state.error_count = 0
                
                st.session_state.graph = get_road_network(city_name.strip())
                
                if st.session_state.graph is None:
                    raise ValueError("Failed to load road network")
                    
                if st.session_state.graph.number_of_nodes() == 0:
                    raise ValueError("Road network has no nodes")
                    
                st.session_state.running = True
                st.session_state.last_update = time.time()
                st.success("Successfully loaded traffic data!")
                
            except Exception as e:
                logger.error(f"Error loading road network: {str(e)}")
                st.error(f"Error: {str(e)}")
                st.error("Could not load traffic data. Trying with default location...")
                try:
                    st.session_state.graph = get_road_network("27.7172, 85.3240")  # Kathmandu
                    
                    if st.session_state.graph is None or st.session_state.graph.number_of_nodes() == 0:
                        raise ValueError("Default location also failed")
                        
                    st.session_state.running = True
                    st.session_state.last_update = time.time()
                    st.success("Successfully loaded default location (Kathmandu, Nepal).")
                except Exception as e2:
                    logger.error(f"Error loading default location: {str(e2)}")
                    st.error("Failed to load default location. Please try again later.")
                    st.stop()
            
            # Create simulation
            try:
                sim = Simulation(st.session_state.graph, num_vehicles)
                
                # Load pre-trained Q-tables for all signals
                q_tables_dir = "q_tables"
                if os.path.exists(q_tables_dir):
                    for signal_id, signal in sim.traffic_signals.items():
                        if signal and hasattr(signal, 'agent') and signal.agent:
                            q_table_path = os.path.join(q_tables_dir, f"q_table_{signal_id}.json")
                            try:
                                signal.agent.load_q_table(q_table_path)
                            except Exception as e:
                                logger.warning(f"Could not load Q-table for signal {signal_id}: {e}")
                
                st.session_state.simulation = sim
                st.success("Real-time traffic monitoring is now active. The system is now displaying live traffic data.")
                
            except Exception as e:
                logger.error(f"Error creating simulation: {str(e)}")
                st.error(f"Error creating simulation: {str(e)}")
                st.session_state.running = False
                st.stop()

    if st.button("Stop"):
        st.session_state.running = False
        st.session_state.error_count = 0
        st.info("Simulation stopped.")

# --- Watermark ---
add_watermark()

# --- Main Dashboard Layout ---
if not st.session_state.running:
    st.info("Please initialize the simulation using the controls in the sidebar.")
else:
    # Check for too many errors
    if st.session_state.error_count > 10:
        st.error("Too many errors occurred. Please restart the simulation.")
        st.session_state.running = False
        st.stop()
        
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
            
            try:
                # Calculate traffic metrics
                if st.session_state.graph and st.session_state.graph.number_of_edges() > 0:
                    edges = list(st.session_state.graph.edges(data=True))
                    if edges:
                        congested_roads = sum(1 for _, _, data in edges 
                                            if isinstance(data, dict) and 
                                            isinstance(data.get('congestion', 0), (int, float)) and 
                                            data.get('congestion', 0) > 0.5)
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
                    else:
                        st.info("No traffic data available yet.")
                else:
                    st.warning("No road network loaded.")
            except Exception as e:
                logger.error(f"Error calculating traffic metrics: {e}")
                st.error("Error calculating traffic metrics.")
        
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
        try:
            sim = st.session_state.simulation
            graph = st.session_state.graph
            
            if not sim or not graph:
                st.error("Simulation or graph is not available.")
                st.session_state.running = False
                break

            # Refresh real-world traffic data every 60 seconds
            if time.time() - st.session_state.last_update > 60:
                try:
                    with st.spinner('Fetching latest traffic data from TomTom API...'):
                        midpoints = get_edge_midpoints(graph)
                        if midpoints:
                            update_graph_with_traffic(graph, midpoints, st.session_state.api_key)
                        st.session_state.last_update = time.time()
                except Exception as e:
                    logger.warning(f"Error updating traffic data: {e}")
                    st.session_state.error_count += 1

            # Advance simulation by one step
            try:
                sim_data = sim.step()
                
                if not isinstance(sim_data, dict):
                    raise ValueError("Invalid simulation data returned")
                    
            except Exception as e:
                logger.error(f"Error in simulation step: {e}")
                st.session_state.error_count += 1
                st.error(f"Simulation error: {str(e)}")
                continue

            # Update metrics
            try:
                step_counter.metric("Simulation Step", f"{sim_data.get('step', 0):,}")
                vehicle_counter.metric("Active Vehicles", f"{sim_data.get('active_vehicles', 0):,}")
                avg_trip_time = sim_data.get('avg_trip_time', 0)
                avg_trip_time_counter.metric("Avg. Trip Time (steps)", f"{avg_trip_time:.2f}")
            except Exception as e:
                logger.warning(f"Error updating metrics: {e}")

            # Update signal states table
            try:
                signal_states = sim_data.get("signal_states", {})
                if signal_states:
                    signal_df = pd.DataFrame(
                        signal_states.items(),
                        columns=['Intersection ID', 'Green Lane']
                    ).set_index('Intersection ID')
                    signal_states_table.dataframe(signal_df)
                else:
                    signal_states_table.info("No traffic signals active.")
            except Exception as e:
                logger.warning(f"Error updating signal states: {e}")

            # Update traffic map with enhanced visualization
            try:
                with map_placeholder.container():
                    # Create figure with larger size for better visibility
                    fig = plot_traffic_graph(graph, figsize=(12, 10))
                    
                    if fig and hasattr(fig, 'axes') and fig.axes:
                        # Add traffic signals to the map
                        ax = fig.axes[0]
                        if hasattr(sim, 'traffic_signals') and sim.traffic_signals:
                            for signal_id, signal in sim.traffic_signals.items():
                                try:
                                    if not signal or not hasattr(signal, 'intersection_node'):
                                        continue
                                        
                                    # Get the intersection node position
                                    if signal.intersection_node in graph.nodes:
                                        node_data = graph.nodes[signal.intersection_node]
                                        if 'x' in node_data and 'y' in node_data:
                                            node_pos = (node_data['x'], node_data['y'])
                                            
                                            # Plot the traffic signal
                                            signal_color = 'green' if hasattr(signal, 'green_lane_index') and signal.green_lane_index is not None else 'red'
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
                                except Exception as e:
                                    logger.warning(f"Error plotting signal {signal_id}: {e}")
                        
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
                    
            except Exception as e:
                logger.error(f"Error updating traffic map: {e}")
                st.session_state.error_count += 1
                map_placeholder.error(f"Error displaying map: {str(e)}")

            # Control the loop speed
            time.sleep(2) # Refresh every 2 seconds
            
        except Exception as e:
            logger.error(f"Critical error in main loop: {e}")
            st.session_state.error_count += 1
            st.error(f"Critical error: {str(e)}")
            
            if st.session_state.error_count > 5:
                st.error("Too many errors. Stopping simulation.")
                st.session_state.running = False
                break
            
            time.sleep(5)  # Wait longer on error