from nextcord import Interaction
import nextcord

import src.utils
from src.global_settings import get_settings
import src.views

# NEEDS TO BE FIXED

# @bot.slash_command(name = "help", description = "Help with the InfiniBot.")
# async def help(interaction: Interaction):
#   support_server_invite_link = get_settings()["support_server_invite_link"]
#   support_email = get_settings()["support_email"]

#   description = f"""For help with InfiniBot, use `/help` followed by what you need help with.
  
#   • Discord's autocomplete feature can be useful.
  
#   For more help, join us at {support_server_invite_link} or contact at {support_email}.
#   """
  
#   # On Mobile, extra spaces cause problems. We'll get rid of them here:
#   description = src.utils.standardize_str_indention(description)
  
#   embed = nextcord.Embed(title = "Help", description = description, color = nextcord.Color.greyple())
#   await interaction.response.send_message(embed = embed, ephemeral=True, view = src.views.SupportAndInviteView())


# @help.subcommand(name = "moderation_profanity", description = "Help with the Admin Channel, Strikes, Infinibot Mod, Flagged/Profane Words, and more.")
# async def profanityModerationHelp(interaction: Interaction):
#   support_server_invite_link = get_settings()["support_server_invite_link"]
#   support_email = get_settings()["support_email"]

#   description = f"""
#   Out of the box, profanity moderation is mostly set up. To complete the setup, visit `/dashboard → Moderation → Profanity` and enable the feature.

#   **Admin Channel Overview:**
#   - When a member uses flagged words, their message is automatically deleted, and they receive a strike.
#   - All strikes are reported to the Admin Channel, where admins can review and decide on their legitimacy.
#       - Note: Ensure InfiniBot can view the channel and send messages.

#   **Strike Handling:**
#   - Admins can mark strikes as incorrect in the Admin Channel, refunding them to the member.
#   - Admins can also view the original message that was automatically deleted.

#   **Understanding Strikes:**
#   - A single strike is not dangerous, but they can accumulate.
#   - Upon reaching the server's maximum strikes (configured at `/dashboard → Moderation → Profanity`), a timed-out duration is applied.
#   - After serving the timeout, the member resets to 0 strikes.

#   **Strike Expire Time:**
#   - In some servers, strikes can be cleared by waiting for the "strike expire time" (configured at `/dashboard → Moderation → Profanity`), which refunds one strike.

#   **Managing Filtered Words:**
#   - Add, delete, and view filtered words at `/dashboard → Moderation → Profanity → Filtered Words`.
#       - Note: InfiniBot also detects variations of these words.

#   **Disabling Profanity Moderation:**
#   - If profanity moderation isn't suitable for your server, turn it off at `/dashboard → Moderation → Profanity → Disable Profanity Moderation`.

#   **Extra Commands:**
#   - `/view_strikes`: View another member's strikes. (Works without Infinibot Mod)
#   - `/my_strikes`: View your own strikes. (Works without Infinibot Mod)
#   - `/dashboard → Moderation → Profanity`: Configure specific features in Profanity Moderation.
#   - `/dashboard → Moderation → Profanity → Manage Members`: View and configure strikes.

#   For additional assistance, join us at {support_server_invite_link} or contact us at {support_email}.
#   """
  
#   # On Mobile, extra spaces cause problems. We'll get rid of them here:
#   description = src.utils.standardize_str_indention(description)
  
#   embed = nextcord.Embed(title = "Fine-Tune Profanity Moderation for Your Server", description = description, color = nextcord.Color.greyple())
#   await interaction.response.send_message(embed = embed, ephemeral = True, view = src.views.SupportAndInviteView())