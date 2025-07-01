import nextcord
import datetime
import logging

from core.db_manager import get_database
from config.messages.utils import *
from config.global_settings import get_configs


def store_message(message: nextcord.Message | MessageRecord, override_checks=False) -> bool:
    """
    Store a message in the database.

    :param message: The message to store in the database.
    :type message: nextcord.Message
    :return: True if the message was added/updated, False if not.
    :rtype: bool
    """

    if not override_checks:
        if message_checks(message) is False:
            logging.debug("Message checks failed, not storing message.")
            return False

    message_record = message_to_message_record_type(message)

    query = """
    INSERT INTO messages 
        (message_id, guild_id, channel_id, author_id, content, last_updated)
        VALUES (:message_id, :guild_id, :channel_id, :author_id, :content, :last_updated)
    ON CONFLICT(message_id) DO UPDATE SET
        content = excluded.content,
        last_updated = CURRENT_TIMESTAMP
    """
    affected_rows = get_database().execute_query(query, {
        'message_id': message_record.message_id,
        'guild_id': message_record.guild_id,
        'channel_id': message_record.channel_id,
        'author_id': message_record.author_id,
        'content': message_record.content,
        'last_updated': message_record.last_updated
    }, commit=True, return_affected_rows=True)

    success = affected_rows > 0
    if success:
        logging.debug(f"Stored message with ID {message_record.message_id} in the database.")

    return success

def get_message(message_id: int) -> MessageRecord | None:
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

    return MessageRecord(
        message_id=result[0],
        guild_id=result[1],
        channel_id=result[2],
        author_id=result[3],
        content=result[4],
        last_updated=datetime.datetime.fromisoformat(result[5])
    )
    

def get_all_messages(guild:nextcord.Guild=None, guild_id=None) -> list[MessageRecord]:
    """
    USE FOR TESTING ONLY! VERY EXPENSIVE!

    Retrieve all messages from the database.

    :param guild: The guild to retrieve messages from. If None, all messages will be retrieved.
    :type guild: nextcord.Guild | None
    :param guild_id: The ID of the guild to retrieve messages from. Ignored if guild is provided.
    :type guild_id: int | None

    :return: A list of MessageRecord objects.
    :rtype: list[MessageRecord]
    """

    guild_id = guild.id if guild else guild_id

    query = "SELECT * FROM messages"
    if guild_id:
        query += " WHERE guild_id = :guild_id"
    result = get_database().execute_query(query, {'guild_id': guild_id} if guild_id else {}, multiple_values=True)

    logging.debug(f"Retrieved {len(result)} messages from the database.")

    messages = []
    for message_data in result:
        message = MessageRecord(
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
    logging.debug(f"Removed message with ID {message_id} from the database.")

def remove_messages_from_guild(guild_id: int):
    """
    Remove all messages from the database for a specific guild.

    :param guild_id: The ID of the guild to remove messages from.
    :type guild_id: int
    """
    query = "DELETE FROM messages WHERE guild_id = :guild_id"
    get_database().execute_query(query, {'guild_id': guild_id}, commit=True)
    logging.info(f"Removed all messages from guild with ID {guild_id} from the database.")

def remove_messages_from_channel(channel_id: int):
    """
    Remove all messages from the database for a specific channel.

    :param channel_id: The ID of the channel to remove messages from.
    :type channel_id: int
    """
    query = "DELETE FROM messages WHERE channel_id = :channel_id"
    get_database().execute_query(query, {'channel_id': channel_id}, commit=True)
    logging.info(f"Removed all messages from channel with ID {channel_id} from the database.")


def cleanup_db(max_messages_to_keep_per_guild=None, max_days_to_keep=None):
    """
    Clean up messages from the database by removing older entries and limiting 
    the total number of messages per guild.

    :param max_messages_to_keep_per_guild: Maximum number of recent messages to keep per guild.
    :type max_messages_to_keep_per_guild: int | None
    :param max_days_to_keep: Maximum age (in days) for messages to remain stored.
    :type max_days_to_keep: int | None
    :return: The total number of messages deleted.
    :rtype: int
    """
    logging.info("Cleaning up the database...")

    total_deleted = 0
    if max_messages_to_keep_per_guild is None:
        max_messages_to_keep_per_guild = get_configs()['discord-message-logging']["max-messages-to-keep-per-guild"]

    if max_days_to_keep is None:
        max_days_to_keep = get_configs()['discord-message-logging']["max-days-to-keep"]

    # Delete messages older than max-days-to-keep (config) days 
    query = f"""
    DELETE FROM messages 
    WHERE last_updated < datetime('now', '-{max_days_to_keep} days');
    """
    total_deleted += get_database().execute_query(query, commit=True, return_affected_rows=True)

    # Delete extra message log entries over max-messages-to-keep-per-guild (config) per guild
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
    total_deleted += get_database().execute_query(query, commit=True, return_affected_rows=True)

    logging.info(f"Cleanup complete. Total deleted: {total_deleted}")
    return total_deleted