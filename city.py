from dataclasses import dataclass
from bs4 import BeautifulSoup
import requests
import json
import osmnx as ox
import networkx
from typing import TypeAlias

CityGraph : TypeAlias = networkx.Graph
OsmnxGraph : TypeAlias = networkx.MultiDiGraph
Coord : TypeAlias = tuple[float, float]   # (latitude, longitude)

def get_osmnx_graph() -> OsmnxGraph:
	# Define the latitude and longitude coordinates
	latitude = 41.3838
	longitude = 2.1873

	# Retrieve the graph from OpenStreetMap data
	return ox.graph_from_address((latitude, longitude), network_type='all', dist=1000)


def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
	# guarda el graf g al fitxer filename
	ox.save_graphml(g, filename)

def load_osmnx_graph(filename: str) -> OsmnxGraph:
	# retorna el graf guardat al fitxer filename
	return ox.load_graphml(filename)

'''def build_city_graph(g1: OsmnxGraph, g2: BusesGraph) -> CityGraph:
	# retorna un graf fusió de g1 i g2

def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path:

def show(g: CityGraph) -> None:
	# mostra g de forma interactiva en una finestra

def plot(g: CityGraph, filename: str) -> None:
	# desa g com una imatge amb el mapa de la cuitat de fons en l'arxiu filename

def plot_path(g: CityGraph, p: Path, filename: str) -> None:
	# mostra el camí p en l'arxiu filename
'''

save_osmnx_graph(get_osmnx_graph(),'bcn_graph')
graph=load_osmnx_graph('bcn_graph')