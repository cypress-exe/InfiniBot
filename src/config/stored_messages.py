import nextcord
import datetime
import logging

from core.db_manager import get_database


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
        :param created_at: The timestamp when the message was created.
        :type created_at: datetime.datetime
        """
        self.message_id = None
        self.channel_id = None
        self.guild_id = None
        self.author_id = None
        self.content = None
        self.created_at = None

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
                f"author_id={self.author_id}, content={self.content}, created_at={self.created_at})")


def store_message(message: nextcord.Message):
    """
    Store a message in the database.

    :param message: The message to store in the database.
    :type message: nextcord.Message
    """

    if message == None: return
    if message.guild == None: return
    if message.author.bot == True: return # Don't store bot messages

    query = """
    INSERT INTO messages 
        (message_id, guild_id, channel_id, author_id, content, created_at)
        VALUES (:message_id, :guild_id, :channel_id, :author_id, :content, :created_at)
    """
    get_database().execute_query(query, {
        'message_id': message.id,
        'guild_id': message.guild.id,
        'channel_id': message.channel.id,
        'author_id': message.author.id,
        'content': message.content,
        'created_at': datetime.datetime.now().isoformat()
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
        created_at=datetime.datetime.fromisoformat(result[5])
    )
    

def get_all_messages() -> list[StoredMessage]:
    """
    USE FOR TESTING ONLY! VERY EXPENSIVE!

    Retrieve all messages from the database.

    :return: A list of message objects.
    :rtype: list
    """
    query = "SELECT * FROM messages"
    result = get_database().execute_query(query, multiple_values=True)

    logging.info(f"Retrieved {len(result)} messages from the database.")

    messages = []
    for message_data in result:
        message = StoredMessage(
            message_id=message_data[0],
            guild_id=message_data[1],
            channel_id=message_data[2],
            author_id=message_data[3],
            content=message_data[4],
            created_at=datetime.datetime.fromisoformat(message_data[5])
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