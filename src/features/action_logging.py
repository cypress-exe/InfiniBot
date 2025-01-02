import asyncio
import datetime
import humanfriendly
import io
import logging
import math
import mmap
from nextcord import AuditLogAction, Interaction
import nextcord

from components import ui_components
from components import utils
from config.server import Server
from modules.custom_types import UNSET_VALUE


class ShowMoreButton(nextcord.ui.View):
  """
  A View that will be used for the Action Logging feature.
  """
  def __init__(self):
    super().__init__(timeout = None)
    self.possible_embeds = [
        ["Possible Margin For Error", "Infinibot is relying on an educated guess regarding the deleter of this message. Thus, there *is* a margin for error (In testing, about 2%)."],
        ["Possible Margin For Error", "Because the message can not be retrieved, Infinibot is relying on an educated guess regarding the author and deleter of this message. Thus, there *is* a margin for error (In testing, about 6.5%)."],
        ["Unable to find specifics", "Infinibot is unable to find any info regarding this message because of Discord's limitations.\n\nThe user might have deleted their own message."],
        ["Unable to find specifics", "Infinibot is unable to find the deleter because of Discord's limitations.\n\nThe user might have deleted their own message."]
    ]
  
  @nextcord.ui.button(label = 'Show More', style = nextcord.ButtonStyle.gray, custom_id = "show_more")
  async def event(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
    if button.label == "Show More":
        # Show more
        embed = interaction.message.embeds[0]
        code = embed.footer.text.split(" ")[-1]
        index = int(code) - 1
        
        info_embed = nextcord.Embed(title = "More Information", color = nextcord.Color.red())
        info_embed.add_field(name = self.possible_embeds[index][0], value = self.possible_embeds[index][1])
        
        # Change the Name of the button
        button.label = "Show Less"

        all_embeds = interaction.message.embeds
        all_embeds.append(info_embed)
    else:
        # Show less
        embed = interaction.message.embeds[0]
        
        # Change the Name of the button
        button.label = "Show More"
        
        if len(interaction.message.embeds) > 2:
            # Extra embeds were added to the message
            all_embeds = interaction.message.embeds[:-1] # Remove the last embed

    await interaction.response.edit_message(view=self, embeds = all_embeds)
  


async def should_log(guild: nextcord.Guild) -> tuple[bool, nextcord.TextChannel | None]:
    """
    |coro|

    Determines whether logging should be performed for the given guild.

    :param guild: The guild to check logging settings for.
    :type guild: nextcord.Guild
    :return: A tuple indicating whether logging is active and the log channel if active.
    :rtype: Tuple[bool, Optional[nextcord.TextChannel]]
    """

    server = Server(guild.id)
    
    if not utils.feature_is_active(server = server, feature = "logging"):
        return False, None

    log_channel_id = server.logging_profile.channel
    if log_channel_id == UNSET_VALUE:
        return False, None
    
    log_channel = guild.get_channel(log_channel_id)
    if not log_channel:
        return False, None
    
    if not await utils.check_text_channel_permissions(log_channel, True, custom_channel_name = f"Log Message Channel (#{log_channel.name})"):
        return False, None
    
    else:
        return True, log_channel

def entry_is_fresh(entry: nextcord.AuditLogEntry) -> bool:
    """
    Determines whether the given AuditLogEntry is fresh enough to be considered recently modified.

    :param entry: The AuditLogEntry to check the freshness of.
    :type entry: nextcord.AuditLogEntry
    :return: A boolean indicating whether the entry is considered fresh.
    :rtype: bool
    """
    return (entry.created_at.month == datetime.datetime.now(datetime.timezone.utc).month 
                            and entry.created_at.day == datetime.datetime.now(datetime.timezone.utc).day 
                            and entry.created_at.hour == datetime.datetime.now(datetime.timezone.utc).hour 
                            and ((datetime.datetime.now(datetime.timezone.utc).minute - entry.created_at.minute) <= 5))

async def trigger_edit_log(guild: nextcord.Guild, original_message: nextcord.Message, edited_message: nextcord.Message, user: nextcord.Member = None) -> None:
    """
    |coro|

    Triggers the edit log system.

    :param guild: The guild where the edited message is located.
    :type guild: nextcord.Guild
    :param original_message: The original message.
    :type original_message: nextcord.Message
    :param edited_message: The edited message.
    :type edited_message: nextcord.Message
    :param user: The user who edited the message. If None, the author of the edited message is used.
    :type user: Optional[nextcord.Member]
    :return: None
    :rtype: None
    """

    if not user: user = edited_message.author

    # Get the log channel
    server = Server(guild.id)
    if not utils.feature_is_active(server = server, feature = "logging"): return
    log_channel_id = server.logging_profile.channel
    if log_channel_id == UNSET_VALUE: return
    log_channel = guild.get_channel(log_channel_id)
    if not log_channel: return
    if not await utils.check_text_channel_permissions(log_channel, True, custom_channel_name = f"Log Message Channel (#{log_channel.name})"): return
    
    # Avatar
    avatar_url = user.display_avatar.url
    # Field name, Link name, content
    content_tasks = []
    # Added or Deleted, embed
    embed_tasks = []

    # Create an embed to edit
    embed = nextcord.Embed(title = "Message Edited", description = edited_message.channel.mention, color = nextcord.Color.yellow(), timestamp = datetime.datetime.now(), url = edited_message.jump_url)
    
    # Check that the original message is still cached
    if not original_message:
        # Configure the embed
        embed.add_field(name = "Contents Unretrievable", value = "The original message is unretrievable because the message was created too long ago.")
        
        # Add the extra stuff in the message
        embed.set_author(name = user.name, icon_url = avatar_url)
        
        # Send the message
        await log_channel.send(embed = embed)
        return
    
    
    # Compare Contents
    if original_message.content != edited_message.content:
        if len(original_message.content) <= 1024:
            embed.add_field(name = "Original Message", value = original_message.content)
        elif len(original_message.content) > 2000:
            embed.add_field(name = "Original Message", value = "Message too long. Please wait...")
            content_tasks.append(["Original Message", "View Original Message (Truncated)", original_message.content[:1999]])
        else:
            embed.add_field(name = "Original Message", value = "Message too long. Please wait...")
            content_tasks.append(["Original Message", "View Original Message", original_message.content])
            
        if len(edited_message.content) <= 1024:
            embed.add_field(name = "Edited Message", value = edited_message.content)
        elif len(edited_message.content) > 2000:
            embed.add_field(name = "Edited Message", value = "Message too long. Please wait...")
            content_tasks.append(["Edited Message", "View Edited Message (Truncated)", edited_message.content[:1999]])
        else:
            embed.add_field(name = "Edited Message", value = "Message too long. Please wait...")
            content_tasks.append(["Edited Message", "View Edited Message", edited_message.content])
            
            
    # Compare embeds
    if (len(original_message.embeds) > 0) or (len(edited_message.embeds)) > 0:
        deleted_embeds = []
        for original_embed in original_message.embeds:
            counterpart_exists = False
            for edited_embed in edited_message.embeds:
                if original_embed == edited_embed:
                    counterpart_exists = True
                    break
                
            if not counterpart_exists:
                # They deleted or edited this embed
                deleted_embeds.append(original_embed)
                
        added_embeds = []
        for edited_embed in edited_message.embeds:
            counterpart_exists = False
            for original_embed in original_message.embeds:
                if edited_embed == original_embed:
                    counterpart_exists = True
                    break
                
            if not counterpart_exists:
                # They added or edited this embed
                added_embeds.append(edited_embed)
                
        if deleted_embeds == [] and added_embeds == []:
            # They didn't do anything to the embeds
            pass
        else:
            # They DID do something to the embeds.
            embed.add_field(name = "Embed(s)", value = "One or more embeds were modified. Here's a list of modifications:\n\nPlease Wait...\n\nNote: Edited embeds will appear as them being deleted then added.", inline = False)
            
            # Loop through embeds
            for embed in deleted_embeds:
                embed_tasks.append(["Deleted", embed])
            
            for embed in added_embeds:
                embed_tasks.append(["Added", embed])
                
    
    # Add the extra stuff in the message
    embed.set_author(name = user.name, icon_url = avatar_url)
                
    # Send Message
    message = await log_channel.send(embed = embed)
    
    # Do the other stuff after sending the message
    if message: # We want to make sure that the message was even sent
        if content_tasks == [] and embed_tasks == []: return
        
        completed_content_tasks = []
        for task in content_tasks:
            content_message = await log_channel.send(content = task[2], reference = message)
            completed_content_tasks.append([task[0], task[1], content_message.jump_url])
            
        completed_embed_tasks = []
        for task in embed_tasks:
            embed_message = await log_channel.send(embed = task[1], reference = message)
            completed_embed_tasks.append([task[0], task[1].title, embed_message.jump_url])
            
        # We've sent the other messages. Time to circle back and edit our old message to include the just sent links
        fields = embed.fields
        
        # Clear the old fields
        embed.clear_fields()
        
        # Update the fields and re-add them
        completed_content_tasks_field_names = [task[0] for task in completed_content_tasks]
        for field in fields:
            if field.name in completed_content_tasks_field_names:
                # This is where our content info will go (it could be an original message or an edited message)
                index = completed_content_tasks_field_names.index(field.name)
                embed.add_field(name = completed_content_tasks[index][0], value = f"[{completed_content_tasks[index][1]}]({completed_content_tasks[index][2]})", inline = field.inline)
                continue

            if field.name == "Embed(s)":
                # This is where our embed info will go
                links = []
                for task in completed_embed_tasks:
                    links.append(f"• **{task[0]}** [{task[1]}]({task[2]})")
                    
                content = field.value
                content = content.replace("Please Wait...", "\n".join(links))
                embed.add_field(name = field.name, value = content, inline = field.inline)
                continue
            
            # The field was not a task, but we should still replace it
            embed.add_field(name = field.name, value = field.value, inline = field.inline)
                
        # Finally, update the old message to have the new embed
        await message.edit(embed = embed)
    
async def file_computation(file: nextcord.Attachment) -> nextcord.File | None:
    """
    |coro|

    :param file: The file to be processed
    :type file: nextcord.Attachment
    :return: The processed file, or None if there was an error
    :rtype: nextcord.File or None
    """
    # ChatGPT :)
    try:
        file_bytes = await file.read()
        
        with mmap.mmap(-1, len(file_bytes), access=mmap.ACCESS_WRITE) as mem:
            mem.write(file_bytes)
            mem.seek(0)
            file_data = bytes(mem)
            
        file = nextcord.File(io.BytesIO(file_data), file.filename, description=file.description, spoiler=file.is_spoiler())
        return file
    except:
        return None
    
async def files_computation(deleted_message: nextcord.Message, log_channel: nextcord.TextChannel, log_message: nextcord.Message) -> None:
    """
    |coro|

    Compute a list of files from a deleted message.

    :param deleted_message: The deleted message that had the attachments
    :type deleted_message: nextcord.Message
    :param log_channel: The channel to send the files to
    :type log_channel: nextcord.TextChannel
    :param log_message: The message to update after sending all the files
    :type log_message: nextcord.Message
    :return: None
    :rtype: None
    """
    
    # ChatGPT :)
    # Create tasks for each attachment
    tasks = []
    for attachment in deleted_message.attachments:
        tasks.append(asyncio.create_task(file_computation(attachment)))
    
    # Wait for all tasks to complete asynchronously
    completed_tasks = await asyncio.gather(*tasks)
    
    # Collect the files from the completed tasks
    files = [task_result for task_result in completed_tasks if task_result is not None]
    
        
    if len(files) > 0:
        await log_channel.send(files = files, reference = log_message)
    else:
        await log_channel.send(embed = nextcord.Embed(title = "Error", description = "There was a problem when retrieving these files. They have been lost to the void.", color = nextcord.Color.red()), reference = log_message)



async def log_raw_message_edit(guild: nextcord.Guild, before_message: nextcord.Message, after_message: nextcord.Message) -> None:
    """
    |coro|

    Logs the edit of a message in a guild.

    :param guild: The guild where the message was edited.
    :type guild: nextcord.Guild
    :param before_message: The original message before it was edited.
    :type before_message: nextcord.Message
    :param after_message: The message after it was edited.
    :type after_message: nextcord.Message
    :return: None
    :rtype: None
    """

    # Test if logging is enabled
    logging_enabled, _ = await should_log(guild)
    if not logging_enabled: return
    
    # Test for false-positives
    if not logging_enabled: return
    if after_message.author.bot == True: return
    if after_message == None: return
    if after_message.content == "": return
    if before_message != None and before_message.content == "": return
    if before_message != None and after_message.content == before_message.content: return
    
    # UI Log
    await trigger_edit_log(guild, before_message, after_message)
 
async def log_raw_message_delete(bot: nextcord.Client, guild: nextcord.Guild, channel: nextcord.TextChannel, message: nextcord.Message, message_id: int) -> None:
    """
    |coro|

    Logs the deletion of a message in a guild.

    :param bot: The bot instance
    :type bot: nextcord.Client
    :param guild: The guild where the message was deleted
    :type guild: nextcord.Guild
    :param channel: The channel where the message was deleted
    :type channel: nextcord.TextChannel
    :param message: The message that was deleted
    :type message: nextcord.Message
    :param message_id: The ID of the message that was deleted
    :type message_id: int
    :return: None
    :rtype: None
    """
    # Make sure that logging is enabled
    logging_enabled, log_channel = await should_log(guild)
    if not logging_enabled: return
    
    await asyncio.sleep(1) # We need this time delay for some other features
    
    # Remove the message if we're storing it TODO
    # server = Server(guild.id)
    # server.messages.delete(payload.message_id)
    # server.messages.save()
    # del server

    # Do not trigger if confident that the message was InfiniBot's
    if message:
        if message.author.id == bot.application_id: return
    
    # Gather more data and eliminate cases -----------------------------------------------------------------------------------------------------------------------------
    # Get more information about the message with Audit Logs
    if not guild.me.guild_permissions.view_audit_log:
        await utils.send_error_message_to_server_owner(guild, "View Audit Log", guild_permission = True)
        return
    try:
        entry = await anext( # Grabs the first item from an iterator.
            guild.audit_logs(limit=1, action=AuditLogAction.message_delete), # Iterator
            None # If the Iterator is empty, return None without throwing an error
        )
    except Exception as e:
        logging.error(f"Error getting audit log in {guild.id}: {e}")
        return
    
    # Log whether or not the audit log is fresh enough to be accurate (within 5 seconds)
    if entry: fresh_audit_log = entry_is_fresh(entry)
    else: fresh_audit_log = False
    
    if entry and fresh_audit_log:
        # We prioritize the author of the message if we know it, but if we don't we use this
        if not message: user = entry.target
        else: user = message.author
        # Set the deleter (because we didn't know that before)
        deleter = entry.user
    else:
        # The user probably just deleted their own message. We'll go with that theory.
        # We don't actually need any of this information to exist then
        if not message: user = None
        deleter = None
    
    # Eliminate whether InfiniBot is the author / deleter (only do this if we're sure that the audit log is fresh)
    if fresh_audit_log and user.id == bot.application_id: return
    if fresh_audit_log and deleter.id == bot.application_id: return
        
    
    # Send log information!!! -------------------------------------------------------------------------------------------------------------------------------------------
    embed = nextcord.Embed(title = "Message Deleted", color = nextcord.Color.red(), timestamp = datetime.datetime.now())
    embeds = []
    code = 1
    
    # Embed description and code
    if fresh_audit_log:
        if deleter.id != user.id:
            embed.description = f"{deleter.mention} deleted {user.mention}'s message from {channel.mention}"
        else:
            embed.description = f"{deleter.mention} deleted their message from {channel.mention}"
            
        if message:
            code = 1
        else:
            code = 2
    else:
        if not message:
            embed.description = f"A message was deleted from {channel.mention}"
            code = 3
        else:
            embed.description = f"{message.author.mention}'s message was deleted from {channel.mention}"
            code = 4
            
    
    # Message content
    if message: 
        if message.content != "": 
            if len(message.content) <= 1024: 
                embed.add_field(name = "Message", value = message.content)
            else:
                embed.add_field(name = "Message", value = "Message is too long! Discord won't display it.")
    else: 
        embed.add_field(name = "Message", value = "The message cannot be retrieved. This is due to the message being deleted too long after creation. This is a Discord limitation.", inline = False)
    
    # Attached Embeds
    if message and message.embeds != []:
        attachedMessage = "Attached below"
        if len(message.embeds) > 9:
            attachedMessage = f"9/{len(message.embeds)} are attached below"
            
        embed.add_field(name = "Embeds", value = f"This message contained one or more embeds. ({attachedMessage})", inline = False)
        embeds = message.embeds
        
    # Attached Files
    if message and message.attachments != []:              
        embed.add_field(name = "Files", value = f"This message contained one or more files. (Attached Below)\n→ Please wait as InfiniBot processes these files and Discord uploads them", inline = False)
        
    if fresh_audit_log and entry.reason != None:
            embed.add_field(name = "Reason", value = entry.reason, inline = False)

    # The Profile
    if deleter:
        embed.set_author(name = deleter.name, icon_url = deleter.display_avatar.url)  
        
    # The footer
    embed.set_footer(text = f"Message ID: {message_id}\nCode: {code}")

    # Actually send the embed
    view = ShowMoreButton()
    log_message = await log_channel.send(view = view, embeds = ([embed] + (embeds[0:8] if len(embeds) >= 10 else embeds)))
    if message and message.attachments != []:
        await files_computation(message, log_channel, log_message)

async def log_member_update(before: nextcord.Member, after: nextcord.Member) -> None:
    """
    |coro|

    Logs a member update event.

    :param before: The member before the update.
    :type before: nextcord.Member
    :param after: The member after the update.
    :type after: nextcord.Member
    :return: None
    :rtype: None
    """
    guild = after.guild

    logging_enabled, log_channel = await should_log(guild)
    if not logging_enabled: return

    if not guild.me.guild_permissions.view_audit_log:
        await utils.send_error_message_to_server_owner(guild, "View Audit Log", guild_permission = True)
        return
    
    # Wait 1 second for the audit log to catch up
    await asyncio.sleep(1)

    # Get audit log entry
    entry = await anext(
        guild.audit_logs(limit=1),
        None
    )

    fresh_audit_log = entry_is_fresh(entry)
    
    if entry == None:
        # No audit log entry
        return

    # Nickname change --------------------------------------------------------------
    if before.nick != after.nick:
        user = entry.user

        embed = nextcord.Embed(title = "Nickname Changed", description = f"{user.mention} changed {after.mention}'s nickname.", color = nextcord.Color.blue(), timestamp = datetime.datetime.now())

        if before.nick != None: embed.add_field(name = "Before", value = before.nick, inline = True)
        else: embed.add_field(name = "Before", value = "None", inline = True)

        if after.nick != None: embed.add_field(name = "After", value = after.nick, inline = True)
        else: embed.add_field(name = "After", value = "None", inline = True)

        if fresh_audit_log and entry.reason != None:
            embed.add_field(name = "Reason", value = entry.reason, inline = False)

        await log_channel.send(embed = embed)

    # Roles change --------------------------------------------------------------  
    if before.roles != after.roles:
        added_roles = []
        for after_role in after.roles:
            for before_role in before.roles:
                found_role = False
                if before_role == after_role:
                    found_role = True
                    break

            if found_role == False:
                added_roles.append(after_role.mention)
        
        deleted_roles = []
        for before_role in before.roles:
            for after_role in after.roles:
                found_role = False
                if before_role == after_role:
                    found_role = True
                    break
            
            if found_role == False:
                deleted_roles.append(before_role.mention)

        if len(added_roles) == 0 and len(deleted_roles) == 0:
            return
        
        if len(deleted_roles) == 0 and len(added_roles) == 1:
            if guild.premium_subscriber_role:
                if added_roles[0].id == guild.premium_subscriber_role.id: return # Do not log when a user gets the boost role
        
        user = entry.user
        if fresh_audit_log:
            description = f"{user.mention} modified {after.mention}'s roles."
        else:
            description = f"Someone modified {after.mention}'s roles."

        embed = nextcord.Embed(title = "Roles Modified", description = description, color = nextcord.Color.blue(), timestamp = datetime.datetime.now())

        if len(added_roles) > 0:
            embed.add_field(name = "Added", value = "\n".join(added_roles), inline = True)

        if len(deleted_roles) > 0:
            embed.add_field(name = "Removed", value = "\n".join(deleted_roles), inline = False)

        if fresh_audit_log and entry.reason != None:
            embed.add_field(name = "Reason", value = entry.reason, inline = False)

        await log_channel.send(embed = embed)
            
    # Timeout change --------------------------------------------------------------
    if before.communication_disabled_until != after.communication_disabled_until:
        user = entry.user
            
        if before.communication_disabled_until == None: # If they weren't timed out before
            # Get the seconds
            timeout_time: datetime.timedelta = after.communication_disabled_until - datetime.datetime.now(datetime.timezone.utc)

            # Round to the nearest second (ceiling)
            rounded_timeout_time = datetime.timedelta(seconds=math.ceil(timeout_time.total_seconds()))
            
            # Display
            timeout_time_ui_text = humanfriendly.format_timespan(rounded_timeout_time)
            embed = nextcord.Embed(title = "Member Timed-Out", description = f"{user.mention} timed out {after.mention} for about {timeout_time_ui_text}", color = nextcord.Color.orange(), timestamp = datetime.datetime.now())
            
            if fresh_audit_log and entry.reason != None:
                embed.add_field(name = "Reason", value = entry.reason)
            
            await log_channel.send(embed = embed)
            
        elif after.communication_disabled_until == None: #their timeout was removed manually
            embed = nextcord.Embed(title = "Timeout Revoked", description = f"{user.mention} revoked {after.mention}'s timeout", color = nextcord.Color.orange(), timestamp = datetime.datetime.now())
            
            await log_channel.send(embed = embed)

async def log_member_removal(guild: nextcord.Guild, member: nextcord.Member) -> None:
    """
    |coro|

    Logs a member removal event.

    :param guild: The guild the member was removed from.
    :type guild: nextcord.Guild
    :param member: The member that was removed.
    :type member: nextcord.Member
    :return: None
    :rtype: None
    """
    if guild == None: return
    if guild.unavailable: return
    if guild.me == None: return
    
    if not guild.me.guild_permissions.view_audit_log:
        await utils.send_error_message_to_server_owner(guild, "View Audit Log", guild_permission = True)
        return
    
    entries = guild.audit_logs(limit=5) # Look 5 entries back in the audit log to find the kick/ban
    entry = None
    async for _entry in entries:
        if _entry.action == AuditLogAction.kick or _entry.action == AuditLogAction.ban:
            entry = _entry
            break
        
    if entry == None: # User chose to leave the server
        return
    
    user = entry.user 
    reason = entry.reason

    logging_enabled, log_channel = await should_log(guild)
    if logging_enabled:
        if entry.action == AuditLogAction.kick:
            embed = nextcord.Embed(title = "Member Kicked", description = f"{user} kicked {member}.", color = nextcord.Color.red(), timestamp = datetime.datetime.now())
            embed.add_field(name = "Reason", value = f"{reason}", inline = False)
            
        elif entry.action == AuditLogAction.ban:
            embed = nextcord.Embed(title = "Member Banned", description = f"{user} banned {member}.", color = nextcord.Color.dark_red(), timestamp = datetime.datetime.now())
            embed.add_field(name = "Reason", value = f"{reason}", inline = False)
            
        else:
            return
        
        await log_channel.send(embed = embed)


async def run_set_log_channel_command(interaction: Interaction) -> None:
    """
    |coro|

    Runs the command to set the log channel for moderation updates and alerts.

    :param interaction: The interaction object from the Discord event.
    :type interaction: Interaction
    
    :return: None
    :rtype: None
    """
    if await utils.user_has_config_permissions(interaction) and await utils.check_and_warn_if_channel_is_text_channel(interaction):
        server = Server(interaction.guild.id)

        server.logging_profile.channel = interaction.channel.id

        embed = nextcord.Embed(title = "Log Channel Set", description = f"This channel will now be used for logging.\n\n**Notification Settings**\nSet notification settings for this channel to \"Nothing\". InfiniBot will constantly be sending log messages in this channel.", color =  nextcord.Color.green())
        embed.set_footer(text = f"Action done by {interaction.user}")
        await interaction.response.send_message(embed = embed, view = ui_components.SupportAndInviteView())