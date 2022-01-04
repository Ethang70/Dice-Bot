import discord
import os
from decouple import config
from discord.ext import commands

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

version = "0.4"
token = config('TOKEN')
prefix = config('PREFIX')
botColour = config("COLOUR")
botColourInt = int(botColour, 16)

def get_prefix(bot, message):
    if message.channel.id == (config('MUSIC_CHANNEL_ID')):
        return ""
    else:
        return prefix

client = commands.Bot(command_prefix=get_prefix, help_command=None)

# Load Extension
@client.command()
async def load(ctx, extension):
  client.load_extension(f'cogs{extension}')

# Unload Extension
@client.command()
async def unload(ctx, extension):
  client.unload_extension(f'cogs{extension}')

# Loading all cogs
print(bcolors.HEADER + "Logging in || Bot running version " + version + bcolors.ENDC)


# Function to remove prefix from string
def remove_prefix(text, prefix):
    print('prefix removed')
    return text[text.startswith(prefix) and len(prefix):]

# Triggers when the bot is 'ready'/logged in  
@client.event
async def on_ready():
    print(bcolors.OKCYAN + 'We have logged in as {0.user}'.format(client) + bcolors.ENDC)
  
    print(bcolors.HEADER + "Loading extensions" + bcolors.ENDC)

    for filename in os.listdir('./cogs'):
      if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')
        print(bcolors.OKBLUE + filename + " found" + bcolors.ENDC)

    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='you '+ config('PREFIX') +'rtd | v' + version))


@client.event # Triggers when a message is sent in the chat
async def on_message(message): 
    # So the bot doesn't react to its own messages.
  if message.author == client.user:
    return
  
  if "thanks bot" == message.content.lower() or "thank you bot" == message.content.lower():
      user = message.author.id
      await message.channel.send("No worries, <@%s>" % user)
  
  if ("bad bot") == message.content.lower():
    await message.add_reaction('😢')
    await message.channel.send(":(")
  
  await client.process_commands(message)

client.run(token)