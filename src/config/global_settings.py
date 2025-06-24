import nextcord
import logging

from config.file_manager import JSONFile

shards_loaded = []
bot_loaded = False
bot_id = None

channels_purging = []

# Feature dependencies are used to determine if a feature should be enabled or disabled.
# The bot will check if the dependency is enabled or disabled, and if it is disabled, the
# feature will be disabled as well.
feature_dependencies = {
    "dashboard": {"global_kill": "dashboard"},
    "profile": {"global_kill": "profile"},
    "options_menu": {"global_kill": "options_menu"},
    "options_menu__banning": {"global_kill": "options_menu__banning"},
    "options_menu__editing": {"global_kill": "options_menu__editing"},
    # ------------------------------------------------------------------------------------------------------
    "moderation__profanity": {
        "global_kill": "moderation__profanity",
        "server": "profanity_moderation_profile.active",
    },
    "moderation__spam": {
        "global_kill": "moderation__spam",
        "server": "spam_moderation_profile.active",
    },
    "delete_invite_links": {
        "global_kill": "delete_invite_links",
        "global_kill": "moderation__spam",
        "server": "spam_moderation_profile.delete_invites",
    },
    # ------------------------------------------------------------------------------------------------------
    "logging": {"global_kill": "logging", "server": "logging_profile.active"},
    # ------------------------------------------------------------------------------------------------------
    "leveling": {"global_kill": "leveling", "server": "leveling_profile.active"},
    "level_rewards": {
        "global_kill": ("level_rewards", "leveling"),
        "server": "leveling_profile.active",
    },
    # ------------------------------------------------------------------------------------------------------
    "join_leave_messages": {"global_kill": "join_leave_messages"},
    "join_messages": {
        "global_kill": "join_leave_messages",
        "server": "join_message_profile.active",
    },
    "leave_messages": {
        "global_kill": "join_leave_messages",
        "server": "leave_message_profile.active",
    },
    # ------------------------------------------------------------------------------------------------------
    "birthdays": {"global_kill": "birthdays"},
    # ------------------------------------------------------------------------------------------------------
    "default_roles": {"global_kill": "default_roles"},
    # ------------------------------------------------------------------------------------------------------
    "join_to_create_vcs" : {"global_kill": "join_to_create_vcs"},
    # ------------------------------------------------------------------------------------------------------
    "autobans": {"global_kill": "autobans"},
    # ------------------------------------------------------------------------------------------------------
    "reaction_roles": {"global_kill": "reaction_roles"},
    # ------------------------------------------------------------------------------------------------------
    "embeds": {"global_kill": "embeds"},
    # ------------------------------------------------------------------------------------------------------
    "role_messages": {"global_kill": "role_messages"},
    # ------------------------------------------------------------------------------------------------------
    "purging": {"global_kill": "purging"},
    # ------------------------------------------------------------------------------------------------------
    "motivational_statements": {"global_kill": "motivational_statements"},
    # ------------------------------------------------------------------------------------------------------
    "jokes": {"global_kill": "jokes"},
    # ------------------------------------------------------------------------------------------------------
    "joke_submissions": {"global_kill": "joke_submissions"},
    # ------------------------------------------------------------------------------------------------------
    "onboarding": {"global_kill": "onboarding"},
    
}

# WHEN UPDATING, REMEMBER TO:
# 1. Update github-pages-site/docs/getting-started/install-and-setup.md#Required Permissions
# 2. Update join link to reflect new permissions:
#    - Replace link in generated/configure/config.json["links"]["bot-invite-link"]
#    - Replace link in discord developer portal
#    - Replace link on promotion sites (top.gg, etc...) 
required_permissions = {
    "General Server Permissions": {
        "View Channels": ["view_channel", "read_messages"],
        "Manage Channels": ["manage_channels"],
        "Manage Roles": ["manage_roles"],
        "View Audit Log": ["view_audit_log"],
        "Manage Server": ["manage_guild"],
    },
    "Membership Permissions": {
        "Manage Nicknames": ["manage_nicknames"],
        "Kick, Approve, and Reject Members": ["kick_members"],
        "Ban Members": ["ban_members"],
        "Timeout Members": ["moderate_members"],
    },
    "Text Channel Permissions": { # Don't change the names of this category. It's referred to by name in the code.
        "Send Messages": ["send_messages"],
        "Send Messages in Threads": ["send_messages_in_threads"],
        "Embed Links": ["embed_links"],
        "Attach Files": ["attach_files"],
        "Add Reactions": ["add_reactions"],
        "Mention @everyone, @here, and All Roles": ["mention_everyone"],
        "Manage Messages": ["manage_messages"],
        "Read Message History": ["read_message_history", "read_messages"],
    },
    "Voice Channel Permissions": { # Don't change the names of this category. It's referred to by name in the code.
        "Connect": ["connect"],
        "Move Members": ["move_members"],
    }
}


class GlobalSetting:
    '''This parent class is used to store global settings. It is used to store global settings in the JSON file.'''
    def __init__(self, file_name, variable_list:dict):
        self.file_name = file_name
        file = JSONFile(self.file_name)

        self.variable_list = variable_list

        for variable, value in self.variable_list.items():
            if variable not in file:
                file.add_variable(variable, value)
                logging.debug(f"Added {variable} to {self.file_name} with value: {value}")

    def __getitem__(self, name):
        return self.get_variable(name)
    
    def __setitem__(self, name, value):
        self.set_variable(name, value)

    def get_variable(self, name):
        """
        Gets a variable from the global setting.

        :param name: The name of the variable to get.
        :type name: str
        :return: The value of the variable.
        :rtype: Any
        """
        file = JSONFile(self.file_name)

        if name not in file:
            raise AttributeError(f"{self.__class__.__name__} object has no item {name}")
        
        return file[name]

    def set_variable(self, name, value):
        """
        Sets a variable in the global setting.

        :param name: The name of the variable to set.
        :type name: str
        :param value: The value to set the variable to.
        :type value: Any
        """
        file = JSONFile(self.file_name)

        if name not in file:
            raise AttributeError(f"{self.__class__.__name__} object has no item {name}")

        logging.info(f"Updating global setting. Name: {name}, Value: {value}")
        file[name] = value

    def __contains__(self, name):
        file = JSONFile(self.file_name)
        return name in file
    
    def reset(self):
        """
        Resets the global setting to its default value. Be careful with this method.
        """
        file = JSONFile(self.file_name)
        file.delete_file()

