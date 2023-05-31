from dataclasses import dataclass
from bs4 import BeautifulSoup
import requests
import json

@dataclass 
class Film: 
	title: str
	genre: list[str]
	director: list[str]
	actors: list[str]


@dataclass 
class Cinema: 
	name: str
	address: str
	coord: tuple[float, float]

@dataclass 
class Projection: 
	film: Film
	cinema: Cinema
	time: tuple[int, int]   # hora:minut
	language: str

@dataclass 
class Billboard: 
	films: list[Film]
	cinemas: list[Cinema]
	projections: list[Projection]

@dataclass
class Film_data:
	'''This dataclass stores for a certain film, the list of the cinemas 
	where it is showed and the schedule of each cinema in format hh:mm'''
	
	theatres_names: list[str]
	original_version: list[str]
	times: list[list[str]]

	def __init__(self) -> None:
		self.theatres_names=list()
		self.original_version=list()
		self.times=list()

cinemas_location: dict[str, tuple[float, float]] = {
    "Arenas Multicines 3D": (41.37645873603848, 2.1492467400941715),
    "Aribau Multicines": (41.38622954118975, 2.1625393383857823),
    "Bosque Multicines": (41.40161248569297, 2.151937970358723),
    "Cinema Comedia": (41.38963905352764, 2.1677083550158467),
    "Cinemes Girona": (41.39976219340622, 2.1646021126874433),
    "Cines Verdi Barcelona": (41.404123503674946, 2.1569592746060673),
    "Cinesa Diagonal 3D": (41.3939571456629, 2.136310199194024),
    "Cinesa Diagonal Mar 18": (41.4104066884377, 2.2165577979125546),
    "Cinesa La Maquinista 3D": (41.43968702910417, 2.1983860838534364),
    "Cinesa SOM Multiespai": (41.435576596290986, 2.1807710685108392),
    "Glòries Multicines": (41.4053995786576, 2.1927300415232907),
    "Gran Sarrià Multicines": (41.39492805273361, 2.1339482242103953),
    "Maldá Arts Forum": (41.38335521981628, 2.1739034685088092),
    "Renoir Floridablanca": (41.38181932245526, 2.162600741522349),
    "Sala Phenomena Experience": (41.40916923817682, 2.171972029879437),
    "Yelmo Cines Icaria 3D": (41.39081534652564, 2.198733496795877),
    "Boliche Cinemes": (41.39540740361847, 2.153624068509293),
    "Zumzeig Cinema": (41.37754018596865, 2.1450699973441822),
    "Balmes Multicines": (41.40736701577023, 2.138718385701353),
    "Cinesa La Farga 3D ": (41.36324361629017, 2.104830226735673),
    "Filmax Gran Via 3D": (41.358458853930166, 2.12835815131626),
    "Full HD Cinemes Centre Splau": (41.34757656010739, 2.0790624624109917),
    "Cine Capri": (41.325897166270195, 2.0953815132325104),
    "Ocine Màgic": (41.44390419188643, 2.2306844298807826),
    "Cinebaix": (41.38204532152056, 2.0451188433715655),
    "Cinemes Can Castellet": (41.345363870736016, 2.0405710690597574),
    "Cinemes Sant Cugat": (41.469755698209426, 2.0905412796073817),
    "Cines Montcada": (41.49435241992408, 2.180264296085647),
    "Yelmo Cines Baricentro": (41.508494990085694, 2.1383378243356965),
    "Cinesa La Farga 3D": (41.36328395211327, 2.104722953165676),
}



def get_cinemas() -> dict[str,Cinema]:
	'''This method returns a dictionary with all the cinemas in
	Barcelona where the key is a cinema name and the value is its data'''

	cinema_dict=dict()
	theatre_address:list[str,str]=dict() #Contains the street where a certain theatre is located
	
	for i in range(1,4):

		urlToScrape = "https://www.sensacine.com/cines/cines-en-72480/?page=" + str(i)
		r = requests.get(urlToScrape)
		soup = BeautifulSoup(r.content, "html.parser")
		item_resa_elements = soup.find_all("div", class_="item_resa")

		cinema_info=soup.find_all('a', class_='j_entities')
		span_address = soup.find_all('span', class_='lighten')

		for i,cinema in enumerate(cinema_info):
			#this retrieves the adress of each theatre
			cinema_id=json.loads(cinema["data-entities"])["entityId"]
			theatre_address[cinema_id]=span_address[2*i+1].get_text(strip=True)

		for item in item_resa_elements:
			jw_div=item.find('div', class_='j_w')
			data_theater = json.loads(jw_div['data-theater'])
			if not data_theater['name'] in cinema_dict:
				cinema_dict[data_theater['name']] = Cinema(name=data_theater['name'],address=theatre_address[data_theater['id']],coord=cinemas_location[data_theater['name']])

	return cinema_dict

