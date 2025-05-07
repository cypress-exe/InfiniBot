import nextcord

from components.ui_components import ErrorWhyAdminPrivilegesButton
from features.action_logging import ShowMoreButton
from features.moderation import IncorrectButtonView
from features.role_messages import RoleMessageButton_Multiple, RoleMessageButton_Single

def init_views(bot: nextcord.Client):
    views = [
        IncorrectButtonView(),
        ShowMoreButton(),
        ErrorWhyAdminPrivilegesButton(),
        RoleMessageButton_Multiple(),
        RoleMessageButton_Single(),
    ]

    for view in views:
        bot.add_view(view)
