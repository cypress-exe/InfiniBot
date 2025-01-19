import datetime
import logging
from typing import Any

import nextcord
from nextcord import Interaction

from config.global_settings import feature_dependencies, get_global_kill_status


def format_var_to_pythonic_type(_type: str, value: Any) -> Any:
    """
    Format a variable based on its type.

    :param _type: Data type of the variable.
    :type _type: str
    :param value: Value to format.
    :type value: Any
    :return: Formatted value.
    :rtype: Any
    """
    if _type.lower() == "boolean" or _type.lower() == "bool":
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            return value.lower() == "true"
    if _type.lower() == "integer" or _type.lower() == "int":
        if isinstance(value, str):
            return int(value)
    if _type.lower() == "text":
        if isinstance(value, str):
            if value.startswith("'") and value.endswith("'") or value.startswith('"') and value.endswith('"'):
                return format_var_to_pythonic_type(_type, value[1:-1])
            else:
                return value
    return value

def standardize_dict_properties(default_dict: dict, object_dict: dict, aliases: dict = {}) -> dict:
    """
    A recursive function that makes sure that two dictionaries have the same properties.

    :param default_dict: A dictionary containing all the properties and their default values.
    :type default_dict: dict
    :param object_dict: The dictionary that will be edited.
    :type object_dict: dict
    :param aliases: A dictionary of aliases (for backwards compatibility) (ex: {'old':'new'}).
    :type aliases: dict
    :return: The object dictionary after having its properties standardized.
    :rtype: dict
    """

    # cloning default_dict as returnDict
    return_dict = dict(default_dict)
    
    # checking for aliases and changing the dictionary to account for them
    object_dict = {aliases.get(k, k): v for k, v in object_dict.items()}
    
    # for each key:
    for key in return_dict.keys():
        # for each key in returnDict
           
        if key in object_dict.keys():
            # the key was in our objectdict. Now we just have to set it.
            # We have to check this recursively if this is a dictionary, and set this to be the returned value from the recursive function.
            
            if type(object_dict[key]) == dict:
                # this is a dictionary. 
                # Now, we have to run this recursively to make sure that all values inside the dictionary are updated
                return_dict[key] = standardize_dict_properties(return_dict[key], object_dict[key], aliases = aliases)
            else:
                # this is not a dictionary. It's just a regular value
                # putting this value into returnDict
                return_dict[key] = object_dict[key]
        else:
            # the key was not in the object_dict, but it was in the default_dict.
            # but, because the key was already added (as the default), we don't need to worry at all.
            # lower dictionaries that may be attached to this are also not a concern, seeing how it never existed on the object_dict, so the defaults are fine.
            continue
        
    return return_dict

def standardize_str_indention(string: str) -> str:
    """
    Standardize the indentation level of a given string.

    This function takes a string and standardizes the indentation level.
    This is useful for strings that have been formatted with inconsistent indentation levels.

    :param string: The string to standardize the indentation level for.
    :type string: str
    :return: The string with standardized indentation level.
    :rtype: str
    """
    # Split the string into lines
    lines = string.split('\n')

    # Remove the first level of indentation
    for i in range(len(lines)):
        lines[i] = lines[i].lstrip()

    # Iterate through each line and remove unneeded spaces based on the indentation level
    indent_level = 0
    for i in range(len(lines)):
        line = lines[i]
        if len(line) == 0:
            continue  # skip empty lines
        cur_indent_level = len(line) - len(line.lstrip())
        if cur_indent_level > indent_level:
            # Indentation level increased
            indent_level = cur_indent_level
        elif cur_indent_level < indent_level:
            # Indentation level decreased, go back to previous level
            indent_level = cur_indent_level
        # Remove the unneeded spaces
        lines[i] = " " * indent_level + line.lstrip()

    # Join the lines back into a string
    return('\n'.join(lines))