def get_films() -> dict[str,Film]:
	'''This method returns a dictionary with all the films in cinemas of
	Barcelona where the key is the film name and the value is its data'''

	film_dict=dict()
	
	for i in range(1,4):

		urlToScrape = "https://www.sensacine.com/cines/cines-en-72480/?page=" + str(i)
		r = requests.get(urlToScrape)
		soup = BeautifulSoup(r.content, "html.parser")
		item_resa_elements = soup.find_all("div", class_="item_resa")

		for item in item_resa_elements:
			jw_div=item.find('div', class_='j_w')
			data_movie = json.loads(jw_div['data-movie'])
			if not data_movie['id'] in film_dict:
				film_dict[data_movie['id']] = Film(title=data_movie['title'],genre=data_movie['genre'],director=data_movie['directors'],actors=data_movie['actors'])

	return film_dict

def read() -> Billboard:
	'''Returns the billboard of Barcelona cinema's.
	First it retrieves the html blocks of sensacine.com, which are those delimited by the divs with class item_resa.
	Each block of this type contains a film, the cinema where it's showed and the schedule.
	We retrieve for each block the id of the movie and the name of the cinema in the sublock delimited by div with class j_w.
	Finally, we load the film information to a dictionary with the cinema and the schedule. To avoid repeated films in repeated
	cinemas we add the tuple (movie_id,theatre_name) to a set, and we use the set movie_info to store its information and avoid
	saving multiple times the same film.'''

	bcn_cinemas=get_cinemas() #Contains all the different cinemas in Barcelona
	bcn_films=get_films() #Contains all the different films in Barcelona
	processed_films:set[str,str]=set() #Contains pairs of (movie id, cinema name) to avoid duplicated movies in the same cinema
	film_info :dict[str,Film_data]=dict() #given a film id, it contains its data

	for i in range(1,4):

		urlToScrape = "https://www.sensacine.com/cines/cines-en-72480/?page=" + str(i)
		r = requests.get(urlToScrape)
		soup = BeautifulSoup(r.content, "html.parser")
		item_resa_elements = soup.find_all("div", class_="item_resa") #The information of films and theaters is in this class


		for item in item_resa_elements:
			#Each item contains a certain film in a certain cinema with its schedule

			jw_div=item.find('div', class_='j_w')
	
			theatre_name = json.loads(jw_div['data-theater'])['name']
			movie_id = json.loads(jw_div['data-movie'])['id']
			
			if not (movie_id,theatre_name) in processed_films: #we check if we have processed a certain movie in a certain cinema
				processed_films.add((movie_id,theatre_name))
				if not movie_id in film_info:
					film_info[movie_id]=Film_data()
				else:
					film_info[movie_id].theatres_names.append(theatre_name) #We add the cinema in the list of cinemas where the film belongs
					film_info[movie_id].original_version.append("Original" if "Original" in str(jw_div) else "Doblada") #retrieve the language of the movie

					#We retrieve all the following times where the film is showed in a particular cinema
					data_times:list[str]=list()
					for time in item.find_all('em'):
						item_times = json.loads(time['data-times'])
						data_times.append(item_times)
			 
					film_info[movie_id].times.append(data_times)			
				
	
	
	films_list:list[Film]=[film for film in bcn_films.values()]
	theater_list:list[Cinema]=[cinema for cinema in bcn_cinemas.values()]
	projection_list:list[Projection]=list()
	

	for id,movie in bcn_films.items(): #for each movie
		if id not in film_info:
			continue
		for i in range(len(film_info[id].times)): #we iterate over the number of cinemas it appears
			for curr_time in film_info[id].times[i]: #for each cinema we iterate over the schedule in that cinema
				projection_list.append(Projection(film=movie,cinema=film_info[id].theatres_names[i],time=(curr_time[0],curr_time[2]),language=film_info[id].original_version[i]))
	
	return Billboard(films=films_list, cinemas=theater_list, projections=projection_list)

def get_projections_by_film_name(name: str, billboard: Billboard) -> list[Projection]:
	'''Given a word, it returns a list with all the films in the Billboard that contain that word in their name'''
	return [projection for projection in billboard.projections if name.lower() in projection.film.title.lower()]

def get_time_in_seconds(time: str) -> int:
	'''Given a time in hh:mm format it returns the seconds from 00:00 to that time'''
	return int(time[:2])*3600+int(time[3])*60+int(time[4])

def sort_projections_by_start_time(time: str, billboard: Billboard) -> list[Projection]:
	'''Given a start time in format hh:mm it sorts the billboard according to time difference between the given time'''
	time_in_secs=get_time_in_seconds(time)
	return sorted(billboard.projections, key=lambda x:abs(get_time_in_seconds(x.time[0])-time_in_secs))

'''
billboard=read()
name=input()
print(projection_by_film_name(name,billboard))'''