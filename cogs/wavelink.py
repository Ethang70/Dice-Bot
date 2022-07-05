import wavelink
import asyncio # For asyncio.sleep()
import mysql.connector # To connect to music db
import datetime # Used to convert time from S to HH:MM:SS
import discord # Use discord components and embeds

from decouple import config # For .env vars
from discord.ext import commands

class Music(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot):
        self.bot = bot
        self.id = int(config('MUSIC_CHANNEL_MSG_ID'))
        self.channel_id = 0
        self.message_id = 0
        self.table = config('MYSQLTB')

        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(bot=self.bot,
                                            host=config("LLIP"),
                                            port=2333,
                                            password=config("LLPASS"))

    class music_button_view(discord.ui.View):
        def __init__(self):
            super().__init__(timeout = None)
        
            self.add_item(Music.PauseButton())
            self.add_item(Music.StopButton())
            self.add_item(Music.SkipButton())
            # self.add_item(Music.LoopButton())
            # self.add_item(Music.ShuffleButton())

    class PauseButton(discord.ui.Button['pause']):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.green, label="▶")

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            ctx = await interaction.client.get_context(interaction.message)

            check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

            if check:
                vc: wavelink.Player = ctx.voice_client

                if vc.is_paused():
                    await vc.resume()
                else:
                    await vc.pause()


    class StopButton(discord.ui.Button['stop']):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.green, label="⬜")

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            ctx = await interaction.client.get_context(interaction.message)

            check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

            if check:
                vc: wavelink.Player = ctx.voice_client
                vc.queue.clear()
                await Music.reset_embed(self, vc)
                await vc.disconnect()



    class SkipButton(discord.ui.Button['skip']):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.green, label="▶▶|")
            
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            ctx = await interaction.client.get_context(interaction.message)

            check = await Music.check_cond(self, ctx, interaction, ctx.voice_client)

            if check:
                vc: wavelink.Player = ctx.voice_client
                end = vc.track.duration
                await vc.seek(end*1000)


            
    async def check_cond(self, ctx, interaction, player):
        if not ctx.voice_client or not player.is_connected():
            msg = await ctx.send('Im not connected')
            await Music.del_msg(self, msg)
            return False
        elif not (
            (interaction.client.user.id in ctx.author.voice.channel.voice_states) and
            (interaction.user.id in ctx.author.voice.channel.voice_states)
        ):
            msg = await ctx.send('You\'re not in my voice channel')
            await Music.del_msg(self, msg)
            return False
        elif not ctx.author.voice:
            msg = await ctx.send('You\re not in a voice channel')
            await Music.del_msg(self, msg)
            return False
        return True
        

            

    # class LoopButton(discord.ui.Button['loop']):
    #     def __init__(self):
    #         super().__init__(style=discord.ButtonStyle.green, label="🔁")

    #     # async def callback(self, interaction: discord.Interaction):
    #     #     await Music.loop(interaction)

    # class ShuffleButton(discord.ui.Button['shuffle']):
    #     def __init__(self):
    #         super().__init__(style=discord.ButtonStyle.green, label="🔀")

    #     # async def callback(self, interaction: discord.Interaction):
    #     #     await Music.shuffle(interaction)


    # Deletes message
    async def del_msg(self, message):
        await asyncio.sleep(0.5)
        await message.delete()

    # Connects to the database and returns inforamtion base on guild_id
    async def connect_db(self, guild_id : int):
        self.mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
        )
        self.db = self.mydb.cursor()

        sql = "SELECT * FROM " + config('MYSQLTB') + " WHERE guild_id = %s"
        val = (guild_id,)
        self.db.execute(sql, val)

        result = self.db.fetchall()

        return result

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
        embed.set_footer(text="Other commands: " + prefix +"mv, " + prefix + "rm, " + prefix + "dc, " + prefix + "q, " + prefix + "np, " + prefix + "seek, " + prefix + "vol")
        await message.edit(content="To add a song join voice, and type song or url here",embed=embed, view=Music.music_button_view())

    # Updates the music embed to reflect whats in the player
    async def update_embed(self, player):
        prefix = config("PREFIX")
        guild_id = str(player.guild.id)
        channel_id = 0
        message_id = 0

        result = await self.connect_db(guild_id)
        
        if len(result) > 0:
          for x in result:
            channel_id = x[2]
            message_id = x[3]

        channel = await self.bot.fetch_channel(channel_id)
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
            else:
                status = "Playing\n"
            
            # if player.repeat:
            #     status += " 🔁"
            
            # if player.shuffle:
            #     status += "  🔀"
            
            embed.set_image(url=thumbnail)
            embed.add_field(name="Queue: ", value=qDesc, inline=True)
            embed.add_field(name="Status: ", value=status)
            embed.set_footer(text="Other commands: " + prefix +"mv, " + prefix + "rm, " + prefix + "dc, " + prefix + "q, " + prefix + "np, " + prefix + "seek, " + prefix + "vol")
            await message.edit(embed=embed, view=self.music_button_view())

    #### MEDIA CONTROLS ####
    async def next(self, player):
        if 1 == 2:
            return await player.play(track)

        if player.queue.is_empty:
            await player.guild.voice_client.disconnect(force=True)
            await Music.reset_embed(self, player)
        else:
            next_song = player.queue.get()
            await player.play(next_song)



    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player: wavelink.Player, track: wavelink.Track):
        await self.update_embed(player)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        # Event fired when a track ends
        await self.next(player)
        if player.is_playing():
            await self.update_embed(player)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        # Event fired when a node has finished connecting
        print(f'Node: <{node.identifier}> is ready!')

    @commands.Cog.listener()
    async def on_message(self, message):
        bot = self.bot

        # So the bot doesn't react to its own messages.
        if message.author == bot.user:
            return

        if message.channel.name != "music":
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
                    await ctx.invoke(bot.get_command('play'), query=message.content)
                else:
                    await self.del_msg(message)


    @commands.command()
    async def play(self, ctx: commands.Context, *, query: str):
        """Play a song with the given search query.

        If not connected, connect to our voice channel.
        """

        track = await wavelink.YouTubeTrack.search(query=query, return_first=True)

        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        if vc.is_playing():
            vc.queue.put(track)
            await self.update_embed(vc)
        else:
            await vc.play(track)

async def setup(bot):
    await bot.add_cog(Music(bot))