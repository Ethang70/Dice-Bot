import discord
from decouple import config
from discord.ext import commands
import functions

prefix = config('PREFIX')
botColour = config("COLOUR")
botColourInt = int(botColour, 16)

## Global Array for commands and their descriptions. Probably a better way to do this exists...
helpCommandNames = ["betrayal", "chess", "clear", "disconnect", "doodle", "fishing", "gtn", "help", "letter", "loop", "move", "now", "pause", "play", "poker", "question", "queue", "remove", "rtd", "seek", "shuffle", "sid", "skip", "thumb", "volume", "words" , "youtube"]

helpCommandAbout = ["A multiplayer social deduction game like Among Us. Usage: " + prefix + "betrayal", "Play chess in the park. Usage: " + prefix + "chess", "Clears a specified number of messages from a discord channel between 1 and 1000.", "Disconnects the Dice Bot from the call. Usage: " + prefix + "disconnect, " + prefix + "dc, " + prefix + "stop", "Draw images that other players must guess. Usage: " + prefix + "doodle", "An online fishing game where you can relax, chat and fish with up to 24 players! Usage: " + prefix + "fishing", "A game where you need to guess the number that the Dice Bot is thinking of. Usage: " + prefix + "gtn (Lower Range) (Upper Range)", "Lists all commands of the Dice Bot. Usage: " + prefix + "help", "Letter Tile is a game where you and your friends take turns placing letters on a shared game board to create words in a crossword-style. Usage: " + prefix + "letter", "Loops the current song. Usage: " + prefix + "loop", "Moves a song to a different position in the queue. Usage: " + prefix + "move [Song number in queue] [Song position in queue to move to], " + prefix + "mv", "Shows the song that is currently playing and its duration. Usage: " + prefix + "now, " + prefix + "np, " + prefix + "n", "Pauses the current song. If song is already paused, it will resume. Usage: " + prefix + "pause", "Searches and plays a song from a given query. Usage: " + prefix + "play [song]", "Play Poker Night with up to 8 other players together. Usage: " + prefix + "poker", "Enter a question you have for the Dice Bot. You must include a question mark. Usage: " + prefix + "question [question to ask]", "Displays the list of songs queued. Usage: " + prefix + "queue, " + prefix + "q", "Removes the specified song from the queue. Usage: " + prefix + "remove [songs position in queue to remove], " + prefix + "rm", "Rolls the dice. Optional parameters to specify number of sides and number of die to roll. Usage: " + prefix + "rtd (number of rolls) (number of faces on the die)", "Moves the song playing to the specified timecode position. Usage: " + prefix + "seek [timecode to seek to]", "Turns on shuffling the queue. If shuffling is already on, the queue will be unshuffled. Usage: " + prefix + "shuffle", "Summoner's ID. Searches a Riot Summoners ID.", "Skips the song that is currently playing. Usage: " + prefix + "skip", "Give me that thumb reaction mate. Usage: " + prefix + "thumb", "Sets the volume of the music in the voice channel. Usage: " + prefix + "volume [volume percent value] , " + prefix + "vol", "A Discord word game. Usage: " + prefix + "words", "Starts a YouTube Party session to watch Youtube with others in the call. Usage: " + prefix + "youtube"]

class helpcommand(commands.Cog):

  def __init__(self, client):
    self.client = client
    self.currentPage = 0
    self.lowerRange = 0
    self.higherRange = 4
    self.pageMin = 0
    self.pageMax = 5
    self.perPage = 5
    self.helpID = None

  @commands.Cog.listener()
  async def on_ready(self):
    print('\033[92m' + 'Help Loaded' + '\033[0m')

  currentPage = 0
  lowerRange = 0  

  # Update the list of help commands currently displayed
  def updateHelpPage(self, embed, page):
      low = page * 5
      high = (page + 1) * 5
      helpCommandNameCurrent = helpCommandNames[low:high]
      helpCommandAboutCurrent = helpCommandAbout[low:high]
      helpCommandContent = ""
      try:
        for i in range(low, high):
          helpCommandContent += prefix + "**" + helpCommandNameCurrent[i-low] + "**" + " - " + helpCommandAboutCurrent[i-low] + "\n"
      except IndexError as err:
        print("\033[93mINFO - " + str(err) + " - end of list but not multiple of 5.")
      embed = discord.Embed(title="Help", description=helpCommandContent, color=botColourInt)
      embed.set_footer(text="Page " + str(page+1) + " of " + str(self.pageMax + 1))
      return embed
  
  def getPageNumber(self, embed):
    pageText = embed.footer.text
    pageArr = pageText.split()
    currentPage = int(pageArr[1]) - 1
    return currentPage

  @commands.command()
  async def help(self, ctx):
    user = ctx.author
    high = self.higherRange+1
    low = self.lowerRange
    helpCommandNameCurrent = helpCommandNames[low:high]
    helpCommandAboutCurrent = helpCommandAbout[low:high]
    helpCommandContent = ""

    for i in range(low, high):
      helpCommandContent += prefix + "**" + helpCommandNameCurrent[i-low] + "**" + " - " + helpCommandAboutCurrent[i-low] + "\n"

    embed = discord.Embed(title="Help", description=helpCommandContent, color=botColourInt)
    embed.set_footer(text="Page 1 of " + str(self.pageMax + 1))

    helpMessage = await ctx.message.channel.send(content="Here " + user.mention,embed=embed)
    await helpMessage.add_reaction("⏪")
    await helpMessage.add_reaction("⏩")
  
  # Reaction helper to help command
  @commands.Cog.listener()
  async def on_raw_reaction_add(self, reaction):
    client = self.client
    #message_id = self.message_id
    ctx = reaction
    ctx.channel = await self.client.fetch_channel(reaction.channel_id)
    ctx.message = await ctx.channel.fetch_message(reaction.message_id)
    ctx = await client.get_context(ctx.message)
    ctx.author = reaction.member

    # So the bot doesnt react to own reactions
    if ctx.author == client.user:
      return

    embed = ctx.message.embeds[0]

    ### Check is a bot help message ###
    if ctx.message.author != client.user and embed.title == "Help":
      return
    
    page = self.getPageNumber(embed) # int(embed.footer.text) - 1
    emojir = str(reaction.emoji)

    if emojir == "⏪":
      await ctx.message.remove_reaction("⏪", ctx.author)
      if page <= self.pageMin:
        return
      else:
        await ctx.message.edit(embed=self.updateHelpPage(embed, page - 1))
    elif emojir == "⏩":
      await ctx.message.remove_reaction("⏩", ctx.author)
      if page < self.pageMax:
        await ctx.message.edit(embed=self.updateHelpPage(embed, page + 1)) 
        return
      else:
        return
    else:
      return

def setup(client):
  client.add_cog(helpcommand(client))