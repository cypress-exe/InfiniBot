from nextcord import Interaction
import nextcord
import re

from components import utils, ui_components
from config.server import Server

class RoleMessageButton_Single(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
    
    class View(nextcord.ui.View):
        def __init__(self, user: nextcord.Member, message: nextcord.Message):
            super().__init__(timeout = None)
            self.message = message
            self.available_roles = []
            
            user_role_ids = [role.id for role in user.roles if role.name != "@everyone"]
            
            options_selected = False
            options = []
            for field in self.message.embeds[0].fields:
                description = "\n".join(field.value.split("\n")[:-1])
                roles = self.extract_ids(field.value.split("/n")[-1])
                self.add_available_roles(roles)
                
                # Check if the user has the roles
                selected = False
                for index, role in enumerate(roles):
                    if not int(role) in user_role_ids:
                        break
                    else:
                        if index == (len(roles) - 1): # If this is the last role to check
                            if not options_selected:
                                selected = True
                                options_selected = True
                            break
                
                options.append(nextcord.SelectOption(label=field.name, description=description, value="|".join(roles), default=selected))
                
            self.select = nextcord.ui.Select(placeholder="Choose a Role", min_values=0, options=options)
            self.select.callback = self.select_callback
            self.add_item(self.select)
                
        def extract_ids(self, input_string):
            pattern = r"<@&(\d+)>"
            matches = re.findall(pattern, input_string)
            return matches
            
        def add_available_roles(self, roles_list):
            for role in roles_list:
                if int(role) not in self.available_roles:
                    self.available_roles.append(int(role))
            
        async def setup(self, interaction: Interaction):
            await interaction.response.send_message(view = self, ephemeral = True)
            
        async def select_callback(self, interaction: Interaction):
            selection = self.select.values
            selected_roles = []
            for option in selection:
                for role in option.split("|"):
                    selected_roles.append(int(role))
                    
            # Get the roles
            roles_add = []
            roles_remove = []
            for role in self.available_roles:
                if role in selected_roles:
                    roles_add.append(interaction.guild.get_role(int(role)))
                else:
                    roles_remove.append(interaction.guild.get_role(int(role)))
                    
            error = False
            try:
                await interaction.user.add_roles(*roles_add)
                await interaction.user.remove_roles(*roles_remove)
            except nextcord.errors.Forbidden:
                error = True
                
            embed = nextcord.Embed(title = "Modified Roles", color = nextcord.Color.green())
            if error: embed.description = "Warning: An error occurred with one or more roles. Please notify server admins."
            
            await interaction.response.edit_message(embed=embed, view=None, delete_after=2.0)
    
    @nextcord.ui.button(label = "Get Role", style = nextcord.ButtonStyle.blurple, custom_id = "get_role")
    async def event(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        message = interaction.message
        await self.View(interaction.user, message).setup(interaction)

class RoleMessageButton_Multiple(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
    
    class View(nextcord.ui.View):
        def __init__(self, user: nextcord.Member, message: nextcord.Message):
            super().__init__(timeout = None)
            self.message = message
            self.available_roles = []
            
            user_role_ids = [role.id for role in user.roles if role.name != "@everyone"]
            
            options = []
            for field in self.message.embeds[0].fields:
                description = "\n".join(field.value.split("\n")[:-1])
                roles = self.extract_ids(field.value.split("/n")[-1])
                self.add_available_roles(roles)
                
                # Check if the user has the roles
                selected = False
                for index, role in enumerate(roles):
                    if not int(role) in user_role_ids:
                        break
                    else:
                        if index == (len(roles) - 1): # If this is the last role to check
                            selected = True
                            break
                
                options.append(nextcord.SelectOption(label=field.name, description=description, value="|".join(roles), default=selected))
                
            self.select = nextcord.ui.Select(placeholder="Choose Roles", min_values=0, max_values=len(options), options=options)
            self.select.callback = self.select_callback
            self.add_item(self.select)
                
        def extract_ids(self, input_string):
            pattern = r"<@&(\d+)>"
            matches = re.findall(pattern, input_string)
            return matches
            
        def add_available_roles(self, rolesList):
            for role in rolesList:
                if int(role) not in self.available_roles:
                    self.available_roles.append(int(role))
            
        async def setup(self, interaction: Interaction):
            await interaction.response.send_message(view = self, ephemeral = True)
            
        async def select_callback(self, interaction: Interaction):
            selection = self.select.values
            selected_roles = []
            for option in selection:
                for role in option.split("|"):
                    selected_roles.append(int(role))
                    
            # Get the roles
            roles_add = []
            roles_remove = []
            for role in self.available_roles:
                if role in selected_roles:
                    roles_add.append(interaction.guild.get_role(int(role)))
                else:
                    roles_remove.append(interaction.guild.get_role(int(role)))
                    
            error = False
            try:
                await interaction.user.add_roles(*roles_add)
                await interaction.user.remove_roles(*roles_remove)
            except nextcord.errors.Forbidden:
                error = True
                
            embed = nextcord.Embed(title="Modified Roles", color=nextcord.Color.green())
            if error: embed.description = "Warning: An error occurred with one or more roles. Please notify server admins."
            
            await interaction.response.edit_message(embed=embed, view=None, delete_after=2.0)
    
    @nextcord.ui.button(label = "Get Roles", style = nextcord.ButtonStyle.blurple, custom_id = "get_roles")
    async def event(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        message = interaction.message
        await self.View(interaction.user, message).setup(interaction)

class RoleMessageSetup(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        nevermind_btn = self.NevermindButton(self)
        self.add_item(nevermind_btn)
        
        get_started_btn = self.GetStartedButton()
        self.add_item(get_started_btn)
        
    async def setup(self, interaction: Interaction):
        if utils.feature_is_active(guild_id=interaction.guild.id, feature="role_messages"):
            embed = nextcord.Embed(
                title="Role Message Creation Wizard",
                description="We will guide you through the process of creating a custom message that enables \
                users to assign themselves roles.\n★ Unlike reaction roles, this method utilizes a modern \
                interface.\n\n**Click on \"Get Started\" to initiate the process!**",
                color = nextcord.Color.green())
            await interaction.response.send_message(embed=embed, view=self, ephemeral=True)
        else:
            await interaction.response.send_message(embed=nextcord.Embed(
                title="Role Messages Disabled", 
                description="Role Messages have been disabled by the developers of InfiniBot. This is likely \
                due to an critical instability with it right now. It will be re-enabled shortly after the issue \
                has been resolved.", 
                color=nextcord.Color.red()), ephemeral=True)
        
    class NevermindButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Nevermind", style = nextcord.ButtonStyle.gray)
            self.outer = outer
            
        async def callback(self, interaction: Interaction):
            for child in self.outer.children:
                if isinstance(child, nextcord.ui.Button):
                    child.disabled = True
                    
            await interaction.response.edit_message(view = self.outer)
        
    class GetStartedButton(nextcord.ui.Button):
        def __init__(self):
            super().__init__(label = "Get Started", style = nextcord.ButtonStyle.blurple)
            
        class Modal(nextcord.ui.Modal):
            def __init__(self):
                super().__init__(title = "Role Message Creation Wizard", timeout = None)
                
                self.title_input = nextcord.ui.TextInput(label="To begin, please add a Title", max_length=256)
                self.add_item(self.title_input)
                
                self.description_input = nextcord.ui.TextInput(label="And then a Description (if you want)", 
                                                               style=nextcord.TextInputStyle.paragraph, 
                                                               max_length=4000,
                                                               required=False)
                self.add_item(self.description_input)
                
            class RoleSelectWizardView(nextcord.ui.View):
                def __init__(self, title, description):
                    super().__init__(timeout = None)
                    self.title = title
                    self.description = description
                    self.color = nextcord.Color.teal()
                    self.options: list[list[list[int], str, str]] = []
                    
                    edit_text_btn = self.EditTextButton(self)
                    self.add_item(edit_text_btn)
                    
                    edit_color_btn = self.EditColorButton(self)
                    self.add_item(edit_color_btn)
                    
                    # Also known as "next" on the first time
                    self.add_btn = self.AddBtn(self, self.options)
                    self.add_item(self.add_btn)
                    
                    self.edit_btn = self.EditBtn(self, self.options)
                    
                    self.remove_btn = self.RemoveBtn(self, self.options)
                    
                    self.finish_btn = self.FinishBtn(self)
                    
                class EditTextButton(nextcord.ui.Button):
                    def __init__(self, outer):
                        super().__init__(label="Edit Text", emoji="✏️")
                        self.outer = outer
                    
                    class EditTextModal(nextcord.ui.Modal):
                        def __init__(self, outer):
                            super().__init__(title="Edit Text")
                            self.outer = outer
                            
                            self.title_input = nextcord.ui.TextInput(
                                label="Title", min_length=1, max_length=256, 
                                placeholder="Title", default_value=outer.title)
                            self.add_item(self.title_input)
                            
                            self.description_input = nextcord.ui.TextInput(
                                label="Description", max_length=4000, 
                                placeholder="Description", default_value=outer.description, 
                                style=nextcord.TextInputStyle.paragraph, required=False)
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
                        super().__init__(label = "Edit Color", emoji = "🎨")
                        self.outer = outer
                        
                    class EditColorView(nextcord.ui.View):
                        def __init__(self, outer):
                            super().__init__()
                            self.outer = outer
                            
                            original_color = utils.get_string_from_discord_color(self.outer.color)        
                            select_options = []
                            for option in utils.COLOR_OPTIONS:
                                select_options.append(nextcord.SelectOption(label=option, value=option, default=(option is original_color)))
                            
                            self.select = nextcord.ui.Select(placeholder="Choose a color", options=select_options)
                            
                            self.back_btn = nextcord.ui.Button(label="Back", style=nextcord.ButtonStyle.gray)
                            self.back_btn.callback = self.back_callback

                            self.create_btn = nextcord.ui.Button(label="Update Color", style=nextcord.ButtonStyle.blurple)
                            self.create_btn.callback = self.create_callback
                            
                            self.add_item(self.select)
                            self.add_item(self.back_btn)
                            self.add_item(self.create_btn)
                            
                        async def setup(self, interaction: Interaction):
                            description = f"""Choose what color you would like the role message to be:
                            
                            **Colors Available**
                            """
                            description += ui_components.get_colors_available_ui_component()
                            description = utils.standardize_str_indention(description)
                
                            embed = nextcord.Embed(title="Role Message Creation Wizard - Edit Color", description=description, color=nextcord.Color.green())
                            await interaction.response.edit_message(embed=embed, view =self)
                                
                        async def create_callback(self, interaction: Interaction):
                            if self.select.values == []: return
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
                        if options == []:    
                            super().__init__(label="Next", style=nextcord.ButtonStyle.blurple)
                        else:
                            super().__init__(label="Add Option", style=nextcord.ButtonStyle.gray, disabled=(len(options) >= 25), emoji="🔨")
                            
                        self.outer = outer
                        self.options = options
                        
                    class AddView(nextcord.ui.View):
                        def __init__(self, outer, options, index = None):
                            super().__init__(timeout = None)
                            self.outer = outer
                            self.options = options
                            self.index = index
                            
                            if self.index == None:
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
                            
                            self.back_btn = nextcord.ui.Button(label="Back", style=nextcord.ButtonStyle.danger, row=(2 if len(self.outer.options) <= 1 else 1))
                            self.back_btn.callback = self.back_btn_callback
                            # Only add if this is not the first option
                            if len(self.outer.options) > 0:
                                self.add_item(self.back_btn)
                            
                            self.finish_btn = nextcord.ui.Button(label=("Finish" if not self.editing else "Save"), style=nextcord.ButtonStyle.blurple, row=1)
                            self.finish_btn.callback = self.finish_btn_callback
                            self.add_item(self.finish_btn)
                            
                        async def validate_data(self, interaction: Interaction):
                            """Make sure you refresh the view after running this"""
                            self.addable_roles = []
                            for role in interaction.guild.roles:
                                if role.name == "@everyone": continue
                                if role.id in self.roles: continue
                                if utils.role_assignable_by_infinibot(role):
                                    self.addable_roles.append(nextcord.SelectOption(label=role.name, value=role.id))
                                    
                            self.remove_roles = []
                            for role in self.roles:
                                discord_role = interaction.guild.get_role(role)
                                if discord_role:
                                    self.remove_roles.append(nextcord.SelectOption(label=discord_role.name, value=role))
                                else:
                                    self.remove_roles.append(nextcord.SelectOption(label="~ Deleted Role ~", value=role, emoji="⚠️"))
                                
                            # Validate buttons
                            self.add_role_btn.disabled = len(self.addable_roles) == 0
                            self.remove_role_btn.disabled = len(self.remove_roles) <= 1
                            
                        async def setup(self, interaction: Interaction):
                            # Validate Data
                            await self.validate_data(interaction)
                            
                            if len(self.roles) == 0 and not self.editing:
                                # Send the user past this view.
                                await self.add_role_btn_callback(interaction)
                            else:
                                if not self.editing:
                                    embed = nextcord.Embed(title="Role Message Creation Wizard - Add Option", 
                                                           description="You have the option to add more roles or \
                                                           make changes to the text. Here is a mockup of what this \
                                                           option will look like:", color=nextcord.Color.green())
                                else:
                                    embed = nextcord.Embed(title="Role Message Creation Wizard - Edit Option", 
                                                           description="You have the option to add more roles or make \
                                                           changes to the text. Here is a mockup of what this option \
                                                           will look like:", color=nextcord.Color.green())
                                
                                self.outer.add_field(embed, [self.roles, self.title, self.description])
                                
                                await interaction.response.edit_message(embed=embed, view=self)
                                
                        async def add_role_btn_callback(self, interaction: Interaction):
                            # Update Information
                            await self.validate_data(interaction)
                            if self.add_role_btn.disabled:
                                await self.setup(interaction)
                                return
                            
                            # Have 2 embeds. One for the first visit, and another for a re-visit
                            if len(self.roles) == 0:
                                embed = nextcord.Embed(title="Role Message Creation Wizard - Add Option", 
                                                       description="Please select a role. This choice will be \
                                                       added as one of the options.\n\n**Unable to find a role?**\
                                                       \nIf you are unable to find a role, please ensure that \
                                                       InfiniBot has the necessary permissions to assign roles, \
                                                       such as managing messages and having a higher rank.", 
                                                       color=nextcord.Color.green())
                            else:
                                embed = nextcord.Embed(title="Role Message Creation Wizard - Add Option - Add Role", 
                                                       description="Select a role to be granted when the user chooses \
                                                       this option.\n\n**Unable to find a role?**\nIf you are unable \
                                                       to find a role, please ensure that InfiniBot has the necessary \
                                                       permissions to assign roles, such as managing messages and having \
                                                       a higher rank.", 
                                                       color=nextcord.Color.green())
                            await ui_components.SelectView(
                                embed=embed, 
                                options=self.addable_roles, 
                                return_command=self.add_role_btn_select_view_callback, 
                                placeholder="Choose a Role", 
                                continue_button_label="Use Role").setup(interaction)
                            
                        async def add_role_btn_select_view_callback(self, interaction: Interaction, value: str):
                            if value == None:
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
                            if self.title == None:
                                await interaction.response.send_modal(self.OptionTitleAndDescriptionModal(self))
                            else:
                                await self.setup(interaction)
                            
                        class OptionTitleAndDescriptionModal(nextcord.ui.Modal):
                            def __init__(self, outer):
                                super().__init__(title = "Option Settings", timeout = None)
                                self.outer = outer

                                if self.outer.title == None:
                                    self.title_input = nextcord.ui.TextInput(label="Please provide a name for that option", max_length=100)
                                else:
                                    self.title_input = nextcord.ui.TextInput(label="Option Name", max_length=100, default_value=self.outer.title)
                                self.add_item(self.title_input)
                                
                                if self.outer.description == None:
                                    self.description_input = nextcord.ui.TextInput(label="Add a description (optional)", max_length=100, required=False)
                                else:
                                    self.description_input = nextcord.ui.TextInput(label="Description (optional)", max_length=100, 
                                                                                  required=False, default_value=self.outer.description)
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
                            
                            embed = nextcord.Embed(title = "Role Message Creation Wizard - Add Option - Remove Role", description = "Choose a role to be removed from this option.", color = nextcord.Color.green())
                            await ui_components.SelectView(
                                embed=embed, 
                                options=self.remove_roles,
                                return_command=self.remove_role_btn_select_view_callback, 
                                placeholder="Choose a Role",
                                continue_button_label="Remove Role").setup(interaction)
                            
                        async def remove_role_btn_select_view_callback(self, interaction: Interaction, value: str):
                            if value == None:
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
                        super().__init__(label = "Edit Option", emoji = "⚙️")
                        self.outer = outer
                        self.options: list[list[list[int], str, str]] = options
                        
                    async def callback(self, interaction: Interaction):
                        # Get the options
                        select_options = []
                        for index, option in enumerate(self.options):
                            select_options.append(nextcord.SelectOption(label=option[1], description=option[2], value=index))
                        
                        embed = nextcord.Embed(title = "Role Message Creation Wizard - Edit Option", description = "Choose an option to edit", color = nextcord.Color.green())
                        await ui_components.SelectView(
                            embed=embed, 
                            options=select_options, return_command=self.select_view_callback,
                            continue_button_label="Edit", 
                            preserve_order=True).setup(interaction)
                    
                    async def select_view_callback(self, interaction, selection):
                        if selection == None:
                            await self.outer.setup(interaction)
                            return
                            
                        # Send them to the editing
                        await self.outer.AddBtn.AddView(self.outer, self.options, index = int(selection)).setup(interaction)
      
                class RemoveBtn(nextcord.ui.Button):
                    def __init__(self, outer, options):
                        super().__init__(label="Remove Option", disabled=(len(options) <= 1), emoji="🚫")
                        self.outer = outer
                        self.options: list[list[list[int], str, str]] = options
                        
                    async def callback(self, interaction: Interaction):
                        # Get the options
                        select_options = []
                        for index, option in enumerate(self.options):
                            select_options.append(nextcord.SelectOption(label=option[1], description=option[2], value=index))
                        
                        embed = nextcord.Embed(title="Edit Role Message - Remove Option", description="Choose an option to remove", color=nextcord.Color.yellow())
                        await ui_components.SelectView(
                            embed=embed,
                            options=select_options,
                            return_command=self.select_view_callback,
                            continue_button_label="Remove",
                            preserve_order=True
                        ).setup(interaction)
                    
                    async def select_view_callback(self, interaction, selection):
                        if selection == None:
                            await self.outer.setup(interaction)
                            return
                            
                        self.outer.options.pop(int(selection))
                        
                        await self.outer.setup(interaction)
  
                class FinishBtn(nextcord.ui.Button):
                    def __init__(self, outer):
                        super().__init__(label="Finish", style=nextcord.ButtonStyle.blurple, row=1, emoji="🏁")
                        self.outer = outer
                        
                    class MultiOrSingleSelectView(nextcord.ui.View):
                        def __init__(self, outer):
                            super().__init__(timeout = None)
                            self.outer = outer
                            
                            options = [
                                nextcord.SelectOption(
                                    label="Single",
                                    description="Members can only select one option",
                                    value="Single"
                                ),
                                nextcord.SelectOption(
                                    label="Multiple",
                                    description="Members can select multiple options.",
                                    value="Multiple"
                                )
                            ]
                            self.select = nextcord.ui.Select(
                                options=options,
                                placeholder="Choose a Mode"
                            )
                            self.add_item(self.select)

                            self.create_btn = nextcord.ui.Button(
                                label="Create Role Select",
                                style=nextcord.ButtonStyle.blurple
                            )
                            self.create_btn.callback = self.create_btn_callback
                            self.add_item(self.create_btn)
                            
                        async def setup(self, interaction: Interaction):
                            embed = nextcord.Embed(
                                title="Role Message Creation Wizard - Finish",
                                description="Finally, decide whether you want members to have the \
                                    option to select multiple choices or just one.",
                                color=nextcord.Color.green()
                            )
                            await interaction.response.edit_message(embed=embed, view=self)
                        
                        async def create_btn_callback(self, interaction: Interaction):
                            values = self.select.values
                            if values == []:
                                return
                            
                            value = values[0]
                            
                            if value == "Single":
                                view = RoleMessageButton_Single()
                            else:
                                view = RoleMessageButton_Multiple()
                            
                            # Create Role Select
                            role_message_embed = self.outer.create_embed(
                                self.outer.title, self.outer.description, self.outer.color, self.outer.options)
                    
                            await self.outer.disable_view(interaction)
                            
                            message = await interaction.channel.send(embed=role_message_embed, view=view)
                            
                            # Catalog Message
                            server = Server(interaction.guild.id)
                            server.managed_messages.add(
                                message_id=message.id,
                                channel_id=interaction.channel.id,
                                author_id=interaction.user.id,
                                message_type="reaction_role",
                                json_data=None
                            )
                        
                    async def callback(self, interaction: Interaction):
                        await self.MultiOrSingleSelectView(self.outer).setup(interaction)
            
                async def setup(self, interaction: Interaction):
                    self.validate_buttons()
                    
                    # Create two embeds depending on whether this is the first time
                    description = (
                        "Excellent work! Your message is below. If you are satisfied with it, click on \"{button_text}\".\n\n"
                        "Alternatively, you can make edits to the text{edit_options}."
                    )
                    if len(self.options) == 0:
                        button_text = "Next"
                        edit_options = " and color"
                    else:
                        button_text = "Finish"
                        edit_options = ", color, and options"

                    embed = nextcord.Embed(
                        title="Role Message Creation Wizard",
                        description=description.format(button_text=button_text, edit_options=edit_options),
                        color=nextcord.Color.green()
                    )
                    
                    # Create a mockup of the embed
                    role_message_embed = self.create_embed(self.title, self.description, self.color, self.options)
                    
                    await interaction.response.edit_message(embeds=[embed, role_message_embed], view=self)
                    
                def validate_buttons(self):
                    """Be sure to update the view after running this"""
                    if len(self.options) > 0:
                        self.add_btn.__init__(self, self.options)
                        self.remove_btn.__init__(self, self.options)
                        if self.edit_btn not in self.children:
                            self.add_item(self.edit_btn)
                        if self.remove_btn not in self.children:
                            self.add_item(self.remove_btn)
                        if self.finish_btn not in self.children:
                            self.add_item(self.finish_btn)
                    
                def create_embed(self, title, description, color, options):
                    embed = nextcord.Embed(title=title, description=description, color=color)
                    for option in options:
                        self.add_field(embed, option)

                    return embed
                        
                def add_field(self, embed: nextcord.Embed, option_info):
                    mentions = [f"<@&{role}>" for role in option_info[0]]
                    if len(mentions) > 1:
                        mentions[-1] = f"and {mentions[-1]}"
                    roles = ", ".join(mentions)
                        
                    title = option_info[1]
                    description = option_info[2]
                    
                    spacer = ("\n" if description != "" else "")
                    
                    embed.add_field(name=title, value=f"{description}{spacer}> Grants {roles}", inline=False)
                
                async def disable_view(self, interaction: Interaction):
                    for child in self.children:
                        if isinstance(child, nextcord.ui.Button):
                            child.disabled = True
                            
                    await interaction.response.edit_message(view=self, delete_after=1.0)
                                     
            async def callback(self, interaction: Interaction):
                await self.RoleSelectWizardView(self.title_input.value, self.description_input.value).setup(interaction)
            
        async def callback(self, interaction: Interaction):
            await interaction.response.send_modal(self.Modal())
      
async def run_role_message_command(interaction: Interaction):
    if await utils.user_has_config_permissions(interaction):
        await RoleMessageSetup().setup(interaction)