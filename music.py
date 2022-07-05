from asyncio.tasks import current_task
import discord
from discord import emoji
import lavalink
import functions
from discord import utils
import asyncio
from decouple import config
from discord.ext import commands
from lavalink.events import TrackEndEvent
import re
import math
import mysql.connector
import threading

url_rx = re.compile(r'https?://(?:www\.)?.+')

class LavalinkVoiceClient(discord.VoiceClient):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        # ensure there exists a client already
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(
                    config("LLIP"),
                    2333,
                    config("LLPASS"),
                    'aus',
                    'default-node',
                    3600)
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

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = True, self_mute: bool = False) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        # ensure there is a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_deaf=self_deaf, self_mute=self_mute)

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
        self.channel_id = 0
        self.message_id = 0
        self.table = config('MYSQLTB')
        self.music_button_view = self.music_button_view()

        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(config("LLIP"), 2333, config("LLPASS"), 'aus', 'default-node', 3600)  # Host, Port, Password, Region, Name

        lavalink.add_event_hook(self.track_hook)

    class music_button_view(discord.ui.View):
        def __init__(self):
            super().__init__(timeout = None)
        
            self.add_item(self.PauseButton())
            self.add_item(self.StopButton())
            self.add_item(self.SkipButton())
            self.add_item(self.LoopButton())
            self.add_item(self.ShuffleButton())

        class PauseButton(discord.ui.Button['pause']):
            def __init__(self):
                super().__init__(style=discord.ButtonStyle.green, label="▶")

            async def callback(self, interaction: discord.Interaction):
                await Music.pause(self, interaction)

        class StopButton(discord.ui.Button['stop']):
            def __init__(self):
                super().__init__(style=discord.ButtonStyle.green, label="⬜")

            async def callback(self, interaction: discord.Interaction):
                await Music.disconnect(interaction)

        class SkipButton(discord.ui.Button['skip']):
            def __init__(self):
                super().__init__(style=discord.ButtonStyle.green, label="▶▶|")

            async def callback(self, interaction: discord.Interaction):
                await Music.skip(interaction)

        class LoopButton(discord.ui.Button['loop']):
            def __init__(self):
                super().__init__(style=discord.ButtonStyle.green, label="🔁")

            async def callback(self, interaction: discord.Interaction):
                await Music.loop(interaction)

        class ShuffleButton(discord.ui.Button['shuffle']):
            def __init__(self):
                super().__init__(style=discord.ButtonStyle.green, label="🔀")

            async def callback(self, interaction: discord.Interaction):
                await Music.shuffle(interaction)


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
        
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            player = self.bot.lavalink.player_manager.create(ctx.guild.id)
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
        player = self.bot.lavalink.player_manager.create(ctx.guild.id)
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
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient, self_deaf=True)
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

        elif isinstance(event, lavalink.events.TrackStartEvent):
            player = event.player
            await self.update_embed(player)

    async def update_embed(self, player):
        prefix = config("PREFIX")
        guild_id = str(player.guild_id)
        channel_id = 0
        message_id = 0

        mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
        )
        db = mydb.cursor()

        sql = "SELECT * FROM " + self.table + " WHERE guild_id = %s"
        val = (guild_id,)
        db.execute(sql, val)

        result = db.fetchall()
        
        if len(result) > 0:
          for x in result:
            channel_id = x[2]
            message_id = x[3]

        channel = await self.bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)
        if not player.is_connected or not player.is_playing:
            embed = discord.Embed(title = "No song currently playing ", color = int(config('COLOUR'), 16))
            embed.add_field(name="Queue: ", value="Empty")
            embed.add_field(name="Status: ", value="Idle")
            embed.set_image(url=config("BKG_IMG"))
            embed.set_footer(text="Other commands: " + prefix +"mv, " + prefix + "rm, " + prefix + "dc, " + prefix + "q, " + prefix + "np, " + prefix + "seek, " + prefix + "vol")
            await message.edit(content="To add a song join voice, and type song or url here",embed=embed, view=self.music_button_view)
            return
        else:
            identifier = player.current.identifier
            currentSong = player.current
            queue = player.queue
            embed = discord.Embed(title = "Playing: " + currentSong.title + " [" + lavalink.format_time(player.current.duration) + "]", url=currentSong.uri, color = int(config('COLOUR'), 16))
            thumbnail = "https://i.ytimg.com/vi/" + identifier + "/hqdefault.jpg"

            if len(queue) == 0:
                qDesc ='Empty'
            else:
                qDesc =''
                if len(queue) > 8:
                    for i, song in enumerate(queue[0:8]):
                        qDesc += f'[{str(i + 1) + ". " + song.title + " [" + lavalink.format_time(song.duration) + "]"}]({song.uri})' + '\n'
                    offset = len(queue) - 8
                    qDesc += "and " + str(offset) + " more track(s)\n"
                else:
                    for i, song in enumerate(queue):
                        qDesc += f'[{str(i + 1) + ". " + song.title + " [" + lavalink.format_time(song.duration) + "]"}]({song.uri})' + '\n'
            
            if player.paused:
                status = "Paused\n"
            else:
                status = "Playing\n"
            
            if player.repeat:
                status += " 🔁"
            
            if player.shuffle:
                status += "  🔀"
            
            embed.set_image(url=thumbnail)
            embed.add_field(name="Queue: ", value=qDesc, inline=True)
            embed.add_field(name="Status: ", value=status)
            embed.set_footer(text="Other commands: " + prefix +"mv, " + prefix + "rm, " + prefix + "dc, " + prefix + "q, " + prefix + "np, " + prefix + "seek, " + prefix + "vol")
            await message.edit(embed=embed, view=self.music_button_view)

    def check_conditions(self, ctx, player):
        if not player.is_connected:
            # We can't do, if we're not connected.
            return False

        if not player.is_playing:
            # We can't do if nothing is playing.
            return False

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return False
        return True

    def music_ch_check(self, ctx):
        if not ctx.channel.id == self.channel_id:
            return False
        return True

    ### MEDIA CONTROL FUNCTIONS ###

    async def pause(self, ctx):
      """ Pauses/Unpauses current song """
      player = lavalink.player_manager.get(ctx.guild.id)

      if not self.check_conditions(ctx, player): 
          return
      elif not self.music_ch_check(ctx):
            channel = await self.bot.fetch_channel(self.channel_id)
            msg = await ctx.send('Please use this command in ' + channel.mention)
            await asyncio.sleep(1)
            await msg.delete()
            return
      
      await self.update_embed(player)

    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        guild_id = ctx.guild.id

        self.mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
        )
        self.db = self.mydb.cursor()
  
        sql = "SELECT * FROM " + self.table + " WHERE guild_id = %s"
        val = (guild_id,)
        self.db.execute(sql, val)
  
        result = self.db.fetchall()
        
        if len(result) > 0:
          for x in result:
            self.channel_id = x[2]
            self.message_id = x[3]

        if not self.music_ch_check(ctx):
            channel = await self.bot.fetch_channel(self.channel_id)
            msg = await ctx.send('Please use this command in ' + channel.mention)
            await asyncio.sleep(1)
            await msg.delete()
            return

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            msg = await ctx.send('Not connected.')
            await asyncio.sleep(1)
            return await msg.delete()

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            msg = await ctx.send('You\'re not in my voicechannel!')
            await asyncio.sleep(1)
            return await msg.delete()

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.voice_client.disconnect(force=True)
        msg = await ctx.send('Disconnected.')
        await asyncio.sleep(1)
        await msg.delete()
        await self.update_embed(player)  

    async def skip(self, ctx):
        """ Skips the current song """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not self.check_conditions(ctx, player): 
          return
        elif not self.music_ch_check(ctx):
            channel = await self.bot.fetch_channel(self.channel_id)
            msg = await ctx.send('Please use this command in ' + channel.mention)
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

    async def loop(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not self.check_conditions(ctx, player): 
            return
        elif not self.music_ch_check(ctx):
            channel = await self.bot.fetch_channel(self.channel_id)
            msg = await ctx.send('Please use this command in ' + channel.mention)
            await asyncio.sleep(1)
            await msg.delete()
            return

        player.repeat = not player.repeat
        await self.update_embed(player)
        if player.repeat:
            embed = functions.discordEmbed(None, "Queue is on loop", int(config('COLOUR'), 16))
        else:
            embed = functions.discordEmbed(None, "Queue no longer looped", int(config('COLOUR'), 16))    
        msg = await ctx.message.channel.send(embed=embed)
        await asyncio.sleep(1)
        await msg.delete()

    async def shuffle(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        
        if not self.check_conditions(ctx, player): 
            return
        elif not self.music_ch_check(ctx):
            channel = await self.bot.fetch_channel(self.channel_id)
            msg = await ctx.send('Please use this command in ' + channel.mention)
            await asyncio.sleep(1)
            await msg.delete()
            return

        player.shuffle = not player.shuffle
        await self.update_embed(player)
        if player.shuffle:
            embed = functions.discordEmbed(None, "Queue will now be shuffled", int(config('COLOUR'), 16))
        else:
            embed = functions.discordEmbed(None, "Queue will no longer be shuffled", int(config('COLOUR'), 16))    
        msg = await ctx.message.channel.send(embed=embed)
        await asyncio.sleep(1)
        await msg.delete()

    def get_sec(self, time_str :str):
        """Get Seconds from time."""
        seconds= 0
        for part in time_str.split(':'):
            seconds= seconds*60 + int(part, 10)
        return seconds


    @commands.Cog.listener()
    async def on_message(self, message):
      client = self.bot

      async def del_msg(message):
        await asyncio.sleep(0.5)
        await message.delete()
      
      # So the bot doesn't react to its own messages.
      if message.author == client.user:
        return

      self.mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
        )
      self.db = self.mydb.cursor()

      guild_id = message.guild.id

      sql = "SELECT * FROM " + self.table + " WHERE guild_id = %s"
      val = (guild_id,)
      self.db.execute(sql, val)

      result = self.db.fetchall()
      
      if len(result) > 0:
        for x in result:
          self.channel_id = x[2]
          self.message_id = x[3]

          if message.channel.id == self.channel_id:
          
            if not message.content.startswith(config('PREFIX')):
                ctx = await client.get_context(message)
                asyncio.get_event_loop().create_task(del_msg(message))
                ctx.command = client.get_command('play')
                await self.cog_before_invoke(ctx)
                await ctx.invoke(client.get_command('play'), query=message.content)
            else:
              await del_msg(message)

    @commands.command()
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        if not self.music_ch_check(ctx):
            channel = await self.bot.fetch_channel(self.channel_id)
            msg = await ctx.send('Please use this command in ' + channel.mention)
            await asyncio.sleep(1)
            await msg.delete()
            return

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
        await self.update_embed(player)
        await asyncio.sleep(0.2)
        await msg.delete()
        # We don't want to call .play() if the player is playing as that will effectively skip
        # the current track.
        if not player.is_playing:
            await player.play()
           


    @commands.command(aliases=['rm'])
    async def remove(self, ctx, index: int):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        guild_id = ctx.guild.id

        self.mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
        )
        self.db = self.mydb.cursor()

        sql = "SELECT * FROM " + self.table + " WHERE guild_id = %s"
        val = (guild_id,)
        self.db.execute(sql, val)

        result = self.db.fetchall()
        
        if len(result) > 0:
          for x in result:
            self.channel_id = x[2]
            self.message_id = x[3]
        
        if not self.check_conditions(ctx, player): 
            return
        elif not self.music_ch_check(ctx):
            channel = await self.bot.fetch_channel(self.channel_id)
            msg = await ctx.send('Please use this command in ' + channel.mention)
            await asyncio.sleep(0.5)
            await msg.delete()
            return

        if index > len(player.queue) or index < 1:
            msg = await ctx.send('Index has to be >=1 and <=queue size')
            await self.update_embed(player)
            await asyncio.sleep(0.5)
            return await msg.delete()

        index = index - 1
        removed = player.queue.pop(index)
        await self.update_embed(player)
        embed = functions.discordEmbed("Removed", removed.title +' from the queue' , int(config('COLOUR'), 16))
        msg = await ctx.message.channel.send(embed=embed)
        await asyncio.sleep(1)
        await msg.delete() 

    @commands.command(aliases=['q'])
    async def queue(self, ctx, page : int=1):
      """ The Queue """
      player = self.bot.lavalink.player_manager.get(ctx.guild.id)

      guild_id = ctx.guild.id

      self.mydb = mysql.connector.connect(
        host = config("MYSQLIP"),
        user = config("MYSQLUSER"),
        password = config("MYSQLPASS"),
        database = config("MYSQLDB")
      )
      self.db = self.mydb.cursor()

      sql = "SELECT * FROM " + self.table + " WHERE guild_id = %s"
      val = (guild_id,)
      self.db.execute(sql, val)

      result = self.db.fetchall()
      
      if len(result) > 0:
        for x in result:
          self.channel_id = x[2]
          self.message_id = x[3]

      if not self.check_conditions(ctx, player): 
            return
      elif not self.music_ch_check(ctx):
            channel = await self.bot.fetch_channel(self.channel_id)
            msg = await ctx.send('Please use this command in ' + channel.mention)
            await asyncio.sleep(1)
            await msg.delete()
            return
    
      queue = player.queue

      if len(queue) == 0:
            msg = await ctx.send('No songs in queue | Why not queue something?')
            await self.update_embed(player)
            await asyncio.sleep(1)
            await msg.delete()
            return
      
      qDesc = ''

      items_per_page = 10
      pages = math.ceil(len(player.queue) / items_per_page)

      start = (page - 1) * items_per_page
      end = start + items_per_page

      for i, song in enumerate(queue[start:end], start=start):
          qDesc += f'[{str(i + 1) + ". " + song.title}]({song.uri})' + '\n'
          
    
      embed = functions.discordEmbed("Queue", qDesc, int(config('COLOUR'), 16))
      embed.set_footer(text=f'Viewing Page {page}/{pages}')
      msg = await ctx.message.channel.send(embed=embed)
      await self.update_embed(player)
      await asyncio.sleep(3)
      await msg.delete()

    @commands.command(aliases=['mv'])
    async def move(self, ctx, current: int, new: int):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        guild_id = ctx.guild.id

        self.mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
        )
        self.db = self.mydb.cursor()
  
        sql = "SELECT * FROM " + self.table + " WHERE guild_id = %s"
        val = (guild_id,)
        self.db.execute(sql, val)
  
        result = self.db.fetchall()
        
        if len(result) > 0:
          for x in result:
            self.channel_id = x[2]
            self.message_id = x[3]
        
        if not self.check_conditions(ctx, player): 
            return
        elif not self.music_ch_check(ctx):
            channel = await self.bot.fetch_channel(self.channel_id)
            msg = await ctx.send('Please use this command in ' + channel.mention)
            await asyncio.sleep(1)
            await msg.delete()
            return

        current = current - 1
        new = new - 1

        if current > len(player.queue)-1 or current < 0:
            msg = await ctx.send('Current index out of bounds')
            await self.update_embed(player)
            await asyncio.sleep(1)
            return await msg.delete()
        
        if new > len(player.queue)-1 or new < 0:
            msg = await ctx.send('New index out of bounds')
            await self.update_embed(player)
            await asyncio.sleep(1)
            return await msg.delete()

        player.queue.insert(new, player.queue.pop(current))
        moved = player.queue[new]
        await self.update_embed(player)
        embed = functions.discordEmbed("Moved ", moved.title +' moved from ' + str(current + 1) + " to " + str(new + 1) , int(config('COLOUR'), 16))
        msg = await ctx.message.channel.send(embed=embed)
        await asyncio.sleep(1)
        await msg.delete()

    @commands.command(aliases=['np', 'n'])
    async def now(self, ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        guild_id = ctx.guild.id

        self.mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
        )
        self.db = self.mydb.cursor()
  
        sql = "SELECT * FROM " + self.table + " WHERE guild_id = %s"
        val = (guild_id,)
        self.db.execute(sql, val)
  
        result = self.db.fetchall()
        
        if len(result) > 0:
          for x in result:
            self.channel_id = x[2]
            self.message_id = x[3]
            
        if not self.check_conditions(ctx, player): 
            return
        elif not self.music_ch_check(ctx):
            channel = await self.bot.fetch_channel(self.channel_id)
            msg = await ctx.send('Please use this command in ' + channel.mention)
            await asyncio.sleep(1)
            await msg.delete()
            return

        song = 'Nothing'

        if player.current:
            pos = lavalink.format_time(player.position)
            if player.current.stream:
                dur = 'LIVE'
            else:
                dur = lavalink.format_time(player.current.duration)
            song = f'**[{player.current.title}]({player.current.uri})**\n({pos}/{dur})'

        embed = discord.Embed(color= int(config('COLOUR'), 16), title='Now Playing', description=song)
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command()
    async def seek(self, ctx, time):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        guild_id = ctx.guild.id

        self.mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
        )
        self.db = self.mydb.cursor()
  
        sql = "SELECT * FROM " + self.table + " WHERE guild_id = %s"
        val = (guild_id,)
        self.db.execute(sql, val)
  
        result = self.db.fetchall()
        
        if len(result) > 0:
          for x in result:
            self.channel_id = x[2]
            self.message_id = x[3]

        if not self.check_conditions(ctx, player):
            return
        elif not self.music_ch_check(ctx):
            channel = await self.bot.fetch_channel(self.channel_id)
            msg = await ctx.send('Please use this command in ' + channel.mention)
            await asyncio.sleep(1)
            await msg.delete()
            return

        time_sec = self.get_sec(str(time))

        if not time_sec:
            return await ctx.send('You need to specify a time to skip to')

        time_ms = time_sec * 1000

        await player.seek(time_ms)

        msg = await ctx.send(f'Moved track to **{lavalink.format_time(time_ms)}**')
        await asyncio.sleep(1)
        await msg.delete()

    @commands.command(aliases=['vol'])
    async def volume(self, ctx, volume: int=None):
        guild_id = ctx.guild.id
  
        self.mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
        )
        self.db = self.mydb.cursor()
  
        sql = "SELECT * FROM " + self.table + " WHERE guild_id = %s"
        val = (guild_id,)
        self.db.execute(sql, val)
  
        result = self.db.fetchall()
        
        if len(result) > 0:
          for x in result:
            self.channel_id = x[2]
            self.message_id = x[3]
            
        if ctx.author.guild_permissions.administrator: 
            player = self.bot.lavalink.player_manager.get(ctx.guild.id)
            if not self.check_conditions(ctx, player):
                return
            elif not self.music_ch_check(ctx):
                channel = await self.bot.fetch_channel(self.channel_id)
                msg = await ctx.send('Please use this command in ' + channel.mention)
                await asyncio.sleep(1)
                await msg.delete()
                return

            if volume is None:
              msg = await ctx.send(f'🔈 | {player.volume}%')
              await asyncio.sleep(1)
              return await msg.delete()
              
            if volume > 1000:
                msg = await ctx.send(f'Too large')
                await asyncio.sleep(1)
                return await msg.delete()

            await player.set_volume(volume)
            msg = await ctx.send(f'🔈 | Set to {player.volume}%')
            await asyncio.sleep(1)
            await msg.delete()
        else:
            msg = await ctx.send(f'You do not have the permissions to use this command')
            await asyncio.sleep(1)
            await msg.delete()


    @commands.command()
    async def update(self,ctx):
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        guild_id = ctx.guild.id
    
        self.mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
        )
        self.db = self.mydb.cursor()
  
        sql = "SELECT * FROM " + self.table + " WHERE guild_id = %s"
        val = (guild_id,)
        self.db.execute(sql, val)
  
        result = self.db.fetchall()
        
        if len(result) > 0:
          for x in result:
            self.channel_id = x[2]
            self.message_id = x[3]
            
        await self.update_embed(player)
    
async def setup(bot):
    await bot.add_cog(Music(bot))