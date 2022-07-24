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

version = "1.0a"
token = config('TOKEN')
prefix = config('PREFIX')
botColour = config("COLOUR")
botColourInt = int(botColour, 16)
intents = discord.Intents.all()

def get_prefix(bot, message):
    if message.channel.id == (config('MUSIC_CHANNEL_ID')):
        return ""
    else:
        return prefix

client = commands.Bot(command_prefix=get_prefix, help_command=None, intents=intents)

# Loading all cogs
print(bcolors.HEADER + "Logging in || Bot running version " + version + bcolors.ENDC)

tree = client.tree

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
        await client.load_extension(f'cogs.{filename[:-3]}')
        print(bcolors.OKBLUE + filename + " found" + bcolors.ENDC)

    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='you '+ config('PREFIX') +'rtd | v' + version))
    await tree.sync()
    
client.run(token)