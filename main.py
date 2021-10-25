import discord
from discord.ext import commands
from discord.ext.commands.context import Context

#import youtube_dl
import yt_dlp

import os
import asyncio

from googleapiclient.discovery import build

from deletemp3 import truncate as removeMP3s

TOKEN = "OTAxODk5MTEwMzM0OTk2NTYw.YXWlAA.cPog94xte8jGzCZTnXTYPV2JWHA"
YT_API_KEY = "AIzaSyA_DWGx66IOUZryUtUH9fXdDJ1JO9WA0H8"

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
# id="PLlv1wuE2aMi__xQcsEiBimc_4qZQyQW8Z" #id de cette vidéo
# playlistId="PLlv1wuE2aMi__xQcsEiBimc_4qZQyQW8Z" #id de la playlist complete
# request=youtube.playlistItems().list(
#         part="snippet",
#         id=id,
#         maxResults="50")
# response = request.execute()
# print(response)

#fin tests

@bot.event
async def on_ready():
    removeMP3s()
    print("Le bot est prêt !")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="vos instructions"))
    await bot.user.edit(nick="test")

def addPlaylistToQueue(url:str):
    plid = url.split("playlist?list=",1)[1]
    print(plid) 
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

@bot.command()
async def play(ctx:Context, url:str, channel:str = "General"):
    if not any(url.startswith(YT_LINK) for YT_LINK in YOUTUBE_LINKS):
        await ctx.send("Ce n'est pas un lien Youtube !")
        return
    
    if "playlist?list" in url: #on a mis une playlist
        await ctx.send("Eeeet zééééparti pour la playlist")
        addPlaylistToQueue(url)
    elif "&list" in url:  #on a mis une seule musique mais elle a une playlist dans le lien
        queue.append(Musique(url.split("&list")[0])) 
    else: 
        queue.append(Musique(url))

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
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if len(queue) == 0:
        if vc is None:
            return

        if not vc.is_playing():
            asyncio.run_coroutine_threadsafe(ctx.send("No more songs in queue."), bot.loop)
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

    asyncio.run_coroutine_threadsafe(bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=queue[0].videoName)), bot.loop)
    
    del queue[0]
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
    message = await bot.wait_for("message")    
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


bot.run(TOKEN)
