from file_manager import JSONFile
import logging


shards_loaded = []
bot_loaded = False

feature_dependencies = {
    "dashboard": {"global_kill": "dashboard"},
    # ------------------------------------------------------------------------------------------------------
    "profanity_moderation": {
        "global_kill": "profanity_moderation",
        "server": "profanity_moderation_profile.active",
    },
    "spam_moderation": {
        "global_kill": "spam_moderation",
        "server": "spam_moderation_profile.active",
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
}


class GlobalSetting:
    '''This parent class is used to store global settings. It is used to store global settings in the JSON file.'''
    def __init__(self, file_name, variable_list:dict):
        self.file_name = file_name
        file = JSONFile(self.file_name)

        for variable, value in variable_list.items():
            if variable not in file:
                file.add_variable(variable, value)
                logging.debug(f"Added {variable} to {self.file_name} with value: {value}")

    def __getitem__(self, name):
        file = JSONFile(self.file_name)

        if name not in file:
            raise AttributeError(f"{self.__class__.__name__} object has no item {name}")
        
        return file[name]
    
    def __setitem__(self, name, value):
        file = JSONFile(self.file_name)

        if name not in file:
            raise AttributeError(f"{self.__class__.__name__} object has no item {name}")

        logging.debug(f"Updating global setting. Name: {name}, Value: {value}")
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
            "profanity_moderation": False,
            "spam_moderation": False,
            "logging": False,
            "leveling": False,
            "level_rewards": False,
            "join_leave_messages": False,
            "birthdays": False,
            "default_roles": False,
            "join_to_create_vcs": False,
            "auto_bans": False,
            # "active_messages": False, Removed for now since I think it's being phased out in this update
            "reaction_roles": False,
            "embeds": False,
            "role_messages": False,
            "purging": False,
            "motivational_statements": False,
            "jokes": False,
            "joke_submissions": False,
            "dashboard": False,
            "profile": False
        }


        super().__init__("global_kill_status", variable_list)

    def reset(self):
        logging.warning("Clearing global_kill_status.json")
        super().reset()

class PeristentData(GlobalSetting):
    '''This class is used to store persistent data. It is used to store persistent data in the JSON file. '''
    def __init__(self):
        variable_list = {
            "login_response_guildID": None,
            "login_response_channelID": None
        }

        super().__init__("persistent_data", variable_list)

class Settings(GlobalSetting):
    '''This class is used to store and access special channel ids for InfiniBot. Stored in special_channel_ids.json. '''
    def __init__(self):
        variable_list = {
            "dev_guilds": [],
            "dev_ids": [],
            "infinibot_guild_id": 0,
            "issue_report_channel_id": 0,
            "submission_channel_id": 0,
            "updates_channel_id": 0,
            "infinibot_updates_role_id": 0,
            "support_server_invite_link": "https://example.com",
            "topgg_link": "https://example.com",
            "topgg_vote_link": "https://example.com",
            "topgg_review_link": "https://example.com",
            "bot_invite_link": "https://example.com",
            "support_email": "unset_email@example.com"
        }

        super().__init__("settings", variable_list)

def get_global_kill_status():
    return GlobalKillStatus()

def get_persistent_data():
    return PeristentData()

def get_settings():
    return Settings()
