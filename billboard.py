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
	theatre_address:list[str,str]={}
	processed_films:set[str,str]=set() #movie id, cine id (evitar repetits)

	for i in range(1,4):
		urlToScrape = "https://www.sensacine.com/cines/cines-en-72480/?page=" + str(i)
		r = requests.get(urlToScrape)
		soup = BeautifulSoup(r.content, "html.parser")
		item_resa_elements = soup.find_all("div", class_="item_resa")
		
		cinema_info=soup.find_all('a', class_='j_entities')
		span_address = soup.find_all('span', class_='lighten')

		for i,cinema in enumerate(cinema_info):
			cinema_id=json.loads(cinema["data-entities"])["entityId"]
			theatre_address[cinema_id]=span_address[2*i+1].get_text(strip=True)

		for item in item_resa_elements:
			jw_div=item.find('div', class_='j_w')
	
			data_theater = json.loads(jw_div['data-theater'])
			data_movie = json.loads(jw_div['data-movie'])
			
			if not (data_movie['id'],data_theater['id']) in processed_films:
				processed_films.add((data_movie['id'],data_theater['id']))
				original_version_list.append("Original" if "Original" in str(jw_div) else "Doblada")
				data_theater_list.append(data_theater)
				data_movie_list.append(data_movie)
			
				data_times=[]
				for time in item.find_all('em'):
					item_times = json.loads(time['data-times'])
					data_times.append(item_times)
			 
				data_times_list.append(data_times)
			
	
	
	films_list=[Film(title=film['title'],genre=film['genre'],director=film['directors'],actors=film['actors']) for film in data_movie_list]
	theater_list=[Cinema(name=cinema['name'],address=theatre_address[cinema['id']]) for cinema in data_theater_list]
	projection_list=[]
	for i,film_times in enumerate(data_times_list):
		for curr_time in film_times:
			projection_list.append(Projection(film=films_list[i],cinema=theater_list[i],time=(curr_time[0],curr_time[2]),language=original_version_list[i]))
	return Billboard(films=films_list, cinemas=theater_list, projections=projection_list)

def projection_by_film_name(name: str, billboard: Billboard) -> list[Projection]:
	return [projection for projection in billboard.projections if name.lower() in projection.film.title.lower()]

def get_time_in_seconds(time: str) -> int:
	return int(time[:2])*3600+int(time[3])*60+int(time[4])

def projection_by_start_time(time: str, billboard: Billboard) -> list[Projection]:
	time_in_secs=get_time_in_seconds(time)
	return sorted(billboard.projections, key=lambda x:abs(get_time_in_seconds(x.time[0])-time_in_secs))


'''billboard=read()
name=input()
print(projection_by_start_time(name,billboard))'''