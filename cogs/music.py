import discord
import os
import youtube_dl
from discord.ext import commands


class music(commands.Cog):
    def __init__(self, client):
        self.client = client

    connect = False

    # Plays music
    @commands.command()
    async def play(self, ctx, url: str):
        song_there = os.path.isfile("song.mp3")
        try:
            if song_there:
                os.remove("song.mp3")
        except PermissionError:
            await ctx.send("Wait for current music to end or use $stop command")
            return

        voiceChannel = discord.utils.get(ctx.guild.voice_channels, name='General')

        if self.connect == False:
            await voiceChannel.connect()
            self.connect = True

        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)

        ydl_opts = {
            'format':
            'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                os.rename(file, "song.mp3")

        voice.play(discord.FFmpegPCMAudio("song.mp3"))

    # Make bot dc
    @commands.command()
    async def leave(self, ctx):
        self.connect = False
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_connected():
            await voice.disconnect()
        else:
            await ctx.send("Not connected to VC")

    # Pauses music
    @commands.command()
    async def pause(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
        else:
            await ctx.send("No music currently playing")

    # Resumes music
    @commands.command()
    async def resume(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
        else:
            await ctx.send("Music already playing")

    # Stops music
    @commands.command()
    async def stop(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        voice.stop()


def setup(client):
    client.add_cog(music(client))
