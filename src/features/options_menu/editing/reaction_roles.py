import logging
from nextcord import Interaction
import nextcord
import re
import json

from config.server import Server
from components import utils, ui_components
from components.ui_components import CustomModal, CustomView
from features.action_logging import trigger_edit_log

class EditReactionRole(CustomView):
    def __init__(self, message_id: int):
        super().__init__(timeout=None)
        self.message_id = message_id
        
    async def load_buttons(self, interaction: Interaction):
        self.message = await interaction.channel.fetch_message(self.message_id)
        self.server = Server(interaction.guild.id)
        self.message_info = self.server.managed_messages[self.message_id]
        
        self.clear_items()
        
        self.add_item(self.EditTextButton(self))
        self.add_item(self.EditOptionsButton(self, self.message_info))
        
    async def setup(self, interaction: Interaction):
        await self.load_buttons(interaction)
        
        if not utils.feature_is_active(feature="options_menu__editing", guild_id=interaction.guild.id):
            await ui_components.disabled_feature_override(self, interaction)
            return
        
        description = utils.standardize_str_indention(
            """Edit the following reaction role's text and options.

            Utilize InfiniBot's [Generic Replacements](https://cypress-exe.github.io/InfiniBot/docs/messaging/generic-replacements/) to customize your reaction role."""
            )
        
        main_embed = nextcord.Embed(
            title="Edit Reaction Role",
            description=description,
            color=nextcord.Color.yellow()
        )
        
        edit_embed = self.message.embeds[0]
        await interaction.response.edit_message(embeds=[main_embed, edit_embed], view=self)
  
    class EditTextButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label="Edit Text", emoji="✏️")
            self.outer = outer
        
        class EditTextModal(CustomModal):
            def __init__(self, outer):
                super().__init__(title="Edit Text")
                self.outer = outer
                self.title_input = nextcord.ui.TextInput(
                    label="Title", min_length=1, max_length=256,
                    placeholder="Title", default_value=outer.message.embeds[0].title
                )
                self.description_input = nextcord.ui.TextInput(
                    label="Description", min_length=0, max_length=4000,
                    placeholder="Description", default_value=outer.message.embeds[0].description,
                    style=nextcord.TextInputStyle.paragraph, required=False
                )
                self.add_item(self.title_input)
                self.add_item(self.description_input)
                
            async def callback(self, interaction: Interaction):
                before_message = await interaction.channel.fetch_message(self.outer.message.id)
                embed = nextcord.Embed(
                    title=self.title_input.value,
                    description=self.description_input.value,
                    color=before_message.embeds[0].color
                )

                embed = utils.apply_generic_replacements(embed, None, interaction.guild)

                for field in before_message.embeds[0].fields:
                    embed.add_field(name=field.name, value=field.value, inline=field.inline)
                    
                await before_message.edit(embed=embed)
                await self.outer.setup(interaction)
                await trigger_edit_log(
                    interaction.guild, before_message,
                    await interaction.channel.fetch_message(self.outer.message.id),
                    user=interaction.user
                )
        
        async def callback(self, interaction: Interaction):
            await interaction.response.send_modal(self.EditTextModal(self.outer))
  
    class EditOptionsButton(nextcord.ui.Button):
        def __init__(self, outer, message_info):
            super().__init__(label="Edit Options", emoji="🎚️")
            self.outer = outer
            self.message_info = message_info
        
        class EditOptionsView(CustomView):
            def __init__(self, outer, message_info):
                super().__init__(timeout=None)
                self.outer = outer
                self.message_info = message_info
                self.added_reactions__emojis = []
                self.added_roles__IDs = []
                self.added_options__no_format = []
                self.message_id = None
                
                self.add_item(self.AddButton(self, self.message_info))
                self.add_item(self.DeleteButton(self, self.message_info))
                self.back_btn = nextcord.ui.Button(label="Back", style=nextcord.ButtonStyle.gray, row=1)
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                
            async def setup(self, interaction: Interaction):
                try:           
                    channel = await utils.get_channel(self.message_info.channel_id)
                    message = await channel.fetch_message(self.message_info.message_id)       
                except (nextcord.errors.Forbidden, nextcord.errors.NotFound, AttributeError) as e:
                    logging.error(f"Failed to fetch message for reaction role editing: {e}")
                    embed = nextcord.Embed(
                        title="Error",
                        description="Failed to fetch the reaction role message. Please try again later.",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
                    return
                
                options = message.embeds[0].fields[0].value.split("\n")
                self.formatted_options, problem = self.format_options(interaction.guild, options)
                
                embed = nextcord.Embed(
                    title="Edit Reaction Role - Edit Options",
                    description="Add, Manage, and Delete Options.",
                    color=nextcord.Color.yellow()
                )
                embed.add_field(name="Roles", value="\n".join(self.formatted_options))
                
                if problem:
                    embed.add_field(
                        name="⚠️ Issue With One or More Roles ⚠️",
                        value="One or more of your roles no longer exist.",
                        inline=False
                    )
                    
                self.available_roles = [
                    role for role in interaction.guild.roles
                    if role.name != "@everyone" and role.id not in self.added_roles__IDs
                    and utils.role_assignable_by_infinibot(role)
                ]
                
                self.children[0].disabled = len(self.formatted_options) >= 10 or self.available_roles == []
                self.children[1].disabled = len(self.formatted_options) <= 1
                
                try:
                    message = await interaction.response.edit_message(embed=embed, view=self)
                    self.message_id = message.id
                except:
                    await interaction.followup.edit_message(message_id=self.message_id, embed=embed, view=self)

            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
           
            def get_role(self, guild: nextcord.Guild, string: str):
                # Handle already marked invalid roles
                if "⚠️" in string:
                    return None
                    
                # Original regex pattern with improved handling
                match = re.search(r"^(<@&)?(\d+)>?$", string)
                if match:
                    return nextcord.utils.get(guild.roles, id=int(match.group(2)))
                return nextcord.utils.get(guild.roles, name=string) if string else None
           
            def format_options(self, guild: nextcord.Guild, lines: list[str], packet_to_modify=None, display_errors=True):
                self.added_roles__IDs.clear()
                self.added_reactions__emojis.clear()
                self.added_options__no_format.clear()
                return_list = []
                problem = False
                json_data = json.loads(self.message_info.json_data)

                if packet_to_modify:
                    # Only add valid packets for modification
                    if packet_to_modify[1] is not None:  # Only add if we have a role ID
                        lines.append(f"{packet_to_modify[0] or ''} {packet_to_modify[1]}")

                added_options__asci = []
                number = 1
                ignore_extra_packet = False
                for index, line in enumerate(lines):
                    if not line.strip():
                        continue
                        
                    # Split into maximum 2 parts (emoji and role)
                    line_split = line.split(" ", 1)
                    raw_role_name = line_split[-1].strip() if len(line_split) > 1 else ''
                        
                    role = self.get_role(guild, raw_role_name)
                    
                    if packet_to_modify and role and packet_to_modify[1] and role.id == int(packet_to_modify[1]):
                        if ignore_extra_packet or index != (len(lines) - 1):
                            ignore_extra_packet = True
                            continue
                    
                    # Handle invalid roles more carefully
                    first_letter = None
                    if not role:
                        if not display_errors:
                            continue  # Skip invalid roles when not displaying errors
                            
                        # Prevent duplicate warning markers
                        if raw_role_name.startswith("⚠️"):
                            name = raw_role_name
                            non_formatted_name = raw_role_name
                        else:
                            name = f"⚠️ {raw_role_name} ⚠️"
                            non_formatted_name = f"⚠️ {raw_role_name} ⚠️"
                        problem = True
                    else:
                        name = (role.mention if bool(int(json_data["mention_roles"])) else role.name)
                        non_formatted_name = role.name
                        first_letter = role.name[0].lower()

                    if first_letter in added_options__asci:
                        first_letter = None # If we already have an option with this letter, don't use it
                    
                    if json_data["type"] == 0:
                        target_letter = first_letter or utils.get_next_open_letter(added_options__asci)
                        emoji, letter_used = utils.asci_to_emoji(target_letter, fallback_letter=utils.get_next_open_letter(added_options__asci))
                        added_options__asci.append(letter_used)
                    elif json_data["type"] == 1:
                        emoji = utils.asci_to_emoji(number)[0]
                        number += 1
                    else:
                        emoji = line_split[0] if line_split else "❌"

                    self.added_roles__IDs.append(role.id if role else None)
                    self.added_reactions__emojis.append(emoji)
                    self.added_options__no_format.append(f"{emoji} {non_formatted_name}")
                    return_list.append(f"{emoji} {name}")
                    
                return return_list, problem

            async def add_or_remove_option(self, interaction: Interaction, emoji, role_id, index=None):
                try:           
                    channel = await utils.get_channel(self.message_info.channel_id)
                    message = await channel.fetch_message(self.message_info.message_id)       
                except (nextcord.errors.Forbidden, nextcord.errors.NotFound) as e:
                    logging.error(f"Failed to fetch message for reaction role editing: {e}")
                    embed = nextcord.Embed(
                        title="Error",
                        description="Failed to fetch the reaction role message. Please try again later.",
                        color=nextcord.Color.red()
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
                    return
                    
                options = message.embeds[0].fields[0].value.split("\n")
                
                if index is not None:
                    emoji = self.added_reactions__emojis[index]
                    role_id = self.added_roles__IDs[index]
                
                formatted_options, _ = self.format_options(
                    interaction.guild, options,
                    packet_to_modify=[emoji, role_id],
                    display_errors=False
                )
                
                new_embed = nextcord.Embed(
                    title=message.embeds[0].title,
                    description=message.embeds[0].description,
                    color=message.embeds[0].color
                )
                new_embed.add_field(name="React for the following roles", value="\n".join(formatted_options), inline=False)
                await message.edit(embed=new_embed)
                await self.setup(interaction)
                
                await message.clear_reactions()
                for reaction in self.added_reactions__emojis:
                    try:
                        await message.add_reaction(emoji=reaction)
                    except (nextcord.errors.Forbidden, nextcord.errors.HTTPException):
                        await interaction.followup.send(
                            embed=nextcord.Embed(
                                title="Emoji Error",
                                description=f"Failed to add emoji: {reaction}",
                                color=nextcord.Color.red()
                            ),
                            ephemeral=True
                        )
                     
            class AddButton(nextcord.ui.Button):
                def __init__(self, outer, message_info):
                    super().__init__(label="Add Role")
                    self.outer = outer
                    self.message_info = message_info
                    
                async def callback(self, interaction: Interaction):                     
                    select_options = [
                        nextcord.SelectOption(label=role.name, value=role.id, description=str(role.id))
                        for role in self.outer.available_roles
                    ]
                    
                    embed = nextcord.Embed(
                        title="Edit Reaction Role - Edit Options - Add Role", 
                        description="Add a Role to your Reaction Role.\n\n**Don't See Your Role?**\nMake sure InfiniBot has permission to assign it.",
                        color=nextcord.Color.yellow()
                    )
                    
                    await ui_components.SelectView(
                        embed, select_options, self.select_view_callback,
                        continue_button_label="Add Role", preserve_order=True
                    ).setup(interaction)
                    
                async def select_view_callback(self, interaction: Interaction, selection):
                    if not selection:
                        await self.outer.setup(interaction)
                        return
                    
                    json_data = json.loads(self.message_info.json_data)
                    if json_data["type"] == 2:
                        await self.EmojiSelectView(self.outer, selection).setup(interaction)
                    else:
                        await self.outer.add_or_remove_option(interaction, None, selection)

                class EmojiSelectView(CustomView):
                    def __init__(self, outer, selection):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.selection = selection
                        
                        back_btn = nextcord.ui.Button(label="Back", style=nextcord.ButtonStyle.danger)
                        back_btn.callback = self.back_btn_callback
                        self.add_item(back_btn)
                        
                        next_btn = nextcord.ui.Button(label="Next", style=nextcord.ButtonStyle.blurple)
                        next_btn.callback = self.next_btn_callback
                        self.add_item(next_btn)
                        
                    async def setup(self, interaction: Interaction):
                        embed = nextcord.Embed(
                            title="Edit Reaction Role - Edit Options - Add Role", 
                            description="Because this is a custom reaction role, InfiniBot requires an emoji. Therefore, you need to get an emoji into your clipboard (unless you're fancy and know unicode.)\n\n**How?**\nGo to a channel that you don't care about (or InfiniBot's dms) and select the emoji you want. Then, send it, and copy what you sent. Now, come back and click \"Next\".", 
                            color=nextcord.Color.yellow())
                        await interaction.response.edit_message(embed=embed, view=self)
                        
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    async def next_btn_callback(self, interaction: Interaction):
                        await interaction.response.send_modal(self.EmojiSelectModal(self.outer, self.selection))
                   
                    class EmojiSelectModal(CustomModal):
                        def __init__(self, outer, selection):
                            super().__init__(title = "Emoji Selection")
                            self.outer = outer
                            self.selection = selection
                            
                            self.emoji_text_input = nextcord.ui.TextInput(label="Paste the emoji for this option.", max_length=100)     
                            self.add_item(self.emoji_text_input)
                            
                        async def callback(self, interaction: Interaction):
                            await self.outer.add_or_remove_option(interaction, self.emoji_text_input.value, self.selection)
                              
            class DeleteButton(nextcord.ui.Button):
                def __init__(self, outer, message_info):
                    super().__init__(label="Delete Role")
                    self.outer = outer
                    self.message_info = message_info
                    
                async def callback(self, interaction: Interaction):                     
                    select_options = [
                        nextcord.SelectOption(label=option, value=str(idx))
                        for idx, option in enumerate(self.outer.added_options__no_format)
                    ]
                    
                    embed = nextcord.Embed(
                        title="Edit Reaction Role - Edit Options - Delete Role",
                        description="Delete a Role from your Reaction Role.",
                        color=nextcord.Color.yellow()
                    )
                    await ui_components.SelectView(
                        embed, select_options, self.select_view_callback,
                        continue_button_label="Delete Role", preserve_order=True
                    ).setup(interaction)
                    
                async def select_view_callback(self, interaction: Interaction, selection):
                    if selection is None:
                        await self.outer.setup(interaction)
                        return

                    if selection is not None:
                        await self.outer.add_or_remove_option(interaction, None, None, index=int(selection))
                           
        async def callback(self, interaction: Interaction):
            await self.EditOptionsView(self.outer, self.message_info).setup(interaction)