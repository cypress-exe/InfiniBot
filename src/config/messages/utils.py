import nextcord
from typing import Any
import datetime

class MessageRecord:
    """
    Represents a stored message. Used to represent both database and cache objects.
    """

    def __init__(self, **kwargs):
        """
        Initialize the MessageRecord object with the given parameters.

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

        An **expensive method** to fetch all data of the message from Discord, using the IDs stored in the MessageRecord object.

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
        Return a string representation of the MessageRecord object.

        :return: A string representation of the object.
        :rtype: str
        """
        return (f"MessageRecord(message_id={self.message_id}, channel_id={self.channel_id}, guild_id={self.guild_id}, "
                f"author_id={self.author_id}, content={self.content}, last_updated={self.last_updated})")

    def __eq__(self, other):
        """
        Check if two MessageRecord objects are equal based on their attributes.

        :param other: The other object to compare with.
        :type other: object
        :return: True if all attributes are equal, False otherwise.
        :rtype: bool
        """
        if not isinstance(other, MessageRecord):
            return False
        
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

def message_checks(message: nextcord.Message | MessageRecord) -> bool:
    """
    Check if a message is valid for caching or storing.

    :param message: The message to check.
    :type message: nextcord.Message | MessageRecord
    :return: True if the message is valid, False otherwise.
    :rtype: bool
    """
    if not message:
        return False
    if hasattr(message, 'guild') and message.guild is None:
        return False
    if hasattr(message, 'author') and hasattr(message.author, 'bot') and message.author.bot:
        return False  # Don't cache bot messages
    return True

def message_to_message_record_type(message: nextcord.Message | MessageRecord) -> MessageRecord:
    """
    Convert a nextcord.Message or MessageRecord object to a MessageRecord object.

    :param message: The message to convert.
    :type message: nextcord.Message | MessageRecord
    :return: A MessageRecord object with the same attributes as the input message.
    :rtype: MessageRecord
    """
    
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

    # Extract message data
    message_id = get_var(message, 'id', 'message_id')
    channel_id = get_var(message, 'channel.id', 'channel_id')
    guild_id = get_var(message, 'guild.id', 'guild_id')
    author_id = get_var(message, 'author.id', 'author_id')
    content = message.content
    last_updated = get_var(message, 'last_updated', 'created_at') or datetime.datetime.now()

    return MessageRecord(
        message_id=message_id,
        channel_id=channel_id,
        guild_id=guild_id,
        author_id=author_id,
        content=content,
        last_updated=last_updated
    )
