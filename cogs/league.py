import os
import requests
import json
from discord.ext import commands


class league(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.riotkey = os.environ['RIOT']
  
  @commands.Cog.listener()
  async def on_ready(self):
    print('\033[92m' + 'League Loaded' + '\033[0m')
  
  # Function to return the encrypted SummonerId using Riot API & Summoner name
  def get_summoner_id(self, name):
    if name == None:
      return(1) # If no name is present return 1
    if name:  
      url = "https://oc1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + name
      response = requests.get(url, headers={"X-Riot-Token":self.riotkey}) 
      json_data = json.loads(response.text)
  
      if "status" in json_data:
        if json_data['status']['status_code'] == 401: # If error code recieved return it
          return(401)
        if json_data['status']['status_code'] == 404: # If error code recieved return it
          return(404) 

      id = json_data['id']
      return(id)

  # Function to return current game information using encrypted SummonerId
  def get_current_game(self, summoner_id):
    url = "https://oc1.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/" + summoner_id
    response = requests.get(url, headers={"X-Riot-Token":self.riotkey})
    json_data = json.loads(response.text)

    if "status" in json_data:
      if json_data['status']['status_code'] == 401:
          return(401) #If error code got return 401
      if json_data['status']['status_code'] == 404:
          return(404) #If error code got return 404
    else:
      return(json_data)

  @commands.command()
  async def sid(self, ctx, arg): 
      name = arg
      id = self.get_summoner_id(name)
      if id == 404:
        await ctx.send('Summoner not found')
      elif id == 401:
        await ctx.send('Unauthorised Access (Check API Key)')
      elif id == 1:
        await ctx.channel.send('Enter in a name')
      else:
        await ctx.channel.send('Summoner id is: ' + str(id))
  
def setup(client):
     client.add_cog(league(client))
