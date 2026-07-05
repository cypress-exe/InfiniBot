"""
Memory profiling utilities to help identify memory leaks in production.
"""
import logging
import psutil
import os
import threading
from typing import Dict, Any, Optional
from config.messages import cached_messages


def _get_nextcord_cache_stats() -> Optional[Dict[str, int]]:
    """
    Get counts of the things nextcord itself is caching in memory.

    :return: Dictionary of nextcord cache stats, or None if the bot isn't
        connected yet (e.g. before on_ready).
    :rtype: Optional[Dict[str, int]]
    """
    try:
        from core.bot import get_bot
        bot = get_bot()
        connection = bot._connection

        guilds = bot.guilds
        chunked_guilds = sum(1 for guild in guilds if guild.chunked)

        # _view_store._views maps (component_type, message_id, custom_id) -> (view, item),
        # so a single view with N dispatchable items occupies N entries. Both view metrics
        # report on this raw-entry scale (rather than the de-duplicated all_views()) so the
        # duplicated in-memory entries are actually visible and so "active" and "raw_total"
        # stay comparable (active <= raw_total, the difference being unswept/finished entries).
        view_entries = connection._view_store._views.values()
        view_store_active = sum(1 for (view, _item) in view_entries if not view.is_finished())
        view_store_raw_total = len(connection._view_store._views)
        all_modals = list(connection._modal_store._modals.values())

        return {
            'view_store_active': view_store_active,
            'view_store_raw_total': view_store_raw_total,
            'modal_store_active': sum(1 for m in all_modals if not m.is_finished()),
            'modal_store_raw_total': len(all_modals),
            'chunked_guilds': chunked_guilds,
            'total_guilds': len(guilds),
            # Per-guild Member objects (the ~500k-member concern from section 1).
            'cached_members_total': sum(len(guild.members) for guild in guilds),
            # nextcord's global User cache (DM users, message authors, mentions,
            # etc.) - distinct from per-guild Member objects above.
            'cached_users_total': len(connection._users),
            # nextcord's own bounded message cache (max_messages=1000 in
            # src/core/bot.py) - distinct from InfiniBot's own DB-backed message
            # cache reported separately below.
            'nextcord_cached_messages': len(bot.cached_messages),
        }
    except Exception:
        # Bot not ready / not connected yet, or nextcord internals changed.
        return None


def get_memory_stats() -> Dict[str, Any]:
    """
    Get current memory usage statistics.

    :return: Dictionary with memory statistics
    :rtype: Dict[str, Any]
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    cache_stats = cached_messages.get_cache_stats()

    # Count active threads
    active_threads = threading.active_count()

    nextcord_stats = _get_nextcord_cache_stats()

    def _n(key):
        return nextcord_stats[key] if nextcord_stats else None

    return {
        'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
        'percent': process.memory_percent(),
        'active_threads': active_threads,
        'cached_messages_total': cache_stats['total_messages'],
        'cached_channels': cache_stats['total_channels'],
        'view_store_active': _n('view_store_active'),
        'view_store_raw_total': _n('view_store_raw_total'),
        'modal_store_active': _n('modal_store_active'),
        'modal_store_raw_total': _n('modal_store_raw_total'),
        'chunked_guilds': _n('chunked_guilds'),
        'total_guilds': _n('total_guilds'),
        'cached_members_total': _n('cached_members_total'),
        'cached_users_total': _n('cached_users_total'),
        'nextcord_cached_messages': _n('nextcord_cached_messages'),
    }


def log_memory_stats():
    """
    Log current memory statistics.
    """
    stats = get_memory_stats()

    log_msg = "Memory: "
    log_msg += f"{stats['rss_mb']:.1f}MB ({stats['percent']:.1f}%), "
    log_msg += f"Threads: {stats['active_threads']}, "
    log_msg += f"Cached: {stats['cached_messages_total']} msgs / {stats['cached_channels']} channels, "
    log_msg += f"Views: {stats['view_store_active']} active / {stats['view_store_raw_total']} unswept, "
    log_msg += f"Modals: {stats['modal_store_active']} active / {stats['modal_store_raw_total']} unswept, "
    log_msg += f"Chunked: {stats['chunked_guilds']}/{stats['total_guilds']} guilds, "
    log_msg += f"Members: {stats['cached_members_total']}, Users: {stats['cached_users_total']}, "
    log_msg += f"nextcord msgs: {stats['nextcord_cached_messages']}"

    logging.info(log_msg)
