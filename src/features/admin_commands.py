import datetime
import inspect
import json
import logging
import os
import sys
import time
from functools import wraps
from typing import Dict, Callable, Any

import nextcord

from config.global_settings import get_configs, get_global_kill_status, get_bot_load_status
from config.server import Server
from components import ui_components, utils
from components.ui_components import CustomView, CustomModal
from components.ui_components import TopGGVoteView

# Bot instance cache to avoid multiple imports
_bot_cache = None

def _get_bot():
    """Get bot instance with caching to avoid circular imports."""
    global _bot_cache
    if _bot_cache is None:
        from core.bot import get_bot
        _bot_cache = get_bot()
    return _bot_cache


# <COMMAND REGISTRY SYSTEM>
# Command registry for decorator-based system
_admin_command_registry: Dict[int, Dict[str, Dict[str, Any]]] = {
    1: {},  # Level 1 commands
    2: {},  # Level 2 commands  
    3: {}   # Level 3 commands
}

def admin_command_level_1(command_name: str, description: str = ""):
    """
    Decorator for Level 1 admin commands (Basic admin commands).
    
    Args:
        command_name (str): The command name (without dashes)
        description (str): Description of the command
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        _admin_command_registry[1][command_name] = {
            'function': wrapper,
            'description': description or f"Level 1 admin command: {command_name}",
            'name': command_name
        }
        return wrapper
    return decorator

def admin_command_level_2(command_name: str, description: str = ""):
    """
    Decorator for Level 2 admin commands (Server management).
    
    Args:
        command_name (str): The command name (without dashes)
        description (str): Description of the command
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        _admin_command_registry[2][command_name] = {
            'function': wrapper,
            'description': description or f"Level 2 admin command: {command_name}",
            'name': command_name
        }
        return wrapper
    return decorator

