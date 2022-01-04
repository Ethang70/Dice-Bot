from discord.ext import commands
from discordTogether import DiscordTogether

class discordtogether(commands.Cog): 

  def __init__(self, client):
    self.client = client
    self.togetherControl = DiscordTogether(client)

  @commands.Cog.listener()
  async def on_ready(self):
    print('\033[92m' + 'DiscordTogether Loaded' + '\033[0m')

  @commands.command(name="youtube")
  async def youtube(self, ctx):
    link = await self.togetherControl.create_link(ctx.author.voice.channel.id, '880218394199220334')
    await ctx.send(f"CLICK HERE FOR FREE V-BuckS\n{link}")

  @commands.command()
  async def chess(self, ctx):
    link = await self.togetherControl.create_link(ctx.author.voice.channel.id, 'chess')
    await ctx.send(f"Click the blue link!\n{link}")

  @commands.command()
  async def poker(self, ctx):
    link = await self.togetherControl.create_link(ctx.author.voice.channel.id, 'poker')
    await ctx.send(f"Click the blue link!\n{link}")

  @commands.command()
  async def betrayal(self, ctx):
    link = await self.togetherControl.create_link(ctx.author.voice.channel.id, 'betrayal')
    await ctx.send(f"Click the blue link!\n{link}")

  @commands.command()
  async def fishing(self, ctx):
    link = await self.togetherControl.create_link(ctx.author.voice.channel.id, 'fishing')
    await ctx.send(f"Click the blue link!\n{link}")

  @commands.command()
  async def letter(self, ctx):
    link = await self.togetherControl.create_link(ctx.author.voice.channel.id, 'letter-tile')
    await ctx.send(f"Click the blue link!\n{link}")
  
  @commands.command()
  async def words(self, ctx):
    link = await self.togetherControl.create_link(ctx.author.voice.channel.id, 'word-snack')
    await ctx.send(f"Click the blue link!\n{link}")

  @commands.command()
  async def doodle(self, ctx):
    link = await self.togetherControl.create_link(ctx.author.voice.channel.id, 'doodle-crew')
    await ctx.send(f"Click the blue link!\n{link}")

def setup(client):
    client.add_cog(discordtogether(client))