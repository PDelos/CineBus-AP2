from dataclasses import dataclass
from typing import TypeAlias, Any
import staticmap as stm
import networkx as nx
from yogi import read
from haversine import haversine
import json

BusesGraph : TypeAlias = nx.DiGraph
Coord : TypeAlias = tuple[float, float]   # (latitude, longitude)

@dataclass
class Stop: 
    name: str
    address: str
    pos: Coord


class BusLine:
    _id: int #id del recorregut (no nomes linea)
    _name: str #nom de la linea amb parada inicial i final
    _busStops: list[Stop]
    _busRoute: list[Coord]

    def __init__(self, Id: int, Nom: str) -> None:
        self._id = Id
        self._name = Nom

        self._busStops = list()
        self._busRoute = list()

    
    def setStops(self, stops: list[Stop]) -> None:
        self._busStops = stops

    def setRoute(self, route: list[Coord]) -> None:
        self._busRoute = route

    def mergeStopsRoute(self) -> None:
        for s in self.stops():
            #get index of closest point of route
            i: int = min(range(len(self.route())), key=lambda i: dist(s.pos, self.route()[i]))
            #what is better insert in i or insert i+1 ?
            route = self.route()
            dist_1 = (
                dist(route[i-1], s.pos) + dist(s.pos, route[i]) + dist(route[i], route[i+1])
                if i < len(route) - 1 and i > 0
                else float('inf')
            ) #importa poc quan es inici o final de ruta
            dist_2 = (
                dist(route[i], s.pos) + dist(s.pos, route[i+1]) + dist(route[i-1], route[i])
                if i < len(route) - 1 and i > 0
                else float('inf')
            ) #importa poc quan es inici o final de ruta

            self.route().insert(i if dist_1 < dist_2 else i+1, s.pos)


    def id(self) -> int:
        return self._id
    
    def name(self) -> str:
        return self._name
    
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


def format_and_overwrite_json(file_path: str) -> None:
    # Open the file and load the JSON data
    with open(file_path, "r") as file:
        data = json.load(file)

    # Format the JSON data with indentation
    formatted_data = json.dumps(data, indent=4)

    # Overwrite the file with the formatted JSON data
    with open(file_path, "w") as file:
        file.write(formatted_data)


def create_network_base() -> NetworkBus:
    #fem servir el fitxer de les rutes per establir totes les que hi hauran
    with open("busRoutes.json", "r") as file:
        json_data = file.read()
    TMBdata = json.loads(json_data)
    BcnNetwork = NetworkBus()
    for route in TMBdata['features']: #iterating over stops in json file
        #get id and list ofcoords
        id: str = route['properties']['ID_RECORREGUT']
        name: str = route['properties']['NOM_LINIA'] + '-' + route['properties']['ORIGEN_TRAJECTE'] + '/' + route['properties']['DESTI_TRAJECTE'] 
        NewLine = BusLine(id, name)
        BcnNetwork.addBusLine(NewLine)
    return BcnNetwork


def get_route_json(json_file: str, BcnNetwork: NetworkBus) -> NetworkBus:
    with open(json_file, "r") as file:
        json_data = file.read()
    TMBdata = json.loads(json_data)

    for route in TMBdata['features']: #iterating over stops in json file
        #get id and list ofcoords
        route_id: str = route['properties']['ID_RECORREGUT']
        route_coords: list[Coord] = route['geometry']['coordinates'][0]
        #add the list of coords to the coorrespoinding line
        BcnNetwork.getBusLine(route_id).setRoute(route_coords)
        
    return BcnNetwork


def fetch_stops(json_file: str, route_id: int) -> list[tuple[int, Stop]]:
    with open(json_file, "r") as file:
        json_data = file.read()
    TMBdata = json.loads(json_data)

    busStops: list[tuple[int, Stop]] = list()
    for stop in TMBdata['features']:
        if stop['properties']['ID_RECORREGUT'] != route_id: continue
        order: int = stop['properties']['ORDRE']
        name: str = stop['properties']['NOM_PARADA']
        address: str = stop['properties']['ADRECA']
        pos: Coord = stop['geometry']['coordinates']
        busStops.append((order, Stop(name, address, pos)))

    return busStops


