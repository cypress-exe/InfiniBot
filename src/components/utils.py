import datetime
import logging
import math

import dateparser
import nextcord
from nextcord import Interaction

from config.global_settings import feature_dependencies, get_global_kill_status
from config.member import Member

def format_var_to_pythonic_type(_type:str, value):
  """
  Format a variable based on its type.

  Args:
      _type (str): Data type of the variable.
      value (any): Value to format.

  Returns:
      any: Formatted value.
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

def standardize_dict_properties(default_dict: dict, object_dict: dict, aliases: dict = {}):
    """A recursive function that makes sure that two dictionaries have the same properties.

    ------
    Parameters
    ------
    default_dict: `dict`
        A dictionary containing all the properties and their default values.
    object_dict: `dict`
        The dictionary that will be edited.
        
    Optional Parameters
    ------
    aliases: optional [`dict`]
        A dictionary of aliases (for backwards compatibility) (ex: {'old':'new'}).
        
    Returns
    ------
    `dict`
        The object dictionary after having its properties standardized.
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

def standardize_str_indention(string: str):
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

def calculate_utc_offset(user_date_str, user_time_str):
    """
    Calculate the UTC offset based on the provided date and time strings.

    This function parses a wide variety of date and time formats using `dateparser`,
    calculates the difference between the provided datetime and the current UTC time,
    and snaps the offset to the nearest quarter-hour.

    Args:
        user_date_str (str): The date string (e.g., "11/24/2024", "November 24, 2024").
        user_time_str (str): The time string (e.g., "15:30", "3:30 PM").

    Returns:
        float: The snapped UTC offset in hours (rounded to the nearest 15 minutes).

    Raises:
        ValueError: If the date or time string cannot be parsed.
    """
    # Parse the user-provided date and time
    user_datetime = dateparser.parse(f"{user_date_str} {user_time_str}")

    if not user_datetime:
        raise ValueError("Invalid date or time format. Please provide a recognizable format.")

    # Get the current UTC time
    utc_now = datetime.datetime.now(datetime.timezone.utc)

    # Calculate the UTC offset as a timedelta
    offset = user_datetime - utc_now.replace(tzinfo=None)

    # Convert timedelta to hours
    offset_hours = offset.total_seconds() / 3600

    # Snap to the nearest 15 minutes (0.25 hours)
    snapped_offset = round(offset_hours * 4) / 4

    # Return the calculated offset
    return snapped_offset

def conversion_local_time_and_utc_time(utc_offset, local_time_str=None, utc_time_str=None, return_entire_datetime=False):
    """
    Convert a given local time string to UTC time using a UTC offset.

    Args:
        utc_offset (float): The UTC offset in hours (e.g., -5.0 for EST).
        time_str (str, optional): The time string to parse (e.g., "5:21 PM", "17:21").
        utc_time_str (str, optional): The UTC time string to parse (e.g., "22:21", "5:21 PM").
        return_entire_datetime (bool, optional): If True, returns a datetime object instead of just the time.

    Returns:
        time: A `datetime.time` object representing the time in UTC.

    Raises:
        ValueError: If neither local_time_str nor utc_time_str is provided.
        ValueError: If both local_time_str and utc_time_str are provided.
        ValueError: If the time string cannot be parsed.
    """
    if local_time_str == None and utc_time_str == None:
        raise ValueError("Either local_time_str or utc_time_str must be provided.")
    if local_time_str != None and utc_time_str != None:
        raise ValueError("Either local_time_str and utc_time_str must be provided, but not both.")
    
    working_time_str = local_time_str if local_time_str != None else utc_time_str

    # Parse the time string into a datetime object
    parsed_time = dateparser.parse(working_time_str)
    if not parsed_time:
        raise ValueError("Invalid time format. Please provide a recognizable time format.")

    # Extract the time component
    local_time = parsed_time.time()

    # Convert local time to a datetime object for arithmetic
    dummy_date = datetime.datetime(2000, 1, 1, local_time.hour, local_time.minute, local_time.second)

    # Adjust the time to UTC by subtracting the UTC offset
    if local_time_str != None: # Converting from local time to UTC time
        utc_datetime = dummy_date - datetime.timedelta(hours=utc_offset)
    else: # Converting from UTC time to local time
        utc_datetime = dummy_date + datetime.timedelta(hours=utc_offset)

    if return_entire_datetime:
        return utc_datetime
    else:
        # Return only the time component
        return utc_datetime.time()


