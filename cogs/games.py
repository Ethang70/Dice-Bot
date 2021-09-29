import random
import asyncio
import discord
from decouple import config
from discord.ext import commands
import functions

class games(commands.Cog):
  def __init__(self, client):
    self.client = client

  # Guess the random number
  @commands.command()
  async def gtn(self, ctx, lowRange=None, highRange=None):

    # Usage of command
    usage = functions.discordEmbed("Usage: ", config('PREFIX') + "gtn (Lower Range) (Upper Range)", int(config('COLOUR'), 16))

    # Initial variable setup
    noArgs = False
    guessCounter = 0
    oldAnswer = ""

    # If first argument is a string
    if isinstance(lowRange, str):
      if lowRange == "?" or lowRange.lower() == "help":
        await ctx.message.channel.send(embed=usage)
        return 0
      elif lowRange is not None and highRange is None:
        await ctx.message.channel.send(embed=usage)
        return 0

    if lowRange is None and highRange is None:
      noArgs = True
    elif lowRange is not None and highRange is not None:
      try:
        lowRange = int(lowRange)
        highRange = int(highRange)
      except ValueError:
        embed = functions.discordEmbed("Arguments invalid", "Type " + config('PREFIX') + "gtn ? for usage.", int(config('COLOUR'), 16))
        await ctx.message.channel.send(embed=embed)
        return 0

    if not noArgs and highRange < lowRange:
      embed = functions.discordEmbed("Invalid range", "The upper range is less than the lower range.  Type " + config('PREFIX') + "gtn ? for usage.", int(config('COLOUR'), 16))
      await ctx.message.channel.send(embed=embed)
      return 0
    elif not noArgs and highRange == lowRange:
      embed = functions.discordEmbed("Invalid range", "The upper range is equal to the lower range. Type " + config('PREFIX') + "gtn ? for usage.", int(config('COLOUR'), 16))
      await ctx.message.channel.send(embed=embed)
      return 0
    if noArgs:
      lowRange = 0
      highRange = 100

    theNumber = random.randint(lowRange, highRange)
    numberGuessed = False
    embed = functions.discordEmbed("Guess the number!", "The number is between " + str(lowRange) + " and " + str(highRange) + ".", int(config('COLOUR'), 16))
    gameStartMSG = await ctx.message.channel.send("Guess the number: ", embed=embed)
    gameID = gameStartMSG.id

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
        message = await ctx.channel.fetch_message(gameID)
        await message.edit(embed=embed)
        return 0
      else:
        guessCounter+=1
        embededGuess = checkGuess(self, ctx, answer.content)
        message = await ctx.channel.fetch_message(gameID)
        await message.edit(embed=embededGuess)
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

def setup(client):
    client.add_cog(games(client))