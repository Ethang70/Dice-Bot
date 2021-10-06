import discord

# Returns a Discord Embed Object, cleaner code
def discordEmbed(title, description, colour):
  if title is None:
    return discord.Embed(description=description, color=colour)
  elif description is None:
    return discord.Embed(title=title, color=colour)
  else:
    return discord.Embed(title=title, description=description, color=colour)
  return 0 # Failed