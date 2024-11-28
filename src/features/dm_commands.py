import nextcord

from config.global_settings import discord_bot


async def check_and_run_dm_commands(message: nextcord.Message):
    if message.content.lower() == "clear":
        for message in await message.channel.history().flatten():
            if message.author.id == discord_bot.application_id:
                await message.delete()
                            
    elif message.content.lower() == "del":
        for message in await message.channel.history().flatten():
            if message.author.id == discord_bot.application_id:
                await message.delete()
                return