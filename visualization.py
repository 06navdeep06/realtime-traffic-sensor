import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import logging
from matplotlib.colors import LinearSegmentedColormap
from typing import Dict, Tuple, List, Optional

logger = logging.getLogger(__name__)

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
    # Validate input
    if not isinstance(congestion, (int, float)):
        logger.warning(f"Invalid congestion value type: {type(congestion)}")
        congestion = 0.0
    
    # Convert congestion to a value between 0 and 1 for the colormap
    value = min(max(congestion, 0), 1)
    
    try:
        color = traffic_cmap(value)
        # Convert to hex if it's an RGBA tuple
        if isinstance(color, tuple) and len(color) >= 3:
            return f"#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}"
        return color
    except Exception as e:
        logger.warning(f"Error getting traffic color for value {value}: {e}")
        return "#808080"  # Default gray color

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
    if not isinstance(graph, (nx.MultiDiGraph, nx.DiGraph)):
        logger.error(f"Invalid graph type: {type(graph)}")
        return plt.figure()
        
    if not isinstance(edge_congestion, dict):
        logger.warning(f"Invalid edge_congestion type: {type(edge_congestion)}")
        edge_congestion = {}
        
    try:
        # Determine the color for each edge based on congestion
        edge_colors = []
        for u, v, _ in graph.edges():
            congestion = edge_congestion.get((u, v), 0)
            
            # Ensure congestion is a valid number
            if not isinstance(congestion, (int, float)):
                congestion = 0
            
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
        
    except Exception as e:
        logger.error(f"Error plotting congestion heatmap: {e}")
        # Return empty figure on error
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, f'Error plotting graph: {str(e)}', 
                ha='center', va='center', transform=ax.transAxes)
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
    if not isinstance(G, (nx.MultiDiGraph, nx.DiGraph)):
        logger.error(f"Invalid graph type: {type(G)}")
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, 'Invalid graph provided', ha='center', va='center')
        return fig
        
    # Validate parameters
    if not isinstance(figsize, tuple) or len(figsize) != 2:
        logger.warning(f"Invalid figsize: {figsize}, using default")
        figsize = (12, 10)
        
    node_alpha = max(0, min(1, float(node_alpha))) if isinstance(node_alpha, (int, float)) else 0.7
    edge_alpha = max(0, min(1, float(edge_alpha))) if isinstance(edge_alpha, (int, float)) else 0.9
    
    try:
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize, facecolor='#f0f0f0')
        
        # Check if graph has nodes
        if G.number_of_nodes() == 0:
            ax.text(0.5, 0.5, 'Empty graph - no nodes to display', 
                   ha='center', va='center', transform=ax.transAxes)
            return fig
        
        # Get node positions
        pos = {}
        for node, data in G.nodes(data=True):
            if isinstance(data, dict) and 'x' in data and 'y' in data:
                try:
                    pos[node] = (float(data['x']), float(data['y']))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid coordinates for node {node}: {data}")
        
        if not pos:
            ax.text(0.5, 0.5, 'No valid node coordinates found', 
                   ha='center', va='center', transform=ax.transAxes)
            return fig
        
        # Draw edges with traffic-based coloring
        edges_drawn = 0
        for u, v, key, data in G.edges(keys=True, data=True):
            if not isinstance(data, dict):
                continue
                
            # Get congestion level (default to 0 if not available)
            congestion = data.get('congestion', 0)
            if not isinstance(congestion, (int, float)):
                congestion = 0
            congestion = max(0, min(1, congestion))  # Clamp to [0, 1]
            
            # Skip edges without geometry and valid positions
            if u not in pos or v not in pos:
                continue
                
            try:
                if "geometry" in data and data["geometry"] is not None:
                    # Draw the edge using geometry
                    x, y = data['geometry'].xy
                    ax.plot(x, y, 
                            color=get_traffic_color(congestion),
                            linewidth=1.5 + congestion * 2,
                            alpha=edge_alpha,
                            solid_capstyle='round')
                else:
                    # Draw straight line between nodes
                    x_coords = [pos[u][0], pos[v][0]]
                    y_coords = [pos[u][1], pos[v][1]]
                    ax.plot(x_coords, y_coords,
                            color=get_traffic_color(congestion),
                            linewidth=1.5 + congestion * 2,
                            alpha=edge_alpha,
                            solid_capstyle='round')
                edges_drawn += 1
            except Exception as e:
                logger.warning(f"Error drawing edge {u}->{v}: {e}")
                continue
        
        if edges_drawn == 0:
            logger.warning("No edges were drawn")
        
        # Draw nodes (intersections)
        try:
            node_sizes = []
            for node in G.nodes():
                degree = G.degree(node) if hasattr(G, 'degree') else 1
                node_sizes.append(15 + 10 * min(degree, 5))  # Cap the size
            
            nx.draw_networkx_nodes(G, pos, 
                                  node_size=node_sizes, 
                                  node_color='#3498db',
                                  alpha=node_alpha,
                                  edgecolors='black',
                                  linewidths=0.5,
                                  ax=ax)
        except Exception as e:
            logger.warning(f"Error drawing nodes: {e}")
        
        # Add a colorbar legend
        try:
            sm = plt.cm.ScalarMappable(cmap=traffic_cmap, 
                                     norm=plt.Normalize(vmin=0, vmax=1))
            sm.set_array([])
            cbar = plt.colorbar(sm, ax=ax, orientation='vertical', 
                               fraction=0.02, pad=0.04)
            cbar.set_label('Traffic Congestion Level', fontsize=10)
            cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
            cbar.set_ticklabels(['Free', 'Light', 'Moderate', 'Heavy', 'Severe'])
        except Exception as e:
            logger.warning(f"Error adding colorbar: {e}")
        
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
        
    except Exception as e:
        logger.error(f"Error in plot_traffic_graph: {e}")
        # Return error figure
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, f'Error creating traffic visualization:\n{str(e)}', 
                ha='center', va='center', transform=ax.transAxes)
        return fig
