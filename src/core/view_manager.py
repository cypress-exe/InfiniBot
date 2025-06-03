import nextcord

from components.ui_components import ErrorWhyAdminPrivilegesButton
from core.server_join_and_leave_manager import NewServerJoinView, ResendSetupMessageView
from features.action_logging import ShowMoreButton
from features.check_infinibot_permissions import InfiniBotPermissionsReportView
from features.jokes import JokeView, JokeVerificationView
from features.moderation import IncorrectButtonView
from features.role_messages import RoleMessageButton_Multiple, RoleMessageButton_Single

def init_views(bot: nextcord.Client):
    views = [
        ErrorWhyAdminPrivilegesButton(),
        NewServerJoinView(),
        ResendSetupMessageView(),
        ShowMoreButton(),
        InfiniBotPermissionsReportView(),
        JokeView(),
        JokeVerificationView(),
        IncorrectButtonView(),
        RoleMessageButton_Multiple(),
        RoleMessageButton_Single()
    ]

    for view in views:
        bot.add_view(view)
