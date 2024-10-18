from nextcord import Interaction
import nextcord
import logging

from global_settings import get_global_kill_status, feature_dependencies


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
          if value.startswith("'") and value.endswith("'"):
              return format_var_to_pythonic_type(_type, value[1:-1])
          else:
              return value
  return value

def standardize_dict_properties(defaultDict: dict, objectDict: dict, aliases: dict = {}):
    """A recursive function that makes sure that two dictionaries have the same properties.

    ------
    Parameters
    ------
    defaultDict: `dict`
        A dictionary containing all the properties and their default values.
    objectDict: `dict`
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


    # cloning defaultDict as returnDict
    returnDict = dict(defaultDict)
    
    # checking for aliases and changing the dictionary to account for them
    objectDict = {aliases.get(k, k): v for k, v in objectDict.items()}
    
    # for each key:
    for key in returnDict.keys():
        # for each key in returnDict
           
        if key in objectDict.keys():
            # the key was in our objectdict. Now we just have to set it.
            # We have to check this recursively if this is a dictionary, and set this to be the returned value from the recursive function.
            
            if type(objectDict[key]) == dict:
                # this is a dictionary. 
                # Now, we have to run this recursively to make sure that all values inside the dictionary are updated
                returnDict[key] = standardize_dict_properties(returnDict[key], objectDict[key], aliases = aliases)
            else:
                # this is not a dictionary. It's just a regular value
                # putting this value into returnDict
                returnDict[key] = objectDict[key]
        else:
            # the key was not in the objectDict, but it was in the defaultDict.
            # but, because the key was already added (as the default), we don't need to worry at all.
            # lower dictionaries that may be attached to this are also not a concern, seeing how it never existed on the objectDict, so the defaults are fine.
            continue
        
    return returnDict
    
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

def get_string_from_discord_color(color: nextcord.colour.Colour):
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

def feature_is_active(**kwargs):
    from server import Server

    server = kwargs.get("server")
    server_id = kwargs.get("server_id")
    if kwargs.get("guild_id"): server_id = kwargs.get("guild_id")
    feature = kwargs.get("feature")

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
        if feature not in global_kill_statuses:
            raise ValueError(f"Error: {__name__} received an invalid feature (not registered in global kill settings).")

        if global_kill_statuses[key]:
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
            return False

    return True

async def user_has_config_permissions(interaction: Interaction, notify = True):
    """|coro|
    
    Determins if an interaction can be continued if it is protected by InfiniBot Mod.

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