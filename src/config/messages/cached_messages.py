import nextcord
import logging
from typing import Any, Dict, List
from collections import deque

from config.messages.utils import *

# Global cache storage - dictionary mapping channel_id to deque of messages
# Each channel has a maximum of 25 messages (FIFO)
_message_cache: Dict[int, deque] = {}
_MAX_CACHE_SIZE = 25

def cache_message(message: nextcord.Message | MessageRecord, override_checks=False) -> bool:
    """
    Cache a message in memory with FIFO behavior per channel.

    :param message: The message to cache in memory.
    :type message: nextcord.Message | MessageRecord
    :param override_checks: Whether to override standard checks (bot messages, etc.)
    :type override_checks: bool
    :return: True if the message was cached, False if not.
    :rtype: bool
    """
    global _message_cache

    if not override_checks:
        if message_checks(message) is False:
            logging.debug("Message checks failed, not caching message.")
            return False

    message_record = message_to_message_record_type(message)

    if message_record.channel_id is None:
        return False

    # Initialize channel cache if it doesn't exist
    if message_record.channel_id not in _message_cache:
        _message_cache[message_record.channel_id] = deque(maxlen=_MAX_CACHE_SIZE)

    # Check if message already exists in cache and update it
    channel_cache = _message_cache[message_record.channel_id]
    for i, existing_msg in enumerate(channel_cache):
        if existing_msg.message_id == message_record.message_id:
            # Update existing message
            channel_cache[i] = message_record
            logging.debug(f"Updated cached message with ID {message_record.message_id} in channel {message_record.channel_id}.")
            return True

    # Add new message to cache (FIFO will automatically remove oldest if at max capacity)
    channel_cache.append(message_record)
    logging.debug(f"Cached message with ID {message_record.message_id} in channel {message_record.channel_id}. Cache size: {len(channel_cache)}")
    
    return True

def get_cached_message(message_id: int, channel_id: int = None) -> MessageRecord | None:
    """
    Retrieve a cached message by its ID, optionally within a specific channel.

    :param message_id: The ID of the message to retrieve.
    :type message_id: int
    :param channel_id: The ID of the channel to search in. If None, searches all channels.
    :type channel_id: int | None
    :return: The cached message object or None if not found.
    :rtype: MessageRecord | None
    """
    global _message_cache

    if channel_id is not None:
        # Search in specific channel
        if channel_id in _message_cache:
            for msg in _message_cache[channel_id]:
                if msg.message_id == message_id:
                    return msg
    else:
        # Search in all channels
        for channel_cache in _message_cache.values():
            for msg in channel_cache:
                if msg.message_id == message_id:
                    return msg

    return None

def get_cached_messages_from_channel(channel_id: int) -> List[MessageRecord]:
    """
    Retrieve all cached messages from a specific channel.

    :param channel_id: The ID of the channel to retrieve messages from.
    :type channel_id: int
    :return: A list of MessageRecord objects from the channel.
    :rtype: List[MessageRecord]
    """
    global _message_cache

    if channel_id not in _message_cache:
        return []

    return list(_message_cache[channel_id])


def get_all_cached_messages() -> Dict[int, List[MessageRecord]]:
    """
    Retrieve all cached messages organized by channel.

    :return: A dictionary mapping channel_id to list of MessageRecord objects.
    :rtype: Dict[int, List[MessageRecord]]
    """
    global _message_cache

    result = {}
    for channel_id, channel_cache in _message_cache.items():
        result[channel_id] = list(channel_cache)

    return result


def remove_cached_message(message_id: int, channel_id: int = None) -> bool:
    """
    Remove a cached message by its ID.

    :param message_id: The ID of the message to remove.
    :type message_id: int
    :param channel_id: The ID of the channel to search in. If None, searches all channels.
    :type channel_id: int | None
    :return: True if the message was found and removed, False otherwise.
    :rtype: bool
    """
    global _message_cache

    if channel_id is not None:
        # Remove from specific channel
        if channel_id in _message_cache:
            channel_cache = _message_cache[channel_id]
            for i, msg in enumerate(channel_cache):
                if msg.message_id == message_id:
                    del channel_cache[i]
                    logging.debug(f"Removed cached message with ID {message_id} from channel {channel_id}.")
                    return True
    else:
        # Remove from all channels
        for channel_id, channel_cache in _message_cache.items():
            for i, msg in enumerate(channel_cache):
                if msg.message_id == message_id:
                    del channel_cache[i]
                    logging.debug(f"Removed cached message with ID {message_id} from channel {channel_id}.")
                    return True

    return False

def remove_cached_messages_from_channel(channel_id: int) -> int:
    """
    Remove all cached messages from a specific channel.

    :param channel_id: The ID of the channel to remove messages from.
    :type channel_id: int
    :return: The number of messages removed.
    :rtype: int
    """
    global _message_cache

    if channel_id not in _message_cache:
        return 0

    count = len(_message_cache[channel_id])
    del _message_cache[channel_id]
    logging.info(f"Removed {count} cached messages from channel with ID {channel_id}.")
    return count

def remove_cached_messages_from_guild(guild_id: int) -> int:
    """
    Remove all cached messages from a specific guild.

    :param guild_id: The ID of the guild to remove messages from.
    :type guild_id: int
    :return: The number of messages removed.
    :rtype: int
    """
    global _message_cache

    total_removed = 0
    channels_to_remove = []

    for channel_id, channel_cache in _message_cache.items():
        # Check if any message in this channel belongs to the guild
        messages_to_remove = []
        for i, msg in enumerate(channel_cache):
            if msg.guild_id == guild_id:
                messages_to_remove.append(i)

        # Remove messages in reverse order to maintain indices
        for i in reversed(messages_to_remove):
            del channel_cache[i]
            total_removed += 1

        # If channel is now empty, mark it for removal
        if len(channel_cache) == 0:
            channels_to_remove.append(channel_id)

    # Remove empty channels
    for channel_id in channels_to_remove:
        del _message_cache[channel_id]

    logging.info(f"Removed {total_removed} cached messages from guild with ID {guild_id}.")
    return total_removed


def clear_all_cached_messages() -> int:
    """
    Clear all cached messages from memory.

    :return: The total number of messages cleared.
    :rtype: int
    """
    global _message_cache

    total_count = sum(len(channel_cache) for channel_cache in _message_cache.values())
    _message_cache.clear()
    logging.info(f"Cleared all {total_count} cached messages from memory.")
    return total_count

def get_cache_stats() -> Dict[str, Any]:
    """
    Get statistics about the current message cache.

    :return: Dictionary containing cache statistics.
    :rtype: Dict[str, Any]
    """
    global _message_cache

    total_messages = sum(len(channel_cache) for channel_cache in _message_cache.values())
    channel_count = len(_message_cache)
    
    channel_stats = {}
    for channel_id, channel_cache in _message_cache.items():
        channel_stats[channel_id] = len(channel_cache)

    return {
        'total_messages': total_messages,
        'total_channels': channel_count,
        'max_cache_size_per_channel': _MAX_CACHE_SIZE,
        'channel_message_counts': channel_stats
    }
