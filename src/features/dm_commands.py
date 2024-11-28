import nextcord

async def check_and_run_dm_commands(bot: nextcord.Client, message: nextcord.Message):
    if message.content.lower() == "clear":
        for message in await message.channel.history().flatten():
            if message.author.id == bot.application_id:
                await message.delete()
                            
    elif message.content.lower() == "del":
        for message in await message.channel.history().flatten():
            if message.author.id == bot.application_id:
                await message.delete()
                return