def get_discord_color_from_string(color: str):
    if color == None or color == "": return nextcord.Color.default()
        
    if color == "Red": return nextcord.Color.red()
    if color == "Green": return nextcord.Color.green()
    if color == "Blue": return nextcord.Color.blue()
    if color == "Yellow": return nextcord.Color.yellow()
    if color == "White": return nextcord.Color.from_rgb(255, 255, 255) #white
    
    if color == "Blurple": return nextcord.Color.blurple()
    if color == "Greyple": return nextcord.Color.greyple()
    if color == "Teal": return nextcord.Color.teal()
    if color == "Purple": return nextcord.Color.purple()
    
    if color == "Gold": return nextcord.Color.gold()
    if color == "Magenta": return nextcord.Color.magenta()
    if color == "Fuchsia": return nextcord.Color.fuchsia()
    
    return nextcord.Color.default()

def get_string_frolm_discord_color(color: nextcord.colour.Colour):
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

def feature_is_active(**kwargs):
    """
    Checks if a feature is active for a server (or globally).

    Args:
        server (Server, optional): The server object to check the feature for.
        server_id (int, optional): The ID of the server to check the feature for.
        guild_id (in, optional): The ID of the guild to check the feature for.
        feature (str): The name of the feature to check.

    Returns:
        bool: True if the feature is active for the server (or globally), False otherwise.
    """
    from config.server import Server

    server:Server = kwargs.get("server")
    server_id:int = kwargs.get("server_id")
    if kwargs.get("guild_id"): server_id:int = kwargs.get("guild_id")
    feature:str = kwargs.get("feature")

    # Validate inputs
    if not server and not server_id:
        raise ValueError(f"Error: {__name__} received no server or server_id.")
    if not feature:
        raise ValueError(f"Error: {__name__} received no feature.")
    
    if not server:
        server = Server(server_id)

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
    for key in server_feature_keys:
        path = key.split(".")
        attr = server
        for level in path:
            if not hasattr(attr, level):
                raise ValueError(f"Error: {__name__} received an invalid path when checking if the feature is enabled in the server. Path: {key}")
            attr = getattr(attr, level)

        if not isinstance(attr, bool):
            raise ValueError(f"Error: {__name__} received an invalid type when checking if the feature is enabled in the server. Type: {type(attr)}")
        
        if not attr:
            logging.debug(f"Determined that feature {feature} is disabled in the server. Key: {key}")
            return False

    logging.debug(f"Determined that feature {feature} is enabled in the server. Key: {key}")
    return True

def convert_score_and_level(score: int = None, level: int = None):
    if score != None: # CALCULATING LEVEL
        score /= 10
        if score == 0: return 0
        return(math.floor(score ** 0.65)) # levels are calculated by x^0.65
    
    elif level != None: # CALCULATING SCORE
        if level == 0: return 0
    
        score = level**(1/0.65)
        score *= 10
        score = math.floor(score)
        
        for _ in range(0, 100):
            if convert_score_and_level(score=score) == level:
                return score
            elif convert_score_and_level(score=score) > level:
                score -= 1
            else:
                score += 1
        
        return(score) #levels are calculated by x^0.65
    
    else:
        raise ValueError(f"Error: {__name__} received no score or level.")

def role_assignable_by_infinibot(role: nextcord.Role):
    """Determins if InfiniBot can assign a role.

    ------
    Parameters
    ------
    role: `nextcord.Role`
        The role to check

    Returns
    ------
    `bool`
        True if assignable, False if not.
    """    
    if role.is_default(): return False
    if role.is_integration(): return False
    
    return role.is_assignable()


async def check_and_warn_if_channel_is_text_channel(interaction: Interaction):
    """|coro|
    
    Check to see if the channel that this `Interaction` was used in was a `Text Channel`.
    Notifies the user if this was not a `Text Channel`. Recommened to immediately return if this function returns False.

    ------
    Parameters
    ------
    interaction: `nextcord.Interaction`
        The interaction.

    Returns
    ------
    `bool`
        Whether or not this is a text channel.
    """    
    
    if type(interaction.channel) == nextcord.TextChannel:
        return True
    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = "You can't use that here!", description = "You can only use this command in text channels.", color = nextcord.Color.red()), ephemeral=True)
        return False

async def user_has_config_permissions(interaction: Interaction, notify = True):
    """|coro|
    
    Determines if an interaction can be continued if it is protected by InfiniBot Mod. NOT SILENT!!!
    InfiniBot WILL warn the user if they do not have the required permissions.

    ------
    Parameters
    ------
    interaction: `nextcord.Interaction`
        The interaction.
        
    Optional Parameters
    ------
    notify: optional [`bool`]
        Whether to notify the user if they fail. Defaults to True.

    Returns
    ------
    `bool`
        Whether or not the interaction can continue.
    """
    
    if interaction.guild.owner == interaction.user: return True
    
    infinibotMod_role = nextcord.utils.get(interaction.guild.roles, name='Infinibot Mod')
    if infinibotMod_role in interaction.user.roles:
        return True

    if notify: await interaction.response.send_message(embed = nextcord.Embed(title = "Missing Permissions", description = "You need to have the Infinibot Mod role to use this command.\n\nType `/help infinibot_mod` for more information.", color = nextcord.Color.red()), ephemeral = True)
    return False

