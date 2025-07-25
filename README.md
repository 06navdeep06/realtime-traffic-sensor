# 🚦 AI-Powered Traffic Management System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![GitHub last commit](https://img.shields.io/github/last-commit/06navdeep06/realtime-traffic-sensor)](https://github.com/06navdeep06/realtime-traffic-sensor/commits/main)

An intelligent traffic management system that uses reinforcement learning to optimize traffic light timing based on real-time traffic conditions. The system integrates with the TomTom API to fetch live traffic data and simulates vehicle movement through a city's road network.

## 📌 Latest Updates (July 2024)

- **Enhanced Simulation**: Improved vehicle movement and traffic signal control
- **Robust Error Handling**: Added comprehensive error handling and logging
- **Compatibility Fixes**: Resolved OSMnx version compatibility issues
- **Performance Optimizations**: Improved simulation performance and stability
- **Detailed Logging**: Added timestamped logging for better debugging

## 🌟 Features

- **Real-time Traffic Monitoring**: Displays live traffic data through a city's road network
- **AI-Powered Traffic Signals**: Uses Q-learning to optimize traffic light timing
- **Interactive Dashboard**: Streamlit-based web interface for monitoring and control
- **Detailed Simulation**: Realistic vehicle movement and traffic flow modeling
- **Comprehensive Logging**: Timestamped logs for debugging and analysis
- **Error Resilience**: Robust error handling and recovery mechanisms
- **Modular Architecture**: Easy to extend and customize

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Internet connection (for fetching real-time traffic data)
- [TomTom API Key](https://developer.tomtom.com/) (free tier available)
- Git (for version control)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/06navdeep06/realtime-traffic-sensor.git
   cd realtime-traffic-sensor
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
   
   For development, also install:
   ```bash
   pip install -r requirements-dev.txt
   ```

### Development Setup

1. Install pre-commit hooks for code quality:
   ```bash
   pre-commit install
   ```

2. Run tests:
   ```bash
   python -m pytest tests/
   ```

3. Run the debug script to test the simulation:
   ```bash
   python debug_simulation.py
   ```

### Environment Setup

1. Copy the example environment file and update with your API key:
   ```bash
   copy .env.example .env
   ```
   
2. Edit the `.env` file and add your TomTom API key:
   ```
   TOMTOM_API_KEY=your_api_key_here
   DEBUG=False
   ```
   
   Note: Make sure to add `.env` to your `.gitignore` to keep your API key secure.

## 🏃‍♂️ Running the Application

### Web Dashboard

1. Start the Streamlit dashboard:
   ```bash
   streamlit run dashboard.py
   ```

2. Open your browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. In the sidebar:
   - Specify the city to monitor (e.g., "Patan, Nepal")
   - Adjust the number of vehicles to display (10-500)
   - Click "Start Real-time Traffic Monitoring"

### Running Simulations

1. For a quick test of the simulation:
   ```bash
   python simple_simulation_test.py
   ```

2. For detailed debugging:
   ```bash
   python debug_simulation.py
   ```
   
   This will generate a timestamped log file with detailed simulation information.

## 🛠 Project Structure

- `dashboard.py`: Streamlit web interface for the traffic simulation
- `simulation.py`: Core simulation logic and vehicle management
- `traffic_signal.py`: Traffic signal controller with Q-learning agent
- `rl_agent.py`: Implementation of the Q-learning algorithm
- `road_network.py`: Handles road network data and real-time traffic updates
- `visualization.py`: Visualization utilities for the road network and traffic
- `debug_simulation.py`: Debugging tool for the simulation engine
- `simple_simulation_test.py`: Basic test script for the simulation
- `test_*.py`: Unit tests for various components

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

- TomTom for their excellent mapping and traffic APIs
- OSMnx for powerful street network analysis
- Streamlit for the intuitive web interface
- The open-source community for invaluable tools and libraries

## 📬 Contact

For questions or feedback, please contact nepal00909@gmail.com
