import discord
from discord.channel import DMChannel
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.message import Message

from os import getenv 
from dotenv import load_dotenv 
load_dotenv()

#import youtube_dl
import yt_dlp

import os
import asyncio

from googleapiclient.discovery import build

from deletemp3 import truncate as removeMP3s

from paroles import getLyrics

import json

import random

import time
from threading import Timer

from gestionRadio import *

from checkAnswers import *

TOKEN = getenv("TOKEN")
YT_API_KEY = getenv("YT_API_KEY_3")

YTDL_OPTIONS = {
            'format': 'bestaudio/best',
            'postprocessors':[{
                'key':'FFmpegExtractAudio',
                'preferredcodec':'mp3',
                'preferredquality':'192',
                }],
            }

YOUTUBE_LINKS = [
        "https://www.youtube.com/",
        "https://youtu.be"
    ]

bot = commands.Bot(command_prefix="!")

youtube = build('youtube', 'v3', developerKey=YT_API_KEY)

queue = []

blindTest = {
    "on": False,
    "chansonBlindTest" : None,
    "joueurs":[],
    "embedLeaderboard":None
}

#joueurs contient des objets {"nom":nom, "points":points, "dejaRepTitre":bool, "dejaRepArtiste":bool}




'''
* Classes
'''

class Musique():
    def __init__(self, url, title="", artists=[]):
        self.url = url

        request = youtube.videos().list(part="snippet", id=url.split("?v=",1)[1])
        response = request.execute()

        try:
            self.videoName = response['items'][0]['snippet']['title']
        except:
            self.videoName = "Problème Lecture Musique"
        
        self.title=title
        self.artists=artists




#tests

# l="https://www.youtube.com/watch?v=nBI0bDH8W28&list=PLlv1wuE2aMi__xQcsEiBimc_4qZQyQW8Z&index=1" #lien de la video seule qui lance la playlist
# id="8U0wIdnX4mw" #id de cette vidéo
# playlistId="PLlv1wuE2aMi__xQcsEiBimc_4qZQyQW8Z" #id de la playlist complete
# request=youtube.playlistItems().list(
#        part="snippet",
#        playlistId=playlistId,
#        maxResults="50")
# response = request.execute()

#for video in response['items']:

    # Si t'enleve part= tu recuperes tout ?
    # Bon si meme l'api youtube c'est de la merde on peut pas y faire grand chose.... 
    # Si y'a lid ...
    
# Ya pas status
#fin tests
def isAllowed(lien: str) -> bool:
    video_id = lien.split("https://www.youtube.com/watch?v=",1)[1]
    request=youtube.videos().list(
       part="contentDetails",
       id=video_id,
       maxResults="50")
    response2 = request.execute()

    allowed = True
    try:
        restrictions = response2["items"][0]['contentDetails']["regionRestriction"]
        try:
            if "FR" in restrictions['blocked']:
                allowed = False
        except:
            pass

        try:
            if not "FR" in restrictions['allowed']:
                allowed = False
        except:
            pass
        
    except:
        pass

    return allowed

@bot.event
async def on_ready():
    removeMP3s()
    print("Le bot est prêt !")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="vos instructions"))

# Genre fais des petites variables et sers toi de ces variable
# Par exemples tu vas te resservir de ca:

def getVideosUrlFromPlaylist(url:str):
    plid = url.split("playlist?list=",1)[1]
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=plid,
        maxResults="50")
    response = request.execute()

    liens = []

    for x in (response['items']):
        liens.append(x['snippet']['resourceId']['videoId'])

    return liens   

def getPlaylistName(url: str):
    plid = url.split("playlist?list=",1)[1]
    request=youtube.playlists().list(
        part="snippet",
        id=plid,
        maxResults="50")
    response = request.execute()
    return response['items'][0]['snippet']['title']

def addPlaylistToQueue(url:str): #return le nom de la playlist
    liens_videos = getVideosUrlFromPlaylist(url)

    for lien in liens_videos:
        queue.append(Musique("https://www.youtube.com/watch?v="+lien))

    return getPlaylistName(url)

@bot.command()
async def play(ctx:Context, url:str, channel:str = "General"):
    if not any(url.startswith(YT_LINK) for YT_LINK in YOUTUBE_LINKS):
        await ctx.send("Ce n'est pas un lien Youtube !")
        return
    
    if "playlist?list" in url: #on a mis une playlist
        nomPlaylist = addPlaylistToQueue(url)
        await ctx.send("Ajout de la playlist : "+nomPlaylist)
    elif "&list" in url:  #on a mis une seule musique mais elle a une playlist dans le lien
        m=Musique(url.split("&list")[0])
        queue.append(m) 
        await ctx.send("Ajout de la musique : "+m.videoName)
    else: 
        m=Musique(url)
        queue.append(m)
        await ctx.send("Ajout de la musique : "+m.videoName)

    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name=channel)
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice: #voice vaut Null si le bot n'était pas dans le channel
        await voiceChannel.connect()
    else:
        # await ctx.send("Le bot est déjà là.")
        pass


    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        
    if not voice.is_playing():
        play_next(ctx)
        await ctx.send("ATTENTION zeparti zeparti, la musique commence !")
    else:
        await ctx.send("Musique ajoutée à la queue")
    