def parse_str_to_time(time_str: str) -> datetime.time:
    """
    Attempt to parse a string as a time of day.

    :param time_str: A string representing the time to be parsed.
    :type time_str: str
    :return: A datetime.time object representing the time.
    :type: datetime.time
    :raises ValueError: If the string cannot be parsed as a time.
    """
    for fmt in ["%I:%M %p", "%H:%M"]:
        try:
            dt = datetime.datetime.strptime(time_str, fmt)
            return dt.time()
        except ValueError:
            pass
    raise ValueError("Invalid time format")

def parse_str_to_datetime(time_str: str) -> datetime.datetime:
    """
    Parse a string as a time of day and return a datetime object with the time set to the parsed value and the date set to January 1, 2000.

    :param time_str: A string representing the time to be parsed (e.g., '2:30 PM' or '14:30').
    :type time_str: str
    :return: A datetime object representing the time.
    :rtype: datetime.datetime
    """
    time_obj = parse_str_to_time(time_str)

    date_obj = datetime.date(2000, 1, 1)
    return datetime.datetime.combine(date_obj, time_obj)

def conversion_local_time_and_utc_time(
    utc_offset: float, local_time_datetime: datetime.datetime = None, utc_time_datetime: datetime.datetime = None
) -> datetime.datetime | datetime.time:
    """
    Convert a given local time to UTC time using a UTC offset.

    :param utc_offset: The UTC offset in hours (e.g., -5.0 for EST).
    :type utc_offset: float
    :param local_time_datetime: The local time to convert.
    :type local_time_datetime: datetime.datetime | None
    :param utc_time_datetime: The UTC time to convert.
    :type utc_time_datetime: datetime.datetime | None
    :return: A `datetime.time` object representing the time in UTC or a `datetime.datetime` object if
        `return_entire_datetime` is True.
    :raises ValueError: If neither local_time_datetime nor utc_time_datetime is provided.
    :raises ValueError: If both local_time_datetime and utc_time_datetime are provided.
    """
    if local_time_datetime == None and utc_time_datetime == None:
        raise ValueError("Either local_time_datetime or utc_time_datetime must be provided.")
    if local_time_datetime != None and utc_time_datetime != None:
        raise ValueError("Either local_time_datetime and utc_time_datetime must be provided, but not both.")
    
    working_time_datetime: datetime.datetime = local_time_datetime if local_time_datetime != None else utc_time_datetime

    # Adjust the time to UTC by subtracting the UTC offset
    if local_time_datetime is None: # Converting from UTC time to local time
        return_datetime = working_time_datetime + datetime.timedelta(hours=utc_offset)
    else: # Converting from local time to UTC time
        return_datetime = working_time_datetime - datetime.timedelta(hours=utc_offset)

    return return_datetime


def get_discord_color_from_string(color: str) -> nextcord.Color:
    """
    Returns a nextcord.Color object based on the given string. If the string is empty or None, returns the default color.
    
    :param color: A string representing the color to be generated.
    :type color: str
    :return: A nextcord.Color object representing the color.
    :rtype: nextcord.Color
    """
    if color == None or color == "": return nextcord.Color.default()

    color = color.lower()
        
    if color == "red": return nextcord.Color.red()
    if color == "green": return nextcord.Color.green()
    if color == "blue": return nextcord.Color.blue()
    if color == "yellow": return nextcord.Color.yellow()
    if color == "white": return nextcord.Color.from_rgb(255, 255, 255) #white
    
    if color == "blurple": return nextcord.Color.blurple()
    if color == "greyple": return nextcord.Color.greyple()
    if color == "teal": return nextcord.Color.teal()
    if color == "purple": return nextcord.Color.purple()
    
    if color == "gold": return nextcord.Color.gold()
    if color == "magenta": return nextcord.Color.magenta()
    if color == "fuchsia": return nextcord.Color.fuchsia()
    
    return nextcord.Color.default()

