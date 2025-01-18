import nextcord
import logging

from components.utils import send_error_message_to_server_owner
from config.server import Server

async def add_roles_for_new_member(member: nextcord.Member):
    """
    |coro|

    Adds default roles to a new member when they join the guild.

    :param member: The member to add roles to.
    :type member: nextcord.Member
    :return: None
    :rtype: None
    """
    server = Server(member.guild.id)
    roles_to_add = []

    # Loop through default role IDs to find corresponding roles in the guild
    for role_id in server.default_roles.default_roles:
        role = member.guild.get_role(role_id)
        if role is not None:
            roles_to_add.append(role)
        else:
            logging.warning(
                f"Role {role_id} was not found in the guild {member.guild.name} ({member.guild.id}) when adding default roles. Skipping..."
            )

    try:
        # Attempt to add roles to the member
        await member.add_roles(*roles_to_add)
    except nextcord.errors.Forbidden:
        logging.warning(
            f"Cannot add roles to member {member.id} in guild {member.guild.name} ({member.guild.id}). Warning owner..."
        )
        send_error_message_to_server_owner(
            member.guild,
            "Manage Roles",
            message=(
                "InfiniBot can't add 1 or more default roles to a new member who joined your server. "
                "Please check that InfiniBot has permissions to manage roles, and has a higher role than the "
                "role it is trying to grant."
            ),
            administrator=False,
        )
