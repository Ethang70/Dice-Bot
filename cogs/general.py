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

class PauseButton(discord.ui.Button['pause']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="▶")

class StopButton(discord.ui.Button['stop']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="⬜")

class SkipButton(discord.ui.Button['skip']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="▶▶|")

class LoopButton(discord.ui.Button['loop']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="🔁")

class ShuffleButton(discord.ui.Button['shuffle']):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="🔀")

class music_button_view(discord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
      
        self.add_item(PauseButton())
        self.add_item(StopButton())
        self.add_item(SkipButton())
        self.add_item(LoopButton())
        self.add_item(ShuffleButton())


class general(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.table = config('MYSQLTB')
    
  ### Command to roll X times with Y number of specified faces ##
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

  ### Facts or Cap ###
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

  ### Command for questions ###
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
  

  ### Allows admins of guild to delete messages ###
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

async def setup(client):
    await client.add_cog(general(client))