import discord
import os
import requests
import json
import random
import re

riotkey = os.environ['RIOT']
client = discord.Client()
prefix = '$'
usage = "Usage: $rtd {Amount of die} {Amount of faces per die}"

# Function to remove prefix from string
def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]

# Function to return the encrypted SummonerId using Riot API & Summoner name
def get_summoner_id(name):
  if name == '$sid':
    return(1) #If no name is present return 1
  if name:  
    url = "https://oc1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + name
    response = requests.get(url, headers={"X-Riot-Token":riotkey}) 
    json_data = json.loads(response.text)
    
    if "status" in json_data:
      if json_data['status']['status_code'] == 401:
        return(401) #If error code got return 401
      if json_data['status']['status_code'] == 404:
        return(404) #If error code got return 404

    id = json_data['id']
    return(id)

# Function to return current game information using encrypted SummonerId
def get_current_game(summoner_id):
  url = "https://oc1.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/" + summoner_id
  response = requests.get(url, headers={"X-Riot-Token":riotkey})
  json_data = json.loads(response.text)
  
  if "status" in json_data:
    if json_data['status']['status_code'] == 401:
        return(401) #If error code got return 401
    if json_data['status']['status_code'] == 404:
        return(404) #If error code got return 404
  else:
    return(json_data)
  
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    # So the bot doesn't react to its own messages.
    if message.author == client.user:
        return

    # Get Encrypted SummonerID from Username
    if message.content.startswith(prefix + 'sid'):  
        name = remove_prefix(message.content, '$sid ')
        id = get_summoner_id(name)

        if id == 404:
          await message.channel.send('Summoner not found')
        elif id == 401:
          await message.channel.send('Unauthorised Access (Check API Key)')
        elif id == 1:
          await message.channel.send('Enter in a name')
        else:
          await message.channel.send('Summoner id is: ' + str(id))

    # Function to roll X amount of dice with Y number of specified faces
    if (prefix + 'rtd') in message.content:
      if (prefix + 'rtd ?') in message.content:
        # RTD Help
        await message.channel.send(usage)
      elif (prefix + 'rtd') == message.content:
        roll = random.randint(1,6)
        await message.channel.send('You rolled a ' + str(roll))
      else:
        diceCommand = message.content
        regexCheck = re.match("^\$[a-zA-Z]+ [0-9]+ [0-9]+$", diceCommand)
        isMatch = bool(regexCheck)
        if isMatch:
          splitDiceCommand = diceCommand.split(" ")
          for i in range(int(splitDiceCommand[1])):
            roll = random.randint(1, int(splitDiceCommand[2]))
            await message.channel.send('You rolled a ' + str(roll))
        else:
          await message.channel.send(usage)
        


    if ('gn stev') == message.content or ("Goodnight Steve") == message.content:
        SteveID = '<@224840296158986240>'
        await message.channel.send('Goodnight %s' % SteveID)

    if ('Gaming time') == message.content:
      await message.channel.send("It's gaming time")

    if message.content.startswith(prefix + 'thumb'):
        channel = message.channel
        await channel.send('Send me that 👍 reaction, mate')

        def check(reaction, user):
            return user == message.author and str(reaction.emoji) == '👍'

        try:
            reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await channel.send('👎')
        else:
            await channel.send('👍')



token = os.environ['TOKEN']
client.run(token)