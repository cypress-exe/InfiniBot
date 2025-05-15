from nextcord import Interaction
import nextcord

from components import utils, ui_components
from config.global_settings import get_configs

async def run_help_command(interaction: Interaction):
    support_server_invite_link = get_configs()["links"]["support_server_invite_link"]
    support_email = get_configs()["links"]["support_email"]
    docs_website = "https://cypress-exe.github.io/InfiniBot/"

    description = f"""For comprehensive help with InfiniBot, visit our documentation website:
    
    {docs_website}
    
    • On desktop: Use the search bar at the top of the page
    • On mobile: Click the button in the top right corner and use the search feature
    
    If you can't find what you need, join our support server at {support_server_invite_link} or contact us at {support_email}.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = utils.standardize_str_indention(description)
  
    embed = nextcord.Embed(title="Help", description=description, color=nextcord.Color.greyple())
    await interaction.response.send_message(embed=embed, ephemeral=True, view=ui_components.SupportAndInviteView())