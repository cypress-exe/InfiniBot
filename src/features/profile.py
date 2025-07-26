import nextcord
from nextcord import Interaction

from components import ui_components, utils
from components.ui_components import CustomModal, CustomView
from config.member import Member


class Profile(CustomView):
    """
    View for the profile command.
    """
    def __init__(self):
        super().__init__(timeout = None)
        
        level_card_btn = self.LevelCardButton(self)
        self.add_item(level_card_btn)
        
        join_card_btn = self.JoinCardButton(self)
        self.add_item(join_card_btn)
        
        settings_btn = self.SettingsButton(self)
        self.add_item(settings_btn)
       
    async def setup(self, interaction: Interaction):
        for child in self.children: del child
        self.__init__()

        if not utils.feature_is_active(feature = "profile"):
            await ui_components.disabled_feature_override(self, interaction)
            return
    
        description = f"""Welcome to your InfiniBot Profile! Choose a setting:
        
        View the [help docs](https://cypress-exe.github.io/InfiniBot/docs/core-features/profile/) for more information."""
        
        # On Mobile, extra spaces cause problems. We'll get rid of them here:
        description = utils.standardize_str_indention(description)
        
        
        embed = nextcord.Embed(title = "Profile", description = description, color = nextcord.Color.blurple())
        try: await interaction.response.edit_message(embed = embed, view = self)
        except: await interaction.response.send_message(embed = embed, view = self, ephemeral=True)
 
    class LevelCardButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Level-Up Card", style = nextcord.ButtonStyle.gray)
            self.outer = outer
            
        class LevelCardView(CustomView):
            def __init__(self, outer, interaction: Interaction):
                super().__init__(timeout = None)
                self.outer = outer
                
                member = Member(interaction.user.id)
                
                if member.level_up_card_enabled:
                    change_text_btn = self.ChangeTextButton(self)
                    self.add_item(change_text_btn)
                    
                    change_color_btn = self.ChangeColorButton(self)
                    self.add_item(change_color_btn)
                    
                self.enable_disable_btn = self.EnableDisableButton(self, member.level_up_card_enabled)
                self.add_item(self.enable_disable_btn)
                
                back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                back_btn.callback = self.back_btn_callback
                self.add_item(back_btn)
                
            async def setup(self, interaction: Interaction):
                member = Member(interaction.user.id)
                if not member.level_up_card_enabled:
                    await self.enable_disable_btn.callback(interaction)
                    return

                description = """**What is a level-up card?**
                Whenever you level-up with InfiniBot, your level-up message will contain this card.
                
                Utilize InfiniBot's [generic replacements](https://cypress-exe.github.io/InfiniBot/docs/messaging/generic-replacements/) to customize your level-up card!"""
                
                # On Mobile, extra spaces cause problems. We'll get rid of them here:
                description = utils.standardize_str_indention(description)
                
                embed = nextcord.Embed(title = "Profile - Level-Up Card", description = description, color = nextcord.Color.blurple())
                
                # Get the card to visualize
                if member.level_up_card_enabled:
                    card = member.level_up_card_embed.to_embed()
                    embeds = [embed, card]
                else:
                    embeds = [embed]
                
                await interaction.response.edit_message(embeds = embeds, view = self)
               
            async def reload(self, interaction: Interaction):
                self.__init__(self.outer, interaction)
                await self.setup(interaction)
                
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class ChangeTextButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Change Text", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class ChangeTextModal(CustomModal):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(title = "Level-Up Card", timeout = None)
                        self.outer = outer
                        
                        member = Member(interaction.user.id)
                        title = member.level_up_card_embed["title"]
                        description = member.level_up_card_embed["description"]
                        
                        self.text_title_input = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, max_length = 256, default_value = title, placeholder = "Yum... Levels")
                        self.add_item(self.text_title_input)
                        
                        self.description_text_input = nextcord.ui.TextInput(label = "Description ([level] = level)", style = nextcord.TextInputStyle.paragraph, max_length = 4000, default_value = description, placeholder = "I am level [level]!")
                        self.add_item(self.description_text_input)
                        
                    async def callback(self, interaction: Interaction):
                        title = self.text_title_input.value
                        description = self.description_text_input.value
                        
                        member = Member(interaction.user.id)
                        embed = member.level_up_card_embed
                        embed["title"] = title
                        embed["description"] = description
                        
                        member.level_up_card_embed = embed
                        
                        # Send the user back
                        await self.outer.setup(interaction)             
                    
                async def callback(self, interaction: Interaction):
                    await interaction.response.send_modal(self.ChangeTextModal(self.outer, interaction))
   
            class ChangeColorButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Change Color", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class ChangeColorView(CustomView):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        options = ["Red", "Green", "Blue", "Yellow", "White", "Blurple", "Greyple", "Teal", "Purple", "Gold", "Magenta", "Fuchsia"]

                        member = Member(interaction.user.id)

                        select_options = []
                        for option in options:
                            select_options.append(nextcord.SelectOption(label = option, value = option, default = (option == member.level_up_card_embed["color"])))
                                
                        self.select = nextcord.ui.Select(options = select_options, placeholder = "Select a Color")
                        self.add_item(self.select)
                        
                        back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        back_btn.callback = self.back_btn_callback
                        self.add_item(back_btn)
                        
                        update_btn = nextcord.ui.Button(label = "Update", style = nextcord.ButtonStyle.green, row = 1)
                        update_btn.callback = self.update_btn_callback
                        self.add_item(update_btn)
                        
                    async def setup(self, interaction: Interaction):
                        description = f"""
                        **Colors Available**
                        Red, Green, Blue, Yellow, White
                        Blurple, Greyple, Teal, Purple
                        Gold, Magenta, Fuchsia
                        """
                        
                        # On Mobile, extra spaces cause problems. We'll get rid of them here:
                        description = utils.standardize_str_indention(description)


                        embed = nextcord.Embed(title = "Profile - Level-Up Card - Change Color", description = description, color = nextcord.Color.blurple())
                        
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    async def update_btn_callback(self, interaction: Interaction):
                        if len(self.select.values) != 1: 
                            await self.outer.setup(interaction)
                            return
                        
                        member = Member(interaction.user.id)
                        embed = member.level_up_card_embed
                        embed["color"] = self.select.values[0]
                        member.level_up_card_embed = embed
                        
                        await self.outer.setup(interaction)
                                           
                async def callback(self, interaction: Interaction):
                    await self.ChangeColorView(self.outer, interaction).setup(interaction)
   
            class EnableDisableButton(nextcord.ui.Button):
                def __init__(self, outer, enabled):
                    self.enabled = ("Disable" if enabled else "Enable")
                    super().__init__(label = self.enabled, style = (nextcord.ButtonStyle.gray if enabled else nextcord.ButtonStyle.green))
                    self.outer = outer
                    
                class EnableDisableView(CustomView):
                    def __init__(self, outer, enabled):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.enabled = enabled
                        
                        back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        back_btn.callback = self.back_btn_callback
                        self.add_item(back_btn)
                        
                        button = self.Button(self.outer, self, self.enabled)
                        self.add_item(button)          
                        
                    async def setup(self, interaction: Interaction):
                        description = ""
                        if self.enabled == "Enable": # Currently disabled
                            description += """
                            Whenever you level-up with InfiniBot, your level-up message can contain a personalizable card. Click "Enable" to begin!
                            """
                            
                        description += """
                        **What is a level-up card?**
                        If enabled, this personalizable level-up card will be displayed after each of your level-up messages. (As long as the server permits it)
                        """
                        
                        # On Mobile, extra spaces cause problems. We'll get rid of them here:
                        description = utils.standardize_str_indention(description)
                        embed = nextcord.Embed(title = f"Profile - Level-Up Card - {self.enabled}", description = description, color = nextcord.Color.blurple())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def back_btn_callback(self, interaction: Interaction):
                        member = Member(interaction.user.id)
                        if member.level_up_card_enabled: # Enabled now, forward to level_up_card screen
                            await self.outer.reload(interaction)
                        else: # Disabled now, forward to profile screen
                            await self.outer.outer.setup(interaction)
                        
                    class Button(nextcord.ui.Button):
                        def __init__(self, outer, parent, label):
                            super().__init__(label = label, style = nextcord.ButtonStyle.green)
                            self.outer = outer
                            self.parent = parent
                            
                        async def callback(self, interaction: Interaction):
                            member = Member(interaction.user.id)
                            member.level_up_card_enabled = not member.level_up_card_enabled
                            
                            await self.parent.back_btn_callback(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.EnableDisableView(self.outer, self.enabled).setup(interaction)
   
        async def callback(self, interaction: Interaction):
            await self.LevelCardView(self.outer, interaction).setup(interaction)
    
    class JoinCardButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Join Card", style = nextcord.ButtonStyle.gray)
            self.outer = outer
            
        class JoinCardView(CustomView):
            def __init__(self, outer, interaction: Interaction):
                super().__init__(timeout = None)
                self.outer = outer
                
                member = Member(interaction.user.id)
                
                if member.join_card_enabled:
                    change_text_btn = self.ChangeTextButton(self)
                    self.add_item(change_text_btn)
                    
                    change_color_btn = self.ChangeColorButton(self)
                    self.add_item(change_color_btn)
                    
                self.enable_disable_btn = self.EnableDisableButton(self, member.join_card_enabled)
                self.add_item(self.enable_disable_btn)
                
                back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                back_btn.callback = self.back_btn_callback
                self.add_item(back_btn)
                
            async def setup(self, interaction: Interaction):
                member = Member(interaction.user.id)
                if not member.join_card_enabled:
                    await self.enable_disable_btn.callback(interaction)
                    return

                description = """**What is a join card?**
                Whenever you join a server that uses InfiniBot, your join message will contain this card.
                
                Utilize InfiniBot's [generic replacements](https://cypress-exe.github.io/InfiniBot/docs/messaging/generic-replacements/) to customize your join card!"""
                
                # On Mobile, extra spaces cause problems. We'll get rid of them here:
                description = utils.standardize_str_indention(description)
                
                embed = nextcord.Embed(title = "Profile - Join Card", description = description, color = nextcord.Color.blurple())
                
                # Get the card to visualize
                if member.join_card_embed:
                    card = member.join_card_embed.to_embed()
                    embeds = [embed, card]
                else:
                    embeds = [embed]
                
                await interaction.response.edit_message(embeds = embeds, view = self)
               
            async def reload(self, interaction: Interaction):
                self.__init__(self.outer, interaction)
                await self.setup(interaction)
                
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class ChangeTextButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Change Text", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class ChangeTextModal(CustomModal):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(title = "Join Card", timeout = None)
                        self.outer = outer
                        
                        member = Member(interaction.user.id)
                        title = member.join_card_embed["title"]
                        description = member.join_card_embed["description"]
                        
                        self.text_title_input = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, max_length = 256, default_value = title, placeholder = "About Me")
                        self.add_item(self.text_title_input)
                        
                        self.description_text_input = nextcord.ui.TextInput(label = "Description", style = nextcord.TextInputStyle.paragraph, max_length = 4000, default_value = description, placeholder = "I am human")
                        self.add_item(self.description_text_input)
                        
                    async def callback(self, interaction: Interaction):
                        title = self.text_title_input.value
                        description = self.description_text_input.value
                        
                        member = Member(interaction.user.id)
                        embed = member.join_card_embed
                        embed["title"] = title
                        embed["description"] = description
                        
                        member.join_card_embed = embed
                        
                        # Send the user back
                        await self.outer.setup(interaction)             
                    
                async def callback(self, interaction: Interaction):
                    await interaction.response.send_modal(self.ChangeTextModal(self.outer, interaction))
   
            class ChangeColorButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Change Color", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class ChangeColorView(CustomView):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        options = ["Red", "Green", "Blue", "Yellow", "White", "Blurple", "Greyple", "Teal", "Purple", "Gold", "Magenta", "Fuchsia"]
                
                        member = Member(interaction.user.id)

                        select_options = []
                        for option in options:
                            select_options.append(nextcord.SelectOption(label = option, value = option, default = (option == member.join_card_embed["color"])))
                                
                        self.select = nextcord.ui.Select(options = select_options, placeholder = "Select a Color")
                        self.add_item(self.select)
                        
                        back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        back_btn.callback = self.back_btn_callback
                        self.add_item(back_btn)
                        
                        update_btn = nextcord.ui.Button(label = "Update", style = nextcord.ButtonStyle.green, row = 1)
                        update_btn.callback = self.update_btn_callback
                        self.add_item(update_btn)
                        
                    async def setup(self, interaction: Interaction):
                        description = f"""
                        **Colors Available**
                        Red, Green, Blue, Yellow, White
                        Blurple, Greyple, Teal, Purple
                        Gold, Magenta, Fuchsia
                        """
                        
                        # On Mobile, extra spaces cause problems. We'll get rid of them here:
                        description = utils.standardize_str_indention(description)


                        embed = nextcord.Embed(title = "Profile - Join Card - Change Color", description = description, color = nextcord.Color.blurple())
                        
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    async def update_btn_callback(self, interaction: Interaction):
                        if len(self.select.values) != 1: 
                            await self.outer.setup(interaction)
                            return
                        
                        member = Member(interaction.user.id)
                        embed = member.join_card_embed
                        embed["color"] = self.select.values[0]
                        member.join_card_embed = embed
                        
                        await self.outer.setup(interaction)
                                           
                async def callback(self, interaction: Interaction):
                    await self.ChangeColorView(self.outer, interaction).setup(interaction)
   
            class EnableDisableButton(nextcord.ui.Button):
                def __init__(self, outer, enabled):
                    self.enabled = ("Disable" if enabled else "Enable")
                    super().__init__(label = self.enabled, style = (nextcord.ButtonStyle.gray if enabled else nextcord.ButtonStyle.green))
                    self.outer = outer
                    
                class EnableDisableView(CustomView):
                    def __init__(self, outer, enabled):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.enabled = enabled
                        
                        back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        back_btn.callback = self.back_btn_callback
                        self.add_item(back_btn)
                        
                        button = self.Button(self.outer, self, self.enabled)
                        self.add_item(button)          
                        
                    async def setup(self, interaction: Interaction):
                        description = ""
                        if self.enabled == "Enable": # Currently disabled
                            description += """
                            Whenever you join with InfiniBot, your join message can contain a personalizable card. Click "Enable" to begin!
                            """
                            
                        description += """
                        **What is a join card?**
                        If enabled, this personalizable join card will be attached to your join message every time you join a server with InfiniBot. (As long as the server permits it)
                        """
                        
                        # On Mobile, extra spaces cause problems. We'll get rid of them here:
                        description = utils.standardize_str_indention(description)
                        embed = nextcord.Embed(title = f"Profile - Join Card - {self.enabled}", description = description, color = nextcord.Color.blurple())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def back_btn_callback(self, interaction: Interaction):
                        member = Member(interaction.user.id)
                        if member.join_card_enabled: # Enabled now, forward to join_card screen
                            await self.outer.reload(interaction)
                        else: # Disabled now, forward to profile screen
                            await self.outer.outer.setup(interaction)
                        
                    class Button(nextcord.ui.Button):
                        def __init__(self, outer, parent, label):
                            super().__init__(label = label, style = nextcord.ButtonStyle.green)
                            self.outer = outer
                            self.parent = parent
                            
                        async def callback(self, interaction: Interaction):
                            member = Member(interaction.user.id)
                            member.join_card_enabled = not member.join_card_enabled
                            
                            await self.parent.back_btn_callback(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.EnableDisableView(self.outer, self.enabled).setup(interaction)
   
        async def callback(self, interaction: Interaction):
            await self.JoinCardView(self.outer, interaction).setup(interaction)

    class SettingsButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Settings", style = nextcord.ButtonStyle.gray, row = 1)
            self.outer = outer
            
        class SettingsView(CustomView):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                dms_btn = self.DmsButton(self)
                self.add_item(dms_btn)
                
                data_btn = self.DataButton(self)
                self.add_item(data_btn)
                
                back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                back_btn.callback = self.back_btn_callback
                self.add_item(back_btn)
            
            async def setup(self, interaction: Interaction):
                def icon(bool):
                    if bool:
                        return "✅"
                    return "❌"
                
                member = Member(interaction.user.id)
                
                description = f"""Configure InfiniBot to fit your needs.
                
                {icon(member.direct_messages_enabled)} Direct Messages Enabled"""
                
                # On Mobile, extra spaces cause problems. We'll get rid of them here:
                description = utils.standardize_str_indention(description)
                
                embed = nextcord.Embed(title = "Profile - Settings", description = description, color = nextcord.Color.blurple())
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
        
            class DmsButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Direct Messages", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
        
                class DmsView(CustomView):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        backBtn.callback = self.back_btn_callback
                        self.add_item(backBtn)        
                        
                        member = Member(interaction.user.id)
                        if member.direct_messages_enabled: label = "Disable"
                        else: label = "Enable"
                        
                        button = nextcord.ui.Button(label = label, style = nextcord.ButtonStyle.green)
                        button.callback = self.callback
                        self.add_item(button)
                        
                    async def setup(self, interaction: Interaction):
                        member = Member(interaction.user.id)
                        
                        if member.direct_messages_enabled: 
                            description = """
                            To disable Direct Messages from InfiniBot, click the button "Disable"
                            
                            By doing this, you will no longer recieve permission errors, birthday updates, or strike notices.
                            """
                        else: 
                            description = """
                            To enable Direct Messages from InfiniBot, click the button "Enable"
                            
                            By doing this, you will now recieve permission errors, birthday updates, and strike notices.
                            """
                        description = utils.standardize_str_indention(description)
                        
                        embed = nextcord.Embed(title = "Profile - Settings - Direct Messages", description = description, color = nextcord.Color.blurple())
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    async def callback(self, interaction: Interaction):
                        member = Member(interaction.user.id)
                        member.direct_messages_enabled = not member.direct_messages_enabled
                        
                        await self.outer.setup(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.DmsView(self.outer, interaction).setup(interaction)
        
            class DataButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Delete My Data", style = nextcord.ButtonStyle.gray)
                    self.outer = outer       
                    
                class DataView(CustomView):
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        backBtn.callback = self.back_btn_callback
                        self.add_item(backBtn)
                        
                        button = nextcord.ui.Button(label = "Confirm", style = nextcord.ButtonStyle.green)
                        button.callback = self.callback
                        self.add_item(button)            
                    
                    async def setup(self, interaction: Interaction):
                        description = """By deleting your data, you will delete all your profile information associated with InfiniBot. This action is not reversable.
                        
                        This will not delete:
                        • Any message logs inside a server
                        • Any moderation strikes, levels, birthdays, infinibot-powered messages, etc in any server
                        
                        Some information not deleted by this process may be deleted when you leave a server. Check InfiniBot's [privacy policy](https://cypress-exe.github.io/InfiniBot/docs/legal/privacy-policy/) for complete transparency and more information.
                        
                        Click "Confirm" to delete all your profile information.
                        """
                        
                        # On Mobile, extra spaces cause problems. We'll get rid of them here:
                        description = utils.standardize_str_indention(description)
                        
                        embed = nextcord.Embed(title = "Profile - Settings - Delete My Data", description = description, color = nextcord.Color.blurple())
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def back_btn_callback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    async def callback(self, interaction: Interaction):
                        member = Member(interaction.user.id)
                        member.remove_all_data()
                        
                        await self.outer.setup(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.DataView(self.outer).setup(interaction)           
        
        async def callback(self, interaction: Interaction):
            await self.SettingsView(self.outer).setup(interaction)
    
async def run_profile_command(interaction: Interaction) -> None:
    """
    |coro|

    Runs the profile command.

    :param interaction: The interaction to respond to.
    :type interaction: :class:`~nextcord.Interaction`
    :return: None
    :rtype: None
    """
    view = Profile()
    await view.setup(interaction)