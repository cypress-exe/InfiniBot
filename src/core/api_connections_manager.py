import asyncio
import os
import logging

import topgg
import discordlists

# Matches topggpy's own autopost default. Top.gg rejects intervals under 15 minutes.
TOPGG_POST_INTERVAL_SECONDS = 1800

async def post_topgg_stats(bot):
    """
    Posts the bot's guild and shard counts to Top.gg.

    The shard count is sent, but Top.gg's v0 API currently discards it — a post
    carrying one reads back as null, and nothing in their UI displays it. It
    costs nothing to keep sending, and the listing's server count does update.

    :param bot: The bot instance to post stats for.
    :return: None
    :rtype: None
    """
    server_count = len(bot.guilds)
    await bot.topggpy.post_guild_count(guild_count=server_count, shard_count=bot.shard_count)

    logging.info(f"Posted {server_count} guilds across {bot.shard_count} shards to Top.gg.")

async def run_topgg_post_loop(bot):
    """
    Posts stats to Top.gg on an interval until the bot closes.

    Replaces topggpy's built-in autopost, which dispatched failures to an
    ``on_autopost_error`` event nothing listens for and permanently killed its
    own task on an unauthorized response. Failures are logged here instead, and
    a failed post never stops the loop — a rotated or briefly rejected token
    recovers on the next cycle.

    :param bot: The bot instance to post stats for.
    :return: None
    :rtype: None
    """
    while not bot.is_closed():
        try:
            await post_topgg_stats(bot)
        except Exception as e:
            logging.error(f"Failed to post stats to Top.gg: {e}", exc_info=True)

        await asyncio.sleep(TOPGG_POST_INTERVAL_SECONDS)

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

    bot.topggpy = topgg.DBLClient(bot, dbl_token)

    # Held on the bot because asyncio only keeps a weak reference to running
    # tasks — a local would let the loop be garbage collected mid-flight.
    bot.topgg_post_task = bot.loop.create_task(run_topgg_post_loop(bot))

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
    api.set_auth("discordlist.gg", discordlists_token)
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
