#fichier permet de clear de la base de données json
import json

def truncate():
    with open("./radioPlaylist.json", "w", encoding="utf-8") as file:
        json.dump([], file)

if __name__ == "__main__":
    truncate()
    