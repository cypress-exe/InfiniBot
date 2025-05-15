from nextcord import Interaction
import nextcord

from components import utils, ui_components
from config.server import Server

class EmbedModal(nextcord.ui.Modal):        
    def __init__(self):
        super().__init__(title = "Create Embed")
   
        self.title_text_input = nextcord.ui.TextInput(label="Title", style=nextcord.TextInputStyle.short, required=True, max_length=256)
        self.description_text_input = nextcord.ui.TextInput(label="Description", style=nextcord.TextInputStyle.paragraph, required=True, max_length=4000)
        
        self.add_item(self.title_text_input)
        self.add_item(self.description_text_input)

    async def callback(self, interaction: Interaction):
        self.title_value = self.title_text_input.value
        self.description_value = self.description_text_input.value  
        self.stop()

class EmbedInfoView(nextcord.ui.View):
    def __init__(self):
        super().__init__()

        self.return_modal = None
        
        # Continue button
        self.continue_button = nextcord.ui.Button(label="Continue", style=nextcord.ButtonStyle.success)
        self.continue_button.callback = self.continue_callback
        
        # Embeds documentation button
        embeds_docs = nextcord.ui.Button(
            label="Embeds Documentation", 
            style=nextcord.ButtonStyle.link, 
            url="https://cypress-exe.github.io/InfiniBot/docs/messaging/embeds/"
        )
        
        # Generic replacements documentation button
        replacements_docs = nextcord.ui.Button(
            label="Available Replacements", 
            style=nextcord.ButtonStyle.link, 
            url="https://cypress-exe.github.io/InfiniBot/docs/messaging/generic-replacements/"
        )
        
        self.add_item(self.continue_button)
        self.add_item(embeds_docs)
        self.add_item(replacements_docs)
        
    async def continue_callback(self, interaction: Interaction):
        self.continue_button.disabled = True

        # Send Modal
        modal = EmbedModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        self.return_modal = modal

        self.stop()

class EmbedColorView(nextcord.ui.View):
    def __init__(self):
        super().__init__()
                
        select_options = []
        for option in utils.COLOR_OPTIONS:
            select_options.append(nextcord.SelectOption(label=option, value=option))
        
        self.select = nextcord.ui.Select(placeholder="Choose a color", options=select_options)

        self.button = nextcord.ui.Button(label="Create", style=nextcord.ButtonStyle.blurple)
        self.button.callback = self.create_callback
        
        self.add_item(self.select)
        self.add_item(self.button)
             
    async def create_callback(self, interaction: Interaction):
        self.selection = self.select.values[0]
        if self.selection == []: return
        
        self.select.disabled = True
        self.button.disabled = True

        await interaction.response.edit_message(view=self, delete_after=1.0)
        self.stop()

async def run_create_embed_command(interaction: Interaction, role: nextcord.Role):
    if not utils.feature_is_active(guild_id=interaction.guild.id, feature="embeds"):
        await interaction.response.send_message(embed = nextcord.Embed(
            title="Embeds Disabled", 
            description="Embeds have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", 
            color=nextcord.Color.red()), ephemeral=True)
        return
    
    # Handle the role pinging if enabled
    content = ""
    if role != None:
        if interaction.guild.me.guild_permissions.mention_everyone or role.mentionable:
            content = role.mention
        else:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Can't Ping that Role", description = "InfiniBot can't ping that role. Either *allow anyone to @mention this role*, or give InfiniBot permission to *mention @everyone, @here, and All Roles*.", color = nextcord.Color.red()), ephemeral = True)
            return
    
    # Display info about embeds and generic replacements before showing the modal
    info_embed = nextcord.Embed(
        title="Create an Embed",
        description="You're about to create an embed message. Embeds can be customized with a title, description, and color.\n\n"
                   "**Available Replacements**\n"
                   "You can use placeholders in your embeds like `@mention`, `@server`, etc. Check the documentation "
                   "for all available replacements.\n\n"
                   "Click 'Continue' to proceed or check the documentation links below for more information.",
        color=nextcord.Color.blue()
    )
    
    # Show the info view with continue button and documentation links
    info_view = EmbedInfoView()
    await interaction.response.send_message(embed=info_embed, view=info_view, ephemeral=True)
    await info_view.wait()
    
    embed_title = info_view.return_modal.title_value
    embed_description = info_view.return_modal.description_value

    description = f"""Choose what color you would like the embed to be:
    
    **Colors Available**
    """
    
    description += ui_components.get_colors_available_ui_component();
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = utils.standardize_str_indention(description)
    
    embed = nextcord.Embed(title="Choose a Color", description=description, color=nextcord.Color.blue())
    view = EmbedColorView()
    
    await interaction.edit_original_message(embed=embed, view=view)
    
    await view.wait()
    
    color = view.selection
    
    # Translate the color to a discord color
    discord_color = utils.get_discord_color_from_string(color)
    
    # Now we just display the embed
    embed = nextcord.Embed(title=embed_title, description=embed_description, color=discord_color)

    # Apply replacements
    embed = utils.apply_generic_replacements(embed, None, interaction.guild)

    interaction_response = await interaction.channel.send(content=content, embed=embed)
    
    # Finally, add the embed to our active messages for future editing
    server = Server(interaction.guild.id)
    server.managed_messages.add(
        message_id = interaction_response.id,
        channel_id = interaction.channel.id,
        author_id = interaction.user.id,
        message_type = "embed",
        json_data = None
    )
