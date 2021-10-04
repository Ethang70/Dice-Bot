import random
import re
import asyncio
import discord
from decouple import config
from discord.ext import commands
import functions

class general(commands.Cog):
  def __init__(self, client):
    self.client = client

  @commands.Cog.listener()
  async def on_ready(self):
    print('\033[92m' + 'General Loaded' + '\033[0m')

  @commands.command()
  async def help(self, ctx):
      user = ctx.author
      helpCommandList = ("Hi. I'm the Dice Bot.\n**Prefix:** " + config('PREFIX') +" \n\n**General Commands:**\nrtd\nthumb\nquestion\n\n**League of Legends Commands:**\nsid\n\n**Music Commands:**\nplay\njoin\nsummon\nleave\nvolume\nnow\npause\nresume\nstop\nskip\nqueue\nshuffle\nremove\nloop\nType " + config('PREFIX') + "[command] ? to get more help on a command!\nSee ya later!")
      await user.send(helpCommandList)
      await ctx.message.add_reaction('👍')
    
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
            msg = await ctx.message.channel.send(embed=embed)
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

  # Command for questions
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
        
def setup(client):
    client.add_cog(general(client))