def get_string_from_discord_color(color: nextcord.colour.Colour) -> str | None:
    """
    Returns a string representing the color based on the given nextcord.Color object. If the color is the default color, returns None.
    
    :param color: A nextcord.Color object representing the color to be generated.
    :type color: nextcord.colour.Colour
    :return: A string representing the color, or None if the color is the default color.
    :rtype: str | None
    """
    if color == None or color == nextcord.Color.default(): return None
        
    if color == nextcord.Color.red(): return "Red"
    if color == nextcord.Color.green(): return "Green"
    if color == nextcord.Color.blue(): return "Blue"
    if color == nextcord.Color.yellow(): return "Yellow"
    if color == nextcord.Color.from_rgb(255, 255, 255): return "White"
    
    if color == nextcord.Color.blurple(): return "Blurple"
    if color == nextcord.Color.greyple(): return "Greyple"
    if color == nextcord.Color.teal(): return "Teal"
    if color ==nextcord.Color.purple(): return  "Purple"
    
    if color == nextcord.Color.gold(): return "Gold"
    if color == nextcord.Color.magenta(): return "Magenta"
    if color == nextcord.Color.fuchsia(): return "Fuchsia"
    
    return None

def replace_placeholders_in_embed(
    embed: nextcord.Embed, 
    member: nextcord.Member, 
    guild: nextcord.Guild, 
    custom_replacements: dict = {}, 
    skip_channel_replacement: bool = False
) -> nextcord.Embed:
    """
    Replaces placeholders in an embed with values from a member and a guild.

    :param embed: The embed to replace placeholders in.
    :type embed: nextcord.Embed
    :param member: The member to use for placeholder replacement.
    :type member: nextcord.Member
    :param guild: The guild to use for placeholder replacement.
    :type guild: nextcord.Guild
    :param custom_replacements: A dictionary of custom placeholder replacements.
    :type custom_replacements: dict
    :param skip_channel_replacement: Whether to skip replacing channel mentions.
    :type skip_channel_replacement: bool
    :return: The modified embed with replaced placeholders.
    :rtype: nextcord.Embed
    """
    replacements = custom_replacements

    # Add default replacements
    replacements["@displayname"] = member.display_name
    replacements["@mention"] = member.mention
    replacements["@username"] = member.name
    replacements["@server"] = guild.name

    # Replace placeholders with values
    for key, value in replacements.items():
        if embed.title:
            embed.title = embed.title.replace(key, value)
        if embed.description:
            embed.description = embed.description.replace(key, value)
        if embed.footer and embed.footer.text:
            embed.footer.text = embed.footer.text.replace(key, value)
        if embed.url:
            embed.url = embed.url.replace(key, value)
        
        for field in embed.fields:
            field.name = field.name.replace(key, value)
            field.value = field.value.replace(key, value)
    
    if not skip_channel_replacement:
        # Optimization: Skip channel replacement if no "#" in the embed
        embed_content = (
            (embed.title or "") +
            (embed.description or "") +
            (embed.footer.text if embed.footer and embed.footer.text else "") +
            "".join(field.name + field.value for field in embed.fields)
        )
        if "#" in embed_content:
            # Replace channel names with mentions
            for channel in guild.text_channels:
                channel_placeholder = f"#{channel.name}"
                channel_mention = channel.mention
                
                if embed.title:
                    embed.title = embed.title.replace(channel_placeholder, channel_mention)
                if embed.description:
                    embed.description = embed.description.replace(channel_placeholder, channel_mention)
                if embed.footer and embed.footer.text:
                    embed.footer.text = embed.footer.text.replace(channel_placeholder, channel_mention)
                
                for field in embed.fields:
                    field.name = field.name.replace(channel_placeholder, channel_mention)
                    field.value = field.value.replace(channel_placeholder, channel_mention)
    
    return embed

