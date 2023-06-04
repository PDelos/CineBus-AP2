from dataclasses import dataclass
from PIL import Image
from typing import TypeAlias, Any
import osmnx as ox
import networkx as nx
import buses
import os
import pickle
import matplotlib.pyplot as plt
import staticmap as stm


CityGraph : TypeAlias = nx.DiGraph
OsmnxGraph : TypeAlias = nx.DiGraph
BusesGraph : TypeAlias = nx.DiGraph

Coord : TypeAlias = tuple[float, float]   # (longitude, latitude)
Path : TypeAlias = list


def get_osmnx_graph() -> OsmnxGraph:
	""" Returns procesed Barcelona graph """
	# Delete duplicated edges by converting it to DiGraph
	# Same functionality than deleting all edges with key != 0
	GraphBcn: OsmnxGraph = OsmnxGraph(ox.graph_from_place("Barcelona", network_type="walk", simplify=True))

	# Filter the edge and node information
	node_attributes = ['x', 'y'] # Information in nodes we whant to keep (x=longitud, y=latitut)
	edge_attributes = ['length'] # information in edges we whant to keep ()

	# Iterating through nodes
	for node_id, node_data in GraphBcn.nodes(data=True):
		# If not in node_attributes we want to delete the atribute
		for attr in list(node_data):
			if attr  not in node_attributes:
				del(GraphBcn.nodes[node_id][attr])

		# New information we whant to add to node
		GraphBcn.nodes[node_id].update({'poblacio': 'Barcelona', 'color' : '#000000'})

	# Iterating through edges
	for u, v, edge_data in list(GraphBcn.edges(data = True)):
		if u == v: 
			GraphBcn.remove_edge(u,v)
			continue

		# If not in edge_attributes we want to delete the atribute
		for attr in list(edge_data):
			if attr  not in edge_attributes:
				del(GraphBcn[u][v][attr])
		GraphBcn[u][v]['length'] /= 1.11 #length is now like time assuming we walk at 4km/h
		# New information we whant to add to edge
		u_pos: Coord = (GraphBcn.nodes[u]['x'], GraphBcn.nodes[u]['y'])
		v_pos: Coord = (GraphBcn.nodes[v]['x'], GraphBcn.nodes[v]['y'])
		GraphBcn[u][v].update({'color' : '#000000', 'route': [u_pos, v_pos]})

	return GraphBcn


def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
	""" Saves the graph at: filename """
	with open(filename, "wb") as file:
		pickle.dump(g, file)

def load_osmnx_graph(filename: str) -> OsmnxGraph:
	""" Loads the graph from: filename """
	assert os.path.exists(filename)
	with open(filename, 'rb') as file:
		return pickle.load(file)

def build_city_graph(bcn: OsmnxGraph, bus: BusesGraph) -> CityGraph:
	""" Returns the graph of the city (merge of the street graph and the bus graph)"""
	city_graph: nx.DiGraph = nx.compose(bcn, bus) # We use compose to merge both graphs

	# We get the list of nearest nodes from each node of the bus to the bcn graph using ox.distance.nearest_nodes
	lon_stops: list[float] = [bus.nodes[id]['x'] for id in bus.nodes]
	lat_stops: list[float] = [bus.nodes[id]['y'] for id in bus.nodes]
	nearest_cruilla: list[int] = ox.distance.nearest_nodes(bcn, lon_stops, lat_stops, return_dist=False)

	# Create the edge between the stop and its nearest node in bcn graph
	for stop_id, cruilla_id in zip(bus.nodes, nearest_cruilla):
		stop_pos: Coord = (bus.nodes[stop_id]['x'], bus.nodes[stop_id]['y'])
		cruilla_pos: Coord = (bcn.nodes[cruilla_id]['x'], bcn.nodes[cruilla_id]['y'])
		edge_length = buses.dist(stop_pos, cruilla_pos) #harversine
		
		#Since it is directed we want to add both directions
		city_graph.add_edge(cruilla_id, stop_id, route = [cruilla_pos, stop_pos], length = edge_length/1.11+3*60, color='#000000') #suposem 3 min de espera
		city_graph.add_edge(stop_id, cruilla_id, route = [stop_pos, cruilla_pos], length = edge_length/1.11, color='#000000') #suposem 3 min de espera
	
	return city_graph
	

