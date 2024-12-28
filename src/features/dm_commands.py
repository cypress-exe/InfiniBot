import nextcord

async def check_and_run_dm_commands(bot: nextcord.Client, message: nextcord.Message):
    if message.content.lower() == "clear": # Clear all messages
        async for message in message.channel.history():
            if message.author.id == bot.application_id:
                await message.delete()
                            
    elif message.content.lower() == "del": # Clear last message
        async for message in message.channel.history(limit=1):
            if message.author.id == bot.application_id:
                await message.delete()