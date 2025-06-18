from nextcord import Interaction
import nextcord

from config.server import Server
from components import utils, ui_components
from components.ui_components import CustomModal, CustomView
from features.action_logging import trigger_edit_log

class EditEmbed(CustomView):
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
        
        edit_color_btn = self.EditColorButton(self)
        self.add_item(edit_color_btn)
        
    async def setup(self, interaction: Interaction):
        await self.load_buttons(interaction)
        
        if not utils.feature_is_active(guild_id=interaction.guild.id, feature="options_menu__editing"):
            await ui_components.disabled_feature_override(self, interaction)
            return
        
        main_embed = nextcord.Embed(title="Edit Embed", description="Edit the following embed's text and color.", color=nextcord.Color.yellow())
        edit_embed = self.message.embeds[0]
        embeds = [main_embed, edit_embed]
        await interaction.response.edit_message(embeds = embeds, view = self)
  
    class EditTextButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label="Edit Text", emoji="✏️")
            self.outer = outer
        
        class EditTextModal(CustomModal):
            def __init__(self, outer):
                super().__init__(title="Edit Text")
                self.outer = outer
                
                self.title_input = nextcord.ui.TextInput(label="Title", min_length=1, max_length=256, 
                                                         placeholder="Title", default_value=outer.message.embeds[0].title)
                self.add_item(self.title_input)
                
                self.description_input = nextcord.ui.TextInput(label="Description", min_length=1, max_length=4000, 
                                                               placeholder="Description", default_value=outer.message.embeds[0].description, 
                                                               style=nextcord.TextInputStyle.paragraph)
                self.add_item(self.description_input)
                
            async def callback(self, interaction: Interaction):
                self.stop()
                before_message = await interaction.channel.fetch_message(self.outer.message.id)

                new_embed = nextcord.Embed(title=self.title_input.value,
                                          description=self.description_input.value, 
                                          color=before_message.embeds[0].color)
                
                new_embed = utils.apply_generic_replacements(new_embed, interaction.user, interaction.guild)

                await before_message.edit(embed = new_embed)
                await self.outer.setup(interaction)
                
                # Trigger Edit Log
                after_message = await interaction.channel.fetch_message(self.outer.message.id)
                await trigger_edit_log(interaction.guild, before_message, after_message, user=interaction.user)
        
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
                
                original_color = utils.get_string_from_discord_color(self.outer.message.embeds[0].color)        
                select_options = []
                for option in utils.COLOR_OPTIONS:
                    select_options.append(nextcord.SelectOption(label=option, value=option, default=(option is original_color)))
                
                self.select = nextcord.ui.Select(placeholder="Choose a color", options=select_options)
                
                self.backBtn = nextcord.ui.Button(label="Back", style=nextcord.ButtonStyle.gray)
                self.backBtn.callback = self.back_callback

                self.button = nextcord.ui.Button(label="Update Color", style=nextcord.ButtonStyle.blurple)
                self.button.callback = self.create_callback
                
                self.add_item(self.select)
                self.add_item(self.backBtn)
                self.add_item(self.button)
                
            async def setup(self, interaction: Interaction):
                description = f"""Choose what color you would like the embed to be:
                
                **Colors Available**
                """
                description += ui_components.get_colors_available_ui_component()
                description = utils.standardize_str_indention(description)

                embed = nextcord.Embed(title="Edit Color", description=description, color=nextcord.Color.yellow())
                await interaction.response.edit_message(embed=embed, view=self)
                    
            async def create_callback(self, interaction: Interaction):
                if self.select.values == []: return
                self.selection = self.select.values[0]
                self.stop()
                
                message = await interaction.channel.fetch_message(self.outer.message.id)
                await message.edit(embed=nextcord.Embed(title=message.embeds[0].title, description=message.embeds[0].description, color = (utils.get_discord_color_from_string(self.selection))))
                await self.outer.setup(interaction)
       
            async def back_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
       
        async def callback(self, interaction: Interaction):
            await self.EditColorView(self.outer).setup(interaction)