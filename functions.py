import discord
from discord.ext import commands

# Returns a Discord Embed Object
def discordEmbed(title, description, colour):
  return discord.Embed(title=title, description=description,color=colour)