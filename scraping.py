# import requests
# from bs4 import BeautifulSoup

# url = 'https://www.allsides.com/media-bias/media-bias-ratings'

# r = requests.get(url)
# soup = BeautifulSoup(r.content, 'html.parser')

# print(soup)

from os import getenv 
from dotenv import load_dotenv 
load_dotenv()

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID,
                                                           client_secret=SPOTIFY_CLIENT_SECRET))

from main import *
from paroles import filterWords
import json

from checkAnswers import *


def getSongsOfArtist(artist, limit=10):
    results = sp.search(q=f"artist:{artist}", limit=limit, market="FR")
    for r in results['tracks']['items']:
        print(f"{r['name']} par {r['artists'][0]['name']}")

def spotiSearch(recherche):
    results = sp.search(q=recherche, limit=5, market="FR") #market='FR' extremement important !!! sinon les resultats ne sont pas les memes que sur le site
    for r in results['tracks']['items']:
        print(f"{r['name']} par {r['artists'][0]['name']}")

def getSongsOfPlaylist(playlist, jsonfile, limiteDePlaylists=10, limiteDeChansonsParPlaylist=100): #on donne un jsonfile pour ne pas ajouter les artistes/chansons deja presents dans le json à data
    results = sp.search(q=playlist, limit=limiteDePlaylists, market="FR", type="playlist")
    #print(results)
    data=[]
    dataJson=[]
    try:
        with open("./"+jsonfile, "r") as file:
            dataJson=json.load(file)
    except:
        pass

    for r in results["playlists"]['items']:
        id=r["id"]
        print(id)
        resultSongs=sp.user_playlist_tracks("spotify",id, limit=limiteDeChansonsParPlaylist)
        for track in resultSongs['items']:
            pass
            artistes=([a["name"] for a in track["track"]['artists']])
            titre=(track["track"]["name"])
            if not any([valideReponse(titre, d['titre'], 0.9) and valideReponse(" ".join(artistes)," ".join(d['artistes']),0.9) for d in dataJson]):
                data.append({"artistes": artistes, "titre":titre})
            else:
                print(f"{titre} par {artistes} déjà présent dans le json")
                
    return data

#d=(getSongsOfPlaylist("années 80", "blindTestPlaylist2.json",1,100))

def addUrlOfSongs(data, jsonfile): #ajoute les url et ajoute un à un au json
    for d in data:
        request = youtube.search().list(
            part="snippet", 
            type="video",
            q= d['titre']
            )
        response = request.execute()
        try:
            d["url"]
        except:
            d["url"]=("https://www.youtube.com/watch?v="+response['items'][0]["id"]["videoId"])
            ajouterMusiqueDansJson(jsonfile, d)
            print(f"{d['titre']} par {d['artistes']} ajouté au json ")
    return data



def ajouterJsonPlaylist(jsonfile,playlist,limiteDePlaylists=10, limiteDeChansonsParPlaylist=100):
    d=getSongsOfPlaylist(playlist,jsonfile, limiteDePlaylists=limiteDePlaylists,limiteDeChansonsParPlaylist=limiteDeChansonsParPlaylist)
    d=addUrlOfSongs(d, jsonfile)

def ajouterMusiqueDansJson(jsonfile, d): #ajoute une seule musique dans le json
    data=[]
    try :
        with open("./"+jsonfile, "r") as file:
            data=json.load(file)
    except:
        pass
    data.append(d)
    with open("./"+jsonfile, "w") as file:
        json.dump(data,file)

ajouterJsonPlaylist("blindTestPlaylist2.json","vianney",limiteDePlaylists=1, limiteDeChansonsParPlaylist=5)

def removeIndexesFromList(indexes, list):
    for index in sorted(indexes, reverse=True):
        del list[index]

def ajouterArtistesChansons():

    data = []
    try:
        with open("./blindTestPlaylist.json", "r", encoding="utf-8") as file:
            data=json.load(file)
    except:
        pass

    #musiques=["VIANNEY - Les filles d'aujourd'hui", 'Industry baby']



    musiques=[Musique(d['url']) for d in data]
    nomsMusiques=[filterWords(m.videoName) for m in musiques]
    nbErreurs=0
    indicesARetirer=[]
    print(f"longueur de data : {len(data)}")
    for i,musique in enumerate(musiques):
        #on fait tout ça seulement si on n'a pas l'artiste ou le nom, sinon en s'en fiche
        try: #si artiste et titre définis, on passe
            data[i]["artiste"]
            data[i]["titre"]
        except:
            results = sp.search(q=nomsMusiques[i], limit=1, market="FR")
            if results['tracks']['items']==[]:
                print(f"Problème pour la musique :{nomsMusiques[i]}")
                nbErreurs+=1
                supp=input("Voulez-vous supprimer cette musique de la playlist ? (Oui=ne rien mettre, Non=mettre quelque chose)")
                if supp.lower()=="":
                    indice=i
                    indicesARetirer.append(indice)
                else: #on veut modifier
                    print(f"musique : {musique.videoName}")
                    artiste=input("Qui sont les interprètes de cette chanson (séparer les noms par des virgules) : ")
                    artistes=",".split(artiste)
                    titre=input("Quel est le titre de cette chanson : ")
                    data[i]["artiste"]=artistes
                    data[i]["titre"]=titre
            else:
                for idx, track in enumerate(results['tracks']['items']):
                    #print([artiste['name'] for artiste in track['artists']])
                    #print(track['name'])
                    indice=i
                    data[indice]["artiste"]=[artiste['name'] for artiste in track['artists']]
                    data[indice]["titre"]=track['name']
                    pass

    print(f"longueur de data : {len(data)}")
    removeIndexesFromList(indicesARetirer, data)


    with open("./blindTestPlaylist.json", "w", encoding="utf-8") as file:
        json.dump(data, file)


    print(f"Il y a {nbErreurs} erreurs")

#ajouterArtistesChansons()


