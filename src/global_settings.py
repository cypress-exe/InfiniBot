from file_manager import JSONFile
import logging

class GlobalSetting:
    '''This parent class is used to store global settings. It is used to store global settings in the JSON file.'''
    def __init__(self, file_name, variable_list, default_value):
        self.file_name = file_name
        file = JSONFile(self.file_name)

        for variable in variable_list:
            if variable not in file:
                file.add_variable(variable, default_value)
                logging.debug(f"Added {variable} to {self.file_name} with value: {default_value}")

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
        variable_list = [
            "profanity_moderation",
            "spam_moderation",
            "logging",
            "leveling",
            "level_rewards",
            "join_leave_messages",
            "birthdays",
            "default_roles",
            "join_to_create_vcs",
            "auto_bans",
            # "active_messages", Removed for now since I think it's being phased out in this update
            "reaction_roles",
            "embeds",
            "role_messages",
            "purging",
            "motivational_statements",
            "jokes",
            "joke_submissions",
            "dashboard",
            "profile"
        ]

        super().__init__("global_kill_status", variable_list, False)

class PeristentData(GlobalSetting):
    '''This class is used to store persistent data. It is used to store persistent data in the JSON file. '''
    def __init__(self):
        variable_list = [
            "login_response_guildID",
            "login_response_channelID"
        ]

        super().__init__("persistent_data", variable_list, None)
        
def get_global_kill_status():
    return GlobalKillStatus()

def get_persistent_data():
    return PeristentData()