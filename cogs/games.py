import random
import asyncio
import discord
from decouple import config
from discord.ext import commands
from discord import app_commands # Used for slash commands
import functions


prefix = config('PREFIX')
botColour = config("COLOUR")
botColourInt = int(botColour, 16)

class games(commands.Cog):
  def __init__(self, client):
    self.client = client

  ### Guess the random number ###

  @app_commands.command(name = "gtn", description="Guess the random number game")
  @app_commands.describe(lowrange = "Lowest number in range", highrange = "Highes number in range")
  async def gtn(self, interaction: discord.Interaction, lowrange: int = None, highrange:int = None):
    ctx = await interaction.client.get_context(interaction.message)
    # Usage of command
    #usage = functions.discordEmbed("Usage: ", config('PREFIX') + "gtn (Lower Range) (Upper Range)", int(config('COLOUR'), 16))
    lowRange = lowrange
    highRange = highrange
    # Initial variable setup
    noArgs = False
    guessCounter = 0
    oldAnswer = ""

    # # If first argument is a string
    # if isinstance(lowRange, str):
    #   if lowRange == "?" or lowRange.lower() == "help":
    #     await ctx.message.channel.send(embed=usage)
    #     return 0
    #   elif lowRange is not None and highRange is None:
    #     await ctx.message.channel.send(embed=usage)
    #     return 0

    if lowRange is None and highRange is None:
      noArgs = True
    # elif lowRange is not None and highRange is not None:
    #   try:
    #     lowRange = int(lowRange)
    #     highRange = int(highRange)
    #   except ValueError:
    #     embed = functions.discordEmbed("Arguments invalid", "Type " + config('PREFIX') + "gtn ? for usage.", int(config('COLOUR'), 16))
    #     await ctx.message.channel.send(embed=embed)
    #     return 0

    if not noArgs and highRange < lowRange:
      embed = functions.discordEmbed("Invalid range", "The upper range is less than the lower range.  Type " + config('PREFIX') + "gtn ? for usage.", int(config('COLOUR'), 16))
      await interaction.response.send_message(embed=embed)
      return 0
    elif not noArgs and highRange == lowRange:
      embed = functions.discordEmbed("Invalid range", "The upper range is equal to the lower range. Type " + config('PREFIX') + "gtn ? for usage.", int(config('COLOUR'), 16))
      await interaction.response.send_message(embed=embed)
      return 0
    if noArgs:
      lowRange = 0
      highRange = 100

    theNumber = random.randint(lowRange, highRange)
    numberGuessed = False
    embed = functions.discordEmbed("Guess the number!", "The number is between " + str(lowRange) + " and " + str(highRange) + ".", int(config('COLOUR'), 16))
    await interaction.response.send_message("Guess the number: ", embed=embed)


    def checkGuess(self, ctx, userGuess):
      if isinstance(userGuess, str):
        if userGuess.lower() == "exit":
          embed = functions.discordEmbed("You gave up! Game Over!", "The number was: " + str(theNumber), int(config('COLOUR'), 16))
          return embed
      try:
        userGuess = int(userGuess)
      except ValueError:
        embed = functions.discordEmbed("Invalid guess! Try Again!", "The number is between " + str(lowRange) + " and " + str(highRange) + ".", int(config('COLOUR'), 16))
        return embed
      
      if userGuess > highRange:
        # print(str(userGuess) + " " + str(highRange))
        embed = functions.discordEmbed("Your guess is above the set range!", "The number is between " + str(lowRange) + " and " + str(highRange) + ". Number of guesses: " + str(guessCounter), int(config('COLOUR'), 16))
      elif userGuess < lowRange:
        # print(str(userGuess) + " " + str(lowRange))
        embed = functions.discordEmbed("Your guess is below the set range!", "The number is between " + str(lowRange) + " and " + str(highRange) + ". Number of guesses: " + str(guessCounter), int(config('COLOUR'), 16))
      elif userGuess > theNumber:
        # print(str(userGuess) + " " + str(theNumber))
        embed = functions.discordEmbed("Lower", "The number is between " + str(lowRange) + " and " + str(highRange) + ". Number of guesses: " + str(guessCounter), int(config('COLOUR'), 16))
      elif userGuess < theNumber:
        # print(str(userGuess) + " " + str(theNumber))
        embed = functions.discordEmbed("Higher", "The number is between " + str(lowRange) + " and " + str(highRange) + ". Number of guesses: " + str(guessCounter), int(config('COLOUR'), 16))
      elif userGuess == theNumber:
        # print(str(userGuess) + " " + str(theNumber))
        embed = functions.discordEmbed("You guessed the number!", "Congratulations! The number was " + str(theNumber) + ".\nThanks for playing! :smile:\nYou made " + str(guessCounter) + " guesses", int(config('COLOUR'), 16))
      return embed

    while not numberGuessed:
      def check(m):
        return m.author == ctx.message.author
      try:
        answer = await self.client.wait_for('message', timeout=30.0, check=check)
      except asyncio.TimeoutError:
        embed = functions.discordEmbed("You took too long to respond...", "Game over! The number was " + str(theNumber) + ".", int(config('COLOUR'), 16))
        await interaction.edit_original_message(embed=embed)
        return 0
      else:
        guessCounter+=1
        embededGuess = checkGuess(self, ctx, answer.content)
        await interaction.edit_original_message(embed=embededGuess)
        if oldAnswer != "":
          oldMessage = await ctx.channel.fetch_message(oldAnswer.id)
          await oldMessage.delete()
        oldAnswer = answer
        if embededGuess.title == "You gave up! Game Over!":
          numberGuessed = True
        elif embededGuess.title == "You guessed the number!":
          numberGuessed = True
        if numberGuessed is True:
          finalMessage = await ctx.channel.fetch_message(answer.id)
          await finalMessage.delete()
    return theNumber + 1

  ### Rock Paper Scissors ###
  ### Returns 1 on player win, 0 on bot win, 2 on draw and -1 on error
  @commands.command()
  async def rps(self, ctx, playerInput):

    # Usage of command
    usage = functions.discordEmbed("Usage: ", config('PREFIX') + "rps [Rock, Paper or Scissors]", int(config('COLOUR'), 16))
    
    playerMove = -1
    
    if str(playerInput).lower() == "rock" or str(playerInput).lower() == "r":
      playerMove = 0
    elif str(playerInput).lower() == "paper" or str(playerInput).lower() == "p":
      playerMove = 1
    elif str(playerInput).lower() == "scissors" or str(playerInput).lower() == "s":
      playerMove = 2
    else:
      embed = discord.Embed(title="Rock Paper Scissors", description="Invalid move!", color=botColourInt)
      embed.set_footer(text="Please enter either Rock, Paper or Scissors.")
      await ctx.message.channel.send(embed=embed)
      return -1

    botMove = random.randint(0, 2)

    # 0 = Rock
    # 1 = Paper
    # 2 = Scissors
    moves = {"0": "Rock", "1": "Paper", "2": "Scissors"}

    def moveEmbed(botMove, win=None):
      if win is None:
        embed = discord.Embed(title="Draw!", description="You drew!", color=botColourInt)
      elif win:
        embed = discord.Embed(title="You win!", description="Congratulations!", color=botColourInt)
      else:
        embed = discord.Embed(title="You lose!", description="Unlucky!", color=botColourInt)
      embed.set_footer(text="Bot chose " + moves[str(botMove)] + ".")
      return embed

    if botMove == playerMove:
      await ctx.message.channel.send(embed=moveEmbed(botMove))
      return 2

    if botMove == 0:
      if playerMove == 1:
        await ctx.message.channel.send(embed=moveEmbed(botMove, True))
        return 1
      else:
        await ctx.message.channel.send(embed=moveEmbed(botMove, False))
        return 0
    elif botMove == 1:
      if playerMove == 0:
        await ctx.message.channel.send(embed=moveEmbed(botMove, False))
        return 0
      else:
        await ctx.message.channel.send(embed=moveEmbed(botMove, True))
        return 1
    elif botMove == 2:
      if playerMove == 0:
        await ctx.message.channel.send(embed=moveEmbed(botMove, True))
        return 1
      else:
        await ctx.message.channel.send(embed=moveEmbed(botMove, False))
        return 0
    
    return -1

async def setup(client):
    await client.add_cog(games(client))