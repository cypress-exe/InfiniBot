import asyncio
import datetime
import logging
import datetime
from typing import Any

import nextcord
from nextcord import Interaction

from components.ui_components import ErrorWhyAdminPrivilegesButton
from config.global_settings import feature_dependencies, required_permissions, get_global_kill_status, get_bot_load_status
from modules.custom_types import ExpiringSet

COLOR_OPTIONS = ["Red", "Green", "Blue", "Yellow", "White", "Blurple", "Greyple", "Teal", "Purple", "Gold", "Magenta", "Fuchsia"]

def asci_to_emoji(letter, fallback_letter = "1"):
    letter = str(letter)
    letter = letter.lower()

    if letter == "a": return "🇦", "a"
    if letter == "b": return "🇧", "b"
    if letter == "c": return "🇨", "c"
    if letter == "d": return "🇩", "d"
    if letter == "e": return "🇪", "e"
    if letter == "f": return "🇫", "f"
    if letter == "g": return "🇬", "g"
    if letter == "h": return "🇭", "h"
    if letter == "i": return "🇮", "i"
    if letter == "j": return "🇯", "j"
    if letter == "k": return "🇰", "k"
    if letter == "l": return "🇱", "l"
    if letter == "m": return "🇲", "m"
    if letter == "n": return "🇳", "n"
    if letter == "o": return "🇴", "o"
    if letter == "p": return "🇵", "p"
    if letter == "q": return "🇶", "q"
    if letter == "r": return "🇷", "r"
    if letter == "s": return "🇸", "s"
    if letter == "t": return "🇹", "t"
    if letter == "u": return "🇺", "u"
    if letter == "v": return "🇻", "v"
    if letter == "w": return "🇼", "w"
    if letter == "x": return "🇽", "x"
    if letter == "y": return "🇾", "y"
    if letter == "z": return "🇿", "z"
    if letter == "1": return "1️⃣", "1"
    if letter == "2": return "2️⃣", "2"
    if letter == "3": return "3️⃣", "3"
    if letter == "4": return "4️⃣", "4"
    if letter == "5": return "5️⃣", "5"
    if letter == "6": return "6️⃣", "6"
    if letter == "7": return "7️⃣", "7"
    if letter == "8": return "8️⃣", "8"
    if letter == "9": return "9️⃣", "9"
    if letter == "0": return "0️⃣", "0"

    return asci_to_emoji(fallback_letter)

def get_next_open_letter(list):
    if not ("a" in list): return "a"
    if not ("b" in list): return "b"
    if not ("c" in list): return "c"
    if not ("d" in list): return "d"
    if not ("e" in list): return "e"
    if not ("f" in list): return "f"
    if not ("g" in list): return "g"
    if not ("h" in list): return "h"
    if not ("i" in list): return "i"
    if not ("j" in list): return "j"
    if not ("k" in list): return "k"
    if not ("l" in list): return "l"
    if not ("m" in list): return "m"
    if not ("n" in list): return "n"
    if not ("o" in list): return "o"
    if not ("p" in list): return "p"
    if not ("q" in list): return "q"
    if not ("r" in list): return "r"
    if not ("s" in list): return "s"
    if not ("t" in list): return "t"
    if not ("u" in list): return "u"
    if not ("v" in list): return "v"
    if not ("w" in list): return "w"
    if not ("x" in list): return "x"
    if not ("y" in list): return "y"
    if not ("z" in list): return "z"
    if not ("1" in list): return "1"
    if not ("2" in list): return "2"
    if not ("3" in list): return "3"
    if not ("4" in list): return "4"
    if not ("5" in list): return "5"
    if not ("6" in list): return "6"
    if not ("7" in list): return "7"
    if not ("8" in list): return "8"
    if not ("9" in list): return "9"
    if not ("0" in list): return "0"

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

