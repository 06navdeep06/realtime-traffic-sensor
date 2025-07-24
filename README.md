# AI-Powered Traffic Management System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io/)

An intelligent traffic management system that uses reinforcement learning to optimize traffic light timing based on real-time traffic conditions. The system integrates with the TomTom API to fetch live traffic data and simulates vehicle movement through a city's road network.

## 🌟 Features

- **Real-time Traffic Monitoring**: Displays live traffic data through a city's road network
- **AI-Powered Analysis**: Uses machine learning to analyze traffic patterns
- **Interactive Dashboard**: Streamlit-based web interface for monitoring and control
- **Real-time Data Integration**: Continuously fetches and displays live traffic data
- **Scalable Architecture**: Handles hundreds of vehicles and multiple intersections

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Internet connection (for fetching real-time traffic data)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/06navdeep06/realtime-traffic-sensor.git
   cd realtime-traffic-sensor
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## 🏃‍♂️ Running the Application

1. Start the Streamlit dashboard:
   ```bash
   streamlit run dashboard.py
   ```

2. Open your browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. In the sidebar:
   - Specify the city to monitor (e.g., "Patan, Nepal")
   - Adjust the number of vehicles to display (10-500)
   - Click "Start Real-time Traffic Monitoring"

## 🛠 Project Structure

- `dashboard.py`: Streamlit web interface for the traffic simulation
- `simulation.py`: Core simulation logic and vehicle management
- `traffic_signal.py`: Traffic signal controller with Q-learning agent
- `rl_agent.py`: Implementation of the Q-learning algorithm
- `road_network.py`: Handles road network data and real-time traffic updates
- `visualization.py`: Visualization utilities for the road network and traffic

## 🤖 How It Works

The system provides real-time traffic monitoring and analysis:

1. **Road Network Modeling**: Uses OSMnx to fetch and model real-world road networks
2. **Real-time Data Processing**: Continuously fetches and processes live traffic data
3. **Traffic Analysis**: Uses machine learning to analyze traffic patterns and congestion
4. **Interactive Visualization**: Provides real-time visualization of traffic flow and conditions

## 📊 Performance Metrics

The dashboard displays several key metrics:
- Simulation step count
- Number of active vehicles
- Average trip time (in simulation steps)
- Current state of each traffic signal

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [TomTom](https://www.tomtom.com/) for their traffic data API
- [OSMnx](https://github.com/gboeing/osmnx) for road network data
- [Streamlit](https://streamlit.io/) for the web interface
- [NetworkX](https://networkx.org/) for graph operations

## 📬 Contact

For questions or feedback, please contact nepal00909@gmail.com
