import asyncio
import json
import traceback
from datetime import datetime

import discord
import youtube_dl
from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


def get_prefix(_client, message):
    with open('config.json', 'r') as f:
        config = json.load(f)

    return config[str(message.guild.id)]["prefix"]


intents = discord.Intents.all()
client = commands.Bot(command_prefix=get_prefix, intents=intents)


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online)
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
async def changeprefix(ctx, prefix):
    with open('config.json', 'r') as f:
        config = json.load(f)

    config[str(ctx.guild.id)]['prefix'] = prefix

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    await ctx.send(f"You've changed prefix to: '{prefix}'")


@client.command()
async def ping(ctx):
    await ctx.send(f"Pong!{round(client.latency * 1000)}ms")


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Invalid command used.')


@client.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount=1):
    await ctx.channel.purge(limit=(amount + 1))


@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please specify an amount of messages to delete.')


@client.command()
async def set_log_channel(ctx):
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


@client.command(name="play")
async def play(ctx, *, url):
    try:
        voice_channel = ctx.author.voice.channel
        if voice_channel is not None:
            voice_client = await voice_channel.connect()

            async def after(error):
                if error:
                    print(error)
                await asyncio.sleep(1)
                await voice_client.disconnect()

            player = await YTDLSource.from_url(url, loop=client.loop, stream=True)
            voice_client.play(player,
                              after=lambda error: asyncio.run_coroutine_threadsafe(after(error), client.loop))

            await ctx.send(f'Now playing: {player.title}')
        else:
            await ctx.send(str(ctx.author.name) + "is not in a channel.")
    except:
        traceback.print_exc()


with open("token.txt", "r") as f:
    token = f.read().strip()
client.run(token)
