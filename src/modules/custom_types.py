import threading
import nextcord

class FalseType(type):
    # Override __bool__ to make the class itself falsy
    def __bool__(cls):
        return False

class _Missing(metaclass=FalseType):
    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    def __bool__(self):
        return False

    def __repr__(self):
        return "_Missing()"
    
    def __str__(self):
        return "MISSING"

MISSING = _Missing
'''A constant value used for cases when there is no value when there should be.'''

class _Unset_Value(metaclass=FalseType):
    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    def __bool__(self):
        return False

    def __repr__(self):
        return "_Unset_Value()"
    
    def __str__(self):
        return "UNSET_VALUE"

UNSET_VALUE = _Unset_Value
'''A constant value used as a placeholder value.'''

class ExpiringSet:
    def __init__(self, expiration_time=5):
        """
        Initialize the set with a specified expiration time for elements.
        :param expiration_time: Time in seconds after which elements expire.
        """
        self.store = set()
        self.expiration_time = expiration_time
        self.lock = threading.Lock()

    def add(self, item):
        """
        Add an item to the set with an expiration time.
        :param item: Item to add.
        """
        with self.lock:
            self.store.add(item)

        # Schedule removal of the item after expiration_time seconds
        threading.Timer(self.expiration_time, self._remove_item, args=[item]).start()

    def remove(self, item):
        """
        Remove an item from the set.
        :param item: Item to remove.
        """
        self._remove_item(item)

    def __contains__(self, item):
        """
        Check if an item exists in the set and hasn't expired.
        :param item: Item to check.
        :return: True if the item exists, False otherwise.
        """
        with self.lock:
            return item in self.store

    def _remove_item(self, item):
        """
        Remove an item from the set. This is called internally by the timer.
        :param item: Item to remove.
        """
        with self.lock:
            self.store.discard(item)   # Use discard to avoid KeyError if the item is not present

    def __repr__(self):
        """
        String representation of the set for debugging.
        """
        with self.lock:
            return repr(self.store)
        
    def __iter__(self):
        """
        Iterate over the items in the set.
        """
        with self.lock:
            return iter(self.store)
        

class MessageInfo:
    """
    Represents a stored message in the database.
    """

    def __init__(self, **kwargs):
        """
        Initialize the MessageInfo object with the given parameters.

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

        An **expensive method** to fetch all data of the message from Discord, using the IDs stored in the MessageInfo object.

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
        Return a string representation of the MessageInfo object.

        :return: A string representation of the object.
        :rtype: str
        """
        return (f"MessageInfo(message_id={self.message_id}, channel_id={self.channel_id}, guild_id={self.guild_id}, "
                f"author_id={self.author_id}, content={self.content}, created_at={self.created_at})")
