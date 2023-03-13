import wavelink # The library used for lavalink
import asyncio # For asyncio.sleep()
import mysql.connector # To connect to music db
import datetime # Used to convert time from S to HH:MM:SS
import discord # Use discord components and embeds
import math # Used for create queue pages
import functions # Used for embed function
import random # Used for shuffle selection song index

from discord import app_commands # Used for slash commands
from decouple import config # For .env vars
from discord.ext import commands # To use command tree structure

botColour = config("COLOUR")
botColourInt = int(botColour, 16) # Colour to be used on embeds

class Music(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot):
        self.bot = bot
        self.id = int(config('MUSIC_CHANNEL_MSG_ID'))
        self.channel_id = 0
        self.message_id = 0
        self.table = config('MYSQLTB')

        bot.loop.create_task(self.connect_nodes())

    #### CLASSES FOR BUTTONS ####

    class music_button_view(discord.ui.View):
        def __init__(self, paused: bool = True, loop: int = 0, shuffle: int = 0, playing: bool = True):
            super().__init__(timeout = None)
            self.paused = paused
            self.loops = loop
            self.shuffle = shuffle
            self.playing = playing
        
            if playing:
                if self.paused:
                    self.add_item(Music.PauseButton("<:play:1084708670664880158>", discord.ButtonStyle.green))
                else:
                    self.add_item(Music.PauseButton("<:pause:1084703479114780724>", discord.ButtonStyle.danger))
            else:
                self.add_item(Music.PauseButton("<:play:1084708670664880158>", discord.ButtonStyle.danger))
            
            self.add_item(Music.StopButton())
            self.add_item(Music.SkipButton())
            
            if self.loops == 0:
                self.add_item(Music.LoopButton(discord.ButtonStyle.danger))
            elif self.loops == 1:
                self.add_item(Music.LoopButton(discord.ButtonStyle.green))
            else:
                self.add_item(Music.LoopButton(discord.ButtonStyle.blurple))
            
            if self.shuffle == 0:
                self.add_item(Music.ShuffleButton(discord.ButtonStyle.danger))
            else:
                self.add_item(Music.ShuffleButton(discord.ButtonStyle.green))

    class PauseButton(discord.ui.Button['pause']):
        def __init__(self, emoji : str, style):
            super().__init__(style=style, emoji=emoji)

        async def callback(self, interaction: discord.Interaction):
            ctx = await interaction.client.get_context(interaction.message)
            check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

            if check:
                await interaction.response.defer()
                vc: wavelink.Player = ctx.voice_client

                if vc.is_paused():
                    await vc.resume()
                else:
                    await vc.pause()
                
                await Music.update_embed(self, vc)

    class StopButton(discord.ui.Button['stop']):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.danger, emoji="<:stop:1084708262169034792>")

        async def callback(self, interaction: discord.Interaction):
            ctx = await interaction.client.get_context(interaction.message)

            check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

            if check:
                await interaction.response.defer()
                vc: wavelink.Player = ctx.voice_client
                vc.queue.clear()
                await Music.reset_embed(self, vc)
                await vc.disconnect()


    class SkipButton(discord.ui.Button['skip']):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.danger, emoji="<:skip:1084707456975908908>")
            
        async def callback(self, interaction: discord.Interaction):
            ctx = await interaction.client.get_context(interaction.message)

            check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

            if check:
                await interaction.response.defer()
                vc: wavelink.Player = ctx.voice_client
                end = vc.track.duration
                await vc.seek(end*1000)

    
    class LoopButton(discord.ui.Button['loop']):
        def __init__(self, style):
            super().__init__(style=style, emoji="<:loopeat:1084703648724033546>")

        async def callback(self, interaction: discord.Interaction):
            ctx = await interaction.client.get_context(interaction.message)
            check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

            if check:
                await interaction.response.defer()
                vc: wavelink.Player = ctx.voice_client

                result = await Music.connect_db(self, interaction.guild_id)

                if len(result) > 0:
                    for x in result:
                        loop = x[4]
                
                loop = loop + 1

                if loop > 2:
                    loop = 0

                self.mydb = await Music.db_connector(self)
                self.db = self.mydb.cursor()

                sql = "UPDATE " + config('MYSQLTB') + " SET loop_b = %s WHERE guild_id = %s"
                val = (loop, interaction.guild_id) 
                self.db.execute(sql, val)
                self.mydb.commit()
                self.db.close()
                self.mydb.close()

                await Music.update_embed(self, vc)


    class ShuffleButton(discord.ui.Button['shuffle']):
        def __init__(self, style):
            super().__init__(style=style, emoji="<:shuffle:1084703804995403806>")

        async def callback(self, interaction: discord.Interaction):
            ctx = await interaction.client.get_context(interaction.message)
            check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

            if check:
                await interaction.response.defer()
                vc: wavelink.Player = ctx.voice_client

                result = await Music.connect_db(self, interaction.guild_id)

                if len(result) > 0:
                    for x in result:
                        shuffle = x[5]

                if shuffle == 0:
                    shuffle = 1
                else:
                    shuffle = 0

                self.mydb = await Music.db_connector(self)
                self.db = self.mydb.cursor()
                    
                sql = "UPDATE " + config('MYSQLTB') + " SET shuffle_b = %s WHERE guild_id = %s"
                val = (shuffle, interaction.guild_id) 
                self.db.execute(sql, val)
                self.mydb.commit()
                self.db.close()
                self.mydb.close()
            
                await Music.update_embed(self, vc)

    #### GENERAL FUNCTIONS ####

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(bot=self.bot,
                                            host=config("LLIP"),
                                            port=2333,
                                            password=config("LLPASS"))
            
    # Checks thats conditions are right for interactions
    async def check_cond(self, ctx, interaction, player, author = None):
        if interaction is not None:
            result = await Music.connect_db(self, interaction.guild_id)
        else:
            result = await Music.connect_db(self, ctx.guild.id)

        if len(result) > 0:
          for x in result:
            channel_id = x[2]
            message_id = x[3]

        if (not ctx.voice_client or not player.is_connected()) and interaction is not None:
            embed = functions.discordEmbed("Failed Check", "Im not connected", botColourInt)
            await interaction.response.send_message(embed=embed, ephemeral = True, delete_after = (5))
            return False
        
        if interaction is not None:
            if not (
            (interaction.client.user.id in ctx.author.voice.channel.voice_states) and
            (interaction.user.id in ctx.author.voice.channel.voice_states)
            ):
                embed = functions.discordEmbed("Failed Check", 'You\'re not in my voice channel', botColourInt)
                await interaction.response.send_message(embed=embed, ephemeral = True, delete_after = (5))
                return False
            elif not ctx.author.voice:
                embed = functions.discordEmbed("Failed Check", 'You\'re not in a voice channel', botColourInt)
                await interaction.response.send_message(embed=embed, ephemeral = True, delete_after = (5))
                return False
            elif interaction.channel_id != channel_id:
                embed = functions.discordEmbed("Failed Check", 'Please use this command in the music channel', botColourInt)
                await interaction.response.send_message(embed=embed, ephemeral = True, delete_after = (5))
                return False
            return True
        else:
            if (ctx.author.voice is None):
                embed = functions.discordEmbed("Failed Check", 'You\'re not in a voice channel', botColourInt)
                msg = await ctx.send(embed=embed)
                await asyncio.sleep(2)
                await msg.delete()
                return False
            elif (not (self.bot.user.id in ctx.author.voice.channel.voice_states)) and (player is not None):
                embed = functions.discordEmbed("Failed Check", 'You\'re not in my voice channel', botColourInt)
                msg = await ctx.send(embed=embed)
                await asyncio.sleep(2)
                await msg.delete()
                return False
            return True
        
    # Deletes message
    async def del_msg(self, message):
        await asyncio.sleep(0.5)
        await message.delete()

    # Converts HH:MM:SS to seconds
    def get_sec(self, time_str :str):
        """Get Seconds from time."""
        seconds= 0
        for part in time_str.split(':'):
            seconds= seconds*60 + int(part, 10)
        return seconds

    # Connect to database
    async def db_connector(self):
        mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
        )

        return mydb

    # Connects to the database and returns inforamtion based on guild_id
    async def connect_db(self, guild_id : int):
        self.mydb = await Music.db_connector(self)
        self.db = self.mydb.cursor()

        sql = "SELECT * FROM " + config('MYSQLTB') + " WHERE guild_id = %s"
        val = (guild_id,)
        self.db.execute(sql, val)

        result = self.db.fetchall()

        self.db.close()
        self.mydb.close()

        return result

    # Resets the music embed to default state
    async def reset_embed(self, player):
        prefix = config("PREFIX")
        guild_id = str(player.guild.id)
        channel_id = 0
        message_id = 0

        result = await Music.connect_db(self, guild_id)
        
        if len(result) > 0:
          for x in result:
            channel_id = x[2]
            message_id = x[3]

        channel = player.client.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        embed = discord.Embed(title = "No song currently playing ", color = int(config('COLOUR'), 16))
        embed.add_field(name="Queue: ", value="Empty")
        embed.add_field(name="Status: ", value="Idle")
        embed.set_image(url=config("BKG_IMG"))
        embed.set_footer(text="Other commands: /mv, /rm, /dc, /q, /np, /seek, /vol")
        await message.edit(content="To add a song join voice, and type song or url here",embed=embed, view=Music.music_button_view(True, playing = False))

    # Updates the music embed to reflect whats in the player
    async def update_embed(self, player):
        prefix = config("PREFIX")
        guild_id = str(player.guild.id)
        channel_id = 0
        message_id = 0

        result = await Music.connect_db(self, guild_id)
        
        if len(result) > 0:
          for x in result:
            channel_id = x[2]
            message_id = x[3]
            loop = x[4]
            shuffle = x[5]

        channels = await player.guild.fetch_channels()

        for channeli in channels:
            if channeli.id == channel_id:
                channel = channeli
                break

        message = await channel.fetch_message(message_id)
        
        if not player.is_connected or not player.is_playing:
            Music.reset_embed(self,player)
            return
        else:
            currentSong = player.track
            identifier = currentSong.identifier
            queue = player.queue
            embed = discord.Embed(title = "Playing: " + currentSong.title + " [" + str(datetime.timedelta(seconds=currentSong.length)) + "]", url=currentSong.uri, color = int(config('COLOUR'), 16))
            thumbnail = "https://i.ytimg.com/vi/" + identifier + "/hqdefault.jpg"

            if queue.is_empty:
                qDesc ='Empty'
            else:
                qDesc =''
                if queue.count > 8:
                    for i in range(0,7):
                        song = queue._queue[i]
                        qDesc += f'[{str(i + 1) + ". " + song.title + " [" + str(datetime.timedelta(seconds=song.length)) + "]"}]({song.uri})' + '\n'
                    offset = queue.count - 7
                    qDesc += "and " + str(offset) + " more track(s)\n"
                else:
                    for i in range(0,queue.count):
                        song = queue._queue[i]
                        qDesc += f'[{str(i + 1) + ". " + song.title + " [" + str(datetime.timedelta(seconds=song.length)) + "]"}]({song.uri})' + '\n'
            
            if player.is_paused():
                status = "Paused\n"
                paused = True
            else:
                status = "Playing\n"
                paused = False

            if loop == 2:
                status += " 🔂"
            elif loop == 1:
                status += " 🔁"

            if shuffle == 1:
                status += "  🔀"
            
            embed.set_image(url=thumbnail)
            embed.add_field(name="Queue: ", value=qDesc, inline=True)
            embed.add_field(name="Status: ", value=status)
            embed.set_footer(text="Other commands: /mv, /rm, /dc, /q, /np, /seek, /vol")
            await message.edit(embed=embed, view=Music.music_button_view(paused, loop, shuffle))

    # Will play next track in queue or dc if no tracks left
    async def next(self, player):
        loop = False
        if loop:
            return await player.play(track)

        if player.queue.is_empty:
            await player.guild.voice_client.disconnect(force=True)
            await Music.reset_embed(self, player)
        else:
            next_song = player.queue.get()
            await player.play(next_song)

    #### LISTENERS ####

    # Triggers when a track starts playing
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player: wavelink.Player, track: wavelink.Track):
        await self.update_embed(player)

    # Triggers when a track ends 
    # Either by full run through or skip
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        result = await Music.connect_db(self, player.guild.id)
        
        if len(result) > 0:
          for x in result:
            loop = x[4]
            shuffle = x[5]
        
        if shuffle == 1:
            if not player.queue.is_empty:
                index = random.randint(0,player.queue.count-1)
                strack = player.queue._queue[index]
        
        if loop == 0:
            if shuffle == 1 and not player.queue.is_empty:
                await player.play(strack)
                del player.queue._queue[index]
            else:
                await self.next(player)
        elif loop == 2:
            await player.play(track)
        else:
            player.queue.put(track)
            if shuffle == 1 and not player.queue.is_empty:
                await player.play(strack)
                del player.queue._queue[index]
            else:
                await self.next(player)

        if player.is_playing():
            await self.update_embed(player)

    # Triggers when a connection to a node has been established
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f'Node: <{node.identifier}> is ready!')

    # Triggers when any message is sent
    @commands.Cog.listener()
    async def on_message(self, message):
        bot = self.bot

        # So the bot doesn't react to its own messages.
        if message.author == bot.user:
            return
        
        result = await self.connect_db(message.guild.id)

        if len(result) > 0:
            for x in result:
                self.channel_id = x[2]
                self.message_id = x[3]

            if message.channel.id == self.channel_id:
                if not message.content.startswith(config('PREFIX')):
                    ctx = await bot.get_context(message)
                    asyncio.get_event_loop().create_task(self.del_msg(message))
                    ctx.command = bot.get_command('play')
                    await self.cog_before_invoke(ctx)
                    await ctx.invoke(bot.get_command('play'), query=message.content, author=message.author)
                else:
                    await self.del_msg(message)


    #### COMMANDS ####

    # Play a song given a query, joins a voicechannel if not already in one
    @commands.command()
    async def play(self, ctx: commands.Context, *, query: str, author):
        check = await Music.check_cond(self, ctx, None, ctx.voice_client, author)
        if not check:
            return

        if '&list' in query:
            query = query.split("&")[1]
            query = "https://www.youtube.com/playlist?" + query

        if query.startswith("https://www.youtube.com/playlist?"):
            tracks = await wavelink.YouTubePlaylist.search(query=query)
            tracks = tracks.tracks
        else:
            try:
                track = await wavelink.YouTubeTrack.search(query=query, return_first=True)
                tracks = [track]
            except:
                tracks = None

        if tracks is None:
            embed = functions.discordEmbed("Player", "Error: Could not find track, try giving me the URL", botColourInt)
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(2)
            await msg.delete()
            return

        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        for track in tracks:
            if vc.is_playing():
                vc.queue.put(track)
            else:
                await vc.play(track)
        await self.update_embed(vc)

    # Moves a song position in the queue to one specified
    @app_commands.command(name = "mv", description = "Change a songs position in queue")
    @app_commands.describe(song_number = "Song number in queue", move_number = "New position in queue")
    async def move(self, interaction: discord.Interaction, song_number: int, move_number: int):
        ctx = await interaction.client.get_context(interaction)
        check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

        if check:
            vc: wavelink.Player = ctx.voice_client
            if vc.queue.is_empty:
                return
        
            current = song_number - 1
            new = move_number - 1

            if current > len(vc.queue)-1 or current < 0:
                await interaction.response.send_message(content = 'Current index out of bounds', ephemeral = True, delete_after = (2))
        
            if new > len(vc.queue)-1 or new < 0:
                await interaction.response.send_message(content = 'New index out of bounds', ephemeral = True, delete_after = (2))

            song = vc.queue._queue[current]
            
            del vc.queue._queue[current]
            queue = vc.queue

            for i in range(len(queue)-1, new):
                if i == len(queue) -1:
                    queue.put(queue._queue[i])
                else:
                    queue._queue[i+1] = queue._queue[i]
        else:
            return

        vc.queue.put_at_index(new, song)
        await self.update_embed(vc)
        embed = functions.discordEmbed('Move', 'Moved ' + song.title + ' from ' + str(current+1) + ' to ' + str(new+1), botColourInt)
        await interaction.response.send_message(embed=embed, delete_after = (4))

    # Removes a song from queue given its queue index
    @app_commands.command(name = "rm", description = "Remove song from queue")
    @app_commands.describe(song_number = "Song number in queue")
    async def remove(self, interaction: discord.Interaction, song_number: int):
        ctx = await interaction.client.get_context(interaction)
        check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

        if check:
            vc: wavelink.Player = ctx.voice_client
            if vc.queue.is_empty:
                return
            song = vc.queue._queue[song_number-1]
            del vc.queue._queue[song_number-1]

            embed = functions.discordEmbed('Remove', "Song removed: " + song.title, botColourInt)
            await interaction.response.send_message(embed=embed, delete_after = (1))
            await self.update_embed(vc)

    # Disconnects the bot from the voice channel and clears player queue
    @app_commands.command(name = "dc", description = "Disconnect bot from voice")
    async def disconnect(self, interaction: discord.Interaction):
        ctx = await interaction.client.get_context(interaction)
        check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

        if check:
            vc: wavelink.Player = ctx.voice_client
            vc.queue.clear()
            await Music.reset_embed(self, vc)
            await vc.disconnect()
            embed = functions.discordEmbed(title = 'Disconnected', description = 'Bot disconnected', colour = botColourInt)
            await interaction.response.send_message(embed=embed, delete_after = (1))

    # Outputs the queue in pages of 10 songs each, page number needs to be inputted
    @app_commands.command(name = "q", description = "Shows music queue")
    @app_commands.describe(page = "Page number of queue")
    async def queue(self, interaction: discord.Interaction, page: int = 1):
        ctx = await interaction.client.get_context(interaction)
        check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

        if check:
            vc: wavelink.Player = ctx.voice_client
        
        queue = vc.queue

        if len(queue) == 0:
            embed = functions.discordEmbed("Queue", 'No songs in queue | Why not queue something?', int(config('COLOUR'), 16))
            await interaction.response.send_message(embed=embed, ephemeral = True, delete_after = (1))
            return
        
        qDesc = ''

        items_per_page = 10
        pages = math.ceil(len(queue) / items_per_page)

        if page > pages:
            embed = functions.discordEmbed("Queue", 'Invalid page: Max page is ' + str(pages), int(config('COLOUR'), 16))
            await interaction.response.send_message(embed=embed, ephemeral = True, delete_after = (1))
            return

        start = (page - 1) * items_per_page
        if len(queue) < items_per_page:
            end = len(queue)
        elif len(queue) - ((page -1) * items_per_page) > items_per_page:
            end = start + items_per_page
        else:
            end = start + len(queue) - ((page -1) * items_per_page)


        for i in range(start,end):
            song = queue._queue[i]
            qDesc += f'[{str(i + 1) + ". " + song.title}]({song.uri})' + '\n'
            
        
        embed = functions.discordEmbed("Queue", qDesc, int(config('COLOUR'), 16))
        embed.set_footer(text=f'Viewing Page {page}/{pages}')
        await interaction.response.send_message(embed=embed, delete_after = (7))

    # Sends a message containing the current runtime of the song
    @app_commands.command(name = "np", description = "Shows information about whats currently playing")
    async def now(self, interaction: discord.Interaction):
        ctx = await interaction.client.get_context(interaction)
        check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

        if check:
            vc: wavelink.Player = ctx.voice_client
            current_song  = vc.track
            pos = str(datetime.timedelta(seconds=int(vc.position))) 
            dur = str(datetime.timedelta(seconds=current_song.length)) 

            song = f'**[{current_song.title}]({current_song.uri})**\n({pos}/{dur})'
            embed = discord.Embed(color= int(config('COLOUR'), 16), title='Now Playing', description=song)
            await interaction.response.send_message(embed=embed, ephemeral = True, delete_after = (5))

    # Seeks out and jumps to a point in a song based on time given
    @app_commands.command(name = "seek", description = "Jump to a time in the song")
    @app_commands.describe(time = "Time to jump to in (HH:)MM:SS")
    async def seek(self, interaction: discord.Interaction, time: str):
        ctx = await interaction.client.get_context(interaction)
        check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

        if check:
            vc: wavelink.Player = ctx.voice_client
            time_msec = self.get_sec(time) * 1000

            if not time_msec:
                embed = functions.discordEmbed('Seek' , 'You need to specify a time to skip to', botColourInt)
            else:
                embed = functions.discordEmbed('Seek', 'Moved track to ' + time, botColourInt)
                await vc.seek(time_msec)
            
            await interaction.response.send_message(embed=embed, delete_after = (1))

    # Adds a volume filter to the player, up to volume increase of 500%
    @app_commands.command(name = "vol", description = "Change volume of the player")
    @app_commands.describe(vol = "Volume in percent (Goes up to 500%) (No need for %)")
    async def volume(self, interaction: discord.Interaction, vol: int):
        ctx = await interaction.client.get_context(interaction)
        check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

        if check:
            vc: wavelink.Player = ctx.voice_client
            
            true_volume = vol/100

            if true_volume > 5 or true_volume < 0:
                embed = functions.discordEmbed('Volume' , 'Invalid volume size, please try between 0-500', botColourInt)
            else:
                filter = wavelink.Filter(volume = true_volume)
                await vc.set_filter(filter)
                embed = functions.discordEmbed('Volume' , f'🔈 | Set to {vol}%', botColourInt)

            await interaction.response.send_message(embed=embed, delete_after = (1))

    # Only really to be used in the even the embed is stuck/not updated
    @app_commands.command(name = "update", description = "Updates the music embed if stuck")
    async def update(self, interaction: discord.Interaction):
        ctx = await interaction.client.get_context(interaction)
        check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

        if check:
            vc: wavelink.Player = ctx.voice_client
            await self.update_embed(vc)
            embed = functions.discordEmbed('Update' , 'Updated!', botColourInt)
            await interaction.response.send_message(embed=embed, ephemeral = True)
        else:
            await Music.reset_embed(self, interaction)
            embed = functions.discordEmbed('Update' , 'Reset!', botColourInt)
            await interaction.response.send_message(embed=embed, ephemeral = True)

    # Sets up the channel to take in queries & commands and adds to database
    @app_commands.command(name = "setup", description = "Setups up music channel")
    async def setup(self, interaction: discord.Interaction):
        ctx = await interaction.client.get_context(interaction)
        if not ctx.author.guild_permissions.administrator:
            embed = functions.discordEmbed('Setup' , 'You have insufficient permissions', botColourInt)
            await interaction.response.send_message(embed=embed, ephemeral = True)
            return

        result = await self.connect_db(interaction.guild_id)   

        if len(result) > 0:
            embed = functions.discordEmbed('Setup' , 'Music channel already set up :)', botColourInt)  
            await interaction.response.send_message(embed=embed, ephemeral = True)
        else:
            channel = await ctx.guild.create_text_channel("music")
            guild_id = interaction.guild_id

            embed = discord.Embed(title = "No song currently playing ", color = int(config('COLOUR'), 16))
            embed.add_field(name="Queue: ", value="Empty")
            embed.add_field(name="Status: ", value="Idle")
            embed.set_image(url=config("BKG_IMG"))
            embed.set_footer(text="Other commands: /mv, /rm, /dc, /q, /np, /seek, /vol")
            message = await channel.send(content="To add a song join voice, and type song or url here",embed=embed, view=Music.music_button_view())

            channel_id = message.channel.id
            msg_id = message.id
            
            mydb = mysql.connector.connect(
                host = config("MYSQLIP"),
                user = config("MYSQLUSER"),
                password = config("MYSQLPASS"),
                database = config("MYSQLDB")
                )
            db = mydb.cursor()

            sql = "INSERT INTO " + self.table + " (guild_id, channel_id, message_id, loop_b, shuffle_b) VALUES (%s, %s, %s, 0, 0)"
            val = (guild_id, channel_id, msg_id) 
            db.execute(sql, val)
            mydb.commit()
            db.close()
            mydb.close()
            embed = functions.discordEmbed('Setup' , 'Channel now setup', botColourInt)
            await interaction.response.send_message(embed=embed, ephemeral = True)


    # Removes the music channel and its entry in the database
    @app_commands.command(name = "terminate", description = "Removes music channel")
    async def terminate(self, interaction: discord.Interaction):
        ctx = await interaction.client.get_context(interaction)
        if not ctx.author.guild_permissions.administrator:
            await interaction.response.send_message("You have insufficient permissions", ephemeral = True)
            return

        result = await self.connect_db(interaction.guild_id)

        if len(result) > 0:
            for x in result:
                channel_id = x[2]
                message_id = x[3]
                channel = interaction.client.get_channel(channel_id)
                await channel.delete()

                guild_id = interaction.guild_id
                mydb = mysql.connector.connect(
                host = config("MYSQLIP"),
                user = config("MYSQLUSER"),
                password = config("MYSQLPASS"),
                database = config("MYSQLDB")
                )
                db = mydb.cursor()

                sql = "DELETE FROM " + self.table + " WHERE guild_id = %s"
                val = (guild_id,)
                db.execute(sql, val)
                mydb.commit()
                db.close()
                mydb.close()
            
            embed = functions.discordEmbed('Terminate' , 'Music channel removed', botColourInt)
            await interaction.response.send_message(embed=embed, ephemeral = True)

        else:
            embed = functions.discordEmbed('Terminate' , 'There is no channel setup, please use /setup', botColourInt)
            await interaction.response.send_message(embed=embed, ephemeral = True)

async def setup(bot):
    await bot.add_cog(Music(bot))
    