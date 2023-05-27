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

Coord : TypeAlias = tuple[float, float]   # (latitude, longitude)
Path : TypeAlias = list

def get_osmnx_graph() -> OsmnxGraph:
	#delete duplicated edges by converting it to DiGraph
	bcn: OsmnxGraph = nx.DiGraph(ox.graph_from_place("Barcelona", network_type="walk", simplify=True))

	#filter the edge and node information
	node_attributes = ['x', 'y'] #lat = y, lon = x
	edge_attributes = ['length'] #u=start, v=end
	for node_id, node_data in bcn.nodes(data=True):
		for attr in list(node_data):
			if attr  not in node_attributes:
				del(bcn.nodes[node_id][attr])
		bcn.nodes[node_id].update({'color' : '#000000'})

	for u, v, edge_data in bcn.edges(data = True):
		for attr in list(edge_data):
			if attr  not in edge_attributes:
				del(bcn[u][v][attr])
		u_pos: Coord = (bcn.nodes[u]['x'], bcn.nodes[u]['y'])
		v_pos: Coord = (bcn.nodes[v]['x'], bcn.nodes[v]['y'])
		bcn[u][v].update({'color' : '#000000', 'route': [u_pos, v_pos]})

	return bcn

def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
	# guarda el graf g al fitxer filename
	with open(filename, "wb") as file:
		pickle.dump(g, file)

def load_osmnx_graph(filename: str) -> OsmnxGraph:
	# retorna el graf guardat al fitxer filename
	assert os.path.exists(filename)
	with open(filename, 'rb') as file:
		return pickle.load(file)

def build_city_graph(bcn: OsmnxGraph, bus: BusesGraph) -> CityGraph:
	# retorna un graf fusió de g1 i g2
	#bcn: OsmnxGraph = get_osmnx_graph()
	#bus: BusesGraph = buses.get_buses_graph()

	city_graph: nx.DiGraph = nx.compose(bcn, bus)

	lon_stops: list[float] = [bus.nodes[id]['x'] for id in bus.nodes]
	lat_stops: list[float] = [bus.nodes[id]['y'] for id in bus.nodes]
	nearest_cruilla: list[int] = ox.distance.nearest_nodes(bcn, lon_stops, lat_stops, return_dist=False)
	for stop_id, cruilla_id in zip(bus.nodes, nearest_cruilla):
		stop_pos: Coord = (bus.nodes[stop_id]['x'], bus.nodes[stop_id]['y'])
		cruilla_pos: Coord = (bcn.nodes[cruilla_id]['x'], bcn.nodes[cruilla_id]['y'])
		edge_length = buses.dist(stop_pos, cruilla_pos)
		#recordem que es directed
		city_graph.add_edge(cruilla_id, stop_id, route = [cruilla_pos, stop_pos], length = edge_length, color='#808080')
		city_graph.add_edge(stop_id, cruilla_id, route = [stop_pos, cruilla_pos], length = edge_length, color='#808080')
	return city_graph
	

def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path:
	src_nearest_node = ox.distance.nearest_nodes(ox_g,src[1],src[0])
	dst_nearest_node = ox.distance.nearest_nodes(ox_g,dst[1],dst[0])
	return nx.shortest_path(g,src_nearest_node,dst_nearest_node, weight='length')

def show(g: CityGraph) -> None:
	# mostra g de forma interactiva en una finestra
	fig, ax = plt.subplots()
	pos: dict[Any, float] = {node: (data['x'], data['y']) for node, data in g.nodes(data=True)}
	nx.draw(g, pos, ax=ax, with_labels=False, node_color='lightblue', edge_color='gray', node_size = 1)
	plt.show()

def plot(g: CityGraph, filename: str) -> None:
	# Create a new map object
	barcelona = stm.StaticMap(800, 600)
	barcelona.center = (2.1734, 41.3851) #staticmap uses 

	for id, data in g.nodes(data=True):
		pos: Coord = (data['x'], data['y'])
		marker = stm.CircleMarker(pos, data['color'], 2)
		barcelona.add_marker(marker)
    
	for u, v, data in g.edges(data=True):
		line = stm.Line(data['route'], data['color'], 1)
		barcelona.add_line(line)
    
	image = barcelona.render()
	image.save(filename)
	image = Image.open(filename)
	image.show()

def plot_path(g: CityGraph, p: Path, filename: str) -> None:
	# mostra el camí p en l'arxiu filename
	barcelona = stm.StaticMap(800, 600)
	barcelona.center = (2.1873, 41.3838)

	# Add a marker at a specific location in Barcelona
	for id in p:
		pos: Coord = (g.nodes[id]['x'], g.nodes[id]['y'])
		marker = stm.CircleMarker(pos, g.nodes[id]['color'], 3)
		barcelona.add_marker(marker)

	for u,v in zip(p,p[1:]):
		line = stm.Line(g[u][v]['route'], g[u][v]['color'], 2)
		barcelona.add_line(line)
	
	image = barcelona.render()
	image.save(filename)

ox_g=load_osmnx_graph('bcn_graph.pickle')
city = build_city_graph(ox_g, buses.get_buses_graph())

p: Path = find_path(ox_g,city,(41.401727281643055, 2.151696185862085),(41.38962588196832, 2.167422817271395))
plot_path(city, p, "short_path.png")