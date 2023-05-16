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

def read() -> Billboard:
	data_theater_list:list[dict]=[]
	data_movie_list:list[dict]=[]
	data_times_list:list[list]=[]
	original_version_list:list[str]=[]

	for i in range(1,4):
		urlToScrape = "https://www.sensacine.com/cines/cines-en-72480/?page=" + str(i)
		r = requests.get(urlToScrape)
		soup = BeautifulSoup(r.content, "html.parser")
		item_resa_elements = soup.find_all("div", class_="item_resa")

		for item in item_resa_elements:
			jw_div=item.find('div', class_='j_w')
			original_version_list.append("Original" if "Original" in str(jw_div) else "Doblada")
			data_theater = json.loads(jw_div['data-theater'])
			data_theater_list.append(data_theater)
			data_movie = json.loads(jw_div['data-movie'])
			data_movie_list.append(data_movie)
			data_times=[]
			for time in item.find_all('em'):
				item_times = json.loads(time['data-times'])
				data_times.append(item_times)
			data_times_list.append(data_times)
			
	
	
	films_list=[Film(title=film['title'],genre=film['genre'],director=film['directors'],actors=film['actors']) for film in data_movie_list]
	theater_list=[Cinema(name=cinema['name'],address=cinema['city']) for cinema in data_theater_list]
	projection_list=[]
	for i,film_times in enumerate(data_times_list):
		for curr_time in film_times:
			projection_list.append(Projection(film=films_list[i],cinema=theater_list[i],time=(curr_time[0],curr_time[2]),language=original_version_list[i]))
	return Billboard(films=films_list, cinemas=theater_list, projections=projection_list)


#read()