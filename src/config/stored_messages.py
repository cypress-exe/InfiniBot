import nextcord
import datetime
import logging
from typing import Any

from core.db_manager import get_database
from config.global_settings import get_configs


class StoredMessage:
    """
    Represents a stored message in the database.
    """

    def __init__(self, **kwargs):
        """
        Initialize the StoredMessage object with the given parameters.

        :param message_id: The ID of the message.
        :type message_id: int
        :param channel_id: The ID of the channel the message is in.
        :type channel_id: int
        :param guild_id: The ID of the guild the message is in.
        :type guild_id: int
        :param author_id: The ID of the author of the message.
        :type author_id: int
        :param content: The content of the message.
        :type content: str
        :param last_updated: The timestamp when the message was created.
        :type last_updated: datetime.datetime
        """
        self.message_id = None
        self.channel_id = None
        self.guild_id = None
        self.author_id = None
        self.content = None
        self.last_updated = None

        # Added for compatibility reasons. Not stored in db, and will always be empty.
        self.embeds = []
        self.attachments = []

        # Unfetched data
        self.guild = None
        self.channel = None
        self.author = None
        self.message = None

        for key, value in kwargs.items():
            setattr(self, key, value)
    
    async def fetch_all_data(self):
        """
        |coro|

        An **expensive method** to fetch all data of the message from Discord, using the IDs stored in the StoredMessage object.

        This method is used to fetch the guild, channel, author and message objects from Discord. Note that this method
        requires the bot to have the appropriate permissions to access the guild, channel and message.

        :return: None
        :rtype: None
        """
        await self.fetch("guild")
        await self.fetch("channel")
        await self.fetch("author")
        await self.fetch("message")

    async def fetch(self, variable):
        """
        |coro|

        Fetch a specific data entity related to the message from Discord using the variable name provided.

        This method retrieves either the guild, channel, author, or message object by utilizing their respective IDs.

        :param variable: The name of the entity to fetch. Valid options are "guild", "channel", "author", "message".
        :type variable: str
        :return: The fetched entity corresponding to the variable.
        :rtype: Union[nextcord.Guild, nextcord.TextChannel, nextcord.User, nextcord.Message]

        :raises ValueError: If the variable name is not one of the recognized options.
        """
        from core.bot import get_bot
        if variable == "guild":
            self.guild = await get_bot().fetch_guild(self.guild_id)
            return self.guild
        elif variable == "channel":
            self.channel = await get_bot().fetch_channel(self.channel_id)
            return self.channel
        elif variable == "author":
            self.author = await get_bot().fetch_user(self.author_id)
            return self.author
        elif variable == "message":
            if not self.channel: await self.fetch("channel")
            self.message = await self.channel.fetch_message(self.message_id)
            return self.message
        
        raise ValueError(f"Invalid variable name: {variable}")

    def __str__(self):
        """
        Return a string representation of the StoredMessage object.

        :return: A string representation of the object.
        :rtype: str
        """
        return (f"StoredMessage(message_id={self.message_id}, channel_id={self.channel_id}, guild_id={self.guild_id}, "
                f"author_id={self.author_id}, content={self.content}, last_updated={self.last_updated})")

    def __eq__(self, other):
        """
        Check if two StoredMessage objects are equal based on their attributes.

        :param other: The other object to compare with.
        :type other: object
        :return: True if all attributes are equal, False otherwise.
        :rtype: bool
        """
        if not isinstance(other, StoredMessage):
            return False
        
        # STart removing one by one to see whwere the issue is.
        
        if str(self.message_id) != str(other.message_id): return False
        if str(self.channel_id) != str(other.channel_id): return False
        if str(self.guild_id) != str(other.guild_id): return False
        if str(self.author_id) != str(other.author_id): return False
        if str(self.content) != str(other.content): return False
        if str(self.last_updated) != str(other.last_updated): return False

        return True
    
    def __hash__(self):
        return hash(
            (str(self.message_id), 
             str(self.channel_id), 
             str(self.guild_id), 
             str(self.author_id), 
             str(self.content), 
             str(self.last_updated))
            )

