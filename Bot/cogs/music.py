"""
This example cog demonstrates basic usage of Lavalink.py, using the DefaultPlayer.
As this example primarily showcases usage in conjunction with discord.py, you will need to make
modifications as necessary for use with another Discord library.
Usage of this cog requires Python 3.6 or higher due to the use of f-strings.
Compatibility with Python 3.5 should be possible if f-strings are removed.
"""
from asyncio.tasks import current_task
import re

import discord
import lavalink
import functions
import asyncio
from decouple import config
from discord.ext import commands
from lavalink.events import TrackEndEvent

url_rx = re.compile(r'https?://(?:www\.)?.+')


class LavalinkVoiceClient(discord.VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    https://discordpy.readthedocs.io/en/latest/api.html#voiceprotocol
    """

    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        # ensure there exists a client already
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(
                    'localhost',
                    2333,
                    'youshallnotpass',
                    'aus',
                    'default-node')
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
                't': 'VOICE_SERVER_UPDATE',
                'd': data
                }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
                't': 'VOICE_STATE_UPDATE',
                'd': data
                }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        # ensure there is a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel)

    async def disconnect(self, *, force: bool) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that
        # would set channel_id to None doesn't get dispatched after the 
        # disconnect
        player.channel_id = None
        self.cleanup()


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.id = int(config('MUSIC_CHANNEL_MSG_ID'))

        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'eu', 'default-node')  # Host, Port, Password, Region, Name

        lavalink.add_event_hook(self.track_hook)
        lavalink.add_event_hook(self.track_hook_end)

    @commands.Cog.listener()
    async def on_ready(self):
        print('\033[92m' + 'General Loaded' + '\033[0m')

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            await self.ensure_voice(ctx)
            #  Ensure that the bot and command author share a mutual voicechannel.

        return guild_check

    async def update_embed(self, player):
        channel = await self.bot.fetch_channel(int(config('MUSIC_CHANNEL_ID')))
        message = await channel.fetch_message(int(config('MUSIC_CHANNEL_MSG_ID')))
        if not player.is_connected or not player.is_playing:
            embed = functions.discordEmbed("No song playing currently", "Status: ", int(config('COLOUR'), 16))
            await message.edit(content="Queue: ",embed=embed)
            return
        else:
            queue = player.queue

            if len(queue) == 0:
                qDesc ='Queue: '
            else:
                qDesc ='Queue: \n'
                for i, song in enumerate(queue):
                    qDesc += str(i + 1) + ". " + song.title + '\n'
            
            if player.paused:
                status = "Status: Paused"
            else:
                status = "Status: Playing"

            currentSong = player.current
            title = 'Playing: ' + f'[{currentSong.title}]({currentSong.uri})'

            embed = functions.discordEmbed(title, status, int(config('COLOUR'), 16))
            await message.edit(content=qDesc, embed=embed)
        
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            player = self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
            msg = await ctx.send(error.original)
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a voicechannel" etc. You can modify the above
            # if you want to do things differently.

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        # Create returns a player if one exists, otherwise creates.
        # This line is important because it ensures that a player always exists for a guild.

        # Most people might consider this a waste of resources for guilds that aren't playing, but this is
        # the easiest and simplest way of ensuring players are created.

        # These are commands that require the bot to join a voicechannel (i.e. initiating playback).
        # Commands such as volume/skip etc don't require the bot to be in a voicechannel so don't need listing here.
        should_connect = ctx.command.name in ('play',)

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Our cog_command_error handler catches this and sends it to the voicechannel.
            # Exceptions allow us to "short-circuit" command invocation via checks so the
            # execution state of the command goes no further.
            raise commands.CommandInvokeError('Join a voicechannel first.')

        if not player.is_connected:
            if not should_connect:
                raise commands.CommandInvokeError('Not connected.')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')

            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CommandInvokeError('You need to be in my voicechannel.')

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the voicechannel.
            guild_id = int(event.player.guild_id)
            guild = self.bot.get_guild(guild_id)
            await self.update_embed(event.player)
            await guild.voice_client.disconnect(force=True)

    async def track_hook_end(self, event):
        if isinstance(event, lavalink.events.TrackEndEvent):
            player = event.player
            await self.update_embed(player)



    @commands.Cog.listener()
    async def on_message(self, message):
      client = self.bot
      # So the bot doesn't react to its own messages.
      if message.author == client.user:
        return
      
      if message.channel.id == int(config('MUSIC_CHANNEL_ID')):
        await asyncio.sleep(0.5)
        await message.delete()
      #await client.process_commands(message)


    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        # Get the player for this guild from cache.
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
        query = query.strip('<>')

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
        # ALternatively, resullts['tracks'] could be an empty array if the query yielded no tracks.
        if not results or not results['tracks']:
            return await ctx.send('Nothing found!')

        embed = discord.Embed(color=discord.Color.blurple())

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']

            for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                player.add(requester=ctx.author.id, track=track)
            embed.title = 'Playlist Enqueued!'
            embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
            embed.color = (int(config('COLOUR'), 16))
        else:
            track = results['tracks'][0]
            embed.title = 'Track Enqueued'
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
            embed.color = (int(config('COLOUR'), 16))
            # You can attach additional information to audiotracks through kwargs, however this involves
            # constructing the AudioTrack class yourself.
            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)

        msg = await ctx.send(embed=embed)
        
        
        # We don't want to call .play() if the player is playing as that will effectively skip
        # the current track.
        if not player.is_playing:
            await player.play()
        
            
        await self.update_embed(player)
        await asyncio.sleep(1)
        await msg.delete()

    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            await self.update_embed(player)
            msg = await ctx.send('Not connected.')
            await self.update_embed(player)
            await asyncio.sleep(1)
            return await msg.delete()

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            await self.update_embed(player)
            msg = await ctx.send('You\'re not in my voicechannel!')
            await self.update_embed(player)
            await asyncio.sleep(1)
            return await msg.delete()

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.voice_client.disconnect(force=True)
        msg = await ctx.send('*⃣ | Disconnected.')
        await self.update_embed(player)
        await asyncio.sleep(1)
        await msg.delete()

    @commands.command(aliases=['s'])
    async def skip(self, ctx):
        #if ctx.author.guild_permissions.administrator:  
            """ Skips the current song """
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)

            if not player.is_connected:
                # We can't skip, if we're not connected.
                msg = await ctx.send('Not connected.')
                await self.update_embed(player)
                await asyncio.sleep(1)
                await msg.delete()
                return

            if not player.is_playing:
                # We can't skip if nothing is playing.
                msg = await ctx.send('No songs currently playing')
                await self.update_embed(player)
                await asyncio.sleep(1)
                await msg.delete()
                return

            if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
                # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
                # may not disconnect the bot.
                msg = await ctx.send('You\'re not in my voicechannel!')
                await self.update_embed(player)
                await asyncio.sleep(1)
                await msg.delete()
                
                return
            
            currentTrack = player.current
            #Skips current track
            await player.skip()
            await self.update_embed(player)

            embed = functions.discordEmbed("Skipped", currentTrack.title + " was skipped", int(config('COLOUR'), 16))
            msg = await ctx.message.channel.send(embed=embed)
            await asyncio.sleep(1)
            await msg.delete()
            

        #else:
        #    embed = functions.discordEmbed("Unauthorised", "Insufficient permissions", int(config('COLOUR'), 16))
        #    msg = await ctx.message.channel.send(embed=embed)
        #    await self.update_embed(player)
        #    await asyncio.sleep(2)
        #    await msg.delete()

        

    @commands.command(aliases=['||'])
    async def pause(self, ctx):
      """ Pauses/Unpauses current song """
      player = self.bot.lavalink.player_manager.get(ctx.guild.id)

      if not player.is_connected:
            # We can't skip, if we're not connected.
            msg = await ctx.send('Not connected.')
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            return

      if not player.is_playing:
            # We can't skip if nothing is playing.
            msg = await ctx.send('No songs currently playing')
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            return

      if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            msg = await ctx.send('You\'re not in my voicechannel!')
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            return

      if player.paused:
        await player.set_pause(False)
        await self.update_embed(player)
        embed = functions.discordEmbed(None, "Unpaused Song", int(config('COLOUR'), 16))
        msg = await ctx.message.channel.send(embed=embed)
        await asyncio.sleep(1)
        await msg.delete()
        return
      
      await player.set_pause(True)
      await self.update_embed(player)
      embed = functions.discordEmbed(None, "Paused Song", int(config('COLOUR'), 16))
      msg = await ctx.message.channel.send(embed=embed)
      await asyncio.sleep(1)
      await msg.delete()

    @commands.command(aliases=['||>'])
    async def unpause(self, ctx):
      """ Pauses/Unpauses current song """
      player = self.bot.lavalink.player_manager.get(ctx.guild.id)

      if not player.is_connected:
            # We can't skip, if we're not connected.
            msg = await ctx.send('Not connected.')
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            return

      if not player.is_playing:
            # We can't skip if nothing is playing.
            msg = await ctx.send('No songs currently playing')
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            return

      if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            msg = await ctx.send('You\'re not in my voicechannel!')
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            return

      if player.paused:
        await player.set_pause(False)
        await self.update_embed(player)
        embed = functions.discordEmbed(None, "Unpaused Song", int(config('COLOUR'), 16))
        msg = await ctx.message.channel.send(embed=embed)
        await asyncio.sleep(1)
        await msg.delete()
        
      
      embed = functions.discordEmbed(None, "Song already playing", int(config('COLOUR'), 16))
      msg = await ctx.message.channel.send(embed=embed)
      await self.update_embed(player)
      await asyncio.sleep(1)
      await msg.delete()

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
      """ The Queue """
      player = self.bot.lavalink.player_manager.get(ctx.guild.id)

      if not player.is_connected:
            # We can't skip, if we're not connected.
            msg = await ctx.send('Not connected.')
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            return

      if not player.is_playing:
            # We can't skip if nothing is playing.
            msg = await ctx.send('No songs currently playing')
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            return

      if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            msg = await ctx.send('You\'re not in my voicechannel!')
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            return
    
      queue = player.queue
      #queue = await lavalink.decode_tracks(queue)

      if len(queue) == 0:
            msg = await ctx.send('No songs in queue')
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            return
      
      qDesc = ''

      for i, song in enumerate(queue):
          qDesc += f'[{str(i + 1) + ". " + song.title}]({song.uri})' + '\n'
          
    
      embed = functions.discordEmbed("Queue", qDesc, int(config('COLOUR'), 16))
      msg = await ctx.message.channel.send(embed=embed)
      await self.update_embed(player)
      await asyncio.sleep(1)
      await msg.delete()

    @commands.command()
    async def update(self,ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        self.update_embed(player)

    @commands.command()
    async def setup(self, ctx):
        embed = functions.discordEmbed("No song playing currently", "Status: N/A", int(config('COLOUR'), 16))
        await ctx.message.channel.send("Queue: ",embed=embed)
        

            
def setup(bot):
    bot.add_cog(Music(bot))