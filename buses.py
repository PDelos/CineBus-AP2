from dataclasses import dataclass
from typing import TypeAlias
from haversine import haversine
from PIL import Image
import staticmap as stm
import networkx as nx
import json
import matplotlib.pyplot as plt


BusesGraph : TypeAlias = nx.DiGraph
Coord : TypeAlias = tuple[float, float]   # (longitud, latitud)

@dataclass
class Stop: 
    code: str
    name: str
    address: str
    pos: Coord
    dist_prev: float


class BusLine:
    _id: int #id del recorregut (no nomes linea)
    _name: str #nom de la linea amb parada inicial i final
    _color: str
    _busStops: list[Stop]
    _busRoute: list[Coord]

    def __init__(self, Id: int, Nom: str, Color: str) -> None:
        self._id = Id
        self._name = Nom
        self._color = Color

        self._busStops = list()
        self._busRoute = list()

    
    def setStops(self, stops: list[Stop]) -> None:
        self._busStops = stops

    def setRoute(self, route: list[Coord]) -> None:
        self._busRoute = route

    def id(self) -> int:
        return self._id
    
    def name(self) -> str:
        return self._name
    
    def color(self) -> str:
        return self._color
    
    def stops(self) -> list[Stop]:
        return self._busStops
    
    def route(self) -> list[Coord]:
        return self._busRoute
        


class NetworkBus:
    _busLines: dict[int, BusLine] #id de lina + sentit

    def __init__(self) -> None:
        self._busLines = dict()

    def busLines(self) -> dict[int, BusLine]:
        return self._busLines

    def addBusLine(self, line: BusLine) -> None:
        assert line.id() not in self._busLines, line.id()
        self.busLines()[line.id()] = line
    
    def getBusLine(self, id_route: int) -> dict[int, BusLine]:
        assert id_route in self.busLines(), id_route 
        return self.busLines()[id_route]



def dist(x: Coord, y: Coord) -> float:  #lon, lat
    return haversine((x[1], x[0]), (y[1], y[0]), unit='m')  #lat, lon


def create_network_base() -> NetworkBus:
    #fem servir el fitxer de les rutes per establir totes les que hi hauran
    with open("busRoutes.json", "r") as file:
        json_data = file.read()
    TMBdata = json.loads(json_data)
    BcnNetwork = NetworkBus()
    for route in TMBdata['features']: #iterating over stops in json file
        #get id and list ofcoords
        id: str = route['properties']['ID_RECORREGUT']
        name: str = route['properties']['NOM_LINIA'] + ' - ' + route['properties']['DESC_PAQUET']+' ('+route['properties']['DESC_SENTIT']+")"
        color: str = route['properties']['COLOR_REC']
        NewLine = BusLine(id, name, color)
        BcnNetwork.addBusLine(NewLine)
    return BcnNetwork


def get_route_json(json_file: str, BcnNetwork: NetworkBus) -> NetworkBus:
    with open(json_file, "r") as file:
        json_data = file.read()
    TMBdata = json.loads(json_data)

    for route in TMBdata['features']: #iterating over stops in json file
        #get id and list ofcoords
        route_id: str = route['properties']['ID_RECORREGUT']
        route_coords: list[Coord] =  [tuple(lst) for lst in route['geometry']['coordinates'][0]] # per declarar be el tipus
        #add the list of coords to the coorrespoinding line
        BcnNetwork.getBusLine(route_id).setRoute(route_coords)
        
    return BcnNetwork


def get_stops_json(json_file: str, BcnNetwork: NetworkBus) -> NetworkBus:
    #find all stops related to routes_id
    with open(json_file, "r") as file:
        json_data = file.read()
    TMBdata = json.loads(json_data)

    BusStops: dict[int, list[Stop]] = dict()
    for stop in TMBdata['features']:
        id: int = stop['properties']['ID_RECORREGUT']
        if id not in BusStops: BusStops[id] = list()

        #all info we whant to get from stop
        code: str = str(stop['properties']['CODI_PARADA'])
        name: str = stop['properties']['NOM_PARADA']
        address: str = stop['properties']['ADRECA']
        pos: Coord = tuple(stop['geometry']['coordinates'])
        dist_prev: float = stop['properties']['DISTANCIA_PAR_ANTERIOR']

        BusStops[id].append(Stop(code+"-"+str(id), name, address, pos, dist_prev)) #bus stops are all organized by order

    for id, stop_list in BusStops.items():
        BcnNetwork.getBusLine(id).setStops(stop_list) # set the stop of the bus lines
    
    return BcnNetwork