class GlobalKillStatus(GlobalSetting):
    '''This class is used to store global kill settings. It is used to store global kill settings in the JSON file. '''
    def __init__(self):
        variable_list = {
            "moderation__profanity": False,
            "moderation__spam": False,
            "logging": False,
            "leveling": False,
            "level_rewards": False,
            "join_leave_messages": False,
            "birthdays": False,
            "default_roles": False,
            "join_to_create_vcs": False,
            "autobans": False,
            "reaction_roles": False,
            "embeds": False,
            "role_messages": False,
            "purging": False,
            "motivational_statements": False,
            "jokes": False,
            "joke_submissions": False,
            "dashboard": False,
            "profile": False,
            "delete_invite_links": False,
            "options_menu": False,
            "options_menu__banning": False,
            "options_menu__editing": False,
            "onboarding": False,
        }


        super().__init__("global_kill_status", variable_list)

    def reset(self):
        logging.warning("Clearing global_kill_status.json")
        super().reset()

class Configs(GlobalSetting):
    '''This class is used to store and access special channel ids for InfiniBot. Stored in config.json. '''
    def __init__(self):
        variable_list = {
            "logging": {
                "log-level": "INFO",
                "max-logs-to-keep": 10
            },
            "admin-ids": {
                'level-1-admins': [],
                'level-2-admins': [],
                'level-3-admins': []
            },
            "notify-on-startup":{
                "enabled": False,
                "channel-id": 0,
            },
            "support-server": {
                "support-server-id": 0,
                "submission-channel-id": 0,
                "updates-channel-id": 0,
                "infinibot-updates-role-id": 0
            },
            "links": {
                "support-server-invite-link": "https://example.com",
                "topgg-link": "https://example.com",
                "topgg-vote-link": "https://example.com",
                "topgg-review-link": "https://example.com",
                "bot-invite-link": "https://example.com",
                "support-email": "unset_email@example.com"
            },
            "spam-moderation": {
                "max-messages-to-check": 11,
                "message-chars-to-check-repetition": 140
            },
            "discord-message-logging": {
                "max-days-to-keep": 7,
                "max-messages-to-keep-per-guild": 1000
            },
            "scheduler": {
                "misfire-grace-time-seconds": 30
            }
        }

        super().__init__("config", variable_list)


def get_global_kill_status() -> GlobalKillStatus:
    """
    Retrieve the global kill status.

    :return: An instance representing the global kill status.
    :rtype: GlobalKillStatus
    """

    return GlobalKillStatus()

def get_configs() -> Configs:
    """
    Retrieve the config.

    :return: An instance representing the config.
    :rtype: Configs
    """
    return Configs()


def get_bot_load_status() -> bool:
    """
    Retrieve the bot load status.

    :return: Whether the bot is loaded.
    :rtype: bool
    """
    return bot_loaded

def set_bot_load_status(status: bool) -> None:
    """
    Set the bot load status.

    :param status: Whether the bot is loaded.
    :type status: bool
    :return: None
    :rtype: None
    """
    global bot_loaded
    bot_loaded = status

class ShardLoadedStatus: # Context manager
    """
    Context manager for managing a list of loaded shards.
    """
    def __init__(self):
        global shards_loaded
        self.shards_loaded: list = shards_loaded

    def __enter__(self) -> list:
        return self.shards_loaded

    def __exit__(self, exc_type, exc_value, exc_traceback):
        global shards_loaded
        shards_loaded = self.shards_loaded


def get_bot_id() -> int | None:
    """
    Retrieve the bot id.

    :return: The bot id.
    :rtype: int | None
    """
    return bot_id

def update_bot_id(bot: nextcord.Client):
    """
    Update the bot id.

    :param bot: The bot instance.
    :type bot: nextcord.Client
    :return: None
    :rtype: None
    """
    global bot_id
    bot_id = bot.application_id


def is_channel_purging(channel_id: int) -> bool:
    """
    Check if a channel is being purged.

    :param channel_id: The id of the channel to check.
    :type channel_id: int
    :return: Whether the channel is being purged.
    :rtype: bool
    """
    global channels_purging
    return channel_id in channels_purging

def add_channel_to_purging(channel_id: int):
    """
    Add a channel to the list of channels that are being purged.

    :param channel_id: The id of the channel to add.
    :type channel_id: int
    :return: None
    :rtype: None
    """
    global channels_purging
    channels_purging.append(channel_id)

def remove_channel_from_purging(channel_id: int):
    """
    Remove a channel from the list of channels that are being purged if it exists.

    :param channel_id: The id of the channel to remove.
    :type channel_id: int
    :return: None
    :rtype: None
    """
    global channels_purging
    if channel_id in channels_purging:
        channels_purging.remove(channel_id)

def reset_purging():
    """
    Reset the list of channels that are being purged.

    :return: None
    :rtype: None
    """
    global channels_purging
    channels_purging = []