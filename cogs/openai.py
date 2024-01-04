import discord

from decouple import config
from discord.ext import commands
from discord import app_commands # Used for slash commands
from openai import AsyncOpenAI # Used for OpenAI API
import functions

class openai(commands.Cog):
    def __init__(self, client):
        self.client = client

    Oai = AsyncOpenAI(api_key=config('OPENAI_API_KEY'))

    @app_commands.command(name = "chatgpt", description = "Use ChatGPT (Uses GPT3.5 Tubo model)")
    @app_commands.describe(prompt = "Your prompt")
    async def chatgpt(self, interaction: discord.Interaction, prompt: str):
        ctx = await interaction.client.get_context(interaction)
        await interaction.response.defer()

        if len(prompt) > 255:
            title = prompt[0:252] + "..."
        else:
            title = prompt
            
        embed = discord.Embed(title=title, color = int(config('COLOUR'), 16))

        try:
            completion = await self.Oai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=
                [
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
        except:
            embed.add_field(name="An error occured", value="Sorry", inline=True)
            await interaction.followup.send(embed=embed)
            return

        # The following splits up the embeds so the full message can be sent #
        response = ""
        edited = False
        if len(completion.choices[0].message.content) > 4095:
            for i in range(len(completion.choices[0].message.content)):
                response += completion.choices[0].message.content[i]
                if len(response) > 4095:
                    if edited is False:
                        embed.description = response
                        await interaction.followup.send(embed=embed)
                        response = ""
                        edited = True
                    else:
                        embed = functions.discordEmbed(None, response, int(config('COLOUR'), 16))
                        await ctx.message.channel.send(embed=embed)
                        response = ""
        
        # Once loop is completed send what ever is left in the buffer
        if edited is False:
                embed.description = completion.choices[0].message.content
                embed.set_footer(text="GPT 3.5 Turbo")
                await interaction.followup.send(embed=embed)
        else:
                embed = functions.discordEmbed(None, response, int(config('COLOUR'), 16))
                embed.set_footer(text="GPT 3.5 Turbo")
                await ctx.message.channel.send(embed=embed)


    ### Function that allows users to use OpenAI models ### 
    @app_commands.command(name = "openai", description = "Use OpenAI's models")
    @app_commands.describe(prompt = "Your prompt", model = "Choose your model")
    @app_commands.choices(model=[
        app_commands.Choice(name="GPT 3.5 Turbo", value="gpt-3.5-turbo"),
        app_commands.Choice(name="GPT 4 Turbo", value="gpt-4-1106-preview"),
        app_commands.Choice(name="GPT 4", value="gpt-4"),
        app_commands.Choice(name="DALL-E 2", value="dall-e-2")
    ])
    async def openai(self, interaction: discord.Interaction, prompt: str, model: app_commands.Choice[str]):
        ctx = await interaction.client.get_context(interaction)
        await interaction.response.defer()
        
        if len(prompt) > 255:
            title = prompt[0:252] + "..."
        else:
            title = prompt

        embed = discord.Embed(title=title, color = int(config('COLOUR'), 16))

        if model.name == "DALL-E 2":
            try:
                response = await self.Oai.images.generate(
                    model=model.value,
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                embed.set_image(url=response.data[0].url)
                embed.set_footer(text=model.name)
                await interaction.followup.send(embed=embed)
            except:
                embed.add_field(name="An error occured", value="Sorry", inline=True)
                await interaction.followup.send(embed=embed)
                return
        else:
            try:
                completion = await self.Oai.chat.completions.create(
                    model=model.value,
                    messages=
                    [
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                )
            
                # The following splits up the embeds so the full message can be sent #
                response = ""
                edited = False
                if len(completion.choices[0].message.content) > 4095:
                    for i in range(len(completion.choices[0].message.content)):
                        response += completion.choices[0].message.content[i]
                        if len(response) > 4095:
                            if edited is False:
                                embed.description = response
                                await interaction.followup.send(embed=embed)
                                response = ""
                                edited = True
                            else:
                                embed = functions.discordEmbed(None, response, int(config('COLOUR'), 16))
                                await ctx.message.channel.send(embed=embed)
                                response = ""
                
                # Once loop is completed send what ever is left in the buffer
                if edited is False:
                        embed.description = completion.choices[0].message.content
                        embed.set_footer(text=model.name)
                        await interaction.followup.send(embed=embed)
                else:
                        embed = functions.discordEmbed(None, response, int(config('COLOUR'), 16))
                        embed.set_footer(text=model.name)
                        await ctx.message.channel.send(embed=embed)
            except:
                embed.add_field(name="An error occured", value="Sorry", inline=True)
                await interaction.followup.send(embed=embed)
                return

async def setup(client):
    await client.add_cog(openai(client))