def get_stops_json(json_file: str, BcnNetwork: NetworkBus) -> NetworkBus:
    for route_id in BcnNetwork.busLines(): #iterating over all routes
        #find all stops related to that route
        stops: list[tuple[int, Coord]] = fetch_stops(json_file, route_id)
        stops.sort(key = lambda x: x[0])
        BcnNetwork.getBusLine(route_id).setStops([s[1] for s in stops]) # set the stop of the bus lines
        BcnNetwork.getBusLine(route_id).mergeStopsRoute() #merge stops into route (aka adds stops to the route)
    
    return BcnNetwork


def generate_map_network(BcnNetwork: NetworkBus) -> None:
    # Create a new map object
    barcelona = stm.StaticMap(800, 600)
    barcelona.center = (2.1734, 41.3851) #staticmap uses 

    for busline in BcnNetwork.busLines().values(): #iterating over all buslines
        #find all stops related to that route
        for s in busline.stops():
            marker = stm.CircleMarker(s.pos, 'red', 2)
            barcelona.add_marker(marker)
        route = stm.Line(busline.route(), 'black', 1)
        barcelona.add_line(route)

    image = barcelona.render()
    image.save("barcelona_map.png")


def generate_map_line(BcnNetwork: NetworkBus) -> None:
    # Create a new map object
    barcelona = stm.StaticMap(800, 600)
    barcelona.center = (2.1734, 41.3851) #lon, lat

    #shows all rout_id and thier names:
    for id, busline in BcnNetwork.busLines().items():
        print(id, '--->', busline.name())
    print('Please intput the id of the bus line you want to look at:')

    busline = BcnNetwork.busLines()[read(int)]
    for s in busline.stops():
        marker = stm.CircleMarker(s.pos, 'red', 2)
        barcelona.add_marker(marker)

    route = stm.Line(busline.route(), 'black', 1)
    barcelona.add_line(route)

    image = barcelona.render()
    image.save('barcelona_line.png')



def get_graph_dist(x: Coord, y: Coord, route: list[Coord]) -> float:
    i: int = route.index(x) #could be imporved complexity
    j: int = route.index(y) #could be imporved complexity
    return sum(dist(src, dst) for src, dst in zip(route[i:j+1], route[i+1:j+1]))

def get_buses_graph(BcnNetwork: NetworkBus) -> BusesGraph:
    BcnBusGraph = BusesGraph()
    for i, busline in zip([0], BcnNetwork.busLines().values()):
        #Add nodes to the graph
        for s in busline.stops():
            BcnBusGraph.add_node(s.name, address=s.address, pos=s.pos)
        #Add edges to the graph

        for src, dst in zip(busline.stops(), busline.stops()[1:]):
            if src.name == dst.name: continue
            distance_between = get_graph_dist(src.pos, dst.pos, busline.route()) #using harversine
            BcnBusGraph.add_edge(src.name, dst.name, weight=distance_between)
    return BcnBusGraph


if __name__ == '__main__':
    #format_and_overwrite_json("busRoutes.json")
    #format_and_overwrite_json("busStops.json")

    #latitud es numero gran, longitud petit
    bcnNetwork = create_network_base()
    bcnNetwork = get_route_json("busRoutes.json", bcnNetwork)
    bcnNetwork = get_stops_json("busStops.json", bcnNetwork)

    #generate_map_network(bcnNetwork) #genera el mapa amb tot
    #generate_map_line(bcnNetwork) #genera el mapa de una linea
    BcnBusGraph = get_buses_graph(bcnNetwork) #genera el graph (dirigit amb weight = distancia que fa el bus)
