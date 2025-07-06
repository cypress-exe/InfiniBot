import logging
import os
import json

import config.global_settings as global_settings

# Calculate optimal shard count based on configuration and previous data
def calculate_shard_count():
    """Calculate optimal shard count based on configuration and stored guild data"""
    try:
        # Check if sharding is enabled in config
        if not global_settings.get_configs()["sharding.enabled"]:
            logging.info("Auto-sharding is disabled in configuration. Using Discord's recommendation.")
            return None
        
        guilds_per_shard = global_settings.get_configs()["sharding.guilds-per-shard"]
        
        # Try to read previous guild count from shard_config.json
        shard_config_path = os.path.join("generated", "configure", "shard_config.json")
        previous_guild_count = 0
        
        try:
            with open(shard_config_path, 'r') as f:
                shard_data = json.load(f)
                previous_guild_count = shard_data.get("last_guild_count", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.info("No previous shard data found. Will calibrate on first startup.")
            return None
        
        if previous_guild_count == 0:
            logging.info("No previous guild count data. Will calibrate on first startup.")
            return None
        
        # Calculate optimal shard count
        calculated_shards = max(1, (previous_guild_count // guilds_per_shard) + 1)
        logging.info(f"Calculated {calculated_shards} shards for {previous_guild_count} guilds ({guilds_per_shard} guilds per shard)")
        
        return calculated_shards
        
    except Exception as e:
        logging.warning(f"Error calculating shard count: {e}. Using Discord's recommendation.")
        return None