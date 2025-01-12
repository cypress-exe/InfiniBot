import dateparser
import datetime
import logging
import nextcord

from components import utils
from config.global_settings import get_bot_load_status, get_global_kill_status
from config.member import Member
from config.server import Server
from modules.custom_types import UNSET_VALUE

def calculate_utc_offset(user_date_str: str, user_time_str: str) -> float:
    """
    Calculate the UTC offset based on the provided date and time strings.

    This function parses a wide variety of date and time formats using `dateparser`,
    calculates the difference between the provided datetime and the current UTC time,
    and snaps the offset to the nearest quarter-hour.

    :param user_date_str: The date string (e.g., "11/24/2024", "November 24, 2024").
    :type user_date_str: str
    :param user_time_str: The time string (e.g., "15:30", "3:30 PM").
    :type user_time_str: str
    :return: The snapped UTC offset in hours (rounded to the nearest 15 minutes).
    :rtype: float
    :raises ValueError: If the date or time string cannot be parsed.
    """
    # Parse the user-provided date and time
    user_datetime = dateparser.parse(f"{user_date_str} {user_time_str}")

    if not user_datetime:
        raise ValueError("Invalid date or time format. Please provide a recognizable format.")

    # Get the current UTC time
    utc_now = datetime.datetime.now(datetime.timezone.utc)

    # Calculate the UTC offset as a timedelta
    offset = user_datetime - utc_now.replace(tzinfo=None)

    # Convert timedelta to hours
    offset_hours = offset.total_seconds() / 3600

    # Snap to the nearest 15 minutes (0.25 hours)
    snapped_offset = round(offset_hours * 4) / 4

    # Return the calculated offset
    return snapped_offset

def calculate_age(local_datetime: datetime.datetime, birth_date: datetime.datetime) -> int:
    """
    Calculate the age based on a given local datetime and birth date.
    
    :param local_datetime: A timezone-aware datetime representing the current time in the user's local timezone.
    :type local_datetime: datetime
    :param birth_date: The user's birth date as a naive or timezone-aware datetime.
    :type birth_date: datetime
    :return: The calculated age.
    :rtype: int
    """
    # Ensure both inputs are date-only for comparison
    if isinstance(birth_date, datetime.datetime):
        birth_date = birth_date.date()
    local_date = local_datetime.date()
    
    # Calculate age by comparing year, month, and day
    age = local_date.year - birth_date.year - ((local_date.month, local_date.day) < (birth_date.month, birth_date.day))
    return age

async def fifteen_minutely_action(bot: nextcord.Client) -> None:
    """
    Run the 15-minute birthday task.

    This function is intended to be run every 15 minutes. It checks if the runtime
    for birthday messages is now, and if so, sends out birthday messages to the
    specified channels.

    :param bot: The bot client.
    :type bot: nextcord.Client
    :return: None
    :rtype: None
    """
    logging.info("15 MINUTE ACTION: Birthdays -----")
    if get_global_kill_status()["birthdays"]:
        logging.warning("Skipping birthdays because of global kill status.")
        return
    if get_bot_load_status() == False:
        logging.warning("Skipping birthdays because of bot load status.")
        return
    
    now = datetime.datetime.now(datetime.timezone.utc)
    now = now.replace(second=0, microsecond=0)
    hour_minute_now = now.strftime("%H:%M")
    
    for guild in bot.guilds:
        try:
            if guild == None: continue

            server = Server(guild.id)
            
            # Checks
            if server == None : continue
            if server.birthdays_profile.runtime == UNSET_VALUE: continue
            if len(server.birthdays) == 0: continue
            if server.birthdays_profile.utc_offset == UNSET_VALUE: continue

            # Check if runtime is now
            if hour_minute_now != server.birthdays_profile.runtime: continue

            logging.debug(f"Found a server with runtime now. Server: {guild.name} (ID: {guild.id})")

            # Get date to check (convert to the server's timezone)
            utc_offset = server.birthdays_profile.utc_offset
            local_datetime: datetime.datetime = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=utc_offset)

            # Find members with birthdays 
            # Based on IntegratedList_TableManager's get_matching() and _get_all_matching_indexes()
            query = f"SELECT {server.birthdays.secondary_key_sql_name} FROM {server.birthdays.table_name} WHERE {server.birthdays.primary_key_sql_name} = :primary_key_value AND strftime('%m-%d', birth_date) = :month_day"
            raw_values = server.birthdays.database.execute_query(query, {'primary_key_value': server.birthdays.primary_key_value, 'month_day': local_datetime.strftime("%m-%d")}, multiple_values=True)
            member_ids_with_birthdays_today = [server.birthdays.database.get_query_first_value(value) for value in raw_values]
            entrys_with_birthdays_today = [server.birthdays._get_entry(row) for row in member_ids_with_birthdays_today]

            logging.debug(f"Found {len(entrys_with_birthdays_today)} members with birthdays today.")

            for entry in entrys_with_birthdays_today:
                member_id = entry.member_id
                member = bot.get_user(member_id)

                if member == None: # Member left. Warn server owner
                    message = f"""
                    In the server {guild.name} ({guild.id}), the member {member_id} {f"({entry.real_name})" if entry.real_name != None else ""} has left the server.
                    
                    Please remove their birthday from InfiniBot.
                    """
                    message = utils.standardize_str_indention(message)
                    await utils.send_error_message_to_server_owner(guild, None, 
                                                                message = message)
                    continue

                # Calculate age
                birth_date = datetime.datetime.strptime(entry.birth_date, "%Y-%m-%d")
                age = calculate_age(local_datetime, birth_date)

                # Send birthday message
                # Send to server channel
                channel_id = server.birthdays_profile.channel
                
                if channel_id == UNSET_VALUE:
                    channel = guild.system_channel
                elif channel_id != None:
                    channel = guild.get_channel(channel_id)
                else:
                    logging.warning(f"Birthday channel id is NONE somehow in server {guild.id}. Ignoring...")
                    channel = None


                if channel is not None:
                    embed: nextcord.Embed = server.birthdays_profile.embed.to_embed()
                    embed.set_author(name = member.name, icon_url = member.display_avatar.url)

                    embed = utils.replace_placeholders_in_embed(embed, member, guild, custom_replacements={
                        "[age]" : str(age),
                        "[realname]" : (entry.real_name if entry.real_name != None else member.name)
                    })

                    await channel.send(embed = embed)

                # Send to DM
                member_settings = Member(member.id)
                if member_settings.direct_messages_enabled:
                    description = f"""
                    It's your birthday today! You just turned {age} years old! Happy birthday! 🎂

                    You recieved this message because you have a birthday setup in `{guild.name}`.
                    """
                    description = utils.standardize_str_indention(description)
                    embed = nextcord.Embed(title = f"Happy Birthday, {(entry.real_name if entry.real_name != None else member.name)}!", description=description,color = nextcord.Color.gold())
                    embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")

                    await member.send(embed = embed)

                logging.info("Successfully sent birthday message to member")

        except Exception as e:
            logging.error(f"ERROR when checking birthdays with guild {guild.id}: {e}")
            continue