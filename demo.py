import tkinter as tk
import buses
import city
import billboard
from PIL import ImageTk, Image
import requests
from io import BytesIO
import osmnx as ox
from networkx import shortest_path_length
from typing import TypeAlias
from dataclasses import asdict
from datetime import datetime


Coord: TypeAlias = tuple[float, float]   # (latitude, longitude)
Path: TypeAlias = list


class MovieApp(tk.Tk):

    def __init__(self):
        """ Constructor for the movie app """
        super().__init__()
        self.title("Movie App")  # Title of the window
        self.geometry("500x850")  # Size of window

        # initializ som values we will use in th entire program
        self.selected_movie = ""
        self.billboard = billboard.read()
        self.BusGraph = buses.BusesGraph()
        self.CityGraph = city.CityGraph()

        # Set up the widgets
        self.set_widgets()

    def set_widgets(self):
        self.movie_widgets()
        self.movie_info_widgets()
        self.bus_widgets()
        self.city_widgets()
        self.path_widgets()

        author_label = tk.Label(
            self, text="Authors: Pol de los Santos & Roger Bargall\u00F3")
        author_label.pack(pady=20)

    ############################ MOVIES ############################

    def movie_widgets(self) -> None:
        """ Creates and manages all Buttons that have to do with searching and selecting movies in Billboard """

        # Create a frame to hold the movie list and scrollbar and sarchbar
        list_frame = tk.Frame(self)
        list_frame.pack(pady=10)

        # Create all the Buttons
        list_label = tk.Label(list_frame, text="Movies:")  # title
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)  # scrollbar
        listbox = tk.Listbox(list_frame, width=50,
                             yscrollcommand=scrollbar.set)  # List of movies
        # Making scrollbar move list by y axis
        scrollbar.config(command=listbox.yview)

        search_var = tk.StringVar()  # Text variable that will be inside search bar
        search = tk.Entry(list_frame, textvariable=search_var,
                          width=50)  # Search Bar
        search.bind('<Return>', lambda event: self.search_movies(
            event, listbox, search_var.get().lower()))  # When pressing enter execute the function

        # Create a grid in wich you place all the buttons and lists
        list_label.grid(row=0, column=0)
        scrollbar.grid(row=1, column=1, sticky='ns')
        listbox.grid(row=1, column=0, sticky='nsew')
        search.grid(row=2, column=0)

        # Create a frame to hold button
        button_frame_movies = tk.Frame(self)
        button_frame_movies.pack(pady=10)

        # Create "Update" and "Select" button to update movie list
        update_button = tk.Button(button_frame_movies, text="Update Movies", command=lambda: self.update_movies(
            listbox))  # When pushing button the fucntion is executed
        select_button = tk.Button(button_frame_movies, text="Select Movie", command=lambda: self.select(
            listbox))  # When pushing button the fucntion is executed

        # Create a grid in wich you place all the buttons
        update_button.grid(row=0, column=0, padx=10)
        select_button.grid(row=0, column=1, padx=10)

    def fill_listbox(self, listbox: tk.Listbox, data: list[str]) -> None:
        """Fill the listbox with the given data"""
        listbox.delete(0, tk.END)
        for item in data:
            listbox.insert(tk.END, item)

    def update_movies(self, listbox: tk.Listbox) -> None:
        """Update the listbox with the movies from billboard"""
        listbox.delete(0, tk.END)
        movieList = [film.title for film in self.billboard.films]
        self.fill_listbox(listbox, movieList)

    def select(self, listbox: tk.Listbox) -> None:
        """Get the selected movie from the listbox and update the selected movies info """
        self.selected_movie = str(listbox.get(tk.ANCHOR))
        self.movie_info_update()

    def search_movies(self, event, listbox: tk.Listbox, search: str) -> None:
        """Search for movies based on the search input """
        if search == "":
            self.fill_listbox(
                listbox, [film.title for film in self.billboard.films])
            return
        search_movies = [movie for movie in listbox.get(
            0, tk.END) if search in movie.lower()]
        listbox.delete(0, tk.END)
        self.fill_listbox(listbox, search_movies)

    ############################ SELECTED MOVIE INFO ############################

    def movie_info_widgets(self) -> None:
        """ Creates and monitors all widgets that have to do with the selected movie (shows its information) """
        # Creates frame for the widgets
        movie_frame = tk.Frame(self)
        movie_frame.pack(pady=10)

        # Creates a blank image and an empty squar as  models for when we selcet movie
        # gets movie in format tk can process
        blank_image_tk = ImageTk.PhotoImage(
            Image.new("RGB", (150, 200), "white"))
        # sets label with movie poster
        self.movie_poster = tk.Label(movie_frame, image=blank_image_tk)
        # Mypy says error but withought this the image does not show
        self.movie_poster.image = blank_image_tk
        self.movie_info = tk.Label(
            movie_frame, text="Titol:\n Generes:\n Director:\n Actors:", justify='left')  # label with information

        # If checked th program will search for movie with Original Language if not will look for Dubbed
        self.projection_language = tk.BooleanVar(value=False)
        language = tk.Checkbutton(movie_frame, text="Original Language",
                                  variable=self.projection_language, onvalue=True, offvalue=False)

        # Puts all widgets in a grid to organize
        self.movie_poster.grid(row=0, column=0, padx=20)
        self.movie_info.grid(row=0, column=1, padx=2)
        language.grid(row=2, column=0, columnspan=2, padx=2, pady=3)

    def movie_info_update(self) -> None:
        """ Updates the movie information based on self.selected_movie """
        movie = next(
            (movie for movie in self.billboard.films if movie.title == self.selected_movie), None)
        assert movie != None, "Movie info not found"
        if movie is not None:  # if not mypy has errors even though we hav assert
            # Create a frame to hold the movie list and scrollbar and sarchbar
            image_data = requests.get(movie.poster).content
            image_tk = ImageTk.PhotoImage(Image.open(BytesIO(image_data)).resize(
                (150, 200)))  # Gets image and resizes it with format tk can process
            self.movie_poster.configure(image=image_tk)  # changes image
            # Mypy says error but withought this the image does not show
            self.movie_poster.image = image_tk

            # movie.title (str), movie.genre (list of str), movie.director (list of str), movie.actors (list of str)
            info = \
                "Titol: "+movie.title + \
                "\nGeneres: " + str(movie.genre)[1:-1] +\
                "\nDirector: " + str(movie.director)[1:-1] +\
                "\nActors: " + str(movie.actors)[1:-1]
            self.movie_info.configure(
                text=info, justify='left', wraplength=300)  # changes information

    ############################ BUSES ############################

    def bus_widgets(self) -> None:
        """ Creates and manages all buttons that have to do with Buses.py"""
        # Create a frame to hold buttons
        button_frame_bus = tk.Frame(self)
        button_frame_bus.pack(pady=10)

        # Create "Fetch", "Show", "Plot", "Plot Line" button to update bus graph
        fetchBus_button = tk.Button(
            button_frame_bus, text="Fetch Busses", command=self.get_buses_info)
        showBus_button = tk.Button(
            button_frame_bus, text="Show Busses", command=self.show_buses)
        plotBus_button = tk.Button(
            button_frame_bus, text="Plot Busses", command=self.plot_buses)
        plotBusLine_button = tk.Button(
            button_frame_bus, text="Plot Bus Line", command=self.show_buslines)

        # Creats a grid to insert buttons
        fetchBus_button.grid(row=0, column=0, padx=2)
        showBus_button.grid(row=0, column=1, padx=2)
        plotBus_button.grid(row=0, column=2, padx=2)
        plotBusLine_button.grid(row=0, column=3, padx=2)

    def get_buses_info(self) -> None:
        """Gets the Bus Graph using function in buses.py"""
        self.BusGraph = buses.get_buses_graph()

    def show_buses(self) -> None:
        """ Shows bus graph using function in buses.py """
        buses.show(self.BusGraph)

    def plot_buses(self) -> None:
        """ Plots bus graph using function in buses.py """
        buses.plot(self.BusGraph, "plot_buses.png")

    def show_buslines(self) -> None:
        """ Opens a new window with all the busline codes and when one is entered in search bar, it plots it using buses.py function """
        # Create a new window
        window = tk.Toplevel(self)
        # Create a listbox
        input = tk.StringVar()
        search = tk.Entry(window, textvariable=input, width=70)
        search.pack()

        listbox_buslines = tk.Listbox(window, width=70)
        listbox_buslines.pack(pady=5)
        # Add some items to the listbox
        for line in open('BusCodes.txt', "r"):
            listbox_buslines.insert(tk.END, line.strip())
        search.bind('<Return>', lambda event: buses.plot_BusLine(
            self.BusGraph, input.get(), str(input.get())+'.png'))

    ############################ CITY ############################

    def city_widgets(self) -> None:
        """ Creates and manages all buttons that have to do with City.py """
        # Create a frame to hold buttons
        button_frame_city = tk.Frame(self)
        button_frame_city.pack(pady=10)

        # Create "Fetch", "Show", "Plot" button to update city graph
        fetchCity_button = tk.Button(
            button_frame_city, text="Fetch City", command=self.build_city_graph)
        showCity_button = tk.Button(
            button_frame_city, text="Show City", command=self.show_city)
        plotCity_button = tk.Button(
            button_frame_city, text="Plot City", command=self.plot_city)

        # Creates grid to put buttons
        fetchCity_button.grid(row=0, column=0, padx=2)
        showCity_button.grid(row=0, column=1, padx=2)
        plotCity_button.grid(row=0, column=2, padx=2)

    def build_city_graph(self) -> None:
        """ If it is the first time it loads and saves the osmnx graph and then creates city graph using the previously obtained bus graph (nd to fetch bus graph before)"""
        if city.os.path.exists("barcelona.pickle"):
            ox_g = city.load_osmnx_graph("barcelona.pickle")
        else:
            ox_g = city.get_osmnx_graph()
            city.save_osmnx_graph(ox_g, "barcelona.pickle")
        self.CityGraph = city.build_city_graph(ox_g, self.BusGraph)

    def show_city(self) -> None:
        """ Shows City graph using function in city.py """
        city.show(self.CityGraph)

    def plot_city(self) -> None:
        """ Plots City graph using function in city.py """
        city.plot(self.CityGraph, "plot_city.png")

    ############################ PATH ############################

    def path_widgets(self) -> None:
        """ Creates and manages all widgts that have to do with the position of the user and search of the path """
        # Create a frame to hold buttons
        button_frame_loc = tk.Frame(self)
        button_frame_loc.pack(pady=10)

        # Create buttons for search with adress
        address_label = tk.Label(button_frame_loc, text="Address:")
        address = tk.StringVar()  # String variable that we will use in input bar
        address_entry = tk.Entry(
            button_frame_loc, textvariable=address, width=20)
        button_address = tk.Button(
            button_frame_loc, text="Find", command=lambda: self.pos_address(address.get()))

        # Create buttons to search with pos
        position_label = tk.Label(button_frame_loc, text="Position 'lat lon':")
        position = tk.StringVar()  # String variable that we will use in input bar
        position_entry = tk.Entry(
            button_frame_loc, textvariable=position, width=20)
        button_position = tk.Button(
            button_frame_loc, text="Find", command=lambda: self.pos_lonlat(position.get()))

        # Create grid to put the buttons
        address_label.grid(row=0, column=0, padx=2, pady=5)
        address_entry.grid(row=0, column=1, padx=2, pady=5)
        button_address.grid(row=0, column=2, padx=4, pady=5)

        position_label.grid(row=1, column=0, padx=2, pady=5)
        position_entry.grid(row=1, column=1, padx=2, pady=5)
        button_position.grid(row=1, column=2, padx=4, pady=5)

    def find_closest_projection(self, userPos: Coord) -> Coord:
        """ Given the coords of the user, calculates the firt projection the user can arrive in time and see. It takes into consideration time to arrive to the cinema and the language you wwhant to watch it in """
        user_node = ox.distance.nearest_nodes(
            self.CityGraph, userPos[0], userPos[1])  # finds nearest node for userPos
        # iterate through available films (in order) given time
        for projection in billboard.sort_projections_by_start_time(get_time(), self.billboard):
            # Search for films with the sam title
            if projection.film.title != self.selected_movie:
                continue

            # Checks if language is correct
            if self.projection_language.get() == True and projection.language == "Doblada":
                continue
            elif self.projection_language.get() == False and projection.language == "Original":
                continue

            # Calcualtes time to travl from userPos to the cinema
            projection_pos: Coord = billboard.cinemas_location[projection.cinema.name]
            projection_start: int = billboard.get_time_in_seconds(
                projection.time)
            projection_node = ox.distance.nearest_nodes(
                self.CityGraph, projection_pos[0], projection_pos[1])
            t: float = shortest_path_length(
                self.CityGraph, user_node, projection_node, weight='length')
            # If you can arrive in time return since projections are ordered
            if get_time()+t <= projection_start:
                return projection_pos

        return (-1, -1)  # If no projections are found -> error

    def pos_address(self, address: str) -> None:
        """ Given an adrss geocodes it to get position and then finds path betwen desired cinema and saves the image"""
        assert ox.geocode(address) != None, 'Location not found'
        location: Coord = ox.geocode(address)[::-1]

        closest_projection: Coord = self.find_closest_projection(location)
        assert closest_projection != (
            -1, -1), 'Could not find a Cinema that offers your desiered film and language in time for you to get there'
        path: city.Path = city.find_path(
            self.CityGraph, location, closest_projection)
        city.plot_path(self.CityGraph, path, 'path_to_cinema.png')

    def pos_lonlat(self, position: str) -> None:
        """ Given an position in coordenates  finds the path betwen desired cinema and saves the iamge"""
        assert len(position.split()
                   ) == 2, 'Not formated corrctly (just seperate with space).'
        lon = float(position.split()[0])
        lat = float(position.split()[1])
        closest_projection: Coord = self.find_closest_projection((lon, lat))
        assert closest_projection != (
            -1, -1), 'Could not find a Cinema that offers your desiered film and language in time for you to get there'
        path: city.Path = city.find_path(
            self.CityGraph, (lon, lat), closest_projection)
        city.plot_path(self.CityGraph, path, 'path_to_cinema.png')


def get_time() -> int:
    """ Gets PC current time in seconds """
    current_time = datetime.now()
    midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    return int((current_time - midnight).total_seconds())


# Create an instance of the MovieApp class and run the app
if __name__ == "__main__":
    app = MovieApp()
    app.mainloop()  # Runs app
