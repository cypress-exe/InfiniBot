from nextcord import Interaction
import nextcord
import re

from components import utils, ui_components
from components.ui_components import CustomModal, CustomView
from features.action_logging import trigger_edit_log
from features.role_messages import RoleMessageButton_Multiple, RoleMessageButton_Single
from features.role_messages import RoleMessageSetup

RoleSelectWizardView = RoleMessageSetup.GetStartedButton.Modal.RoleSelectWizardView

class EditRoleMessage(CustomView):
    def __init__(self, message_id: int):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.guild = None # Unset until load
        
        self.title = None
        self.description = None
        self.color = None
        self.options: list[list[list[int], str, str]] = []
        
    class EditTextButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label="Edit Text", emoji="✏️")
            self.outer = outer
        
        class EditTextModal(CustomModal):
            def __init__(self, outer):
                super().__init__(title="Edit Text")
                self.outer = outer
                
                self.title_input = nextcord.ui.TextInput(
                    label="Title",
                    min_length=1,
                    max_length=256,
                    placeholder="Title",
                    default_value=outer.title
                )
                self.add_item(self.title_input)
                
                self.description_input = nextcord.ui.TextInput(
                    label="Description",
                    min_length=1,
                    max_length=4000,
                    placeholder="Description",
                    default_value=outer.description,
                    style=nextcord.TextInputStyle.paragraph,
                    required=False
                )
                self.add_item(self.description_input)
                
            async def callback(self, interaction: Interaction):
                self.stop()
                self.outer.title = self.title_input.value
                self.outer.description = self.description_input.value
                
                await self.outer.setup(interaction)
        
        async def callback(self, interaction: Interaction):
            await interaction.response.send_modal(self.EditTextModal(self.outer))
        
    class EditColorButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label="Edit Color", emoji="🎨")
            self.outer = outer
            
        class EditColorView(CustomView):
            def __init__(self, outer):
                super().__init__()
                self.outer = outer
                
                original_color = utils.get_string_from_discord_color(self.outer.color)        
                select_options = []
                for option in utils.COLOR_OPTIONS:
                    select_options.append(nextcord.SelectOption(
                        label=option,
                        value=option,
                        default=(option == original_color)
                    ))
                
                self.select = nextcord.ui.Select(
                    placeholder="Choose a color",
                    options=select_options
                )
                
                self.back_btn = nextcord.ui.Button(
                    label="Back",
                    style=nextcord.ButtonStyle.gray
                )
                self.back_btn.callback = self.back_callback

                self.button = nextcord.ui.Button(
                    label="Update Color",
                    style=nextcord.ButtonStyle.blurple
                )
                self.button.callback = self.create_callback
                
                self.add_item(self.select)
                self.add_item(self.back_btn)
                self.add_item(self.button)
                
            async def setup(self, interaction: Interaction):
                description = """Choose what color you would like the role message to be:
                
                **Colors Available**
                """

                description += ui_components.get_colors_available_ui_component()
                description = utils.standardize_str_indention(description)
    
                embed = nextcord.Embed(
                    title="Edit Role Message - Edit Color",
                    description=description,
                    color=nextcord.Color.yellow()
                )
                await interaction.response.edit_message(embed=embed, view=self)
                    
            async def create_callback(self, interaction: Interaction):
                if self.select.values == []:
                    return
                self.selection = self.select.values[0]
                self.stop()
                
                self.outer.color = utils.get_discord_color_from_string(self.selection)
                
                await self.outer.setup(interaction)
    
            async def back_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
    
        async def callback(self, interaction: Interaction):
            await self.EditColorView(self.outer).setup(interaction)
        
    class AddBtn(nextcord.ui.Button):
        def __init__(self, outer, options):
            super().__init__(
                label="Add Option",
                style=nextcord.ButtonStyle.gray,
                disabled=(len(options) >= 25),
                emoji="🔨"
            )
                
            self.outer = outer
            self.options = options
            
        class AddView(CustomView):
            def __init__(self, outer, options, index=None):
                super().__init__(timeout=None)
                self.outer = outer
                self.options = options
                self.index = index
                
                if self.index is None:
                    self.title = None
                    self.description = None
                    self.roles: list[int] = []
                    self.editing = False
                else:
                    self.title = self.options[index][1]
                    self.description = self.options[index][2]
                    self.roles: list[int] = self.options[index][0]
                    self.editing = True
                    
                # Make roles all ints
                self.roles = [int(role) for role in self.roles]
                
                change_text_btn = nextcord.ui.Button(label="Change Text")
                change_text_btn.callback = self.change_text_btn_callback
                self.add_item(change_text_btn)
                
                self.add_role_btn = nextcord.ui.Button(label="Add Role")
                self.add_role_btn.callback = self.add_role_btn_callback
                self.add_item(self.add_role_btn)
                
                self.remove_role_btn = nextcord.ui.Button(label="Remove Role")
                self.remove_role_btn.callback = self.remove_role_btn_callback
                self.add_item(self.remove_role_btn)
                
                self.back_btn = nextcord.ui.Button(
                    label="Back",
                    style=nextcord.ButtonStyle.danger,
                    row=(2 if len(self.outer.options) <= 1 else 1)
                )

                self.back_btn.callback = self.back_btn_callback
                # Only add if this is not the first option
                if len(self.outer.options) > 0:
                    self.add_item(self.back_btn)
                
                self.finish_btn = nextcord.ui.Button(
                    label=("Finish" if not self.editing else "Save"),
                    style=nextcord.ButtonStyle.blurple,
                    row=1)
                self.finish_btn.callback = self.finish_btn_callback
                self.add_item(self.finish_btn)
                
            async def validate_data(self, interaction: Interaction):
                """Make sure you refresh the view after running this"""
                self.addable_roles = []
                for role in interaction.guild.roles:
                    if role.name == "@everyone":
                        continue
                    if role.id in self.roles:
                        continue
                    if utils.role_assignable_by_infinibot(role):
                        self.addable_roles.append(nextcord.SelectOption(
                            label=role.name,
                            value=role.id
                        ))
                        
                self.removable_roles = []
                for role in self.roles:
                    discord_role = interaction.guild.get_role(role)
                    if discord_role:
                        self.removable_roles.append(nextcord.SelectOption(
                            label=discord_role.name,
                            value=role
                        ))
                    else:
                        self.removable_roles.append(nextcord.SelectOption(
                            label="~ Deleted Role ~",
                            value=role,
                            emoji="⚠️"
                        ))
                    
                # Validate buttons
                self.add_role_btn.disabled = len(self.addable_roles) == 0
                self.remove_role_btn.disabled = len(self.removable_roles) <= 1
                
            async def setup(self, interaction: Interaction):
                # Validate Data
                await self.validate_data(interaction)
                
                if len(self.roles) == 0 and not self.editing:
                    # Send the user past this view.
                    await self.add_role_btn_callback(interaction)
                else:
                    if not self.editing:
                        embed = nextcord.Embed(
                            title="Edit Role Message - Add Option",
                            description="You have the option to add more roles or make changes to the text. Here is a mockup of what this option will look like:",
                            color=nextcord.Color.yellow()
                        )
                    else:
                        embed = nextcord.Embed(
                            title="Edit Role Message - Edit Option",
                            description="You have the option to add more roles or make changes to the text. Here is a mockup of what this option will look like:",
                            color=nextcord.Color.yellow()
                        )
                    
                    successful = self.outer.add_field(embed, [self.roles, self.title, self.description])
                    if not successful:
                        self.finish_btn.style = nextcord.ButtonStyle.red
                    else:
                        self.finish_btn.style = nextcord.ButtonStyle.blurple         
                    
                    await interaction.response.edit_message(embed=embed, view=self)
                    
            async def add_role_btn_callback(self, interaction: Interaction):
                # Update Information
                await self.validate_data(interaction)
                if self.add_role_btn.disabled:
                    await self.setup(interaction)
                    return
                
                # Have 2 embeds. One for the first visit, and another for a re-visit
                if len(self.roles) == 0:
                    embed = nextcord.Embed(
                        title="Role Message Creation Wizard - Add Option",
                        description="Please select a role. This choice will be added as one of the options.\n\n**Unable to find a role?**\nIf you are unable to find a role, please ensure that InfiniBot has the necessary permissions to assign roles, such as managing messages and having a higher rank.",
                        color=nextcord.Color.green()
                    )
                else:
                    embed = nextcord.Embed(
                        title="Role Message Creation Wizard - Add Option - Add Role",
                        description="Select a role to be granted when the user chooses this option.\n\n**Unable to find a role?**\nIf you are unable to find a role, please ensure that InfiniBot has the necessary permissions to assign roles, such as managing messages and having a higher rank.",
                        color=nextcord.Color.green()
                    )
                await ui_components.SelectView(
                    embed=embed,
                    options=self.addable_roles,
                    return_command=self.add_role_btn_select_view_callback,
                    placeholder="Choose a Role",
                    continue_button_label="Use Role"
                ).setup(interaction)
                
            async def add_role_btn_select_view_callback(self, interaction: Interaction, value: str):
                if value is None:
                    # User canceled. Return them to us.
                    # Unless they actually came from the original view. If so, let's send them back to that.
                    if self.roles == []:
                        await self.outer.setup(interaction)
                        return
                    else:
                        await self.setup(interaction)
                        return
                    
                if value.isdigit():
                    self.roles.append(int(value))
                
                # Send them to the modal, or just back home
                if self.title is None:
                    await interaction.response.send_modal(self.OptionTitleAndDescriptionModal(self))
                else:
                    await self.setup(interaction)
                
            class OptionTitleAndDescriptionModal(CustomModal):
                def __init__(self, outer):
                    super().__init__(title="Option Settings", timeout=None)
                    self.outer = outer

                    if self.outer.title is None:
                        self.title_input = nextcord.ui.TextInput(
                            label="Please provide a name for that option",
                            max_length=100
                        )
                    else:
                        self.title_input = nextcord.ui.TextInput(
                            label="Option Name",
                            max_length=100,
                            default_value=self.outer.title
                        )
                    self.add_item(self.title_input)
                    
                    if self.outer.description is None:
                        self.description_input = nextcord.ui.TextInput(
                            label="Add a description (optional)",
                            max_length=100,
                            required=False
                        )
                    else:
                        self.description_input = nextcord.ui.TextInput(
                            label="Description (optional)",
                            max_length=100,
                            required=False,
                            default_value=self.outer.description
                        )
                    self.add_item(self.description_input)
                    
                async def callback(self, interaction: Interaction):
                    self.outer.title = self.title_input.value
                    self.outer.description = self.description_input.value
                    
                    await self.outer.setup(interaction)
                                    
            async def change_text_btn_callback(self, interaction: Interaction):
                await interaction.response.send_modal(self.OptionTitleAndDescriptionModal(self))
            
            async def remove_role_btn_callback(self, interaction: Interaction): 
                # Update Information
                await self.validate_data(interaction)
                if self.remove_role_btn.disabled:
                    await self.setup(interaction)
                    return
                
                embed = nextcord.Embed(
                    title="Role Message Creation Wizard - Add Option - Remove Role",
                    description="Choose a role to be removed from this option.",
                    color=nextcord.Color.green()
                )
                await ui_components.SelectView(
                    embed=embed,
                    options=self.removable_roles,
                    return_command=self.remove_role_btn_select_view_callback,
                    placeholder="Choose a Role",
                    continue_button_label="Remove Role"
                ).setup(interaction)
                
            async def remove_role_btn_select_view_callback(self, interaction: Interaction, value: str):
                if value is None:
                    await self.setup(interaction)
                    return
                    
                if value.isdigit() and int(value) in self.roles:
                    self.roles.remove(int(value))
                
                await self.setup(interaction)
                
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                            
            async def finish_btn_callback(self, interaction: Interaction):
                if not self.editing:
                    # Add data to self.outer.options in the form of list[list[int], str, str]
                    self.outer.options.append([self.roles, self.title, self.description])
                else:
                    self.outer.options[self.index] = [self.roles, self.title, self.description]
                
                await self.outer.setup(interaction)
                                
        async def callback(self, interaction: Interaction):
            await self.AddView(self.outer, self.options).setup(interaction)
    
    class EditBtn(nextcord.ui.Button):
        def __init__(self, outer, options):
            super().__init__(label="Edit Option", emoji="⚙️")
            self.outer = outer
            self.options: list[list[list[int], str, str]] = options
            
        async def callback(self, interaction: Interaction):
            # Get the options
            select_options = []
            for index, option in enumerate(self.options):
                select_options.append(nextcord.SelectOption(
                    label=option[1],
                    description=option[2],
                    value=index
                ))
            
            embed = nextcord.Embed(
                title="Edit Role Message - Edit Option",
                description="Choose an option to edit",
                color=nextcord.Color.yellow()
            )
            await ui_components.SelectView(
                embed=embed,
                options=select_options,
                return_command=self.select_view_callback,
                continue_button_label="Edit",
                preserve_order=True
            ).setup(interaction)
        
        async def select_view_callback(self, interaction, selection):
            if selection is None:
                await self.outer.setup(interaction)
                return
                
            # Send them to the editing
            await self.outer.AddBtn.AddView(
                self.outer,
                self.options,
                index=int(selection)
            ).setup(interaction)
     
    class RemoveBtn(nextcord.ui.Button):
        def __init__(self, outer, options):
            super().__init__(
                label="Remove Option",
                disabled=(len(options) <= 1),
                emoji="🚫"
            )
            self.outer = outer
            self.options: list[list[list[int], str, str]] = options
            
        async def callback(self, interaction: Interaction):
            # Get the options
            select_options = []
            for index, option in enumerate(self.options):
                select_options.append(nextcord.SelectOption(
                    label=option[1],
                    description=option[2],
                    value=index
                ))
            
            embed = nextcord.Embed(
                title="Edit Role Message - Remove Option",
                description="Choose an option to remove",
                color=nextcord.Color.yellow()
            )
            await ui_components.SelectView(
                embed=embed,
                options=select_options,
                return_command=self.select_view_callback,
                continue_button_label="Remove",
                preserve_order=True
            ).setup(interaction)
        
        async def select_view_callback(self, interaction, selection):
            if selection is None:
                await self.outer.setup(interaction)
                return
                
            self.outer.options.pop(int(selection))
            
            await self.outer.setup(interaction)
        
    class EditModeBtn(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label="Change Mode", row=1, emoji="🎚️")
            self.outer = outer
            
        class MultiOrSingleSelectView(CustomView):
            def __init__(self, outer):
                super().__init__(timeout=None)
                self.outer = outer
                
                options = [
                    nextcord.SelectOption(
                        label="Single",
                        description="Members can only select one option",
                        value="Single",
                        default=(self.outer.mode == "Single")
                    ),
                    nextcord.SelectOption(
                        label="Multiple",
                        description="Members can select multiple options.",
                        value="Multiple",
                        default=(self.outer.mode == "Multiple")
                    )
                ]
                
                self.select = nextcord.ui.Select(
                    options=options,
                    placeholder="Choose a Mode"
                )
                self.add_item(self.select)
                
                self.back_btn = nextcord.ui.Button(
                    label="Back",
                    style=nextcord.ButtonStyle.danger,
                    row=1
                ) 
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                
                self.create_btn = nextcord.ui.Button(
                    label="Change Mode",
                    style=nextcord.ButtonStyle.blurple
                )
                self.create_btn.callback = self.create_btn_callback
                self.add_item(self.create_btn)
                
            async def setup(self, interaction: Interaction):
                embed = nextcord.Embed(
                    title="Edit Role Message - Change Mode",
                    description="Decide whether you want members to have the option to select multiple choices or just one.",
                    color=nextcord.Color.yellow()
                )
                await interaction.response.edit_message(embed=embed, view=self)
            
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            async def create_btn_callback(self, interaction: Interaction):
                values = self.select.values
                if values == []:
                    return
                
                value = values[0]
                
                self.outer.mode = value
                
                await self.outer.setup(interaction)
            
        async def callback(self, interaction: Interaction):
            await self.MultiOrSingleSelectView(self.outer).setup(interaction)
       
    async def load(self, interaction: Interaction):
        self.message = await utils.get_message(interaction.channel, self.message_id)
        if self.message is None:
            # Message no longer exists or was recently not found
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Message Not Found",
                    description="The role message could not be found. It may have been deleted.",
                    color=nextcord.Color.red()
                ),
                ephemeral=True
            )
            return
        self.guild = interaction.guild
        
        if (self.title is None and self.description is None 
                and self.color is None and self.options == []):
            self.title = self.message.embeds[0].title
            self.description = self.message.embeds[0].description
            self.color = self.message.embeds[0].color
            
            # Get options
            self.options = []
            for field in self.message.embeds[0].fields:
                name = field.name
                description = "\n".join(field.value.split("\n")[:-1])
                roles = self.extract_ids(field.value.split("\n")[-1])
                self.options.append([roles, name, description])
                
            # Get Mode
            self.mode = "Multiple"
            for component in self.message.components:
                if isinstance(component, nextcord.components.ActionRow):
                    for item in component.children:
                        if isinstance(item, nextcord.components.Button):
                            if item.custom_id == "get_roles":
                                self.mode = "Multiple"
                                break
                            elif item.custom_id == "get_role":
                                self.mode = "Single"
                                break
            self.current_mode = self.mode
        
        self.clear_items()
            
        # Load buttons   
        edit_text_btn = self.EditTextButton(self)
        self.add_item(edit_text_btn)
        
        edit_color_btn = self.EditColorButton(self)
        self.add_item(edit_color_btn)
        
        self.add_btn = self.AddBtn(self, self.options)
        self.add_item(self.add_btn)
        
        self.edit_btn = self.EditBtn(self, self.options)
        self.add_item(self.edit_btn)
        
        self.remove_btn = self.RemoveBtn(self, self.options)
        self.add_item(self.remove_btn)
        
        edit_mode_btn = self.EditModeBtn(self)
        self.add_item(edit_mode_btn)
        
        self.confirm_btn = nextcord.ui.Button(
            label="Confirm Edits",
            style=nextcord.ButtonStyle.blurple,
            row=1
        )
        self.confirm_btn.callback = self.confirm_btn_callback
        self.add_item(self.confirm_btn)
        
    async def setup(self, interaction: Interaction):
        await self.load(interaction)

        description = utils.standardize_str_indention(
            """Edit your role message by making to the text, color, and options. Once finished, click on \"Confirm Edits\"

            Utilize InfiniBot's [Generic Replacements](https://cypress-exe.github.io/InfiniBot/docs/messaging/generic-replacements/) to customize your role message."""
            )
        
        embed = nextcord.Embed(
            title="Edit Role Message",
            description=description,
            color=nextcord.Color.yellow()
        )
        
        # Create a mockup of the embed
        role_message_embed, errors = self.create_embed(
            self.title,
            self.description,
            self.color,
            self.options
        )
        self.confirm_btn.disabled = errors
        
        embeds = [embed, role_message_embed]
        
        # Give warning about mode if needed
        if self.mode != self.current_mode:
            warning_embed = nextcord.Embed(
                title="Warning: Mode Not Saved",
                description="Be sure to Confirm Edits to save your mode.",
                color=nextcord.Color.red()
            )
            embeds.append(warning_embed)
        
        await interaction.response.edit_message(embeds=embeds, view=self)
        
    def create_embed(self, title, description, color, options):
        """Create the role message embed.

        :param title: The title of the embed
        :type title: str
        :param description: The description of the embed
        :type description: str
        :param color: The color of the embed
        :type color: nextcord.Color
        :param options: The options to add to the embed
        :type options: list[list[list[int], str, str]]
        :return: The created embed
        :rtype: nextcord.Embed
        """
        embed = nextcord.Embed(title=title, description=description, color=color)

        embed = utils.apply_generic_replacements(embed, None, self.guild)

        errors = False
        for option in options:
            if not self.add_field(embed, option):
                errors = True

        return embed, errors
            
    def add_field(self, embed: nextcord.Embed, option_info):
        """Add a field to the embed based on option info.

        :param embed: The embed to add the field to
        :type embed: nextcord.Embed
        :param option_info: The option info in the form of [list[int], str, str]
        :type option_info: list[list[int], str, str]
        :return: True if field was added successfully, False if there was an error
        :rtype: bool
        """
        mentions = [f"<@&{role}>" for role in option_info[0]]
        if len(mentions) > 1:
            mentions[-1] = f"and {mentions[-1]}"
        roles = ", ".join(mentions)
            
        title = option_info[1]
        description = option_info[2]
        
        spacer = ("\n" if description != "" else "")

        value = f"{description}{spacer}> Grants {roles}"
        if len(value) > 1024: # 1024 is the max length for an embed field value
            embed.add_field(name=title, value="```⚠️ CRITICAL: Too many roles to display. Option must be edited to reduce number of roles.```", inline=False)
            return False
        
        embed.add_field(name=title, value=value, inline=False)
        return True
    
    def extract_ids(self, input_string):
        pattern = r"<@&(\d+)>"
        matches = re.findall(pattern, input_string)
        return matches
    
    async def disable_view(self, interaction: Interaction):
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                child.disabled = True
                
        await interaction.response.edit_message(view=self, delete_after=1.0)
    
    async def confirm_btn_callback(self, interaction: Interaction):
        role_message_embed, _ = self.create_embed( # Ignore errors here; they were handled earlier
            self.title,
            self.description,
            self.color,
            self.options
        )
        
        await self.disable_view(interaction)
        
        if self.mode == "Single":
            view = RoleMessageButton_Single()
        else:
            view = RoleMessageButton_Multiple()

        # Get message from discord before edit
        original_message = await utils.get_message(self.message.channel, self.message.id)
        if original_message is None:
            # Message no longer exists, can't proceed with edit
            await interaction.followup.send(
                embed=nextcord.Embed(
                    title="Edit Failed",
                    description="The original message could not be found. It may have been deleted.",
                    color=nextcord.Color.red()
                ),
                ephemeral=True
            )
            return
        
        edited_message = await self.message.edit(embed=role_message_embed, view=view)

        def embeds_are_similar(embed1, embed2):
            args = ["title", "description", "color"]
            for arg in args:
                if getattr(embed1, arg) != getattr(embed2, arg):
                    return False
                
            for field1, field2 in zip(embed1.fields, embed2.fields):
                if field1.name != field2.name or field1.value != field2.value:
                    return False
                
            return True

        if not embeds_are_similar(original_message.embeds[0], edited_message.embeds[0]): # If the embeds are different
            await trigger_edit_log(
                self.message.guild,
                original_message,
                edited_message,
                user=interaction.user
            )
                            
    async def callback(self, interaction: Interaction):
        await self.RoleSelectWizardView(
            self.title_input.value,
            self.description_input.value
        ).setup(interaction)