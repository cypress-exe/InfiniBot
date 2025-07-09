import nextcord
import logging
import os
import json
import time
import datetime

import config.global_settings as global_settings

def calculate_shard_count():
    """
    Returns the optimal shard count based on config and previous guild data, or None to use Discord's default.

    :return: The calculated optimal shard count, or None if auto-sharding is disabled or no data is available.
    :rtype: Optional[int]
    """
    # Calculate optimal shard count based on configuration and previous data
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

def log_and_store_shard_distribution(bot: nextcord.Client):
    """
    Logs the bot's shard distribution, saves guild/shard stats for next startup, and suggests sharding adjustments.
    
    Args:
        bot (nextcord.Client): The Discord bot client (with sharding).
    """
    # Log shard distribution and save data for next startup (optimized)
    shard_start = time.time()
    total_guilds = len(bot.guilds)
    shard_guild_counts = {}
    
    # Single iteration through guilds to count by shard
    for guild in bot.guilds:
        shard_id = guild.shard_id
        shard_guild_counts[shard_id] = shard_guild_counts.get(shard_id, 0) + 1
    
    logging.info(f"Shard distribution calculated in {time.time() - shard_start:.2f}s")
    
    # Save guild count data for next startup (async file operations)
    try:
        shard_config_path = os.path.join("generated", "configure", "shard_config.json")
        os.makedirs(os.path.dirname(shard_config_path), exist_ok=True)
        
        # Cache config value to avoid multiple calls
        sharding_config = global_settings.get_configs()["sharding"]
        
        shard_data = {
            "last_guild_count": total_guilds,
            "last_shard_count": bot.shard_count,
            "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "guilds_per_shard_config": sharding_config["guilds-per-shard"]
        }
        
        with open(shard_config_path, 'w') as f:
            json.dump(shard_data, f, indent=2)
            
        logging.info(f"Saved guild count data: {total_guilds} guilds across {bot.shard_count} shards")
        
    except Exception as e:
        logging.warning(f"Could not save shard data: {e}")
    
    # Display shard distribution (optimized)
    if shard_guild_counts:
        logging.info("Shard distribution:")
        max_guilds_per_shard = max(shard_guild_counts.values())
        for shard_id in sorted(shard_guild_counts.keys()):
            guild_count = shard_guild_counts[shard_id]
            logging.info(f"  Shard {shard_id}: {guild_count} guilds")
    
        # Intelligent recommendations (cached config)
        if sharding_config["enabled"]:
            guilds_per_shard = sharding_config["guilds-per-shard"]
            optimal_shards = max(1, (total_guilds // guilds_per_shard) + 1)
            
            if max_guilds_per_shard > guilds_per_shard * 1.5:  # 50% over target
                logging.warning(f"⚠️  HIGH SHARD LOAD: Some shards have {max_guilds_per_shard} guilds (target: {guilds_per_shard}). Consider restarting - next startup will use {optimal_shards} shards.")
            elif bot.shard_count < optimal_shards:
                logging.info(f"💡 SCALING SUGGESTION: Current: {bot.shard_count} shards, Optimal: {optimal_shards} shards. Restart to apply.")
            elif bot.shard_count > optimal_shards * 1.5:  # Over-sharded
                logging.info(f"💡 OPTIMIZATION: You might be over-sharded. Current: {bot.shard_count}, Optimal: {optimal_shards}. Restart to optimize.")
            else:
                logging.info(f"✅ SHARD COUNT: Optimal ({bot.shard_count} shards for {total_guilds} guilds)")
        else:
            logging.info(f"ℹ️  AUTO-SHARDING: Disabled in config. Using Discord's recommendation ({bot.shard_count} shards)")
    else:
        logging.info("No guilds found on any shards.")