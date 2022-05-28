import discord
import random
import re
import asyncio
from decouple import config
from discord.ext import commands
import functions
import mysql.connector

prefix = config('PREFIX')
botColour = config("COLOUR")
botColourInt = int(botColour, 16)

class general(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.table = config('MYSQLTB')

  @commands.Cog.listener()
  async def on_ready(self):
    print('\033[92m' + 'General Loaded' + '\033[0m')

  # Command to roll X times with Y number of specified faces 
  @commands.command()
  async def rtd(self, ctx, noRoll=None, noFace=None):

    usage = functions.discordEmbed("Usage: ", config('PREFIX') + "rtd [Number of Rolls] [Number of faces on the die]", int(config('COLOUR'), 16))

    async def rolldie(self, ctx, noRoll, noFace):
      regexCheck = re.match("[0-9]", noRoll)
      isMatch = bool(regexCheck)
      if isMatch:
        embed = functions.discordEmbed("Rolling the dice", "Rolling " + noRoll + " dice with " + noFace + " faces", int(config('COLOUR'), 16))
        msg = await ctx.message.channel.send("Dice Roll: ",embed=embed)
        id = msg.id
        edited = False

        if int(noRoll) == 1:
          roll = random.randint(1, int(noFace))
          embed = functions.discordEmbed("You rolled a " + str(roll), None, int(config('COLOUR'), 16))
          message = await ctx.channel.fetch_message(id)
          await message.edit(embed=embed)
        else:
          dieArr = [] # Define an empty array to store the rolls in
          for i in range(int(noRoll)):
              roll = random.randint(1, int(noFace))
              dieArr.append(roll)
          allDieRolls = ""
          for i in range(len(dieArr)):
            allDieRolls += "(" + str(dieArr[i]) + ") "
            if len(allDieRolls) > 4000:
              if edited is False:
                embed = functions.discordEmbed("Performed " + noRoll + " rolls with a " + noFace + "-sided die.", allDieRolls, int(config('COLOUR'), 16))
                message = await ctx.channel.fetch_message(id)
                await message.edit(embed=embed)
                allDieRolls = "" # Clear the message
                edited = True
              else:
                embed = functions.discordEmbed(None, allDieRolls, int(config('COLOUR'), 16))
                msg = await ctx.message.channel.send(embed=embed)
                allDieRolls = "" # Clear the message
          if edited is False:
            embed = functions.discordEmbed("Performed " + noRoll + " rolls with a " + noFace + "-sided die.", allDieRolls, int(config('COLOUR'), 16))
            message = await ctx.channel.fetch_message(id)
            await message.edit(embed=embed)
          else:
            embed = functions.discordEmbed(None, allDieRolls, int(config('COLOUR'), 16))
            msg = await ctx.message.channel.send(embed=embed)          
      else:
        await ctx.message.channel.send("Roll the dice: ", embed=usage) # RTD Help


    if noRoll is None and noFace is None:
      await rolldie(self, ctx, "1", "6")
    elif noRoll == "?" or noRoll == "help":
      await ctx.message.channel.send("Roll the dice: ",embed=usage) # RTD Help
    elif noRoll is not None and noFace is None:
      await rolldie(self, ctx, noRoll, "6")
    else:
      await rolldie(self, ctx, noRoll, noFace)

  # Command to test thumb reactions
  @commands.command()
  async def thumb(self, ctx):
      channel = ctx.message.channel
      await ctx.channel.send('Send me that 👍 reaction, mate')

      def check(reaction, user):
          return user == ctx.message.author and str(reaction.emoji) == '👍'

      try:
          reaction, user = await self.client.wait_for('reaction_add', timeout=10.0, check=check)
      except asyncio.TimeoutError:
          await channel.send('👎')
      else:
          await channel.send('👍')

  #coding on a phone is bad
  # Facts or Cap
  @commands.command() 
  async def factsorcap(self, ctx):
    randomFactOrCap = random.randint(1,2)
    if randomFactOrCap == 1:
      facts = await ctx.message.channel.send("Fax!")
      await facts.add_reaction('📠')
    else:
      cap = await ctx.message.channel.send("Cap!")
      await cap.add_reaction('🇨')
      await cap.add_reaction('🅰️')
      await cap.add_reaction('🅿️') 
    await ctx.message.delete()
    return randomFactOrCap

  #Command for questions   
  @commands.command()
  async def question(self, ctx, *arg):
      question = False
      quesHelp = False

      # Check for a question mark and whether its alone or help is requested
      for args in arg:
        if "?" in args:
          question = True
        if args == "?" and len(arg) == 1 or args == "help" and len(arg) == 1:
          quesHelp = True

      if quesHelp == True:
        await ctx.message.channel.send("Usage: " + config('PREFIX') + "question [Enter your yes or no question for me to answer, don't forget the question mark]")
        return
      if question == False:
        await ctx.message.channel.send("Hmm, either that isn't a question or you forgot a question mark. Try again.")
        return
      response = random.randint(1,10)
      if response == 1:
        await ctx.message.channel.send("Yes!")
      elif response == 2:
        await ctx.message.channel.send("There's a very good chance.")
      elif response == 3:
        await ctx.message.channel.send("Certainly not.")
      elif response == 4:
        await ctx.message.channel.send("Potentially.")
      elif response == 5:
        await ctx.message.channel.send("I don't know.")
      elif response == 6:
        await ctx.message.channel.send("Of course!")
      elif response == 7:
        await ctx.message.channel.send("Wow... Of course not! Why would you even ask that?")
      elif response == 8:
        await ctx.message.channel.send("There is a chance.")
      elif response == 9:
        await ctx.message.channel.send("It's almost certain.")
      elif response == 10:
        await ctx.message.channel.send("No!")
  
  @commands.command()
  async def clear(self,ctx, amount: int):
    if not ctx.author.guild_permissions.administrator:
      ctx.message.send("You have insufficent permissions.")
      return
    
    amount = int(amount)
    
    if(amount < 1):
      return ctx.message.send("Enter a positive number")
    if(amount > 1000):
      return ctx.message.send("Enter a smaller number")

    await ctx.channel.purge(limit=amount)


  ### Sets up the channel and message for the music bot ###
  @commands.command()
  async def setup(self, ctx):
        prefix = config("PREFIX")
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
              channel_id = x[2]
              
            msg = await ctx.message.channel.send("Music channel already set up :)")
            await asyncio.sleep(2)
            await msg.delete()
        else:
          channel = await ctx.guild.create_text_channel("music")

          embed = discord.Embed(title = "No song currently playing ", color = int(config('COLOUR'), 16))
          embed.add_field(name="Queue: ", value="Empty")
          embed.add_field(name="Status: ", value="Idle")
          embed.set_image(url=config("DEFTN"))
          embed.set_footer(text="Other commands: " + prefix +"mv, " + prefix + "rm, " + prefix + "dc, " + prefix + "q, " + prefix + "np, " + prefix + "seek, " + prefix + "vol")
          message = await channel.send(content="To add a song join voice, and type song or url here",embed=embed)
          await message.add_reaction('⏯')
          await message.add_reaction('⏹')
          await message.add_reaction('⏭')
          await message.add_reaction('🔁')
          await message.add_reaction('🔀')

          channel_id = message.channel.id
          msg_id = message.id
        
          sql = "INSERT INTO server_info_test (guild_id, channel_id, message_id) VALUES (%s, %s, %s)"
          val = (guild_id, channel_id, msg_id) 
          self.db.execute(sql, val)
          self.mydb.commit()

  @commands.command()
  async def terminate(self, ctx):
    prefix = config("PREFIX")
    guild_id = ctx.guild.id
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
          channel = self.client.get_channel(channel_id)
          await channel.delete()

          guild_id = ctx.guild.id
          mydb = mysql.connector.connect(
          host = config("MYSQLIP"),
          user = config("MYSQLUSER"),
          password = config("MYSQLPASS"),
          database = config("MYSQLDB")
           )
          db = mydb.cursor()

          sql = "DELETE FROM server_info_test WHERE guild_id = %s"
          val = (guild_id,)
          db.execute(sql, val)
          mydb.commit()

    else:
      msg = await ctx.message.channel.send("There is no music channel setup! Please use  " + prefix + "setup to setup the channel")
      await asyncio.sleep(2)
      await msg.delete()

def setup(client):
    client.add_cog(general(client))