def play_next(ctx:Context):

    if len(queue) > 0:
        if not isAllowed(queue[0].url):
            asyncio.run_coroutine_threadsafe(ctx.send("La musique de merde qui fonctionne pas a été skip, ca nous aura pris 4h mais elle est skip juste pour pas que vous ayez a relancer la playlist depuis le depart.... Remerciez nous bande de merdes !"), bot.loop)
            del queue[0]
            play_next(ctx)
            return

    # for el in queue:
    #     print(el.videoName)

    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if len(queue) == 0:
        if vc is None:
            return

        if not vc.is_playing():
            asyncio.run_coroutine_threadsafe(ctx.send("Il n'y a plus de musique dans la queue."), bot.loop)
            asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="vos instructions")), bot.loop)
        return

    downloadSong(queue[0])

    asyncio.run_coroutine_threadsafe(writeLyrics(ctx, queue[0]), bot.loop)
    asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=queue[0].videoName)), bot.loop)
    
    def after_func(ctx):
        del queue[0]
        play_next(ctx)

    vc.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: after_func(ctx))
    
@bot.command()
async def search(ctx:Context, *, txt:str): #* pour pouvoir passer plusieurs mots en arguments txt
    request = youtube.search().list(
        part="snippet",
        q=txt,
        maxResults="5",
        type='video')

    response = request.execute()
    texteAAfficher="Quelle musique voulez-vous lancer ?\n"
    liens=[]
    for i,x in enumerate(response['items']):
        texteAAfficher+= f"{str(i+1)}. {x['snippet']['title']}\n"
        liens.append("https://www.youtube.com/watch?v="+x['id']['videoId'])
    await ctx.send(texteAAfficher)

    await ctx.send("Merci d'entrer un nombre entre 1 et 5.")

    def validity(msg: Message):
        return msg.author == ctx.author

    message = await bot.wait_for("message", check=validity)    
    if message.content.isnumeric() and 0<int(message.content)<=5:
        await play(ctx, liens[int(message.content)-1])
    else:
        await ctx.send("Recherche annulée.")
        # Bon moi je finis le taff, je rentre chez moi et je re ! A toute A toute :) Quand je reviens c'est finis (: j'ai la pression xD A tte !
    # relance c'est good

@bot.command()
async def skip(ctx:Context):
    # Stop current song
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice.stop()

    # Play next song on queue (pas nécessaire car quand on voice.stop() ça lance le after qui lance play_next)
    # play_next(ctx)

@bot.command()
async def leave(ctx:Context):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        await voice.disconnect()
        queue.clear()
    else:
        await ctx.send("Le bot n'est pas dans un channel vocal.")

@bot.command()
async def pause(ctx:Context):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("Il n'y a pas de musique en cours de lecture.")

@bot.command()
async def resume(ctx:Context):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("Le lecteur n'est pas en pause.")

async def writeLyrics(ctx:Context, m:Musique, sorted_=False):
    print("VIVANT")
    guild = ctx.message.guild
    channel = discord.utils.get(ctx.guild.channels, name="paroles") #recupérer le nom du channel pour savoir s'il existe
    if channel is None:
        await guild.create_text_channel("paroles")
    
    channel = discord.utils.get(ctx.guild.channels, name="paroles")
    lyrics = getLyrics(m.videoName, sorted_)

    await channel.send("Paroles de "+m.videoName)

    if len(lyrics) > 1500:
        await channel.send(lyrics[0:1500])
        await channel.send(lyrics[1501:])
    else:
        await channel.send(lyrics)
        

    #await ctx.send(f"Created a channel named paroles")


@bot.command()
async def changeLyrics(ctx:Context):
    if ctx.channel.name != "paroles":
        return
        
    await writeLyrics(ctx, queue[0], True)

@bot.command()
async def addToRadio(ctx:Context, url): #pas de vérif que c'est bien une playlist pour l'instant
    # Lire un fichier

    # TODO: Verifier si c'est bien une playlist

    if not any(url.startswith(YT_LINK) for YT_LINK in YOUTUBE_LINKS):
        await ctx.send("Ce n'est pas un lien Youtube !")
        return

    if "playlist?list" in url: #on a mis une playlist
        nomPlaylist = addPlaylistToJson(url)
        await ctx.send("Ajout de la playlist : "+nomPlaylist)
    elif "&list" in url:  #on a mis une seule musique mais elle a une playlist dans le lien
        m=Musique(url.split("&list")[0])
        addSongToJson(m.url) 
        await ctx.send("Ajout de la musique : "+m.videoName)
    else: 
        m=Musique(url)
        addSongToJson(m.url) 
        await ctx.send("Ajout de la musique : "+m.videoName)

    


