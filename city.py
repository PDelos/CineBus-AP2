from dataclasses import dataclass
import osmnx as ox
import networkx as nx
from typing import TypeAlias
import buses
import os
import pickle
import matplotlib.pyplot as plt
from staticmap import StaticMap, CircleMarker, Line
from haversine import haversine, Unit
from osmnx.utils_graph import get_undirected

CityGraph : TypeAlias = nx.Graph
OsmnxGraph : TypeAlias = nx.MultiDiGraph
Coord : TypeAlias = tuple[float, float]   # (latitude, longitude)
BusesGraph : TypeAlias = nx.Graph
Path : TypeAlias = list

def get_osmnx_graph() -> OsmnxGraph:
	# Retrieve the graph from OpenStreetMap data
	#graph = ox.graph_from_place("Barcelona", network_type='walk', simplify=True)
	graph = ox.graph_from_point((41.3838, 2.1873), dist=3000, network_type='walk')
	duplicated_edges=[]
	for u, nbrsdict in graph.adjacency():
		for v, edgesdict in nbrsdict.items():
			for key in edgesdict:
				if key!=0:
					duplicated_edges.append((u,v,key))

	for u, v, key in duplicated_edges:
		graph.remove_edge(u, v, key)

	for u, v, key, data in graph.edges(data = True, keys = True):
		if "geometry" in graph[u][v][key]:
			del(graph[u][v][key]["geometry"])
		if "highway" in graph[u][v][key]:
			del(graph[u][v][key]["highway"])
		if "lanes" in graph[u][v][key]:
			del(graph[u][v][key]["lanes"])
		if "oneway" in graph[u][v][key]:
			del(graph[u][v][key]["oneway"])

	return graph


def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
	# guarda el graf g al fitxer filename
	with open(filename, "wb") as file:
		pickle.dump(g, file)

def load_osmnx_graph(filename: str) -> OsmnxGraph:
	# retorna el graf guardat al fitxer filename
	assert os.path.exists(filename)
	with open(filename, 'rb') as file:
		return pickle.load(file)

def build_city_graph(g1: OsmnxGraph, g2: BusesGraph) -> CityGraph:
	# retorna un graf fusió de g1 i g2
	city_graph = nx.Graph()
	for node, data in g1.nodes(data=True):
		city_graph.add_node(node, **data, node_type='Cruilla')

	for node, data in g2.nodes(data=True):
		pos=data['pos']
		del data['pos']
		data['x']=pos[1]
		data['y']=pos[0]
		city_graph.add_node(node, **data, node_type='Parada')

	for u, v, data in g1.edges(data=True):
		city_graph.add_edge(u,v,**data, edge_type='Carrer')


	for parada_node in g2.nodes:
		nearest_cruilla_node = ox.distance.nearest_nodes(g1, g2.nodes[parada_node]['x'], g2.nodes[parada_node]['y'])
		edge_length = haversine((g1.nodes[nearest_cruilla_node]['x'],g1.nodes[nearest_cruilla_node]['y']),
        (g2.nodes[parada_node]['x'],g2.nodes[parada_node]['y']), unit = Unit.METERS)
		city_graph.add_edge(parada_node, nearest_cruilla_node, edge_type = 'Carrer', length = edge_length)

	for parada1, parada2 in g2.edges:
		nearest_cruilla_node_1 = ox.distance.nearest_nodes(g1, g2.nodes[parada1]['x'], g2.nodes[parada1]['y'])
		nearest_cruilla_node_2 = ox.distance.nearest_nodes(g1, g2.nodes[parada2]['x'], g2.nodes[parada2]['y'])
		edge_length = nx.shortest_path_length(g1, nearest_cruilla_node_1, nearest_cruilla_node_2, weight='length')
		city_graph.add_edge(parada1, parada2, edge_type = 'Bus', length=edge_length/3)

	return city_graph

	

def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path:
	src_nearest_node = ox.distance.nearest_nodes(ox_g,src[1],src[0])
	dst_nearest_node = ox.distance.nearest_nodes(ox_g,dst[1],dst[0])
	return nx.shortest_path(g,src_nearest_node,dst_nearest_node, weight='length')

def show(g: CityGraph) -> None:
	# mostra g de forma interactiva en una finestra
	fig, ax = plt.subplots()
	pos = {node: (data['x'], data['y']) for node, data in g.nodes(data=True)}
	
	nx.draw_networkx_nodes(g, pos, ax=ax, node_size=1, node_color='lightblue')
	nx.draw_networkx_edges(g, pos, ax=ax, edge_color='gray')

	plt.show()

def plot(g: CityGraph, filename: str) -> None:
	# desa g com una imatge amb el mapa de la cuitat de fons en l'arxiu filename
	barcelona = StaticMap(800, 600)
	barcelona.center = (2.1873, 41.3838)

	# Add a marker at a specific location in Barcelona
	for node, data in g.nodes(data=True):
		barcelona.add_marker(CircleMarker((data['x'], data['y']), '#FF0000', 1))

	for u,v in g.edges:
		if u == v: continue
		if g[u][v]['edge_type']=='Carrer':
			barcelona.add_line(Line([(g.nodes[v]['x'], g.nodes[v]['y']), (g.nodes[u]['x'], g.nodes[u]['y'])], '#0000FF', 1))
		elif g[u][v]['edge_type']=='Bus':
			barcelona.add_line(Line([(g.nodes[v]['x'], g.nodes[v]['y']), (g.nodes[u]['x'], g.nodes[u]['y'])], '#00FF1A', 1))
	
	image = barcelona.render()
	image.save(filename)

def plot_path(g: CityGraph, p: Path, filename: str) -> None:
	# mostra el camí p en l'arxiu filename
	barcelona = StaticMap(800, 600)
	barcelona.center = (2.1873, 41.3838)

	# Add a marker at a specific location in Barcelona
	for node in p:
		barcelona.add_marker(CircleMarker((g.nodes[node]['x'], g.nodes[node]['y']), '#FF0000', 1))

	for u,v in zip(p,p[1:]):
		if u == v: continue
		if g[u][v]['edge_type']=='Carrer':
			barcelona.add_line(Line([(g.nodes[v]['x'], g.nodes[v]['y']), (g.nodes[u]['x'], g.nodes[u]['y'])], '#0000FF', 1))
		elif g[u][v]['edge_type']=='Bus':
			barcelona.add_line(Line([(g.nodes[v]['x'], g.nodes[v]['y']), (g.nodes[u]['x'], g.nodes[u]['y'])], '#00FF1A', 1))
	
	image = barcelona.render()
	image.save(filename)


#save_osmnx_graph(get_osmnx_graph(),'bcn_graph.pickle')
#print("saved")
graph=build_city_graph(load_osmnx_graph('bcn_graph.pickle'),buses.get_buses_graph())
#graph=load_osmnx_graph("city.pickle")
#save_osmnx_graph(graph,'city.pickle')
print("graph builded")
#show(graph)
#show(graph)
#plot(graph,"map.png")
plot_path(graph,find_path(load_osmnx_graph('bcn_graph.pickle'),graph,(41.401727281643055, 2.151696185862085),(41.38962588196832, 2.167422817271395)),"short_path.png")