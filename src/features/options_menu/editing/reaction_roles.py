from nextcord import Interaction
import nextcord
import re
import json
import logging

from config.server import Server
from components import utils, ui_components
from features.action_logging import trigger_edit_log

class EditReactionRole(nextcord.ui.View):
    def __init__(self, message_id: int):
        super().__init__(timeout = None)
        self.message_id = message_id
        
    async def load_buttons(self, interaction: Interaction):
        self.message = await interaction.channel.fetch_message(self.message_id)
        self.server = Server(interaction.guild.id)
        self.message_info = self.server.managed_messages[self.message_id]
        
        self.clear_items()
        
        edit_text_btn = self.EditTextButton(self)
        self.add_item(edit_text_btn)
        
        edit_options_btn = self.EditOptionsButton(self, self.message_info)
        self.add_item(edit_options_btn)
        
    async def setup(self, interaction: Interaction):
        await self.load_buttons(interaction)
        
        if not utils.feature_is_active(feature="options_menu.editing", guild_id=interaction.guild.id):
            await ui_components.disabled_feature_override(self, interaction)
            return
        
        main_embed = nextcord.Embed(
            title = "Edit Reaction Role", 
            description = "Edit the following reaction role's text and options.", 
            color = nextcord.Color.yellow())
        
        edit_embed = self.message.embeds[0]
        embeds = [main_embed, edit_embed]

        await interaction.response.edit_message(embeds=embeds, view=self)
  
    class EditTextButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Edit Text", emoji = "✏️")
            self.outer = outer
        
        class EditTextModal(nextcord.ui.Modal):
            def __init__(self, outer):
                super().__init__(title = "Edit Text")
                self.outer = outer
                
                self.title_input = nextcord.ui.TextInput(label = "Title", min_length = 1, max_length = 256, placeholder = "Title", default_value = outer.message.embeds[0].title)
                self.add_item(self.title_input)
                
                self.description_input = nextcord.ui.TextInput(label = "Description", min_length = 1, max_length = 4000, placeholder = "Description", default_value = outer.message.embeds[0].description, style = nextcord.TextInputStyle.paragraph)
                self.add_item(self.description_input)
                
            async def callback(self, interaction: Interaction):
                self.stop()
                before_message = await interaction.channel.fetch_message(self.outer.message.id)
                
                embed = nextcord.Embed(title=self.title_input.value, description=self.description_input.value, color=before_message.embeds[0].color)
                for field in before_message.embeds[0].fields:
                    embed.add_field(name=field.name, value=field.value, inline=field.inline)
                    
                await before_message.edit(embed = embed)
                await self.outer.setup(interaction)
                
                # Trigger Edit Log
                after_message = await interaction.channel.fetch_message(self.outer.message.id)
                await trigger_edit_log(interaction.guild, before_message, after_message, user=interaction.user)
        
        async def callback(self, interaction: Interaction):
            await interaction.response.send_modal(self.EditTextModal(self.outer))
  
    class EditOptionsButton(nextcord.ui.Button):
        def __init__(self, outer, message_info):
            super().__init__(label = "Edit Options", emoji = "🎚️")
            self.outer = outer
            self.message_info = message_info
        
        class EditOptionsView(nextcord.ui.View):
            def __init__(self, outer, message_info):
                super().__init__(timeout = None)
                self.outer = outer
                self.message_info = message_info
                self.added_reactions__emojis = []
                self.added_roles__IDs = []
                self.added_options__no_format = []
                self.message_id = None
                
                self.add_btn = self.AddButton(self, self.message_info)
                self.add_item(self.add_btn)
                
                self.delete_btn = self.DeleteButton(self, self.message_info)
                self.add_item(self.delete_btn)
                
                self.back_btn = nextcord.ui.Button(label="Back", style=nextcord.ButtonStyle.gray, row=1) 
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                
            async def setup(self, interaction: Interaction):             
                # Get the message
                channel = await interaction.guild.fetch_channel(self.message_info.channel_id)
                message = await channel.fetch_message(self.message_info.message_id)       
                            
                # Get all options
                options = message.embeds[0].fields[0].value.split("\n")
                self.formatted_options, problem = self.format_options(interaction.guild, options)
                
                # Create UI
                embed = nextcord.Embed(title = "Edit Reaction Role - Edit Options",
                                       description = "Add, Manage, and Delete Options.",
                                       color = nextcord.Color.yellow())
                
                embed.add_field(name = "Roles", value = "\n".join(self.formatted_options))
                
                # Help Messages
                if problem:
                    embed.add_field(name = "⚠️ Issue With One or More Roles ⚠️", value = "One or more of your roles no longer exist.", inline = False)
                    
                    
                # ============================================ OTHER SETUP ============================================
                
                
                # Prepare Available Roles
                self.available_roles = []
                
                for role in interaction.guild.roles:
                    if role.name == "@everyone": continue
                    if role.id in self.added_roles__IDs: continue
                    if utils.role_assignable_by_infinibot(role): self.available_roles.append(role)
                    
                
                # Check Buttons and their Availability
                if len(self.formatted_options) >= 10 and len(self.available_roles) > 0:
                    self.add_btn.disabled = True
                else:
                    self.add_btn.disabled = False
                    
                if len(self.formatted_options) <= 1:
                    self.delete_btn.disabled = True
                else:
                    self.delete_btn.disabled = False
                    
                    
                # Edit the message
                try:
                    message = await interaction.response.edit_message(embed = embed, view = self)
                    self.message_id = message.id
                except:
                    await interaction.followup.edit_message(message_id = self.message_id, embed = embed, view = self)

            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
           
            def get_role(self, guild: nextcord.Guild, string: str):
                pattern = r"^(<@&)(.*)>$"  # "<@&...>"
                match = re.search(pattern, string)
                if match:
                    id = int(match.group(2))
                    role = nextcord.utils.get(guild.roles, id=id)
                elif string.isdigit():
                    role = nextcord.utils.get(guild.roles, id=int(string))
                else:
                    role = nextcord.utils.get(guild.roles, name=string)
                    
                return role
           
            def format_options(self, guild: nextcord.Guild, lines: list[str], packet_to_modify=None, display_errors=True):
                self.added_roles__IDs = []
                self.added_reactions__emojis = []
                self.added_options__no_format = []
                
                return_list = []
                problem = False
                
                json_data = json.loads(self.message_info.json_data)

                # Inject another role if we are modifying a role. If we are deleting the role, well, we actually have it twice and ignore it twice.
                if packet_to_modify:
                    if packet_to_modify[0] == None: packet_to_modify[0] = "🚫"
                    lines.append(f"{packet_to_modify[0]} {packet_to_modify[1]}")

                added_options__asci = []
                number = 1
                ignore_extra_packet = False
                for index, line in enumerate(lines):
                    line_split = line.split(" ") # Emoji, Role
                    raw_role_name = " ".join(line_split[1:])
                    role: nextcord.Role = self.get_role(guild, raw_role_name)
                    
                    # Do some modification checks
                    if packet_to_modify:
                        if role and packet_to_modify[1] and role.id == int(packet_to_modify[1]): # If the ids match
                            if ignore_extra_packet:
                                continue
                            if index != (len(lines) - 1): # If this is not the last item in the list
                                ignore_extra_packet = True
                                continue
                    
                    # Manage the apparent name of the role
                    if role:
                        name = (role.mention if bool(json_data["mention_roles"]) else role.name)
                        first_letter = role.name[0].lower()
                        non_formatted_name = role.name
                    else:
                        if not display_errors: continue
                        name = f"⚠️ {raw_role_name} ⚠️"
                        non_formatted_name = f"⚠️ {raw_role_name} ⚠️"
                        first_letter = None
                        problem = True
                    
                    if first_letter:
                        if json_data["type"] == "0":
                            # Letter Reaction Role
                            if not first_letter in added_options__asci: # If this letter has not already been used as a reaction
                                emoji, letter_used = utils.asci_to_emoji(first_letter, fallback_letter=utils.get_next_open_letter(added_options__asci))
                                added_options__asci.append(letter_used)
                            else:
                                nextOpenLetter = utils.get_next_open_letter(added_options__asci)
                                emoji, letter_used = utils.asci_to_emoji(nextOpenLetter)
                                added_options__asci.append(letter_used)
                        elif json_data["type"] == "1":
                            # Number Reaction Role
                            emoji = utils.asci_to_emoji(number)
                            number += 1
                        else:
                            # Custom Reaction Role
                            emoji = line_split[0]
                    else:
                        emoji = "❌"
                        
                    
                    self.added_roles__IDs.append(role.id if role else None)
                    self.added_reactions__emojis.append(emoji)
                    self.added_options__no_format.append(f"{emoji} {non_formatted_name}")
                    return_list.append(f"{emoji} {name}")
                    
                return return_list, problem

            async def add_or_remove_option(self, interaction: Interaction, emoji, role_id, index=None):
                # Get the message
                channel = await interaction.guild.fetch_channel(self.message_info.channel_id)
                message = await channel.fetch_message(self.message_info.message_id)
                            
                # Get all options
                options = message.embeds[0].fields[0].value.split("\n")
                
                # (Add some helping code for deleting)
                if index is not None:
                    emoji = self.added_reactions__emojis[index]
                    role_id = self.added_roles__IDs[index]
                
                # Continue getting the options
                logging.info(f"Emoji: {emoji}, Role ID: {role_id}")
                logging.info(f"Added Reactions: {self.added_reactions__emojis}")
                logging.info(f"Added Roles: {self.added_roles__IDs}")
                formatted_options, problem = self.format_options(interaction.guild, options, packet_to_modify=[emoji, role_id], display_errors=False)
                
                
                # Get new embed
                new_embed = nextcord.Embed(title=message.embeds[0].title, description=message.embeds[0].description, color=message.embeds[0].color)
                new_embed.add_field(name="React for the following roles", value="\n".join(formatted_options), inline=False)
                
                # Update embed
                await message.edit(embed = new_embed)
                
                # Go back
                await self.setup(interaction)
                
                # Update Reactions
                await message.clear_reactions()
                added_emoji_uses = 0
                for index, reaction in enumerate(self.added_reactions__emojis):
                    if reaction == emoji:
                        added_emoji_uses += 1
                        if added_emoji_uses >= 2:
                            # If this is the emoji that we're using now and this isn't the last thing,
                            # We messed up. We gotta remove this guy
                            await self.add_or_remove_option(interaction, emoji, role_id)
                            await interaction.followup.send(embed = nextcord.Embed(title = "Can't Use the Same Emoji", description = "Every Emoji has to be unique. Try again.", color = nextcord.Color.red()), ephemeral = True)
                            return
                    try:
                        await message.add_reaction(emoji = reaction)
                    except (nextcord.errors.Forbidden, nextcord.errors.HTTPException):
                        try:
                            await interaction.followup.send(embed = nextcord.Embed(title = "Emoji Error", description = f"InfiniBot is unable to apply the emoji: \"{reaction}\". If the emoji *is* valid, check that InfiniBot has the permission \"Add Reactions\".", color = nextcord.Color.red()), ephemeral = True)
                        except nextcord.errors.Forbidden:
                            await utils.send_error_message_to_server_owner(interaction.guild, "Add Reactions")
                        await self.add_or_remove_option(interaction, reaction, self.added_roles__IDs[index])
                     
            class AddButton(nextcord.ui.Button):
                def __init__(self, outer, message_info):
                    super().__init__(label = "Add Role")
                    self.outer = outer
                    self.message_info = message_info
                    
                async def callback(self, interaction: Interaction):                     
                    select_options = []
                    available_roles: list[nextcord.Role] = self.outer.available_roles
                    for role in available_roles:
                        select_options.append(nextcord.SelectOption(label=role.name, value=role.id, description=role.id))
                    
                    embed = nextcord.Embed(
                        title="Edit Reaction Role - Edit Options - Add Role", 
                        description="Add a Role to your Reaction Role.\n\n**Don't See Your Role?**\nMake sure InfiniBot has permission to assign it (higher role or administrator).", 
                        color=nextcord.Color.yellow())
                    
                    await ui_components.SelectView(embed, select_options, self.select_view_callback, 
                                                   continue_button_label="Add Role", preserve_order=True).setup(interaction)
                    
                async def select_view_callback(self, interaction: Interaction, selection):
                    if selection == None: 
                        await self.outer.setup(interaction)
                        return
                    
                    json_data = json.loads(self.message_info.json_data)
                    if json_data["type"] == "2": # If this is a custom reaction role,
                        await self.EmojiSelectView(self.outer, selection).setup(interaction)
                        return
                    
                    # Get emoji
                    await self.outer.add_or_remove_option(interaction, None, selection)
                    
                class EmojiSelectView(nextcord.ui.View):
                    def __init__(self, outer, selection):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.selection = selection
                        
                        back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        back_btn.callback = self.back_btn_callback
                        self.add_item(back_btn)
                        
                        next_btn = nextcord.ui.Button(label = "Next", style = nextcord.ButtonStyle.blurple)
                        next_btn.callback = self.next_btn_callback
                        self.add_item(next_btn)
                        
                    async def setup(self, interaction: Interaction):
                        embed = nextcord.Embed(title="Edit Reaction Role - Edit Options - Add Role", 
                                               description="Because this is a custom reaction role, InfiniBot requires an emoji. Therefore, you need to get an emoji into your clipboard (unless you're fancy and know unicode.)\n\n**How?**\nGo to a channel that you don't care about (or InfiniBot's dms) and select the emoji you want. Then, send it, and copy what you sent. Now, come back and click \"Next\".", 
                                               color=nextcord.Color.yellow())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    async def next_btn_callback(self, interaction: Interaction):
                        await interaction.response.send_modal(self.EmojiSelectModal(self.outer, self.selection))
                   
                    class EmojiSelectModal(nextcord.ui.Modal):
                        def __init__(self, outer, selection):
                            super().__init__(title = "Emoji Selection")
                            self.outer = outer
                            self.selection = selection
                            
                            self.emoji_text_input = nextcord.ui.TextInput(label = "Paste the emoji for this option.", max_length = 100)     
                            self.add_item(self.emoji_text_input)
                            
                        async def callback(self, interaction: Interaction):
                            await self.outer.add_or_remove_option(interaction, self.emoji_text_input.value, self.selection)
                              
            class DeleteButton(nextcord.ui.Button):
                def __init__(self, outer, message_info):
                    super().__init__(label = "Delete Role")
                    self.outer = outer
                    self.message_info = message_info
                    
                async def callback(self, interaction: Interaction):                     
                    select_options = []
                    
                    for index, option in enumerate(self.outer.added_options__no_format):
                        select_options.append(nextcord.SelectOption(label=option, value=index))
                    
                    embed = nextcord.Embed(title="Edit Reaction Role - Edit Options - Delete Role", description="Delete a Role from your Reaction Role.", color = nextcord.Color.yellow())
                    await ui_components.SelectView(embed, select_options, self.select_view_callback, continue_button_label="Delete Role", preserve_order=True).setup(interaction)
                    
                async def select_view_callback(self, interaction: Interaction, selection):
                    if selection == None: 
                        await self.outer.setup(interaction)
                        return
                    
                    await self.outer.add_or_remove_option(interaction, None, None, index=int(selection))
                           
        async def callback(self, interaction: Interaction):
            await self.EditOptionsView(self.outer, self.message_info).setup(interaction)
   