from nextcord import Interaction
import nextcord
import logging

from components import utils, ui_components
from components.ui_components import CustomView
from config.global_settings import get_configs, ShardLoadedStatus
from config.server import Server
from features.dashboard import Dashboard

class Onboarding(CustomView):
    def __init__(self):
        super().__init__(timeout=None)
        
        self.dropdown_options = [
            ["Profanity Moderation", "Automatically moderate your server for profanity."],
            ["Spam Moderation", "Help keep spam to a minimum."],
            ["Leveling", "Encourage activity as members compete for levels."],
            ["Message and Action Logging", "Track deleted and edited messages, and server modifications."],
            ["Join / Leave Messages", "Welcome / bid farewell with customized messages."],
            ["Birthdays", "Celebrate birthdays with personalized messages."],
            ["Default Roles", "Automatically assign roles to new members."],
            ["Join-To-Create VCs", "Allow members to create custom voice channels."]
        ]
        
        formatted_options = [nextcord.SelectOption(label=option[0], description=option[1]) for option in self.dropdown_options]
        self.dropdown = nextcord.ui.Select(
            placeholder="Select Features", 
            min_values=0, 
            max_values=len(formatted_options), 
            options=formatted_options
        )
        self.add_item(self.dropdown)
        
        self.cancel_btn = self.CancelButton(self)
        self.add_item(self.cancel_btn)
        
        self.next_btn = self.NextButton(self)
        self.add_item(self.next_btn)
        
    async def setup(self, interaction: Interaction, new_message: bool = False):
        for child in self.children: 
            del child
        self.__init__()
        
        embed = nextcord.Embed(
            title="🎉 Welcome to InfiniBot!",
            description=(
            "**Hello there!** 👋\n\n"
            "Thank you for giving InfiniBot a try! Let's start by setting up InfiniBot's features!\n\n"
            "🔽  **Below**, you'll find a convenient drop-down menu showcasing various features that InfiniBot can set up for your server.\n\n"
            "⏰  **Take your time** to choose the ones that best suit your preferences.\n\n"
            "▶️  Once you've made your selections, simply click the **\"Next\"** button to proceed.\n\n"
            "✨  **Happy customizing!**"
            ),
            color=nextcord.Color.fuchsia()
        )
        
        try:
            if new_message: 
                raise 
            await interaction.response.edit_message(embed=embed, view=self)
        except: 
            await interaction.response.send_message(embed=embed, view=self, ephemeral=True)
    
    class CancelButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label="Cancel", style=nextcord.ButtonStyle.danger, row=1)
            self.outer = outer
            
        class CancelView(CustomView):
            def __init__(self, outer):
                super().__init__(timeout=None)
                self.outer = outer
                
                self.go_back_btn = nextcord.ui.Button(label="Go Back")
                self.go_back_btn.callback = self.go_back_btn_callback
                self.add_item(self.go_back_btn)
                
            async def setup(self, interaction: Interaction):
                embed = nextcord.Embed(
                    title="Canceling Onboarding Process", 
                    description="To get back to this onboarding process, type `/onboarding`.", 
                    color=nextcord.Color.red()
                )
                await interaction.response.edit_message(embed=embed, view=self)
                
            async def go_back_btn_callback(self, interaction: Interaction):
                # Put us back to where we were at the start.
                self.outer.__init__()
                await self.outer.setup(interaction)
            
        async def callback(self, interaction: Interaction):          
            await self.CancelView(self.outer).setup(interaction)
    
    # This button gives a screen talking about the onboarding setup process. Then it jumps to the onboarding walkthrough class.
    class NextButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label="Next", style=nextcord.ButtonStyle.blurple)
            self.outer = outer
            
        class OnboardingInfoView(CustomView):
            def __init__(self, outer, order: list):
                super().__init__(timeout=None)
                self.outer = outer
                self.order = order
                
                self.back_btn = nextcord.ui.Button(label="Back", style=nextcord.ButtonStyle.danger)
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                
                self.start_btn = nextcord.ui.Button(label="Start", style=nextcord.ButtonStyle.blurple)
                self.start_btn.callback = self.start_btn_callback
                self.add_item(self.start_btn)              
                
            async def setup(self, interaction: Interaction):
                description = (
                    "🎯  **Next Step: Feature Configuration**\n"
                    "You'll be guided through each selected feature with step-by-step instructions "
                    "from the dashboard interface.\n\n"
                    "🌍  **First up:** We'll help you select your timezone so InfiniBot can "
                    "optimize its performance for your region.\n\n"
                    "✨  Simply click **\"Start\"** when you're ready to begin the configuration process!"
                )
                description = utils.standardize_str_indention(description)
                
                embed = nextcord.Embed(
                    title="🚀 Onboarding Setup",
                    description=description,
                    color=nextcord.Color.fuchsia()
                )
                
                await interaction.response.edit_message(embed=embed, view=self)
                
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                
            async def start_btn_callback(self, interaction: Interaction):
                await self.outer.OnboardingWalkthrough(self.order, self.setup).start(interaction)
            
        async def callback(self, interaction: Interaction):
            selected_options = self.outer.dropdown.values
        
            if selected_options == []: 
                return
            
            # Re-order the options
            ordered_list = []
            for option in [option[0] for option in self.outer.dropdown_options]:
                if option in selected_options:
                    ordered_list.append(option)
            
            await self.OnboardingInfoView(self.outer, ordered_list).setup(interaction)
           
    class OnboardingWalkthrough:
        def __init__(self, order: list, previous):
            self.order = ["Timezone Setup"] + order
            self.previous = previous
            
            self.current = self.order[0]
            self.objective = None
            self.next_objective = None
            self.onboarding_embed = None
            self.last_objective_bool = False
            
        async def start(self, interaction: Interaction):
            self.update_objectives()

            if self.current == "Timezone Setup":
                await self.timezone_setup(interaction)
                return
            
            if self.current == "Profanity Moderation":
                await self.profanity_moderation(interaction)
                return
            
            if self.current == "Spam Moderation":
                await self.spam_moderation(interaction)
                return
            
            if self.current == "Leveling":
                await self.leveling(interaction)
                return
            
            if self.current == "Message and Action Logging":
                await self.logging(interaction)
                return
            
            if self.current == "Join / Leave Messages":
                await self.join_leave_messages(interaction)
                return
            
            if self.current == "Birthdays":
                await self.birthdays(interaction)
                return
            
            if self.current == "Default Roles":
                await self.default_roles(interaction)
                return
        
            if self.current == "Join-To-Create VCs":
                await self.join_to_create_vcs(interaction)
                return
            
        async def previous_item(self, interaction: Interaction):
            index = self.order.index(self.current)
            
            # Check if we are able to
            if index == 0:
                await self.previous(interaction)
            else:
                self.current = self.order[index - 1]
                await self.start(interaction)
            
        async def next_item(self, interaction: Interaction):
            index = self.order.index(self.current)
            
            # Check if we are able to
            if index == (len(self.order) - 1):
                await self.finished(interaction)
            else:
                self.current = self.order[index + 1]
                await self.start(interaction)
                
        def update_objectives(self):
            index = self.order.index(self.current)
            
            self.objective = f"configure {self.current}"
            
            if index == (len(self.order) - 1):
                self.next_objective = "Finish"
                self.last_objective_bool = True
            else:
                self.next_objective = f"Setup {self.order[index + 1]}"
                self.last_objective_bool = False
                
            self.onboarding_embed = nextcord.Embed(title = f"Click \"Next\" to {self.next_objective}",
                                   description = f"Alternatively, {self.objective}.\n\nNote: You can always get back to this page later by typing `/dashboard`.",
                                   color = nextcord.Color.fuchsia())
                              
        async def finished(self, interaction: Interaction):
            await self.FinishedView(self).setup(interaction)
        
        def remap_view_buttons(self, view: nextcord.ui.View):
            # Remove back (and next) button(s)
            # Also remove disable buttons (if they're there)
            for child in list(view.children):
                if isinstance(child, nextcord.ui.Button):
                    if child.label == "Back" or child.label == "Cancel":
                        view.remove_item(child)
                    if child.label == "Next" or child.label == "Finish":
                        view.remove_item(child)
                    if "Disable" in child.label:
                        view.remove_item(child)
                        
            # Add new buttons
            back_btn = nextcord.ui.Button(label="Back", style=nextcord.ButtonStyle.danger, row=4)
            back_btn.callback = self.previous_item
            view.add_item(back_btn)
            
            next_btn = nextcord.ui.Button(label=("Finish" if self.last_objective_bool else "Next"), style=nextcord.ButtonStyle.green, row=4)
            next_btn.callback = self.next_item
            view.add_item(next_btn)
            
            return view
   
        # Some dashboard features may want to go all the way back. This function is for that
        async def setup(self, interaction: Interaction):
            await self.previous_item(interaction)
            return
        
        async def timezone_setup(self, interaction: Interaction):
            view = Dashboard.ConfigureTimezoneButton.ConfigureTimezoneView(
                outer=self, 
                onboarding_modifier=self.remap_view_buttons, 
                onboarding_embed=self.onboarding_embed
            )
            await view.setup(interaction)
        
        async def profanity_moderation(self, interaction: Interaction):
            # Enable the feature
            server = Server(interaction.guild.id)
            server.profanity_moderation_profile.active = True
            
            view = Dashboard.ModerationButton.ModerationView.ProfaneModerationButton.ProfaneModerationView(
                outer=self, 
                guild_id=interaction.guild.id, 
                onboarding_modifier=self.remap_view_buttons, 
                onboarding_embed=self.onboarding_embed
            )
            await view.setup(interaction)
            
        async def spam_moderation(self, interaction: Interaction):
            # Enable the feature
            server = Server(interaction.guild.id)
            server.spam_moderation_profile.active = True
        
            view = Dashboard.ModerationButton.ModerationView.SpamModerationButton.SpamModerationView(
                outer=self, 
                onboarding_modifier=self.remap_view_buttons, 
                onboarding_embed=self.onboarding_embed
            )
            await view.setup(interaction)
            
        async def leveling(self, interaction: Interaction):
            # Enable the feature
            server = Server(interaction.guild.id)
            server.leveling_profile.active = True
        
            view = Dashboard.LevelingButton.LevelingView(
                outer=self, 
                onboarding_modifier=self.remap_view_buttons, 
                onboarding_embed=self.onboarding_embed
            )
            await view.setup(interaction)
            
        async def logging(self, interaction: Interaction):
            # Enable the feature
            server = Server(interaction.guild.id)
            server.logging_profile.active = True
        
            view = Dashboard.LoggingButton.LoggingView(
                outer=self, 
                onboarding_modifier=self.remap_view_buttons, 
                onboarding_embed=self.onboarding_embed
            )
            await view.setup(interaction)
            
        async def join_leave_messages(self, interaction: Interaction):
            # Enable the feature
            server = Server(interaction.guild.id)
            server.join_message_profile.active = True
            server.leave_message_profile.active = True
            del server
            
            view = Dashboard.JoinLeaveMessagesButton.JoinLeaveMessagesView(
                outer=self, 
                onboarding_modifier=self.remap_view_buttons, 
                onboarding_embed=self.onboarding_embed
            )
            await view.setup(interaction)
            
        async def birthdays(self, interaction: Interaction):
            view = Dashboard.BirthdaysButton.BirthdaysView(
                outer=self, 
                onboarding_modifier=self.remap_view_buttons, 
                onboarding_embed=self.onboarding_embed
            )
            await view.setup(interaction)
            
        async def default_roles(self, interaction: Interaction):
            view = Dashboard.DefaultRolesButton.DefaultRolesView(
                outer=self, 
                onboarding_modifier=self.remap_view_buttons, 
                onboarding_embed=self.onboarding_embed
            )
            await view.setup(interaction)

        async def join_to_create_vcs(self, interaction: Interaction):
            view = Dashboard.JoinToCreateVCsButton.JoinToCreateVCsView(
                outer=self,
                guild=interaction.guild,
                onboarding_modifier=self.remap_view_buttons, 
                onboarding_embed=self.onboarding_embed
            )
            await view.setup(interaction)

        class FinishedView(CustomView):
            def __init__(self, outer):
                super().__init__(timeout=None)
                self.outer = outer
                
                self.back_btn = nextcord.ui.Button(label="Back", style=nextcord.ButtonStyle.danger)
                self.back_btn.callback = self.back_btn_callback
                self.add_item(self.back_btn)
                
                support_server_btn = nextcord.ui.Button(label="Support Server", style=nextcord.ButtonStyle.link, url=get_configs()["links"]["support-server-invite-link"])
                self.add_item(support_server_btn)
                
            async def setup(self, interaction: Interaction):
                description = (
                    "🎉  **Congratulations!** InfiniBot is now set up for your server.\n\n"
                    "🔧  **Need more features?** Type `/dashboard` to explore everything InfiniBot has to offer. "
                    "This is also where you can modify any settings from today's setup.\n\n"
                    "❓  **Questions or need help?** Join our support server for assistance from our community.\n\n"
                    "✨  **Thank you for choosing InfiniBot!** We hope you enjoy using our bot!"
                )
                
                embed = nextcord.Embed(
                    title="🎊  Onboarding Complete!",
                    description=utils.standardize_str_indention(description), 
                    color=nextcord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=self)
                
            async def back_btn_callback(self, interaction: Interaction):
                await self.outer.start(interaction)

async def run_onboarding_command(interaction: Interaction):
    """Run the onboarding command."""
    if not utils.feature_is_active(guild_id=interaction.guild.id, feature="onboarding"):
        # Create a simple view for the disabled feature override
        disabled_view = CustomView()
        await ui_components.disabled_feature_override(disabled_view, interaction, edit_message=False)
        return
    
    with ShardLoadedStatus() as shards_loaded:
        if not interaction.guild.shard_id in shards_loaded:
            logging.warning(f"Onboarding: Shard {interaction.guild.shard_id} is not loaded. Forwarding to inactive screen for guild {interaction.guild.id}.")
            loading_view = CustomView()
            await ui_components.infinibot_loading_override(loading_view, interaction, edit_message=False)
            return
        
    if await utils.user_has_config_permissions(interaction):
        view = Onboarding()
        await view.setup(interaction, new_message=True)