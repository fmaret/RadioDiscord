import discord
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



TOKEN = getenv("TOKEN")
YT_API_KEY = getenv("YT_API_KEY")

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



'''
* Classes
'''

class Musique():
    def __init__(self, url):
        self.url = url

        request = youtube.videos().list(part="snippet", id=url.split("?v=",1)[1])
        response = request.execute()

        self.videoName = response['items'][0]['snippet']['title']
        


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

def addPlaylistToQueue(url:str): #return le nom de la playlist
    plid = url.split("playlist?list=",1)[1]
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=plid,
        maxResults="50")
    response = request.execute()

    liens = []

    for x in (response['items']):
        liens.append(x['snippet']['resourceId']['videoId'])
        

    for lien in liens:
        queue.append(Musique("https://www.youtube.com/watch?v="+lien))

    #Récupérer le nom de la playlist
    request=youtube.playlists().list(
        part="snippet",
        id=plid,
        maxResults="50")
    response = request.execute()
    return response['items'][0]['snippet']['title']

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
            asyncio.run_coroutine_threadsafe(ctx.send("La musique de merde qui fonctionne pas a été skip, ca nous aura pris 3h mais elle est skip juste pour pas que vous ayez a relancer la playlist depuis le depart.... Remerciez nous bande de merdes !"), bot.loop)
            # Hesite pas a mettre un autre message,xDDD tqt j'ai peaufiné la fin
            del queue[0]
            play_next(ctx)
            return

    if len(queue) > 1:
        del queue[0]

    for el in queue:
        print(el.videoName)

    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if len(queue) == 0:
        if vc is None:
            return

        if not vc.is_playing():
            asyncio.run_coroutine_threadsafe(ctx.send("Il n'y a plus de musique dans la queue."), bot.loop)
            asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="vos instructions")), bot.loop)
        return

    song_there = os.path.isfile("song.mp3")   

    try:
        if song_there:
            os.remove("song.mp3")
    except PermissionError:
        pass 

    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        ydl.download([queue[0].url])

    for file in os.listdir("./"):   
        if file.endswith(".mp3"):
            os.rename(file, "song.mp3")

    asyncio.run_coroutine_threadsafe(writeLyrics(ctx, queue[0]), bot.loop)
    asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=queue[0].videoName)), bot.loop)
    
    vc.play(discord.FFmpegPCMAudio("song.mp3"), after=lambda e: play_next(ctx))
    
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
    #play_next(ctx)

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
    
bot.run(TOKEN)

