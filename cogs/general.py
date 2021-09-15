import random
import re
import asyncio
from decouple import config
from discord.ext import commands

class general(commands.Cog):
  def __init__(self, client):
    self.client = client

  usage = "Usage: " + config('PREFIX') + "rtd [Number of Rolls] [Number of faces on the die]"


  @commands.Cog.listener()
  async def on_ready(self):
    print('\033[92m' + 'General Loaded' + '\033[0m')

  @commands.command()
  async def help(self, ctx):
      user = ctx.author
      helpCommandList = ("Hi. I'm the Dice Bot. My prefix is " + config('PREFIX') +". \nList of Dice Bot Commands:\nrtd, sid, question\nType " + config('PREFIX') + "[command] ? to get more help on a command!")
      await user.send(helpCommandList)
      await ctx.message.add_reaction('👍')
    
  # Command to roll X times with Y number of specified faces 
  @commands.command()
  async def rtd(self, ctx, arg1=None, arg2=None):
      if (arg1 == None):
        await ctx.message.channel.send("Rolling...")
        roll = random.randint(1,6)
        await ctx.message.channel.send('You rolled a ' + str(roll))
      elif (arg1 == "?") or (arg1 == "help"):
        await ctx.message.channel.send(self.usage) # RTD Help
      else:
        noRoll = arg1
        noFace = arg2
        regexCheck = re.match("[0-9]", arg1)
        isMatch = bool(regexCheck)
        if isMatch:
         # splitDiceCommand = diceCommand.split(" ")
          if int(noRoll) == 1:
            roll = random.randint(1, int(noFace))
            await ctx.message.channel.send('You rolled a ' + str(roll))
          else:
            dieArr = [] # Define an empty array to store the rolls in
            await ctx.message.channel.send("Rolling...")
            for i in range(int(noRoll)):
              roll = random.randint(1, int(noFace))
              dieArr.append(roll)
            allDieRolls = ""
            await ctx.message.channel.send(noRoll + " Rolls complete:")
            for i in range(len(dieArr)):
              allDieRolls += "(" + str(dieArr[i]) + ") "
              if len(allDieRolls) > 1000:
                await ctx.message.channel.send(allDieRolls) # Send now to avoid 4000 character limit
                allDieRolls = "" # Clear the message
            if allDieRolls != "":
              await ctx.message.channel.send(allDieRolls)
            await ctx.message.channel.send("Performed " + noRoll + " rolls with a " + noFace + "-sided die.")
        else:
          await ctx.message.channel.send(self.usage) # RTD Help

  # Command to test thumb reactions
  @commands.command()
  async def thumb(self, ctx):
      channel = ctx.message.channel
      await ctx.channel.send('Send me that 👍 reaction, mate')

      def check(reaction, user):
          return user == ctx.message.author and str(reaction.emoji) == '👍'

      try:
          reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
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