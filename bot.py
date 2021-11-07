import discord
import json
from datetime import datetime
from discord.ext import commands


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
    await ctx.channel.purge(limit=(amount+1))


@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please specify an amount of messages to delete.')


@client.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)


@client.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'Banned {member.mention}')


@client.command()
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'Unbanned {user.mention}')
            return


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

with open("token.txt", "r") as f:
    token = f.read().strip()
client.run(token)
