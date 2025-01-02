import logging

from nextcord.member import Member as NextcordMember

from core.db_manager import get_database, Simple_TableManager

class Member_Simple_TableManager(Simple_TableManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.member_id = self.primary_id

class Member(Member_Simple_TableManager):
    """
    Represents a member in the database.

    :param member_id: The ID of the member to represent
    :type member_id: int or nextcord.Member

    :return: The Member object
    :rtype: Member
    """
    def __init__(self, member_id:int):    
        super().__init__(self._format_member_id(member_id), "member_profile")

    def __str__(self):
        return str(self.member_id)

    def _format_member_id(self, member_id):
        if isinstance(member_id, NextcordMember):
            logging.warning(f"Member ID {member_id} is an instance of nextcord.Member. Implicitly converting to member_id. This is not recommended.")
            member_id = member_id.id
        else:
            if not isinstance(member_id, int):
                try:
                    logging.warning(f"Member ID {member_id} is not an integer. Implicitly converting to integer. This is not recommended.")
                    member_id = int(member_id)
                except ValueError:
                    raise ValueError(f"Member ID {member_id} is not an integer.")
                
        return member_id

    def remove_all_data(self):
        '''Removes all data relating to this member from the member_profile table.'''
        database = get_database()
        database.force_remove_entry(self.table_name, self.member_id)

    @Simple_TableManager.boolean_property("level_up_card_enabled")
    def level_up_card_enabled(self): pass

    @Simple_TableManager.boolean_property("join_card_enabled")
    def join_card_enabled(self): pass

    @Simple_TableManager.embed_property("level_up_card_embed")
    def level_up_card_embed(self): pass

    @Simple_TableManager.embed_property("join_card_embed")
    def join_card_embed(self): pass

    @Simple_TableManager.boolean_property("direct_messages_enabled")
    def direct_messages_enabled(self): pass
