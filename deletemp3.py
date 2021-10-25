import os

def truncate(): 
    for file in os.listdir("./"):   
        if file.endswith(".mp3"):
            os.remove(file)

if __name__ == "__main__":
    truncate()