import os
import logging

import topgg
import discordlists

def setup_topgg(bot, dbl_token):
    """
    Sets up the Top.gg API connection for the bot.

    :param bot: The bot instance to set up the Top.gg connection for.
    :param dbl_token: The token for the Top.gg API.
    :return: None
    :rtype: None
    """

    logging.info("Setting up Top.gg API connection...")
    if not dbl_token:
        raise ValueError("Top.gg token is required to set up the Top.gg API connection.")
    
    bot.topggpy = topgg.DBLClient(bot, dbl_token, autopost=True, post_shard_count=True)
    
    logging.info("Top.gg API connection established successfully.")

def setup_discordlists(bot, discordlists_token):
    """
    Sets up the DiscordLists API connection for the bot.

    :param bot: The bot instance to set up the DiscordLists connection for.
    :param discordlists_token: The token for the DiscordLists API.
    :return: None
    :rtype: None
    """
    
    logging.info("Setting up DiscordLists API connection...")
    if not discordlists_token:
        raise ValueError("DiscordLists token is required to set up the DiscordLists API connection.")
    
    # TODO: Setup bots.ondiscord.xyz 
    api = discordlists.Client(bot)
    api.set_auth("discordbots.group", discordlists_token)
    api.start_loop()

    logging.info("DiscordLists API connection established successfully.")

def start_all_api_connections():
    """
    Sets up the API connections for the bot.

    :return: None
    :rtype: None
    """
    # Get bot instance
    from core.bot import get_bot
    bot = get_bot()

    # Setup top.gg API connection
    topgg_token = os.environ.get('TOPGG_AUTH_TOKEN', '')
    if topgg_token and topgg_token.lower() not in ["none", "missing"]:
        try:
            setup_topgg(bot, topgg_token)
        except ValueError as e:
            logging.error(f"Failed to set up Top.gg API connection: {e}")
    else:
        logging.warning("TOPGG_AUTH_TOKEN is not set or is invalid. Top.gg API connection will not be established.")

    # Setup discordlists API connection
    discordlists_token = os.environ.get('DISCORDLISTS_AUTH_TOKEN', '')
    if discordlists_token and discordlists_token.lower() not in ["none", "missing"]:
        try:
            setup_discordlists(bot, discordlists_token)
        except ValueError as e:
            logging.error(f"Failed to set up DiscordLists API connection: {e}")
    else:
        logging.warning("DISCORDLISTS_AUTH_TOKEN is not set or is invalid. DiscordLists API connection will not be established.")