def feature_is_active(**kwargs) -> bool:
    """
    Checks if a feature is active for a server (or globally).

    :param server: The server object to check the feature for.
    :type server: Server | None
    :param server_id: The ID of the server to check the feature for.
    :type server_id: int | None
    :param guild: The guild object to check the feature for.
    :type guild: nextcord.Guild | None
    :param guild_id: The ID of the guild to check the feature for.
    :type guild_id: int | None
    :param feature: The name of the feature to check.
    :type feature: str
    :param skip_server_check: If True, skip checking server-specific status.
    :type skip_server_check: bool

    :raises ValueError: If neither a server nor server_id (guild or guild_id) is provided when required.

    :return: True if the feature is active for the server (or globally), False otherwise.
    :rtype: bool
    """
    from config.server import Server

    server:Server = kwargs.get("server")
    if not server:
        if kwargs.get("guild"):
            server_id = kwargs.get("guild").id
        else:
            server_id:int = kwargs.get("server_id") or kwargs.get("guild_id")
        if server_id: server = Server(server_id)

    if server and not isinstance(server, Server):
        raise ValueError(f"Error: {__name__} received an invalid server object. Server: {server}")
        
    feature:str = kwargs.get("feature")
    skip_server_check = kwargs.get("skip_server_check", False)

    # Make feature case insensitive
    feature = feature.lower()

    # Validate feature
    if feature not in feature_dependencies:
        raise ValueError(f"Error: {__name__} received an invalid feature (not in feature_dependencies). Feature: {feature}")

    global_kill_keys = feature_dependencies[feature].get("global_kill", ())
    if not isinstance(global_kill_keys, tuple):
        global_kill_keys = (global_kill_keys,)

    server_feature_keys = feature_dependencies[feature].get("server", ())
    if not isinstance(server_feature_keys, tuple):
        server_feature_keys = (server_feature_keys,)

    # Check if globally killed
    global_kill_statuses = get_global_kill_status()
    for key in global_kill_keys:
        if global_kill_statuses[key]:
            logging.debug(f"Determined that feature {feature} is globally killed. Key: {key}")
            return False

    # Check if feature is enabled in the server
    if not skip_server_check:
        # Validate server
        if len(server_feature_keys) > 0 and server is None:
            raise ValueError(f"Error: {__name__} received server or server_id. A server instance is required for this feature.")

        for key in server_feature_keys:
            path = key.split(".")
            attr = server
            for level in path:
                if not hasattr(attr, level):
                    raise ValueError(f"Error: {__name__} received an invalid path when checking if the feature is enabled in the server. Path: {key}. Level: {level}")
                attr = getattr(attr, level)

            if not isinstance(attr, bool):
                raise ValueError(f"Error: {__name__} received an invalid type when checking if the feature is enabled in the server. Type: {type(attr)}")
            
            if not attr:
                logging.debug(f"Determined that feature {feature} is disabled in the server. Key: {key}")
                return False

    logging.debug(f"Determined that feature {feature} is enabled in the server. Key: {key}")
    return True

def role_assignable_by_infinibot(role: nextcord.Role) -> bool:
    """
    Determines if InfiniBot can assign a role.

    :param role: The role to check.
    :type role: nextcord.Role
    :return: True if the role is assignable by InfiniBot, False otherwise.
    :rtype: bool
    """
    if role.is_default(): return False
    if role.is_integration(): return False
    
    return role.is_assignable()


async def check_and_warn_if_channel_is_text_channel(interaction: Interaction) -> bool:
    """
    |coro|
    
    Checks if the channel in which the interaction was used is a text channel.
    Notifies the user if it is not a text channel.

    :param interaction: The interaction object from the Discord event.
    :type interaction: nextcord.Interaction
    :return: True if the channel is a text channel, False otherwise.
    :rtype: bool
    """
    
    if type(interaction.channel) == nextcord.TextChannel:
        return True
    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = "You can't use that here!", description = "You can only use this command in text channels.", color = nextcord.Color.red()), ephemeral=True)
        return False

