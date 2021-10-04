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

version = "0.2"
token = config('TOKEN')
prefix = config('PREFIX')
botColour = config("COLOUR")

def get_prefix(bot, message):
    if message.channel.id == (config('MUSIC_CHANNEL_ID')):
        return ""
    else:
        return prefix

client = commands.Bot(command_prefix=get_prefix, help_command=None)

# Discord User ID's
STEVE_ID = config('STEVE')
JAMES_ID = config('JAMES')
ETHAN_ID = config('ETHAN')
JORDY_ID = config('JORDY')
JOSH_ID = config('JOSH')
LIAM_ID = config('LIAM')

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
  
  if 'gn stev' == message.content.lower() or ('gn steve') == message.content.lower() or ("goodnight steve") == message.content.lower():
      await message.channel.send('Goodnight %s' % STEVE_ID)

  if 'gn james' == message.content.lower() or ("goodnight james") == message.content.lower():
        await message.channel.send('Goodnight %s' % JAMES_ID)

  if 'gn ethan' == message.content.lower() or ("goodnight ethan") == message.content.lower() or ('gn bthan') == message.content.lower():
        await message.channel.send('Goodnight %s' % ETHAN_ID)
  
  if 'gn josh' == message.content.lower() or ("goodnight josh") == message.content.lower():
        await message.channel.send('Goodnight %s' % JOSH_ID)

  if 'gn jordy' == message.content.lower() or ("goodnight jordy") == message.content.lower() or ('gn jp') == message.content.lower():
        await message.channel.send('Goodnight %s' % JORDY_ID)

  if 'gn liam' == message.content.lower() or ("goodnight liam") == message.content.lower():
        await message.channel.send('Goodnight %s' % LIAM_ID)

  if 'gaming time' == message.content.lower():
    await message.channel.send("It's gaming time")
    
  if "give me hacks in val" == message.content.lower():
      await message.channel.send("You now have hacks in Valorant")
  
  if "thanks bot" == message.content.lower() or "thank you bot" == message.content.lower():
      user = message.author.id
      await message.channel.send("No worries, <@%s>" % user)
  
  if ("bad bot") == message.content.lower():
    await message.add_reaction('😢')
    await message.channel.send(":(")
  
  await client.process_commands(message)

client.run(token)