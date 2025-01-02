import nextcord

async def check_and_run_dm_commands(bot: nextcord.Client, message: nextcord.Message) -> None:
    """
    |coro|

    Checks if the message is a direct message and if the author is the bot owner.
    If true, runs the specified command.
    
    :param bot: The bot client
    :type bot: nextcord.Client
    :param message: The message to check
    :type message: nextcord.Message
    :return: None
    :rtype: None
    """
    if message.content.lower() == "clear": # Clear all messages
        async for message in message.channel.history():
            if message.author.id == bot.application_id:
                await message.delete()
                            
    elif message.content.lower() == "del": # Clear last message
        async for message in message.channel.history(limit=1):
            if message.author.id == bot.application_id:
                await message.delete()