async def user_has_config_permissions(interaction: Interaction, notify: bool = True) -> bool:
    """|coro|
    
    Determines if an interaction can be continued if it is protected by InfiniBot Mod. NOT SILENT!!!
    InfiniBot WILL warn the user if they do not have the required permissions.

    Parameters
    ----------
    interaction: Interaction
        The interaction.
    notify: bool, optional
        Whether to notify the user if they fail, by default True

    Returns
    -------
    bool
        Whether or not the interaction can continue.
    """
    
    if interaction.guild.owner == interaction.user: return True
    
    infinibotMod_role = nextcord.utils.get(interaction.guild.roles, name='Infinibot Mod')
    if infinibotMod_role in interaction.user.roles:
        return True

    if notify: await interaction.response.send_message(embed = nextcord.Embed(title = "Missing Permissions", description = "You need to have the Infinibot Mod role to use this command.\n\nType `/help infinibot_mod` for more information.", color = nextcord.Color.red()), ephemeral = True)
    return False

async def check_text_channel_permissions(channel: nextcord.TextChannel, auto_warn: bool, custom_channel_name: str = None) -> bool:
    """
    Ensure that InfiniBot has permissions to send messages and embeds in a channel.

    :param channel: The channel to check.
    :type channel: nextcord.TextChannel
    :param auto_warn: Whether or not to warn the guild's owner if InfiniBot does NOT have the required permissions.
    :type auto_warn: bool
    :param custom_channel_name: If warning the owner, specifies a specific name for the channel instead of the default channel name. Defaults to None.
    :type custom_channel_name: str, optional
    :return: Whether or not InfiniBot has permissions to send messages and embeds in the channel.
    :rtype: bool
    """    
    
    if channel == None:
        return False
    
    if channel.guild == None:
        return False
    
    if channel.guild.me == None:
        return False
    
    channel_name = (custom_channel_name if custom_channel_name else channel.name)
    
    if channel.permissions_for(channel.guild.me).view_channel:
        if channel.permissions_for(channel.guild.me).send_messages:
            if channel.permissions_for(channel.guild.me).embed_links:
                return True
            elif auto_warn:
                await send_error_message_to_server_owner(channel.guild, "Embed Links", channel = channel_name, administrator = False)
        elif auto_warn:
            await send_error_message_to_server_owner(channel.guild, "Send Messages and/or Embed Links", channel = channel_name, administrator = False)
    elif auto_warn:
        await send_error_message_to_server_owner(channel.guild, "View Channels", channel = channel_name, administrator = False)

    return False

async def send_error_message_to_server_owner(
    guild: nextcord.Guild, 
    permission: str, 
    message: str = None, 
    administrator: bool = True, 
    channel: str = None, 
    guild_permission: bool = False
) -> None:
    """
    Sends an error message to the owner of the server via DM (Direct Message).

    :param guild: The guild in which the error occured.
    :type guild: nextcord.Guild
    :param permission: The permission needed.
    :type permission: str
    :param message: A custom message to send (the opt out info is appended to this). Defaults to None.
    :type message: str, optional
    :param administrator: Whether to include info about giving InfiniBot adminstrator. Defaults to True.
    :type administrator: bool, optional
    :param channel: The channel where the permission is needed. Defaults to None (meaning the message says "one or more channels").
    :type channel: str, optional
    :param guild_permission: Whether the permission is a guild permission. If so, channel (↑) is overwritten. Defaults to False.
    :type guild_permission: bool, optional
    :return: None
    :rtype: None
    """
    
    if not guild:
        logging.warning("No guild found for send_error_message_to_server_owner")
        return
    
    logging.info(f"Sending error message to server owner (guild_id: {guild.id}). ({guild}, {permission}, {message}, {administrator}, {channel}, {guild_permission})")
    member = guild.owner
    
    # Make sure the member has DMs enabled in their profile settings for InfiniBot
    from config.member import Member # Avoids cyclic import
    if member == None: return
    member_settings = Member(member.id)
    if not member_settings.direct_messages_enabled: return
    
    # UI stuff
    if channel != None:
        channels = channel
    else:
        channels = "one or more channels"
        
    if guild_permission:
        in_channels = ""
    else:
        in_channels = f" in {channels}"
        
    
    
    if message == None:
        if permission != None: 
            embed = nextcord.Embed(title = f"Missing Permissions in in \"{guild.name}\" Server", description = f"InfiniBot is missing the **{permission}** permission{in_channels}.\n\nWe advise that you grant InfiniBot administrator privileges so that this is no longer a concern.", color = nextcord.Color.red())
        else:
            embed = nextcord.Embed(title = f"Missing Permissions in \"{guild.name}\" Server", description = f"InfiniBot is missing a permission{in_channels}.\n\nWe advise that you grant InfiniBot administrator privileges so that this is no longer a concern.", color = nextcord.Color.red())
    else:
        embed = nextcord.Embed(title = f"Missing Permissions in \"{guild.name}\" Server", description = f"{message}", color = nextcord.Color.red())

    embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
    embed.timestamp = datetime.datetime.now()

    try:
        dm = await member.create_dm()
        if administrator:
            await dm.send(embed = embed) # TODO add ErrorWhyAdminPrivilegesButton()
        else:
            await dm.send(embed = embed)
    except:
        return
    
