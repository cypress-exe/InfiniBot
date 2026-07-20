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
        bool: True if the member matched an autoban entry (whether or not the ban
            call itself succeeded), meaning normal join processing should be
            suppressed. False if the member is not an autoban target.
    """
    
    if member_has_autoban(member.guild.id, member.id):
        # The member is autobanned. Ban them.
        
        # However, wait a moment to ensure that things settle out
        await asyncio.sleep(1)

        # Now proceed with the autoban
        banned = False
        missing_permission = False
        try:
            await member.ban(reason="Autoban triggered")
            banned = True
            logging.info(f"Autobanned member {member.id} ({member.name}) in guild {member.guild.id}")
        except nextcord.Forbidden:
            logging.error(f"Failed to autoban member {member.id} ({member.name}) in guild {member.guild.id}: Forbidden")
            missing_permission = True
        except Exception as e:
            logging.error(f"Failed to autoban member {member.id} ({member.name}) in guild {member.guild.id}: {e}")

        if not banned:
            # Keep the entry so the autoban retries once the permission is granted.
            # The member is still an autoban target, so don't welcome or auto-role them.
            if missing_permission:
                reason = "since it's missing the \"Ban Members\" permission"
                remedy = " Additionally, ensure InfiniBot has the \"Ban Members\" permission so that it can enforce future autobans."
            else:
                reason = "due to an unexpected error"
                remedy = ""

            message = (
                f"Failed to autoban member {member.name} ({member.id}) in guild {member.guild.name}.\n\n"
                f"**What Happened:** InfiniBot detected that {member.name} just joined your server. InfiniBot failed to "
                f"execute their autoban {reason}. {member.name} *is* still in your server, but InfiniBot "
                f"intentionally did not grant them any roles or welcome them. Their autoban record remains in place, "
                f"but InfiniBot will not retry unless they leave and rejoin the server.\n\n"
                f"**Next Steps:** Consider manually banning the member, since InfiniBot was unable to.{remedy}"
            )
            await send_error_message_to_server_owner(member.guild, None, message=message)
            return True

        await asyncio.sleep(5)  # Ensure the ban is processed before removing autoban entry

        # Remove autoban entry after banning
        server = Server(member.guild.id)
        server.autobans.delete(member.id)

        return True

    return False

def member_has_autoban(guild_id: int, member_id: int) -> bool:
    """
    Checks if a member has an autoban entry.

    Args:
        guild_id (int): The ID of the guild to check.
        member_id (int): The ID of the member to check.
    Returns:
        bool: True if the member has an autoban entry, False otherwise.
    """
    server = Server(guild_id)
    return len(server.autobans.get_matching(member_id=member_id)) > 0