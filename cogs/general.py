import discord
import random
import re
import asyncio
from decouple import config
from discord.ext import commands
import functions
import mysql.connector
from discord import app_commands # Used for slash commands

prefix = config('PREFIX')
botColour = config("COLOUR")
botColourInt = int(botColour, 16)

class general(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.table = config('MYSQLTB')

  ### Command to roll X times with Y number of specified faces ##
  @app_commands.command(name = "rtd", description = "Rolls a die. Can be specified with number of rolls and number of faces.")
  @app_commands.describe(
    number_rolls = "Number of times to roll the die. If not specified, it will roll once.",
    number_faces = "Number of faces on the die. If not specified, it will have 6 sides.")
  async def rtd(self, interaction: discord.Interaction, number_rolls: str=None, number_faces: str=None):

    ctx = await interaction.client.get_context(interaction)

    async def rolldie(self, ctx, noRoll, noFace):
      regexCheck = re.match("[0-9]", noRoll)
      isMatch = bool(regexCheck)
      if isMatch:
        embed = functions.discordEmbed("Rolling the dice", "Rolling " + noRoll + " dice with " + noFace + " faces", int(config('COLOUR'), 16))
        await interaction.response.send_message(embed=embed)
        edited = False

        if int(noRoll) == 1:
          roll = random.randint(1, int(noFace))
          embed = functions.discordEmbed("You rolled a " + str(roll), None, int(config('COLOUR'), 16))
          await interaction.edit_original_message(embed=embed)
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
                await interaction.edit_original_message(embed=embed)
                allDieRolls = "" # Clear the message
                edited = True
              else:
                embed = functions.discordEmbed(None, allDieRolls, int(config('COLOUR'), 16))
                msg = await ctx.message.channel.send(embed=embed)
                allDieRolls = "" # Clear the message
          if edited is False:
            embed = functions.discordEmbed("Performed " + noRoll + " rolls with a " + noFace + "-sided die.", allDieRolls, int(config('COLOUR'), 16))
            msg = await ctx.message.channel.send(embed=embed)
          else:
            embed = functions.discordEmbed(None, allDieRolls, int(config('COLOUR'), 16))
            msg = await ctx.message.channel.send(embed=embed)       
      else:
        await usage(self)

    async def usage(self):
      usage = functions.discordEmbed("Usage: ", "/" + "rtd\nnumber_rolls: Number of times to roll the die. If not specified, it will roll once.\nnumber_faces: Number of faces on the die. If not specified, it will have 6 sides.", int(config('COLOUR'), 16))
      await interaction.response.send_message(embed=usage) # RTD Help

    if number_rolls is None and number_faces is None:
      await rolldie(self, ctx, "1", "6")
    elif number_rolls == "?" or number_rolls == "help" or number_faces == "?" or number_faces == "help":
      await usage(self)
    elif number_rolls is not None and number_faces is None:
      await rolldie(self, ctx, number_rolls, "6")
    elif number_rolls is None and number_faces is not None:
      await rolldie(self, ctx, "1", number_faces)
    else:
      await rolldie(self, ctx, number_rolls, number_faces)

  ### Facts or Cap ###
  @app_commands.command(name = "factsorcap", description = "Bot says if the above message is facts or cap.")
  async def factsorcap(self, interaction: discord.Interaction):
    randomFactOrCap = random.randint(1,2)
    if randomFactOrCap == 1:
      await interaction.response.send_message("Fax!")
      fax = await interaction.original_message()
      await fax.add_reaction('📠')
    else:
      await interaction.response.send_message("Cap!")
      cap = await interaction.original_message()
      await cap.add_reaction('🇨')
      await cap.add_reaction('🅰️')
      await cap.add_reaction('🅿️') 
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