async def check_server_for_infinibot_mod_role(guild: nextcord.Guild) -> bool:
    """
    Check to see if InfiniBot Mod role exists. If not, create it.

    :param guild: The guild in which to check.
    :type guild: nextcord.Guild
    :return: True if the role was created. False if it already existed, or the process failed.
    :rtype: bool
    """
    
    if not guild:
        logging.warning("No guild found for check_server_for_infinibot_mod_role")
        return False
    
    roles = guild.roles
    for x in range(0, len(roles)): roles[x] = roles[x].name

    if not "Infinibot Mod" in roles:
        try:
            await guild.create_role(name = "Infinibot Mod")
            return True
        except nextcord.errors.Forbidden:
            await send_error_message_to_server_owner(guild, None, 
                                                     message = "InfiniBot is missing the **Manage Roles** permission which prevents it from creating the role *InfiniBot Mod*. Please give InfiniBot this permission.", 
                                                     administrator=False)
            return False
    else:
        return False

async def timeout(member: nextcord.Member, seconds: int, reason: str = None) -> str | None:
    """
    |coro|

    Handles the timing out of a member.

    :param member: The member to time out.
    :type member: nextcord.Member
    :param seconds: The timeout time in seconds.
    :type seconds: int
    :param reason: The reason that appears in the audit log. Defaults to None.
    :type reason: str, optional

    :return: A string indicating the result of the timeout operation or None.
    :rtype: str | None
    - "Success revoked" - If the member was successfully un-timed out
    - "Success granted" - If the member was successfully timed out
    - "Failure Forbidden" - If the member could not be timed out due to missing permissions
    - "Failure Unknown" - If the member could not be timed out due to an error
    """
    # Check permissions
    if not member.guild.me.guild_permissions.moderate_members:
        await send_error_message_to_server_owner(member.guild, None, 
                                                 message = "InfiniBot is missing the **Moderate Members** permission which prevents it from timing out members.", 
                                                 administrator=False)
        return "Success revoked"

    try:
        if seconds == 0: await member.edit(timeout=None, reason = reason)
        else: await member.edit(timeout=nextcord.utils.utcnow()+datetime.timedelta(seconds=seconds), reason = reason)
        return "Success granted"
    except nextcord.errors.Forbidden:
        logging.debug(f"Missing permissions to timeout member {member.id} in guild {member.guild.id}")
        return "Failure Forbidden"
    except Exception as e:
        logging.error(f"Error timing out member {member.id} in guild {member.guild.id}: {e}", exc_info=True)
        return "Failure Unknown"