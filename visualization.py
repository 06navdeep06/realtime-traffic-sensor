import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Tuple

def plot_congestion_heatmap(graph: nx.MultiDiGraph, edge_congestion: Dict[Tuple[int, int], int], step: int) -> plt.Figure:
    """
    Plots the road network with edges colored by congestion and returns the figure.

    Args:
        graph: The road network graph.
        edge_congestion: A dictionary mapping edges to vehicle counts.
        step: The current simulation step, for the plot title.

    Returns:
        The matplotlib Figure object.
    """
    # Determine the color for each edge based on congestion
    edge_colors = []
    for u, v, _ in graph.edges():
        congestion = edge_congestion.get((u, v), 0)
        if congestion == 0:
            color = 'limegreen' # Free-flowing
        elif congestion <= 2:
            color = 'gold' # Light traffic
        elif congestion <= 5:
            color = 'orange' # Moderate traffic
        else:
            color = 'red' # Heavy traffic
        edge_colors.append(color)

    # Plot the graph with the new edge colors
    fig, ax = ox.plot_graph(
        graph,
        show=False,
        close=True,
        node_size=0,
        edge_linewidth=0.8,
        edge_color=edge_colors,
        bgcolor='#FFFFFF'
    )

    ax.set_title(f'Traffic Congestion - Step {step}')
    return fig

def plot_traffic_graph(G) -> plt.Figure:
    """Plots the road network with edges colored by congestion level and returns the figure."""
    edge_colors = []
    for u, v, key, data in G.edges(keys=True, data=True):
        if "congestion" in data:
            congestion = data.get("congestion", 0)
            if congestion < 0.6:
                edge_colors.append("green")
            elif congestion < 0.9:
                edge_colors.append("orange")
            else:
                edge_colors.append("red")
        else:
            edge_colors.append("gray")
    
    fig, ax = ox.plot_graph(
        G, 
        show=False, 
        close=True, 
        node_size=0, 
        edge_linewidth=1.5, 
        edge_color=edge_colors
    )
    ax.set_title("Real-Time Traffic Congestion")
    return fig
