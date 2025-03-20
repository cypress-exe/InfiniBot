import logging

from nextcord import Guild as NextcordGuild

from core.db_manager import get_database, Simple_TableManager, IntegratedList_TableManager

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
        self._autobans = None
        
        self._embeds = None
        self._reaction_roles = None
        self._role_messages = None

    def __str__(self):
        return str(self.server_id)

    def _format_server_id(self, server_id):
        if isinstance(server_id, NextcordGuild):
            logging.warning(f"Server ID {server_id} is an instance of nextcord.Guild. Implicitly converting to guild_id. This is not recommended.")
            server_id = server_id.id
        else:
            if not isinstance(server_id, int):
                try:
                    logging.warning(f"Server ID {server_id} is not an integer. Implicitly converting to integer. This is not recommended.")
                    server_id = int(server_id)
                except ValueError:
                    raise ValueError(f"Server ID {server_id} is not an integer.")
                
        return server_id

    def remove_all_data(self):
        '''Removes all data relating to this server from the database.'''
        database = get_database()
        for table in database.tables:
            database.force_remove_entry(table, self.server_id)

    # PROFILES
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

        @Server_Simple_TableManager.list_property("filtered_words", accept_duplicate_values=False)
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

        @Server_Simple_TableManager.float_property("utc_offset", accept_none_value=False, allow_negative_values=True)
        def utc_offset(self): pass

    @property
    def infinibot_settings_profile(self):
        if self._infinibot_settings_profile is None: self._infinibot_settings_profile = self.InfinibotSettingsProfile(self.server_id)
        return self._infinibot_settings_profile
    class InfinibotSettingsProfile(Server_Simple_TableManager):
        def __init__(self, server_id):
            super().__init__(server_id, "infinibot_settings_profile")

        @Server_Simple_TableManager.boolean_property("delete_invites")
        def delete_invites(self): pass

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
    def autobans(self):
        if self._autobans is None: self._autobans = self.AutoBans(self.server_id)
        return self._autobans
    class AutoBans(Server_IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("auto_bans", "server_id", server_id, "member_id")

    # MESSAGE LOGS
    @property
    def embeds(self):
        if self._embeds is None: self._embeds = self.Embeds(self.server_id)
        return self._embeds
    class Embeds(Server_IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("embeds", "server_id", server_id, "message_id")

    @property
    def reaction_roles(self):
        if self._reaction_roles is None: self._reaction_roles = self.ReactionRoles(self.server_id)
        return self._reaction_roles
    class ReactionRoles(Server_IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("reaction_roles", "server_id", server_id, "message_id")

    @property
    def role_messages(self):
        if self._role_messages is None: self._role_messages = self.RoleMessages(self.server_id)
        return self._role_messages
    class RoleMessages(Server_IntegratedList_TableManager):
        def __init__(self, server_id):
            super().__init__("role_messages", "server_id", server_id, "message_id")
