# PracticaAP2-2 - CineBus
Segona pràctica d'AP2 - CineBus - GCED - UPC

Basat en la [pràctica 2 d'ap2 2023](https://github.com/jordi-petit/ap2-cinebus-2023)

## Descripció

Aquesta pràctica ofereix una aplicació desenvolupada en Python, que donada una película en un cinema de Barcelona, proporciona el camí més curt per arribar a l'hora a veure la película utilitzant el bus.
L'aplicació funciona de forma interactiva, i és senzilla d'entendre per l'usuari.

### Prerequisits

Per poder executar el programa és necessari tenir instal·lat:

```
python3
pip3
requests
beatifulsoup (bs4)
networkx 
osmnx
haversine
staticmap 
json
matplotlib
typing
dataclasses
PIL
pickle
datetime
tkinter
```

### Execució

Per executar el programa cal la comanda ```python3 demo.py``` i tenir connexió a internet.
En algunes ocasions es pot donar un error a l'executar el mòdul per una mala sincronització amb la web de la cartellera de cinemes de Barcelona, si això succeeix es pot tornar a provar d'executar el mòdul.

## Canvis respecte el projecte original

Respecte la idea original de la pràctica s'han fet els següents canvis amb autorització del professorat:
S'ha considerat el graf de buses i de city com dirigit, per tal de simular de forma més acurada les rutes.
S'ha posat certa velocitat diferent en els trossos de ruta a peu i en bus, per tal de garantir que sempre s'agafa el camí més ràpid.
S'ha assignat un temps d'espera a cada parada, ja que agafar el bus de forma instantània no és realista.
S'ha agafat un json de AMB que conté informació real de les rutes dels busos, per tal de mostrar el recorregut real.
Hem utilizat una llibreria per mostrar el programa en una interfície gràfica i fer-lo més amigable i intuitiu per l'usuari.
S'ha implementat una funció per mostrar el recorregut d'una línia concreta de bus de Barcelona.
S'ha assignat el color corresponent a cada línia de bus.

### Instruccions

Un cop tinguem la finestra principal del programa cal seguir els següents passos:
Premer els botons fetch buses i fetch city, que carreguen els grafs de busos i de la ciutat.
Seleccionar pelicula de la llista que apareixerà en el requadre superior, en cas de que no surti cap llista apretar el botó Update Movies.
Si volem veure la película en versió original cal marcar la casella Original Language.
A continuació cal escriure l'adreça o les coordenades des d'on volem sortir per anar al cine i premer Find.
Ens apareixerà una imatge amb la ruta que haurem de fer.

### Estil de codi

S'ha utilitzat el format estàndard PEP8 de python per formatejar el codi.

## Versió

Aquesta és la verió 1.0 del projecte. 

## Autors

* **Pol de los Santos Subirats** - *1r GCED* - [Github](https://github.com/PDelos)
* **Roger Bargalló Roselló** - *1r GCED* - [Github](https://github.com/rbargallor)

## Llicència
Aquest projecte està sota la llicència del MIT - see the [LICENSE.md](LICENSE.md) file for details

