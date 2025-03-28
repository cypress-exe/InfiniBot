import nextcord

from components.ui_components import ErrorWhyAdminPrivilegesButton
from features.action_logging import ShowMoreButton
from features.moderation import IncorrectButtonView

def init_views(bot: nextcord.Client):
    bot.add_view(IncorrectButtonView())
    bot.add_view(ShowMoreButton())
    bot.add_view(ErrorWhyAdminPrivilegesButton())