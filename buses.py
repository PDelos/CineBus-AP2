from dataclasses import dataclass
from typing import TypeAlias
from haversine import haversine
from PIL import Image
import staticmap as stm
import networkx as nx
import json
import matplotlib.pyplot as plt


BusesGraph : TypeAlias = nx.DiGraph
Coord : TypeAlias = tuple[float, float] # (longitud, latitud)

@dataclass
class Stop: 
    """ Dataclass representing a bus stop"""
    code: str # id used to identify the bus stop, unique to each route 
    name: str 
    address: str 
    pos: Coord # Coordinates in (longitud, latitud)
    dist_prev: float # distance between current stop and the previous on the same line


class BusLine:
    """ Class representing a bus line for each direction (circle lines are divided) """
    _id: int # id of the bus line (diferent for each direction)
    _name: str # name of
    _color: str # color of the bus line
    _busStops: list[Stop] # list containing all the bus stops in order
    _busRoute: list[Coord] # path de busline takes

    def __init__(self, Id: int, Nom: str, Color: str) -> None:
        """ constructor for the BusLine class. Sets the stops and route as empty lists """
        self._id = Id
        self._name = Nom
        self._color = Color

        self._busStops = list()
        self._busRoute = list()

    ######################## GETTERS ################################
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
    
    ######################## FUNCTIONS ################################
    def addStop(self, stop: Stop) -> None:
        """" Given a list of stops, sets the stops of the bus lin to it """
        self._busStops.append(stop)

    def setRoute(self, route: list[Coord]) -> None:
        """" Given a list of coordinates, sets the route of the bus line to it """
        self._busRoute = route
        


class NetworkBus:
    """ Class to represent the set of bus lines"""
    _busLines: dict[int, BusLine] # id of the bus line -> BusLine 

    def __init__(self) -> None:
        """ Constructor of the class creates an empty dictionary """
        self._busLines = dict()

    ######################## GETTERS ################################
    def busLines(self) -> dict[int, BusLine]:
        return self._busLines

    ######################## FUNCTIONS ################################
    def addBusLine(self, line: BusLine) -> None:
        """ Adds a bus line to the dicctionary (if added previouslly asserts pops up) """
        assert line.id() not in self._busLines, str(line.id())+' already added' #error message
        self.busLines()[line.id()] = line
    
    def getBusLine(self, id_route: int) -> dict[int, BusLine]:
        """ Given the id of a bus line, returns that busline if it is in network """
        assert id_route in self.busLines(), str(id_route)+' not in network'
        return self.busLines()[id_route]



def dist(x: Coord, y: Coord) -> float:  #lon, lat
    """ Returns the distance of 2 points given their coordinates in (longitud, latitud) using haversine formula in meters"""
    return haversine((x[1], x[0]), (y[1], y[0]), unit='m') #we flip them because harversine function uses invers (lat, lon)


def create_network_base() -> NetworkBus:
    """ Creates the template for the NetworkBus class. aka creates all the buslines extracted form json but with no information """
    # We open the file and read it
    with open("busRoutes.json", "r") as file:
        json_data: str = file.read()
    TMBdata: json = json.loads(json_data)

    # Iterating through each route and getting all information needed to inicialize the route, we add it to the NetworkBus class
    network = NetworkBus()
    for route in TMBdata['features']: # Iterating over routes in json file
        id: str = str(route['properties']['ID_RECORREGUT'])
        name: str = str(route['properties']['NOM_LINIA'] + ' - ' + route['properties']['DESC_PAQUET']+' ('+route['properties']['DESC_SENTIT']+")")
        color: str = str(route['properties']['COLOR_REC'])
        NewLine: BusLine = BusLine(id, name, color) # Create new busline
        network.addBusLine(NewLine)

    return network


def get_route_json(json_file: str, network: NetworkBus) -> NetworkBus:
    """ Adds the information (list[Coord]) of the route of each BusLine to the NetworkBus passed by reference """
    # We open the file and read it
    with open(json_file, "r") as file:
        json_data: str = file.read()
    TMBdata: json = json.loads(json_data)

    # Iterating through we get the list of coordinates indicating the path the busline takes and adding them to the coorrespoinding bus line
    for route in TMBdata['features']: #iterating over routes in json file
        id: str = str(route['properties']['ID_RECORREGUT'])
        path: list[Coord] =  [tuple(lst) for lst in route['geometry']['coordinates'][0]] # We do this to avoid type errors
        network.getBusLine(id).setRoute(path)
        
    return network


def get_stops_json(json_file: str, network: NetworkBus) -> NetworkBus:
    """ Adds the information of all the stops in each bus line to the NetworkBus passed by reference """
    # We open the file and read it
    with open(json_file, "r") as file:
        json_data = file.read()
    TMBdata = json.loads(json_data)


    # We iterate through the stops getting all the information we need to inicialize them. Then add them to the corresponding bus line
    for stop in TMBdata['features']:
        id: int = stop['properties']['ID_RECORREGUT'] # id of the busroute to which the stop belongs
        # We fetch all information we need to create stop
        code: str = str(stop['properties']['CODI_PARADA'])
        name: str = str(stop['properties']['NOM_PARADA'])
        address: str = str(stop['properties']['ADRECA'])
        pos: Coord = tuple(stop['geometry']['coordinates'])
        dist_prev: float = float(stop['properties']['DISTANCIA_PAR_ANTERIOR'])

        NewStop: Stop = Stop(code+"-"+str(id) , name, address, pos, dist_prev)
        network.getBusLine(id).addStop(NewStop) #bus stops all apear in oreder 
    
    return network


