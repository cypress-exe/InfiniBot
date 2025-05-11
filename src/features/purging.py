from nextcord import Interaction
import nextcord
import logging
import asyncio
import datetime

from components import utils, ui_components
from config.global_settings import is_channel_purging, add_channel_to_purging, remove_channel_from_purging, ShardLoadedStatus
from config.server import Server

class ConfirmationView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        self.choice = None
        
        self.no_btn = nextcord.ui.Button(label="No", style=nextcord.ButtonStyle.red)
        self.no_btn.callback = self.no_btn_callback
        self.add_item(self.no_btn)
        
        self.yes_btn = nextcord.ui.Button(label="Yes", style=nextcord.ButtonStyle.green)
        self.yes_btn.callback = self.yes_btn_callback
        self.add_item(self.yes_btn)

    async def no_btn_callback(self, interaction: Interaction):
        self.choice = False
        self.disable_buttons()

        await interaction.response.edit_message(view=self, delete_after=1.0)
        self.stop()

    async def yes_btn_callback(self, interaction: Interaction):
        self.choice = True
        self.disable_buttons()

        await interaction.response.edit_message(view=self, delete_after=1.0)
        self.stop()

    def disable_buttons(self):
        self.no_btn.disabled = True
        self.yes_btn.disabled = True

async def run_purge_command(interaction: Interaction, amount: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            embed=nextcord.Embed(
                title="Permission Error", 
                description="You do not have the \"manage messages\" permission which is required to use this command.", 
                color=nextcord.Color.red()
            ), 
            ephemeral=True
        )
        return
    
    # Ensure InfiniBot loaded
    with ShardLoadedStatus() as shards_loaded_status:
        if not interaction.guild.shard_id in shards_loaded_status:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="InfiniBot Still Loading", 
                    description="InfiniBot is still loading. Please try again in a few minutes.", 
                    color=nextcord.Color.red()
                ), 
                ephemeral=True
            )
            return

    if await utils.user_has_config_permissions(interaction):
        if not utils.feature_is_active(feature="purging", guild_id=interaction.guild.id):
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Purging Disabled", 
                    description="Purging has been disabled by the developers of InfiniBot. This is likely due \
                    to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", 
                    color=nextcord.Color.red()
                ), 
                ephemeral=True
            )
            return
        
        def is_valid_input(input: str):
            if not input: return False
            if input.isdigit(): 
                if int(input) <= 0: return False
                return True
            if input.lower() == "all": return True
            return False
        
        if not is_valid_input(amount):
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Invalid Purge Amount", 
                    description="The purge amount must be a positive number or \"all\".", 
                    color=nextcord.Color.red()
                ), 
                ephemeral=True
            )
            return
        
        if amount.lower() == "all":
            # Show confirmation view
            embed = nextcord.Embed(
                title="Are you sure?", 
                description="Are you sure you want to purge (delete) all messages in this channel?\n\n\
                **WARNING**\nInfiniBot will replace this channel with an identical copy to instantly purge it. \
                InfiniBot will try to preserve configurations for this channel, but third-party services that \
                store their own data may be affected.\n\nIf you still would like to continue, click \"Yes\".", 
                color=nextcord.Color.orange()
            )

            embed.set_footer(text="This action cannot be undone. Use with caution.")

            view = ConfirmationView()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            await view.wait()

            if not view.choice:
                return
            
            if not interaction.channel.permissions_for(interaction.guild.me).manage_channels:
                await interaction.followup.send(
                    embed=nextcord.Embed(
                        title="Permission Error", 
                        description="InfiniBot needs to have the Manage Channels permission in this channel to use this command.", 
                        color=nextcord.Color.red()
                    ), 
                    ephemeral=True
                )
                return
            
            # Create a channel, and move it to where it should
            try:
                new_channel: nextcord.TextChannel = await interaction.channel.clone(reason="Purging Channel")
                await new_channel.edit(position=interaction.channel.position + 1, reason="Purging Channel")
            except nextcord.errors.Forbidden:
                await interaction.followup.send(
                    embed=nextcord.Embed(
                        title="Unknown Error", 
                        description="An unknown error occurred when purging the channel. Please double check InfiniBot's \
                        permissions and try again.\n\nNote: It is possible that InfiniBot started the purging process but \
                        failed to finish. There might be an extra cloned channel that needs to be deleted. You may want to double check.", 
                        color=nextcord.Color.red()
                    ), 
                    ephemeral=True
                )
                return
            


            # Check for if the channel is connected to anything. And if so, replace it:
            try:
                server = Server(interaction.guild.id)

                def get_attr(parent,attr_name):
                    attr_parts = attr_name.split(".")
                    attr = parent
                    for part in attr_parts:
                        attr = getattr(attr, part)
                    return attr
                
                def set_attr(parent, attr_name, value):
                    attr_parts = attr_name.split(".")
                    attr = parent
                    for part in attr_parts[:-1]:
                        attr = getattr(attr, part)
                    setattr(attr, attr_parts[-1], value)

                items_to_check = [
                    "profanity_moderation_profile.channel",
                    "logging_profile.channel",
                    "leveling_profile.channel",
                    "join_message_profile.channel",
                    "leave_message_profile.channel"
                ]

                recursive_items_to_check = [
                    "leveling_profile.exempt_channels"
                ]

                for item in items_to_check:
                    if get_attr(server, item) == interaction.channel.id:
                        set_attr(server, item, new_channel.id)

                for item in recursive_items_to_check:
                    changed = False
                    attr = get_attr(server, item)
                    for channel_id in attr:
                        if channel_id == interaction.channel.id:
                            channel_id = new_channel.id
                            changed = True
                            break
                    
                    if changed:
                        set_attr(server, item, attr)

            except Exception as e:
                logging.error(f"Failed to update server: {e}")

            try:
                # Update the System Messages Channel
                if interaction.guild._system_channel_id == interaction.channel.id:
                    if not interaction.guild.me.guild_permissions.manage_guild:
                        await utils.send_error_message_to_server_owner(interaction.guild, "Manage Server", message="InfiniBot is missing the Manage Server permission. This means that it can't transfer the System Messages Channel to the new, cloned channel automatically that it created when purging. Please transfer the System Messages Channel to the new channel manually, and give InfiniBot the Manage Server permission for the future.")
                    await interaction.guild.edit(system_channel=new_channel, reason="Purging Channel. Transfered System Messages Channel to new, cloned channel.")

            except Exception as e:
                logging.error(f"Failed to update system channel: {e}")
            
            # Delete old channel
            try:
                await interaction.channel.delete(reason="Purging Channel")
            except nextcord.errors.Forbidden:
                await interaction.followup.send(
                    embed=nextcord.Embed(
                        title="Unknown Error", 
                        description="An unknown error occurred when purging the channel. Please double check InfiniBot's \
                        permissions and try again.\n\nNote: It is possible that InfiniBot cloned this channel. You may want to double check.", 
                        color=nextcord.Color.red()
                    ), 
                    ephemeral=True
                )
                return
            
            await new_channel.send(
                embed=nextcord.Embed(
                    title="Purged Messages", 
                    description=f"{interaction.user} has instantly purged {new_channel.mention} of all messages", 
                    color=nextcord.Color.orange(),
                    timestamp=datetime.datetime.now(tz=datetime.timezone.utc)
                ), 
                view=ui_components.InviteView()
            )
        
        else:
            # Purging a specified amount of messages
            try:
                int(amount)
            except TypeError:
                interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="Format Error", 
                        description="\"Amount\" needs to be a number", 
                        color=nextcord.Color.red()
                    ), 
                    ephemeral=True
                )
                return

            # Get confirmation
            embed = nextcord.Embed(
                title="Are you sure?", 
                description=f"Are you sure you want to purge (delete) {amount} messages in this channel?\n\nThis action cannot \
                be undone.", 
                color=nextcord.Color.orange()
            )

            view = ConfirmationView()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            await view.wait()

            if not view.choice:
                return
            
            if is_channel_purging(interaction.guild_id):
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="Purging Error", 
                        description="This channel is already being purged.", 
                        color=nextcord.Color.red()
                    )
                )
                return

            add_channel_to_purging(interaction.guild_id)

            deleted = []

            try:
                deleted = await interaction.channel.purge(limit=int(amount))
            except nextcord.errors.NotFound:
                # We reached the end of all the messages that we can purge.
                pass
            except Exception as e:
                # Remove it from the purging list
                if is_channel_purging(interaction.guild_id):
                    remove_channel_from_purging(interaction.guild_id)
                    
                # Throw error
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="Unknown Error", 
                        description="An unknown error occurred when purging. Please double check InfiniBot's permissions and try again.", 
                        color=nextcord.Color.red()
                    ), 
                    ephemeral=True
                )
                
                # Log error
                logging.error(f"Failed to purge channel: {e}")
                return

            await asyncio.sleep(1)

            if is_channel_purging(interaction.guild_id):
                remove_channel_from_purging(interaction.guild_id)

            await interaction.channel.send(
                embed=nextcord.Embed(
                    title="Purged Messages", 
                    description=f"{interaction.user} has purged {interaction.channel.mention} of {str(len(deleted))} messages", 
                    color=nextcord.Color.orange(),
                    timestamp=datetime.datetime.now(tz=datetime.timezone.utc)
                ), 
                view=ui_components.InviteView()
            )
