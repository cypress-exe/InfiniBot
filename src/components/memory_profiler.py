"""
Memory profiling utilities to help identify memory leaks in production.
"""
import logging
import psutil
import os
import threading
from typing import Dict, Any
from config.messages import cached_messages


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
    
    return {
        'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
        'percent': process.memory_percent(),
        'active_threads': active_threads,
        'cached_messages_total': cache_stats['total_messages'],
        'cached_channels': cache_stats['total_channels'],
    }


def log_memory_stats():
    """
    Log current memory statistics.
    """
    stats = get_memory_stats()
    
    log_msg = "Memory: "
    log_msg += f"{stats['rss_mb']:.1f}MB ({stats['percent']:.1f}%), "
    log_msg += f"Threads: {stats['active_threads']}, "
    log_msg += f"Cached: {stats['cached_messages_total']} msgs / {stats['cached_channels']} channels"
    
    logging.info(log_msg)
