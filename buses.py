from requests import get
from dataclasses import dataclass
from typing import TypeAlias
import networkx as nx
import matplotlib.pyplot as plt
from staticmap import StaticMap, CircleMarker, Line
import math


BusesGraph : TypeAlias = nx.Graph
Coord : TypeAlias = tuple[float, float]   # (latitude, longitude)

@dataclass
class Stop: 
    name: str
    address: str
    pos: Coord


class BusLine:
    _id: int
    _name: str
    _busStops: list[Stop]

    def __init__(self, Id: int, Nom: str) -> None:
        self._id = Id
        self._name = Nom
        self._busStops = list()

    def addStop(self, s: Stop) -> None:
        self._busStops.append(s)

    def id(self) -> int:
        return self._id
    
    def name(self) -> str:
        return self._name
    
    def stops(self) -> list[Stop]:
        return self._busStops


class NetworkBus:
    _busLines: list[BusLine]

    def __init__(self) -> None:
        self._busLines = list()

    def addLine(self, line: BusLine) -> None:
        self._busLines.append(line)
    
    def busLines(self) -> list[BusLine]:
        return self._busLines


def get_buses_graph() -> BusesGraph:

    url = 'https://www.ambmobilitat.cat/OpenData/ObtenirDadesAMB.json'
    AMBdata =  get(url).json()

    #PROCESS JSON FILE
    network = NetworkBus()
    for line in AMBdata['ObtenirDadesAMBResult']['Linies']['Linia']:
        lineBus = BusLine(line['Id'], line['Nom'])
        for stop in line['Parades']['Parada']:
            lineBus.addStop(Stop(stop['Nom'], stop['Adreca'], (float(stop['UTM_X']), float(stop['UTM_Y']))))
        network.addLine(lineBus)

    # Create an empty graph
    graph = BusesGraph()

    for i, line in zip(range(70), network.busLines()):
        #Add nodes to the graph
        for s in line.stops():
            graph.add_node(s.name, address=s.address, pos=s.pos)
        
        #Add edges to the graph
        for src, dst in zip(line.stops(), line.stops()[1:]):
            if src.name == dst.name: continue
            graph.add_edge(src.name, dst.name)

    return graph

def show(graph: BusesGraph) -> None:
    pos = nx.get_node_attributes(graph, 'pos')
    fig, ax = plt.subplots()
    
    nx.draw(graph, pos, with_labels=False, node_color='lightblue', edge_color='gray', node_size = 1)
    plt.show()


def generate_map_with_graph(network: NetworkBus) -> None:
    # Create a new map object
    barcelona = StaticMap(800, 600)
    barcelona.center = (2.1734, 41.3851)

    # Add a marker at a specific location in Barcelona
    for i, line in zip(range(1), network.busLines()):
        for s in line.stops():
            barcelona.add_marker(CircleMarker((s.pos[1], s.pos[0]), '#FF0000', 1))

        for src, dst in zip(line.stops(), line.stops()[1:]):
            if src.name == dst.name: continue
            # Add a line to represent the graph
            barcelona.add_line(Line([(src.pos[1], src.pos[0]), (dst.pos[1], dst.pos[0])], '#0000FF', 1))
    
    image = barcelona.render()
    image.save("barcelona_map.png")
