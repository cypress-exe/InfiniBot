import asyncio
import os
import logging

import aiohttp

class BotListConnection:
    """
    Base class for posting InfiniBot's guild count to a bot list.

    Subclasses MUST implement the :meth:`build_request` method to describe the
    HTTP request for posting stats. The base class handles the loop, error
    handling, and logging.

    :param bot: The bot instance to post stats for.
    :param token: The API token for this website (bot list).
    """

    name = None
    """Human-readable website (bot list) name for use in log messages."""

    post_interval_seconds = 1800 # 30 minutes
    """Seconds between posts."""

    def __init__(self, bot, token):
        if not token:
            raise ValueError(f"A token must be specified in order to setup the {self.name} API connection.")

        self.bot = bot
        self.token = token
        self.task = None

    @property
    def server_count(self):
        """
        The number of guilds the bot is in.

        :return: The guild count.
        :rtype: int
        """
        return len(self.bot.guilds)

    def build_request(self):
        """
        Describes the stats HTTP request for this bot list website.

        :return: The HTTP method, URL, JSON body and headers to send.
        :rtype: tuple[str, str, dict, dict]
        """
        raise NotImplementedError

    def success_message(self):
        """
        The line logged after a successful post.

        :return: The message to log.
        :rtype: str
        """
        return f"Posted {self.server_count} guilds to {self.name}."

    async def post_stats(self):
        """
        Sends a single stats request, raising on any non-success response.

        :return: None
        :rtype: None
        """
        method, url, payload, headers = self.build_request()

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=payload, headers=headers) as response:
                response.raise_for_status()

        logging.info(self.success_message())

    async def run_post_loop(self):
        """
        Posts stats on an interval until the bot closes.

        :return: None
        :rtype: None
        """
        # Mirrors Top.gg's now-removed module for posting bot stats on an interval.
        while not self.bot.is_closed():
            try:
                await self.post_stats()
            except Exception as e:
                logging.error(f"Failed to post stats to {self.name}: {e}", exc_info=True)

            await asyncio.sleep(self.post_interval_seconds)

    def start(self):
        """
        Starts the posting loop.

        :return: None
        :rtype: None
        """
        self.task = self.bot.loop.create_task(self.run_post_loop())
        logging.info(f"{self.name} API connection established successfully.")

class TopGGConnection(BotListConnection):
    name = "Top.gg"
    url = "https://top.gg/api/v1/projects/@me/metrics"

    def build_request(self):
        payload = {"server_count": self.server_count}

        # Apparently, sending an explicit null is not the same
        # as omitting the field. So we only include the shard_count
        # if it's set.
        if self.bot.shard_count:
            payload["shard_count"] = self.bot.shard_count

        return "PATCH", self.url, payload, {"Authorization": f"Bearer {self.token}"}

    def success_message(self):
        return f"Posted {self.server_count} guilds across {self.bot.shard_count} shards to {self.name}."

class DiscordListConnection(BotListConnection):
    name = "discordlist.gg"
    url = "https://api.discordlist.gg/v0/bots/{bot_id}/guilds"

    def build_request(self):
        return (
            "POST",
            self.url.format(bot_id=self.bot.user.id),
            {"count": self.server_count},
            {"Authorization": f"Bearer {self.token}"},
        )

# TODO: Setup bots.ondiscord.xyz
BOT_LIST_CONNECTIONS = (
    (TopGGConnection, "TOPGG_AUTH_TOKEN"),
    (DiscordListConnection, "DISCORDLISTS_AUTH_TOKEN"),
)

def start_all_api_connections():
    """
    Sets up the API connections for the bot.

    :return: None
    :rtype: None
    """
    # Get bot instance
    from core.bot import get_bot
    bot = get_bot()

    # Connections are held on the bot because asyncio only keeps a weak
    # reference to running tasks — dropping them would let a loop be garbage
    # collected mid-flight.
    bot.bot_list_connections = []

    for connection_class, token_variable in BOT_LIST_CONNECTIONS:
        token = os.environ.get(token_variable, '')
        if not token or token.lower() in ["none", "missing"]:
            logging.warning(f"{token_variable} is not set or is invalid. {connection_class.name} API connection will not be established.")
            continue

        logging.info(f"Setting up {connection_class.name} API connection...")
        try:
            connection = connection_class(bot, token)
            connection.start()
            bot.bot_list_connections.append(connection)
        except Exception as e:
            logging.error(f"Failed to set up {connection_class.name} API connection: {e}")
