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

searchs = ["Patrick Sébastien", "mili camellia","GIGA","Vianney : Pour de vrai","Other side of the wall","100 % Johnny Live A La Tour Eiffel En Intégralité 720p"]

for search in searchs:
    test = api.search_songs(search)
    print()
    print()
    print(test['hits'][0]['result']['full_title'])
    print()
    print()

    # test_id = api.lyrics(test['hits'][0]['result']['id'])
    # print(test_id)

# print(test)

# with open('./test.json', "w", encoding="utf-8") as file:
#     json.dump(test, file)

# with open('./Lyrics_KendjiGirac.json', 'r', encoding="utf-8") as file:
#     x = json.load(file)
#     x['songs'][0]['lyrics']