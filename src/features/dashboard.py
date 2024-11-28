import copy
import datetime
import json
import logging

import humanfriendly
import nextcord
from nextcord import Interaction

from components import ui_components, utils
from components.ui_components import CustomView, CustomModal
from config.global_settings import shards_loaded, get_configs
from config.server import Server
from features import help_commands
from modules.custom_types import UNSET_VALUE



class Dashboard(CustomView):
    def __init__(self):
        super().__init__(timeout = None)
        
        self.moderation_btn = self.ModerationButton(self)
        self.add_item(self.moderation_btn)
        
        self.logging_btn = self.LoggingButton(self)
        self.add_item(self.logging_btn)
        
        self.leveling_btn = self.LevelingButton(self)
        self.add_item(self.leveling_btn)
        
        self.join_leave_messages_btn = self.JoinLeaveMessagesButton(self)
        self.add_item(self.join_leave_messages_btn)
        
        self.birthdays_btn = self.BirthdaysButton(self)
        self.add_item(self.birthdays_btn)
        
        self.default_roles_btn = self.DefaultRolesButton(self)
        self.add_item(self.default_roles_btn)
        
        self.join_to_create_VCs_button = self.JoinToCreateVCsButton(self)
        self.add_item(self.join_to_create_VCs_button)
        
        self.extra_features_btn = self.ExtraFeaturesButton(self)
        self.add_item(self.extra_features_btn)

    async def setup(self, interaction: Interaction):
        for child in self.children: del child
        self.__init__()
        
        if not utils.feature_is_active(guild_id = interaction.guild.id, feature = "dashboard"):
            await ui_components.disabled_feature_override(self, interaction)
            return
        
        if not interaction.guild.shard_id in shards_loaded:
            logging.warning(f"Dashboard:Shard {interaction.guild.shard_id} is not loaded. Forwarding to inactive screen for guild {interaction.guild.id}.")
            await ui_components.infinibot_loading_override(self, interaction)
            return
        
        description = """Welcome to the InfiniBot Dashboard! Choose a feature to setup / edit:"""
        
        # On Mobile, extra spaces cause problems. We'll get rid of them here:
        description = utils.standardize_str_indention(description)
        
        embed = nextcord.Embed(title = "Dashboard", description = description, color = nextcord.Color.blue())
        try: await interaction.response.edit_message(embed = embed, view = self)
        except: await interaction.response.send_message(embed = embed, view = self, ephemeral=True)
              

    class ModerationButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Moderation", style = nextcord.ButtonStyle.gray)
            self.outer = outer 
          
        class ModerationView(CustomView):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.profane_moderation_btn = self.ProfaneModerationButton(self)
                self.add_item(self.profane_moderation_btn)
                
                self.spam_moderation_btn = self.SpamModerationButton(self)
                self.add_item(self.spam_moderation_btn)
                
                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1) 
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                
            async def setup(self, interaction: Interaction):
                for child in self.children: 
                    del child
                    self.__init__(self.outer)
                
                description = """
                InfiniBot will help you moderate your server with built-in profanity and spam moderation.
                
                **Exemptions**
                Members with the "Administrator" permission are exempt from moderation.
                InfiniBot will not moderate age-restricted channels for profanity.
                
                Use the buttons below to configure profanity and spam moderation.
                """
                
                description = utils.standardize_str_indention(description)
                
                embed = nextcord.Embed(title = "Dashboard - Moderation", description = description, color = nextcord.Color.blue())
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class ProfaneModerationButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Profanity", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class ProfaneModerationView(CustomView):
                    def __init__(self, outer, guild_id, onboarding_modifier = None, onboarding_embed = None):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.onboarding_modifier = onboarding_modifier
                        self.onboarding_embed = onboarding_embed
                        
                        self.filtered_words_btn = self.FilteredWordsButton(self)
                        self.add_item(self.filtered_words_btn)
                        
                        self.timeout_duration_btn = self.TimeoutDurationButton(self)
                        self.add_item(self.timeout_duration_btn)
                        
                        self.admin_channel_btn = self.AdminChannelButton(self)
                        self.add_item(self.admin_channel_btn)

                        self.manage_strike_system_btn = self.ManageStrikeSystemButton(self)
                        self.add_item(self.manage_strike_system_btn)
                        
                        self.disable_btn = self.EnableDisableButton(self)
                        self.add_item(self.disable_btn)
                        
                        self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 3) 
                        self.back_btn.callback = self.back_btn_callback
                        self.add_item(self.back_btn)
                                    
                    async def setup(self, interaction: Interaction):
                        # Redirect to Activation Screen if needed
                        server = Server(interaction.guild.id)
                        if not server.profanity_moderation_profile.active: 
                            logging.debug(f"Profanity moderation is disabled for server {interaction.guild.id}. Forwarding to activation screen.")
                            await self.EnableDisableButton.EnableDisableView(self).setup(interaction)
                            return
                            
                        if self.onboarding_modifier: self.onboarding_modifier(self)
                        
                        # Clean up
                        if not self.onboarding_modifier:
                            for child in self.children: 
                                del child 
                                self.__init__(self.outer, interaction.guild.id)
                        
                        # Global Kill
                        if not utils.feature_is_active(server = server, feature = "profanity_moderation"): # Works because we redirect to the activation screen if profanity moderation is locally disabled
                            logging.debug(f"Profanity moderation is disabled for {interaction.guild.id}. Forwarding to disabled feature override.")
                            await ui_components.disabled_feature_override(self, interaction)
                            return
                        
                        if server.profanity_moderation_profile.channel == UNSET_VALUE:
                            logging.debug(f"Admin channel not set for {interaction.guild.id}. Forwarding to admin channel button.")
                            await self.admin_channel_btn.callback(interaction, skipped = True)
                            return
                        
                        # Strike Info
                        if server.profanity_moderation_profile.channel == None: admin_channel_ui_text = "None"
                        elif server.profanity_moderation_profile.channel == UNSET_VALUE: admin_channel_ui_text = "UNSET"
                        else: 
                            admin_channel = interaction.guild.get_channel(server.profanity_moderation_profile.channel)
                            if admin_channel: admin_channel_ui_text = admin_channel.mention
                            else: admin_channel_ui_text = "#unknown"

                        if server.profanity_moderation_profile.strike_system_active: strike_system_active = "ENABLED"
                        else: strike_system_active = "DISABLED"
                        
                        description = f"""
                        InfiniBot helps you moderate profanity in your server by constantly scanning incoming messages for profane words. You can add or delete the words InfiniBot filters by clicking on "Filtered Words". In addition, you can customize the timeout duration and admin channel (where strike reports are sent).

                        InfiniBot also supports a strike system for profanity. You can manage the system by clicking "Manage Strike System".

                        **Settings**
                        - **Timeout Duration:** {humanfriendly.format_timespan(server.profanity_moderation_profile.timeout_seconds)}
                        - **Admin Channel:** {admin_channel_ui_text}
                        - **Strike System:** {strike_system_active}

                        For more information, use: {UNSET_VALUE}
                        """ # TODO add shortcut for help command
                        description = utils.standardize_str_indention(description)
                        
                        
                        embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity", description = description, color = nextcord.Color.blue())
                        
                        if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
                        else: embeds = [embed]
                        
                        try: await interaction.response.edit_message(embeds = embeds, view = self)
                        except: await interaction.edit_original_message(embeds = embeds, view = self)
                        
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)

                    class FilteredWordsButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Filtered Words", style = nextcord.ButtonStyle.gray)
                            self.outer = outer           
                            
                        class FilteredWordsView(CustomView): #Filtered Words Window -----------------------------------------------------
                            def __init__(self, outer):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                self.add_word_btn = self.AddWordButton(self)
                                self.add_item(self.add_word_btn)
                                
                                self.delete_word_btn = self.DeleteWordButton(self)
                                self.add_item(self.delete_word_btn)
                                
                                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                                self.back_btn.callback = self.back_btn_callback
                                self.add_item(self.back_btn)
                                
                            async def setup(self, interaction: Interaction):
                                server = Server(interaction.guild.id)

                                description = """
                                    InfiniBot will automatically filter messages for profane words and their variants (English only). You can add or delete words to be filtered here:
                                """
                                description = utils.standardize_str_indention(description)
                                
                                self.embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity - Filtered Words", description = description, color = nextcord.Color.blue())
                                filtered_words = server.profanity_moderation_profile.filtered_words
                                filtered_words.sort()
                                filtered_words_string = "\n".join(filtered_words)
                                if filtered_words_string == "": filtered_words_string = "You don't have any filtered words yet. Add some!"
                                else: 
                                    filtered_words_string = f"||{filtered_words_string}||"
                                
                                self.embed.add_field(name = "Filtered Words", value = filtered_words_string)
                                
                                try: await interaction.response.edit_message(embed = self.embed, view = self)
                                except: await interaction.edit_original_message(embed = self.embed, view = self)
                                                           
                            async def back_btn_callback(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                                await interaction.edit_original_message(view = self.outer)
                                                                            
                            class AddWordButton(nextcord.ui.Button):
                                def __init__(self, outer):
                                    super().__init__(label = "Add Word", style = nextcord.ButtonStyle.gray)
                                    self.outer = outer
                                    
                                class GetWordModal(CustomModal): #Add Word Modal -----------------------------------------------------
                                    def __init__(self, outer):
                                        super().__init__(title = "Add Word")
                                        self.outer = outer
                                        self.response = None

                                        self.input = nextcord.ui.TextInput(label = "Word to filter", style = nextcord.TextInputStyle.short, placeholder="Must have no suffixes. Ex: walking → walk, jumped → jump")
                                        self.add_item(self.input)
                                        
                                    async def callback(self, interaction: Interaction):
                                        server = Server(interaction.guild_id)

                                        self.response = self.input.value
                                        filtered_words = server.profanity_moderation_profile.filtered_words

                                        # Check if word exists already
                                        if self.response.lower() in [x.lower() for x in filtered_words]:
                                            self.stop()
                                            await interaction.response.send_message(embed = nextcord.Embed(title = "Error", description = f"Word `{self.response}` already exists in filtered words.", color = nextcord.Color.red()), ephemeral = True)
                                            return

                                        # Else, add the word
                                        filtered_words.append(self.response.lower())
                                        server.profanity_moderation_profile.filtered_words = filtered_words

                                        self.stop()
                                        
                                async def callback(self, interaction: Interaction):
                                    modal = self.GetWordModal(self)
                                    await interaction.response.send_modal(modal)
                                    await modal.wait()
                                    
                                    await self.outer.setup(interaction)
                                                                           
                            class DeleteWordButton(nextcord.ui.Button):
                                def __init__(self, outer):
                                    super().__init__(label = "Delete Word", style = nextcord.ButtonStyle.gray)
                                    self.outer = outer                     
                                        
                                async def callback(self, interaction: Interaction):
                                    server = Server(interaction.guild.id)
                                    filtered_words_select_options = [nextcord.SelectOption(label = x) for x in server.profanity_moderation_profile.filtered_words]
                                    
                                    embed: nextcord.Embed = copy.copy(self.outer.embed)
                                    embed.description = "Remove Filtered Words"
                                    embed.clear_fields()
                                    await ui_components.SelectView(embed, filtered_words_select_options, self.selection_callback, continue_button_label = "Delete").setup(interaction)
                                    
                                async def selection_callback(self, interaction: Interaction, selection):
                                    if selection != None:
                                        # Delete word
                                        server = Server(interaction.guild_id)
                                        filtered_words = server.profanity_moderation_profile.filtered_words
                                        filtered_words.remove(selection)
                                        server.profanity_moderation_profile.filtered_words = filtered_words

                                    await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction): #Filtered Words Button Callback ————————————————————————————————————————————————————————————
                            view = self.FilteredWordsView(self.outer)
                            await view.setup(interaction)
                                    
                    class TimeoutDurationButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Timeout Duration", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class TimeoutDurationModal(CustomModal): #Timeout Duration Modal -----------------------------------------------------
                            def __init__(self, outer, guild_id):
                                super().__init__(title = "Timeout Duration")
                                self.outer = outer
                                server = Server(guild_id)
                                
                                timeout_time_human_readable = humanfriendly.format_timespan(server.profanity_moderation_profile.timeout_seconds)
                                self.input = nextcord.ui.TextInput(label = "Timeout Duration (Format: 2 days, 5 seconds)", 
                                                                   default_value = timeout_time_human_readable, 
                                                                   placeholder = "Enter a number greater than 1", max_length=200)
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                format_error_embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The timeout time needs to be formated like this: 10 seconds, 20 minutes, 1 hour and 20 minutes, 1 day, etc...", color = nextcord.Color.red())
                                if self.input.value == "" or self.input.value == None:
                                    await interaction.response.send_message(embed = format_error_embed, ephemeral=True)
                                    return
                                
                                try:
                                    response_in_seconds = humanfriendly.parse_timespan(self.input.value)
                                except:
                                    await interaction.response.send_message(embed = format_error_embed, ephemeral=True)
                                    return
                                
                                server = Server(interaction.guild.id)
                                server.profanity_moderation_profile.timeout_seconds = response_in_seconds
                                await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.TimeoutDurationModal(self.outer, interaction.guild.id))
                            
                    class AdminChannelButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Admin Channel", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                                                
                        async def callback(self, interaction: Interaction, skipped = False):
                            self.skipped = skipped
                            server = Server(interaction.guild.id)
                                
                            select_options = []
                            for channel in interaction.guild.text_channels:
                                if channel.category != None: categoryName = channel.category.name
                                else: categoryName = None
                                if not await utils.check_text_channel_permissions(channel, False): continue
                                select_options.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.profanity_moderation_profile.channel != None and server.profanity_moderation_profile.channel == channel.id)))
                            
                            if self.skipped: title = "Dashboard - Moderation - Profanity"
                            else: title = "Dashboard - Moderation - Profanity - Admin Channel"
                            
                            description = """
                            Where should InfiniBot send moderation reports?
                            
                            **Ensure Admin-Only Access**
                            This channel lets members report incorrect strikes, so limit access to admins.
                            
                            **Can't Find Your Channel?**
                            Ensure InfiniBot has permissions to view and send messages in all your channels.
                            """
                            description = utils.standardize_str_indention(description)
                            embed = nextcord.Embed(title = title, 
                                                   description = description, 
                                                   color = nextcord.Color.blue())
                            await ui_components.SelectView(embed, select_options, self.select_view_callback, continue_button_label = "Confirm", cancel_button_label = ("Back" if self.skipped else "Cancel")).setup(interaction)
                            
                        async def select_view_callback(self, interaction: Interaction, selection):
                            if selection == None:
                                if not self.skipped:
                                    await self.outer.setup(interaction)
                                    return
                                else:
                                    await self.outer.outer.setup(interaction)
                                    return
                                
                            server = Server(interaction.guild.id)
                            server.profanity_moderation_profile.channel = selection
                            await self.outer.setup(interaction)
                                
                            #send a message to the new admin channel
                            embed = nextcord.Embed(title = "Admin Channel Set", description = f"Strikes will now be logged in this channel.\n\n**Ensure Admin-Only Access**\nThis channel lets members report incorrect strikes, so limit access to admins.", color =  nextcord.Color.green())
                            embed.set_footer(text = f"Action done by {interaction.user}")
                            discord_channel = interaction.guild.get_channel(server.profanity_moderation_profile.channel)
                            await discord_channel.send(embed = embed, view = ui_components.SupportAndInviteView())

                    class ManageStrikeSystemButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Manage Strike System", row = 1)
                            
                            self.outer = outer
                            
                        class ManageStrikeSystemView(CustomView):
                            def __init__(self, outer, guild_id:int):
                                super().__init__(timeout = None)
                                self.outer = outer

                                server = Server(guild_id)
                                if (server.profanity_moderation_profile.strike_system_active):
                                    self.manage_members_btn = self.ManageMembersButton(self)
                                    self.add_item(self.manage_members_btn)
                                    
                                    self.max_strikes_btn = self.MaxStrikesButton(self)
                                    self.add_item(self.max_strikes_btn)

                                    if server.profanity_moderation_profile.strike_expiring_active:
                                        self.strike_expire_time_btn = self.StrikeExpireTimeButton(self)
                                        self.add_item(self.strike_expire_time_btn)

                                    self.strike_expiring_enable_disable_btn = self.StrikeExpiringEnableDisableButton(self, server.profanity_moderation_profile.strike_expiring_active)
                                    self.add_item(self.strike_expiring_enable_disable_btn)

                                self.enable_disable_btn = self.EnableDisableButton(self, server.profanity_moderation_profile.strike_system_active)
                                self.add_item(self.enable_disable_btn)
                                
                                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 2)
                                self.back_btn.callback = self.back_btn_callback
                                self.add_item(self.back_btn)
                                
                            async def setup(self, interaction: Interaction):
                                self.__init__(self.outer, interaction.guild.id)
                                server = Server(interaction.guild.id)

                                # Create Description
                                if server.profanity_moderation_profile.strike_system_active: # Strike system is active
                                    strike_info = f"""
                                    ✅ ​ **STRIKE SYSTEM ENABLED**
                                    Your server is set up to grant strikes to members that use profanity. Members gain strikes for each infraction for profanity. Once a member reaches the maximum number of strikes, they are timed out for the specified timeout duration (configurable in Dashboard - Moderation - Profanity) and their strike count resets.
                                    """
                                    if server.profanity_moderation_profile.strike_expiring_active:
                                        strike_info += """
                                        ✅ ​ **STRIKE EXPIRATION ENABLED**
                                        Members' strikes will expire after a customizable number of days (assuming no new infractions).
                                        """
                                    else:
                                        strike_info += """
                                        ❌ ​ **STRIKE EXPIRATION DISABLED**
                                        Members' strikes will never expire.
                                        """

                                    strike_info = utils.standardize_str_indention(strike_info)

                                    if server.profanity_moderation_profile.strike_expiring_active == False: strike_expiration_info = ""
                                    else: strike_expiration_info = f"\n- **Strike Expire Time:** {server.profanity_moderation_profile.strike_expire_days} days"

                                    description = f"""
                                    Configure how you want InfiniBot to handle strikes.
                                    {strike_info}
                                    **Settings**
                                    - **Maximum Strikes:** {server.profanity_moderation_profile.max_strikes}{strike_expiration_info}
                                    
                                    To manage each member's strikes, click "Manage Members".
                                    """
                                else: # Strike system is disabled. We need to explain to them what it is:
                                    description = f"""
                                    ❌ ​ **STRIKE SYSTEM DISABLED**
                                    Your server is set up to punish members for using profanity on their first infraction. Members are timed out for the specified timeout duration (configurable in Dashboard - Moderation - Profanity).
                                    
                                    By enabling the strike system, members will receive a strike for each infraction for profanity, and once the maximum number of strikes is reached, they will be timed out and their strike count resets.
                                    """

                                description = utils.standardize_str_indention(description)

                                embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity - Manage Strike System", 
                                                        description = description,
                                                        color = nextcord.Color.blue())
                                    
                                await interaction.response.edit_message(embed = embed, view = self)

                            class ManageMembersButton(nextcord.ui.Button):
                                def __init__(self, outer):
                                    super().__init__(label = "Manage Members", style = nextcord.ButtonStyle.gray)
                                    self.outer = outer
                                    
                                class ManageMembersView(CustomView):
                                    def __init__(self, outer):
                                        super().__init__(timeout=None)
                                        self.outer = outer

                                        self.add_item(self.EditStrikesButton(self))
                                        self.add_item(self.ResetAllStrikesButton(self))
                                        
                                        back_btn = nextcord.ui.Button(label="Back", style=nextcord.ButtonStyle.danger, row=1)
                                        back_btn.callback = self.back_btn_callback
                                        self.add_item(back_btn)
                                    
                                    async def setup(self, interaction: Interaction):
                                        self.members = self.get_members(interaction, limit=25)
                                        
                                        members_string = [f"{item[2]} - {item[0]}" for item in self.members]
                                        self.embed = nextcord.Embed(
                                            title="Dashboard - Moderation - Profanity - Manage Members",
                                            color=nextcord.Color.blue()
                                        )
                                        self.embed.add_field(name="Strike # - Member", value="\n".join(members_string), inline=True)
                                        
                                        await interaction.response.edit_message(embed=self.embed, view=self)
                                    
                                    def get_members(self, interaction: Interaction, limit: int = None):
                                        """Fetches and sorts members by strike count."""
                                        server = Server(interaction.guild_id)
                                        data = []
                                        for member in interaction.guild.members:
                                            if member.bot: continue # ignore bots
                                            
                                            strikes = 0
                                            if member.id in server.moderation_strikes:
                                                strikes = server.moderation_strikes[member.id].strikes
                                            data.append([member.display_name, member.id, strikes])

                                        data = sorted(data, key=lambda x: (-x[2], x[0]))

                                        for i, item in enumerate(data):
                                            if limit and i >= limit:
                                                yield [f"{len(data) - limit} more. Use */get_strikes* to view specific member strikes", None, None]
                                                return
                                            # EX: [member_name, member_id, strike#]
                                            yield item
                                    
                                    async def back_btn_callback(self, interaction: Interaction):
                                        await self.outer.setup(interaction)
                                        await interaction.edit_original_message(view=self.outer)
                                    
                                    class EditStrikesButton(nextcord.ui.Button):
                                        def __init__(self, outer):
                                            super().__init__(label="Edit", style=nextcord.ButtonStyle.gray)
                                            self.outer = outer                      
                                        
                                        class EditStrikesView(CustomView):
                                            def __init__(self, outer, guild: nextcord.Guild, user_selection):
                                                super().__init__(timeout=None)
                                                self.outer = outer

                                                user_selection = json.loads(user_selection)

                                                self.member_name, self.member_id, self.member_strikes = user_selection

                                                server = Server(guild.id)
                                                
                                                strike_levels = [
                                                    nextcord.SelectOption(label=str(level), default=(level==self.member_strikes))
                                                    for level in range(server.profanity_moderation_profile.max_strikes + 1)
                                                ][::-1] # invert list
                                                
                                                self.strike_select = nextcord.ui.Select(options=strike_levels, placeholder="Choose a Strike Level")
                                                self.strike_select.callback = self.confirm_selection
                                                self.add_item(self.strike_select)
                                                
                                                cancel_btn = nextcord.ui.Button(label="Cancel", style=nextcord.ButtonStyle.danger)
                                                cancel_btn.callback = self.cancel
                                                self.add_item(cancel_btn)

                                            async def setup(self, interaction: Interaction):
                                                embed:nextcord.Embed = self.outer.embed.copy()
                                                embed.description = f"Select a strike level for {self.member_name}."
                                                embed._fields.clear() # Not technically supported.
                                                await interaction.response.edit_message(embed=embed, view=self)
                                            
                                            async def cancel(self, interaction: Interaction):
                                                await self.outer.setup(interaction)
                                            
                                            async def confirm_selection(self, interaction: Interaction):
                                                strikes = int(self.strike_select.values[0])
                                                server = Server(interaction.guild.id)
                                                
                                                if self.member_id in server.moderation_strikes:
                                                    if strikes != 0: 
                                                        server.moderation_strikes.edit(self.member_id, strikes=strikes, last_strike=datetime.datetime.now())
                                                    else:
                                                        server.moderation_strikes.delete(self.member_id)
                                                else:
                                                    if strikes != 0:
                                                        server.moderation_strikes.add(member_id=self.member_id, strikes=strikes, last_strike=datetime.datetime.now())
                                                
                                                await self.outer.setup(interaction)

                                        async def callback(self, interaction: Interaction):
                                            member_select_options = [
                                                nextcord.SelectOption(label=f"{data[2]} - {data[0]}", value=json.dumps(data)) for data in self.outer.get_members(interaction)
                                            ]
                                            embed = self.outer.embed.copy()
                                            embed.description = "Choose a Member:"
                                            await ui_components.SelectView(
                                                embed, member_select_options, self.member_select_view_callback, placeholder="Choose a Member", continue_button_label="Next", preserve_order=True
                                            ).setup(interaction)

                                        async def member_select_view_callback(self, interaction: Interaction, selection):
                                            if not selection: # User clicked "Cancel"
                                                await self.outer.setup(interaction)
                                            else:
                                                await self.EditStrikesView(self.outer, interaction.guild, selection).setup(interaction)
                                                
                                    class ResetAllStrikesButton(nextcord.ui.Button):  
                                        def __init__(self, outer):
                                            super().__init__(label="Reset All Strikes", style=nextcord.ButtonStyle.gray)
                                            self.outer = outer

                                        class ResetAllStrikesView(CustomView):
                                            def __init__(self, outer):
                                                super().__init__(timeout=None)
                                                self.outer = outer
                                                
                                                no_btn = nextcord.ui.Button(label="No", style=nextcord.ButtonStyle.danger)
                                                no_btn.callback = self.cancel
                                                self.add_item(no_btn)
                                                
                                                yes_btn = nextcord.ui.Button(label="Yes", style=nextcord.ButtonStyle.green)
                                                yes_btn.callback = self.confirm
                                                self.add_item(yes_btn)

                                            async def setup(self, interaction: Interaction):
                                                embed = nextcord.Embed(
                                                    title="Are you sure you want to reset all strikes?",
                                                    description="This action cannot be undone.",
                                                    color=nextcord.Color.blue()
                                                )
                                                await interaction.response.edit_message(embed=embed, view=self)

                                            async def cancel(self, interaction: Interaction):
                                                await self.outer.setup(interaction)

                                            async def confirm(self, interaction: Interaction):
                                                server = Server(interaction.guild.id)
                                                
                                                # Delete all strikes:
                                                for strike_info in server.moderation_strikes:
                                                    server.moderation_strikes.delete(strike_info.member_id)

                                                await self.outer.setup(interaction)
                                            
                                        async def callback(self, interaction: Interaction):
                                            await self.ResetAllStrikesView(self.outer).setup(interaction)

                                async def callback(self, interaction: Interaction):
                                    await self.ManageMembersView(self.outer).setup(interaction)

                            class MaxStrikesButton(nextcord.ui.Button):
                                def __init__(self, outer):
                                    super().__init__(label = "Maximum Strikes", style = nextcord.ButtonStyle.gray)
                                    self.outer = outer
                                    
                                class MaxStrikesModal(CustomModal): #Max Strikes Modal -----------------------------------------------------
                                    def __init__(self, outer, guild_id):
                                        super().__init__(title = "Maximum Strikes")
                                        self.outer = outer
                                        server = Server(guild_id)
                                        
                                        self.input = nextcord.ui.TextInput(label = "Maximum Strikes (Must be a number)", 
                                                                        default_value = server.profanity_moderation_profile.max_strikes, 
                                                                        placeholder = "Enter a number between 2 and 24.", max_length=2)
                                        self.add_item(self.input)
                                        
                                    async def callback(self, interaction: Interaction):
                                        server = Server(interaction.guild.id)
                                        try:
                                            if int(self.input.value) > 24: raise Exception
                                            if int(self.input.value) < 2: raise Exception
                                        except:
                                            await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Maximum Strikes setting needs to be a number between 2 and 24.", color = nextcord.Color.red()), ephemeral=True)
                                            return
                                    
                                        server.profanity_moderation_profile.max_strikes = self.input.value

                                        await self.outer.setup(interaction)
                                        
                                async def callback(self, interaction: Interaction):
                                    await interaction.response.send_modal(self.MaxStrikesModal(self.outer, interaction.guild.id))
                                            
                            class StrikeExpireTimeButton(nextcord.ui.Button):
                                def __init__(self, outer):
                                    super().__init__(label = "Strike Expire Time", style = nextcord.ButtonStyle.gray)
                                    self.outer = outer
                                    
                                class StrikeExpireTimeModal(CustomModal): #Strike Expire Time Modal -----------------------------------------------------
                                    def __init__(self, outer, guild_id):
                                        super().__init__(title = "Strike Expire Time")
                                        self.outer = outer
                                        server = Server(guild_id)
                                        
                                        self.input = nextcord.ui.TextInput(label = "Strike Expire Time (Days) (Must be a number)", 
                                                                        default_value = server.profanity_moderation_profile.strike_expire_days, 
                                                                        placeholder = "Enter a number greater than 0.", max_length=2)
                                        self.add_item(self.input)
                                        
                                    async def callback(self, interaction: Interaction):
                                        try:
                                            if int(self.input.value) <= 0: raise Exception
                                        except:
                                            await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Strike Expire Time needs to be a number greater than 0.", color = nextcord.Color.red()), ephemeral=True)
                                            return
                                    
                                        server = Server(interaction.guild.id)
                                        server.profanity_moderation_profile.strike_expire_days = int(self.input.value)
                                        
                                        await self.outer.setup(interaction)
                                        
                                async def callback(self, interaction: Interaction):
                                    await interaction.response.send_modal(self.StrikeExpireTimeModal(self.outer, interaction.guild.id))

                            class StrikeExpiringEnableDisableButton(nextcord.ui.Button):
                                def __init__(self, outer, strike_expiring_active):
                                    if strike_expiring_active:
                                        super().__init__(label = "Disable Strike Expiring", row = 1)
                                    else:
                                        super().__init__(label = "Enable Strike Expiring", row = 1)
                                    self.outer = outer
                                    
                                class EnableDisableView(CustomView):
                                    def __init__(self, outer):
                                        super().__init__(timeout = None)
                                        self.outer = outer
                                        
                                        self.back_btn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                                        self.back_btn.callback = self.back_btn_callback
                                        self.add_item(self.back_btn)
                                        
                                        self.action_btn = nextcord.ui.Button(label = "ACTION", style = nextcord.ButtonStyle.green)
                                        self.action_btn.callback = self.action_btn_callback
                                        self.add_item(self.action_btn)
                                                                              
                                    async def setup(self, interaction: Interaction, server = None):
                                        if not server: server = Server(interaction.guild.id)
                                        
                                        # Determine whether or not we are active or not.
                                        if server.profanity_moderation_profile.strike_expiring_active:
                                            # We *are* active. Give info for deactivation
                                            embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity - Manage Strike System - Strike Expiring", 
                                                                description = "Are you sure you want to disable strike expiring? You can re-enable this feature at any time.",
                                                                color = nextcord.Color.blue())
                                            self.action_btn.label = "Disable"
                                            
                                        else:
                                            # We are *not* active. Give info for activation
                                            embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity - Manage Strike System - Strike Expiring",
                                                                description = "Strike expiring is currently disabled. Do you want to enable it?",
                                                                color = nextcord.Color.blue())
                                            self.action_btn.label = "Enable"
                                            
                                        await interaction.response.edit_message(embed = embed, view = self)
                                        
                                    async def back_btn_callback(self, interaction: Interaction):
                                        await self.outer.setup(interaction)
                                        
                                    async def action_btn_callback(self, interaction: Interaction):
                                        server = Server(interaction.guild.id)
                                        
                                        server.profanity_moderation_profile.strike_expiring_active = (not server.profanity_moderation_profile.strike_expiring_active)
                                        
                                        # Return the user
                                        await self.back_btn_callback(interaction)
                                    
                                async def callback(self, interaction: Interaction):
                                    await self.EnableDisableView(self.outer).setup(interaction)
        
                            class EnableDisableButton(nextcord.ui.Button):
                                def __init__(self, outer, strike_system_active):
                                    if strike_system_active: super().__init__(label = "Disable Strike System", row = 1)
                                    else: super().__init__(label = "Enable Strike System", row = 1, style=nextcord.ButtonStyle.blurple)

                                    self.outer = outer
                                    
                                class EnableDisableView(CustomView):
                                    def __init__(self, outer):
                                        super().__init__(timeout = None)
                                        self.outer = outer
                                        
                                        self.back_btn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                                        self.back_btn.callback = self.back_btn_callback
                                        self.add_item(self.back_btn)
                                        
                                        self.action_btn = nextcord.ui.Button(label = "Disable", style = nextcord.ButtonStyle.green)
                                        self.action_btn.callback = self.action_btn_callback
                                        self.add_item(self.action_btn)
                                                                             
                                    async def setup(self, interaction: Interaction, server = None):
                                        if not server: server = Server(interaction.guild.id)
                                        
                                        # Determine whether or not we are active or not.
                                        if server.profanity_moderation_profile.strike_system_active:
                                            # We *are* active. Give info for deactivation
                                            embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity - Manage Strike System", 
                                                                description = "Are you sure you want to disable the strike system for profanity moderation? You can re-enable this feature at any time.\n\nThis will change your server's configurations such that members will be punished for using profanity on their first infraction.",
                                                                color = nextcord.Color.blue())
                                            
                                            await interaction.response.edit_message(embed = embed, view = self)
                                            
                                        else:
                                            # We are *not* active. Give info for activation
                                            # This is a unique situation, and for this specific component, we skip the validation here and just proceed to enable it
                                            
                                            await self.action_btn_callback(interaction)
                                        
                                    async def back_btn_callback(self, interaction: Interaction):
                                        server = Server(interaction.guild.id)
                                
                                        # Return either to manage strike system or profanity moderation
                                        if server.profanity_moderation_profile.strike_system_active:
                                            # Strike system is active. Put us here
                                            await self.outer.setup(interaction)
                                            
                                        else:
                                            # Strike system is disabled. Put us in the level above (profanity moderation)
                                            await self.outer.outer.setup(interaction)
                                        
                                    async def action_btn_callback(self, interaction: Interaction):
                                        server = Server(interaction.guild.id)
                                        
                                        server.profanity_moderation_profile.strike_system_active = (not server.profanity_moderation_profile.strike_system_active)
                                        
                                        # Return the user
                                        await self.back_btn_callback(interaction)
                                    
                                async def callback(self, interaction: Interaction):
                                    await self.EnableDisableView(self.outer).setup(interaction)
                        
                            async def back_btn_callback(self, interaction: Interaction, server = None):
                                await self.outer.setup(interaction)
                            
                        async def callback(self, interaction: Interaction):
                            await self.ManageStrikeSystemView(self.outer, interaction.guild.id).setup(interaction)

                    class EnableDisableButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Disable Profanity Moderation", row = 1)
                            self.outer = outer
                            
                        class EnableDisableView(CustomView):
                            def __init__(self, outer):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                self.back_btn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                                self.back_btn.callback = self.back_btn_callback
                                self.add_item(self.back_btn)
                                
                                self.action_btn = nextcord.ui.Button(label = "ACTION", style = nextcord.ButtonStyle.green)
                                self.action_btn.callback = self.action_btn_callback
                                self.add_item(self.action_btn)
                                                             
                            async def setup(self, interaction: Interaction, server = None):
                                if not server: server = Server(interaction.guild.id)
                                
                                # Determine whether or not we are active or not.
                                if server.profanity_moderation_profile.active:
                                    # We *are* active. Give info for deactivation
                                    embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity - Disable", 
                                                           description = "Are you sure you want to disable profanity moderation? You can re-enable this feature at any time.",
                                                           color = nextcord.Color.blue())
                                    self.action_btn.label = "Disable"
                                    
                                else:
                                    # We are *not* active. Give info for activation
                                    embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity",
                                                           description = "Profanity moderation is currently disabled. Do you want to enable it?",
                                                           color = nextcord.Color.blue())
                                    self.action_btn.label = "Enable"
                                    
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                            async def back_btn_callback(self, interaction: Interaction, server = None):
                                if not server: server = Server(interaction.guild.id)
                                
                                # Return either to profanity moderation or moderation.
                                if server.profanity_moderation_profile.active:
                                    # Profanity Moderation is enabled. Put us in here.
                                    await self.outer.setup(interaction)
                                    
                                else:
                                    # Profanity Moderation is disabled. Put us in the level above (moderation)
                                    await self.outer.outer.setup(interaction)
                                
                            async def action_btn_callback(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                server.profanity_moderation_profile.active = (not server.profanity_moderation_profile.active)
                                
                                # Return the user
                                await self.back_btn_callback(interaction, server = server)
                            
                        async def callback(self, interaction: Interaction):
                            await self.EnableDisableView(self.outer).setup(interaction)
                                     
                async def callback(self, interaction: Interaction):
                    view = self.ProfaneModerationView(self.outer, interaction.guild.id)
                    await view.setup(interaction)
             
            class SpamModerationButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Spam", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class SpamModerationView(CustomView):
                    def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.onboarding_modifier = onboarding_modifier
                        self.onboarding_embed = onboarding_embed
                        
                        self.timeout_duration_btn = self.TimeoutDurationButton(self)
                        self.add_item(self.timeout_duration_btn)
                        
                        self.message_threshold_btn = self.MessagesThresholdButton(self)
                        self.add_item(self.message_threshold_btn)
                        
                        self.disable_btn = self.EnableDisableButton(self)
                        self.add_item(self.disable_btn)
                        
                        self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 2) 
                        self.back_btn.callback = self.back_btn_callback
                        self.add_item(self.back_btn)
                        
                    async def setup(self, interaction: Interaction):
                        # Redirect to Activation Screen if needed
                        server = Server(interaction.guild.id)
                        if not server.spam_moderation_profile.active: 
                            await self.EnableDisableButton.EnableDisableView(self).setup(interaction)
                            return
                        
                        if self.onboarding_modifier: self.onboarding_modifier(self)
                        
                        server = Server(interaction.guild.id)
                        
                        if not utils.feature_is_active(server = server, feature = "spam_moderation"):
                            await ui_components.disabled_feature_override(self, interaction)
                            return
                        
                        timeout_time = humanfriendly.format_timespan(server.spam_moderation_profile.timeout_seconds)

                        description = f"""
                        InfiniBot helps you moderate spam in your server. Customize the options below to suit your server's requirements.
                        
                        **Settings**
                        - **Timeout Duration:** {timeout_time}
                        - **Messages Threshold:** {server.spam_moderation_profile.messages_threshold} messages
                        
                        For more information, use: {UNSET_VALUE}""" # TODO add shortcut for help command
                        
                        description = utils.standardize_str_indention(description)
                        
                        embed = nextcord.Embed(title = "Dashboard - Moderation - Spam", 
                                               description = description, 
                                               color = nextcord.Color.blue())
                        
                        if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
                        else: embeds = [embed]
                        
                        await interaction.response.edit_message(embeds = embeds, view = self)
                    
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                                                     
                    class TimeoutDurationButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Timeout Duration", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class TimeoutDurationModal(CustomModal): #Timeout Duration Modal -----------------------------------------------------
                            def __init__(self, outer, guild_id):
                                super().__init__(title = "Timeout Duration")
                                self.outer = outer
                                server = Server(guild_id)
                                timeout_time = humanfriendly.format_timespan(server.spam_moderation_profile.timeout_seconds)

                                self.input = nextcord.ui.TextInput(label = "Timeout Duration (Format: 2 days, 5 seconds)", default_value = timeout_time, placeholder = "This Field is Required", max_length=200)
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                format_error_embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The timeout time needs to be formated like this: 10 seconds, 20 minutes, 1 hour and 20 minutes, 1 day, etc...", color = nextcord.Color.red())
                                if self.input.value == "" or self.input.value == None:
                                    await interaction.response.send_message(embed = format_error_embed, ephemeral=True)
                                    return
                                
                                try:
                                    response_in_seconds = humanfriendly.parse_timespan(self.input.value)
                                except:
                                    await interaction.response.send_message(embed = format_error_embed, ephemeral=True)
                                    return
                                
                                server = Server(interaction.guild.id)
                                server.spam_moderation_profile.timeout_seconds = response_in_seconds
                                await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.TimeoutDurationModal(self.outer, interaction.guild.id))
                         
                    class MessagesThresholdButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Messages Threshold", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class MessagesThresholdModal(CustomModal): #Timeout Duration Modal -----------------------------------------------------
                            def __init__(self, outer, guild_id):
                                super().__init__(title = "Message Threshold")
                                self.outer = outer
                                server = Server(guild_id)
                                
                                self.input = nextcord.ui.TextInput(label = "Message Threshold (# of messages)", default_value = server.spam_moderation_profile.messages_threshold, placeholder = "This Field is Required", max_length=2)
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                if self.input.value == "" or self.input.value == None:
                                    return
                                
                                try:
                                    if int(self.input.value) <= 1: raise Exception
                                except:
                                    await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The messages threshold needs to be a number greater than 1.", color = nextcord.Color.red()), ephemeral=True)
                                    return
                                
                                server = Server(interaction.guild.id)
                                server.spam_moderation_profile.messages_threshold = int(self.input.value)
                                await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.MessagesThresholdModal(self.outer, interaction.guild.id))

                    class EnableDisableButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Disable Spam Moderation", row = 1)
                            self.outer = outer
                            
                        class EnableDisableView(CustomView):
                            def __init__(self, outer):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                self.back_btn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                                self.back_btn.callback = self.back_btn_callback
                                self.add_item(self.back_btn)
                                
                                self.action_btn = nextcord.ui.Button(label = "ACTION", style = nextcord.ButtonStyle.green)
                                self.action_btn.callback = self.action_btn_callback
                                self.add_item(self.action_btn)
                                                              
                            async def setup(self, interaction: Interaction, server = None):
                                if not server: server = Server(interaction.guild.id)
                                
                                # Determine whether or not we are active or not.
                                if server.spam_moderation_profile.active:
                                    # We *are* active. Give info for deactivation
                                    embed = nextcord.Embed(title = "Dashboard - Moderation - Spam - Disable", 
                                                           description = "Are you sure you want to disable spam moderation? You can re-enable this feature at any time.",
                                                           color = nextcord.Color.blue())
                                    self.action_btn.label = "Disable"
                                    
                                else:
                                    # We are *not* active. Give info for activation
                                    embed = nextcord.Embed(title = "Dashboard - Moderation - Spam",
                                                           description = "Spam moderation is currently disabled. Do you want to enable it?",
                                                           color = nextcord.Color.blue())
                                    self.action_btn.label = "Enable"
                                    
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                            async def back_btn_callback(self, interaction: Interaction, server = None):
                                if not server: server = Server(interaction.guild.id)
                                
                                # Return either to spam moderation or moderation.
                                if server.spam_moderation_profile.active:
                                    # Enabled. Put us in here.
                                    await self.outer.setup(interaction)
                                    
                                else:
                                    # Disabled. Put us in the level above
                                    await self.outer.outer.setup(interaction)
                                
                            async def action_btn_callback(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                server.spam_moderation_profile.active = (not server.spam_moderation_profile.active)
                                
                                # Return the user
                                await self.back_btn_callback(interaction, server = server)
                            
                        async def callback(self, interaction: Interaction):
                            await self.EnableDisableView(self.outer).setup(interaction)
                                                                     
                async def callback(self, interaction: Interaction):
                    view = self.SpamModerationView(self.outer)
                    await view.setup(interaction)
                                                                
        async def callback(self, interaction: Interaction):
            view = self.ModerationView(self.outer)
            await view.setup(interaction)
            
    class LoggingButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Logging", style = nextcord.ButtonStyle.gray)
            self.outer = outer
            
        class LoggingView(CustomView): #Logging Window -----------------------------------------------------
            def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
                super().__init__(timeout = None)
                self.outer = outer
                self.onboarding_modifier = onboarding_modifier
                self.onboarding_embed = onboarding_embed
                
                self.log_channel_btn = self.LogChannelButton(self)
                self.add_item(self.log_channel_btn)
                
                self.disable_btn = self.EnableDisableButton(self)
                self.add_item(self.disable_btn)
                
                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                
            async def setup(self, interaction: Interaction):
                # Redirect to Activation Screen if needed
                server = Server(interaction.guild.id)
                if not server.logging_profile.active: 
                    await self.EnableDisableButton.EnableDisableView(self).setup(interaction)
                    return
                
                if self.onboarding_modifier: self.onboarding_modifier(self)
                
                # Clean up
                if not self.onboarding_modifier:
                    for child in self.children: 
                        del child 
                        self.__init__(self.outer)
                
                # Global Kill
                if not utils.feature_is_active(server = server, feature = "logging"):
                    await ui_components.disabled_feature_override(self, interaction)
                    return
                
                if server.logging_profile.channel == UNSET_VALUE:
                    await self.log_channel_btn.callback(interaction, skipped = True)
                    return
                
                log_channel = interaction.guild.get_channel(server.logging_profile.channel)
                if log_channel: log_channel_ui_text = log_channel.mention
                else: log_channel_ui_text = "#unknown"
                
                description = f"""
                ✅ ​ InfiniBot is set up to enhance server management with comprehensive logging. View deleted and edited messages, and administrative changes.
                
                **Settings**
                - **Log Channel:** {log_channel_ui_text}
                
                For more information, use: {UNSET_VALUE}""" # TODO add shortcut for help command
                description = utils.standardize_str_indention(description)
                
                embed = nextcord.Embed(title = "Dashboard - Logging", 
                                       description = description, 
                                       color = nextcord.Color.blue())
                
                if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
                else: embeds = [embed]
                
                await interaction.response.edit_message(embeds = embeds, view = self)
                
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class LogChannelButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Log Channel", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    self.skipped = False
           
                async def callback(self, interaction: Interaction, skipped = False):
                    self.skipped = skipped
                    
                    server = Server(interaction.guild.id)
                        
                    select_options = []
                    for channel in interaction.guild.text_channels:
                        if channel.category != None: category_name = channel.category.name
                        else: category_name = None
                        if not await utils.check_text_channel_permissions(channel, False): continue
                        select_options.append(nextcord.SelectOption(label = channel.name, 
                                                                   value = channel.id, 
                                                                   description = category_name, 
                                                                   default = (server.logging_profile.channel != UNSET_VALUE and server.logging_profile.channel == channel.id)))
                    
                    description = """
                    Choose a channel for InfiniBot to send message and action logs.

                    **Ensure Admin-Only Access**
                    Message logs may contain information about conversations anywhere in the server (even restricted channels). Therefore, ensure that only admins have access to this channel.

                    **Notification Settings**
                    InfiniBot will constantly be sending log messages in this channel. It's advised to set this channel's notification settings to "Nothing".

                    **Can't Find Your Channel?**
                    Ensure InfiniBot has permissions to view and send messages in all your channels.
                    """
                    description = utils.standardize_str_indention(description)
                    
                    embed = nextcord.Embed(title = ("Dashboard - Logging" if self.skipped else "Dashboard - Logging - Log Channel"), 
                                           description = description, color = nextcord.Color.blue())
                    
                    await ui_components.SelectView(embed, 
                                     select_options, 
                                     self.select_view_callback, 
                                     continue_button_label = "Confirm", 
                                     cancel_button_label = ("Back" if self.skipped else "Cancel")).setup(interaction)
                    
                async def select_view_callback(self, interaction: Interaction, selection):
                    if selection == None:
                        if self.skipped: await self.outer.outer.setup(interaction)
                        else: await self.outer.setup(interaction)
                        return
                    
                    server = Server(interaction.guild.id)
                    server.logging_profile.channel = selection
                    await self.outer.setup(interaction)
                    
                    embed = nextcord.Embed(title = "Log Channel Set", description = f"This channel will now be used for logging.\n\n**Notification Settings**\nSet notification settings for this channel to \"Nothing\". InfiniBot will constantly be sending log messages in this channel.", color =  nextcord.Color.green())
                    embed.set_footer(text = f"Action done by {interaction.user}")
                    await interaction.guild.get_channel(server.logging_profile.channel).send(embed = embed, view = ui_components.SupportAndInviteView())
            
            class EnableDisableButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Disable Logging")
                    self.outer = outer
                    
                class EnableDisableView(CustomView):
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.back_btn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                        self.back_btn.callback = self.back_btn_callback
                        self.add_item(self.back_btn)
                        
                        self.action_btn = nextcord.ui.Button(label = "ACTION", style = nextcord.ButtonStyle.green)
                        self.action_btn.callback = self.action_btn_callback
                        self.add_item(self.action_btn)
                                           
                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        # Determine whether or not we are active or not.
                        if server.logging_profile.active:
                            # We *are* active. Give info for deactivation
                            embed = nextcord.Embed(title = "Dashboard - Logging - Disable", 
                                                    description = "Are you sure you want to disable logging? You can re-enable this feature at any time.",
                                                    color = nextcord.Color.blue())
                            self.action_btn.label = "Disable"
                            
                        else:
                            # We are *not* active. Give info for activation
                            embed = nextcord.Embed(title = "Dashboard - Logging",
                                                    description = "Logging is currently disabled. Do you want to enable it?",
                                                    color = nextcord.Color.blue())
                            self.action_btn.label = "Enable"
                            
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def back_btn_callback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        # Return either to logging or dashboard
                        if server.logging_profile.active:
                            # Enabled. Put us in here.
                            await self.outer.setup(interaction)
                            
                        else:
                            # Disabled. Put us in the level above (dashboard)
                            await self.outer.outer.setup(interaction)
                        
                    async def action_btn_callback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        server.logging_profile.active = (not server.logging_profile.active)

                        # Return the user
                        await self.back_btn_callback(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.EnableDisableView(self.outer).setup(interaction)
                        
        async def callback(self, interaction: Interaction):
            await self.LoggingView(self.outer).setup(interaction)

    class LevelingButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Leveling", style = nextcord.ButtonStyle.gray)
            self.outer = outer
            
        class LevelingView(CustomView):
            def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
                super().__init__(timeout = None)
                self.outer = outer
                self.onboarding_modifier = onboarding_modifier
                self.onboarding_embed = onboarding_embed
                
                self.manage_members_btn = self.ManageMembersButton(self)
                self.add_item(self.manage_members_btn)
                
                self.level_rewards_btn = self.LevelRewardsButton(self)
                self.add_item(self.level_rewards_btn)

                self.advanced_btn = self.AdvancedButton(self)
                self.add_item(self.advanced_btn)

                self.leveling_channel_btn = self.LevelingChannelButton(self)
                self.add_item(self.leveling_channel_btn)
                
                self.leveling_message_btn = self.LevelingMessageButton(self)
                self.add_item(self.leveling_message_btn)

                self.disable_btn = self.EnableDisableButton(self)
                self.add_item(self.disable_btn)
                
                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 3)
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                
            async def setup(self, interaction: Interaction):
                # Redirect to Activation Screen if needed
                server = Server(interaction.guild.id)
                if not server.leveling_profile.active: 
                    await self.EnableDisableButton.EnableDisableView(self).setup(interaction)
                    return
                
                if self.onboarding_modifier: self.onboarding_modifier(self)
                        
                # Clean up
                if not self.onboarding_modifier:
                    for child in self.children: 
                        del child 
                        self.__init__(self.outer)
                
                if not utils.feature_is_active(server = server, feature = "leveling"):
                    await ui_components.disabled_feature_override(self, interaction)
                    return
                
                if server.leveling_profile.channel == None: leveling_channel_ui_text = "No Notifications (disabled)"
                elif server.leveling_profile.channel == UNSET_VALUE: leveling_channel_ui_text = "System Messages Channel"
                else: 
                    leveling_channel = interaction.guild.get_channel(server.leveling_profile.channel)
                    if leveling_channel: leveling_channel_ui_text = leveling_channel.mention
                    else: leveling_channel_ui_text = "#unknown"
                
                if server.leveling_profile.channel == None: leveling_message = "N/A (Notifications are disabled)\n"
                else: leveling_message = f"\n```Title: {server.leveling_profile.level_up_embed["title"]} \
                    \nDescription: {server.leveling_profile.level_up_embed['description']}```"
                
                
                description = f"""
                ✅ ​ InfiniBot enhances server engagement through activity-based leveling. Members earn points for participating in the server. Level-up notifications are sent to members' DMs and the notification channel (message & channel configurable below). If enabled, level rewards grant roles based on member levels.

                **Settings:**
                - **Notifications Channel:** {leveling_channel_ui_text}
                - **Level-Up Message:** {leveling_message}
                For more information, use: {UNSET_VALUE}
                """ # TODO add shortcut for help command.
                description = utils.standardize_str_indention(description)
                
                embed = nextcord.Embed(title = "Dashboard - Leveling", 
                                       description = description, 
                                       color = nextcord.Color.blue())
                
                if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
                else: embeds = [embed]
                
                # Update buttons
                self.leveling_message_btn.disabled = (server.leveling_profile.channel == None)
                
                await interaction.response.edit_message(embeds = embeds, view = self)
             
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                
            class ManageMembersButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Manage Members", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class MembersView(CustomView):#Members View Window -----------------------------------------------------
                    def __init__(self, outer):
                        super().__init__(timeout=None)
                        self.outer = outer
                        
                        self.edit_level_btn = self.EditLevelButton(self)
                        self.add_item(self.edit_level_btn)
                        
                        self.delete_all_levels_btn = self.DeleteAllLevelsButton(self)
                        self.add_item(self.delete_all_levels_btn)
                        
                        self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        self.back_btn.callback = self.back_btn_callback
                        self.add_item(self.back_btn)
                        
                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        self.ranked_members = []
                        
                        for member in interaction.guild.members: 
                            if member.bot: continue
                            
                            if member.id in server.member_levels: score = server.member_levels[member.id].score
                            else: score = 0

                            self.ranked_members.append([member, score])
                        
                        
                        # Sort
                        self.ranked_members = sorted(self.ranked_members, key=lambda x: (-x[1], x[0].name))


                        self.embed = nextcord.Embed(title = "Dashboard - Leveling - Manage Members", color = nextcord.Color.blue())
                        
                        rank, lastScore = 1, 0
                        for index, member in enumerate(self.ranked_members): 
                            if index < 20:
                                level = utils.convert_score_and_level(score = member[1])
                                if member[0].nick != None: member_name = f"{member[0]} ({member[0].nick})"
                                else: member_name = f"{member[0]}"
                                
                                if member[1] < lastScore:
                                    rank += 1
                                lastScore = member[1]
                            
                                self.embed.add_field(name = f"**#{rank} {member_name}**", value = f"Level: {str(level)}, Score: {str(member[1])}", inline = False)
                            else:
                                self.embed.add_field(name = f"+ {str(len(self.ranked_members) - 20)} more", value = f"To see a specific member's level, type */level [member]*", inline = False)
                                break
                        
                        await interaction.response.edit_message(embed = self.embed, view = self)
                        
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        await interaction.edit_original_message(view = self.outer)
                        
                    class EditLevelButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Edit", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                                                        
                        class LevelModal(CustomModal):
                            def __init__(self, outer, member_id, default_level):
                                super().__init__(title = "Choose Level")
                                self.outer = outer
                                self.member_id = member_id

                                self.input = nextcord.ui.TextInput(label = "Choose a level. Must be a number.", default_value=str(default_level), placeholder="Enter a positive number", max_length=4)
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                # Check
                                if (not self.input.value.isdigit()) or int(self.input.value) < 0:
                                    embed = nextcord.Embed(title = "Invalid Level", description = "The level needs to be a positive number.", color = nextcord.Color.red())
                                    await interaction.response.send_message(embed = embed, ephemeral = True)
                                    return
                                
                                member_id = self.member_id
                                level = int(self.input.value)
                                score = utils.convert_score_and_level(level = level)
                                
                                if member_id == None: return # Bad parameters
                                
                                # Save
                                server = Server(interaction.guild.id)
                                if member_id in server.member_levels:
                                    if score == 0: # Delete member record
                                        server.member_levels.delete(member_id)
                                    else: # Edit member record
                                        member_info = server.member_levels[member_id]
                                        member_info.score = score
                                        server.member_levels[member_id] = member_info
                                else: # Add member record
                                    server.member_levels.add(member_id = member_id, score = score)
                                    

                                await self.outer.setup(interaction)
                                
                                # Get the member
                                discord_member = None
                                for _member in interaction.guild.members:
                                    if _member.id == int(member_id):
                                        discord_member = _member
                                
                                # TODO Check their level rewards
                                # await checkForLevelsAndLevelRewards(interaction.guild, discord_member, silent = True)  
                                                       
                        async def callback(self, interaction: Interaction): # Edit Levels Callback ————————————————————————————————————————————————————————————
                            member_select_options:list[nextcord.SelectOption] = []
                            for data in self.outer.ranked_members:
                                level = utils.convert_score_and_level(score = data[1])
                                member = data[0]
                                if member.nick != None: member_name = f"{member} ({member.nick})"
                                else: member_name = f"{member}"
                            
                                member_select_options.append(nextcord.SelectOption(label = f"{member_name} - Level {str(level)}, Score - {str(data[1])}", value = data[0].id))
                            
                            embed: nextcord.Embed = copy.copy(self.outer.embed)
                            embed.description = "Choose a Member"
                            await ui_components.SelectView(embed, member_select_options, self.select_view_callback, continue_button_label = "Next", placeholder = "Choose", preserve_order = True).setup(interaction)
                        
                        async def select_view_callback(self, interaction: Interaction, selection):       
                            if selection == None:
                                await self.outer.setup(interaction)
                                return
                            
                            member_id = selection
                            server = Server(interaction.guild.id)
                            if member_id in server.member_levels:
                                member_info = server.member_levels[member_id]
                                score = member_info.score
                            else: 
                                score = 0

                            level = utils.convert_score_and_level(score=score)
                                    
                            await interaction.response.send_modal(self.LevelModal(self.outer, selection, level))
                    
                    class DeleteAllLevelsButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Reset", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class DeleteAllLevelsView(CustomView):
                            def __init__(self, outer):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                self.no_btn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
                                self.no_btn.callback = self.no_btn_command
                                self.add_item(self.no_btn)
                                
                                self.yes_btn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
                                self.yes_btn.callback = self.yes_btn_command
                                self.add_item(self.yes_btn)
                                
                            async def setup(self, interaction: Interaction):
                                embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will reset all levels in the server to 0.\nThis action cannot be undone.", color = nextcord.Color.blue())
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                            async def no_btn_command(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                                
                            async def yes_btn_command(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                for member_level in server.member_levels:
                                    server.member_levels.delete(member_level.member_id)
                                await self.outer.setup(interaction)
                            
                        async def callback(self, interaction: Interaction):
                            await self.DeleteAllLevelsView(self.outer).setup(interaction)
                    
                async def callback(self, interaction: Interaction): # Strikes Callback ————————————————————————————————————————————————————————————
                    view = self.MembersView(self.outer)
                    await view.setup(interaction)
            
            class LevelRewardsButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Level Rewards", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class LevelRewardsView(CustomView): # Level Rewards Window -----------------------------------------------------
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.create_level_reward_btn = self.CreateLevelRewardButton(self)
                        self.add_item(self.create_level_reward_btn)
                        
                        self.delete_level_rewards_btn = self.DeleteLevelRewardButton(self)
                        self.add_item(self.delete_level_rewards_btn)
                        
                        self.delete_all_level_rewards_btn = self.DeleteAllLevelRewardsBtn(self)
                        self.add_item(self.delete_all_level_rewards_btn)
                        
                        self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        self.back_btn.callback = self.back_btn_callback
                        self.add_item(self.back_btn)
                        
                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        if not utils.feature_is_active(server = server, feature = "level_rewards"):
                            await ui_components.disabled_feature_override(self, interaction)
                            return
                        
                        self.embed = nextcord.Embed(title = "Dashboard - Leveling - Level Rewards", 
                                                    description = "Unlock roles as you progress through levels on the server.",
                                                    color = nextcord.Color.blue())
                        
                        level_rewards = []
                        for level_reward in server.level_rewards:
                            role_id = level_reward.role_id
                            role = interaction.guild.get_role(role_id)
                            if role == None:
                                logging.warning(f"Role {role_id} was not found in the guild {interaction.guild.id} when checking level rewards (viewing). Deleting.")
                                server.level_rewards.delete(role_id)
                                continue

                            level_rewards.append(f"{role.mention} - Level {level_reward.level}")
                                
                        if level_rewards == []: level_rewards.append("You don't have any level rewards set up. Create one!")
                        self.embed.add_field(name = "Level Rewards", value = "\n".join(level_rewards))
                        try: await interaction.response.edit_message(embed = self.embed, view = self)
                        except: await interaction.edit_original_message(embed = self.embed, view = self)
                        
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        await interaction.edit_original_message(view = self.outer)
                                                                   
                    class CreateLevelRewardButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Create", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                                               
                        async def callback(self, interaction: Interaction):
                            server = Server(interaction.guild.id)
                            all_level_reward_role_ids = [level_reward.role_id for level_reward in server.level_rewards]
                            
                            select_options = []
                            for role in interaction.guild.roles:
                                if role.name == "@everyone": continue
                                if not utils.role_assignable_by_infinibot(role): continue
                                if role.id not in all_level_reward_role_ids: 
                                    select_options.append(nextcord.SelectOption(label = role.name, description = role.id, value = role.id))
                            
                            if select_options == []:
                                await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", 
                                                                                               description = "You've run out of roles to use! To fix this, ensure that infinibot can grant the roles you would like to set as level rewards. An easy way to do this is to promote InfiniBot to a Moderator role.", 
                                                                                               color = nextcord.Color.red()), ephemeral=True)
                                return          
                                        
                            description = """
                            Select a role to be rewarded.
                            
                            **Note**
                            The selected role will be revoked from members below the specified level requirement (to be set later).
                            """
                            description = utils.standardize_str_indention(description)
                            embed = nextcord.Embed(title = "Dashboard - Leveling - Level Rewards - Add",
                                                    description = description,
                                                    color = nextcord.Color.blue())
                            await ui_components.SelectView(embed, select_options, self.select_view_callback, continue_button_label = "Next", placeholder = "Choose").setup(interaction)            
                            
                        async def select_view_callback(self, interaction: Interaction, selection):
                            if selection == None: 
                                await self.outer.setup(interaction) 
                                return
                            
                            await interaction.response.send_modal(self.LevelModal(self.outer, selection))
                                                
                        class LevelModal(CustomModal):
                            def __init__(self, outer, role_id):
                                super().__init__(title = "Choose Level")
                                self.outer = outer
                                self.role_id = role_id
                                
                                self.input = nextcord.ui.TextInput(label = "Level at which to reward this role (number)")
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                self.role_id
                                level = int(self.input.value)
                                
                                server = Server(interaction.guild.id)
                                server.level_rewards.add(role_id = self.role_id, level = level)
                                        
                                await self.outer.setup(interaction)
                                
                                discord_role = interaction.guild.get_role(int(self.role_id))
                                
                                await interaction.followup.send(embed = nextcord.Embed(title = "Level Reward Created", description = f"{discord_role.mention} is now assigned to level {str(level)}.\n\nInfiniBot will revoke this role from anyone who is below level {str(level)}.", color = nextcord.Color.green()), ephemeral=True)                  

                                # TODO Update the Level Rewards for Everyone in the Server
                                for member in interaction.guild.members:
                                    #await checkForLevelsAndLevelRewards(interaction.guild, member, silent = True)
                                    pass
                    
                    class DeleteLevelRewardButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Delete", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                                                                                
                        async def callback(self, interaction: Interaction):# Delete Level Reward Callback ————————————————————————————————————————————————————————————
                            server = Server(interaction.guild.id)
                            all_level_reward_roles = []
                            for level_reward in server.level_rewards:
                                role_id = level_reward.role_id
                                role = interaction.guild.get_role(role_id)
                                if role == None: # Should never happen because of earlier checks. But just in case...
                                    logging.warning(f"Role {role_id} was not found in the guild {interaction.guild.id} when checking level rewards (deletion). Ignoring...")
                                    continue

                                all_level_reward_roles.append(role)
                                                                
                            select_options = [nextcord.SelectOption(label = role.name, description = role.id, value = role.id) for role in all_level_reward_roles]
                            
                            if select_options == []:
                                await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", description = "You don't have any level rewards set up!", color = nextcord.Color.red()), ephemeral=True)                     
                            else:
                                embed = nextcord.Embed(title = "Dashboard - Leveling - Level Rewards - Delete",
                                                       description = "Select a level reward to delete. This does not delete the role.",
                                                       color = nextcord.Color.blue())
                                await ui_components.SelectView(embed, select_options, self.select_view_callback, continue_button_label = "Delete", placeholder = "Choose").setup(interaction)
                   
                        async def select_view_callback(self, interaction: Interaction, selection):
                            if selection == None:
                                await self.outer.setup(interaction)
                                return
                            
                            server = Server(interaction.guild.id)
                            server.level_rewards.delete(selection)
                            
                            await self.outer.setup(interaction)
                   
                    class DeleteAllLevelRewardsBtn(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Delete All Level Rewards", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class DeleteAllLevelsView(CustomView):
                            def __init__(self, outer):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                self.no_btn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
                                self.no_btn.callback = self.no_btn_command
                                self.add_item(self.no_btn)
                                
                                self.yes_btn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
                                self.yes_btn.callback = self.yes_btn_command
                                self.add_item(self.yes_btn)
                                
                            async def setup(self, interaction: Interaction):
                                embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will delete all level rewards in the server (the actual roles will not be deleted).\n\nThis action cannot be undone.", color = nextcord.Color.blue())
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                            async def no_btn_command(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                                
                            async def yes_btn_command(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                for level_reward in server.level_rewards:
                                    server.level_rewards.delete(level_reward.role_id)
                                await self.outer.setup(interaction)
                                
                            async def callback(self, interaction: Interaction):
                                await self.DeleteAllLevelsView(self.outer).setup(interaction)
                        
                        async def callback(self, interaction: Interaction):
                            await self.DeleteAllLevelsView(self.outer).setup(interaction)
                    
                async def callback(self, interaction: Interaction): #Filtered Words Button Callback ————————————————————————————————————————————————————————————
                    view = self.LevelRewardsView(self.outer)
                    await view.setup(interaction)           

            class LevelingChannelButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Notifications Channel", style = nextcord.ButtonStyle.gray, row = 1)
                    self.outer = outer
            
                async def callback(self, interaction: Interaction):
                    server = Server(interaction.guild.id)
                    select_options = [
                        nextcord.SelectOption(label = "No Notifications", value = "__DISABLED__", description = "Do not notify about level updates.", default = (server.leveling_profile.channel == None)),
                        nextcord.SelectOption(label = "System Messages Channel", value = "__SYS__", description = "Display in system messages channel", default = (server.leveling_profile.channel == UNSET_VALUE))
                        ]
                    for channel in interaction.guild.text_channels:
                        if channel.category != None: category_name = channel.category.name
                        else: category_name = None
                        if not await utils.check_text_channel_permissions(channel, False): continue
                        select_options.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = category_name, 
                                                                    default = (server.leveling_profile.channel == channel.id)))
                        
                    description = """
                    Choose a channel for InfiniBot to send level-up notifications in.

                    **What is the System Messages Channel?**
                    In Discord's server settings, you can configure a System Messages Channel. If you choose this channel, InfiniBot will send level-up notifications there.
                    
                    **Can't Find Your Channel?**
                    Ensure InfiniBot has permissions to view and send messages in all your channels.
                    """
                    description = utils.standardize_str_indention(description)

                    embed = nextcord.Embed(title = "Dashboard - Leveling - Notifications Channel", description = description, color = nextcord.Color.blue())
                    await ui_components.SelectView(embed, select_options, self.select_view_callback).setup(interaction)

                async def select_view_callback(self, interaction: Interaction, selection):
                    if selection == None:
                        await self.outer.setup(interaction)
                        return
                    
                    if selection == "__DISABLED__": new_leveling_channel_value = None
                    elif selection == "__SYS__": new_leveling_channel_value = UNSET_VALUE
                    else: new_leveling_channel_value = selection
                    
                    server = Server(interaction.guild.id)
                    server.leveling_profile.channel = new_leveling_channel_value
                    await self.outer.setup(interaction)

            class LevelingMessageButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Level-Up Message", style = nextcord.ButtonStyle.gray, row  = 1)
                    self.outer = outer
                    
                class LevelingMessageModal(CustomModal): #Leveling Message Modal -----------------------------------------------------
                    def __init__(self, guild: nextcord.Guild, outer):
                        super().__init__(timeout = None, title = "Level-Up Message")
                        self.outer = outer
                        
                        server = Server(guild.id)
                        
                        self.leveling_message_title_input = nextcord.ui.TextInput(label = "Message Title", style = nextcord.TextInputStyle.short, 
                                                                                  max_length=256, default_value = server.leveling_profile.level_up_embed["title"], 
                                                                                  placeholder = "Congratulations, @displayname!")
                        self.add_item(self.leveling_message_title_input)

                        self.leveling_message_description_input = nextcord.ui.TextInput(label = "Message Description", style = nextcord.TextInputStyle.paragraph, 
                                                                                  max_length=1024, default_value = server.leveling_profile.level_up_embed["description"], 
                                                                                  placeholder = "Congrats! You reached level [level]!")
                        self.add_item(self.leveling_message_description_input)
                        
                    async def callback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        level_up_embed = server.leveling_profile.level_up_embed
                        level_up_embed["title"] = self.leveling_message_title_input.value
                        level_up_embed["description"] = self.leveling_message_description_input.value
                        server.leveling_profile.level_up_embed = level_up_embed
                        
                        await self.outer.setup(interaction)
                                         
                async def callback(self, interaction: Interaction):
                    await interaction.response.send_modal(self.LevelingMessageModal(interaction.guild, self.outer))                                     
                    
            class AdvancedButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Advanced", style = nextcord.ButtonStyle.gray, row  = 2)
                    self.outer = outer

                class AdvancedView(CustomView):
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer

                        self.points_lost_per_day_btn = self.PointsLostPerDayButton(self)
                        self.add_item(self.points_lost_per_day_btn)
                        
                        self.level_cards_btn = self.LevelCardsButton(self)
                        self.add_item(self.level_cards_btn)

                        self.exempt_channels_btn = self.ExemptChannelsButton(self)
                        self.add_item(self.exempt_channels_btn)

                        self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 2)
                        self.back_btn.callback = self.back_btn_callback
                        self.add_item(self.back_btn)

                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)

                        allow_level_up_cards = "Yes" if server.leveling_profile.allow_leveling_cards else "No"
                        
                        description = f"""
                        **Advanced Features**
                        - **Points Lost Per Day:** Automatically removes points from all members at midnight.
                        - **Custom Level-Up Cards:** Adds personalized cards to level-up messages.
                        - **Exempt Channels:** Prevents points from being granted in exempted channels.

                        **Settings**
                        - **Points Lost Per Day:** {server.leveling_profile.points_lost_per_day}  
                        - **Level-Up Cards:** {allow_level_up_cards}
                        """
                        description = utils.standardize_str_indention(description)

                        embed = nextcord.Embed(title = "Dashboard - Leveling - Advanced", description = description, color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)

                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)

                    class PointsLostPerDayButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Points Lost Per Day", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class PointsLostPerDayModal(CustomModal): #Leveling Message Modal -----------------------------------------------------
                            def __init__(self, guild: nextcord.Guild, outer):
                                super().__init__(timeout = None, title = "Points Lost Per Day")
                                self.outer = outer
                                
                                server = Server(guild.id)
                                
                                self.pointsLostPerDayTextInput = nextcord.ui.TextInput(label = "Points (must be a number, blank = DISABLED)", style = nextcord.TextInputStyle.short, 
                                                                                    max_length=3, default_value = server.leveling_profile.points_lost_per_day, required = False)
                                self.add_item(self.pointsLostPerDayTextInput)
                                
                            async def callback(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                value:str = self.pointsLostPerDayTextInput.value
                                if not (value == None or value == "" or value == "0"):
                                    if not value.isnumeric() or int(value) < 0:
                                        await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "\"Points\" must be a positive number.", color = nextcord.Color.red()), ephemeral = True)
                                        return
                                    server.leveling_profile.points_lost_per_day = int(value)
                                
                                    await self.outer.setup(interaction)
                                    await interaction.followup.send(embed = nextcord.Embed(title = "Points Lost Per Day Set", description = f"Every day at midnight, everyone will loose {value} points.", color = nextcord.Color.green()), ephemeral = True)
                                
                                else:
                                    server.leveling_profile.points_lost_per_day = None
                                
                                    await self.outer.setup(interaction)
                                    await interaction.followup.send(embed = nextcord.Embed(title = "Points Lost Per Day Disabled", description = f"InfiniBot will not take points from anyone at midnight.", color = nextcord.Color.green()), ephemeral = True)
                                        
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.PointsLostPerDayModal(interaction.guild, self.outer))       
               
                    class LevelCardsButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Level-Up Cards", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class LevelCardsView(CustomView):
                            def __init__(self, outer, interaction: Interaction):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                server = Server(interaction.guild.id)
                                
                                if server.leveling_profile.allow_leveling_cards: button_label = "Disable"
                                else: button_label = "Enable"
                                
                                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                                self.back_btn.callback = self.back_btn_callback
                                self.add_item(self.back_btn)
                                
                                self.main_btn = nextcord.ui.Button(label = button_label, style = nextcord.ButtonStyle.green)
                                self.main_btn.callback = self.main_btn_callback
                                self.add_item(self.main_btn)
                                
                            async def setup(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                if server.leveling_profile.allow_leveling_cards: level_cards_status = "on"
                                else: level_cards_status = "off"
                        
                                embed = nextcord.Embed(title = "Dashboard - Leveling - Level-Up Cards", description = f"Currently, level-up cards are turned {level_cards_status}.\n\n**What are level-up cards?**\nWhen enabled, members can craft personalized level-up cards displayed after each level-up message.", color = nextcord.Color.blue())
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                            async def back_btn_callback(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                            
                            async def main_btn_callback(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                server.leveling_profile.allow_leveling_cards = not server.leveling_profile.allow_leveling_cards
                                
                                await self.outer.setup(interaction)
                            
                        async def callback(self, interaction: Interaction):
                            await self.LevelCardsView(self.outer, interaction).setup(interaction)
            
                    class ExemptChannelsButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Exempt Channels", style = nextcord.ButtonStyle.gray, row = 1)
                            self.outer = outer
                            
                        class ExemptChannelsView(CustomView):
                            def __init__(self, outer, interaction: Interaction):
                                super().__init__(timeout = None)
                                self.outer = outer 
                                
                                add_button = self.AddButton(self, interaction)
                                self.add_item(add_button)
                                
                                delete_button = self.DeleteButton(self, interaction)
                                self.add_item(delete_button)
                                
                                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                                self.back_btn.callback = self.back_btn_callback
                                self.add_item(self.back_btn)
                                        
                            async def setup(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                leveling_exempt_channels:list[nextcord.abc.GuildChannel] = []
                                for channel_id in server.leveling_profile.exempt_channels:
                                    channel = interaction.guild.get_channel(channel_id)
                                    if channel == None:
                                        logging.warning(f"Leveling exempt channel ({channel_id}) not found in server {interaction.guild.id}. Deleting...")
                                        leveling_exempt_channel_ids = server.leveling_profile.exempt_channels
                                        leveling_exempt_channel_ids.remove(channel_id)
                                        server.leveling_profile.exempt_channels = leveling_exempt_channels
                                        continue

                                    leveling_exempt_channels.append(channel)
                                
                                channels = "\n".join([f"• {channel.mention}" for channel in leveling_exempt_channels])
                                
                                if channels == "":
                                    channels = "You don't have any exempt channels yet. Add one!"
                                
                                
                                description = f"Select channels that will not grant points when messages are sent.\n\n**Exempt Channels**\n{channels}\n\n★ 20 Channels Maximum ★"
                                
                                embed = nextcord.Embed(title = "Dashboard - Leveling - Exempt Channels", description = description, color = nextcord.Color.blue())
                                await interaction.response.edit_message(embed = embed, view = self)
                            
                            async def reload(self, interaction: Interaction):
                                self.__init__(self.outer, interaction)
                                await self.setup(interaction)
                            
                            async def back_btn_callback(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                            
                            class AddButton(nextcord.ui.Button):
                                def __init__(self, outer, interaction: Interaction):
                                    server = Server(interaction.guild.id)
                                    disabled = (len(server.leveling_profile.exempt_channels) >= 20)
                                    super().__init__(label = "Add Channel", style = nextcord.ButtonStyle.gray, disabled = disabled)
                                    self.outer = outer
                                                            
                                async def callback(self, interaction: Interaction):
                                    options = []
                                    server = Server(interaction.guild.id)
                                    for channel in interaction.guild.channels:
                                        if channel.id in server.leveling_profile.exempt_channels: continue # Ignore if already exempt
                                        channel_category = (channel.category.name if channel.category else None)
                                        if type(channel) == nextcord.TextChannel: label = f"#{channel.name}"
                                        elif type(channel) == nextcord.VoiceChannel: label = f"🔉{channel.name}"
                                        else: continue # Ignore if not a text or voice channel
                                        options.append(nextcord.SelectOption(label = label, value = channel.id, description = channel_category))
                                    
                                    if len(options) == 0:
                                        await interaction.response.send_message(embed = nextcord.Embed(title = "No More Channels", description = "You've ran out of channels to exempt. Create more channels, or give InfiniBot higher permissions to see more channels!", color = nextcord.Color.red()), ephemeral = True)
                                        return
                                    
                                    description = """
                                    Choose a channel to make it an exempt channel. InfiniBot won't grant points for messages sent in this channel.

                                    **Can't Find Your Channel?**
                                    Ensure InfiniBot has permissions to view all your channels.
                                    """
                                    description = utils.standardize_str_indention(description)
                                    embed = nextcord.Embed(title = "Dashboard - Leveling - Exempt Channels - Add", description = description, color = nextcord.Color.blue())
                                    await ui_components.SelectView(embed, options, self.select_callback, placeholder = "Choose a Channel", continue_button_label = "Add Channel").setup(interaction)
                    
                                async def select_callback(self, interaction: Interaction, choice):
                                    if choice != None:
                                        server = Server(interaction.guild.id)
                                        leveling_exempt_channels:list = server.leveling_profile.exempt_channels
                                        leveling_exempt_channels.append(int(choice))
                                        server.leveling_profile.exempt_channels = leveling_exempt_channels
                                        
                                    await self.outer.reload(interaction)

                            class DeleteButton(nextcord.ui.Button):
                                def __init__(self, outer, interaction: Interaction):
                                    server = Server(interaction.guild.id)
                                    disabled = (len(server.leveling_profile.exempt_channels) == 0)
                                    super().__init__(label = "Delete Channel", style = nextcord.ButtonStyle.gray, disabled = disabled)
                                    self.outer = outer
                                                            
                                async def callback(self, interaction: Interaction):
                                    options = []
                                    server = Server(interaction.guild.id)
                                    for channel_id in server.leveling_profile.exempt_channels:
                                        channel = interaction.guild.get_channel(channel_id)
                                        if channel == None: # Should never happen due to previous checks.
                                            logging.warning(f"Leveling exempt channel ({channel_id}) not found in server {interaction.guild.id}. Ignoring...")
                                            continue

                                        channel_category = (channel.category.name if channel.category else None)
                                        if type(channel) == nextcord.TextChannel: label = f"#{channel.name}"
                                        elif type(channel) == nextcord.VoiceChannel: label = f"🔉{channel.name}"
                                        else:
                                            logging.warning(f"Leveling exempt channel ({channel_id}) not a text or voice channel in server {interaction.guild.id}. Ignoring...")
                                            continue

                                        options.append(nextcord.SelectOption(label = label, value = channel.id, description = channel_category))
                                    
                                    embed = nextcord.Embed(title = "Dashboard - Leveling - Exempt Channels - Delete", description = "Choose a Channel to Remove from Exempt Channels", color = nextcord.Color.blue())
                                    await ui_components.SelectView(embed, options, self.select_callback, placeholder = "Choose a Channel", continue_button_label = "Delete Channel").setup(interaction)
                    
                                async def select_callback(self, interaction: Interaction, choice):
                                    if choice != None:
                                        server = Server(interaction.guild.id)
                                        for channel_id in server.leveling_profile.exempt_channels:
                                            if channel_id == int(choice):
                                                leveling_exempt_channels = server.leveling_profile.exempt_channels
                                                leveling_exempt_channels.remove(int(choice))
                                                server.leveling_profile.exempt_channels = leveling_exempt_channels
                                                break
                                        
                                    await self.outer.reload(interaction)
                            
                        async def callback(self, interaction: Interaction):
                            await self.ExemptChannelsView(self.outer, interaction).setup(interaction)
    
                async def callback(self, interaction: Interaction):
                    await self.AdvancedView(self.outer).setup(interaction)
                                                             
            class EnableDisableButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Disable Leveling", row = 2)
                    self.outer = outer
                    
                class EnableDisableView(CustomView):
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.back_btn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                        self.back_btn.callback = self.back_btn_callback
                        self.add_item(self.back_btn)
                        
                        self.action_btn = nextcord.ui.Button(label = "ACTION", style = nextcord.ButtonStyle.green)
                        self.action_btn.callback = self.action_btn_callback
                        self.add_item(self.action_btn)
                        
                        
                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        # Determine whether or not we are active or not.
                        if server.leveling_profile.active:
                            # We *are* active. Give info for deactivation
                            embed = nextcord.Embed(title = "Dashboard - Leveling - Disable", 
                                                    description = "Are you sure you want to disable leveling? You can re-enable this feature at any time.",
                                                    color = nextcord.Color.blue())
                            self.action_btn.label = "Disable"
                            
                        else:
                            # We are *not* active. Give info for activation
                            embed = nextcord.Embed(title = "Dashboard - Leveling",
                                                    description = "Leveling is currently disabled. Do you want to enable it?\n\nLeveling gives your members a rank based on their activity in the server.",
                                                    color = nextcord.Color.blue())
                            self.action_btn.label = "Enable"
                            
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def back_btn_callback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        # Return either to leveling or dashboard
                        if server.leveling_profile.active:
                            # Enabled. Put us in here.
                            await self.outer.setup(interaction)
                            
                        else:
                            # Disabled. Put us in the level above (dashboard)
                            await self.outer.outer.setup(interaction)
                        
                    async def action_btn_callback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        server.leveling_profile.active = (not server.leveling_profile.active)
                        
                        # Return the user
                        await self.back_btn_callback(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.EnableDisableView(self.outer).setup(interaction)
                               
        async def callback(self, interaction: Interaction):
            await self.LevelingView(self.outer).setup(interaction)

    class JoinLeaveMessagesButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Join / Leave Messages", style = nextcord.ButtonStyle.gray)
            self.outer = outer
            
        class JoinLeaveMessagesView(CustomView):
            def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
                super().__init__(timeout = None)
                self.outer = outer
                self.onboarding_modifier = onboarding_modifier
                self.onboarding_embed = onboarding_embed
                
                self.join_message_btn = self.JoinMessagesButton(self)
                self.add_item(self.join_message_btn)

                self.leave_messages_btn = self.LeaveMessagesButton(self)
                self.add_item(self.leave_messages_btn)
                
                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 3)
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                
            async def setup(self, interaction: Interaction):
                if self.onboarding_modifier: self.onboarding_modifier(self)
                
                # Clean up
                if not self.onboarding_modifier:
                    for child in self.children: 
                        del child 
                        self.__init__(self.outer)
                
                # Global Kill
                if not utils.feature_is_active(server_id = interaction.guild.id, feature = "join_leave_messages"): # server_id won't be used here, but it's required as an input
                    await ui_components.disabled_feature_override(self, interaction)
                    return
                
                description = """
                InfiniBot can send messages to members when they join or leave the server.
                
                To enable / configure this feature, use the **Join Messages** or **Leave Messages** buttons below.
                """
                description = utils.standardize_str_indention(description)

                embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages", description = description, color = nextcord.Color.blue())
                await interaction.response.edit_message(embed = embed, view = self)
            
            class JoinMessagesButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Join Messages", style = nextcord.ButtonStyle.gray)
                    self.outer = outer

                class JoinMessagesView(CustomView): #Join Messages Window --------------------------------------------
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.join_message_btn = self.JoinMessageButton(self)
                        self.add_item(self.join_message_btn)
                        
                        self.join_channel_btn = self.JoinChannelButton(self)
                        self.add_item(self.join_channel_btn)

                        self.cards_btn = self.CardsBtn(self)
                        self.add_item(self.cards_btn)

                        self.disable_btn = self.EnableDisableButton(self)
                        self.add_item(self.disable_btn)
                        
                        self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 2)
                        self.back_btn.callback = self.back_btn_callback
                        self.add_item(self.back_btn)

                    async def setup(self, interaction: Interaction):
                        # Redirect to Activation Screen if needed
                        server = Server(interaction.guild.id)
                        if not server.join_message_profile.active: 
                            await self.EnableDisableButton.EnableDisableView(self).setup(interaction)
                            return
                
                        server = Server(interaction.guild.id)
                        
                        # Global Kill
                        if not utils.feature_is_active(server = server, feature = "join_messages"):
                            await ui_components.disabled_feature_override(self, interaction)
                            return
                        
                        if server.join_message_profile.channel == UNSET_VALUE: channel_ui_text = "System Messages Channel"
                        else: 
                            channel = interaction.guild.get_channel(server.join_message_profile.channel)
                            if channel: channel_ui_text = channel.mention
                            else: channel_ui_text = "#unknown"

                        if server.join_message_profile.allow_join_cards: cards_ui_text = "Enabled"
                        else: cards_ui_text = "Disabled"

                        description = f"""
                        InfiniBot can welcome members of your server by sending a message when they join. Configure the message, where it's sent, and its contents.

                        **Settings**
                        - **Channel**: {channel_ui_text}
                        - **Cards**: {cards_ui_text}
                        - **Message**: 
                        ```
                        Title: {server.join_message_profile.embed["title"]}
                        Description: {server.join_message_profile.embed["description"]}
                        ```
                        For more information, use: {UNSET_VALUE}
                        """ # TODO add shortcut for help command.
                        description = utils.standardize_str_indention(description)

                        embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Join Messages", description = description, color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)

                    class JoinMessageButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Join Message", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class JoinMessageModal(CustomModal): #Join Message Modal -----------------------------------------------------
                            def __init__(self, guild: nextcord.Guild, outer):
                                super().__init__(timeout = None, title = "Join Message")
                                self.outer = outer
                                
                                server = Server(guild.id)
                                
                                self.join_message_title_input = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, max_length=256, 
                                                                                      default_value = server.join_message_profile.embed["title"], placeholder = "@displayname just joined the server!")
                                self.add_item(self.join_message_title_input)

                                self.join_message_description_input = nextcord.ui.TextInput(label = "Description", style = nextcord.TextInputStyle.paragraph, max_length=1024, 
                                                                                      default_value = server.join_message_profile.embed["description"], placeholder = "Welcome to the server, @member!")
                                self.add_item(self.join_message_description_input)
                                
                            async def callback(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                embed = server.join_message_profile.embed
                                embed["title"] = self.join_message_title_input.value
                                embed["description"] = self.join_message_description_input.value
                                server.join_message_profile.embed = embed

                                await self.outer.setup(interaction)                     
                                
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.JoinMessageModal(interaction.guild, self.outer))                
                                        
                    class JoinChannelButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Join Message Channel", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                                            
                        async def callback(self, interaction: Interaction):
                            server = Server(interaction.guild.id)
                                
                            select_options = [nextcord.SelectOption(label = "System Messages Channel", value = "__SYS__", description = "Display in system messages channel", default = (server.join_message_profile.channel == UNSET_VALUE))]
                            for channel in interaction.guild.text_channels:
                                if channel.category != None: category_name = channel.category.name
                                else: category_name = None
                                if not await utils.check_text_channel_permissions(channel, False): continue
                                select_options.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = category_name, 
                                                                            default = (server.join_message_profile.channel == channel.id)))
                            
                            description = """
                            Choose a channel for InfiniBot to send join messages in.

                            **What is the System Messages Channel?**
                            In Discord's server settings, you can configure a System Messages Channel. If you choose this channel, InfiniBot will send join messages there.

                            **Can't Find Your Channel?**
                            Ensure InfiniBot has permissions to view and send messages in all your channels.
                            """
                            description = utils.standardize_str_indention(description)

                            embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Join Messages - Channel", description = description, color = nextcord.Color.blue())
                            await ui_components.SelectView(embed, select_options, self.select_view_return, continue_button_label = "Confirm").setup(interaction)
                            
                        async def select_view_return(self, interaction: Interaction, selection):
                            if selection == None:
                                await self.outer.setup(interaction)
                                return
                            
                            if selection == "__SYS__": value = UNSET_VALUE
                            else: value = selection
                            
                            server = Server(interaction.guild.id)
                            server.join_message_profile.channel = value
                            await self.outer.setup(interaction)

                    class CardsBtn(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Cards", style = nextcord.ButtonStyle.gray, row = 1)
                            self.outer = outer
                            
                        class CardsView(CustomView): # Join Cards
                            def __init__(self, outer, interaction: Interaction):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                server = Server(interaction.guild.id)
                                
                                if server.join_message_profile.allow_join_cards: button_label = "Disable"
                                else: button_label = "Enable"
                                
                                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                                self.back_btn.callback = self.back_btn_callback
                                self.add_item(self.back_btn)
                                
                                self.main_btn = nextcord.ui.Button(label = button_label, style = nextcord.ButtonStyle.green)
                                self.main_btn.callback = self.main_btn_callback
                                self.add_item(self.main_btn)
                                
                            async def setup(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                if server.join_message_profile.allow_join_cards: join_card_status = "on"
                                else: join_card_status = "off"

                                description = f"""
                                Currently, cards are turned {join_card_status}.
                                
                                **What are cards?**
                                If enabled, members can personalize a card for them to use when they join the server.
                                Go to `/profile` to customize your join card.
                                """
                                description = utils.standardize_str_indention(description)
                                embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Join Messages - Cards", description = description, color = nextcord.Color.blue())
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                            async def back_btn_callback(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                            
                            async def main_btn_callback(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                server.join_message_profile.allow_join_cards = not server.join_message_profile.allow_join_cards
                                
                                await self.outer.setup(interaction)
                            
                        async def callback(self, interaction: Interaction):
                            await self.CardsView(self.outer, interaction).setup(interaction)

                    class EnableDisableButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Disable Join Messages", row = 1)
                            self.outer = outer
                            
                        class EnableDisableView(CustomView):
                            def __init__(self, outer):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                self.back_btn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                                self.back_btn.callback = self.back_btn_callback
                                self.add_item(self.back_btn)
                                
                                self.action_btn = nextcord.ui.Button(label = "ACTION", style = nextcord.ButtonStyle.green)
                                self.action_btn.callback = self.action_btn_callback
                                self.add_item(self.action_btn)
                                                
                            async def setup(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                # Determine whether or not we are active or not.
                                if server.join_message_profile.active:
                                    # We *are* active. Give info for deactivation
                                    embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Join Messages", 
                                                            description = "Are you sure you want to disable join messages? You can re-enable this feature at any time.",
                                                            color = nextcord.Color.blue())
                                    self.action_btn.label = "Disable"
                                    
                                else:
                                    # We are *not* active. Give info for activation
                                    embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Join Messages",
                                                            description = "Join messages are currently disabled. Do you want to enable them?",
                                                            color = nextcord.Color.blue())
                                    self.action_btn.label = "Enable"
                                    
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                            async def back_btn_callback(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                # Return either to join / leave messages or join messages
                                if server.join_message_profile.active:
                                    # Enabled. Put us in here.
                                    await self.outer.setup(interaction)
                                    
                                else:
                                    # Disabled. Put us in the level above (join / leave messages)
                                    await self.outer.outer.setup(interaction)
                                
                            async def action_btn_callback(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                server.join_message_profile.active = (not server.join_message_profile.active)

                                # Return the user
                                await self.back_btn_callback(interaction)
                            
                        async def callback(self, interaction: Interaction):
                            await self.EnableDisableView(self.outer).setup(interaction)
                
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)

                async def callback(self, interaction: Interaction):
                    await self.JoinMessagesView(self.outer).setup(interaction)

            class LeaveMessagesButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Leave Messages", style = nextcord.ButtonStyle.gray)
                    self.outer = outer

                class LeaveMessagesView(CustomView): #Leave Messages Window --------------------------------------------
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.leave_message_btn = self.LeaveMessagesButton(self)
                        self.add_item(self.leave_message_btn)
                        
                        self.leave_channel_btn = self.LeaveChannelButton(self)
                        self.add_item(self.leave_channel_btn)

                        self.disable_btn = self.EnableDisableButton(self)
                        self.add_item(self.disable_btn)
                        
                        self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 2)
                        self.back_btn.callback = self.back_btn_callback
                        self.add_item(self.back_btn)

                    async def setup(self, interaction: Interaction):
                        # Redirect to Activation Screen if needed
                        server = Server(interaction.guild.id)
                        if not server.leave_message_profile.active: 
                            await self.EnableDisableButton.EnableDisableView(self).setup(interaction)
                            return
                
                        server = Server(interaction.guild.id)
                        
                        # Global Kill
                        if not utils.feature_is_active(server = server, feature = "leave_messages"):
                            await ui_components.disabled_feature_override(self, interaction)
                            return
                        
                        if server.leave_message_profile.channel == UNSET_VALUE: channel_ui_text = "System Messages Channel"
                        else: 
                            channel = interaction.guild.get_channel(server.leave_message_profile.channel)
                            if channel: channel_ui_text = channel.mention
                            else: channel_ui_text = "#unknown"

                        description = f"""
                        InfiniBot can say farewell to members of your server by sending a message when they leave. Configure the message, where it's sent, and its contents.

                        **Settings**
                        - **Channel**: {channel_ui_text}
                        - **Message**: 
                        ```
                        Title: {server.leave_message_profile.embed["title"]}
                        Description: {server.leave_message_profile.embed["description"]}
                        ```
                        For more information, use: {UNSET_VALUE}
                        """ # TODO add shortcut for help command.
                        description = utils.standardize_str_indention(description)

                        embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Join Messages", description = description, color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)

                    class LeaveMessagesButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Leave Message", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class LeaveMessagesModal(CustomModal): #Leave Message Modal -----------------------------------------------------
                            def __init__(self, guild: nextcord.Guild, outer):
                                super().__init__(timeout = None, title = "Leave Message")
                                self.outer = outer
                                
                                server = Server(guild.id)
                                
                                self.leave_message_title_input = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, max_length=256, 
                                                                                      default_value = server.leave_message_profile.embed["title"], placeholder = "@displayname just left the server.")
                                self.add_item(self.leave_message_title_input)

                                self.leave_message_description_input = nextcord.ui.TextInput(label = "Description", style = nextcord.TextInputStyle.paragraph, max_length=1024, 
                                                                                      default_value = server.leave_message_profile.embed["description"], placeholder = "@member left.")
                                self.add_item(self.leave_message_description_input)
                                
                            async def callback(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                embed = server.leave_message_profile.embed
                                embed["title"] = self.leave_message_title_input.value
                                embed["description"] = self.leave_message_description_input.value
                                server.leave_message_profile.embed = embed

                                await self.outer.setup(interaction)                     
                                
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.LeaveMessagesModal(interaction.guild, self.outer))                
                                        
                    class LeaveChannelButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Leave Message Channel", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                                            
                        async def callback(self, interaction: Interaction):
                            server = Server(interaction.guild.id)
                                
                            select_options = [nextcord.SelectOption(label = "System Messages Channel", value = "__SYS__", description = "Display in system messages channel", default = (server.leave_message_profile.channel == UNSET_VALUE))]
                            for channel in interaction.guild.text_channels:
                                if channel.category != None: category_name = channel.category.name
                                else: category_name = None
                                if not await utils.check_text_channel_permissions(channel, False): continue
                                select_options.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = category_name, 
                                                                            default = (server.leave_message_profile.channel == channel.id)))
                            
                            description = """
                            Choose a channel for InfiniBot to send leave messages in.

                            **What is the System Messages Channel?**
                            In Discord's server settings, you can configure a System Messages Channel. If you choose this channel, InfiniBot will send leave messages there.

                            **Can't Find Your Channel?**
                            Ensure InfiniBot has permissions to view and send messages in all your channels.
                            """
                            description = utils.standardize_str_indention(description)

                            embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Leave Messages - Channel", description = description, color = nextcord.Color.blue())
                            await ui_components.SelectView(embed, select_options, self.select_view_return, continue_button_label = "Confirm").setup(interaction)
                            
                        async def select_view_return(self, interaction: Interaction, selection):
                            if selection == None:
                                await self.outer.setup(interaction)
                                return
                            
                            if selection == "__SYS__": value = UNSET_VALUE
                            else: value = selection
                            
                            server = Server(interaction.guild.id)
                            server.leave_message_profile.channel = value
                            await self.outer.setup(interaction)

                    class EnableDisableButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Disable Leave Messages", row = 1)
                            self.outer = outer
                            
                        class EnableDisableView(CustomView):
                            def __init__(self, outer):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                self.back_btn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                                self.back_btn.callback = self.back_btn_callback
                                self.add_item(self.back_btn)
                                
                                self.action_btn = nextcord.ui.Button(label = "ACTION", style = nextcord.ButtonStyle.green)
                                self.action_btn.callback = self.action_btn_callback
                                self.add_item(self.action_btn)
                                                
                            async def setup(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                # Determine whether or not we are active or not.
                                if server.leave_message_profile.active:
                                    # We *are* active. Give info for deactivation
                                    embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Leave Messages", 
                                                            description = "Are you sure you want to disable leave messages? You can re-enable this feature at any time.",
                                                            color = nextcord.Color.blue())
                                    self.action_btn.label = "Disable"
                                    
                                else:
                                    # We are *not* active. Give info for activation
                                    embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Leave Messages",
                                                            description = "Leave messages are currently disabled. Do you want to enable them?",
                                                            color = nextcord.Color.blue())
                                    self.action_btn.label = "Enable"
                                    
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                            async def back_btn_callback(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                # Return either to join / leave messages or leave messages
                                if server.leave_message_profile.active:
                                    # Enabled. Put us in here.
                                    await self.outer.setup(interaction)
                                    
                                else:
                                    # Disabled. Put us in the level above (join / leave messages)
                                    await self.outer.outer.setup(interaction)
                                
                            async def action_btn_callback(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                server.leave_message_profile.active = (not server.leave_message_profile.active)

                                # Return the user
                                await self.back_btn_callback(interaction)
                            
                        async def callback(self, interaction: Interaction):
                            await self.EnableDisableView(self.outer).setup(interaction)
                
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)

                async def callback(self, interaction: Interaction):
                    await self.LeaveMessagesView(self.outer).setup(interaction)
  
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                                      
        async def callback(self, interaction: Interaction):
            await self.JoinLeaveMessagesView(self.outer).setup(interaction)
    
    class BirthdaysButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Birthdays", style = nextcord.ButtonStyle.gray, row = 1)
            self.outer = outer 
            
        class BirthdaysView(CustomView): #Birthdays Window -----------------------------------------------------
            def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
                super().__init__(timeout = None)
                self.outer = outer
                self.onboarding_modifier = onboarding_modifier
                self.onboarding_embed = onboarding_embed
                
                self.configure_birthdays_btn = self.ConfigureBirthdaysButton(self)
                self.add_item(self.configure_birthdays_btn)
                
                self.birthdays_channel_btn = self.BirthdaysChannelButton(self)
                self.add_item(self.birthdays_channel_btn)

                self.update_message_btn = self.UpdateMessageTimeButton(self)
                self.add_item(self.update_message_btn)

                self.edit_birthday_message_btn = self.EditBirthdayMessageButton(self)
                self.add_item(self.edit_birthday_message_btn)
                
                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 2) 
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                             
            async def setup(self, interaction: Interaction):
                if self.onboarding_modifier: self.onboarding_modifier(self)
                        
                # Clean up
                if not self.onboarding_modifier:
                    for child in self.children: 
                        del child 
                        self.__init__(self.outer)
                
                if not utils.feature_is_active(server_id = interaction.guild.id, feature = "birthdays"): # server_id won't be used here, but it's required as an input
                    await ui_components.disabled_feature_override(self, interaction)
                    return
                
                server = Server(interaction.guild.id)
                
                if server.birthdays_profile.channel == UNSET_VALUE: birthday_channel_ui_text = "System Messages Channel"
                else: 
                    birthday_channel = interaction.guild.get_channel(server.birthdays_profile.channel)
                    if birthday_channel: birthday_channel_ui_text = birthday_channel.mention
                    else: birthday_channel_ui_text = "#unknown"

                if server.birthdays_profile.runtime == UNSET_VALUE: server.birthdays_profile.runtime = get_configs()["birthday_message_runtime_default_utc"]
                try:
                    hour, minute = server.birthdays_profile.runtime.split(":")
                    epoch_time = datetime.datetime(2000, 1, 1, int(hour), int(minute), 0, tzinfo = datetime.timezone.utc).timestamp()
                    epoch_time = round(epoch_time)
                    message_time_ui_text = f"<t:{epoch_time}:t>"
                except Exception as e:
                    logging.error(e)
                    message_time_ui_text = "Unknown"

                description = f"""
                Celebrate birthdays with InfiniBot's personalized messages.
                
                **Settings**
                - **Notifications Channel:** {birthday_channel_ui_text}
                - **Message Time:** {message_time_ui_text}
                - **Message**: 
                ```
                Title: {server.birthdays_profile.embed["title"]}
                Description: {server.birthdays_profile.embed["description"]}
                ```
                **Configure Birthdays**
                To set up birthdays for members, use the "Configure Birthdays" button below.

                **Message Time**
                The time shown above includes a date due to Discord's timestamp behavior, but the date can be ignored. Birthday messages are sent at the specified time on the day of the birthday. Unfortunately, Discord timestamps always display an associated date, even when it's irrelevant.
                
                For more information, use: {UNSET_VALUE}
                """ # TODO add shortcut for help command
                description = utils.standardize_str_indention(description)
                
                embed = nextcord.Embed(title = "Dashboard - Birthdays", description = description, color = nextcord.Color.blue())
                
                if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
                else: embeds = [embed]
                
                await interaction.response.edit_message(embeds = embeds, view = self)

            class ConfigureBirthdaysButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Configure Birthdays", style = nextcord.ButtonStyle.gray)
                    self.outer = outer

                class ConfigureBirthdaysView(CustomView):
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer

                        self.add_birthday_btn = self.AddBirthdayButton(self)
                        self.add_item(self.add_birthday_btn)
                        
                        self.edit_birthday_btn = self.EditBirthdayButton(self)
                        self.add_item(self.edit_birthday_btn)
                        
                        self.delete_birthday_btn = self.DeleteBirthdayButton(self)
                        self.add_item(self.delete_birthday_btn)
                        
                        self.delete_all_birthdays_btn = self.DeleteAllBirthdaysButton(self)
                        self.add_item(self.delete_all_birthdays_btn)

                        self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1) 
                        self.back_btn.callback = self.back_btn_callback
                        self.add_item(self.back_btn)

                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                
                        birthdays = []
                        for bday in server.birthdays:
                            try:
                                member_id = bday.member_id
                                member = interaction.guild.get_member(member_id)
                                
                                if member == None: # Member left. Delete their birthday
                                    server.birthdays.delete(member_id)
                                    continue
                                
                                member_mention = member.mention if member != None else "#unknown"

                                if bday.real_name != None: birthdays.append(f"{member_mention} ({str(bday.real_name)}) - {bday.birth_date}")
                                else: birthdays.append(f"{member_mention} - {bday.birth_date}")
                                    
                            except Exception as err:
                                logging.error(f"Birthdays View Error: {err}")
                                
                        if len(birthdays) == 0: birthdays_str = "You don't have any birthdays. Create one!"
                        else: birthdays_str = "\n".join(birthdays)

                        description = f"""
                        Celebrate birthdays with InfiniBot's personalized messages.

                        **Birthdays**
                        {birthdays_str}
                        """ # TODO add shortcut for help command
                        description = utils.standardize_str_indention(description)
                        
                        self.embed = nextcord.Embed(title = "Dashboard - Birthdays", description = description, color = nextcord.Color.blue())
                        
                        try: await interaction.response.edit_message(embed = self.embed, view = self)
                        except: await interaction.edit_original_message(embed = self.embed, view = self)
                
                    class AddBirthdayButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Add", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        async def callback(self, interaction: Interaction):# Edit Strikes Callback ————————————————————————————————————————————————————————————
                            server = Server(interaction.guild.id)
                                
                            member_select_options = []
                            for member in interaction.guild.members:
                                if member.bot: continue
                                if member.id in server.birthdays: continue
                                member_select_options.append(nextcord.SelectOption(label = f"{member}", description = member.nick, value = member.id))
                            
                            
                            if member_select_options == []: 
                                await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Members", description = "Every member in your server already has a birthday! Go invite someone!", color = nextcord.Color.red()), ephemeral = True)
                                return
                            
                            await ui_components.SelectView(self.outer.embed, member_select_options, self.select_view_return, placeholder = "Choose a Member", continue_button_label = "Next").setup(interaction)
                            
                        async def select_view_return(self, interaction: Interaction, selection):
                            if selection == None: # User clicked "Cancel"
                                await self.outer.setup(interaction)
                                return
                            
                            await interaction.response.send_modal(self.InfoModal(self.outer, selection))          
                                            
                        class InfoModal(CustomModal):            
                            def __init__(self, outer, member_id):
                                super().__init__(title = "Add Birthday", timeout = None)
                                self.outer = outer
                                self.member_id = member_id
                                
                                self.date_input = nextcord.ui.TextInput(label = "Date (MM/DD/YYYY)", style = nextcord.TextInputStyle.short, max_length = 10, placeholder = "MM/DD/YYYY")
                                self.add_item(self.date_input)
                                
                                self.real_name_input = nextcord.ui.TextInput(label = "Real Name (Optional)", style = nextcord.TextInputStyle.short, max_length=50, required = False)
                                self.add_item(self.real_name_input)
                                
                            async def callback(self, interaction: Interaction):
                                try:
                                    datetime.datetime.strptime(self.date_input.value, f"%m/%d/%Y")
                                except:
                                    await interaction.response.send_message(embed = nextcord.Embed(title = "Invalid Format", description = "You formatted the date wrong. Try formating it like this: MM/DD/YYYY", color =  nextcord.Color.red()), ephemeral=True)
                                    return
                                
                                server = Server(interaction.guild.id)
                                real_name = self.real_name_input.value if self.real_name_input.value != "" else None
                                server.birthdays.add(member_id = self.member_id, birth_date = self.date_input.value, real_name = real_name)

                                await self.outer.setup(interaction)
                
                    class EditBirthdayButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Edit", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                                                            
                        async def callback(self, interaction: Interaction):
                            server = Server(interaction.guild.id)
                                
                            member_select_options = []
                            for member in interaction.guild.members:
                                if member.id in server.birthdays:
                                    member_select_options.append(nextcord.SelectOption(label = f"{member}", description = member.nick, value = member.id))
                            
                            
                            if member_select_options == []: 
                                await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Members", description = "No members in your server have birthdays. Add some!", color = nextcord.Color.red()), ephemeral = True)
                                return
                            
                            await ui_components.SelectView(self.outer.embed, member_select_options, self.select_view_return, placeholder = "Choose a Member", continue_button_label = "Next").setup(interaction)
                            
                        async def select_view_return(self, interaction: Interaction, selection):
                            if selection == None: # User clicked "Cancel"
                                await self.outer.setup(interaction)
                                return
                            
                            await interaction.response.send_modal(self.InfoModal(self.outer, selection, interaction.guild.id))          
                                            
                        class InfoModal(CustomModal):            
                            def __init__(self, outer, member_id, guild_id):
                                super().__init__(title = "Add Birthday", timeout = None)
                                self.outer = outer
                                self.member_id = member_id
                                
                                server = Server(guild_id)
                                birthday = server.birthdays[self.member_id]
                                
                                self.dateInput = nextcord.ui.TextInput(label = "Date (MM/DD/YYYY)", style = nextcord.TextInputStyle.short, max_length = 10, placeholder = "MM/DD/YYYY", default_value = birthday.birth_date)
                                self.add_item(self.dateInput)
                                
                                self.realNameInput = nextcord.ui.TextInput(label = "Real Name (Optional)", style = nextcord.TextInputStyle.short, max_length=50, required = False, default_value = birthday.real_name)
                                self.add_item(self.realNameInput)
                                
                            async def callback(self, interaction: Interaction):
                                try:
                                    datetime.datetime.strptime(self.dateInput.value, f"%m/%d/%Y")
                                except:
                                    await interaction.response.send_message(embed = nextcord.Embed(title = "Invalid Format", description = "You formatted the date wrong. Try formating it like this: MM/DD/YYYY", color =  nextcord.Color.red()), ephemeral=True)
                                    return
                                
                                server = Server(interaction.guild.id)
                                real_name = self.realNameInput.value if self.realNameInput.value != "" else None
                                server.birthdays.edit(self.member_id, birth_date = self.dateInput.value, real_name = real_name)
                                
                                await self.outer.setup(interaction)

                    class DeleteBirthdayButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Delete", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                                            
                        async def callback(self, interaction: Interaction):# Edit Strikes Callback ————————————————————————————————————————————————————————————
                            server = Server(interaction.guild.id)
                                
                            member_select_options = []
                            for member in interaction.guild.members:
                                if member.id in server.birthdays:
                                    member_select_options.append(nextcord.SelectOption(label = f"{member}", description = member.nick, value = member.id))
                            
                            
                            if member_select_options == []: 
                                await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Members", description = "No members in your server have birthdays. Add some!", color = nextcord.Color.red()), ephemeral = True)
                                return
                            
                            await ui_components.SelectView(self.outer.embed, member_select_options, self.select_view_return, placeholder = "Choose a Member", continue_button_label = "Delete").setup(interaction)
                            
                        async def select_view_return(self, interaction: Interaction, selection):
                            if selection == None: # User clicked "Cancel"
                                await self.outer.setup(interaction)
                                return
                            
                            server = Server(interaction.guild.id)
                            server.birthdays.delete(selection)
                            
                            await self.outer.setup(interaction)      
                                            
                    class DeleteAllBirthdaysButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Delete All", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class DeleteAllStrikesView(CustomView):
                            def __init__(self, outer):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                self.no_btn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
                                self.no_btn.callback = self.no_btn_command
                                self.add_item(self.no_btn)
                                
                                self.yes_btn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
                                self.yes_btn.callback = self.yes_btn_command
                                self.add_item(self.yes_btn)
                                
                            async def setup(self, interaction: Interaction):
                                embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will delete all birthdays in the server.\nThis action cannot be undone.", color = nextcord.Color.blue())
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                            async def no_btn_command(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                                
                            async def yes_btn_command(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                for birthday in server.birthdays:
                                    server.birthdays.delete(birthday.member_id)

                                await self.outer.setup(interaction)
                            
                        async def callback(self, interaction: Interaction):
                            await self.DeleteAllStrikesView(self.outer).setup(interaction)           

                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)

                async def callback(self, interaction: Interaction):
                    await self.ConfigureBirthdaysView(self.outer).setup(interaction)
    
            class BirthdaysChannelButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Notification Channel", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                                     
                async def callback(self, interaction: Interaction):
                    server = Server(interaction.guild.id)
                        
                    select_options = [nextcord.SelectOption(label = "System Messages Channel", value = "__SYS__", description = "Display in system messages channel", 
                                                            default = (server.birthdays_profile.channel == UNSET_VALUE))]
                    for channel in interaction.guild.text_channels:
                        if not await utils.check_text_channel_permissions(channel, False): continue
                        select_options.append(nextcord.SelectOption(label = channel.name, value = channel.id, 
                                                                    description = f"{channel.category}", 
                                                                    default = (server.birthdays_profile.channel == channel.id)))
                    
                    description = """
                    Select a channel to send birthday messages.
                    
                    **Can't Find Your Channel?**
                    Ensure InfiniBot has permissions to view and send messages in all your channels.
                    """
                    description = utils.standardize_str_indention(description)
                    embed = nextcord.Embed(title = "Dashboard - Birthdays - Notification Channel", description = description, color = nextcord.Color.blue())
                    await ui_components.SelectView(embed, select_options, self.select_view_return, continue_button_label = "Confirm").setup(interaction)
                      
                async def select_view_return(self, interaction: Interaction, selection):
                    if selection == None: # User clicked "Cancel"
                        await self.outer.setup(interaction)
                        return
                    
                    if selection == "__SYS__": value = UNSET_VALUE
                    else: value = selection
                    
                    server = Server(interaction.guild.id)
                    server.birthdays_profile.channel = value

                    await self.outer.setup(interaction)

            class UpdateMessageTimeButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Update Message Time", style = nextcord.ButtonStyle.gray, row = 1)
                    self.outer = outer

                class UpdateMessageTimeView(CustomView):
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.cancel_btn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger) 
                        self.cancel_btn.callback = self.cancel_btn_callback
                        self.add_item(self.cancel_btn)

                        self.continue_btn = self.ContinueButton(self)
                        self.add_item(self.continue_btn)

                    async def setup(self, interaction: Interaction):
                        description = """
                        Update the time that InfiniBot will send birthday messages at.

                        To do provide the best experience, InfiniBot needs to account for your timezone. To do this, it will ask for your current date and time. InfiniBot will compare your answers to its date and time to find your UTC offset. Your data will not be stored.
                        
                        If you experience timezone changes throught the year, such as Daylight Savings Time, you may need to periodically update this value.

                        When you're ready, click "Continue".
                        """
                        description = utils.standardize_str_indention(description)
                        embed = nextcord.Embed(title = "Dashboard - Birthdays - Update Message Time", description = description, color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)

                    async def cancel_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)

                    class ContinueButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Continue", style = nextcord.ButtonStyle.green)
                            self.outer = outer
                    
                        class PinpointTimezoneModal(CustomModal):
                            def __init__(self, outer):
                                super().__init__(title = "Pinpoint Timezone", timeout = None)
                                self.outer = outer
                                self.utc_offset = None
                                    
                                self.date_input = nextcord.ui.TextInput(label = "What day is it right now?",  
                                                                    placeholder = "MM/DD/YYYY", max_length=100)
                                self.add_item(self.date_input)

                                self.time_input = nextcord.ui.TextInput(label = "What time is it right now?",
                                                                    placeholder = "HH:MM (AM/PM)", max_length=100)
                                self.add_item(self.time_input)
                                
                            async def callback(self, interaction: Interaction):
                                error_embed = nextcord.Embed(title = "An Error Occurred", description = "Something went wrong. The date must be your current date, formatted as MM/DD/YYYY, and the time must be your current time, formatted as HH:MM (AM/PM).", color = nextcord.Color.red())

                                try:
                                    if self.time_input.value == "" or self.time_input.value == None: raise Exception
                                    if self.date_input.value == "" or self.date_input.value == None: raise Exception

                                    self.utc_offset = utils.calculate_utc_offset(self.date_input.value, self.time_input.value)
                                except:
                                    await interaction.response.send_message(embed = error_embed, ephemeral=True)
                                    return
                                
                                await self.NextView(self.outer, self.utc_offset).setup(interaction)

                            class NextView(CustomView):
                                def __init__(self, outer, utc_offset):
                                    super().__init__(timeout = None)
                                    self.outer = outer
                                    self.utc_offset = utc_offset

                                    self.cancel_btn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger) 
                                    self.cancel_btn.callback = self.cancel_btn_callback
                                    self.add_item(self.cancel_btn)

                                    self.set_time_btn = self.SetTimeButton(self.outer, self.utc_offset)
                                    self.add_item(self.set_time_btn)

                                async def setup(self, interaction: Interaction):
                                    try:
                                        _datetime = utils.conversion_local_time_and_utc_time(self.utc_offset, local_time_str="08:30", return_entire_datetime=True)
                                        epoch_time = _datetime.timestamp()
                                        epoch_time = round(epoch_time)
                                        discord_timestamp = f"<t:{epoch_time}:f>"
                                    except Exception as e:
                                        logging.error(e)
                                        discord_timestamp = "*ERROR: An unknown error occurred.*"


                                    description = f"""
                                    InfiniBot has determined your UTC offset to be {self.utc_offset} hours. 
                                    
                                    The time below should be equivalent to January 1st, 2000 at 8:30 (in the morning).
                                    {discord_timestamp}

                                    If this is incorrect, click "Cancel" and try again.

                                    To update the time that InfiniBot will send birthday messages at, click "Set Time".
                                    """
                                    description = utils.standardize_str_indention(description)
                                    embed = nextcord.Embed(title = "Dashboard - Birthdays - Update Message Time", description = description, color = nextcord.Color.blue())
                                    await interaction.response.edit_message(embed=embed, view=self)

                                async def cancel_btn_callback(self, interaction: Interaction):
                                    await self.outer.setup(interaction)

                                class SetTimeButton(nextcord.ui.Button):
                                    def __init__(self, outer, utc_offset):
                                        super().__init__(label = "Set Time", style = nextcord.ButtonStyle.green)
                                        self.outer = outer
                                        self.utc_offset = utc_offset

                                    async def callback(self, interaction: Interaction):
                                        await interaction.response.send_modal(self.UpdateMessageTimeModal(self.outer, interaction.guild.id, self.utc_offset))
                                
                                    class UpdateMessageTimeModal(CustomModal):
                                        def __init__(self, outer, guild_id, utc_offset):
                                            super().__init__(title = "Update Message Time", timeout = None)
                                            self.outer = outer
                                            self.guild_id = guild_id
                                            self.utc_offset = utc_offset

                                            try:
                                                server = Server(guild_id)
                                                time_formatted = utils.conversion_local_time_and_utc_time(self.utc_offset, utc_time_str=server.birthdays_profile.runtime)
                                                time_formatted = f"{time_formatted}"[:-3] # Remove the seconds
                                            except:
                                                time_formatted = None
                                                
                                            self.local_time_input = nextcord.ui.TextInput(label = "What time should birthday messages be sent?",
                                                                            placeholder = "HH:MM (AM/PM)", default_value=time_formatted, max_length=100)
                                            self.add_item(self.local_time_input)
                                            
                                        async def callback(self, interaction: Interaction):
                                            error_embed = nextcord.Embed(title = "An Error Occurred", description = "Something went wrong. The time must be formatted as HH:MM (AM/PM).", color = nextcord.Color.red())

                                            try:
                                                if self.local_time_input.value == "" or self.local_time_input.value == None: raise Exception
                                                time_split = self.local_time_input.value.split(":")
                                                if len(time_split) != 2: raise Exception
                                                for time in time_split: 
                                                    if not time.isdigit() or int(time) < 0 or int(time) > 23: raise Exception
                                                    
                                                time_formatted = utils.conversion_local_time_and_utc_time(self.utc_offset, local_time_str=self.local_time_input.value)
                                                time_formatted = f"{time_formatted}"[:-3] # Remove the seconds
                                            except:
                                                await interaction.response.send_message(embed = error_embed, ephemeral=True)
                                                return
                                            
                                            server = Server(self.guild_id)
                                            server.birthdays_profile.runtime = time_formatted

                                            await self.outer.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.PinpointTimezoneModal(self.outer))
                
                async def callback(self, interaction: Interaction):
                    await self.UpdateMessageTimeView(self.outer).setup(interaction)

            class EditBirthdayMessageButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Edit Message", style = nextcord.ButtonStyle.gray, row = 1)
                    self.outer = outer
                    
                class EditMessageModal(CustomModal):
                    def __init__(self, guild: nextcord.Guild, outer):
                        super().__init__(timeout = None, title = "Birthday Message")
                        self.outer = outer
                        
                        server = Server(guild.id)
                        
                        self.join_message_title_input = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, max_length=256, 
                                                                                default_value = server.birthdays_profile.embed["title"], placeholder = "Happy Birthday, @realname!")
                        self.add_item(self.join_message_title_input)

                        self.join_message_description_input = nextcord.ui.TextInput(label = "Description", style = nextcord.TextInputStyle.paragraph, max_length=1024, 
                                                                                default_value = server.birthdays_profile.embed["description"], placeholder = "@member just turned [age]!")
                        self.add_item(self.join_message_description_input)
                        
                    async def callback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        embed = server.birthdays_profile.embed
                        embed["title"] = self.join_message_title_input.value
                        embed["description"] = self.join_message_description_input.value
                        server.birthdays_profile.embed = embed

                        await self.outer.setup(interaction)                     
                        
                async def callback(self, interaction: Interaction):
                    await interaction.response.send_modal(self.EditMessageModal(interaction.guild, self.outer))                

            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)

        async def callback(self, interaction: Interaction):
            view = self.BirthdaysView(self.outer)
            await view.setup(interaction)
           
    class DefaultRolesButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Default Roles", style = nextcord.ButtonStyle.gray, row = 1)
            self.outer = outer
            
        class DefaultRolesView(CustomView):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.add_role_btn = self.AddRoleButton(self)
                self.add_item(self.add_role_btn)
                
                self.delete_role_btn = self.DeleteRoleButton(self)
                self.add_item(self.delete_role_btn)
                
                self.delete_all_default_roles_btn = self.DeleteAllDefaultRolesBtn(self)
                self.add_item(self.delete_all_default_roles_btn)
                
                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                
            async def setup(self, interaction: Interaction):
                if not utils.feature_is_active(server_id = interaction.guild.id, feature = "default_roles"): # server_id won't be used here, but it's required as an input
                    await ui_components.disabled_feature_override(self, interaction)
                    return
                
                description = """
                InfiniBot can automatically assign default roles to members when they join the server. Use the buttons below to add or remove default roles.
                """
                description = utils.standardize_str_indention(description)
                self.embed = nextcord.Embed(title = "Dashboard - Default Roles", 
                                            description = description,
                                            color = nextcord.Color.blue())
                
                server = Server(interaction.guild.id)
                
                default_roles = []
                for default_role_id in server.default_roles.default_roles:
                    role = interaction.guild.get_role(int(default_role_id))
                    if role == None:
                        logging.warning(f"Role {default_role_id} was not found in the guild {interaction.guild.id} when checking default roles (viewing). Deleting.")
                        default_roles:list = server.default_roles.default_roles
                        default_roles.remove(default_role_id)
                        server.default_roles.default_roles = default_roles
                        continue

                    default_roles.append(f"{role.mention}")
                        
                if default_roles == []: default_roles.append("You don't have any default roles set up. Create one!")
                self.embed.add_field(name = "Default Roles", value = "\n".join(default_roles))
                try: await interaction.response.edit_message(embed = self.embed, view = self)
                except: await interaction.edit_original_message(embed = self.embed, view = self)
                
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                await interaction.edit_original_message(view = self.outer)
                                                            
            class AddRoleButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Add Role", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                                        
                async def callback(self, interaction: Interaction):
                    server = Server(interaction.guild.id)
                    
                    select_options = []
                    for role in interaction.guild.roles:
                        if role.name == "@everyone": continue
                        if not utils.role_assignable_by_infinibot(role): continue
                        if role.id not in server.default_roles.default_roles: 
                            select_options.append(nextcord.SelectOption(label = role.name, description = role.id, value = role.id))
                    
                    if select_options == []:
                        await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", 
                                                                                        description = "You've run out of roles to use! To fix this, ensure that infinibot can grant the roles you would like to set as default roles. An easy way to do this is to promote InfiniBot to a Moderator role.", 
                                                                                        color = nextcord.Color.red()), ephemeral=True)
                        return          
                                
                    description = """
                    Select a role to add to the list of default roles. InfiniBot will assign this role to any new members upon join.

                    **Don't See Your Role?**
                    Ensure InfiniBot can grant the roles you would like to set as default roles. An easy way to do this is to promote InfiniBot to a Moderator role.
                    """
                    description = utils.standardize_str_indention(description)
                    embed = nextcord.Embed(title = "Dashboard - Default Roles - Add Role",
                                            description = description,
                                            color = nextcord.Color.blue())
                    await ui_components.SelectView(embed, select_options, self.select_view_callback, continue_button_label = "Add", placeholder = "Choose").setup(interaction)            
                    
                async def select_view_callback(self, interaction: Interaction, selection):
                    if selection == None: # User cancelled
                        await self.outer.setup(interaction) 
                        return
                    
                    server = Server(interaction.guild.id)
                    default_roles = server.default_roles.default_roles
                    default_roles.append(int(selection))
                    server.default_roles.default_roles = default_roles

                    await self.outer.setup(interaction)
            
            class DeleteRoleButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Delete Role", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                                                                        
                async def callback(self, interaction: Interaction):# Delete Level Reward Callback ————————————————————————————————————————————————————————————
                    server = Server(interaction.guild.id)
                    all_default_roles = []
                    for default_role_id in server.default_roles.default_roles:
                        role = interaction.guild.get_role(int(default_role_id))
                        if role == None: # Should never happen because of earlier checks. But just in case...
                            logging.warning(f"Role {default_role_id} was not found in the guild {interaction.guild.id} when checking default roles (deletion). Ignoring...")
                            continue

                        all_default_roles.append(role)
                                                        
                    select_options = [nextcord.SelectOption(label = role.name, description = role.id, value = role.id) for role in all_default_roles]
                    
                    if select_options == []:
                        await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", description = "You don't have any default roles set up!", color = nextcord.Color.red()), ephemeral=True)                     
                    else:
                        embed = nextcord.Embed(title = "Dashboard - Default Roles - Delete Role",
                                                description = "Select a default role to delete. This does not delete the role. It just removes it from the list of default roles for InfiniBot to assign to new members.",
                                                color = nextcord.Color.blue())
                        await ui_components.SelectView(embed, select_options, self.select_view_callback, continue_button_label = "Delete", placeholder = "Choose").setup(interaction)
            
                async def select_view_callback(self, interaction: Interaction, selection):
                    if selection == None: # User cancelled
                        await self.outer.setup(interaction)
                        return
                    
                    server = Server(interaction.guild.id)
                    default_roles = server.default_roles.default_roles
                    default_roles.remove(int(selection))
                    server.default_roles.default_roles = default_roles
                    
                    await self.outer.setup(interaction)
            
            class DeleteAllDefaultRolesBtn(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Delete All Default Roles", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class DeleteAllDefaultRolesView(CustomView):
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.no_btn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
                        self.no_btn.callback = self.no_btn_command
                        self.add_item(self.no_btn)
                        
                        self.yes_btn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
                        self.yes_btn.callback = self.yes_btn_command
                        self.add_item(self.yes_btn)
                        
                    async def setup(self, interaction: Interaction):
                        embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will delete all default roles in the server (the actual roles will not be deleted).\n\nThis action cannot be undone.", color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def no_btn_command(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    async def yes_btn_command(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        server.default_roles.default_roles = []
                        await self.outer.setup(interaction)
                        
                    async def callback(self, interaction: Interaction):
                        await self.DeleteAllLevelsView(self.outer).setup(interaction)
                
                async def callback(self, interaction: Interaction):
                    await self.DeleteAllDefaultRolesView(self.outer).setup(interaction)
            
        async def callback(self, interaction: Interaction): #Filtered Words Button Callback ————————————————————————————————————————————————————————————
            view = self.DefaultRolesView(self.outer)
            await view.setup(interaction)           
 
    class JoinToCreateVCsButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Join-To-Create VCs", style = nextcord.ButtonStyle.gray, row = 1)
            self.outer = outer
                    
        class JoinToCreateVCsView(CustomView):
            def __init__(self, outer, guild: nextcord.Guild, onboarding_modifier = None, onboarding_embed = None):
                super().__init__(timeout=None)
                self.outer = outer
                self.guild = guild
                self.onboarding_modifier = onboarding_modifier
                self.onboarding_embed = onboarding_embed

                server = Server(self.guild.id)
                        
                # Find all join-to-create VCs (log which ones have errors)
                # This needs to be done here because the buttons need this info to determine
                # whether or not to be disabled
                self.join_to_create_vcs_with_error_info = []
                for vc_id in server.join_to_create_vcs.channels:
                    voice_channel = guild.get_channel(vc_id)
                    
                    error = False
                    if not voice_channel: error = True; logging.warning(f"Join-to-create VC {vc_id} in guild {self.guild.id} was not found. Ignoring, but marking it as an error...")
                    elif not voice_channel.permissions_for(self.guild.me).view_channel: error = True; logging.warning(f"Join-to-create VC {vc_id} in guild {self.guild.id} does not have view_channel permission for InfiniBot. Ignoring, but marking it as an error...")
                    elif not voice_channel.permissions_for(self.guild.me).manage_channels: error = True; logging.warning(f"Join-to-create VC {vc_id} in guild {self.guild.id} does not have manage_channels permission for InfiniBot. Ignoring, but marking it as an error...")

                    self.join_to_create_vcs_with_error_info.append([voice_channel, error])

                self.add_btn = self.AddButton(self, guild, self.join_to_create_vcs_with_error_info)
                self.add_item(self.add_btn)
                
                self.delete_btn = self.DeleteButton(self, guild)
                self.add_item(self.delete_btn)
                
                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
        
            async def setup(self, interaction: Interaction):
                if self.onboarding_modifier: self.onboarding_modifier(self)
                
                if not utils.feature_is_active(server_id = interaction.guild.id, feature = "join_to_create_vcs"): # server_id won't be used here, but it's required as an input
                    await ui_components.disabled_feature_override(self, interaction)
                    return
                
                # Get server data
                server = Server(interaction.guild.id)
                join_to_create_voice_channels:list = server.join_to_create_vcs.channels
                    
                
                # Build UI
                join_to_create_vcs_ui_text = "**Join-To-Create VCs**\n"

                if len(join_to_create_voice_channels) > 0:
                    vcs_ui_text_list = []
                    for vc_id in join_to_create_voice_channels:
                        voice_channel = interaction.guild.get_channel(vc_id)
                        
                        error = False
                        if not voice_channel: 
                            error = True
                            reference = f"UNKNOWN CHANNEL ({vc_id})"
                        else:
                            reference = voice_channel.mention
                            if not voice_channel.permissions_for(interaction.guild.me).view_channel: error = True
                            elif not voice_channel.permissions_for(interaction.guild.me).manage_channels: error = True

                        vcs_ui_text_list.append(f"• {reference}" if not error else f"• ⚠️ {reference} ⚠️")

                    join_to_create_vcs_ui_text += "\n".join(vcs_ui_text_list)
                else:
                    join_to_create_vcs_ui_text += "You don't have any join-to-create VCs. Click Configure to make one!"

                # Add an error message (if needed)
                if True in [vc_info[1] for vc_info in self.join_to_create_vcs_with_error_info]:
                    error_message = """
                    **⚠️ There is a Problem with One or More of Your VCs ⚠️**
                    Make sure that InfiniBot has the following permissions in all of your join-to-create VCs:
                    • View Channel
                    • Manage Channel
                    • Move Members
                    • Connect
                    """
                else:
                    error_message = ""

                # Build embed   
                description = f"""
                You may select up to ten voice channels that will have this feature.
                
                **What is it?**
                When a user joins one of these Voice Channels, they will be moved to a custom voice channel created just for them. When everyone leaves, the channel will be removed.
                
                {join_to_create_vcs_ui_text}
                {error_message}
                For more information, use: {UNSET_VALUE}
                """ # TODO add shortcut for help command
                description = utils.standardize_str_indention(description)
                embed = nextcord.Embed(title = "Dashboard - Join-To-Create-VCs", description = description, color = nextcord.Color.blue())
                
                if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
                else: embeds = [embed]
                
                await interaction.response.edit_message(embeds = embeds, view = self)
                  
            async def reload(self, interaction: Interaction):
                self.__init__(self.outer, interaction.guild)
                await self.setup(interaction)

            class AddButton(nextcord.ui.Button):
                def __init__(self, outer, guild: nextcord.Guild, join_to_create_vcs_with_error_info:list[nextcord.VoiceChannel, bool]):
                    self.outer = outer
                    self.join_to_create_vcs_with_error_info = join_to_create_vcs_with_error_info

                    # Get a server to work with
                    server = Server(guild.id)

                    # Get the available vcs
                    self.available_voice_channels:list[nextcord.VoiceChannel] = [] # Voice channels that are available (ie. not already a join-to-create VC and have the correct permissions)
                    for voice_channel in guild.voice_channels:
                        if voice_channel.id in server.join_to_create_vcs.channels: continue
                        if not voice_channel.permissions_for(guild.me).view_channel: continue
                        if not voice_channel.permissions_for(guild.me).manage_channels: continue
                        if not voice_channel.permissions_for(guild.me).move_members: continue

                        self.available_voice_channels.append(voice_channel)
                    
                    # Choose whether to be enabled or disabled
                    disabled = False
                    if len(server.join_to_create_vcs.channels) >= 10: disabled = True
                    if len(self.available_voice_channels) == 0: disabled = True
                    
                    # Choose button style
                    if len(server.join_to_create_vcs.channels) == 0 and not disabled: style = nextcord.ButtonStyle.blurple
                    else: style = nextcord.ButtonStyle.gray
    
                    super().__init__(label = "Add Channel", style = style, disabled = disabled)
                                                
                async def callback(self, interaction: Interaction):
                    select_options = []
                    for voice_channel in self.available_voice_channels:
                        select_options.append(
                            nextcord.SelectOption(label = voice_channel.name, value = voice_channel.id,
                                                    description = (voice_channel.category.name if voice_channel.category else None))
                            )
                    
                    description = """Select a Voice Channel to be a Join-To-Create Voice Channel.
                        
                    **Don't See Your Channel?**
                    Make sure that InfiniBot has the following permissions in all of your channels:
                    • View Channel
                    • Manage Channel
                    • Move Members
                    • Connect
                    """
                    description = utils.standardize_str_indention(description)
                    
                    embed = nextcord.Embed(title = "Dashboard - Join-To-Create-VCs - Add Channel", description = description, color = nextcord.Color.blue())
                    view = ui_components.SelectView(embed,
                                        options = select_options, 
                                        return_command = self.select_callback, 
                                        continue_button_label = "Add", 
                                        preserve_order = True, 
                                        placeholder = "Select a Voice Channel")
                    
                    await view.setup(interaction)
                    
                async def select_callback(self, interaction: Interaction, selection: str):
                    if selection == None: # User clicked "Cancel"
                        await self.outer.reload(interaction) 
                        return
                    
                    server = Server(interaction.guild.id)

                    join_to_create_voice_channels = server.join_to_create_vcs.channels
                    join_to_create_voice_channels.append(int(selection))
                    server.join_to_create_vcs.channels = join_to_create_voice_channels
                    
                    await self.outer.reload(interaction)
                    
            class DeleteButton(nextcord.ui.Button):
                def __init__(self, outer, guild: nextcord.Guild):
                    self.outer = outer
                    
                    server = Server(guild.id)
                    
                    # Choose whether to be enabled or disabled
                    disabled = True
                    if len(server.join_to_create_vcs.channels) > 0: disabled = False
    
                    super().__init__(label = "Delete Channel", style = nextcord.ButtonStyle.gray, disabled = disabled)
                                                
                async def callback(self, interaction: Interaction):
                    server = Server(interaction.guild.id)
                    select_options = []
                    for vc_id in server.join_to_create_vcs.channels:
                        voice_channel = interaction.guild.get_channel(vc_id)
                        if voice_channel:
                            label = voice_channel.name
                            description = (voice_channel.category.name if voice_channel.category else None)
                        else:
                            label =  "⚠️ UNKNOWN CHANNEL ⚠️"
                            description = vc_id
                        
                        select_options.append(
                            nextcord.SelectOption(label = label, value = vc_id, description = description)
                        )
                                
                    description = """
                    Select a Join-To-Create Voice Channel to delete. (Does not delete the Voice Channel, but removes it from Join-To-Create).
                    """
                    description = utils.standardize_str_indention(description)
                    
                    embed = nextcord.Embed(title = "Dashboard - Join-To-Create-VCs - Delete Channel", description = description, color = nextcord.Color.blue())
                    view = ui_components.SelectView(embed,
                                        options = select_options, 
                                        return_command = self.select_callback, 
                                        continue_button_label = "Delete", 
                                        preserve_order = True, 
                                        placeholder = "Select a Voice Channel")
                    
                    await view.setup(interaction)
                    
                async def select_callback(self, interaction: Interaction, selection: str):
                    if selection == None: # User clicked "Cancel"
                        await self.outer.reload(interaction)
                        return
                    
                    server = Server(interaction.guild.id)
                
                    join_to_create_voice_channels = server.join_to_create_vcs.channels
                    join_to_create_voice_channels.remove(int(selection))
                    server.join_to_create_vcs.channels = join_to_create_voice_channels
                    
                    await self.outer.reload(interaction)
                   
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
        
        async def callback(self, interaction: Interaction):
            await self.JoinToCreateVCsView(self.outer, interaction.guild).setup(interaction)
        
    class ExtraFeaturesButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Extra Features", style = nextcord.ButtonStyle.gray, row = 2)
            self.outer = outer
            
        class ExtraFeaturesButton(CustomView):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer

                items = {
                    "Auto-Delete Invites": "infinibot_settings_profile.delete_invites",
                    "Update Messages": "infinibot_settings_profile.get_updates",
                }

                for key, value in items.items():
                    self.add_item(self.EnableDisableButton(self, key, value))

                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 4)
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                
            async def setup(self, interaction: Interaction):
                for child in self.children: 
                    del child 
                    self.__init__(self.outer, interaction.guild.id)
                
                server = Server(interaction.guild.id)
                
                description = f"""
                Choose a feature to enable / disable
                
                **{self.bool_to_symbol(server.infinibot_settings_profile.delete_invites)} - Auto-Delete Invites**
                InfiniBot can automatically delete discord invites posted by members. (Does not affect Administrators)
                
                **{self.bool_to_symbol(server.infinibot_settings_profile.get_updates)} - Update Messages**
                Get notified about brand-new updates to InfiniBot.
                """
                description = utils.standardize_str_indention(description)
                
                embed = nextcord.Embed(title = "Dashboard - Extra Features", description = description, color = nextcord.Color.blue())
                await interaction.response.edit_message(embed = embed, view = self)
             
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                
            def bool_to_symbol(self, bool: bool):
                if bool:
                    return "✅"
                else:
                    return "❌"

            class EnableDisableButton(nextcord.ui.Button):
                def __init__(self, outer, name, path, row = 0):
                    super().__init__(label = f"{name}", style = nextcord.ButtonStyle.gray, row = row)
                    self.outer = outer
                    self.name = name
                    self.path = path
                    
                class ChooseView(CustomView):
                    def __init__(self, outer, name, guild_id, path):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.name = name
                        self.guild_id = guild_id
                        self.path = path
                        
                        if self.operate_on_variable(self.path, flip = False):
                            self.choice = "Disable"
                        else:
                            self.choice = "Enable"
                        
                        self.cancel_btn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                        self.cancel_btn.callback = self.cancel_btn_command
                        self.add_item(self.cancel_btn)
                        
                        self.choice_btn = nextcord.ui.Button(label = self.choice, style = nextcord.ButtonStyle.green)
                        self.choice_btn.callback = self.choice_btn_command
                        self.add_item(self.choice_btn)
                        
                    async def setup(self, interaction: Interaction):
                        embed = nextcord.Embed(title = f"Enable / Disable {self.name}", description = f"To {self.choice.lower()} {self.name}, click the button \"{self.choice}\"", color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def cancel_btn_command(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    async def choice_btn_command(self, interaction: Interaction):
                        self.operate_on_variable(self.path, flip = True)
                        
                        await self.outer.setup(interaction)
                        
                    def operate_on_variable(self, path, flip = None):
                        if flip == None: raise ValueError(f"Error: {__name__} received an invalid value for flip.")
                        path = path.split(".")
                        attr = Server(self.guild_id)
                        for index, level in enumerate(path):
                            if not hasattr(attr, level):
                                raise ValueError(f"Error: {__name__} received an invalid path when retrieving a variable from the server. Path: {path}")
                            
                            if index == len(path) - 1: # Last level
                                if flip:
                                    setattr(attr, level, not getattr(attr, level))
                                return getattr(attr, level)
                            
                            attr = getattr(attr, level)

                        raise ValueError(f"Error: {__name__} got an unknown error when retrieving a variable from the server. Path: {path}")
                 
                async def callback(self, interaction: Interaction):
                    await self.ChooseView(self.outer, self.name, self.path).setup(interaction)
                       
        async def callback(self, interaction: Interaction):
            await self.ExtraFeaturesButton(self.outer, interaction.guild.id).setup(interaction)

async def run_dashboard_command(interaction: Interaction):
    if await utils.user_has_config_permissions(interaction):
        view = Dashboard()
        await view.setup(interaction)