def admin_command_level_3(command_name: str, description: str = ""):
    """
    Decorator for Level 3 admin commands (System control).
    
    Args:
        command_name (str): The command name (without dashes)
        description (str): Description of the command
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        _admin_command_registry[3][command_name] = {
            'function': wrapper,
            'description': description or f"Level 3 admin command: {command_name}",
            'name': command_name
        }
        return wrapper
    return decorator

def _get_admin_commands():
    """
    Get all registered admin commands from the decorator-based registry.
    
    Returns:
        dict: Dictionary mapping permission levels to command lists
    """
    commands = {
        'level_1': list(_admin_command_registry[1].keys()),
        'level_2': list(_admin_command_registry[2].keys()),
        'level_3': list(_admin_command_registry[3].keys())
    }
    return commands

def _get_command_description(command_name: str, level: int = None) -> str:
    """Get description for a command from the registry."""
    # First try to get from registry if level is provided
    if level and level in _admin_command_registry and command_name in _admin_command_registry[level]:
        return _admin_command_registry[level][command_name]['description']
    
    # Search through all levels if level not specified
    for level_num in [1, 2, 3]:
        if command_name in _admin_command_registry[level_num]:
            return _admin_command_registry[level_num][command_name]['description']
    
    # If not found, return a default message
    return f"No description available for command: {command_name}"
# </COMMAND REGISTRY SYSTEM>


# <GLOBAL KILL FEATURES>
def _get_global_kill_features():
    """
    Dynamically discover all available global kill features from GlobalKillStatus.
    
    Returns:
        dict: Dictionary mapping feature names to their setter functions
    """
    commands = {}
    
    # Try to get features dynamically from GlobalKillStatus
    try:
        # Try to read the global kill status file directly
        try:
            # Create setter functions for each feature
            global_kill_status = get_global_kill_status()
            for feature_name in global_kill_status.variable_list:      
                commands[feature_name] = lambda value, name=feature_name: global_kill_status.set_variable(name, value)
            
            logging.info(f"Dynamically loaded {len(commands)} global kill features")
            
        except Exception as file_error:
            logging.warning(f"Could not read global kill status file: {file_error}")
            raise file_error
    
    except Exception as e:
        logging.warning(f"Could not dynamically load global kill features: {e}")
    
    return commands
# </GLOBAL KILL FEATURES>


# <INFO FORMATTING FUNCTIONS>
def _format_config_as_json(config_dict):
    """
    Format configuration dictionary as pretty-printed JSON.
    
    Args:
        config_dict: The dictionary to format
    
    Returns:
        str: JSON-formatted string with nice indentation
    """
    try:
        return json.dumps(config_dict, indent=2, ensure_ascii=False, default=str)
    except (TypeError, ValueError) as e:
        # Fallback for non-serializable objects
        return f"Error formatting config: {str(e)}\nRaw config: {str(config_dict)}"

def _split_text_into_messages(text, max_length=1800):
    """
    Split text into messages that fit within Discord's character limit.
    
    Args:
        text: The text to split
        max_length: Maximum character length per message (leave room for code block formatting)
    
    Returns:
        list: List of message contents that fit within the character limit
    """
    if not text:
        return []
    
    if len(text) <= max_length:
        return [text]
    
    messages = []
    current_message = ""
    lines = text.split('\n')
    
    for line in lines:
        # Test if adding this line would exceed the limit
        test_message = current_message + "\n" + line if current_message else line
        
        if len(test_message) <= max_length:
            # Line fits - add to current message
            current_message = test_message
        else:
            # Line doesn't fit - finalize current message and start new one
            if current_message:
                messages.append(current_message)
            
            # Handle very long single lines
            if len(line) > max_length:
                # Split long lines at word boundaries if possible
                words = line.split(' ')
                current_line = ""
                
                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    if len(test_line) <= max_length:
                        current_line = test_line
                    else:
                        if current_line:
                            messages.append(current_line)
                        current_line = word
                
                if current_line:
                    current_message = current_line
                else:
                    current_message = ""
            else:
                # Line fits within limit - start new message with it
                current_message = line
    
    # Add any remaining content as final message
    if current_message:
        messages.append(current_message)
    
    return messages
# </INFO FORMATTING FUNCTIONS>


# ---------------------- ENTRYPOINT FOR ADMIN COMMANDS ----------------------
async def check_and_run_admin_commands(message: nextcord.Message):
    """
    Check if a message contains admin commands and execute them if the user has permissions.
    
    Args:
        message (nextcord.Message): The message to check for admin commands
    """
    if not message.content.startswith("-"):
        return
        
    # Get admin configuration
    admin_config = get_configs()['admin-ids']
    level_one_admins = admin_config.get('level-1-admins', [])
    level_two_admins = admin_config.get('level-2-admins', [])
    level_three_admins = admin_config.get('level-3-admins', [])
    
    # Build combined admin lists (higher levels include lower levels)
    all_level_one = level_one_admins + level_two_admins + level_three_admins
    all_level_two = level_two_admins + level_three_admins
    all_level_three = level_three_admins
    
    user_id = message.author.id
    message_content = message.content.lower()
    message_parts = message_content.split(" ")
    command = message_parts[0][1:]  # Remove the leading dash
    
    # Determine user's permission level
    user_level = 0
    if user_id in all_level_three:
        user_level = 3
    elif user_id in all_level_two:
        user_level = 2
    elif user_id in all_level_one:
        user_level = 1
    
    if user_level == 0:
        return  # User has no admin permissions
    
    # Check all command levels the user has access to (higher levels include lower)
    for level in range(1, user_level + 1):
        if command in _admin_command_registry[level]:
            command_info = _admin_command_registry[level][command]
            command_function = command_info['function']
            
            # Execute the command with appropriate arguments based on function signature
            try:
                # Check function signature to determine argument pattern
                sig = inspect.signature(command_function)
                param_count = len([p for p in sig.parameters.values() if p.name != 'self'])
                
                if param_count == 1:
                    # Single parameter functions
                    await command_function(message)
                else:
                    # Multi-parameter functions
                    await command_function(message, message_parts)
            except Exception as e:
                logging.error(f"Error executing command '{command}': {e}")
                embed = nextcord.Embed(
                    title="Command Error",
                    description=f"An error occurred while executing the command: {str(e)}",
                    color=nextcord.Color.red()
                )
                await message.channel.send(embed=embed)
            return
    
    # Command not found - no action needed (not an admin command)

# ------------------------- ADMIN COMMAND HANDLERS --------------------------
# Level 1 Command Handlers
@admin_command_level_1("help", "Display help message for admin commands")
async def handle_help_command(message: nextcord.Message):
    """Display help message for admin commands - dynamically generated."""
    # Get admin configuration to determine user's permission level
    admin_config = get_configs()['admin-ids']
    level_one_admins = admin_config.get('level-1-admins', [])
    level_two_admins = admin_config.get('level-2-admins', [])
    level_three_admins = admin_config.get('level-3-admins', [])
    
    user_id = message.author.id
    user_level = 0
    
    # Determine user's permission level
    if user_id in level_three_admins:
        user_level = 3
    elif user_id in level_two_admins:
        user_level = 2
    elif user_id in level_one_admins:
        user_level = 1
    
    # Get dynamically discovered commands
    admin_commands = _get_admin_commands()
    
    description = ""
    
    # Build help message based on user's permission level
    if user_level >= 1:
        description += "### **Level 1 Commands (Basic Admin)**\n"
        for cmd in sorted(admin_commands['level_1']):
            # Convert command name to proper format
            formatted_cmd = cmd.replace('_', ' ').title()
            description += f"• `-{cmd}`: {_get_command_description(cmd)}\n"
        description += "\n"
    
    if user_level >= 2:
        description += "### **Level 2 Commands (Server Management)**\n"
        for cmd in sorted(admin_commands['level_2']):
            formatted_cmd = cmd.replace('_', ' ').title()
            description += f"• `-{cmd}`: {_get_command_description(cmd)}\n"
        description += "\n"
    
    if user_level >= 3:
        description += "### **Level 3 Commands (System Control)**\n"
        for cmd in sorted(admin_commands['level_3']):
            formatted_cmd = cmd.replace('_', ' ').title()
            description += f"• `-{cmd}`: {_get_command_description(cmd)}\n"
        description += "\n"
    
    if description:
        description += "**Note:** Higher permission levels include all lower level commands."
    else:
        description = "You do not have admin permissions."
    
    # Clean up indentation for mobile
    description = utils.standardize_str_indention(description)
    
    embed = nextcord.Embed(
        title="InfiniBot Admin Commands", 
        description=description, 
        color=nextcord.Color.blue()
    )
    await message.channel.send(embed=embed)
    logging.info(f"{message.author} used the help command")

@admin_command_level_1("stats", "Display bot statistics")
async def handle_stats_command(message: nextcord.Message):
    """Display bot statistics."""
    bot = _get_bot()
    member_count = 0
    server_count = 0
    
    logging.info(f"Stats requested by: {message.author}")
    for guild in bot.guilds:
        server_count += 1
        member_count += guild.member_count

    embed = nextcord.Embed(
        title="Server Stats:", 
        description=f"Server Count: {server_count}\nTotal Members: {member_count}\n\n*A watched pot never boils*", 
        color=nextcord.Color.blue()
    )
    await message.channel.send(embed=embed, view=TopGGVoteView())

@admin_command_level_1("ping", "Display latency diagnosis")
async def handle_ping_command(message: nextcord.Message):
    """Display latency diagnosis."""
    start_time = time.time()
    response_message = await message.channel.send(
        embed=nextcord.Embed(
            title="InfiniBot Diagnosis Ping", 
            description="Pinging...", 
            color=nextcord.Color.blue()
        )
    )
    end_time = time.time()

    latency = (end_time - start_time) * 1000
    await response_message.edit(
        embed=nextcord.Embed(
            title="InfiniBot Diagnosis Ping", 
            description=f"InfiniBot pinged with a high-priority diagnosis ping.\n\nLatency: {latency:.2f} ms.", 
            color=nextcord.Color.blue()
        )
    )

# Level 2 Command Handlers
@admin_command_level_2("info", "Display information about a server or owner")
async def handle_info_command(message: nextcord.Message, message_parts: list):
    """Display information about a server or owner."""
    if len(message_parts) < 2 or not message_parts[1].isdigit():
        embed = nextcord.Embed(
            title="Incorrect Format", 
            description="Format like this: `-info [serverID or ownerID]`", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    bot = _get_bot()
    target_id = int(message_parts[1])
    
    # Find guilds by server ID or owner ID
    guilds: list[nextcord.Guild] = []
    for guild in bot.guilds:
        if guild.id == target_id or guild.owner.id == target_id:
            guilds.append(guild)
    
    if not guilds:
        embed = nextcord.Embed(
            title="Server or Owner Could Not Be Found", 
            description="Make sure you are formatting correctly: `-info [serverID or ownerID]`", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    # If multiple guilds found, display both, and instruct them to choose
    if len(guilds) > 1:
        embed = nextcord.Embed(
            title="Multiple Servers Found", 
            description="Multiple servers or owners match the provided ID. Please specify which one you want information about:\n\n" +
                        "\n".join([f"- {guild.name} ({guild.id})" for guild in guilds]),
            color=nextcord.Color.blue()
        )
        await message.channel.send(embed=embed)
        return
    
    # Display information for the single guild found (because multiple guilds would have been caught earlier)
    guild = guilds[0]
    server = Server(guild.id)
    
    joined_at = guild.me.joined_at.replace(tzinfo=datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)
    duration = now - joined_at
    
    # Convert generator to string representation
    server_config = server.get_debug_info() if server else {}

    # Format configurations as JSON and split into messages
    config_json = _format_config_as_json(server_config)
    config_messages = _split_text_into_messages(config_json)

    # Build the description
    guild_icon = guild.icon.url if guild.icon else None
    guild_name = guild.name if guild.name else "<<MISSING NAME>>"
    guild_name = guild_name.replace("@", "@\u200b")  # Prevent mentions in embed title
    
    description = f"""Owner: {guild.owner} ({guild.owner.id})
    Members: {guild.member_count}

    **Time In Server**: {duration.days} days"""
    
    # Clean up indentation for mobile
    description = utils.standardize_str_indention(description)
    
    embed = nextcord.Embed(
        title=f"Server: {guild_name} ({guild.id})", 
        description=description, 
        color=nextcord.Color.blue()
    )

    embed.set_thumbnail(url=guild_icon)
    embed.set_footer(text=f"Joined at: {joined_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

    await message.channel.send(embed=embed)

    # Send server configurations if available, split into multiple messages if needed
    if config_messages:
        for i, config_content in enumerate(config_messages):
            # Create header for first message, continuation indicator for subsequent ones
            if i == 0:
                header = f"**Server Configurations for {guild.name} ({guild.id})**:"
            else:
                header = ""
            
            # Send message with proper code block formatting
            content = f"{header}\n```json\n{config_content}\n```"
            await message.channel.send(
                content=content
            )

    logging.info(f"{message.author} requested info about the server {guild.name} ({guild.id})")

@admin_command_level_2("reset-server-configs", "Reset a server's configurations to default")
async def handle_reset_server_config_command(message: nextcord.Message, message_parts: list):
    """Reset a server's configurations to default."""
    if len(message_parts) < 2 or not message_parts[1].isdigit():
        embed = nextcord.Embed(
            title="Incorrect Format", 
            description="Format like this: `-reset-server-configs [serverID]`", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    bot = _get_bot()
    server_id = int(message_parts[1])
    
    # Find the guild
    guild = bot.get_guild(server_id)
    if not guild:
        embed = nextcord.Embed(
            title="Server Could Not Be Found", 
            description="Make sure you are formatting correctly: `-reset-server-configs [serverID]`", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    # Reset server configurations
    server = Server(server_id)
    server.remove_all_data()
    
    embed = nextcord.Embed(
        title="Server Configurations Reset", 
        description=f"The configurations for the server {guild.name} ({guild.id}) have been reset to defaults.", 
        color=nextcord.Color.green()
    )
    await message.channel.send(embed=embed)
    logging.info(f"{message.author} reset configurations in the server {guild.name} ({guild.id})")

@admin_command_level_2("infinibot-mod-help", "Display help for InfiniBot Mod role")
async def handle_infinibot_mod_help_command(message: nextcord.Message):
    """Display help for InfiniBot Mod role."""
    description = """**Why do I need the InfiniBot Mod role?**
    Some features require admin privileges. If you're an admin, add the “InfiniBot Mod” role to yourself. This role is automatically created by InfiniBot and unlocks its full feature set.

    **If you don't see the role, do one of the following:**
    - Grant InfiniBot the “Manage Roles” permission.
    - Run the `/create infinibot-mod-role` command.
    - Manually create a role named “Infinibot Mod” (exact spelling) with no permissions."""
    # Clean up indentation for mobile
    description = utils.standardize_str_indention(description)
    
    embed = nextcord.Embed(
        title="InfiniBot Mod Help", 
        description=description, 
        color=nextcord.Color.blurple()
    )
    await message.channel.send(embed=embed)

# Level 3 Command Handlers  
@admin_command_level_3("restart", "Restart the InfiniBot process")
async def handle_restart_command(message: nextcord.Message):
    """Restart the InfiniBot process."""
    embed = nextcord.Embed(
        title="InfiniBot Restarting", 
        description="InfiniBot is restarting.", 
        color=nextcord.Color.green()
    )
    await message.channel.send(embed=embed)
    
    logging.info(f"{message.author} requested InfiniBot to be restarted. Restarting...")
    
    # Restart the process
    python = sys.executable
    os.execl(python, python, *sys.argv)

@admin_command_level_3("global-kill", "Manage global kill switches for InfiniBot features")
async def handle_global_kill_command(message: nextcord.Message, message_parts: list):
    """Manage global kill switches for InfiniBot features - dynamically generated."""
    if len(message_parts) <= 1:
        embed = nextcord.Embed(
            title="Incorrect Format", 
            description="Please include argument(s). Use the `-global-kill list` command for a list of arguments.", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    argument = message_parts[1].lower()
    
    # Get dynamically discovered global kill commands
    commands = _get_global_kill_features()
    
    if argument == "list" or argument == "help":
        if not commands:
            embed = nextcord.Embed(
                title="Global Kill Commands", 
                description="CRITICAL ERROR: No global kill commands found. Please check the configuration.", 
                color=nextcord.Color.red()
            )
            await message.channel.send(embed=embed)
            logging.error("No global kill commands found in configuration.")
            return
        
        embed = nextcord.Embed(
            title="Global Kill Commands", 
            description=(
            "### ONLY USE THESE COMMANDS FOR EMERGENCIES!!! "
            "THIS GOES INTO EFFECT GLOBALLY ACROSS ALL GUILDS INSTANTLY!!!\n\n"
            "Select one of the following features to kill, revive, or get status:\n"
            f"```{"\n".join(sorted(commands.keys()))}\n\n```\n"
            "**Usage:** `-global-kill <feature> <kill|revive|status>`"
            ), 
            color=nextcord.Color.blue()
        )
        await message.channel.send(embed=embed)
        return
    
    if argument in commands:
        if len(message_parts) >= 3:
            action_str = message_parts[2].lower()
            if action_str == "kill":
                action = True
            elif action_str == "revive":
                action = False
            elif action_str == "status":
                # Special case to just return the current status of the feature
                current_status = get_global_kill_status().get_variable(argument)
                status_str = "disabled, meaning that users CANNOT use it." if current_status else "enabled, meaning that users CAN use it."
                embed = nextcord.Embed(
                    title=f"{argument.replace('_', ' ').title()} Status", 
                    description=f"The {argument.replace('_', ' ').title()} feature is currently **{status_str}**.", 
                    color=nextcord.Color.blue()
                )
                await message.channel.send(embed=embed)
                return
            else:
                embed = nextcord.Embed(
                    title="Invalid Argument", 
                    description="Specify whether to `kill`, `revive`, or get `status`.", 
                    color=nextcord.Color.red()
                )
                await message.channel.send(embed=embed)
                return
            
            # Apply the global kill action
            try:
                commands[argument](action) # Looks kinda funny, but this calls the setter function directly
                
                # Create success message
                feature_name = argument.replace("_", " ").title()
                action_past = "killed" if action else "revived"
                description = f"{feature_name} successfully {action_past}."
                
                embed = nextcord.Embed(
                    title="Success", 
                    description=description, 
                    color=nextcord.Color.green()
                )
                await message.channel.send(embed=embed)
                logging.info(f"{message.author} {action_past} {feature_name}")
                return
            except Exception as e:
                embed = nextcord.Embed(
                    title="Error", 
                    description=f"Failed to {action_str} {argument}: {str(e)}", 
                    color=nextcord.Color.red()
                )
                await message.channel.send(embed=embed)
                logging.error(f"Error in global kill command: {e}")
                return
        else:
            embed = nextcord.Embed(
                title="Missing Argument", 
                description="Specify whether to `kill`, `revive`, or get `status`.", 
                color=nextcord.Color.red()
            )
            await message.channel.send(embed=embed)
            return
    else:
        embed = nextcord.Embed(
            title="Invalid Argument", 
            description="Use the `-global-kill list` command for a list of arguments.", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return

@admin_command_level_3("send-message-to-all-servers", "Send a message to all servers. Unreversable!")
async def handle_send_message_to_all_servers_command(message: nextcord.Message):
    """Send a message to all servers. Unreversable!"""
    
    # Early validation - ensure bot is fully loaded
    if not get_bot_load_status():
        await message.channel.send(embed=nextcord.Embed(
            title="Bot Not Fully Loaded", 
            description="InfiniBot is still loading. Please try again later.", 
            color=nextcord.Color.red()
        ))
        return
    
    # Create embed creation UI components
    class EmbedCreationModal(CustomModal):
        def __init__(self, return_callback):
            super().__init__(title="Create Embed Message")
            self.return_callback = return_callback

            self.embed_title = nextcord.ui.TextInput(
                label="Embed Title",
                style=nextcord.TextInputStyle.short,
                required=True,
                max_length=256,
                placeholder="New Update: Lorem Ipsum Dolor Sit Amet"
            )
            self.add_item(self.embed_title)            

            self.embed_description = nextcord.ui.TextInput(
                label="Embed Description",
                style=nextcord.TextInputStyle.paragraph,
                required=False,
                max_length=4000,
                placeholder="Consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
            )
            self.add_item(self.embed_description)

        async def callback(self, interaction):
            await self.return_callback(
                interaction, 
                embed_title=self.embed_title.value, 
                embed_description=self.embed_description.value
            )

    class EmbedCreationView(CustomView):
        def __init__(self, author: nextcord.User):
            super().__init__(timeout=None)
            self.author = author
            self.embed_data = {}
        
        @nextcord.ui.button(label="Create Embed", style=nextcord.ButtonStyle.green)
        async def create_embed_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
            # Permission check
            if interaction.user != self.author:
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="Permission Denied",
                        description="You can't use this button unless you're the one who ran the original command. If you have permissions, try running the `-send-message-to-all-servers` command yourself.",
                        color=nextcord.Color.red()
                    ), 
                    ephemeral=True
                )
                return
            
            # Show modal for embed creation
            modal = EmbedCreationModal(self._handle_modal_submission)
            await interaction.response.send_modal(modal)
            
        async def _handle_modal_submission(self, interaction, **kwargs):
            """Handle modal submission and store embed data."""
            self.embed_data = kwargs
            self.stop()
    
    # Display initial embed creation interface
    initial_embed = nextcord.Embed(
        title="Send Message to All Servers",
        description="Click the button below to create an embed message that will be sent to all servers. This is an unreversable action!",
        color=nextcord.Color.blue()
    )
    initial_embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
    initial_embed.set_footer(text="Note: This message may expire if not used within a reasonable time frame.")
    
    view = EmbedCreationView(message.author)
    status_message = await message.channel.send(embed=initial_embed, view=view)

    # Wait for user to complete embed creation
    await view.wait()

    # Validate embed data was received
    if not view.embed_data:
        await message.channel.send(embed=nextcord.Embed(
            title="Embed Creation Failed", 
            description="The main process did not receive the embed data. Unknown error.", 
            color=nextcord.Color.red()
        ))
        return
    
    # Create the embed to send
    embed_to_send = nextcord.Embed(
        title=view.embed_data.get('embed_title', 'No Title'),
        description=view.embed_data.get('embed_description', 'No Description'),
        color=nextcord.Color.gold()
    )

    # Update status message to show sending progress
    sending_embed = nextcord.Embed(
        title="Sending Message to All Servers",
        description="Sending the attached embed to all servers... This is an unreversable action!",
        color=nextcord.Color.yellow()
    )
    await status_message.edit(embeds=[sending_embed, embed_to_send], view=None)
    
    # Send the embed to all servers
    bot = _get_bot()
    sent_count = 0
    error_count = 0
    support_server_config = get_configs()['support-server']
    support_server_id = support_server_config['support-server-id']

    for guild in bot.guilds:
        try:
            # Determine channel and role mention based on server type
            if guild.id == support_server_id:
                # Special handling for InfiniBot support server
                logging.info("Running special behavior for the InfiniBot Support Server.")
                channel = guild.get_channel(support_server_config['updates-channel-id'])
                role = guild.get_role(support_server_config['infinibot-updates-role-id'])
                role_mention = role.mention if role else ""
            else:
                # Standard server handling
                channel = await utils.get_channel(guild)
                role_mention = ""

            # Send message if channel is available
            if channel:
                await channel.send(
                    content=role_mention,
                    embed=embed_to_send, 
                    view=ui_components.SupportAndInviteView()
                )
                sent_count += 1
                logging.info(f"Sent message to {guild.name} ({guild.id})")
            else:
                logging.warning(f"No suitable channel found in {guild.name} ({guild.id})")
                
        except Exception as e:
            error_count += 1
            logging.error(f"Failed to send message to {guild.name} ({guild.id}): {e}")

    # Create and send final status report
    status_description = f"Successfully sent the message to {sent_count} servers."
    if error_count > 0:
        status_description += f"\nFailed to send to {error_count} servers due to errors."
    else:
        status_description = "All messages sent successfully."

    final_embed = nextcord.Embed(
        title="Message Sent to All Servers",
        description=status_description,
        color=nextcord.Color.green()
    )
    await status_message.edit(embeds=[final_embed, embed_to_send])

@admin_command_level_3("add-admin", "Add a new admin to the system")
async def handle_add_admin_command(message: nextcord.Message, message_parts: list):
    """Add a new admin to the system."""
    if len(message_parts) < 3 or not message_parts[1].isdigit() or not message_parts[2].isdigit():
        embed = nextcord.Embed(
            title="Incorrect Format", 
            description="Format like this: `-add-admin 12345678912345689 [1-3]`", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    user_id = int(message_parts[1])
    user_level = int(message_parts[2])
    
    if not (1 <= user_level <= 3):
        embed = nextcord.Embed(
            title="Incorrect Level", 
            description="Level can only be between 1 and 3.", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    # Get current admin configuration
    admin_config = get_configs()['admin-ids']
    all_admins = admin_config.get('level-1-admins', []) + admin_config.get('level-2-admins', []) + admin_config.get('level-3-admins', [])
    
    if user_id in all_admins:
        embed = nextcord.Embed(
            title="Already Admin", 
            description=f"\"{user_id}\" is already an admin.", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    # Add admin to appropriate level
    level_key = f'level-{user_level}-admins'
    if level_key not in admin_config:
        admin_config[level_key] = []
    
    admin_config[level_key].append(user_id)
    
    # Save configuration  
    configs = get_configs()
    configs['admin-ids'] = admin_config
    
    embed = nextcord.Embed(
        title="Admin Added", 
        description=f"\"{user_id}\" added as an admin (level {user_level})", 
        color=nextcord.Color.green()
    )
    await message.channel.send(embed=embed)
    logging.info(f"{message.author} added {user_id} as level {user_level} admin")

@admin_command_level_3("edit-admin", "Edit an existing admin's level")
async def handle_edit_admin_command(message: nextcord.Message, message_parts: list):
    """Edit an existing admin's level."""
    if len(message_parts) < 3 or not message_parts[1].isdigit() or not message_parts[2].isdigit():
        embed = nextcord.Embed(
            title="Incorrect Format", 
            description="Format like this: `-edit-admin 12345678912345689 [1-3]`", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    user_id = int(message_parts[1])
    new_level = int(message_parts[2])
    
    if not (1 <= new_level <= 3):
        embed = nextcord.Embed(
            title="Incorrect Level", 
            description="Level can only be between 1 and 3.", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    # Get current admin configuration
    admin_config = get_configs()['admin-ids']
    
    # Find and remove user from current level
    found = False
    for level in [1, 2, 3]:
        level_key = f'level-{level}-admins'
        if level_key in admin_config and user_id in admin_config[level_key]:
            admin_config[level_key].remove(user_id)
            found = True
            break
    
    if not found:
        embed = nextcord.Embed(
            title="Not Admin", 
            description=f"\"{user_id}\" is not an admin.", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    # Add user to new level
    new_level_key = f'level-{new_level}-admins'
    if new_level_key not in admin_config:
        admin_config[new_level_key] = []
    
    admin_config[new_level_key].append(user_id)
    
    # Save configuration
    configs = get_configs()
    configs['admin-ids'] = admin_config
    
    embed = nextcord.Embed(
        title="Admin Edited", 
        description=f"\"{user_id}\" was edited to be of level {new_level}", 
        color=nextcord.Color.green()
    )
    await message.channel.send(embed=embed)
    logging.info(f"{message.author} edited {user_id} to level {new_level} admin")

@admin_command_level_3("remove-admin", "Remove an admin from the system")
async def handle_remove_admin_command(message: nextcord.Message, message_parts: list):
    """Remove an admin from the system."""
    if len(message_parts) < 2 or not message_parts[1].isdigit():
        embed = nextcord.Embed(
            title="Incorrect Format", 
            description="Format like this: `-remove-admin 12345678912345689`", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    user_id = int(message_parts[1])
    
    # Get current admin configuration
    admin_config = get_configs()['admin-ids']
    
    # Find and remove user from their current level
    found = False
    for level in [1, 2, 3]:
        level_key = f'level-{level}-admins'
        if level_key in admin_config and user_id in admin_config[level_key]:
            admin_config[level_key].remove(user_id)
            found = True
            break
    
    if not found:
        embed = nextcord.Embed(
            title="Not Admin", 
            description=f"\"{user_id}\" is not an admin.", 
            color=nextcord.Color.red()
        )
        await message.channel.send(embed=embed)
        return
    
    # Save configuration
    configs = get_configs()
    configs['admin-ids'] = admin_config
    
    embed = nextcord.Embed(
        title="Admin Removed", 
        description=f"\"{user_id}\" was removed as an admin.", 
        color=nextcord.Color.green()
    )
    await message.channel.send(embed=embed)
    logging.info(f"{message.author} removed {user_id} as admin")