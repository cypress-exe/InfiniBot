import nextcord
import logging

async def check_and_run_dm_commands(bot: nextcord.Client, message: nextcord.Message) -> None:
    """
    |coro|

    Runs a specified command for DMs
    
    :param bot: The bot client
    :type bot: nextcord.Client
    :param message: The message to check
    :type message: nextcord.Message
    :return: None
    :rtype: None
    """
    if message.author.id == bot.application_id: return

    if message.content.lower() == "clear-last": # Clear last message
        async for message in message.channel.history(limit=10):
            if message.author.id == bot.application_id:
                await message.delete()
                break

        embed = nextcord.Embed(title = "Cleared Last Message", description="Last message has been cleared.", color = nextcord.Color.green())
        await message.channel.send(embed = embed, delete_after = 3)
        