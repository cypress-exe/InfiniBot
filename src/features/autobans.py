import asyncio
import nextcord
import logging

from components.utils import send_error_message_to_server_owner
from config.server import Server

async def check_and_run_autoban_for_member(member: nextcord.Member) -> bool:
    """
    Checks if a member should be autobanned and runs the autoban if necessary.

    Args:
        member (nextcord.Member): The member to check for autoban.
    Returns:
        bool: True if the member was autobanned, False otherwise.
    """
    
    if member_has_autoban(member):
        # The member is autobanned. Ban them.
        
        # However, wait a moment to ensure that things settle out
        await asyncio.sleep(1)

        # Now proceed with the autoban
        try:
            await member.ban(reason="Autoban triggered")
            logging.info(f"Autobanned member {member.id} ({member.name}) in guild {member.guild.id}")
        except nextcord.Forbidden:
            logging.error(f"Failed to autoban member {member.id} ({member.name}) in guild {member.guild.id}: Forbidden")
            await send_error_message_to_server_owner(member.guild, "Ban Members", guild_permission=True)
        except Exception as e:
            logging.error(f"Failed to autoban member {member.id} ({member.name}) in guild {member.guild.id}: {e}")

        await asyncio.sleep(5)  # Ensure the ban is processed before removing autoban entry
        
        # Remove autoban entry after banning
        server = Server(member.guild.id)
        server.autobans.delete(member.id)

        return True

    return False

def member_has_autoban(member: nextcord.Member) -> bool:
    """
    Checks if a member has an autoban entry.

    Args:
        member (nextcord.Member): The member to check.
    Returns:
        bool: True if the member has an autoban entry, False otherwise.
    """
    server = Server(member.guild.id)
    return len(server.autobans.get_matching(member_id=member.id)) > 0