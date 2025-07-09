import nextcord
import logging

application_emoji_cache = []
async def cache_application_emojis(bot: nextcord.Client) -> None:
    global application_emoji_cache
    application_emoji_cache = await bot.fetch_application_emojis()

def get_emoji_markdown(emoji_name: str, bot=None) -> str:
    """
    Returns the markdown representation of an emoji given its name.
    
    Args:
        emoji_name (str): The name of the emoji.
        bot (nextcord.Client, optional): The bot instance to use for retrieving the emoji. If not provided, it will use the global bot instance.
        
    Returns:
        str: The markdown representation of the emoji or a placeholder if not found.
    """
    global application_emoji_cache

    if len(application_emoji_cache) == 0:
        logging.warning("Emoji cache is empty. Ensure that application emojis are cached before calling this function.")
        return f":{emoji_name}:"

    # Get the bot
    from core.bot import get_bot
    bot = bot or get_bot()

    # Retrieve the emoji object from the bot's emoji cache
    emoji = nextcord.utils.get(application_emoji_cache, name=emoji_name)

    if emoji:
        # Return the markdown representation of the emoji
        return str(emoji)
    else:
        # If the emoji is not found, return a placeholder or an empty string
        logging.warning(f"Emoji '{emoji_name}' not found in the bot's emoji cache.")
        return f":{emoji_name}:"