def create_Bus_Network() -> NetworkBus:
    """ Returns the bus network of Barcelona"""
    network = create_network_base()
    network = get_route_json("busRoutes.json", network)
    network = get_stops_json("busStops.json", network)
    return network


def route_between_stops(idx: int, trgt_dist: float, route: list[Coord]) -> tuple[int, list[Coord]]:
    """ Returns the index and list of coordinates coresponding to the path between stops """
    distance: float = 0 #acumulated distance
    route_between: list[Coord] = [route[idx]] #we know idx is in between src, dst so we add it
    # If we are not out of range and adding the new point does not exceed the target distance we can add it to the route
    while idx < len(route)-1 and distance+dist(route[idx], route[idx+1]) <= trgt_dist:
        distance += dist(route[idx], route[idx+1])  #using harversines
        route_between.append(route[idx+1])
        idx+=1
    #we whant to return the index to the node in front of dst, aka the first one we did not add, so idx+1
    return idx+1, route_between 


def get_buses_from_network(network: NetworkBus) -> BusesGraph:
    """ Given a bus network returns the corresponding directed graph (using networkx) """
    # Initialize the directed graph
    graph = BusesGraph() 

    # Iterate through all buslines we will add the stops and the edges to the directed graph
    for busline in network.busLines().values():
        # Iterate through the stops in each bus line we add them as nodes
        for s in busline.stops():
            graph.add_node(
                s.code, # We use code atribute to idintefy each stop
                name = s.name, # Name of the stop
                address=s.address, # Address of the stop
                x=s.pos[0], y=s.pos[1],  # Postionion of the stop (lon lat)
                color="#"+busline.color() # Color coresponding to bus line
            ) 
                
        index: int = 0
        route_between: list[Coord] = list()
        #Iterating through each pair of stops we add the edge with all its necessary information
        for src, dst in zip(busline.stops(), busline.stops()[1:]):
            # Let us obtain what part of the route stored in the busline is in between each stop
                # Invariant: route[index] allways in between src and dst stops
                # Remember: dst.dist_prev indicates the distance from src->dst using the busRoute (aprox)
                # We will be adding the distance travelled on the busline route until going to the next point in route exceeds the target distance

            #we first substract the distance from src to the bus route to dist_prev to get our target distance
            trgt_dist: float = dst.dist_prev- dist(src.pos, busline.route()[index]) 
            if trgt_dist <= 0: #there are no points in route in between src and dst (invariant not true)
                route_between = list()
            else: # we update our index we currently are at in the route and get the route between stops
                index, route_between = route_between_stops(index, trgt_dist, busline.route()) 

            # We add the eddge with all of its information
            graph.add_edge(
                src.code, dst.code, # start and end id of nodes
                route=[src.pos]+route_between+[dst.pos],  # Path it takes to go from stops
                length=dst.dist_prev/8.33,  # Aproximation of time it takes (we assume average speed 30km/h)
                color="#"+busline.color() # Color corresponding to the bus line
            )
    return graph


def get_buses_graph() -> BusesGraph:
    """ Returns the directed graph representing the busses of Barcelona """
    network: NetworkBus = create_Bus_Network() # We get all the infomation into the NetworkBus class
    return get_buses_from_network(network) #


def show(g: BusesGraph) -> None:
    """ Shows the directed graph using networkx.draw """
    # We extrat the position of each node and create a dictionary
    pos: dict[str, float] = {node: (data['x'], data['y']) for node, data in g.nodes(data=True)}
    # Using the dictionary representing position we plot the graph
    nx.draw(g, pos, with_labels=False, node_color='lightblue', edge_color='gray', node_size = 1)
    plt.show()

def plot(g: BusesGraph, nom_fitxer: str) -> None:
    """ Saves and shows the graph as an image with the background city map in the specified file: nom_fitxer, using staticmaps library """
    # Create a new map object
    barcelona = stm.StaticMap(800, 600)
    barcelona.center = (2.1734, 41.3851)
    
    # Draws all the nodes in the graph using 'x', 'y' information in edge
    for id, data in g.nodes(data=True):
        pos: Coord = (data['x'], data['y'])
        marker = stm.CircleMarker(pos, data['color'], 2)
        barcelona.add_marker(marker)
    
    # Draws all the edges using route information in edge
    for u, v, data in g.edges(data=True):
        line = stm.Line(data['route'], data['color'], 1)
        barcelona.add_line(line)
    
    # Save image
    image = barcelona.render()
    image.save(nom_fitxer)
    # Show image
    image = Image.open(nom_fitxer)
    image.show()


def plot_BusLine(g: BusesGraph, id_line: str, nom_fitxer: str) -> None:
    """ Saves and shows just a bus line of the graph as an image with the background city map in the specified file: nom_fitxer, using staticmaps library """
    # Create a new map object
    barcelona = stm.StaticMap(800, 600)
    barcelona.center = (2.1734, 41.3851)
    
    # Draws all the nodes that belong to the route using that the original stop.code was composed of: stop_id+"-"+route_id
    for id, data in g.nodes(data=True):
        if id.split("-")[1] != id_line: continue
        pos: Coord = (data['x'], data['y'])
        marker = stm.CircleMarker(pos, data['color'], 5)
        barcelona.add_marker(marker)
    
    # Draws all the edges that belong to the route using that the original stop.code was composed of: stop_id+"-"+route_id
    for u, v, data in g.edges(data=True):
        if u.split("-")[1] != id_line or v.split("-")[1] != id_line: continue
        route = stm.Line(data['route'], data['color'], 3)
        barcelona.add_line(route)
    
    # Save image
    image = barcelona.render()
    image.save(nom_fitxer)
    # Show image
    image = Image.open(nom_fitxer)
    image.show()