async def check_text_channel_permissions(channel: nextcord.TextChannel, auto_warn: bool, custom_channel_name: str = None):
    """|coro|
    
    Ensure that InfiniBot has permissions to send messages and embeds in a channel.

    ------
    Parameters
    ------
    channel: `nextcord.TextChannel`
        The channel to check.
    auto_warn: `bool`
        Whether or not to warn the guild's owner if InfiniBot does NOT have the required permissions.
        
    Optional Parameters
    ------
    custom_channel_name: optional [`str`]
        If warning the owner, custom_channel_name specifies a specific name for the channel instead of the default channel name. Defaults to None.

    Returns
    ------
    `bool`
        Whether or not InfiniBot has permissions to send messages and embeds in the channel.
    """    
    
    if channel == None:
        return False
    
    if channel.guild == None:
        return False
    
    if channel.guild.me == None:
        return False
    
    channelName = (custom_channel_name if custom_channel_name else channel.name)
    
    if channel.permissions_for(channel.guild.me).view_channel:
        if channel.permissions_for(channel.guild.me).send_messages:
            if channel.permissions_for(channel.guild.me).embed_links:
                return True
            elif auto_warn:
                await send_error_message_to_server_owner(channel.guild, "Embed Links", channel = channelName, administrator = False)
        elif auto_warn:
            await send_error_message_to_server_owner(channel.guild, "Send Messages and/or Embed Links", channel = channelName, administrator = False)
    elif auto_warn:
        await send_error_message_to_server_owner(channel.guild, "View Channels", channel = channelName, administrator = False)

    return False

async def send_error_message_to_server_owner(guild: nextcord.Guild, permission, message = None, administrator = True, channel = None, guild_permission = False):
    """|coro|
    
    Sends an error message to the owner of the server via dm

    ------
    Parameters
    ------
    guild: `nextcord.Guild` 
        The guild in which the error occured.
    permission: `str`
        The permission needed.

    Optional Parameters
    ------
    message: `str`
        A custom message to send (the opt out info is appended to this). Defaults to None.
    administrator: `bool`
        Whether to include info about giving InfiniBot adminstrator. Defaults to True.
    channel: `str`
        The channel where the permission is needed. Defaults to None (meaning the message says "one or more channels").
    guild_permission: `bool`
        Whether the permission is a guild permission. If so, channel (↑) is overwritten. Defaults to False.

    Returns
    ------
        `None`
    """
    
    if not guild:
        logging.warning("No guild found for send_error_message_to_server_owner")
        return
    
    logging.info(f"Sending error message to server owner (guild_id: {guild.id}). ({guild}, {permission}, {message}, {administrator}, {channel}, {guild_permission})")
    member = guild.owner
    
    # Make sure the member has DMs enabled in their profile settings for InfiniBot
    if member == None: return
    member_settings = Member(member.id)
    if not member_settings.direct_messages_enabled: return
    
    # UI stuff
    if channel != None:
        channels = channel
    else:
        channels = "one or more channels"
        
    if guild_permission:
        inChannels = ""
    else:
        inChannels = f" in {channels}"
        
    
    
    if message == None:
        if permission != None: 
            embed = nextcord.Embed(title = f"Missing Permissions in in \"{guild.name}\" Server", description = f"InfiniBot is missing the **{permission}** permission{inChannels}.\n\nWe advise that you grant InfiniBot administrator privileges so that this is no longer a concern.", color = nextcord.Color.red())
        else:
            embed = nextcord.Embed(title = f"Missing Permissions in \"{guild.name}\" Server", description = f"InfiniBot is missing a permission{inChannels}.\n\nWe advise that you grant InfiniBot administrator privileges so that this is no longer a concern.", color = nextcord.Color.red())
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
    
async def check_server_for_infinibot_mod_role(guild: nextcord.Guild):
    """|coro|
    
    Check to see if InfiniBot Mod role exists. If not, create it.

    ------
    Parameters
    ------
    guild: `nextcord.Guild`
        The guild in which to check.
        
    Returns
    ------
    `bool`
        True if the role was created. False if it already existed, or the process failed.
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

async def timeout(member: nextcord.Member, seconds: int, reason: str = None):
    """|coro|
    
    Handles the timing out of a member.

    ------
    Parameters
    ------
    member: `nextcord.Member`
        The member to time out.
    seconds: `int`
        The timeout time in seconds.
        
    Optional Parameters
    ------
    reason: optional [`str`]
        The reason that appears in the audit log. Defaults to None.

    Returns
    ------
    optional [`True` | `False`]
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