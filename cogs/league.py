import requests
import json
import discord

from decouple import config
from discord.ext import commands
from discord import app_commands # Used for slash commands


class league(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.riotkey = config('RIOT')
  
  ### Function to return the encrypted SummonerId using Riot API & Summoner name ###
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

  ### Function to return current game information using encrypted SummonerId ###
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

  ### Function that obtains and prints summoner id using summoner name ### 
  @app_commands.command(name = "sid", description = "Grab summoner ID of LoL player [OCE]")
  @app_commands.describe(player_name = "In game name")
  async def summoner__id(self, interaction: discord.Interaction, player_name: str): 
      name = player_name
      id = self.get_summoner_id(name)
      if id == 404:
        await interaction.response.send_message('Summoner not found')
      elif id == 401:
        await interaction.response.send_message('Unauthorised Access (Check API Key)')
      elif id == 1:
        await interaction.response.send_message('Enter in a name')
      else:
        await interaction.response.send_message('Summoner id is: ' + str(id))
  
async def setup(client):
    await client.add_cog(league(client))
