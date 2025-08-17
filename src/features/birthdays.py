import datetime
import logging
import re
import nextcord
import zoneinfo

from components import utils
from config.global_settings import get_bot_load_status, get_global_kill_status
from config.member import Member
from config.server import Server
from modules.custom_types import UNSET_VALUE


def calculate_age(local_datetime: datetime.datetime, birth_date: datetime.date | datetime.datetime) -> int:
    """
    Calculate the age based on a given local datetime and birth date.
    
    :param local_datetime: A timezone-aware datetime representing the current time in the user's local timezone.
    :type local_datetime: datetime
    :param birth_date: The user's birth date as a naive or timezone-aware datetime.
    :type birth_date: date | datetime
    :return: The calculated age.
    :rtype: int
    """
    # Ensure both inputs are date-only for comparison
    if isinstance(birth_date, datetime.datetime):
        birth_date = birth_date.date()

    local_date = local_datetime.date()

    # Calculate age by comparing year, month, and day
    age = local_date.year - birth_date.year - (
        (local_date.month, local_date.day) < (birth_date.month, birth_date.day)
    )
    return age


async def check_and_run_birthday_actions(bot: nextcord.Client, guild: nextcord.Guild) -> None:
    """
    |coro|

    Run the 15-minute birthday task.

    This function is intended to be run every 15 minutes. It checks if the runtime
    for birthday messages is now, and if so, sends out birthday messages to the
    specified channels.

    :param bot: The bot client.
    :type bot: nextcord.Client
    :param guild: The guild to check for birthdays.
    :type guild: nextcord.Guild
    :return: None
    :rtype: None
    """
    
    logging.debug(f"Running scheduled action for birthdays in on guild: {guild.name} ({guild.id})")

    if get_global_kill_status()["birthdays"]:
        logging.warning("SKIPPING birthdays because of global kill status.")
        return
    if get_bot_load_status() is False:
        logging.warning("SKIPPING birthdays because of bot load status.")
        return

    now = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
    hour_minute_now = now.strftime("%H:%M")

    try:
        if guild is None:
            return

        server = Server(guild.id)

        # Checks
        if server is None:
            return
        if server.birthdays_profile.runtime == UNSET_VALUE:
            return
        if len(server.birthdays) == 0:
            return

        # Extract HH:MM from values like "18:00 UTC" or "8:00 PDT" or "18:00"
        runtime_text = str(server.birthdays_profile.runtime) # stored as UTC time
        m = re.search(r"\b(\d{1,2}):(\d{2})\b", runtime_text)
        runtime = f"{m.group(1).zfill(2)}:{m.group(2)}" if m else None
        logging.debug(f"Runtime: {runtime}, Current Time: {hour_minute_now}")
        
        if runtime is None or hour_minute_now != runtime:
            return

        logging.debug(f"Found a server with runtime now. Server: {guild.name} (ID: {guild.id})")

        # Convert to server's timezone
        local_datetime = datetime.datetime.now(datetime.timezone.utc).astimezone(
            zoneinfo.ZoneInfo(server.infinibot_settings_profile.timezone or "UTC")
        )

        # Find members with birthdays (month-day match)
        # Based on IntegratedList_TableManager's get_matching() and _get_all_matching_indexes()
        query = (
            f"SELECT {server.birthdays.secondary_key_sql_name} "
            f"FROM {server.birthdays.table_name} "
            f"WHERE {server.birthdays.primary_key_sql_name} = :primary_key_value "
            f"AND strftime('%m-%d', birth_date) = :month_day"
        )
        raw_values = server.birthdays.database.execute_query(
            query,
            {
                "primary_key_value": server.birthdays.primary_key_value,
                "month_day": local_datetime.strftime("%m-%d"),
            },
            multiple_values=True,
        )
        member_ids_with_birthdays_today = [
            server.birthdays.database.get_query_first_value(value) for value in raw_values
        ]
        entries_with_birthdays_today = [
            server.birthdays._get_entry(row) for row in member_ids_with_birthdays_today
        ]

        logging.debug(f"Found {len(entries_with_birthdays_today)} members with birthdays today.")

        for entry in entries_with_birthdays_today:
            member_id = entry.member_id
            member = await utils.get_member(guild, member_id)

            if member is None:  # Member left. Warn server owner
                name_part = f"({entry.real_name})" if entry.real_name is not None else ""
                message = f"""
                In the server {guild.name} ({guild.id}), the member {member_id} {name_part} has left the server.
                
                Please remove their birthday from InfiniBot.
                """
                message = utils.standardize_str_indention(message)
                await utils.send_error_message_to_server_owner(guild, None, message=message)
                continue

            # Parse birth date from string format "YYYY-MM-DD HH:MM:SS+TZ"
            try:
                birth_date = datetime.date.fromisoformat(entry.birth_date[:10])
            except Exception:
                logging.warning(
                    f"Unable to parse birth_date '{entry.birth_date}' for member {member_id} in guild {guild.id}; skipping."
                )
                continue

            age = calculate_age(local_datetime, birth_date)

            # Send to server channel
            channel_id = server.birthdays_profile.channel
            if channel_id == UNSET_VALUE:
                channel = guild.system_channel
            elif channel_id is not None:
                channel = guild.get_channel(channel_id)
            else:
                logging.warning(f"Birthday channel id is NONE somehow in server {guild.id}. Ignoring...")
                channel = None

            if channel is not None:
                embed: nextcord.Embed = server.birthdays_profile.embed.to_embed()
                embed.set_author(name=member.name, icon_url=member.display_avatar.url)
                embed = utils.apply_generic_replacements(
                    embed, member, guild,
                    custom_replacements={
                        "[age]": str(age),
                        "[realname]": (
                            entry.real_name if entry.real_name is not None else member.name
                        ),
                    },
                )

                try:
                    await channel.send(embed=embed)
                except nextcord.errors.Forbidden:
                    await utils.send_error_message_to_server_owner(
                        guild,
                        None,
                        message=utils.standardize_str_indention(f"""
                        InfiniBot couldn't send a birthday message to <#{channel.id}>. To fix this, either:
                        - Check the channel permissions / Ensure the channel is not deleted, or
                        - Change the notification channel for birthdays in the dashboard (`/dashboard`).
                        """),
                        administrator=False
                    )

            # Send DM
            member_settings = Member(member.id)
            if member_settings.direct_messages_enabled:
                description = f"""
                It's your birthday today! You just turned {age} years old! Happy birthday! 🎂

                You received this message because you have a birthday setup in `{guild.name}`.
                """
                description = utils.standardize_str_indention(description)
                embed = nextcord.Embed(
                    title=f"Happy Birthday, {entry.real_name if entry.real_name is not None else member.name}!", 
                    description=description,
                    color=nextcord.Color.gold()
                )
                embed.set_footer(text="To opt out of dm notifications, use /opt_out_of_dms")

                try:
                    await member.send(embed=embed)
                except nextcord.errors.Forbidden:
                    # User has DMs disabled. No need to log an error.
                    pass

            logging.info("Successfully sent birthday message to member")
    except Exception as e:
        logging.error(f"ERROR when checking birthdays with guild {guild.id}: {e}", exc_info=True)