def addSongToJson(songUrl: str):
    data = None
    try:
        with open("./radioPlaylist.json", "r", encoding="utf-8") as file:
            data = json.load(file) 
    except:
        data = []
        
    # No Duplicate
    if any(song for song in data if song['url'] == songUrl):
        return

    if not isAllowed(songUrl):
        return
        
    data.append({"url":songUrl})

    with open("./radioPlaylist.json", "w", encoding="utf-8") as file:
        json.dump(data, file)

def addPlaylistToJson(playlistUrl: str):
    liens_videos = getVideosUrlFromPlaylist(playlistUrl)

    for lien in liens_videos:
        addSongToJson("https://www.youtube.com/watch?v="+lien)

    return getPlaylistName(playlistUrl)


def play_next_radio(ctx:Context):
    #pas de queue dans la radio, on choisit une musique random et on la joue

    chosenSong = chooseSong()
    while not isAllowed(chosenSong.url):
            chosenSong = chooseSong()

    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    downloadSong(chosenSong)

    asyncio.run_coroutine_threadsafe(writeLyrics(ctx, chosenSong), bot.loop)
    asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=chosenSong.videoName)), bot.loop)
    

    vc.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: play_next_radio(ctx))


def chooseSong():
    try:
        with open("./radioPlaylist.json", "r", encoding="utf-8") as file:
            data = json.load(file) 
            m=Musique(random.choice(data)['url'])
            return m
    except:
        data = []
        print("ok")

    

@bot.command()
async def startRadio(ctx:Context):
    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name="General")
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice: #voice vaut Null si le bot n'était pas dans le channel
        await voiceChannel.connect()
    else:
        # await ctx.send("Le bot est déjà là.")
        pass


    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        
    if not voice.is_playing():
        play_next_radio(ctx)
        await ctx.send("Lancement de la radio !")
    else:
        await ctx.send("Le bot est déjà en train de jouer de la musique.")
    
    
def downloadSong(song):
    song_there = os.path.isfile("song.mp3")   

    try:
        if song_there:
            os.remove("song.mp3")
    except PermissionError:
        pass 

    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        ydl.download([song.url])

    for file in os.listdir("./"):   
        if file.endswith(".mp3"):
            os.rename(file, "song.mp3")

@bot.command()
async def blindtest(ctx:Context): #test blindtest : joue une seule chanson pendant 30 secondes parmi la liste des chansons
    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name="General")
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice: #voice vaut Null si le bot n'était pas dans le channel
        await voiceChannel.connect()
    else:
        # await ctx.send("Le bot est déjà là.")
        pass

    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        
    if not voice.is_playing():

        embedVar = discord.Embed(title=f"LANCEMENT !!!! C'EST PARTI !!!!", color=0x00ff00)
        blindTest['on'] = True
        blindTest['joueurs'].append({"nom":ctx.author.name, "points":0, "dejaRepTitre":False, "dejaRepArtiste":False})
        message = await ctx.send(embed=embedVar)
        await displayLeaderboard(ctx)
        play_next_blindtest(ctx, message)
        
    else:
        await ctx.send("Le bot est déjà en train de jouer de la musique.")


def play_next_blindtest(ctx:Context, message):
    #pas de queue dans la radio, on choisit une musique random et on la joue
    for p in blindTest["joueurs"]:
        p["dejaRepTitre"]=False
        p["dejaRepArtiste"]=False
    
    jsonfile="blindtestPlaylist2.json"
    chosenSong = chooseSongFromJson(jsonfile)
    while not isAllowed(chosenSong.url):
            chosenSong = chooseSongFromJson(jsonfile)

    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    downloadSong(chosenSong)

    asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=chosenSong.videoName)), bot.loop)
    
    startTimerBT(ctx, 40, message, chosenSong)

    vc.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: play_next_blindtest(ctx, message))
    blindTest['chansonBlindTest'] = chosenSong

    def skipBlindTest():
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        voice.stop()
        blindTest['chansonBlindTest'] = None

    Timer(40, skipBlindTest).start()
    #time.sleep(20) #compter le temps de dl dedans
    #voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    #voice.stop()
def chooseSongFromJson(jsonfile:str):
    try:
        with open("./"+jsonfile, "r") as file:
            data=json.load(file)
            choix=random.choice(data)
            print(choix)
            m=Musique(choix['url'],choix['titre'], choix['artistes'])
            return m
    except:
        data=[]
        return -1