def find_path(g: CityGraph, src: Coord, dst: Coord) -> Path:
	""" Given a graph, and 2 points descrived by coordinates, returns the shortest using the graph. Coords: lon, lat """
	src_nearest_node = ox.distance.nearest_nodes(g,src[0],src[1]) #find the nearest node from src
	dst_nearest_node = ox.distance.nearest_nodes(g,dst[0],dst[1]) #find the nearest node from dst
	return nx.shortest_path(g,src_nearest_node,dst_nearest_node, weight='length')

def show(g: CityGraph) -> None:
	""" Shows the directed graph using networkx.draw """
	# We extrat the position of each node and create a dictionary
	pos: dict[Any, Coord] = {node: (data['x'], data['y']) for node, data in g.nodes(data=True)}
	# Using the dictionary representing position we plot the graph
	nx.draw(g, pos, with_labels=False, node_color='lightblue', edge_color='gray', node_size = 1)
	plt.show()

def plot(g: CityGraph, filename: str) -> None:
	""" Saves and shows the graph as an image with the background city map in the specified file: filename, using staticmaps library """
	# Create a new map object
	barcelona = stm.StaticMap(3500, 3500)
	# Draws all the nodes in the graph using 'x', 'y' information in edge
	for id, data in g.nodes(data=True):
		if data['poblacio'] == 'Barcelona':
			pos: Coord = (data['x'], data['y'])
			marker = stm.CircleMarker(pos, data['color'], 2)
			barcelona.add_marker(marker)
    
	# Draws all the edges using route information in edge
	for u, v, data in g.edges(data=True):
		if g.nodes[u]['poblacio'] == 'Barcelona' and g.nodes[v]['poblacio'] == 'Barcelona':
			line = stm.Line(data['route'], data['color'], 1)
			barcelona.add_line(line)
    
	# Save image
	image = barcelona.render()
	image.save(filename)
	# Show image
	image = Image.open(filename)
	image.show()

def plot_path(g: CityGraph, p: Path, filename: str) -> None:
	""" Saves and shows a path of nodes as an image with the background city map in the specified file: filename, using staticmaps library """
    # Create a new map object
	barcelona = stm.StaticMap(3500, 3500)
	# Add the nodes form the path with the indecated attributes
	pos_start: Coord = (g.nodes[p[0]]['x'], g.nodes[p[0]]['y'])
	start_marker = stm.CircleMarker(pos_start, g.nodes[p[0]]['color'], 7)
	barcelona.add_marker(start_marker)
	pos_end: Coord = (g.nodes[p[-1]]['x'], g.nodes[p[-1]]['y'])
	end_marker = stm.CircleMarker(pos_end, g.nodes[p[-1]]['color'], 7)
	barcelona.add_marker(end_marker)

	# Add the lines connecting the nodes using the information in the edge u->v
	for u,v in zip(p,p[1:]):
		line = stm.Line(g[u][v]['route'], g[u][v]['color'], 4)
		barcelona.add_line(line)
  
	# Add the nodes form the path with the indecated attributes
	for id in p:
		pos: Coord = (g.nodes[id]['x'], g.nodes[id]['y'])
		marker = stm.CircleMarker(pos, g.nodes[id]['color'], 4)
		outline = stm.CircleMarker(pos, 'black', 7)
		barcelona.add_marker(outline)
		barcelona.add_marker(marker)
	
	# Save image
	image = barcelona.render()
	image.save(filename)
	# Show image
	image = Image.open(filename)
	image.show()