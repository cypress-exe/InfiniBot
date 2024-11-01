import nextcord

from src.global_settings import get_settings

class SupportView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = get_settings()["support_server_invite_link"])
        self.add_item(supportServerBtn)

class InviteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        inviteBtn = nextcord.ui.Button(label = "Add to Your Server", style = nextcord.ButtonStyle.link, url = get_settings()["bot_invite_link"])
        self.add_item(inviteBtn)

class SupportAndInviteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = get_settings()["support_server_invite_link"])
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Add To Your Server", style = nextcord.ButtonStyle.link, url = get_settings()["bot_invite_link"])
        self.add_item(inviteBtn)

class SupportInviteAndTopGGVoteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = get_settings()["support_server_invite_link"])
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Invite", style = nextcord.ButtonStyle.link, url = get_settings()["bot_invite_link"])
        self.add_item(inviteBtn)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote for InfiniBot", style = nextcord.ButtonStyle.link, url = get_settings()["topgg_review_link"])
        self.add_item(topGGVoteBtn)
        
class SupportInviteAndTopGGReviewView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = get_settings()["support_server_invite_link"])
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Invite", style = nextcord.ButtonStyle.link, url = get_settings()["bot_invite_link"])
        self.add_item(inviteBtn)
        
        topGGReviewBtn = nextcord.ui.Button(label = "Leave a Review", style = nextcord.ButtonStyle.link, url = get_settings()["topgg_review_link"])
        self.add_item(topGGReviewBtn)

class TopGGVoteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote", style = nextcord.ButtonStyle.link, url = get_settings()["topgg_vote_link"])
        self.add_item(topGGVoteBtn)
        
class TopGGAll(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        topGG = nextcord.ui.Button(label = "Visit on Top.GG", style = nextcord.ButtonStyle.link, url = get_settings()["topgg_link"])
        self.add_item(topGG)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote for InfiniBot", style = nextcord.ButtonStyle.link, url = get_settings()["topgg_vote_link"])
        self.add_item(topGGVoteBtn)
        
        topGGReviewBtn = nextcord.ui.Button(label = "Leave a Review", style = nextcord.ButtonStyle.link, url = get_settings()["topgg_review_link"])
        self.add_item(topGGReviewBtn)