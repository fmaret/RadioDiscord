import lyricsgenius as genius
import json
import os

# os.system('cls')

geniusCreds = "BmuTK-q96oa5NLEbUPkErL8LHLjrXS_nKTmrTxkAhRaystKdhwdrHsVp9tMWE85V"
# artist_names = ["Ado", "Kendji Girac"]

api = genius.Genius(geniusCreds)

# for artist in artist_names:
#     art = api.search_artist(artist, max_songs=5)
#     os.getcwd()
#     art.save_lyrics()

#searchs = ["Patrick Sébastien", "mili camellia","GIGA","Vianney : Pour de vrai","Other side of the wall","100 % Johnny Live A La Tour Eiffel En Intégralité 720p"]

searchs = ["Début de Soiree - Nuit de Folie - Clip Officiel", "Images - Les Démons de Minuit", "Desireless - Voyage Voyage", "Indochine - J'ai demandé à la lune (Clip officiel)"]



""" for search in searchs:
    test = api.search_songs(search)
    print(test['hits'][0]['result']['full_title'])

    test_id = api.lyrics(test['hits'][0]['result']['id'])
    print(test_id) """

# print(test)

# with open('./test.json', "w", encoding="utf-8") as file:
#     json.dump(test, file)

# with open('./Lyrics_KendjiGirac.json', 'r', encoding="utf-8") as file:
#     x = json.load(file)
#     x['songs'][0]['lyrics']

def filterWords(title):
    wordsToFilter = ["clip officiel", "official video", "4k", "(paroles)", "(parole)", "(lyric)", "(lyrics)",
    "(lyrics video)","(audio)",
    "[]", "()", " -", " –"
    ] #bien mettre à la fin les parenthèses fermées seule et crochets seuls pour faire en dernier
    for m in wordsToFilter:
        if m in title.lower():
            indice=title.lower().find(m)
            title=title[0:indice]+title[indice+len(m):]
    return title

def getLyrics(title: str, sorted_=False):
    #filtrage des noms

    #Attention : tout mettre en minuscules
    
    title=filterWords(title)

    #fin du filtrage
    
    test = api.search_songs(title)
    if test['hits'] != []:
        
        paroles = None

        if sorted_ == True:
            for i in range (len(test['hits'])):
                if not "pageviews" in test['hits'][i]['result']['stats']:
                    test['hits'][i]['result']['stats']['pageviews'] = 0

            sorted_hits = sorted(test['hits'], key=lambda d: d['result']['stats']['pageviews'], reverse=True) 
            paroles = api.lyrics(sorted_hits[0]['result']['id'])
        else:
            paroles = api.lyrics(test['hits'][0]['result']['id'])

        return paroles
    return ""

#Kygo - Love Me Now (Official Video) ft. Zoe Wees

if __name__ == "__main__":
    print(getLyrics("Kygo - Love Me Now"))
    print(getLyrics("Camellia Mili", True))

    # https://genius.com/Kygo-love-me-now-lyrics
    #getLyrics("Johnny Halliday - Allumer le feu")
    # https://genius.com/Mili-indie-camelia-lyrics