def apply_generic_replacements(
    embed: nextcord.Embed, 
    member: nextcord.Member, 
    guild: nextcord.Guild, 
    custom_replacements: dict = {}, 
    skip_channel_replacement: bool = False,
    skip_placeholder_replacement: bool = False
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
    :param skip_placeholder_replacement: Whether to skip replacing placeholders.
    :type skip_placeholder_replacement: bool
    :return: The modified embed with replaced placeholders.
    :rtype: nextcord.Embed
    """
    if not skip_placeholder_replacement:
        replacements = custom_replacements

        if member:
            # Add member-related replacements
            replacements["@displayname"] = member.display_name
            replacements["@mention"] = member.mention
            replacements["@username"] = member.name
            replacements["@id"] = str(member.id)
            replacements["@joindate"] = member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown"
            replacements["@accountage"] = f"{(datetime.datetime.now(datetime.timezone.utc) - member.created_at).days} days" if member.created_at else "Unknown"
        
        if guild:
            # Add server-related replacements
            replacements["@serverid"] = str(guild.id)
            replacements["@server"] = guild.name
            replacements["@membercount"] = str(guild.member_count)
            replacements["@owner"] = guild.owner.display_name if guild.owner else "Unknown"
        
        # Add time and date replacements
        epoch = int(datetime.datetime.now().timestamp())

        replacements["@time"] = f"<t:{epoch}:t>"
        replacements["@dateshort"] = f"<t:{epoch}:d>"
        replacements["@datelong"] = f"<t:{epoch}:D>"
        replacements["@date"] = f"<t:{epoch}:D>"

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

def get_infinibot_top_role(guild: nextcord.Guild):
    """
    Returns InfiniBot's top role.

    :param guild: The guild to check for InfiniBot's role.
    :type guild: nextcord.Guild
    :return: If applicable, returns InfiniBot's top role. Otherwise, returns `None`.
    :rtype: Optional[nextcord.Role]
    """
    if guild and not guild.unavailable:
        return guild.me.top_role
    else:
        return None

def get_infinibot_missing_permissions(guild: nextcord.Guild) -> tuple[list[str], list[tuple[nextcord.abc.GuildChannel, list[str]]]]:
    """
    Returns a list of missing permissions for InfiniBot in the given guild.

    :param guild: The guild to check for missing permissions.
    :type guild: nextcord.Guild
    :return: A tuple containing: (1) A list of missing guild permissions, (2) A list of tuples (channel, list of missing_permissions_for_channel)
    :rtype: tuple[list[str], list[tuple[nextcord.abc.GuildChannel, list[str]]]]
    """
    global required_permissions # Imported from config.global_settings

    if guild.me.guild_permissions.administrator:
        return [], []
    
    # Convert required_permissions to a dictionary of permission names to their backend dependencies
    required_permissions_dict: dict[str, dict[str, list[str]]] = {}
    for category_name, permissions in required_permissions.items():
        this_category_dict = {}
        for permission_name, backend_permission_dependencies in permissions.items():
            for backend_permission in backend_permission_dependencies:
                # Check if the permission exists in nextcord.Permissions
                if hasattr(nextcord.Permissions, backend_permission):
                    if backend_permission not in this_category_dict:
                        this_category_dict[backend_permission] = []
                    this_category_dict[backend_permission].append(permission_name)
                else:
                    # In theory, this should never happen, because there is a test to make sure that all permissions in required_permissions are valid.
                    # But, just in case, we can log a warning.
                    logging.warning(f"Permission {backend_permission} not found in nextcord.Permissions. Skipping...")
        if len(this_category_dict) > 0:
            required_permissions_dict[category_name] = this_category_dict


    # Check backend-permissions for the guild and each channel to ensure that InfiniBot has them.
    # Check guild permissions
    missing_guild_permissions = []

    # Get all unique permissions across all categories
    all_permissions = {k:v for category in required_permissions_dict.values() for k,v in category.items()}
    
    for permission in all_permissions:
        if not getattr(guild.me.guild_permissions, permission, True): # Not all permissions are available in both the guild_permissions and channel_permissions objects, so default to True if the permission does not exist.
            # Find which category this permission belongs to and get its frontend names
            for category_permissions in required_permissions_dict.values():
                if permission in category_permissions:
                    frontend_permissions = category_permissions[permission]
                    for frontend_permission in frontend_permissions:
                        if frontend_permission not in missing_guild_permissions:
                            missing_guild_permissions.append(frontend_permission)
                    break
            logging.debug(f"Missing guild permission: {permission}")
    
    # Check channel permissions
    # We will check all channels, and if the channel is a category, we will skip it.
    missing_channel_permissions = []
    for channel in guild.channels:
        if isinstance(channel, nextcord.CategoryChannel):
            continue
        
        this_channels_missing_perms = []

        if channel.type == nextcord.ChannelType.voice:
            # For voice channels, check both Voice Channel and Text Channel permissions
            voice_perms = required_permissions_dict.get("Voice Channel Permissions", {})
            text_perms = required_permissions_dict.get("Text Channel Permissions", {})
            # Merge the two dictionaries
            this_channels_required_permissions_dict = {**text_perms, **voice_perms}
        else:
            # For text channels, just check Text Channel permissions
            this_channels_required_permissions_dict = required_permissions_dict.get("Text Channel Permissions", {})

        # Check if the channel has the permission
        for permission in this_channels_required_permissions_dict:
            if not getattr(channel.permissions_for(guild.me), permission, True): # Reasoning for defaulting to True is the same as above.
                # If the permission is not granted, add it (the front-end name) to the missing permissions list for this channel if not already present
                frontend_permissions = this_channels_required_permissions_dict[permission]
                for frontend_permission in frontend_permissions:
                    if frontend_permission not in this_channels_missing_perms:
                        this_channels_missing_perms.append(frontend_permission)
                logging.debug(f"Missing channel permission: {permission} in channel #{channel.name}")

        if len(this_channels_missing_perms) > 0:
            # If there are any missing permissions for this channel, add it to the list of missing channel permissions
            missing_channel_permissions.append((channel, this_channels_missing_perms))
            
    return missing_guild_permissions, missing_channel_permissions

async def get_channel(guild: nextcord.Guild) -> nextcord.TextChannel | None:
    """
    |coro|  
    Get a text channel that InfiniBot can send messages and embeds in.
    
    Args:
        guild: The guild in which to check for a suitable channel
    
    Returns:
        A text channel if found, otherwise None
    """
    
    if not guild or guild.unavailable:
        logging.warning(f"Guild {guild} is unavailable or None. Cannot get a channel.")
        return None
    
    # Try system channel first
    if guild.system_channel:
        if await check_text_channel_permissions(guild.system_channel, False):
            return guild.system_channel
    
    # Try common channel names in order of preference
    preferred_channel_names = ['general', 'welcome', 'greetings']
    
    for channel_name in preferred_channel_names:
        channel = nextcord.utils.find(
            lambda x: x.name == channel_name, 
            guild.text_channels
        )
        if channel and await check_text_channel_permissions(channel, False):
            return channel
    
    # Try any available text channel
    for channel in guild.text_channels:
        if await check_text_channel_permissions(channel, False):
            return channel
    
    # No suitable channel found, notify server owner
    await send_error_message_to_server_owner(guild, "Send Messages")
    return None

failed_member_fetches = ExpiringSet(60 * 1)  # 1 minute expiration
async def get_member(guild: nextcord.Guild, user_id: int, override_failed_cache: bool = False) -> nextcord.Member | None:
    """
    |coro|  
    Get a member from a guild by their user ID.

    :param guild: The guild to search for the member.
    :type guild: nextcord.Guild
    :param user_id: The ID of the user to find.
    :type user_id: int
    :param override_failed_cache: If True, will override the failed member fetch cache and attempt to fetch the member again.
    :type override_failed_cache: bool
    :return: The member if found, otherwise None.
    :rtype: nextcord.Member | None
    """
    global failed_member_fetches
    
    if not guild or guild.unavailable:
        logging.warning(f"Guild {guild} is unavailable or None. Cannot get member.")
        return None
    
    if member := guild.get_member(user_id):
        return member

    if (not override_failed_cache) and ((guild.id, user_id) in failed_member_fetches):
        logging.info(f"Member with ID {user_id} was not found in guild {guild.name} recently. Skipping fetch.")
        return None

    try:
        return await guild.fetch_member(user_id)
    except nextcord.NotFound:
        logging.debug(f"Member with ID {user_id} was not found in guild {guild.name}.")
        if not (guild.id, user_id) in failed_member_fetches:
            logging.info(f"Adding failed member fetch for guild {guild.id} and user {user_id}.")
            failed_member_fetches.add((guild.id, user_id))
        return None

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
    
    infinibot_mod_role = await get_infinibot_mod_role(interaction.guild)
    if infinibot_mod_role in interaction.user.roles:
        return True

    if notify: await interaction.response.send_message(embed = nextcord.Embed(title = "Missing Permissions", description = "You need to have the Infinibot Mod role to use this command.\n\nGo to our [docs](https://cypress-exe.github.io/InfiniBot/docs/getting-started/install-and-setup/#the-infinibot-mod-role) for more information.", color = nextcord.Color.red()), ephemeral = True)
    return False

async def check_text_channel_permissions(channel: nextcord.TextChannel, auto_warn: bool, custom_channel_name: str = None) -> bool:
    """
    |coro|  
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
        # Commenting this out for now, because it's been sending a lot of false positives. Maybe uncomment later?
        # await send_error_message_to_server_owner(channel.guild, "View Channels", channel = channel_name, administrator = False)
        pass

    return False

messages_sent = ExpiringSet(60 * 5)  # 5 minutes expiration
async def send_error_message_to_server_owner(
    guild: nextcord.Guild, 
    permission: str, 
    message: str = None, 
    administrator: bool = True, 
    channel: str = None, 
    guild_permission: bool = False
) -> None:
    """
    |coro|  
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

    # Wait a second to let things settle out
    await asyncio.sleep(1)

    # Skip if the bot is not fully loaded
    if not get_bot_load_status():
        logging.warning("Bot is not ready. Skipping send_error_message_to_server_owner.")
        return
    
    if not guild:
        logging.error("No guild found for send_error_message_to_server_owner. Exiting... DID NOT WARN OWNER!!!")
        return
    
    if (guild.id, permission, message, administrator, channel, guild_permission) in messages_sent:
        logging.info(f"Skipping sending error message to server owner (guild_id: {guild.id}) because it was already sent recently. ({guild}, {permission}, {message}, {administrator}, {channel}, {guild_permission})")
        return
    
    member = guild.owner
    if member == None: return

    logging.info(f"Sending error message to server owner (guild_id: {guild.id}). ({guild}, {permission}, {message}, {administrator}, {channel}, {guild_permission})")
    
    # Make sure the member has DMs enabled in their profile settings for InfiniBot
    from config.member import Member # Avoids cyclic import
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
            embed = nextcord.Embed(title = f"Missing Permissions in \"{guild.name}\" Server", description = f"InfiniBot is missing the **{permission}** permission{in_channels}.{"\n\nWe advise that you grant InfiniBot administrator privileges so that this is no longer a concern." if administrator else ""}", color = nextcord.Color.red())
        else:
            embed = nextcord.Embed(title = f"Missing Permissions in \"{guild.name}\" Server", description = f"InfiniBot is missing a permission{in_channels}.{"\n\nWe advise that you grant InfiniBot administrator privileges so that this is no longer a concern." if administrator else ""}", color = nextcord.Color.red())
    else:
        embed = nextcord.Embed(title = f"Missing Permissions in \"{guild.name}\" Server", description = f"{message}", color = nextcord.Color.red())

    embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
    embed.timestamp = datetime.datetime.now()

    try:
        dm = await member.create_dm()
        if administrator:
            await dm.send(embed = embed, view = ErrorWhyAdminPrivilegesButton())
        else:
            await dm.send(embed = embed)
    except:
        pass
    
    # Add to the set of sent messages
    messages_sent.add((guild.id, permission, message, administrator, channel, guild_permission))

async def get_infinibot_mod_role(guild: nextcord.Guild, _iteration=0) -> nextcord.Role | None:
    """
    |coro|

    Gets the InfiniBot Mod role from the server. If it does not exist, it will create it.

    :param guild: The guild to get the InfiniBot Mod role from.
    :type guild: nextcord.Guild
    :return: The InfiniBot Mod role, or None if it does not exist and could not be created.
    :rtype: nextcord.Role | None
    """
    
    if not guild:
        logging.warning("No guild found for get_infinibot_mod_role")
        return None
    
    role = nextcord.utils.get(guild.roles, name='Infinibot Mod')

    if role is None and _iteration == 0:
        await check_server_for_infinibot_mod_role(guild)
        return await get_infinibot_mod_role(guild, _iteration + 1)

    return role

async def check_server_for_infinibot_mod_role(guild: nextcord.Guild) -> bool:
    """
    |coro|  
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