def store_message(message: nextcord.Message | StoredMessage, override_checks=False):
    """
    Store a message in the database.

    :param message: The message to store in the database.
    :type message: nextcord.Message
    """

    if not override_checks:
        if message == None: return
        if message.guild == None: return
        if message.author.bot == True: return # Don't store bot messages

    def get_var(message, main_name, fallback_name) -> Any:
        """
        Get the value of a variable from the message or fallback to the fallback name.

        :param main_name: The main variable name to check.
        :type main_name: str
        :param fallback_name: The fallback variable name to use if the main variable is None.
        :type fallback_name: str
        :return: The value of the variable.
        :rtype: Any
        """
        def getattr_recursive(name, obj):
            parts = name.split('.')
            for part in parts:
                obj = getattr(obj, part, None)
                if obj is None:
                    return None
            return obj
        
        return getattr_recursive(main_name, message) or getattr_recursive(fallback_name, message)

    query = """
    INSERT INTO messages 
        (message_id, guild_id, channel_id, author_id, content, last_updated)
        VALUES (:message_id, :guild_id, :channel_id, :author_id, :content, :last_updated)
    ON CONFLICT(message_id) DO UPDATE SET
        content = excluded.content,
        last_updated = CURRENT_TIMESTAMP
    """
    get_database().execute_query(query, {
        'message_id': get_var(message, 'id', 'message_id'),
        'guild_id': get_var(message, 'guild.id', 'guild_id'),
        'channel_id': get_var(message, 'channel.id', 'channel_id'),
        'author_id': get_var(message, 'author.id', 'author_id'),
        'content': message.content,
        'last_updated': get_var(message, 'last_updated', 'created_at') or datetime.datetime.now().isoformat()
    }, commit=True)

def get_message(message_id: int) -> StoredMessage | None:
    """
    Retrieve a message from the database by its ID.

    :param message_id: The ID of the message to retrieve.
    :type message_id: int
    :return: The message object or None if not found.
    :rtype: nextcord.Message (Object approximation of parameters)
    """
    query = "SELECT * FROM messages WHERE message_id = :message_id"
    result = get_database().execute_query(query, {'message_id': message_id})

    if not result: return None

    return StoredMessage(
        message_id=result[0],
        guild_id=result[1],
        channel_id=result[2],
        author_id=result[3],
        content=result[4],
        last_updated=datetime.datetime.fromisoformat(result[5])
    )
    

def get_all_messages(guild=None) -> list[StoredMessage]:
    """
    USE FOR TESTING ONLY! VERY EXPENSIVE!

    Retrieve all messages from the database.

    :param guild: The guild to retrieve messages from. If None, all messages will be retrieved.
    :type guild: nextcord.Guild | None

    :return: A list of message objects.
    :rtype: list
    """
    query = "SELECT * FROM messages"
    if guild:
        query += " WHERE guild_id = :guild_id"
    result = get_database().execute_query(query, {'guild_id': guild.id} if guild else {}, multiple_values=True)

    logging.debug(f"Retrieved {len(result)} messages from the database.")

    messages = []
    for message_data in result:
        message = StoredMessage(
            message_id=message_data[0],
            guild_id=message_data[1],
            channel_id=message_data[2],
            author_id=message_data[3],
            content=message_data[4],
            last_updated=datetime.datetime.fromisoformat(message_data[5])
        )
        messages.append(message)

    return messages
    

def remove_message(message_id: int):
    """
    Remove a message from the database by its ID.
    If the message is not found, no action is taken.

    :param message_id: The ID of the message to remove.
    :type message_id: int
    """
    query = "DELETE FROM messages WHERE message_id = :message_id"
    get_database().execute_query(query, {'message_id': message_id}, commit=True)

def remove_messages_from_guild(guild_id: int):
    """
    Remove all messages from the database for a specific guild.

    :param guild_id: The ID of the guild to remove messages from.
    :type guild_id: int
    """
    query = "DELETE FROM messages WHERE guild_id = :guild_id"
    get_database().execute_query(query, {'guild_id': guild_id}, commit=True)

def remove_messages_from_channel(channel_id: int):
    """
    Remove all messages from the database for a specific channel.

    :param channel_id: The ID of the channel to remove messages from.
    :type channel_id: int
    """
    query = "DELETE FROM messages WHERE channel_id = :channel_id"
    get_database().execute_query(query, {'channel_id': channel_id}, commit=True)

def cleanup(max_messages_to_keep_per_guild=None, max_days_to_keep=None):
    
    if max_messages_to_keep_per_guild is None:
        max_messages_to_keep_per_guild = get_configs()['discord-message-logging']["max_messages_to_keep_per_guild"]

    if max_days_to_keep is None:
        max_days_to_keep = get_configs()['discord-message-logging']["max_days_to_keep"]

    # Delete messages older than max_days_to_keep (config) days 
    query = f"""
    DELETE FROM messages 
    WHERE last_updated < datetime('now', '-{max_days_to_keep} days');
    """
    get_database().execute_query(query, commit=True)

    # Delete extra message log entries over max_messages_to_keep_per_guild (config) per guild
    query = f"""DELETE FROM messages
    WHERE rowid IN (
        SELECT rowid
        FROM (
            SELECT rowid,
                ROW_NUMBER() OVER (PARTITION BY guild_id ORDER BY last_updated DESC) AS row_num
            FROM messages
        )
        WHERE row_num > {max_messages_to_keep_per_guild}
    );"""
    get_database().execute_query(query, commit=True)