import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from typing import Dict, Tuple, List, Optional

# Custom colormap for traffic congestion (green to red)
traffic_cmap = LinearSegmentedColormap.from_list('traffic', ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c'])

def get_traffic_color(congestion: float) -> str:
    """
    Returns a color based on congestion level.
    
    Args:
        congestion: Value between 0 (no congestion) and 1 (max congestion)
        
    Returns:
        Hex color code representing the congestion level
    """
    # Convert congestion to a value between 0 and 1 for the colormap
    value = min(max(congestion, 0), 1)
    return traffic_cmap(value)

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

def plot_traffic_graph(G: nx.MultiDiGraph, figsize: tuple = (12, 10), 
                      node_alpha: float = 0.7, edge_alpha: float = 0.9) -> plt.Figure:
    """
    Plots the road network with enhanced traffic visualization.
    
    Args:
        G: The road network graph with traffic data
        figsize: Size of the figure (width, height) in inches
        node_alpha: Opacity of the nodes (0-1)
        edge_alpha: Opacity of the edges (0-1)
        
    Returns:
        matplotlib Figure object with the traffic visualization
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize, facecolor='#f0f0f0')
    
    # Get node positions
    pos = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}
    
    # Draw edges with traffic-based coloring
    edge_colors = []
    edge_widths = []
    edge_alphas = []
    
    for u, v, key, data in G.edges(keys=True, data=True):
        # Get congestion level (default to 0 if not available)
        congestion = data.get('congestion', 0)
        
        # Skip edges without geometry
        if 'geometry' not in data:
            continue
            
        # Calculate edge properties based on congestion
        edge_colors.append(get_traffic_color(congestion))
        edge_widths.append(1.5 + congestion * 2)  # Wider lines for more congestion
        edge_alphas.append(edge_alpha)
        
        # Draw the edge
        x, y = data['geometry'].xy
        ax.plot(x, y, 
                color=get_traffic_color(congestion),
                linewidth=1.5 + congestion * 2,
                alpha=edge_alpha,
                solid_capstyle='round')
    
    # Draw nodes (intersections)
    node_sizes = [15 + 10 * G.degree(node) for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, 
                          node_size=node_sizes, 
                          node_color='#3498db',
                          alpha=node_alpha,
                          edgecolors='black',
                          linewidths=0.5,
                          ax=ax)
    
    # Add a colorbar legend
    sm = plt.cm.ScalarMappable(cmap=traffic_cmap, 
                             norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation='vertical', 
                       fraction=0.02, pad=0.04)
    cbar.set_label('Traffic Congestion Level', fontsize=10)
    cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
    cbar.set_ticklabels(['Free', 'Light', 'Moderate', 'Heavy', 'Severe'])
    
    # Add grid and title
    ax.grid(True, color='white', linestyle='-', alpha=0.3)
    ax.set_facecolor('#f8f9fa')
    ax.set_title('Real-Time Traffic Conditions', 
                fontsize=14, pad=20, fontweight='bold')
    
    # Remove axis ticks and labels
    ax.tick_params(axis='both', which='both', length=0)
    plt.xticks([])
    plt.yticks([])
    
    # Add a subtle border
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color('#dddddd')
    
    plt.tight_layout()
    return fig
