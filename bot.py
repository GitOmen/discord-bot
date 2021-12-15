import json
import traceback
from datetime import datetime

import discord
from discord.ext import commands

from music import Music


def get_prefix(_client, message):
    with open('config.json', 'r') as f:
        config = json.load(f)

    return config[str(message.guild.id)]["prefix"]


intents = discord.Intents.all()
client = commands.Bot(command_prefix=get_prefix, intents=intents)


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online)
    client.add_cog(Music(client))
    print("Bot is ready.")


@client.event
async def on_guild_join(guild):
    with open('config.json', 'r') as f:
        config = json.load(f)

    config[str(guild.id)] = {"prefix": '.', "log_channel_id": '-1'}

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)


@client.event
async def on_guild_remove(guild):
    with open('config.json', 'r') as f:
        config = json.load(f)

    config.pop(str(guild.id))

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)


@client.command()
async def change_prefix(ctx, prefix):
    """ Sets custom command prefix. """
    with open('config.json', 'r') as f:
        config = json.load(f)

    config[str(ctx.guild.id)]['prefix'] = prefix

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    await ctx.send(f"You've changed prefix to: '{prefix}'")


@client.command()
async def ping(ctx):
    """ Checks websocket response latency. """
    await ctx.send(f"Pong!{round(client.latency * 1000)}ms")


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Invalid command used.')
        return
    traceback.print_exception(type(error), error, error.__traceback__)


@client.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 1):
    """ Purges specified amount of recent messages. One if no arguments passed """
    await ctx.channel.purge(limit=(amount + 1))


@client.command()
async def set_log_channel(ctx):
    """ Sets voice join/leave log channel. """
    with open('config.json', 'r') as f:
        config = json.load(f)

    config[str(ctx.guild.id)]['log_channel_id'] = str(ctx.channel.id)

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    await ctx.send(f"You've set log channel to: {ctx.channel.mention}")


@client.event
async def on_voice_state_update(member, before, after):
    with open('config.json', 'r') as f:
        config = json.load(f)

    channel = client.get_channel(int(config[str(member.guild.id)]['log_channel_id']))
    if channel is None:
        return

    async def embed(title, colour, target_channel):
        join_embed = discord.Embed(
            title=title,
            colour=colour
        )
        join_embed.set_author(name=member.name, icon_url=member.avatar_url)
        join_embed.add_field(name='User', value=member.mention, inline=True)
        join_embed.add_field(name='Channel', value=target_channel.name, inline=True)
        join_embed.timestamp = datetime.utcnow()

        await channel.send(embed=join_embed)

    if before.channel is None and after.channel is not None:
        await embed('Voice Join', discord.Colour.green(), after.channel)
    elif before.channel is not None and after.channel is None:
        await embed('Voice Leave', discord.Colour.red(), before.channel)


with open("token.txt", "r") as f:
    token = f.read().strip()
client.run(token)