def create_Bus_Network() -> NetworkBus:
    network = create_network_base()
    network = get_route_json("busRoutes.json",network)
    network = get_stops_json("busStops.json",network)
    return network


def route_between_stops(idx: int, target_dist: float, route: list[Coord]) -> tuple[int, list[Coord]]:
    # let us see if route[idx] is actually between the 2 stops
    if target_dist <= 0: 
        #this means that the dist to node in front of src is bigger than the dist betwen the stops
        #so there are no in between points and route[idx] is in front of dst
        return idx, list()
    
    distance: float = 0
    route_between: list[Coord] = [route[idx]]
    while idx < len(route)-1 and distance+dist(route[idx], route[idx+1]) <= target_dist:
        distance += dist(route[idx], route[idx+1])  #using harversines
        route_between.append(route[idx+1])
        idx+=1
    #we whant to return the index to the node in front of dst 
    #aka the first one we did not add, so idx+1
    return idx+1, route_between 
    
def get_buses_from_network(BcnNetwork: NetworkBus) -> BusesGraph:
    BcnBusGraph = BusesGraph()
    for busline in BcnNetwork.busLines().values():
        #Add nodes to the graph
        for s in busline.stops():#easier to work with
            BcnBusGraph.add_node(
                s.code, 
                name = s.name, 
                address=s.address, 
                x=s.pos[0], y=s.pos[1],  #lon lat
                node_type='Parada', 
                color="#"+busline.color()
            ) 
                
        #Add edges to the graph
        index = 0
        for src, dst in zip(busline.stops(), busline.stops()[1:]):
            #let us consider that the src is allways "behind" adn dst is "infront" of the point route[index]
            trgt_dist: float = dst.dist_prev- dist(src.pos, busline.route()[index]) 
            index, route_between = route_between_stops(index, trgt_dist, busline.route())
            BcnBusGraph.add_edge(
                src.code, dst.code,
                edge_type = 'Bus', 
                route=[src.pos]+route_between+[dst.pos], 
                length=dst.dist_prev, 
                color="#"+busline.color()
            )
    return BcnBusGraph


def get_buses_graph() -> BusesGraph:
    BCNbusNetwork = create_Bus_Network()
    return get_buses_from_network(BCNbusNetwork)


def show(g: BusesGraph) -> None:
    pos: dict[str, float] = {node: (data['x'], data['y']) for node, data in g.nodes(data=True)}
    nx.draw(g, pos, with_labels=False, node_color='lightblue', edge_color='gray', node_size = 1)
    plt.show()

def plot(g: BusesGraph, nom_fitxer: str) -> None:
    # Create a new map object
    barcelona = stm.StaticMap(800, 600)
    barcelona.center = (2.1734, 41.3851) #staticmap uses 
    
    for id, data in g.nodes(data=True):
        pos: Coord = (data['x'], data['y'])
        marker = stm.CircleMarker(pos, data['color'], 2)
        barcelona.add_marker(marker)
        
    for u, v, data in g.edges(data=True):
        route = stm.Line(data['route'], data['color'], 1)
        barcelona.add_line(route)
    
    image = barcelona.render()
    image.save(nom_fitxer+'.png')
    image = Image.open(nom_fitxer+'.png')
    image.show()


def plot_BusLine(g: BusesGraph, id_line: str, nom_fitxer: str) -> None:
    # Create a new map object
    barcelona = stm.StaticMap(800, 600)
    barcelona.center = (2.1734, 41.3851) #staticmap uses 
    
    for id, data in g.nodes(data=True):
        if id.split("-")[1] != id_line: continue
        pos: Coord = (data['x'], data['y'])
        marker = stm.CircleMarker(pos, data['color'], 5)
        barcelona.add_marker(marker)
        
    for u, v, data in g.edges(data=True):
        if u.split("-")[1] != id_line or v.split("-")[1] != id_line: continue
        route = stm.Line(data['route'], data['color'], 2)
        barcelona.add_line(route)
    
    image = barcelona.render()
    image.save(nom_fitxer+'.png')
    image = Image.open(nom_fitxer+'.png')
    image.show()