def startTimerBT(ctx:Context,max:int, message, chosenSong):
    def incrementEmbed(*args): 
        if args[1] == True:
            newEmbedVar = discord.Embed(title=f"C'est fini !", color=0x00ff00)
            newEmbedVar.add_field(name="Chanteur", value=f"{', '.join(args[3].artists)}")
            newEmbedVar.add_field(name="Titre", value=f"{args[3].title}")
            asyncio.run_coroutine_threadsafe(args[2].edit(embed=newEmbedVar), bot.loop)
        else:
            newEmbedVar = discord.Embed(title=f"Quelle est cette musique ? {args[0]}", description="Vous gagnez un point pour le titre et un point pour l'artiste.", color=0x00ff00)
            asyncio.run_coroutine_threadsafe(args[2].edit(embed=newEmbedVar), bot.loop)

    for i in range(max-1):
        Timer(i+1, incrementEmbed, (str(i+1), False, message, chosenSong)).start()
    Timer(max, incrementEmbed, (str(max), True, message, chosenSong)).start()
    
@bot.event
async def on_message(message: Message):
    if isinstance(message.channel, DMChannel):
        #print(message.content)  
        #print(message.channel.type)
        #print(blindTest)
        if blindTest['on']:
            if not joueurDansLaPartie(message.author.name) and message.author.name!="La Radio" :
                blindTest["joueurs"].append({"nom":message.author.name, "points":0, "dejaRepTitre":False, "dejaRepArtiste":False})
                print(blindTest["joueurs"])
            checkAnswer(message, blindTest['chansonBlindTest'], 0.9)
    else: 
        await bot.process_commands(message)

def joueurDansLaPartie(nomJoueur:str):
    for joueur in blindTest["joueurs"]:
        if joueur["nom"]==nomJoueur:
            return True
    return False

def getJoueurPartie(nomJoueur:str):
    for joueur in blindTest["joueurs"]:
        if joueur["nom"]==nomJoueur:
            return joueur
    return {}

def checkAnswer(message:Message, music:Musique, pourcent):
    answer=message.content
    # titre = music.title.lower()
    # artistes = [artiste.lower() for artiste in music.artists]
    
    # answer_split = answer.split(" ")


    # Titre = AH SI TU SAVAIS FERMER TA GUEULE
    # String = Ah si tu savais fermer // FAUX
    #  SString = Ah si tu savais fermer ta gueule PATRICK SEBASTIEN // TRUE 2 points

    # test = answer.lower().split(titre)
    

    if goodTitle(answer, music, pourcent) and not getJoueurPartie(message.author.name)["dejaRepTitre"]:
        asyncio.run_coroutine_threadsafe(message.author.send("Bravo c'est le bon titre"), bot.loop)
        getJoueurPartie(message.author.name)["dejaRepTitre"]=True
        getJoueurPartie(message.author.name)["points"]+=1
        asyncio.run_coroutine_threadsafe(updateLeaderboard(), bot.loop)
    if goodArtist(answer, music, pourcent) and not getJoueurPartie(message.author.name)["dejaRepArtiste"]:
       asyncio.run_coroutine_threadsafe(message.author.send("Bravo c'est le bon artiste"), bot.loop)
       getJoueurPartie(message.author.name)["dejaRepArtiste"]=True
       getJoueurPartie(message.author.name)["points"]+=1
       asyncio.run_coroutine_threadsafe(updateLeaderboard(), bot.loop)
    print(blindTest["joueurs"])

def goodTitle(answer:str, music:Musique, pourcent):
    return valideReponse(music.title, answer, pourcent)
            


    
def goodArtist(answer:str, music:Musique, pourcent):
    artistes=music.artists
    artistes=" ".join(artistes)
    return valideReponse(artistes, answer, pourcent)


async def displayLeaderboard(ctx):
    joueurs=[]
    for i,d in enumerate(blindTest["joueurs"]):
        joueurs.append(str(i+1)+". "+d["nom"]+" "+str(d["points"]))
    description="\n".join(joueurs)
    embed = discord.Embed(title=f"Classement",description=description, color=0x00ff00)
    blindTest["embedLeaderboard"] = await ctx.send(embed=embed)
    

async def updateLeaderboard():
    embedMessage = blindTest["embedLeaderboard"]

    joueurs=[]
    sortedList = sorted(blindTest["joueurs"], key=lambda x: x['points'], reverse=True)

    for i,d in enumerate(sortedList):
        joueurs.append(str(i+1)+". "+d["nom"]+" "+str(d["points"]))
    description="\n".join(joueurs)

    newEmbed=discord.Embed(title=f"Classement",description=description, color=0x00ff00)
    print(description)
    await embedMessage.edit(embed=newEmbed)




if __name__=="__main__":
    bot.run(TOKEN)


#Attention : michel berger - La groupie du pianiste (remasterisé en 2002)
