import logging

from nextcord import Guild as NextcordGuild

from config.file_manager import read_txt_to_list
from config.messages.cached_messages import remove_cached_messages_from_guild
from config.messages.stored_messages import remove_db_messages_from_guild
from core.db_manager import get_database, Simple_TableManager, IntegratedList_TableManager, TableManager

class Server_Simple_TableManager(Simple_TableManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server_id = self.primary_id

class Server_IntegratedList_TableManager(IntegratedList_TableManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server_id = self.primary_key_value

class Server:
    """
    Represents a server configuration.

    :param server_id: The ID of the server to manage.
    :type server_id: int
    :return: An instance of the Server object.
    :rtype: Server
    """
    def __init__(self, server_id:int):    
        self.server_id = self._format_server_id(server_id)

        self._moderation_profile = None
        self._profanity_moderation_profile = None
        self._spam_moderation_profile = None
        self._logging_profile = None
        self._leveling_profile = None
        self._join_message_profile = None
        self._leave_message_profile = None
        self._birthdays_profile = None
        self._infinibot_settings_profile = None
        
        self._join_to_create_vcs = None
        self._default_roles = None
        
        self._moderation_strikes = None
        self._member_levels = None
        self._level_rewards = None
        self._birthdays = None
        self._join_to_create_active_vcs = None
        self._autobans = None
        
        self._managed_messages = None
        self._reaction_roles = None
        self._role_messages = None

    def __str__(self):
        return str(self.server_id)

    def _format_server_id(self, server_id):
        if isinstance(server_id, bool) or server_id is None or server_id == "" or server_id == 0:
            logging.error("Server ID cannot be None, False, True, empty string, or zero.", exc_info=True)
            raise ValueError(f"Invalid server ID: `{server_id}`. Server ID must be a valid integer or nextcord.Guild instance.")
        if isinstance(server_id, NextcordGuild):
            logging.warning(f"Server ID `{server_id}` is an instance of nextcord.Guild. Implicitly converting to guild_id. This is not recommended.")
            return server_id.id
        else:
            if not isinstance(server_id, int):
                try:
                    logging.warning(f"Server ID `{server_id}` is not an integer. Implicitly converting to integer. This is not recommended.")
                    return int(server_id)
                except ValueError:
                    raise ValueError(f"Server ID `{server_id}` is not an integer.")
            return server_id

    def remove_all_data(self):
        '''Removes all data relating to this server from the database.'''
        database = get_database()

        # Attributes are lazy loaded, so this accesses them to trigger their loading so that
        # it is possible to programmatically check their tables. Else, there would have to
        # be a manual list of all the tables to check, which would need to be updated anytime
        # a new table is added.

        table_names = []
        for attr_name in dir(self):
            if attr_name.startswith('_') or attr_name.startswith('__'):
                continue
            try:
                attr = getattr(self, attr_name)
                if isinstance(attr, TableManager):
                    table_names.append(attr.table_name)
            except Exception as e:
                logging.error(f"Skipping attribute {attr_name} due to error: {e}")
                continue  # skip properties that throw on access

        for table_name in table_names:
            database.force_remove_entry(table_name, self.server_id)
            logging.debug(f"Removed all data from {table_name} for server {self.server_id}")

        # Remove messages
        remove_db_messages_from_guild(self.server_id)
        remove_cached_messages_from_guild(self.server_id)
        logging.debug(f"Removed all stored messages for server {self.server_id}")

    def get_debug_info(self):
        """
        Retrieves debug information about the server.

        :param self: The server instance
        :type self: Server
        :return: A dictionary containing debug information about the server
        :rtype: dict
        """
        debug_info = {"server_id": str(self.server_id)}
        for attr_name in dir(self):
            if attr_name.startswith('_') or attr_name.startswith('__'):
                continue
            try:
                attr = getattr(self, attr_name)
                if isinstance(attr, TableManager):
                    debug_info[attr_name] = attr.serialize()
            except Exception as e:
                logging.error(f"Skipping attribute {attr_name} due to error: {e}")
                continue
            
        return debug_info

    # PROFILES
    @property
    def moderation_profile(self):
        if self._moderation_profile is None: self._moderation_profile = self.Moderation_Profile(self.server_id)
        return self._moderation_profile
    class Moderation_Profile(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "moderation_profile")

        @Server_Simple_TableManager.list_property("admin_role_ids", accept_duplicate_values=False)
        def admin_role_ids(self): pass

    @property
    def profanity_moderation_profile(self):
        if self._profanity_moderation_profile is None: self._profanity_moderation_profile = self.Profanity_Moderation_Profile(self.server_id)
        return self._profanity_moderation_profile
    class Profanity_Moderation_Profile(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "profanity_moderation_profile")

        @Server_Simple_TableManager.boolean_property("active")
        def active(self): pass

        @Server_Simple_TableManager.typed_property("channel", enforce_numerical_values=True)
        def channel(self): pass

        @Server_Simple_TableManager.boolean_property("strike_system_active")
        def strike_system_active(self): pass

        @Server_Simple_TableManager.integer_property("max_strikes", accept_none_value=False)
        def max_strikes(self): pass

        @Server_Simple_TableManager.boolean_property("strike_expiring_active")
        def strike_expiring_active(self): pass

        @Server_Simple_TableManager.integer_property("strike_expire_days", accept_none_value=False)
        def strike_expire_days(self): pass

        @Server_Simple_TableManager.integer_property("timeout_seconds", accept_none_value=False)
        def timeout_seconds(self): pass

        def _get_filtered_words_with_defaults(words_list):
            """Get filtered words with default values when list is empty."""      
            # If the list is empty, return default words
            if not words_list:
                default_words = read_txt_to_list("default_profane_words.txt")
                return default_words if default_words else []
                
            return words_list         
        def _set_filtered_words_with_optimization(words_list):
            """Set filtered words with storage optimization."""
            # Storage optimization: if the input exactly matches default values, store []
            if words_list:  # Only optimize if list is not empty
                default_words = read_txt_to_list("default_profane_words.txt")
                if default_words and set(words_list) == set(default_words):
                    # Store empty list when contents match defaults exactly
                    return []
            
            return words_list
        @Server_Simple_TableManager.list_property("filtered_words", accept_duplicate_values=False, getter_super_modifier=_get_filtered_words_with_defaults, setter_super_modifier=_set_filtered_words_with_optimization)
        def filtered_words(self): pass

    @property
    def spam_moderation_profile(self):
        if self._spam_moderation_profile is None: self._spam_moderation_profile = self.Spam_Moderation_Profile(self.server_id)
        return self._spam_moderation_profile
    class Spam_Moderation_Profile(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "spam_moderation_profile")

        @Server_Simple_TableManager.boolean_property("active")
        def active(self): pass

        @Server_Simple_TableManager.integer_property("score_threshold",  accept_none_value=False)
        def score_threshold(self): pass

        @Server_Simple_TableManager.integer_property("time_threshold_seconds", accept_none_value=False)
        def time_threshold_seconds(self): pass

        @Server_Simple_TableManager.integer_property("timeout_seconds", accept_none_value=False)
        def timeout_seconds(self): pass

        @Server_Simple_TableManager.boolean_property("delete_invites")
        def delete_invites(self): pass

    @property
    def logging_profile(self):
        if self._logging_profile is None: self._logging_profile = self.Logging_Profile(self.server_id)
        return self._logging_profile
    class Logging_Profile(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "logging_profile")

        @Server_Simple_TableManager.boolean_property("active")
        def active(self): pass

        @Server_Simple_TableManager.typed_property("channel", accept_none_value=False, enforce_numerical_values=True)
        def channel(self): pass

    @property
    def leveling_profile(self):
        if self._leveling_profile is None: self._leveling_profile = self.Leveling_Profile(self.server_id)
        return self._leveling_profile
    class Leveling_Profile(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "leveling_profile")

        @Server_Simple_TableManager.boolean_property("active")
        def active(self): pass

        @Server_Simple_TableManager.typed_property("channel", enforce_numerical_values=True)
        def channel(self): pass

        @Server_Simple_TableManager.embed_property("level_up_embed")
        def level_up_embed(self): pass

        @Server_Simple_TableManager.integer_property("points_lost_per_day", accept_none_value=False)
        def points_lost_per_day(self): pass

        @Server_Simple_TableManager.integer_property("max_points_per_message", accept_none_value=True)
        def max_points_per_message(self): pass

        @Server_Simple_TableManager.list_property("exempt_channels", accept_duplicate_values=False)
        def exempt_channels(self): pass

        @Server_Simple_TableManager.boolean_property("allow_leveling_cards")
        def allow_leveling_cards(self): pass

    @property
    def join_message_profile(self):
        if self._join_message_profile is None: self._join_message_profile = self.JoinMessageProfile(self.server_id)
        return self._join_message_profile
    class JoinMessageProfile(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "join_message_profile")

        @Server_Simple_TableManager.boolean_property("active")
        def active(self): pass

        @Server_Simple_TableManager.typed_property("channel", accept_none_value=False, enforce_numerical_values=True)
        def channel(self): pass

        @Server_Simple_TableManager.embed_property("embed")
        def embed(self): pass

        @Server_Simple_TableManager.boolean_property("allow_join_cards")
        def allow_join_cards(self): pass

    @property
    def leave_message_profile(self):
        if self._leave_message_profile is None: self._leave_message_profile = self.LeaveMessageProfile(self.server_id)
        return self._leave_message_profile
    class LeaveMessageProfile(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "leave_message_profile")

        @Server_Simple_TableManager.boolean_property("active")
        def active(self): pass

        @Server_Simple_TableManager.typed_property("channel", accept_none_value=False, enforce_numerical_values=True)
        def channel(self): pass

        @Server_Simple_TableManager.embed_property("embed")
        def embed(self): pass
        
    @property
    def birthdays_profile(self):
        if self._birthdays_profile is None: self._birthdays_profile = self.BirthdaysProfile(self.server_id)
        return self._birthdays_profile
    class BirthdaysProfile(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "birthdays_profile")

        @Server_Simple_TableManager.typed_property("channel", enforce_numerical_values=True)
        def channel(self): pass

        @Server_Simple_TableManager.embed_property("embed")
        def embed(self): pass
                
        @Server_Simple_TableManager.typed_property("runtime", accept_none_value=False)
        def runtime(self): pass

    @property
    def infinibot_settings_profile(self):
        if self._infinibot_settings_profile is None: self._infinibot_settings_profile = self.InfinibotSettingsProfile(self.server_id)
        return self._infinibot_settings_profile
    class InfinibotSettingsProfile(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "infinibot_settings_profile")

        @Server_Simple_TableManager.boolean_property("get_updates")
        def get_updates(self): pass

        @Server_Simple_TableManager.typed_property("timezone", accept_none_value=False, enforce_numerical_values=False)
        def timezone(self): pass


    # SIMPLE LISTS
    @property
    def join_to_create_vcs(self):
        if self._join_to_create_vcs is None: self._join_to_create_vcs = self.JoinToCreateVCs(self.server_id)
        return self._join_to_create_vcs
    class JoinToCreateVCs(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "join_to_create_vcs")
        
        @Server_Simple_TableManager.list_property("channels", accept_duplicate_values=False)
        def channels(self): pass

    @property
    def default_roles(self):
        if self._default_roles is None: self._default_roles = self.DefaultRoles(self.server_id)
        return self._default_roles
    class DefaultRoles(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "default_roles")

        @Server_Simple_TableManager.list_property("default_roles", accept_duplicate_values=False)
        def default_roles(self): pass


    # INTEGRATED LISTS
    @property
    def moderation_strikes(self):
        if self._moderation_strikes is None: self._moderation_strikes = self.ModerationStrikes(self.server_id)
        return self._moderation_strikes
    class ModerationStrikes(Server_IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("moderation_strikes", "server_id", server_id, "member_id")
    
    @property
    def member_levels(self):
        if self._member_levels is None: self._member_levels = self.MemberLevels(self.server_id)
        return self._member_levels
    class MemberLevels(Server_IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("member_levels", "server_id", server_id, "member_id")
    
    @property
    def level_rewards(self):
        if self._level_rewards is None: self._level_rewards = self.LevelRewards(self.server_id)
        return self._level_rewards
    class LevelRewards(Server_IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("level_rewards", "server_id", server_id, "role_id")

    @property
    def birthdays(self):
        if self._birthdays is None: self._birthdays = self.Birthdays(self.server_id)
        return self._birthdays
    class Birthdays(Server_IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("birthdays", "server_id", server_id, "member_id")

    @property
    def join_to_create_active_vcs(self):
        if self._join_to_create_active_vcs is None: self._join_to_create_active_vcs = self.JoinToCreateActiveVCs(self.server_id)
        return self._join_to_create_active_vcs
    class JoinToCreateActiveVCs(Server_IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("join_to_create_active_vcs", "server_id", server_id, "channel_id")

    @property
    def autobans(self):
        if self._autobans is None: self._autobans = self.AutoBans(self.server_id)
        return self._autobans
    class AutoBans(Server_IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("autobans", "server_id", server_id, "member_id")

    # MANAGED MESSAGES
    @property
    def managed_messages(self):
        if self._managed_messages is None: self._managed_messages = self.ManagedMessages(self.server_id)
        return self._managed_messages
    class ManagedMessages(Server_IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("managed_messages", "server_id", server_id, "message_id")