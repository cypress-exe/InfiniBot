from nextcord import Interaction
from nextcord.ext import commands
import nextcord
import datetime
import humanfriendly
import copy

import ui_components
import utils
import help_commands
from custom_types import UNSET_VALUE

from server import Server


class Dashboard(nextcord.ui.View):
    def __init__(self, interaction: Interaction):
        super().__init__(timeout = None)
        
        self.moderationBtn = self.ModerationButton(self)
        self.add_item(self.moderationBtn)
        
        # self.loggingBtn = self.LoggingButton(self)
        # self.add_item(self.loggingBtn)
        
        # self.levelingBtn = self.LevelingButton(self)
        # self.add_item(self.levelingBtn)
        
        # self.joinLeaveMessagesBtn = self.JoinLeaveMessagesButton(self)
        # self.add_item(self.joinLeaveMessagesBtn)
        
        # self.birthdaysBtn = self.BirthdaysButton(self)
        # self.add_item(self.birthdaysBtn)
        
        # self.defaultRolesBtn = self.DefaultRolesButton(self)
        # self.add_item(self.defaultRolesBtn)
        
        # self.joinToCreateVCsButton = self.JoinToCreateVCsButton(self)
        # self.add_item(self.joinToCreateVCsButton)
        
        # self.bansButton = self.AutoBansButton(self)
        # self.add_item(self.bansButton)
        
        # self.activeMessagesBtn = self.ActiveMessagesButton(self)
        # self.add_item(self.activeMessagesBtn)
        
        # self.enableDisableBtn = self.ExtraFeaturesButton(self)
        # self.add_item(self.enableDisableBtn)

    async def setup(self, interaction: Interaction):
        for child in self.children: del child
        self.__init__(interaction)
        
        if not utils.feature_is_active(guild_id = interaction.guild.id, feature = "dashboard"):
            await ui_components.disabled_feature_override(self, interaction)
            return
        
        description = """Welcome to the InfiniBot Dashboard! Choose a feature to setup / edit:"""
        
        # On Mobile, extra spaces cause problems. We'll get rid of them here:
        description = utils.standardize_str_indention(description)
        
        embed = nextcord.Embed(title = "Dashboard", description = description, color = nextcord.Color.blue())
        try: await interaction.response.edit_message(embed = embed, view = self)
        except: await interaction.response.send_message(embed = embed, view = self, ephemeral=True)
              

    class ModerationButton(nextcord.ui.Button):
        def __init__(self, outer):
            
            super().__init__(label = "Moderation", style = nextcord.ButtonStyle.gray)
            self.outer = outer 
          
        class ModerationView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.ProfaneModerationBtn = self.ProfaneModerationButton(self)
                self.add_item(self.ProfaneModerationBtn)
                
                # self.spamModerationBtn = self.SpamModerationButton(self)
                # self.add_item(self.spamModerationBtn)
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1) 
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
            async def setup(self, interaction: Interaction):
                for child in self.children: 
                    del child
                    self.__init__(self.outer)
                
                description = """
                InfiniBot will help you moderate your server with built-in profanity and spam moderation.
                
                **Exemptions**
                Members with the "Administrator" permission are exempt from moderation.
                InfiniBot will not moderate age-restricted channels for profanity.
                
                Use the buttons below to configure profanity and spam moderation.
                """
                
                description = utils.standardize_str_indention(description)
                
                embed = nextcord.Embed(title = "Dashboard - Moderation", description = description, color = nextcord.Color.blue())
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class ProfaneModerationButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Profanity", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class ProfaneModerationView(nextcord.ui.View): #Moderation Window -----------------------------------------------------
                    def __init__(self, outer, guild_id, onboarding_modifier = None, onboarding_embed = None):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.onboarding_modifier = onboarding_modifier
                        self.onboarding_embed = onboarding_embed
                        
                        self.wordsBtn = self.FilteredWordsButton(self)
                        self.add_item(self.wordsBtn)
                        
                        server = Server(guild_id)
                        self.manageMembersBtn = self.ManageMembersButton(self, server.profanity_moderation_profile.max_strikes)
                        self.add_item(self.manageMembersBtn)
                        del server
                        
                        self.maxStrikesBtn = self.MaxStrikesButton(self)
                        self.add_item(self.maxStrikesBtn)
                        
                        self.strikeExpireTimeBtn = self.StrikeExpireTimeButton(self)
                        self.add_item(self.strikeExpireTimeBtn)
                        
                        self.timeoutDurationBtn = self.TimeoutDurationButton(self)
                        self.add_item(self.timeoutDurationBtn)
                        
                        self.adminChannelBtn = self.AdminChannelButton(self)
                        self.add_item(self.adminChannelBtn)
                        
                        self.disableBtn = self.EnableDisableButton(self)
                        self.add_item(self.disableBtn)
                        
                        self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 4) 
                        self.backBtn.callback = self.backBtnCallback
                        self.add_item(self.backBtn)
                                    
                    async def setup(self, interaction: Interaction):
                        # Redirect to Activation Screen if needed
                        server = Server(interaction.guild.id)
                        if not server.profanity_moderation_profile.active: 
                            await self.EnableDisableButton.EnableDisableView(self).setup(interaction) # BEGIN SLOWLY GOING THROUGH AND FIXING THINGS. 
                            #                                                                           GOAL: GET DASHBOARD WORKING FOR PROFANITY MODERATION
                            return
                            
                        if self.onboarding_modifier: self.onboarding_modifier(self)
                        
                        # Clean up
                        if not self.onboarding_modifier:
                            for child in self.children: 
                                del child 
                                self.__init__(self.outer, interaction.guild.id)
                        
                        # Update Manage Members button
                        self.manageMembersBtn.__init__(self, max_strikes = server.profanity_moderation_profile.max_strikes)
                        
                        # Global Kill
                        if not utils.feature_is_active(server = server, feature = "profanity_moderation"):
                            await ui_components.disabled_feature_override(self, interaction)
                            return
                        
                        if server.profanity_moderation_profile.channel == None:
                            await self.adminChannelBtn.callback(interaction, skipped = True)
                            return
                        
                        # Info
                        if server.profanity_moderation_profile.max_strikes != 0:
                            if server.profanity_moderation_profile.strike_expire_days != None: strikeExpireDays =  str(server.profanity_moderation_profile.strike_expire_days) + " days"
                            else: strikeExpireDays = "Disabled"         
                        else: strikeExpireDays = "N/A"
                        if server.profanity_moderation_profile.channel == None: adminChannelName = "None"
                        elif server.profanity_moderation_profile.channel == UNSET_VALUE: adminChannelName = "UNSET"
                        else: adminChannelName = interaction.guild.get_channel(server.profanity_moderation_profile.channel).mention
                        
                        description = f"""
                        InfiniBot aids in combating profanity in your server. Customize the options below to suit your server's requirements.
                        
                        **Settings**
                        Maximum Strikes: {server.profanity_moderation_profile.max_strikes}
                        Strike Expire Time: {strikeExpireDays}
                        Timeout Duration: {server.profanity_moderation_profile.timeout_seconds} seconds
                        Admin Channel: {adminChannelName}
                        
                        **Understanding Strikes:**
                        Rather than an immediate timeout, members can receive strikes for profanity. Once the "Maximum Strikes" is reached, a timeout is triggered. Adjust "Strike Expiration Time" or disable by setting "Maximum Strikes" to 0.
                        
                        For more information, use: {UNSET_VALUE}
                        """ # TODO add shortcut for help command
                        description = utils.standardize_str_indention(description)
                        
                        
                        embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity", description = description, color = nextcord.Color.blue())
                        
                        if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
                        else: embeds = [embed]
                        
                        try: await interaction.response.edit_message(embeds = embeds, view = self)
                        except: await interaction.edit_original_message(embeds = embeds, view = self)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)

                    class FilteredWordsButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Filtered Words", style = nextcord.ButtonStyle.gray)
                            self.outer = outer           
                            
                        # class FilteredWordsView(nextcord.ui.View): #Filtered Words Window -----------------------------------------------------
                        #     def __init__(self, outer):
                        #         super().__init__(timeout = None)
                        #         self.outer = outer
                                
                        #         self.addWordBtn = self.AddWordButton(self)
                        #         self.add_item(self.addWordBtn)
                                
                        #         self.deleteWordBtn = self.DeleteWordButton(self)
                        #         self.add_item(self.deleteWordBtn)
                                
                        #         self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        #         self.backBtn.callback = self.backBtnCallback
                        #         self.add_item(self.backBtn)
                                
                        #     async def setup(self, interaction: Interaction):
                        #         server = Server_DEP(interaction.guild.id)
                                
                        #         self.embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity - Filtered Words", description = "Moderation Word Settings\n\nThe following words are filtered by InfiniBot", color = nextcord.Color.blue())
                        #         ProfaneWords = server.profane_words
                        #         if ProfaneWords == []: ProfaneWords.append("You don't have any filtered words set. Add some!")
                        #         else: ProfaneWords = sorted(ProfaneWords)
                                
                        #         self.embed.add_field(name = "Filtered Words", value = "||"+"\n".join(ProfaneWords)+"||")
                                
                        #         try: await interaction.response.edit_message(embed = self.embed, view = self)
                        #         except: await interaction.edit_original_message(embed = self.embed, view = self)
                                                           
                        #     async def backBtnCallback(self, interaction: Interaction):
                        #         await self.outer.setup(interaction)
                        #         await interaction.edit_original_message(view = self.outer)
                                                                            
                        #     class AddWordButton(nextcord.ui.Button):
                        #         def __init__(self, outer):
                        #             super().__init__(label = "Add Word", style = nextcord.ButtonStyle.gray)
                        #             self.outer = outer
                                    
                        #         class getWordModal(nextcord.ui.Modal): #Add Word Modal -----------------------------------------------------
                        #             def __init__(self, outer):
                        #                 super().__init__(title = "Add Word")
                        #                 self.outer = outer
                        #                 self.response = None
                                        
                        #                 self.input = nextcord.ui.TextInput(label = "Word to filter", style = nextcord.TextInputStyle.short, placeholder="Must have no suffixes. Ex: walking → walk, jumped → jump")
                        #                 self.add_item(self.input)
                                        
                        #             async def callback(self, interaction: Interaction):
                        #                 response = self.addWord(self.input.value, interaction.guild.id)
                        #                 if response == None:
                        #                     self.response = self.input.value
                        #                     self.stop()
                        #                 else:
                        #                     await interaction.response.send_message(embed = response, ephemeral=True)
                        #                     self.stop()
                                      
                        #             def addWord(word: str, guild_id):
                        #                 server = Server_DEP(guild_id)
                                        
                        #                 if word.lower() in [x.lower() for x in server.profane_words]:
                        #                     return nextcord.Embed(title = "Word Already Exists", description = f"The word \"{word}\" already exists in the database.", color = nextcord.Color.red())

                        #                 if "———" in word:
                        #                     return nextcord.Embed(title = "Word Cannot Contain Unique Case", description = f"Your word cannot contain \"———\" as it is reserved for other uses", color = nextcord.Color.red())

                        #                 #add word
                        #                 server.profane_words.append(word.lower())

                        #                 server.saveProfaneWords()

                        #                 return None
                                        
                        #         async def callback(self, interaction: Interaction):
                        #             modal = self.getWordModal(self)
                        #             await interaction.response.send_modal(modal)
                        #             await modal.wait()
                                    
                        #             await self.outer.setup(interaction)
                                                                           
                        #     class DeleteWordButton(nextcord.ui.Button):
                        #         def __init__(self, outer):
                        #             super().__init__(label = "Delete Word", style = nextcord.ButtonStyle.gray)
                        #             self.outer = outer                     
                                        
                        #         async def callback(self, interaction: Interaction):
                        #             server = Server_DEP(interaction.guild.id)
                        #             ProfaneWords = [nextcord.SelectOption(label = x) for x in server.profane_words]
                                    
                        #             embed: nextcord.Embed = copy.copy(self.outer.embed)
                        #             embed.description = "Remove Moderated Words"
                        #             embed.clear_fields()
                        #             await ui_components.SelectView(embed, ProfaneWords, self.selectionCallback, continueButtonLabel = "Delete").setup(interaction)
                                    
                        #         async def selectionCallback(self, interaction: Interaction, selection):
                        #             if selection != None: self.deleteWord(selection, interaction.guild.id)
                        #             await self.outer.setup(interaction)
                                    
                        #         def deleteWord(self, word: str, guild_id):
                        #             server = Server_DEP(guild_id) 
                        #             server.profane_words.pop(server.profane_words.index(word))
                        #             server.saveProfaneWords()
                                
                        async def callback(self, interaction: Interaction): #Filtered Words Button Callback ————————————————————————————————————————————————————————————
                            return
                            view = self.FilteredWordsView(self.outer)
                            await view.setup(interaction)
                            
                    class ManageMembersButton(nextcord.ui.Button):
                        def __init__(self, outer, max_strikes = 1):
                            super().__init__(label = "Manage Members", style = nextcord.ButtonStyle.gray, disabled = (max_strikes == 0))
                            self.outer = outer
                            
                        # class ManageMembersView(nextcord.ui.View):#Strikes Window -----------------------------------------------------
                        #     def __init__(self, outer):
                        #         super().__init__(timeout=None)
                        #         self.outer = outer
                                
                        #         self.editStrikesBtn = self.EditStrikesButton(self)
                        #         self.add_item(self.editStrikesBtn)
                                
                        #         self.deleteAllStrikesBtn = self.DeleteAllStrikesButton(self)
                        #         self.add_item(self.deleteAllStrikesBtn)
                                
                        #         self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        #         self.backBtn.callback = self.backBtnCallback
                        #         self.add_item(self.backBtn)
                                
                        #     async def setup(self, interaction: Interaction):
                        #         self.dataSorted = self.getMembers(interaction, limit = 25)
                                
                        #         dataString = []
                        #         for index in self.dataSorted:
                        #             dataString.append(index[0])

                        #         self.embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity - Manage Members", color = nextcord.Color.blue())
                        #         self.embed.add_field(name = "Strike - Member", value = "\n".join(dataString), inline = True)
                                
                        #         await interaction.response.edit_message(embed = self.embed, view = self)
                            
                        #     def getMembers(self, interaction: Interaction, limit: str = None):
                        #         server = Server_DEP(interaction.guild_id)
                                
                        #         data = []
                        #         for member in interaction.guild.members:
                        #             if limit != None and (len(data) + 1) > limit: 
                        #                 sortedMembers = sorted(data, key = lambda x: (x[0], x[1]), reverse = True)
                        #                 for data in sortedMembers:
                        #                     yield [f"{data[0]} - {data[1]}", data[2]]
                        #                 yield [f"{len(interaction.guild.members) - limit - 1} more. Use */get_strikes* to get a specific member's strike(s)", None]
                        #                 return
                                    
                        #             if member.bot: continue
                                    
                        #             strike = server.getStrike(member.id)
                        #             if member.nick != None: Member = f"{member} ({member.nick})"
                        #             else: Member = f"{member}"
                                    
                        #             data.append([strike.strike, Member, member.id])
                                    
                                    
                        #         for data in sorted(data, key = lambda x: (x[0], x[1]), reverse = True):
                        #             yield [f"{data[0]} - {data[1]}", data[2]]
                        
                        #     async def backBtnCallback(self, interaction: Interaction):
                        #         await self.outer.setup(interaction)
                        #         await interaction.edit_original_message(view = self.outer)
                                
                        #     class EditStrikesButton(nextcord.ui.Button):
                        #         def __init__(self, outer):
                        #             super().__init__(label = "Edit", style = nextcord.ButtonStyle.gray)
                        #             self.outer = outer
                                    
                        #         class EditStrikesView(nextcord.ui.View):#Edit Strikes Window -----------------------------------------------------
                        #             def __init__(self, outer, guild: nextcord.Guild, userSelection):
                        #                 super().__init__(timeout=None)
                        #                 self.outer = outer
                                        
                        #                 server = Server_DEP(guild.id)
                                        
                        #                 strikeSelectOptions: list[nextcord.SelectOption] = [nextcord.SelectOption(label = str(number)) for number in range(0, int(server.max_strikes) + 1)]
                        #                 strikeSelectOptions.reverse()
                        #                 self.strikeSelect = nextcord.ui.Select(options = strikeSelectOptions, placeholder = "Choose a Strike")
                        #                 self.add_item(self.strikeSelect)
                                        
                        #                 self.cancelBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                        #                 self.cancelBtn.callback = self.cancelBtnCallback
                        #                 self.add_item(self.cancelBtn)
                                        
                        #                 self.confirmBtn = self.ConfirmButton(self.outer, self, userSelection)
                        #                 self.add_item(self.confirmBtn)
                                        
                        #             async def setup(self, interaction: Interaction):
                        #                 Embed = self.outer.embed
                        #                 Embed.description = "Select a Strike"
                        #                 await interaction.response.edit_message(embed = Embed, view = self)
                                        
                        #             async def cancelBtnCallback(self, interaction: Interaction):
                        #                 await self.outer.setup(interaction)
                                        
                        #             class ConfirmButton(nextcord.ui.Button):
                        #                 def __init__(self, outer, parent, userSelection):
                        #                     super().__init__(label = "Confirm", style = nextcord.ButtonStyle.blurple)
                        #                     self.outer = outer
                        #                     self.parent = parent
                        #                     self.userSelection = userSelection
                                            
                        #                 async def callback(self, interaction: Interaction):
                        #                     member = self.userSelection
                        #                     strikes = self.parent.strikeSelect.values
                                            
                        #                     if strikes == []:
                        #                         return
                                            
                        #                     strike = int(strikes[0])
                                            
                        #                     server = Server_DEP(interaction.guild.id)
                        #                     discordMember = server.getStrike(member)
                        #                     discordMember.strike = strike
                        #                     await self.outer.setup(interaction)
                                                            
                        #         async def callback(self, interaction: Interaction):# Edit Strikes Callback and First Step ————————————————————————————————————————————————————————————
                        #             #getting people
                        #             memberSelectOptions = []
                        #             for data in self.outer.getMembers(interaction):
                        #                 memberSelectOptions.append(nextcord.SelectOption(label = data[0], value = data[1]))
                                    
                        #             embed: nextcord.Embed = copy.copy(self.outer.embed)
                        #             embed.description = "Select a member"
                        #             await ui_components.SelectView(embed, memberSelectOptions, self.callbackPart1, placeholder = "Choose a Member", continueButtonLabel = "Next", preserveOrder = True).setup(interaction)
                                    
                        #         async def callbackPart1(self, interaction: Interaction, selection):
                        #             if selection == None: #if they canceled
                        #                 await self.outer.setup(interaction)
                        #             else:
                        #                 await self.EditStrikesView(self.outer, interaction.guild, selection).setup(interaction)
                                                        
                        #     class DeleteAllStrikesButton(nextcord.ui.Button):
                        #         def __init__(self, outer):
                        #             super().__init__(label = "Clear", style = nextcord.ButtonStyle.gray)
                        #             self.outer = outer
                                    
                        #         class DeleteAllStrikesView(nextcord.ui.View):
                        #             def __init__(self, outer):
                        #                 super().__init__(timeout = None)
                        #                 self.outer = outer
                                        
                        #                 self.noBtn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
                        #                 self.noBtn.callback = self.noBtnCommand
                        #                 self.add_item(self.noBtn)
                                        
                        #                 self.yesBtn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
                        #                 self.yesBtn.callback = self.yesBtnCommand
                        #                 self.add_item(self.yesBtn)
                                        
                        #             async def setup(self, interaction: Interaction):
                        #                 embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will reset all strikes in the server to 0.\nThis action cannot be undone.", color = nextcord.Color.blue())
                        #                 await interaction.response.edit_message(embed = embed, view = self)
                                        
                        #             async def noBtnCommand(self, interaction: Interaction):
                        #                 await self.outer.setup(interaction)
                                        
                        #             async def yesBtnCommand(self, interaction: Interaction):
                        #                 server = Server_DEP(interaction.guild.id)
                        #                 server.strikes = []
                        #                 server.saveStrikes()
                        #                 await self.outer.setup(interaction)
                                    
                        #         async def callback(self, interaction: Interaction):
                        #             await self.DeleteAllStrikesView(self.outer).setup(interaction)
                            
                        async def callback(self, interaction: Interaction): # Strikes Callback ————————————————————————————————————————————————————————————
                            return
                            view = self.ManageMembersView(self.outer)
                            await view.setup(interaction)

                    class MaxStrikesButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Maximum Strikes", style = nextcord.ButtonStyle.gray, row  = 1)
                            self.outer = outer
                            
                        # class MaxStrikesModal(nextcord.ui.Modal): #Max Strikes Modal -----------------------------------------------------
                        #     def __init__(self, outer, guild_id):
                        #         super().__init__(title = "Maximum Strikes")
                        #         self.outer = outer
                        #         server = Server_DEP(guild_id)
                                
                        #         self.input = nextcord.ui.TextInput(label = "Maximum Strikes (Must be a number)", default_value = server.max_strikes, placeholder = "This Field is Required", max_length=2)
                        #         self.add_item(self.input)
                                
                        #     async def callback(self, interaction: Interaction):
                        #         try:
                        #             if int(self.input.value) > 25: raise Exception
                        #         except:
                        #             await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Maximum Strikes needs to be a positive number below 26.", color = nextcord.Color.red()), ephemeral=True)
                        #             return
                                
                        #         server = Server_DEP(interaction.guild.id)
                        #         server.max_strikes = int(self.input.value)
                        #         server.saveData()
                        #         await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            return
                            await interaction.response.send_modal(self.MaxStrikesModal(self.outer, interaction.guild.id))
                                       
                    class StrikeExpireTimeButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Strike Expire Time", style = nextcord.ButtonStyle.gray, row  = 1)
                            self.outer = outer
                            
                        # class StrikeExpireTimeModal(nextcord.ui.Modal): #Strike Expire Time Modal -----------------------------------------------------
                        #     def __init__(self, outer, guild_id):
                        #         super().__init__(title = "Strike Expire Time")
                        #         self.outer = outer
                        #         server = Server_DEP(guild_id)
                                
                        #         self.input = nextcord.ui.TextInput(label = "Strike Expire Time (Days) (Must be a number)", default_value = server.strike_expire_time, placeholder = "Disable this feature", max_length=2, required = False)
                        #         self.add_item(self.input)
                                
                        #     async def callback(self, interaction: Interaction):
                        #         if self.input.value != None:
                        #             try:
                        #                 int(self.input.value)
                        #             except:
                        #                 await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Strike Expire Time needs to be a number.", color = nextcord.Color.red()), ephemeral=True)
                        #                 return
                                
                        #             server = Server_DEP(interaction.guild.id)
                        #             server.strike_expire_time = int(self.input.value)
                        #         else:
                        #             server = Server_DEP(interaction.guild.id)
                        #             server.strike_expire_time = None
                                    
                        #         server.saveData()
                        #         await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            return
                            await interaction.response.send_modal(self.StrikeExpireTimeModal(self.outer, interaction.guild.id))
                                   
                    class TimeoutDurationButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Timeout Duration", style = nextcord.ButtonStyle.gray, row = 2)
                            self.outer = outer
                            
                        # class TimeoutDurationModal(nextcord.ui.Modal): #Timeout Duration Modal -----------------------------------------------------
                        #     def __init__(self, outer, guild_id):
                        #         super().__init__(title = "Timeout Duration")
                        #         self.outer = outer
                        #         server = Server_DEP(guild_id)
                                
                        #         self.input = nextcord.ui.TextInput(label = "Timeout Duration (Format: 5s, 10m, 1h, 2d)", default_value = server.profanity_timeout_time, placeholder = "This Field is Required", max_length=10)
                        #         self.add_item(self.input)
                                
                        #     async def callback(self, interaction: Interaction):
                        #         if self.input.value == "" or self.input.value == None:
                        #             await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Timeout Time needs to be like this: 10s, 20s, 1m, 30m, 1h, 5h, 1d", color = nextcord.Color.red()), ephemeral=True)
                        #             return
                                
                        #         try:
                        #             humanfriendly.parse_timespan(self.input.value)
                        #         except:
                        #             await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Timeout Time needs to be like this: 10s, 20s, 1m, 30m, 1h, 5h, 1d", color = nextcord.Color.red()), ephemeral=True)
                        #             return
                                
                        #         server = Server_DEP(interaction.guild.id)
                        #         server.profanity_timeout_time = self.input.value
                        #         server.saveData()
                        #         await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            return
                            await interaction.response.send_modal(self.TimeoutDurationModal(self.outer, interaction.guild.id))
                            
                    class AdminChannelButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Admin Channel", style = nextcord.ButtonStyle.gray, row  = 2)
                            self.outer = outer
                                                
                        async def callback(self, interaction: Interaction, skipped = False):
                            return
                            self.skipped = skipped
                            server = Server_DEP(interaction.guild.id)
                                
                            selectOptions = []
                            for channel in interaction.guild.text_channels:
                                if channel.category != None: categoryName = channel.category.name
                                else: categoryName = None
                                #check permissions
                                if await checkTextChannelPermissions(channel, False):
                                    selectOptions.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.admin_channel != None and server.admin_channel.id == channel.id)))
                            
                            if self.skipped: title = "Dashboard - Moderation - Profanity"
                            else: title = "Dashboard - Moderation - Profanity - Admin Channel"
                            embed = nextcord.Embed(title = title, 
                                                   description = "Choose a channel for moderation info.\n\n**Ensure Admin-Only Access**\nThis channel lets members report incorrect strikes, so limit access to admins.\n\n**Can't Find Your Channel?**\nEnsure InfiniBot has permissions to view and send messages in all your channels.", 
                                                   color = nextcord.Color.blue())
                            await ui_components.SelectView(embed, selectOptions, self.SelectViewCallback, continueButtonLabel = "Confirm", cancelButtonLabel = ("Back" if self.skipped else "Cancel")).setup(interaction)
                            
                        async def SelectViewCallback(self, interaction: Interaction, selection):
                            if selection == None:
                                if not self.skipped:
                                    await self.outer.setup(interaction)
                                    return
                                else:
                                    await self.outer.outer.setup(interaction)
                                    return
                                
                            server = Server_DEP(interaction.guild.id)
                            if server.setAdminChannelID(selection):
                                server.saveData()
                                await self.outer.setup(interaction)
                                
                            #send a message to the new admin channel
                            embed = nextcord.Embed(title = "Admin Channel Set", description = f"Strikes will now be logged in this channel.\n\n**Ensure Admin-Only Access**\nThis channel lets members report incorrect strikes, so limit access to admins.", color =  nextcord.Color.green())
                            embed.set_footer(text = f"Action done by {interaction.user}")
                            await server.admin_channel.send(embed = embed, view = SupportAndInviteView())
                              
                    class EnableDisableButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Disable Profanity Moderation", row = 3)
                            self.outer = outer
                            
                        # class EnableDisableView(nextcord.ui.View):
                        #     def __init__(self, outer):
                        #         super().__init__(timeout = None)
                        #         self.outer = outer
                                
                        #         self.backBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                        #         self.backBtn.callback = self.backBtnCallback
                        #         self.add_item(self.backBtn)
                                
                        #         self.actionBtn = nextcord.ui.Button(label = "ACTION", style = nextcord.ButtonStyle.green)
                        #         self.actionBtn.callback = self.actionBtnCallback
                        #         self.add_item(self.actionBtn)
                                
                                
                        #     async def setup(self, interaction: Interaction, server = None):
                        #         if not server: server = Server_DEP(interaction.guild.id)
                                
                        #         # Determine whether or not we are active or not.
                        #         if server.profanity_moderation_enabled:
                        #             # We *are* active. Give info for deactivation
                        #             embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity - Disable", 
                        #                                    description = "Are you sure you want to disable profanity moderation? You can re-enable this feature at any time.",
                        #                                    color = nextcord.Color.blue())
                        #             self.actionBtn.label = "Disable"
                                    
                        #         else:
                        #             # We are *not* active. Give info for activation
                        #             embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity",
                        #                                    description = "Profanity moderation is currently disabled. Do you want to enable it?",
                        #                                    color = nextcord.Color.blue())
                        #             self.actionBtn.label = "Enable"
                                    
                        #         await interaction.response.edit_message(embed = embed, view = self)
                                
                        #     async def backBtnCallback(self, interaction: Interaction, server = None):
                        #         if not server: server = Server_DEP(interaction.guild.id)
                                
                        #         # Return either to profanity moderation or moderation.
                        #         if server.profanity_moderation_enabled:
                        #             # Profanity Moderation is enabled. Put us in here.
                        #             await self.outer.setup(interaction)
                                    
                        #         else:
                        #             # Profanity Moderation is disabled. Put us in the level above (moderation)
                        #             await self.outer.outer.setup(interaction)
                                
                        #     async def actionBtnCallback(self, interaction: Interaction):
                        #         server = Server_DEP(interaction.guild.id)
                                
                        #         server.profanity_moderation_enabled = (not server.profanity_moderation_enabled)
                                
                        #         server.saveData()
                                
                        #         # Return them.
                        #         await self.backBtnCallback(interaction, server = server)
                            
                        async def callback(self, interaction: Interaction):
                            return
                            await self.EnableDisableView(self.outer).setup(interaction)
                                     
                async def callback(self, interaction: Interaction):
                    view = self.ProfaneModerationView(self.outer, interaction.guild.id)
                    await view.setup(interaction)
             
            # class SpamModerationButton(nextcord.ui.Button):
            #     def __init__(self, outer):
            #         super().__init__(label = "Spam", style = nextcord.ButtonStyle.gray)
            #         self.outer = outer
                    
            #     class SpamModerationView(nextcord.ui.View):
            #         def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
            #             super().__init__(timeout = None)
            #             self.outer = outer
            #             self.onboarding_modifier = onboarding_modifier
            #             self.onboarding_embed = onboarding_embed
                        
            #             self.timeoutDurationBtn = self.TimeoutDurationButton(self)
            #             self.add_item(self.timeoutDurationBtn)
                        
            #             self.messageThresholdBtn = self.MessagesThresholdButton(self)
            #             self.add_item(self.messageThresholdBtn)
                        
            #             self.disableBtn = self.EnableDisableButton(self)
            #             self.add_item(self.disableBtn)
                        
            #             self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 2) 
            #             self.backBtn.callback = self.backBtnCallback
            #             self.add_item(self.backBtn)
                        
            #         async def setup(self, interaction: Interaction):
            #             # Redirect to Activation Screen if needed
            #             server = Server_DEP(interaction.guild.id)
            #             if not server.spam_moderation_enabled: 
            #                 await self.EnableDisableButton.EnableDisableView(self).setup(interaction)
            #                 return
                        
            #             if self.onboarding_modifier: self.onboarding_modifier(self)
                        
            #             server = Server_DEP(interaction.guild.id)
                        
            #             if not utils.enabled.SpamModeration(server = server):
            #                 await ui_components.disabled_feature_override(self, interaction)
            #                 return
                        
                        
            #             description = f"""
            #             InfiniBot contributes to the battle against spam in your server. Customize the options below to tailor them to your server's needs.
                        
            #             **Settings**
            #             Timeout Duration: {server.spam_timeout_time}
            #             Messages Threshold: {server.messages_threshold} messages
                        
            #             For more information, use: {spamModerationHelp.get_mention()}"""
            #             description = utils.standardize_str_indention(description)
                        
            #             embed = nextcord.Embed(title = "Dashboard - Moderation - Spam", 
            #                                    description = description, 
            #                                    color = nextcord.Color.blue())
                        
            #             if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
            #             else: embeds = [embed]
                        
            #             await interaction.response.edit_message(embeds = embeds, view = self)
                    
            #         async def backBtnCallback(self, interaction: Interaction):
            #             await self.outer.setup(interaction)
                                                     
            #         class TimeoutDurationButton(nextcord.ui.Button):
            #             def __init__(self, outer):
            #                 super().__init__(label = "Timeout Duration", style = nextcord.ButtonStyle.gray)
            #                 self.outer = outer
                            
            #             class TimeoutDurationModal(nextcord.ui.Modal): #Timeout Duration Modal -----------------------------------------------------
            #                 def __init__(self, outer, guild_id):
            #                     super().__init__(title = "Timeout Duration")
            #                     self.outer = outer
            #                     server = Server_DEP(guild_id)
                                
            #                     self.input = nextcord.ui.TextInput(label = "Timeout Duration (Format: 5s, 10m, 1h, 2d)", default_value = server.spam_timeout_time, placeholder = "This Field is Required", max_length=10)
            #                     self.add_item(self.input)
                                
            #                 async def callback(self, interaction: Interaction):
            #                     if self.input.value == "" or self.input.value == None:
            #                         await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Timeout Time needs to be like this: 10s, 20s, 1m, 30m, 1h, 5h, 1d", color = nextcord.Color.red()), ephemeral=True)
            #                         return
                                
            #                     try:
            #                         humanfriendly.parse_timespan(self.input.value)
            #                     except:
            #                         await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Timeout Time needs to be like this: 10s, 20s, 1m, 30m, 1h, 5h, 1d", color = nextcord.Color.red()), ephemeral=True)
            #                         return
                                
            #                     server = Server_DEP(interaction.guild.id)
            #                     server.spam_timeout_time = self.input.value
            #                     server.saveData()
            #                     await self.outer.setup(interaction)
                                
            #             async def callback(self, interaction: Interaction):
            #                 await interaction.response.send_modal(self.TimeoutDurationModal(self.outer, interaction.guild.id))
                         
            #         class MessagesThresholdButton(nextcord.ui.Button):
            #             def __init__(self, outer):
            #                 super().__init__(label = "Messages Threshold", style = nextcord.ButtonStyle.gray)
            #                 self.outer = outer
                            
            #             class MessagesThresholdModal(nextcord.ui.Modal): #Timeout Duration Modal -----------------------------------------------------
            #                 def __init__(self, outer, guild_id):
            #                     super().__init__(title = "Message Threshold")
            #                     self.outer = outer
            #                     server = Server_DEP(guild_id)
                                
            #                     self.input = nextcord.ui.TextInput(label = "Message Threshold (# of messages)", default_value = server.messages_threshold, placeholder = "This Field is Required", max_length=2)
            #                     self.add_item(self.input)
                                
            #                 async def callback(self, interaction: Interaction):
            #                     if self.input.value == "" or self.input.value == None:
            #                         return
                                
            #                     try:
            #                         int(self.input.value)
            #                     except:
            #                         await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The messages threshold needs to be a number", color = nextcord.Color.red()), ephemeral=True)
            #                         return
                                
            #                     server = Server_DEP(interaction.guild.id)
            #                     server.messages_threshold = int(self.input.value)
            #                     server.saveData()
            #                     await self.outer.setup(interaction)
                                
            #             async def callback(self, interaction: Interaction):
            #                 await interaction.response.send_modal(self.MessagesThresholdModal(self.outer, interaction.guild.id))

            #         class EnableDisableButton(nextcord.ui.Button):
            #             def __init__(self, outer):
            #                 super().__init__(label = "Disable Spam Moderation", row = 1)
            #                 self.outer = outer
                            
            #             class EnableDisableView(nextcord.ui.View):
            #                 def __init__(self, outer):
            #                     super().__init__(timeout = None)
            #                     self.outer = outer
                                
            #                     self.backBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
            #                     self.backBtn.callback = self.backBtnCallback
            #                     self.add_item(self.backBtn)
                                
            #                     self.actionBtn = nextcord.ui.Button(label = "ACTION", style = nextcord.ButtonStyle.green)
            #                     self.actionBtn.callback = self.actionBtnCallback
            #                     self.add_item(self.actionBtn)
                                
                                
            #                 async def setup(self, interaction: Interaction, server = None):
            #                     if not server: server = Server_DEP(interaction.guild.id)
                                
            #                     # Determine whether or not we are active or not.
            #                     if server.spam_moderation_enabled:
            #                         # We *are* active. Give info for deactivation
            #                         embed = nextcord.Embed(title = "Dashboard - Moderation - Spam - Disable", 
            #                                                description = "Are you sure you want to disable spam moderation? You can re-enable this feature at any time.",
            #                                                color = nextcord.Color.blue())
            #                         self.actionBtn.label = "Disable"
                                    
            #                     else:
            #                         # We are *not* active. Give info for activation
            #                         embed = nextcord.Embed(title = "Dashboard - Moderation - Spam",
            #                                                description = "Spam moderation is currently disabled. Do you want to enable it?",
            #                                                color = nextcord.Color.blue())
            #                         self.actionBtn.label = "Enable"
                                    
            #                     await interaction.response.edit_message(embed = embed, view = self)
                                
            #                 async def backBtnCallback(self, interaction: Interaction, server = None):
            #                     if not server: server = Server_DEP(interaction.guild.id)
                                
            #                     # Return either to spam moderation or moderation.
            #                     if server.spam_moderation_enabled:
            #                         # Enabled. Put us in here.
            #                         await self.outer.setup(interaction)
                                    
            #                     else:
            #                         # Disabled. Put us in the level above
            #                         await self.outer.outer.setup(interaction)
                                
            #                 async def actionBtnCallback(self, interaction: Interaction):
            #                     server = Server_DEP(interaction.guild.id)
                                
            #                     server.spam_moderation_enabled = (not server.spam_moderation_enabled)
                                
            #                     server.saveData()
                                
            #                     # Return them.
            #                     await self.backBtnCallback(interaction, server = server)
                            
            #             async def callback(self, interaction: Interaction):
            #                 await self.EnableDisableView(self.outer).setup(interaction)
                                                                     
            #     async def callback(self, interaction: Interaction):
            #         view = self.SpamModerationView(self.outer)
            #         await view.setup(interaction)
                                                                
        async def callback(self, interaction: Interaction):
            view = self.ModerationView(self.outer)
            await view.setup(interaction)
            
    # class LoggingButton(nextcord.ui.Button):
    #     def __init__(self, outer):
    #         super().__init__(label = "Logging", style = nextcord.ButtonStyle.gray)
    #         self.outer = outer
            
    #     class LoggingView(nextcord.ui.View): #Logging Window -----------------------------------------------------
    #         def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
    #             super().__init__(timeout = None)
    #             self.outer = outer
    #             self.onboarding_modifier = onboarding_modifier
    #             self.onboarding_embed = onboarding_embed
                
    #             self.logChannelBtn = self.LogChannelButton(self)
    #             self.add_item(self.logChannelBtn)
                
    #             self.disableBtn = self.EnableDisableButton(self)
    #             self.add_item(self.disableBtn)
                
    #             self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
    #             self.backBtn.callback = self.backBtnCallback
    #             self.add_item(self.backBtn)
                
    #         async def setup(self, interaction: Interaction):
    #             # Redirect to Activation Screen if needed
    #             server = Server_DEP(interaction.guild.id)
    #             if not server.logging_enabled: 
    #                 await self.EnableDisableButton.EnableDisableView(self).setup(interaction)
    #                 return
                
    #             if self.onboarding_modifier: self.onboarding_modifier(self)
                
    #             # Clean up
    #             if not self.onboarding_modifier:
    #                 for child in self.children: 
    #                     del child 
    #                     self.__init__(self.outer)
                
    #             server = Server_DEP(interaction.guild.id)
                
    #             # Global Kill
    #             if not utils.enabled.Logging(server = server):
    #                 await ui_components.disabled_feature_override(self, interaction)
    #                 return
                
    #             if server.log_channel == None:
    #                 await self.logChannelBtn.callback(interaction, skipped = True)
    #                 return
                
    #             if server.log_channel != None: log_channel_name = server.log_channel.mention
    #             else: log_channel_name = "None"

    #             description = f"""
    #             InfiniBot enhances server management with comprehensive logging. View deleted and edited messages, and administrative changes.
                
    #             **Settings**
    #             Log Channel: {log_channel_name}
                
    #             For more information, use: {loggingHelp.get_mention()}"""
    #             description = utils.standardize_str_indention(description)
                
    #             embed = nextcord.Embed(title = "Dashboard - Logging", 
    #                                    description = description, 
    #                                    color = nextcord.Color.blue())
                
    #             if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
    #             else: embeds = [embed]
                
    #             await interaction.response.edit_message(embeds = embeds, view = self)
                
    #         async def backBtnCallback(self, interaction: Interaction):
    #             await self.outer.setup(interaction)
            
    #         class LogChannelButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Log Channel", style = nextcord.ButtonStyle.gray)
    #                 self.outer = outer
    #                 self.skipped = False
           
    #             async def callback(self, interaction: Interaction, skipped = False):
    #                 self.skipped = skipped
                    
    #                 server = Server_DEP(interaction.guild.id)
                        
    #                 selectOptions = []
    #                 for channel in interaction.guild.text_channels:
    #                     if channel.category != None: categoryName = channel.category.name
    #                     else: categoryName = None
    #                     selectOptions.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.log_channel != None and server.log_channel.id == channel.id)))
                    
    #                 description = """
    #                 Choose a channel for logs.

    #                 Tip: Set notification settings for this channel to "Nothing". InfiniBot will constantly be logging in this channel."""
    #                 description = utils.standardize_str_indention(description)
                    
    #                 embed = nextcord.Embed(title = ("Dashboard - Logging" if self.skipped else "Dashboard - Logging - Log Channel"), 
    #                                        description = description, color = nextcord.Color.blue())
                    
    #                 await ui_components.SelectView(embed, 
    #                                  selectOptions, 
    #                                  self.SelectViewCallback, 
    #                                  continueButtonLabel = "Confirm", 
    #                                  cancelButtonLabel = ("Back" if self.skipped else "Cancel")).setup(interaction)
                    
    #             async def SelectViewCallback(self, interaction: Interaction, selection):
    #                 if selection == None:
    #                     if self.skipped: await self.outer.outer.setup(interaction)
    #                     else: await self.outer.setup(interaction)
    #                     return
                    
    #                 server = Server_DEP(interaction.guild.id)
    #                 if server.setLogChannelID(selection):
    #                     server.saveData()
    #                 await self.outer.setup(interaction)
                    
    #                 embed = nextcord.Embed(title = "Log Channel Set", description = f"This channel will now be used for logging.\n\nTip: Set notification settings for this channel to \"Nothing\". InfiniBot will constantly be logging in this channel.", color =  nextcord.Color.green())
    #                 embed.set_footer(text = f"Action done by {interaction.user}")
    #                 await server.log_channel.send(embed = embed, view = SupportAndInviteView())
            
    #         class EnableDisableButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Disable Logging")
    #                 self.outer = outer
                    
    #             class EnableDisableView(nextcord.ui.View):
    #                 def __init__(self, outer):
    #                     super().__init__(timeout = None)
    #                     self.outer = outer
                        
    #                     self.backBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
    #                     self.backBtn.callback = self.backBtnCallback
    #                     self.add_item(self.backBtn)
                        
    #                     self.actionBtn = nextcord.ui.Button(label = "ACTION", style = nextcord.ButtonStyle.green)
    #                     self.actionBtn.callback = self.actionBtnCallback
    #                     self.add_item(self.actionBtn)
                                           
    #                 async def setup(self, interaction: Interaction, server = None):
    #                     if not server: server = Server_DEP(interaction.guild.id)
                        
    #                     # Determine whether or not we are active or not.
    #                     if server.logging_enabled:
    #                         # We *are* active. Give info for deactivation
    #                         embed = nextcord.Embed(title = "Dashboard - Logging - Disable", 
    #                                                 description = "Are you sure you want to disable logging? You can re-enable this feature at any time.",
    #                                                 color = nextcord.Color.blue())
    #                         self.actionBtn.label = "Disable"
                            
    #                     else:
    #                         # We are *not* active. Give info for activation
    #                         embed = nextcord.Embed(title = "Dashboard - Logging",
    #                                                 description = "Logging is currently disabled. Do you want to enable it?",
    #                                                 color = nextcord.Color.blue())
    #                         self.actionBtn.label = "Enable"
                            
    #                     await interaction.response.edit_message(embed = embed, view = self)
                        
    #                 async def backBtnCallback(self, interaction: Interaction, server = None):
    #                     if not server: server = Server_DEP(interaction.guild.id)
                        
    #                     # Return either to logging or dashboard
    #                     if server.logging_enabled:
    #                         # Enabled. Put us in here.
    #                         await self.outer.setup(interaction)
                            
    #                     else:
    #                         # Disabled. Put us in the level above (dashboard)
    #                         await self.outer.outer.setup(interaction)
                        
    #                 async def actionBtnCallback(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     server.logging_enabled = (not server.logging_enabled)
                        
    #                     server.saveData()
                        
    #                     # Return them.
    #                     await self.backBtnCallback(interaction, server = server)
                    
    #             async def callback(self, interaction: Interaction):
    #                 await self.EnableDisableView(self.outer).setup(interaction)
                        
    #     async def callback(self, interaction: Interaction):
    #         await self.LoggingView(self.outer).setup(interaction)

    # class LevelingButton(nextcord.ui.Button):
    #     def __init__(self, outer):
    #         super().__init__(label = "Leveling", style = nextcord.ButtonStyle.gray)
    #         self.outer = outer
            
    #     class LevelingView(nextcord.ui.View):
    #         def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
    #             super().__init__(timeout = None)
    #             self.outer = outer
    #             self.onboarding_modifier = onboarding_modifier
    #             self.onboarding_embed = onboarding_embed
                
    #             self.manageMembersBtn = self.ManageMembersButton(self)
    #             self.add_item(self.manageMembersBtn)
                
    #             self.levelRewardsBtn = self.LevelRewardsButton(self)
    #             self.add_item(self.levelRewardsBtn)
                
    #             self.levelingMessageBtn = self.LevelingMessageButton(self)
    #             self.add_item(self.levelingMessageBtn)
                
    #             self.levelingChannelBtn = self.LevelingChannelButton(self)
    #             self.add_item(self.levelingChannelBtn)
                
    #             self.pointsLostPerDayBtn = self.PointsLostPerDayButton(self)
    #             self.add_item(self.pointsLostPerDayBtn)
                
    #             self.exemptChannelsBtn = self.ExemptChannelsButton(self)
    #             self.add_item(self.exemptChannelsBtn)
                
    #             self.levelCardsBtn = self.LevelCardsButton(self)
    #             self.add_item(self.levelCardsBtn)
                
    #             self.disableBtn = self.EnableDisableButton(self)
    #             self.add_item(self.disableBtn)
                
    #             self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 4)
    #             self.backBtn.callback = self.backBtnCallback
    #             self.add_item(self.backBtn)
                
    #         async def setup(self, interaction: Interaction):
    #             # Redirect to Activation Screen if needed
    #             server = Server_DEP(interaction.guild.id)
    #             if not server.leveling_enabled: 
    #                 await self.EnableDisableButton.EnableDisableView(self).setup(interaction)
    #                 return
                
    #             if self.onboarding_modifier: self.onboarding_modifier(self)
                        
    #             # Clean up
    #             if not self.onboarding_modifier:
    #                 for child in self.children: 
    #                     del child 
    #                     self.__init__(self.outer)
                
    #             server = Server_DEP(interaction.guild.id)
                
    #             if not utils.enabled.Leveling(server = server):
    #                 await ui_components.disabled_feature_override(self, interaction)
    #                 return
                
    #             if server.leveling_channel == False: levelingChannelName = "No Notifications"
    #             elif server.leveling_channel != None: levelingChannelName = server.leveling_channel.mention
    #             else: levelingChannelName = "System Messages Channel"
                
    #             if server.points_lost_per_day != None: pointsLostPerDay = server.points_lost_per_day
    #             else: pointsLostPerDay = "DISABLED"
                
    #             if server.leveling_channel == False: levelingMessage = "N/A"
    #             elif server.leveling_message != None: levelingMessage = f"```{server.leveling_message}```"
    #             else: levelingMessage = "DISABLED" # This is in theory depricated
                
    #             if server.allow_level_cards_bool: allowLevelCards = "Yes"
    #             else: allowLevelCards = "No"
                
    #             description = f"""
    #             InfiniBot enhances server engagement through leveling. Tailor the options below to align with your server's preferences.
                
    #             **Settings:**
    #             Notifications Channel: {levelingChannelName}
    #             Points Lost Per Day: {pointsLostPerDay}
    #             Allow Level-Up Cards: {allowLevelCards}
    #             Level Up Message: {levelingMessage}
                
    #             **What are Level-Up Cards?**
    #             When enabled, members can craft personalized level-up cards displayed after each level-up message.
                
    #             For more information, use: {levelingHelp.get_mention()}
    #             """
    #             description = utils.standardize_str_indention(description)
                
    #             embed = nextcord.Embed(title = "Dashboard - Leveling", 
    #                                    description = description, 
    #                                    color = nextcord.Color.blue())
                
    #             if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
    #             else: embeds = [embed]
                
    #             # Update buttons
    #             self.levelingMessageBtn.disabled = (server.leveling_channel == False)
                
    #             await interaction.response.edit_message(embeds = embeds, view = self)
             
    #         async def backBtnCallback(self, interaction: Interaction):
    #             await self.outer.setup(interaction)
                
    #         class ManageMembersButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Manage Members", style = nextcord.ButtonStyle.gray)
    #                 self.outer = outer
                    
    #             class MembersView(nextcord.ui.View):#Members View Window -----------------------------------------------------
    #                 def __init__(self, outer):
    #                     super().__init__(timeout=None)
    #                     self.outer = outer
                        
    #                     self.editLevelBtn = self.EditLevelButton(self)
    #                     self.add_item(self.editLevelBtn)
                        
    #                     self.deleteAllLevelsBtn = self.DeleteAllLevelsButton(self)
    #                     self.add_item(self.deleteAllLevelsBtn)
                        
    #                     self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
    #                     self.backBtn.callback = self.backBtnCallback
    #                     self.add_item(self.backBtn)
                        
    #                 async def setup(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
    #                     if not await canLevel(interaction, server): return
                        
    #                     self.rankedMembers = []
                        
    #                     for member in interaction.guild.members: 
    #                         if member.bot: continue
                            
    #                         Member = server.levels.getMember(member.id)
    #                         self.rankedMembers.append([member, Member.score])
                        
                        
    #                     # Sort
    #                     self.rankedMembers = sorted(self.rankedMembers, key=lambda x: (-x[1], x[0].name))


    #                     self.embed = nextcord.Embed(title = "Dashboard - Leveling - Manage Members", color = nextcord.Color.blue())
                        
    #                     rank, lastScore = 1, 0
    #                     for index, member in enumerate(self.rankedMembers): 
    #                         if index < 20:
    #                             level = getLevel(member[1])
    #                             if member[0].nick != None: memberName = f"{member[0]} ({member[0].nick})"
    #                             else: memberName = f"{member[0]}"
                                
    #                             if member[1] < lastScore:
    #                                 rank += 1
    #                             lastScore = member[1]
                            
    #                             self.embed.add_field(name = f"**#{rank} {memberName}**", value = f"Level: {str(level)}, Score: {str(member[1])}", inline = False)
    #                         else:
    #                             self.embed.add_field(name = f"+ {str(len(self.rankedMembers) - 20)} more", value = f"To see a specific member's level, type */level [member]*", inline = False)
    #                             break
                        
    #                     await interaction.response.edit_message(embed = self.embed, view = self)
                        
    #                 async def backBtnCallback(self, interaction: Interaction):
    #                     await self.outer.setup(interaction)
    #                     await interaction.edit_original_message(view = self.outer)
                        
    #                 class EditLevelButton(nextcord.ui.Button):
    #                     def __init__(self, outer):
    #                         super().__init__(label = "Edit", style = nextcord.ButtonStyle.gray)
    #                         self.outer = outer
                                                        
    #                     class levelModal(nextcord.ui.Modal):
    #                         def __init__(self, outer, memberID, defaultLevel):
    #                             super().__init__(title = "Choose Level")
    #                             self.outer = outer
    #                             self.member_id = memberID

    #                             self.input = nextcord.ui.TextInput(label = "Choose a level. Must be a number", default_value=str(defaultLevel))
    #                             self.add_item(self.input)
                                
    #                         async def callback(self, interaction: Interaction):
    #                             # Check
    #                             if (not self.input.value.isdigit()) or int(self.input.value) < 0:
    #                                 embed = nextcord.Embed(title = "Invalid Level", description = "The level needs to be a positive number.", color = nextcord.Color.red())
    #                                 await interaction.response.send_message(embed = embed, ephemeral = True)
    #                                 return
                                
    #                             member_id = self.member_id
    #                             level = int(self.input.value)
                                
    #                             if member_id == None: return
                                
    #                             server = Server_DEP(interaction.guild.id)
    #                             member_info = server.levels.getMember(member_id)
    #                             member_info.score = getScore(level)
    #                             server.saveLevels()

    #                             await self.outer.setup(interaction)
                                
    #                             # Get the member
    #                             discord_member = None
    #                             for _member in interaction.guild.members:
    #                                 if _member.id == int(member_id):
    #                                     discord_member = _member
                                
    #                             #check their level rewards
    #                             await checkForLevelsAndLevelRewards(interaction.guild, discord_member, silent = True)  
                                                       
    #                     async def callback(self, interaction: Interaction):# Edit Levels Callback ————————————————————————————————————————————————————————————
    #                         memberSelectOptions:list[nextcord.SelectOption] = []
    #                         for data in self.outer.rankedMembers:
    #                             level = getLevel(data[1])
    #                             member = data[0]
    #                             if member.nick != None: memberName = f"{member} ({member.nick})"
    #                             else: memberName = f"{member}"
                            
    #                             memberSelectOptions.append(nextcord.SelectOption(label = f"{memberName} - Level {str(level)}, Score - {str(data[1])}", value = data[0].id))
                            
    #                         embed: nextcord.Embed = copy.copy(self.outer.embed)
    #                         embed.description = "Choose a Member"
    #                         await ui_components.SelectView(embed, memberSelectOptions, self.selectViewCallback, continueButtonLabel = "Next", placeholder = "Choose", preserveOrder = True).setup(interaction)
                        
    #                     async def selectViewCallback(self, interaction: Interaction, selection):       
    #                         if selection == None:
    #                             await self.outer.setup(interaction)
    #                             return
                            
    #                         memberID = selection
    #                         server = Server_DEP(interaction.guild.id)
    #                         Member = server.levels.getMember(memberID)
    #                         if Member != None: score = Member.score
    #                         else: score = 0
                                    
    #                         await interaction.response.send_modal(self.levelModal(self.outer, selection, getLevel(score)))
                    
    #                 class DeleteAllLevelsButton(nextcord.ui.Button):
    #                     def __init__(self, outer):
    #                         super().__init__(label = "Reset", style = nextcord.ButtonStyle.gray)
    #                         self.outer = outer
                            
    #                     class DeleteAllLevelsView(nextcord.ui.View):
    #                         def __init__(self, outer):
    #                             super().__init__(timeout = None)
    #                             self.outer = outer
                                
    #                             self.noBtn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
    #                             self.noBtn.callback = self.noBtnCommand
    #                             self.add_item(self.noBtn)
                                
    #                             self.yesBtn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
    #                             self.yesBtn.callback = self.yesBtnCommand
    #                             self.add_item(self.yesBtn)
                                
    #                         async def setup(self, interaction: Interaction):
    #                             embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will reset all levels in the server to 0.\nThis action cannot be undone.", color = nextcord.Color.blue())
    #                             await interaction.response.edit_message(embed = embed, view = self)
                                
    #                         async def noBtnCommand(self, interaction: Interaction):
    #                             await self.outer.setup(interaction)
                                
    #                         async def yesBtnCommand(self, interaction: Interaction):
    #                             server = Server_DEP(interaction.guild.id)
    #                             server.levels.all_members = []
    #                             server.saveLevels()
    #                             await self.outer.setup(interaction)
                            
    #                     async def callback(self, interaction: Interaction):
    #                         await self.DeleteAllLevelsView(self.outer).setup(interaction)
                    
    #             async def callback(self, interaction: Interaction): # Strikes Callback ————————————————————————————————————————————————————————————
    #                 view = self.MembersView(self.outer)
    #                 await view.setup(interaction)
            
    #         class LevelRewardsButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Level Rewards", style = nextcord.ButtonStyle.gray)
    #                 self.outer = outer
                    
    #             class LevelRewardsView(nextcord.ui.View): #Level Rewards Window -----------------------------------------------------
    #                 def __init__(self, outer):
    #                     super().__init__(timeout = None)
    #                     self.outer = outer
                        
    #                     self.createLevelRewardBtn = self.CreateLevelRewardButton(self)
    #                     self.add_item(self.createLevelRewardBtn)
                        
    #                     self.deleteLevelRewardsBtn = self.DeleteLevelRewardButton(self)
    #                     self.add_item(self.deleteLevelRewardsBtn)
                        
    #                     self.deleteAllLevelRewardsBtn = self.DeleteAllLevelRewardsBtn(self)
    #                     self.add_item(self.deleteAllLevelRewardsBtn)
                        
    #                     self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
    #                     self.backBtn.callback = self.backBtnCallback
    #                     self.add_item(self.backBtn)
                        
    #                 async def setup(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     if not utils.enabled.LevelRewards(server = server):
    #                         await ui_components.disabled_feature_override(self, interaction)
    #                         return
                        
    #                     self.embed = nextcord.Embed(title = "Dashboard - Leveling - Level Rewards", 
    #                                                 description = "Unlock roles as you progress through levels on the server.",
    #                                                 color = nextcord.Color.blue())
                        
    #                     levelRewards = []
    #                     for levelReward in server.levels.level_rewards: 
    #                         if levelReward.role != None: #code should be obsolete. This is a security precaution
    #                             levelRewards.append(f"{levelReward.role.mention} - Level {levelReward.level}")
                                
    #                     if levelRewards == []: levelRewards.append("You don't have any level rewards set up. Create one!")
    #                     self.embed.add_field(name = "Level Rewards", value = "\n".join(levelRewards))
    #                     try: await interaction.response.edit_message(embed = self.embed, view = self)
    #                     except: await interaction.edit_original_message(embed = self.embed, view = self)
                        
    #                 async def backBtnCallback(self, interaction: Interaction):
    #                     await self.outer.setup(interaction)
    #                     await interaction.edit_original_message(view = self.outer)
                                                                   
    #                 class CreateLevelRewardButton(nextcord.ui.Button):
    #                     def __init__(self, outer):
    #                         super().__init__(label = "Create", style = nextcord.ButtonStyle.gray)
    #                         self.outer = outer
                                               
    #                     async def callback(self, interaction: Interaction):
    #                         server = Server_DEP(interaction.guild.id)
    #                         allLevelRewardRoles = [levelReward.role for levelReward in server.levels.level_rewards]
                            
    #                         selectOptions = []
    #                         for role in interaction.guild.roles:
    #                             if role.name == "@everyone": continue
    #                             if not canAssignRole(role): continue
    #                             if role not in allLevelRewardRoles: selectOptions.append(nextcord.SelectOption(label = role.name, description = role.id, value = role.id))
                            
    #                         if selectOptions == []:
    #                             await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", description = "You've run out of roles to use! To fix this, either promote InfiniBot to the highest role, give InfiniBot Administrator, or add more roles to the server!", color = nextcord.Color.red()), ephemeral=True)             
                                        
    #                         else:
    #                             embed = nextcord.Embed(title = "Dashboard - Leveling - Level Rewards - Add",
    #                                                    description = "Select a role to be rewarded.\n\n**Note**\nThe selected role will be revoked from members below the specified level requirement (to be set later).",
    #                                                    color = nextcord.Color.blue())
    #                             await ui_components.SelectView(embed, selectOptions, self.selectViewCallback, continueButtonLabel = "Next", placeholder = "Choose").setup(interaction)            
                            
    #                     async def selectViewCallback(self, interaction: Interaction, selection):
    #                         if selection == None: 
    #                             await self.outer.setup(interaction) 
    #                             return
                            
    #                         await interaction.response.send_modal(self.levelModal(self.outer, selection))
                                                
    #                     class levelModal(nextcord.ui.Modal):
    #                         def __init__(self, outer, selection):
    #                             super().__init__(title = "Choose Level")
    #                             self.outer = outer
    #                             self.selection = selection
                                
    #                             self.input = nextcord.ui.TextInput(label = "Level at which to reward this role (number)")
    #                             self.add_item(self.input)
                                
    #                         async def callback(self, interaction: Interaction):
    #                             role = self.selection
    #                             level = int(self.input.value)
                                
    #                             server = Server_DEP(interaction.guild.id)
    #                             server.levels.addLevelReward(role, level)
    #                             server.saveLevelRewards()
                                        
    #                             await self.outer.setup(interaction)
                                
    #                             discordRole = interaction.guild.get_role(int(role))
                                
    #                             await interaction.followup.send(embed = nextcord.Embed(title = "Level Reward Created", description = f"{discordRole.mention} is now assigned to level {str(level)}.\n\n**Note**\nThis will mean that this role will be revoked to anyone who is below level {str(level)}.", color = nextcord.Color.green()), ephemeral=True)                  

    #                             #update the level rewards for everyone
    #                             for member in interaction.guild.members:
    #                                 await checkForLevelsAndLevelRewards(interaction.guild, member, silent = True)
                    
    #                 class DeleteLevelRewardButton(nextcord.ui.Button):
    #                     def __init__(self, outer):
    #                         super().__init__(label = "Delete", style = nextcord.ButtonStyle.gray)
    #                         self.outer = outer
                            
    #                     class DeleteLevelRewardView(nextcord.ui.View): #Delete Level Reward Window -----------------------------------------------------
    #                         def __init__(self, outer, guild: nextcord.Guild):
    #                             super().__init__(timeout=None)
    #                             self.outer = outer
                                
    #                             self.cancelBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
    #                             self.cancelBtn.callback = self.cancelBtnCallback
    #                             self.add_item(self.cancelBtn)
                                
    #                             self.confirmBtn = self.DeleteButton(self.outer, self, guild.id)
    #                             self.add_item(self.confirmBtn)
                                
    #                         async def setup(self, interaction: Interaction):
    #                             server = Server_DEP(interaction.guild.id)
    #                             allLevelRewardRoles = [levelReward.role for levelReward in server.levels.level_rewards]
                                
    #                             selectOptions = [nextcord.SelectOption(label = role.name, description = role.id, value = role.id) for role in allLevelRewardRoles]
                                
    #                             if selectOptions != []:
    #                                 self.roleSelect = nextcord.ui.Select(options = selectOptions, placeholder = "Choose")
    #                                 self.add_item(self.roleSelect)
    #                                 await interaction.response.edit_message(view = self)
                                    
    #                             else:
    #                                 await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", description = "You don't have any level rewards set up!", color = nextcord.Color.red()), ephemeral=True)                     
                                                                                          
    #                         async def cancelBtnCallback(self, interaction: Interaction):
    #                             await self.outer.setup(interaction)
                                                          
    #                     async def callback(self, interaction: Interaction):# Delete Level Reward Callback ————————————————————————————————————————————————————————————
    #                         server = Server_DEP(interaction.guild.id)
    #                         allLevelRewardRoles = [levelReward.role for levelReward in server.levels.level_rewards]
                            
    #                         selectOptions = [nextcord.SelectOption(label = role.name, description = role.id, value = role.id) for role in allLevelRewardRoles]
                            
    #                         if selectOptions == []:
    #                             await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", description = "You don't have any level rewards set up!", color = nextcord.Color.red()), ephemeral=True)                     
    #                         else:
    #                             embed = nextcord.Embed(title = "Dashboard - Leveling - Level Rewards - Delete",
    #                                                    description = "Select a level reward to delete. This does not delete the role.",
    #                                                    color = nextcord.Color.blue())
    #                             await ui_components.SelectView(embed, selectOptions, self.selectViewCallback, continueButtonLabel = "Delete", placeholder = "Choose").setup(interaction)
                   
    #                     async def selectViewCallback(self, interaction: Interaction, selection):
    #                         if selection == None:
    #                             await self.outer.setup(interaction)
    #                             return
                            
    #                         server = Server_DEP(interaction.guild.id)
    #                         server.levels.deleteLevelReward(int(selection))
    #                         server.saveLevelRewards()
                            
    #                         await self.outer.setup(interaction)
                   
    #                 class DeleteAllLevelRewardsBtn(nextcord.ui.Button):
    #                     def __init__(self, outer):
    #                         super().__init__(label = "Delete All", style = nextcord.ButtonStyle.gray)
    #                         self.outer = outer
                            
    #                     class DeleteAllLevelsView(nextcord.ui.View):
    #                         def __init__(self, outer):
    #                             super().__init__(timeout = None)
    #                             self.outer = outer
                                
    #                             self.noBtn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
    #                             self.noBtn.callback = self.noBtnCommand
    #                             self.add_item(self.noBtn)
                                
    #                             self.yesBtn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
    #                             self.yesBtn.callback = self.yesBtnCommand
    #                             self.add_item(self.yesBtn)
                                
    #                         async def setup(self, interaction: Interaction):
    #                             embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will delete all level rewards in the server.\nThis action cannot be undone.", color = nextcord.Color.blue())
    #                             await interaction.response.edit_message(embed = embed, view = self)
                                
    #                         async def noBtnCommand(self, interaction: Interaction):
    #                             await self.outer.setup(interaction)
                                
    #                         async def yesBtnCommand(self, interaction: Interaction):
    #                             server = Server_DEP(interaction.guild.id)
    #                             server.levels.level_rewards = []
    #                             server.saveLevelRewards()
    #                             await self.outer.setup(interaction)
                                
    #                         async def callback(self, interaction: Interaction):
    #                             await self.DeleteAllLevelsView(self.outer).setup(interaction)
                        
    #                     async def callback(self, interaction: Interaction):
    #                         await self.DeleteAllLevelsView(self.outer).setup(interaction)
                    
    #             async def callback(self, interaction: Interaction): #Filtered Words Button Callback ————————————————————————————————————————————————————————————
    #                 view = self.LevelRewardsView(self.outer)
    #                 await view.setup(interaction)           
                    
    #         class LevelingMessageButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Level Up Message", style = nextcord.ButtonStyle.gray, row  = 1)
    #                 self.outer = outer
                    
    #             class LevelingMessageModal(nextcord.ui.Modal): #Leveling Message Modal -----------------------------------------------------
    #                 def __init__(self, guild: nextcord.Guild, outer):
    #                     super().__init__(timeout = None, title = "Level Up Message")
    #                     self.outer = outer
                        
    #                     server = Server_DEP(guild.id)
                        
    #                     self.levelingMessageTextInput = nextcord.ui.TextInput(label = "Message ([level] = Level)", style = nextcord.TextInputStyle.paragraph, max_length=1024, default_value = server.leveling_message, placeholder = "Congrats! You reached level [level")
    #                     self.add_item(self.levelingMessageTextInput)
                        
    #                 async def callback(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     server.leveling_message = self.levelingMessageTextInput.value
                            
    #                     server.saveData()
                        
    #                     await self.outer.setup(interaction)
                                         
    #             async def callback(self, interaction: Interaction):
    #                 await interaction.response.send_modal(self.LevelingMessageModal(interaction.guild, self.outer))                                     
                    
    #         class LevelingChannelButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Notifications Channel", style = nextcord.ButtonStyle.gray, row = 1)
    #                 self.outer = outer
            
    #             async def callback(self, interaction: Interaction):
    #                 server = Server_DEP(interaction.guild.id)
    #                 selectOptions = [
    #                     nextcord.SelectOption(label = "No Notifications", value = "__DISABLED__", description = "Do not notify about level updates.", default = (server.leveling_channel == False)),
    #                     nextcord.SelectOption(label = "System Messages Channel", value = "__NONE__", description = "Display in system messages channel", default = (server.leveling_channel == None))
    #                     ]
    #                 for channel in interaction.guild.text_channels:
    #                     if channel.category != None: categoryName = channel.category.name
    #                     else: categoryName = None
    #                     selectOptions.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.leveling_channel != None and server.leveling_channel != False and server.leveling_channel.id == channel.id)))
                        
    #                 embed = nextcord.Embed(title = "Dashboard - Leveling - Notifications Channel", description = "Select a channel to notify about level updates.", color = nextcord.Color.blue())
    #                 await ui_components.SelectView(embed, selectOptions, self.selectViewCallback).setup(interaction)

    #             async def selectViewCallback(self, interaction: Interaction, selection):
    #                 if selection == None:
    #                     await self.outer.setup(interaction)
    #                     return
                    
    #                 if selection == "__NONE__": value = None
    #                 elif selection == "__DISABLED__": value = False
    #                 else: value = selection
                    
    #                 server = Server_DEP(interaction.guild.id)
    #                 if server.setLevelingChannelID(value):
    #                     server.saveData()
    #                     await self.outer.setup(interaction)

    #         class PointsLostPerDayButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Points Lost Per Day", style = nextcord.ButtonStyle.gray, row  = 2)
    #                 self.outer = outer
                    
    #             class PointsLostPerDayModal(nextcord.ui.Modal): #Leveling Message Modal -----------------------------------------------------
    #                 def __init__(self, guild: nextcord.Guild, outer):
    #                     super().__init__(timeout = None, title = "Points Lost Per Day")
    #                     self.outer = outer
                        
    #                     server = Server_DEP(guild.id)
                        
    #                     self.pointsLostPerDayTextInput = nextcord.ui.TextInput(label = "Points (must be a number, blank = DISABLED)", style = nextcord.TextInputStyle.short, max_length=3, default_value = server.points_lost_per_day, required = False)
    #                     self.add_item(self.pointsLostPerDayTextInput)
                        
    #                 async def callback(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     value: str = self.pointsLostPerDayTextInput.value
    #                     if not (value == None or value == ""):
    #                         if not value.isnumeric() or int(value) < 0:
    #                             await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "\"Points\" must be a number and cannot be negative.", color = nextcord.Color.red()), ephemeral = True)
    #                             return
    #                         server.points_lost_per_day = int(value)
    #                         server.saveData()
                        
    #                         await self.outer.setup(interaction)
    #                         await interaction.followup.send(embed = nextcord.Embed(title = "Points Lost Per Day Set", description = f"Every day at midnight, everyone will loose {value} points.", color = nextcord.Color.green()), ephemeral = True)
                        
    #                     else:
    #                         server.points_lost_per_day = None
    #                         server.saveData()
                        
    #                         await self.outer.setup(interaction)
    #                         await interaction.followup.send(embed = nextcord.Embed(title = "Points Lost Per Day Disabled", description = f"InfiniBot will not take points from anyone at midnight.", color = nextcord.Color.green()), ephemeral = True)
                            
    #             async def callback(self, interaction: Interaction):
    #                 await interaction.response.send_modal(self.PointsLostPerDayModal(interaction.guild, self.outer))       
                                          
    #         class ExemptChannelsButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Exempt Channels", style = nextcord.ButtonStyle.gray, row = 2)
    #                 self.outer = outer
                    
    #             class ExemptChannelsView(nextcord.ui.View):
    #                 def __init__(self, outer, interaction: Interaction):
    #                     super().__init__(timeout = None)
    #                     self.outer = outer 
                        
    #                     addButton = self.AddButton(self, interaction)
    #                     self.add_item(addButton)
                        
    #                     deleteButton = self.DeleteButton(self, interaction)
    #                     self.add_item(deleteButton)
                        
    #                     self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
    #                     self.backBtn.callback = self.backBtnCallback
    #                     self.add_item(self.backBtn)
                                
    #                 async def setup(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
                        
                        
    #                     channels = "\n".join([f"• {channel.mention}" for channel in server.leveling_exempt_channels])
                        
    #                     if channels == "":
    #                         channels = "You don't have any exempt channels yet. Add one!"
                        
                        
    #                     description = f"**Select Channels that will not Grant Points when Messages are Sent**\n{channels}\n\n★ 20 Channels Maximum ★"
                        
    #                     embed = nextcord.Embed(title = "Dashboard - Leveling - Exempt Channels", description = description, color = nextcord.Color.blue())
    #                     await interaction.response.edit_message(embed = embed, view = self)
                    
    #                 async def reload(self, interaction: Interaction):
    #                     self.__init__(self.outer, interaction)
    #                     await self.setup(interaction)
                    
    #                 async def backBtnCallback(self, interaction: Interaction):
    #                     await self.outer.setup(interaction)
                    
    #                 class AddButton(nextcord.ui.Button):
    #                     def __init__(self, outer, interaction: Interaction):
    #                         server = Server_DEP(interaction.guild.id)
    #                         disabled = (len(server.leveling_exempt_channels) == 20)
    #                         super().__init__(label = "Add Channel", style = nextcord.ButtonStyle.gray, disabled = disabled)
    #                         self.outer = outer
                                                    
    #                     async def callback(self, interaction: Interaction):
    #                         options = []
    #                         server = Server_DEP(interaction.guild.id)
    #                         already_added_ids = [channel.id for channel in server.leveling_exempt_channels]
    #                         for channel in interaction.guild.channels:
    #                             if type(channel) != nextcord.TextChannel and type(channel) != nextcord.VoiceChannel: continue
    #                             if channel.id in already_added_ids: continue
    #                             channel_category = (channel.category.name if channel.category else None)
    #                             options.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = channel_category))
                            
    #                         if len(options) == 0:
    #                             await interaction.response.send_message(embed = nextcord.Embed(title = "No More Channels", description = "You've ran out of channels to exempt. Create more channels, or give InfiniBot higher permissions to see more channels!", color = nextcord.Color.red()), ephemeral = True)
    #                             return
                            
    #                         embed = nextcord.Embed(title = "Dashboard - Leveling - Exempt Channels - Add", description = "Choose a channel to make exempt (messages won't grant points in this channel)", color = nextcord.Color.blue())
    #                         ui_components.selectView = ui_components.SelectView(embed, options, self.selectCallback, placeholder = "Choose a Channel", continueButtonLabel = "Add Channel")
    #                         await ui_components.selectView.setup(interaction)
               
    #                     async def selectCallback(self, interaction: Interaction, choice):
    #                         if choice != None:
    #                             server = Server_DEP(interaction.guild.id)
    #                             server.leveling_exempt_channels.append(interaction.guild.get_channel(int(choice)))
    #                             server.saveData()
                                
    #                         await self.outer.reload(interaction)
 
    #                 class DeleteButton(nextcord.ui.Button):
    #                     def __init__(self, outer, interaction: Interaction):
    #                         server = Server_DEP(interaction.guild.id)
    #                         disabled = (len(server.leveling_exempt_channels) == 0)
    #                         super().__init__(label = "Delete Channel", style = nextcord.ButtonStyle.gray, disabled = disabled)
    #                         self.outer = outer
                                                    
    #                     async def callback(self, interaction: Interaction):
    #                         options = []
    #                         server = Server_DEP(interaction.guild.id)
    #                         for channel in server.leveling_exempt_channels:
    #                             channel_category = (channel.category.name if channel.category else None)
    #                             options.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = channel_category))
                            
    #                         embed = nextcord.Embed(title = "Dashboard - Leveling - Exempt Channels - Delete", description = "Choose a Channel to Remove from Exempt Channels", color = nextcord.Color.blue())
    #                         ui_components.selectView = ui_components.SelectView(embed, options, self.selectCallback, placeholder = "Choose a Channel", continueButtonLabel = "Delete Channel")
    #                         await ui_components.selectView.setup(interaction)
               
    #                     async def selectCallback(self, interaction: Interaction, choice):
    #                         if choice != None:
    #                             server = Server_DEP(interaction.guild.id)
    #                             for channel in server.leveling_exempt_channels:
    #                                 if channel.id == int(choice):
    #                                     server.leveling_exempt_channels.remove(channel) #usually, you would never do this in a loop. However, because we are only doing it once, this still works.
    #                                     pass

    #                             server.saveData()
                                
    #                         await self.outer.reload(interaction)
                    
    #             async def callback(self, interaction: Interaction):
    #                 await self.ExemptChannelsView(self.outer, interaction).setup(interaction)
       
    #         class LevelCardsButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Level-Up Cards", style = nextcord.ButtonStyle.gray, row = 3)
    #                 self.outer = outer
                    
    #             class LevelCardsView(nextcord.ui.View):
    #                 def __init__(self, outer, interaction: Interaction):
    #                     super().__init__(timeout = None)
    #                     self.outer = outer
                        
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     if server.allow_level_cards_bool: buttonLabel = "Disable"
    #                     else: buttonLabel = "Enable"
                        
    #                     del server #we don't need it anymore
                        
                        
    #                     self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
    #                     self.backBtn.callback = self.backBtnCallback
    #                     self.add_item(self.backBtn)
                        
                        
    #                     self.mainBtn = nextcord.ui.Button(label = buttonLabel, style = nextcord.ButtonStyle.green)
    #                     self.mainBtn.callback = self.mainBtnCallback
    #                     self.add_item(self.mainBtn)
                        
    #                 async def setup(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     if server.allow_level_cards_bool: levelCards = "on"
    #                     else: levelCards = "off"
                
    #                     embed = nextcord.Embed(title = "Dashboard - Leveling - Level-Up Cards", description = f"Currently, level-up cards are turned {levelCards}.\n\n**What are level-up cards?**\nWhen enabled, members can craft personalized level-up cards displayed after each level-up message.", color = nextcord.Color.blue())
    #                     await interaction.response.edit_message(embed = embed, view = self)
                        
    #                 async def backBtnCallback(self, interaction: Interaction):
    #                     await self.outer.setup(interaction)
                    
    #                 async def mainBtnCallback(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     server.allow_level_cards_bool = not server.allow_level_cards_bool
                        
    #                     server.saveData()
                        
    #                     await self.outer.setup(interaction)
                    
    #             async def callback(self, interaction: Interaction):
    #                 await self.LevelCardsView(self.outer, interaction).setup(interaction)
                 
    #         class EnableDisableButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Disable Leveling", row = 3)
    #                 self.outer = outer
                    
    #             class EnableDisableView(nextcord.ui.View):
    #                 def __init__(self, outer):
    #                     super().__init__(timeout = None)
    #                     self.outer = outer
                        
    #                     self.backBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
    #                     self.backBtn.callback = self.backBtnCallback
    #                     self.add_item(self.backBtn)
                        
    #                     self.actionBtn = nextcord.ui.Button(label = "ACTION", style = nextcord.ButtonStyle.green)
    #                     self.actionBtn.callback = self.actionBtnCallback
    #                     self.add_item(self.actionBtn)
                        
                        
    #                 async def setup(self, interaction: Interaction, server = None):
    #                     if not server: server = Server_DEP(interaction.guild.id)
                        
    #                     # Determine whether or not we are active or not.
    #                     if server.leveling_enabled:
    #                         # We *are* active. Give info for deactivation
    #                         embed = nextcord.Embed(title = "Dashboard - Leveling - Disable", 
    #                                                 description = "Are you sure you want to disable leveling? You can re-enable this feature at any time.",
    #                                                 color = nextcord.Color.blue())
    #                         self.actionBtn.label = "Disable"
                            
    #                     else:
    #                         # We are *not* active. Give info for activation
    #                         embed = nextcord.Embed(title = "Dashboard - Leveling",
    #                                                 description = "Leveling is currently disabled. Do you want to enable it?",
    #                                                 color = nextcord.Color.blue())
    #                         self.actionBtn.label = "Enable"
                            
    #                     await interaction.response.edit_message(embed = embed, view = self)
                        
    #                 async def backBtnCallback(self, interaction: Interaction, server = None):
    #                     if not server: server = Server_DEP(interaction.guild.id)
                        
    #                     # Return either to leveling or dashboard
    #                     if server.leveling_enabled:
    #                         # Enabled. Put us in here.
    #                         await self.outer.setup(interaction)
                            
    #                     else:
    #                         # Disabled. Put us in the level above (dashboard)
    #                         await self.outer.outer.setup(interaction)
                        
    #                 async def actionBtnCallback(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     server.leveling_enabled = (not server.leveling_enabled)
                        
    #                     server.saveData()
                        
    #                     # Return them.
    #                     await self.backBtnCallback(interaction, server = server)
                    
    #             async def callback(self, interaction: Interaction):
    #                 await self.EnableDisableView(self.outer).setup(interaction)
                               
    #     async def callback(self, interaction: Interaction):
    #         await self.LevelingView(self.outer).setup(interaction)

    # class JoinLeaveMessagesButton(nextcord.ui.Button):
    #     def __init__(self, outer):
    #         super().__init__(label = "Join / Leave Messages", style = nextcord.ButtonStyle.gray)
    #         self.outer = outer
            
    #     class JoinLeaveMessagesView(nextcord.ui.View):
    #         def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
    #             super().__init__(timeout = None)
    #             self.outer = outer
    #             self.onboarding_modifier = onboarding_modifier
    #             self.onboarding_embed = onboarding_embed
                
    #             self.joinMessageBtn = self.JoinMessageButton(self)
    #             self.add_item(self.joinMessageBtn)
                
    #             self.joinChannelBtn = self.JoinChannelButton(self)
    #             self.add_item(self.joinChannelBtn)
                
    #             self.leaveMessageBtn = self.LeaveMessageButton(self)
    #             self.add_item(self.leaveMessageBtn)
                
    #             self.leaveChannelBtn = self.LeaveChannelButton(self)
    #             self.add_item(self.leaveChannelBtn)
                
    #             self.joinCardsBtn = self.JoinCardsButton(self)
    #             self.add_item(self.joinCardsBtn)
                
    #             self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 3)
    #             self.backBtn.callback = self.backBtnCallback
    #             self.add_item(self.backBtn)
                
    #         async def setup(self, interaction: Interaction):
    #             if self.onboarding_modifier: self.onboarding_modifier(self)
                
    #             # Clean up
    #             if not self.onboarding_modifier:
    #                 for child in self.children: 
    #                     del child 
    #                     self.__init__(self.outer)

    #             server = Server_DEP(interaction.guild.id)
                
    #             # Global Kill
    #             if not utils.enabled.JoinLeaveMessages(server = server):
    #                 await ui_components.disabled_feature_override(self, interaction)
    #                 return
                
    #             if server.join_message != None and server.join_channel != False: join_message = f"```{server.join_message}```"
    #             else: join_message = "N/A"
                
    #             if server.leave_message != None and server.leave_channel != False: leave_message = f"```{server.leave_message}```"
    #             else: leave_message = "N/A"
                
    #             if server.allow_join_cards_bool: join_cards_enabled = "Yes"
    #             else: join_cards_enabled = "No"
                
    #             if server.join_channel == None: join_channel = "System Messages Channel"
    #             elif server.join_channel == False: join_channel = "DISABLED"
    #             else: join_channel = server.join_channel.mention
                
    #             if server.leave_channel == None: leave_channel = "System Messages Channel"
    #             elif server.leave_channel == False: leave_channel = "DISABLED"
    #             else: leave_channel = server.leave_channel.mention
                
    #             embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages", description = f"Set up custom messages for member joins and leaves.\n\n**Settings:**\nJoin Messages Channel: {join_channel}\nLeave Messages Channel: {leave_channel}\n\nJoin Cards Enabled: {join_cards_enabled}\n\nJoin Message: {join_message}\nLeave Message: {leave_message}\n\nFor more information, use: {levelingHelp.get_mention()}", color = nextcord.Color.blue())
                
    #             if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
    #             else: embeds = [embed]
                
    #             # Update Buttons
    #             self.joinMessageBtn.disabled = (server.join_channel == False)
    #             self.leaveMessageBtn.disabled = (server.leave_channel == False)
                
    #             await interaction.response.edit_message(embeds = embeds, view = self)
             
    #         async def backBtnCallback(self, interaction: Interaction):
    #             await self.outer.setup(interaction)
              
    #         class JoinMessageButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Join Message", style = nextcord.ButtonStyle.gray)
    #                 self.outer = outer
                    
    #             class JoinMessageModal(nextcord.ui.Modal): #Join Message Modal -----------------------------------------------------
    #                 def __init__(self, guild: nextcord.Guild, outer):
    #                     super().__init__(timeout = None, title = "Join Message")
    #                     self.outer = outer
                        
    #                     server = Server_DEP(guild.id)
    #                     if server.join_message != None: joinMessage = server.join_message
    #                     else: joinMessage = ""
    #                     self.joinMessageTextInput = nextcord.ui.TextInput(label = "Message ([member] = member)", style = nextcord.TextInputStyle.paragraph, max_length=1024, default_value = joinMessage, placeholder = "Hello There, [member]!")
    #                     self.add_item(self.joinMessageTextInput)
                        
    #                 async def callback(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
    #                     server.join_message = self.joinMessageTextInput.value  
    #                     server.saveData()
                        
    #                     await self.outer.setup(interaction)                     
                        
    #             async def callback(self, interaction: Interaction):
    #                 await interaction.response.send_modal(self.JoinMessageModal(interaction.guild, self.outer))                
                                
    #         class JoinChannelButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Join Message Channel", style = nextcord.ButtonStyle.gray)
    #                 self.outer = outer
                                     
    #             async def callback(self, interaction: Interaction):
    #                 server = Server_DEP(interaction.guild.id)
                        
    #                 selectOptions = [nextcord.SelectOption(label = "No Join Messages", value = "__DISABLED__", description = "Don't show welcome messages", default = (server.join_channel == False)),
    #                     nextcord.SelectOption(label = "System Messages Channel", value = "__NONE__", description = "Display in system messages channel", default = (server.join_channel == None))]
    #                 for channel in interaction.guild.text_channels:
    #                     if channel.category != None: categoryName = channel.category.name
    #                     else: categoryName = None
    #                     selectOptions.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.join_channel != None and server.join_channel != False and server.join_channel.id == channel.id)))
                    
    #                 embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Join Messages Channel", description = "Select a channel to send join messages", color = nextcord.Color.blue())
    #                 await ui_components.SelectView(embed, selectOptions, self.ui_components.SelectViewReturn, continueButtonLabel = "Confirm").setup(interaction)
                      
    #             async def ui_components.SelectViewReturn(self, interaction: Interaction, selection):
    #                 if selection == None:
    #                     await self.outer.setup(interaction)
    #                     return
                    
    #                 if selection == "__NONE__": value = None
    #                 elif selection == "__DISABLED__": value = False
    #                 else: value = selection
                    
    #                 server = Server_DEP(interaction.guild.id)
    #                 if server.setJoinChannelID(value):
    #                     server.saveData()
    #                     await self.outer.setup(interaction)
                                      
    #         class LeaveMessageButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Leave Message", style = nextcord.ButtonStyle.gray, row = 1)
    #                 self.outer = outer
                    
    #             class leaveMessageModal(nextcord.ui.Modal): #Leave Message Modal -----------------------------------------------------
    #                 def __init__(self, guild: nextcord.Guild, outer):
    #                     super().__init__(timeout = None, title = "Leave Message")
    #                     self.outer = outer
                        
    #                     server = Server_DEP(guild.id)
    #                     if server.leave_message != None: leaveMessage = server.leave_message
    #                     else: leaveMessage = ""
    #                     self.leaveMessageTextInput = nextcord.ui.TextInput(label = "Message ([member] = member)", style = nextcord.TextInputStyle.paragraph, max_length=1024, default_value = leaveMessage, placeholder = "[member] left. They will be remembered.")
    #                     self.add_item(self.leaveMessageTextInput)
                        
    #                 async def callback(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)        
    #                     server.leave_message = self.leaveMessageTextInput.value
    #                     server.saveData()
                        
    #                     await self.outer.setup(interaction)                       
                        
    #             async def callback(self, interaction: Interaction):
    #                 await interaction.response.send_modal(self.leaveMessageModal(interaction.guild, self.outer))                
                                
    #         class LeaveChannelButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Leave Message Channel", style = nextcord.ButtonStyle.gray, row = 1)
    #                 self.outer = outer
                    
    #             async def callback(self, interaction: Interaction):
    #                 server = Server_DEP(interaction.guild.id)
                        
    #                 selectOptions = [nextcord.SelectOption(label = "No Leave Messages", value = "__DISABLED__", description = "Don't show welcome messages", default = (server.leave_channel == False)),
    #                     nextcord.SelectOption(label = "System Messages Channel", value = "__NONE__", description = "Display in system messages channel", default = (server.leave_channel == None))]
    #                 for channel in interaction.guild.text_channels:
    #                     if channel.category != None: categoryName = channel.category.name
    #                     else: categoryName = None
    #                     selectOptions.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.leave_channel != None and server.leave_channel != False and server.leave_channel.id == channel.id)))
                    
    #                 embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Leave Messages Channel", description = "Select a channel to send leave messages", color = nextcord.Color.blue())
    #                 await ui_components.SelectView(embed, selectOptions, self.ui_components.SelectViewReturn, continueButtonLabel = "Confirm").setup(interaction)
                      
    #             async def ui_components.SelectViewReturn(self, interaction: Interaction, selection):
    #                 if selection == None:
    #                     await self.outer.setup(interaction)
    #                     return
                    
    #                 if selection == "__NONE__": value = None
    #                 elif selection == "__DISABLED__": value = False
    #                 else: value = selection
                    
    #                 server = Server_DEP(interaction.guild.id)
    #                 if server.setLeaveChannelID(value):
    #                     server.saveData()
    #                     await self.outer.setup(interaction)
                                    
    #         class JoinCardsButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Join Cards", style = nextcord.ButtonStyle.gray, row = 2)
    #                 self.outer = outer
                    
    #             class JoinCardsView(nextcord.ui.View):
    #                 def __init__(self, outer, interaction: Interaction):
    #                     super().__init__(timeout = None)
    #                     self.outer = outer
                        
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     if server.allow_join_cards_bool: buttonLabel = "Disable"
    #                     else: buttonLabel = "Enable"
                        
    #                     del server #we don't need it anymore
                        
                        
    #                     self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
    #                     self.backBtn.callback = self.backBtnCallback
    #                     self.add_item(self.backBtn)
                        
                        
    #                     self.mainBtn = nextcord.ui.Button(label = buttonLabel, style = nextcord.ButtonStyle.green)
    #                     self.mainBtn.callback = self.mainBtnCallback
    #                     self.add_item(self.mainBtn)
                        
    #                 async def setup(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     if server.allow_join_cards_bool: joinCards = "on"
    #                     else: joinCards = "off"
                
    #                     embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Join Cards", description = f"Currently, join cards are turned {joinCards}.\n\n**What are join cards?**\nIf enabled, members can personalize their own join card which will be displayed after each join message.", color = nextcord.Color.blue())
    #                     await interaction.response.edit_message(embed = embed, view = self)
                        
    #                 async def backBtnCallback(self, interaction: Interaction):
    #                     await self.outer.setup(interaction)
                    
    #                 async def mainBtnCallback(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     server.allow_join_cards_bool = not server.allow_join_cards_bool
                        
    #                     server.saveData()
                        
    #                     await self.outer.setup(interaction)
                    
    #             async def callback(self, interaction: Interaction):
    #                 await self.JoinCardsView(self.outer, interaction).setup(interaction)
                                      
    #     async def callback(self, interaction: Interaction):
    #         await self.JoinLeaveMessagesView(self.outer).setup(interaction)
    
    # class BirthdaysButton(nextcord.ui.Button):
    #     def __init__(self, outer):
    #         super().__init__(label = "Birthdays", style = nextcord.ButtonStyle.gray, row = 1)
    #         self.outer = outer 
            
    #     class BirthdaysView(nextcord.ui.View): #Birthdays Window -----------------------------------------------------
    #         def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
    #             super().__init__(timeout = None)
    #             self.outer = outer
    #             self.onboarding_modifier = onboarding_modifier
    #             self.onboarding_embed = onboarding_embed
                
    #             self.addBirthdayBtn = self.AddBirthdayButton(self)
    #             self.add_item(self.addBirthdayBtn)
                
    #             self.editBirthdayBtn = self.EditBirthdayButton(self)
    #             self.add_item(self.editBirthdayBtn)
                
    #             self.deleteBirthdayBtn = self.DeleteBirthdayButton(self)
    #             self.add_item(self.deleteBirthdayBtn)
                
    #             self.deleteAllBirthdayBtn = self.DeleteAllBirthdaysButton(self)
    #             self.add_item(self.deleteAllBirthdayBtn)
                
    #             self.birthdaysChannelBtn = self.BirthdaysChannelButton(self)
    #             self.add_item(self.birthdaysChannelBtn)
                
    #             self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 2) 
    #             self.backBtn.callback = self.backBtnCallback
    #             self.add_item(self.backBtn)
                             
    #         async def setup(self, interaction: Interaction):
    #             if self.onboarding_modifier: self.onboarding_modifier(self)
                        
    #             # Clean up
    #             if not self.onboarding_modifier:
    #                 for child in self.children: 
    #                     del child 
    #                     self.__init__(self.outer)
                
    #             server = Server_DEP(interaction.guild.id)
                
    #             if not utils.enabled.Birthdays(server = server):
    #                 await ui_components.disabled_feature_override(self, interaction)
    #                 return
                
    #             birthdays = []
    #             for bday in server.birthdays:
    #                 try:
    #                     if False or bday.member == None: # Disabled due to issue with InfiniBot restarting
    #                         server.deleteBirthday(bday.memberID)
    #                         server.saveBirthdays()
    #                         continue
                        
    #                     if bday.real_name != None: birthdays.append(f"{bday.member.mention} ({str(bday.real_name)}) - {bday.date}")
    #                     else: birthdays.append(f"{bday.member.mention} - {bday.date}")
                            
    #                 except Exception as err:
    #                     print("Birthdays View Error:", err)
                        
    #             if len(birthdays) == 0: birthdays_str = "You don't have any birthdays. Create one!"
    #             else: birthdays_str = "\n".join(birthdays)
                
    #             if server.birthday_channel == None: birthday_channel = "System Messages Channel"
    #             else: birthday_channel = server.birthday_channel.mention

    #             description = f"""
    #             Celebrate birthdays with InfiniBot's personalized messages.
                
    #             **Settings**
    #             Notifications Channel: {birthday_channel}
                
    #             **Birthdays**
    #             {birthdays_str}
                
    #             For more information, use: {birthdaysHelp.get_mention()}
    #             """
    #             description = utils.standardize_str_indention(description)
                
    #             self.embed = nextcord.Embed(title = "Dashboard - Birthdays", description = description, color = nextcord.Color.blue())
                
    #             if self.onboarding_embed: embeds = [self.onboarding_embed, self.embed]
    #             else: embeds = [self.embed]
                
    #             try: await interaction.response.edit_message(embeds = embeds, view = self)
    #             except: await interaction.edit_original_message(embeds = embeds, view = self)
                
    #         async def backBtnCallback(self, interaction: Interaction):
    #             await self.outer.setup(interaction)               
              
    #         class AddBirthdayButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Add", style = nextcord.ButtonStyle.gray)
    #                 self.outer = outer
                    
    #             async def callback(self, interaction: Interaction):# Edit Strikes Callback ————————————————————————————————————————————————————————————
    #                 server = Server_DEP(interaction.guild.id)
                        
    #                 memberSelectOptions = []
    #                 for member in interaction.guild.members:
    #                     if member.bot: continue
    #                     if not server.birthdayExists(member.id): memberSelectOptions.append(nextcord.SelectOption(label = f"{member}", description = member.nick, value = member.id))
                    
                    
    #                 if memberSelectOptions == []: 
    #                     await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Members", description = "Every member in your server already has a birthday! Go invite someone!", color = nextcord.Color.red()), ephemeral = True)
    #                     return
                    
    #                 await ui_components.SelectView(self.outer.embed, memberSelectOptions, self.ui_components.SelectViewReturn, placeholder = "Choose a Member", continueButtonLabel = "Next").setup(interaction)
                    
    #             async def ui_components.SelectViewReturn(self, interaction: Interaction, selection):
    #                 if selection == None:
    #                     await self.outer.setup(interaction)
    #                     return
                    
    #                 await interaction.response.send_modal(self.InfoModal(self.outer, selection))          
                                    
    #             class InfoModal(nextcord.ui.Modal):            
    #                 def __init__(self, outer, memberID):
    #                     super().__init__(title = "Add Birthday", timeout = None)
    #                     self.outer = outer
    #                     self.memberID = memberID
                        
    #                     self.dateInput = nextcord.ui.TextInput(label = "Date (MM/DD/YYYY)", style = nextcord.TextInputStyle.short, max_length = 10, placeholder = "MM/DD/YYYY")
    #                     self.add_item(self.dateInput)
                        
    #                     self.realNameInput = nextcord.ui.TextInput(label = "Real Name (Optional)", style = nextcord.TextInputStyle.short, max_length=50, required = False)
    #                     self.add_item(self.realNameInput)
                        
    #                 async def callback(self, interaction: Interaction):
    #                     try:
    #                         datetime.datetime.strptime(self.dateInput.value, f"%m/%d/%Y")
    #                     except:
    #                         await interaction.response.send_message(embed = nextcord.Embed(title = "Invalid Format", description = "You formatted the date wrong. Try formating it like this: MM/DD/YYYY", color =  nextcord.Color.red()), ephemeral=True)
    #                         return
                        
    #                     server = Server_DEP(interaction.guild.id)
    #                     if self.realNameInput.value == "": server.addBirthday(self.memberID, self.dateInput.value)
    #                     else: server.addBirthday(self.memberID, self.dateInput.value, real_name = self.realNameInput.value)
    #                     server.saveBirthdays()
                        
                        
    #                     await self.outer.setup(interaction)
          
    #         class EditBirthdayButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Edit", style = nextcord.ButtonStyle.gray)
    #                 self.outer = outer
                                                      
    #             async def callback(self, interaction: Interaction):# Edit Strikes Callback ————————————————————————————————————————————————————————————
    #                 server = Server_DEP(interaction.guild.id)
                        
    #                 memberSelectOptions = []
    #                 for member in interaction.guild.members:
    #                     if server.birthdayExists(member.id): memberSelectOptions.append(nextcord.SelectOption(label = f"{member}", description = member.nick, value = member.id))
                    
                    
    #                 if memberSelectOptions == []: 
    #                     await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Members", description = "No members in your server have birthdays. Add some!", color = nextcord.Color.red()), ephemeral = True)
    #                     return
                    
    #                 await ui_components.SelectView(self.outer.embed, memberSelectOptions, self.ui_components.SelectViewReturn, placeholder = "Choose a Member", continueButtonLabel = "Next").setup(interaction)
                    
    #             async def ui_components.SelectViewReturn(self, interaction: Interaction, selection):
    #                 if selection == None:
    #                     await self.outer.setup(interaction)
    #                     return
                    
    #                 await interaction.response.send_modal(self.InfoModal(self.outer, selection, interaction.guild.id))          
                                    
    #             class InfoModal(nextcord.ui.Modal):            
    #                 def __init__(self, outer, memberID, guildID):
    #                     super().__init__(title = "Add Birthday", timeout = None)
    #                     self.outer = outer
    #                     self.memberID = memberID
                        
    #                     server = Server_DEP(guildID)
    #                     birthday = server.getBirthday(self.memberID)
                        
    #                     self.dateInput = nextcord.ui.TextInput(label = "Date (MM/DD/YYYY)", style = nextcord.TextInputStyle.short, max_length = 10, placeholder = "MM/DD/YYYY", default_value = birthday.date)
    #                     self.add_item(self.dateInput)
                        
    #                     self.realNameInput = nextcord.ui.TextInput(label = "Real Name (Optional)", style = nextcord.TextInputStyle.short, max_length=50, required = False, default_value = birthday.real_name)
    #                     self.add_item(self.realNameInput)
                        
    #                 async def callback(self, interaction: Interaction):
    #                     try:
    #                         datetime.datetime.strptime(self.dateInput.value, f"%m/%d/%Y")
    #                     except:
    #                         await interaction.response.send_message(embed = nextcord.Embed(title = "Invalid Format", description = "You formatted the date wrong. Try formating it like this: MM/DD/YYYY", color =  nextcord.Color.red()), ephemeral=True)
    #                         return
                        
    #                     server = Server_DEP(interaction.guild.id)
    #                     birthday = server.getBirthday(self.memberID)
    #                     birthday.date = self.dateInput.value
                        
    #                     if self.realNameInput.value != "": birthday.real_name = self.realNameInput.value
    #                     server.saveBirthdays()
                        
                        
    #                     await self.outer.setup(interaction)

    #         class DeleteBirthdayButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Delete", style = nextcord.ButtonStyle.gray)
    #                 self.outer = outer
                                      
    #             async def callback(self, interaction: Interaction):# Edit Strikes Callback ————————————————————————————————————————————————————————————
    #                 server = Server_DEP(interaction.guild.id)
                        
    #                 memberSelectOptions = []
    #                 for member in interaction.guild.members:
    #                     if server.birthdayExists(member.id): memberSelectOptions.append(nextcord.SelectOption(label = f"{member}", description = member.nick, value = member.id))
                    
                    
    #                 if memberSelectOptions == []: 
    #                     await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Members", description = "No members in your server have birthdays. Add some!", color = nextcord.Color.red()), ephemeral = True)
    #                     return
                    
    #                 await ui_components.SelectView(self.outer.embed, memberSelectOptions, self.ui_components.SelectViewReturn, placeholder = "Choose a Member", continueButtonLabel = "Delete").setup(interaction)
                    
    #             async def ui_components.SelectViewReturn(self, interaction: Interaction, selection):
    #                 if selection == None:
    #                     await self.outer.setup(interaction)
    #                     return
                    
    #                 server = Server_DEP(interaction.guild.id)
    #                 server.deleteBirthday(selection)
    #                 server.saveBirthdays()
                    
    #                 await self.outer.setup(interaction)      
                                    
    #         class DeleteAllBirthdaysButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Delete All", style = nextcord.ButtonStyle.gray)
    #                 self.outer = outer
                    
    #             class DeleteAllStrikesView(nextcord.ui.View):
    #                 def __init__(self, outer):
    #                     super().__init__(timeout = None)
    #                     self.outer = outer
                        
    #                     self.noBtn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
    #                     self.noBtn.callback = self.noBtnCommand
    #                     self.add_item(self.noBtn)
                        
    #                     self.yesBtn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
    #                     self.yesBtn.callback = self.yesBtnCommand
    #                     self.add_item(self.yesBtn)
                        
    #                 async def setup(self, interaction: Interaction):
    #                     embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will delete all birthdays in the server.\nThis action cannot be undone.", color = nextcord.Color.blue())
    #                     await interaction.response.edit_message(embed = embed, view = self)
                        
    #                 async def noBtnCommand(self, interaction: Interaction):
    #                     await self.outer.setup(interaction)
                        
    #                 async def yesBtnCommand(self, interaction: Interaction):
    #                     server = Server_DEP(interaction.guild.id)
    #                     server.birthdays = []
    #                     server.saveBirthdays()
    #                     await self.outer.setup(interaction)
                    
    #             async def callback(self, interaction: Interaction):
    #                 await self.DeleteAllStrikesView(self.outer).setup(interaction)           
     
    #         class BirthdaysChannelButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Notification Channel", style = nextcord.ButtonStyle.gray, row = 1)
    #                 self.outer = outer
                                     
    #             async def callback(self, interaction: Interaction):
    #                 server = Server_DEP(interaction.guild.id)
                        
    #                 selectOptions = [nextcord.SelectOption(label = "System Messages Channel", value = "__NONE__", description = "Display in system messages channel", default = (server.birthday_channel == None))]
    #                 for channel in interaction.guild.text_channels:
    #                     if channel.category != None: categoryName = channel.category.name
    #                     else: categoryName = None
    #                     selectOptions.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.birthday_channel != None and server.birthday_channel.id == channel.id)))
                    
    #                 embed = nextcord.Embed(title = "Dashboard - Birthdays - Notification Channel", description = "Select a channel to send birthday messages.", color = nextcord.Color.blue())
    #                 await ui_components.SelectView(embed, selectOptions, self.ui_components.SelectViewReturn, continueButtonLabel = "Confirm").setup(interaction)
                      
    #             async def ui_components.SelectViewReturn(self, interaction: Interaction, selection):
    #                 if selection == None:
    #                     await self.outer.setup(interaction)
    #                     return
                    
    #                 if selection == "__NONE__": value = None
    #                 else: value = selection
                    
    #                 server = Server_DEP(interaction.guild.id)
    #                 if server.setBirthdayChannelID(value):
    #                     server.saveData()
    #                     await self.outer.setup(interaction)
           
    #     async def callback(self, interaction: Interaction):
    #         view = self.BirthdaysView(self.outer)
    #         await view.setup(interaction)
    
    # class DefaultRolesButton(nextcord.ui.Button):
    #     def __init__(self, outer):
    #         super().__init__(label = "Default Roles", style = nextcord.ButtonStyle.gray, row = 1)
    #         self.outer = outer
    
    #     class DefaultRolesView(nextcord.ui.View):
    #         def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
    #             super().__init__(timeout=None)
    #             self.outer = outer
    #             self.onboarding_modifier = onboarding_modifier
    #             self.onboarding_embed = onboarding_embed
                
    #             self.cancelBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
    #             self.cancelBtn.callback = self.cancelBtnCallback

    #             self.updateBtn = self.UpdateButton(self.outer, self)
                
    #         async def setup(self, interaction: Interaction):                   
    #             # Clean up
    #             if not self.onboarding_modifier:
    #                 for child in self.children: 
    #                     del child 
    #                     self.__init__(self.outer)
                
    #             embed = nextcord.Embed(title = "Dashboard - Default Roles", description = "Select the roles you would that InfiniBot will assign to any new members upon join.", color = nextcord.Color.blue())
                
    #             server = Server_DEP(interaction.guild.id)
                
    #             if not utils.enabled.DefaultRoles(server = server):
    #                 self.add_item(self.cancelBtn)
    #                 await ui_components.disabled_feature_override(self, interaction)
    #                 return
                
    #             selectOptions = []
    #             for role in interaction.guild.roles:
    #                 if role.name == "@everyone": continue
    #                 if not canAssignRole(role): continue
    #                 if len(selectOptions) >= 25:
    #                     embed.description += "\n\nNote: Only the first 25 roles of your server can be set as default roles."
    #                     break
                        
    #                 selectOptions.append(nextcord.SelectOption(label = role.name, description = role.id, value = role.id, default = (role in server.default_roles)))
                
    #             if len(selectOptions) <= 5: maxOptions = len(selectOptions)
    #             else: maxOptions = 5
                
    #             if self.onboarding_embed: embeds = [self.onboarding_embed, embed]
    #             else: embeds = [embed]
                
    #             if selectOptions != []:
    #                 self.roleSelect = nextcord.ui.Select(options = selectOptions, placeholder = "Choose", max_values = maxOptions, min_values = 0)
    #                 self.add_item(self.roleSelect)
    #                 self.add_item(self.cancelBtn)
    #                 self.add_item(self.updateBtn)
                    
    #                 if self.onboarding_modifier: 
    #                     self.onboarding_modifier(self)
    #                     self.updateBtn.style = nextcord.ButtonStyle.gray
    #                     self.updateBtn.label = "Save"
    #                     self.updateBtn.go_back_to_dashboard = False
                    
    #                 await interaction.response.edit_message(embeds = embeds, view = self)
                    
    #             else:
    #                 await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", description = "You've run out of roles to use! To fix this, either promote InfiniBot to the highest role, give InfiniBot Administrator, or add more roles to the server!", color = nextcord.Color.red()), ephemeral=True)             
                                            
    #         async def cancelBtnCallback(self, interaction: Interaction):
    #             await self.outer.setup(interaction)
                
    #         class UpdateButton(nextcord.ui.Button):
    #             def __init__(self, outer, parent):
    #                 super().__init__(label = "Update", style = nextcord.ButtonStyle.blurple)
    #                 self.outer = outer     
    #                 self.parent = parent
    #                 self.go_back_to_dashboard = True                 
                        
    #             async def callback(self, interaction: Interaction):
    #                 server = Server_DEP(interaction.guild.id)
                    
    #                 defaultRoles = []
    #                 for roleID in self.parent.roleSelect.values:
    #                     try: defaultRoles.append(interaction.guild.get_role(int(roleID)))
    #                     except: return
                    
                    
    #                 server.default_roles = defaultRoles
    #                 server.saveData()
                    
    #                 if self.go_back_to_dashboard: await self.outer.setup(interaction)
            
    #     async def callback(self, interaction: Interaction):
    #         await self.DefaultRolesView(self.outer).setup(interaction)    
    
    # class JoinToCreateVCsButton(nextcord.ui.Button):
    #     def __init__(self, outer):
    #         super().__init__(label = "Join-To-Create VCs", style = nextcord.ButtonStyle.gray, row = 1)
    #         self.outer = outer
                    
    #     class JoinToCreateVCsView(nextcord.ui.View):
    #         def __init__(self, outer, onboarding_modifier = None, onboarding_embed = None):
    #             super().__init__(timeout=None)
    #             self.outer = outer
    #             self.onboarding_modifier = onboarding_modifier
    #             self.onboarding_embed = onboarding_embed
                
    #             #create buttons
    #             self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
    #             self.backBtn.callback = self.backBtnCallback
    #             self.add_item(self.backBtn)
                
    #             self.configureBtn = self.ConfigureButton(self)
    #             self.add_item(self.configureBtn)
                
    #         def getMessageEmbed(self, guild: nextcord.Guild):
    #             server = Server_DEP(guild.id)
    #             vcs = server.VCs
    #             del server
                    
    #             if len(vcs) > 0:
    #                 description = "**Join-To-Create VCs**\n" + "\n".join([f"• {item.channel.mention}" if item.active else f"• ⚠️ {item.channel.mention} ⚠️" for item in vcs])
    #             else:
    #                 description = "**Join-To-Create VCs**\nYou don't have any join-to-create VCs. Click Configure to make one!"
                    
    #             return nextcord.Embed(title = "Dashboard - Join-To-Create-VCs", description = f"You may select up to five voice channels that will have this feature.\n\n**What is it?**\nWhen a user joins one of these Voice Channels, they will be moved to a custom voice channel created just for them. When everyone leaves, the channel will be removed.\n\n{description}\n\nFor more information, use: {joinToCreateVoiceChannelsHelp.get_mention()}", color = nextcord.Color.blue())
        
    #         async def setup(self, interaction: Interaction):
    #             if self.onboarding_modifier: self.onboarding_modifier(self)
                
    #             if not utils.enabled.JoinToCreateVCs(guild_id = interaction.guild.id):
    #                 await ui_components.disabled_feature_override(self, interaction)
    #                 return
                
    #             if self.onboarding_embed: embeds = [self.onboarding_embed, self.getMessageEmbed(interaction.guild)]
    #             else: embeds = [self.getMessageEmbed(interaction.guild)]
                
    #             await interaction.response.edit_message(embeds = embeds, view = self)
                    
    #         async def backBtnCallback(self, interaction: Interaction):
    #             await self.outer.setup(interaction)
            
    #         class ConfigureButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Configure", style = nextcord.ButtonStyle.blurple)
    #                 self.outer = outer
                    
    #             class ConfigureView(nextcord.ui.View):
    #                 def __init__(self, outer, guild: nextcord.Guild):
    #                     super().__init__(timeout=None)
    #                     self.outer = outer
                        
    #                     self.embed: nextcord.Embed = self.outer.getMessageEmbed(guild)
    #                     dontSeeYourChannelMessage = """\n\n**Having Issues?**
    #                     Make sure InfiniBot has the following permissions in your channel:
    #                     • View Channel
    #                     • Manage Channel
    #                     • Connect
    #                     • Move Members"""
    #                     dontSeeYourChannelMessage = utils.standardize_str_indention(dontSeeYourChannelMessage)
    #                     self.embed.description += dontSeeYourChannelMessage
                        
    #                     #get the vcs
    #                     accessableVCs = [vc for vc in guild.voice_channels if (vc.permissions_for(guild.me).view_channel and vc.permissions_for(guild.me).connect and vc.permissions_for(guild.me).manage_channels)]
                    
    #                     server = Server_DEP(guild.id)
    #                     vcs = [[vc, server.VCExists(vc.id)] for vc in accessableVCs]
                        
    #                     #Error message
    #                     if False in [vc.active for vc in server.VCs]:
    #                         self.embed.description += "\n\n**⚠️ There is a Problem with One or More of Your VCs ⚠️**\nMake sure that all join-to-create VCs have the following permissions:\n• View Channel\n• Manage Channel\n• Connect"
                        
    #                     del server

    #                     #create other buttons
    #                     self.addBtn = self.AddButton(self, guild, vcs)
    #                     self.add_item(self.addBtn)
                        
    #                     self.deleteBtn = self.DeleteButton(self, guild)
    #                     self.add_item(self.deleteBtn)
                        
    #                     self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
    #                     self.backBtn.callback = self.backBtnCallback
    #                     self.add_item(self.backBtn)
                        
    #                 async def setup(self, interaction: Interaction):
    #                     await interaction.response.edit_message(embed = self.embed, view = self)
                       
    #                 async def refresh(self, interaction: Interaction):
    #                     self.__init__(self.outer, interaction.guild)
    #                     await self.setup(interaction)
                        
    #                 async def backBtnCallback(self, interaction: Interaction):
    #                     await self.outer.setup(interaction)
                        
    #                 class AddButton(nextcord.ui.Button):
    #                     def __init__(self, outer, guild: nextcord.Guild, vcs:list[nextcord.VoiceChannel, bool]):
    #                         self.outer = outer
    #                         self.vcs = vcs
                            
    #                         server = Server_DEP(guild.id)
                            
    #                         #choose enabled / disabled
    #                         if len(self.vcs) > 0 and len(server.VCs) < 5 and len([vc for vc in self.vcs if not vc[1]]) > 0: disabled = False
    #                         else: disabled = True
                            
    #                         #choose button style
    #                         server = Server_DEP(guild.id)
    #                         if len(server.VCs) == 0 and not disabled: style = nextcord.ButtonStyle.blurple
    #                         else: style = nextcord.ButtonStyle.gray
           
    #                         super().__init__(label = "Add Channel", style = style, disabled = disabled)
                                                     
    #                     async def callback(self, interaction: Interaction):
    #                         selectOptions = [nextcord.SelectOption(label = vc[0].name, value = vc[0].id, description = (vc[0].category.name if vc[0].category else "")) for vc in [vc for vc in self.vcs if not vc[1]]]
                            
    #                         description = """Select a Voice Channel to be a Join-To-Create Voice Channel.
                                
    #                         **Don't See Your Channel?**
    #                         Make sure InfiniBot has the following permissions in your channel:
    #                         • View Channel
    #                         • Manage Channel
    #                         • Connect"""
                        
    #                         # On Mobile, extra spaces cause problems. We'll get rid of them here:
    #                         description = utils.standardize_str_indention(description)
                            
    #                         embed = nextcord.Embed(title = "Dashboard - Join-To-Create-VCs - Add Channel", description = description, color = nextcord.Color.blue())
    #                         view = ui_components.SelectView(embed,
    #                                           options = selectOptions, 
    #                                           returnCommand = self.selectCallback, 
    #                                           continueButtonLabel = "Add", 
    #                                           preserveOrder = True, 
    #                                           placeholder = "Select a Voice Channel")
                            
    #                         await view.setup(interaction)
                            
    #                     async def selectCallback(self, interaction: Interaction, selection: str):
    #                         if selection == None: 
    #                             await self.outer.refresh(interaction) 
    #                             return
                            
    #                         server = Server_DEP(interaction.guild.id)
    #                         server.VCs.append(JoinToCreateVC(interaction.guild, None, id = selection))
    #                         server.saveVCs()
                            
    #                         await self.outer.refresh(interaction)
                            
    #                 class DeleteButton(nextcord.ui.Button):
    #                     def __init__(self, outer, guild: nextcord.Guild):
    #                         self.outer = outer
                            
    #                         server = Server_DEP(guild.id)
                            
    #                         #choose enabled / disabled
    #                         if len(server.VCs) > 0: disabled = False
    #                         else: disabled = True
           
    #                         super().__init__(label = "Delete Channel", style = nextcord.ButtonStyle.gray, disabled = disabled)
                                                        
    #                     async def callback(self, interaction: Interaction):
    #                         server = Server_DEP(interaction.guild.id)
    #                         selectOptions = [nextcord.SelectOption(label = vc.channel.name, value = vc.id, description = (vc.channel.category.name if vc.channel.category else "")) for vc in server.VCs]
                                        
    #                         description = """Select a Join-To-Create Voice Channel to no longer be a Join-To-Create Voice Channel."""
                        
    #                         # On Mobile, extra spaces cause problems. We'll get rid of them here:
    #                         description = utils.standardize_str_indention(description)
                            
    #                         embed = nextcord.Embed(title = "Dashboard - Join-To-Create-VCs - Delete Channel", description = description, color = nextcord.Color.blue())
    #                         view = ui_components.SelectView(embed,
    #                                           options = selectOptions, 
    #                                           returnCommand = self.selectCallback, 
    #                                           continueButtonLabel = "Delete", 
    #                                           preserveOrder = True, 
    #                                           placeholder = "Select a Voice Channel")
                            
    #                         await view.setup(interaction)
                            
    #                     async def selectCallback(self, interaction: Interaction, selection: str):
    #                         if selection == None: 
    #                             await self.outer.refresh(interaction)
    #                             return
                            
    #                         selection = int(selection)
                            
    #                         server = Server_DEP(interaction.guild.id)
                            
    #                         for vc in list(server.VCs):
    #                             if vc.id == selection:
    #                                 server.VCs.remove(vc)
    #                                 #we're not going to break to ensure that we delete every instance of this in case something glitched
                            
    #                         server.saveVCs()
                            
    #                         await self.outer.refresh(interaction)
                                        
    #             async def callback(self, interaction: Interaction):
    #                 await self.ConfigureView(self.outer, interaction.guild).setup(interaction)                      
        
    #     async def callback(self, interaction: Interaction):
    #         await self.JoinToCreateVCsView(self.outer).setup(interaction)

    # class AutoBansButton(nextcord.ui.Button):
    #     def __init__(self, outer):
    #         super().__init__(label = "Auto-Bans", style = nextcord.ButtonStyle.gray, row = 1)
    #         self.outer = outer
            
    #     class AutoBansView(nextcord.ui.View):
    #         def __init__(self, outer):
    #             super().__init__(timeout=None)
    #             self.outer = outer
                
    #             #create buttons
    #             self.addBtn = self.AddButton(self)
    #             self.add_item(self.addBtn)
                
    #             self.revokeBtn = self.RevokeButton(self)
    #             self.add_item(self.revokeBtn)
                                    
    #             self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
    #             self.backBtn.callback = self.backBtnCallback
    #             self.add_item(self.backBtn)
                                                            
    #         async def setup(self, interaction: Interaction):
    #             if interaction.guild.me.guild_permissions.ban_members:
    #                 server = Server_DEP(interaction.guild.id)
                    
    #                 if not utils.enabled.AutoBans(server = server):
    #                     await ui_components.disabled_feature_override(self, interaction)
    #                     return
                    
    #                 autoBans = []
    #                 for autoBan in server.auto_bans:
    #                     autoBans.append(f"• {autoBan.member_name}  (ID: {autoBan.member_id})")
                        
    #                 if len(autoBans) > 0:
    #                     autoBansStr = "\n".join(autoBans)
    #                     autoBansStr = f"```{autoBansStr}```"
    #                     self.revokeBtn.disabled = False
    #                 else:
    #                     autoBansStr = "You don't have any auto-bans yet."
    #                     self.revokeBtn.disabled = True
                                        
    #                 description = f"""InfiniBot has the capability to ban members both in your server and after they leave.
    #                 ✯ You can even ban people who haven't even joined the server yet.
                    
    #                 **How?**
    #                 Just right click on a message or member, select \"Apps\" and click \"Ban Message Author\" or \"Ban Member\"                           
                    
    #                 **Ban Someone Before They Join the Server**
    #                 Click the "Add" button below, and follow the instructions. You will need the user's Discord ID.               
                    
    #                 **Revoking Auto-Bans**
    #                 Click the \"Revoke\" button to begin revoking auto-bans.
                    
                    
    #                 **Current Auto-Bans**
    #                 {autoBansStr}
                    
    #                 For more information, use: {autoBansHelp.get_mention()}"""
                    
    #                 # On Mobile, extra spaces cause problems. We'll get rid of them here:
    #                 description = utils.standardize_str_indention(description)
                            

    #             else:
    #                 description = f"InfiniBot doesn't have the \"Ban Members\" permission. This feature requires this permission. Please give InfiniBot this permission, and then reload this page."
    #                 self.addBtn.disabled = True
    #                 self.revokeBtn.disabled = True
    #                 #disable all buttons
                
    #             embed = nextcord.Embed(title = "Dashboard - Auto-Bans", description = description, color = nextcord.Color.blue())
    #             await interaction.response.edit_message(embed = embed, view = self)
            
    #         async def backBtnCallback(self, interaction: Interaction):
    #             await self.outer.setup(interaction)
            
    #         class AddButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Add", style = nextcord.ButtonStyle.gray)
    #                 self.outer = outer
                                                
    #             class IDHelp(nextcord.ui.View):
    #                 def __init__(self, outer):
    #                     super().__init__(timeout = None)
    #                     self.outer = outer
                        
    #                     self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
    #                     self.backBtn.callback = self.backBtnCallback
    #                     self.add_item(self.backBtn)
                        
    #                     self.continueBtn = nextcord.ui.Button(label = "I've Copied the ID, Continue", style = nextcord.ButtonStyle.green)
    #                     self.continueBtn.callback = self.continueBtnCallback
    #                     self.add_item(self.continueBtn)
                        
    #                 async def setup(self, interaction: Interaction):
    #                     description = """In order to ban a member before they have joined, you need their Discord ID. To get this, follow these steps:
                    
    #                     **On Desktop**
    #                     • Go to Discord's Settings
    #                     • Scroll Down to "Advanced"
    #                     • Enable "Developer Mode"
    #                     • Exit Settings and Right click on the member whom you would like to auto-ban
    #                     • Click "Copy ID" (at the very bottom)
    #                     • Proceed
                        
    #                     **On Mobile**
    #                     • Go to Discord's Settings (by clicking your profile icon in the bottom right)
    #                     • Scroll Down to "Appearance"
    #                     • Enable "Developer Mode"
    #                     • Exit Settings and touch and hold on the member whom you would like to auto-ban
    #                     • Click the three dots in the top right of their profile 
    #                     • Click "Copy ID"
    #                     • Proceed
    #                     """
                        
    #                     # On Mobile, extra spaces cause problems. We'll get rid of them here:
    #                     description = utils.standardize_str_indention(description)

                        
    #                     embed = nextcord.Embed(title = "Dashboard - Auto-Bans - Add", description = description, color = nextcord.Color.blue())
    #                     await interaction.response.edit_message(embed = embed, view = self)
                        
    #                 async def backBtnCallback(self, interaction: Interaction):
    #                     await self.outer.setup(interaction)
                        
    #                 class AddModal(nextcord.ui.Modal):
    #                     def __init__(self, outer):
    #                         super().__init__(title = "Add Auto-Ban", timeout = None)
    #                         self.outer = outer
    #                         self.userName = None
    #                         self.id = None
                            
    #                         self.userNameInput = nextcord.ui.TextInput(label = "Discord Name (Not Critical)", placeholder = "BillyBob#1234", max_length = 64)
    #                         self.add_item(self.userNameInput)
                            
    #                         self.idInput = nextcord.ui.TextInput(label = "Discord ID (Paste It) (Critical)", placeholder = "12345678910", max_length = 30)
    #                         self.add_item(self.idInput)
                            
    #                     async def callback(self, interaction: Interaction): #saving
    #                         self.stop()
                            
    #                         userName = self.userNameInput.value
    #                         id = self.idInput.value
                            
    #                         embed = None
                            
    #                         if not id.isdigit():
    #                             await self.outer.setup(interaction)
    #                             await interaction.followup.send(embed = nextcord.Embed(title = "User ID must be a number", description = "The User ID must be a number. Try again.", color = nextcord.Color.red()), ephemeral = True);
    #                             return;
                            

    #                         for member in interaction.guild.members:
    #                             if member.id == int(id):
    #                                 embed = nextcord.Embed(title = "User Already In Server", description = f"InfiniBot won't add \"{userName} (ID: {id})\" as an auto-ban because they are already in this server ({member.mention}). You can ban them with the /ban command.", color = nextcord.Color.red())
                            
    #                         if interaction.guild.me.guild_permissions.ban_members == True:
    #                             async for ban in interaction.guild.bans():
    #                                 if ban.user.id == int(id):
    #                                     embed = nextcord.Embed(title = "User Already Banned", description = f"InfiniBot won't add \"{userName} (ID: {id})\" as an auto-ban because they are already banned in this server.", color = nextcord.Color.red())
                            
    #                         if embed == None:
    #                             #save data
    #                             server = Server_DEP(interaction.guild.id)
                                
    #                             server.addAutoBan(userName, id, replace = True)
    #                             server.saveAutoBans()
    #                             del server
                            
    #                         await self.outer.setup(interaction)
                            
    #                         if embed != None:
    #                             await interaction.followup.send(embed = embed, ephemeral = True)
                                                        
    #                 async def continueBtnCallback(self, interaction: Interaction):
    #                     await interaction.response.send_modal(self.AddModal(self.outer))
                                                
    #             async def callback(self, interaction: Interaction):              
    #                 await self.IDHelp(self.outer).setup(interaction)
            
    #         class RevokeButton(nextcord.ui.Button):
    #             def __init__(self, outer):
    #                 super().__init__(label = "Revoke", style = nextcord.ButtonStyle.gray)
    #                 self.outer = outer
                    
    #             async def callback(self, interaction: Interaction):
    #                 server = Server_DEP(interaction.guild.id)
                    
    #                 autoBans = []
    #                 for autoBan in server.auto_bans:
    #                     label = (f"{autoBan.member_name}")
    #                     autoBans.append(nextcord.SelectOption(label = label, description = f"ID: {autoBan.member_id}", value = autoBan.member_id))
                    
    #                 embed = nextcord.Embed(title = "Dashboard - Auto-Bans - Revoke", description = "To revoke an auto-ban, select the member, and click \"Revoke Auto-Ban\". They will then be able to join this server without being auto-banned.", color = nextcord.Color.blue())
    #                 await ui_components.SelectView(embed = embed, options = autoBans, returnCommand = self.selectViewCallback, placeholder = "Select a Member", continueButtonLabel = "Revoke Auto-Ban").setup(interaction)
            
    #             async def selectViewCallback(self, interaction: Interaction, selection):
    #                 if selection != None:
    #                     server = Server_DEP(interaction.guild.id)
    #                     server.deleteAutoBan(selection)
    #                     server.saveAutoBans()
                    
    #                 await self.outer.setup(interaction)
            
    #     async def callback(self, interaction: Interaction):
    #         await self.AutoBansView(self.outer).setup(interaction)

    # class ActiveMessagesButton(nextcord.ui.Button):
    #     def __init__(self, outer):
    #         super().__init__(label = "Active Messages", row = 2)
    #         self.outer = outer
            
    #     class ActiveMessagesView(nextcord.ui.View):
    #         def __init__(self, outer):
    #             super().__init__(timeout = None)
    #             self.outer = outer
                
    #             self.embedBtn = self.OptionButton(self, "Embed")
    #             self.add_item(self.embedBtn)
                
    #             self.votesBtn = self.OptionButton(self, "Vote")
    #             self.add_item(self.votesBtn)
                
    #             self.reactionRolesBtn = self.OptionButton(self, "Reaction Role")
    #             self.add_item(self.reactionRolesBtn)
                
    #             self.roleMessagesBtn = self.OptionButton(self, "Role Message")
    #             self.add_item(self.roleMessagesBtn)
                
    #             self.backBtn = nextcord.ui.Button(label = "Back", row = 1, style = nextcord.ButtonStyle.danger)
    #             self.backBtn.callback = self.backBtnCallback
    #             self.add_item(self.backBtn)
                
    #         async def setup(self, interaction: Interaction):
    #             server = Server_DEP(interaction.guild.id)
                
    #             if not utils.enabled.ActiveMessages(server = server):
    #                 await ui_components.disabled_feature_override(self, interaction)
    #                 return
                
    #             description = f"""InfiniBot caches every vote, reaction role, and embedded message posted on this server (using InfiniBot), enabling the ability to edit these messages. However, there is a maximum limit for some messages (indicated below). Please refer to the list below to manage your active messages.
                
    #             {self.activeMessageStats(server, "Embed")}
    #             {self.activeMessageStats(server, "Vote")}
    #             {self.activeMessageStats(server, "Reaction Role")}
    #             {self.activeMessageStats(server, "Role Message")}"""
                
    #             # On Mobile, extra spaces cause problems. We'll get rid of them here:
    #             description = utils.standardize_str_indention(description)
                
    #             embed = nextcord.Embed(title = "Dashboard - Active Messages", description = description, color = nextcord.Color.blue())
    #             await interaction.response.edit_message(embed = embed, view = self)
                
    #         def activeMessageStats(self, server: Server_DEP, _type: str):
    #             all = server.messages.countOf(_type)
    #             if all == None:
    #                 return "INVALID TYPE"
                
    #             max = server.messages.maxOf(_type)
    #             if max == None:
    #                 max = ""
    #             else:
    #                 max = f"/{max}"
                
    #             return f"{_type}s ({all}{max})"
                
    #         class OptionButton(nextcord.ui.Button):
    #             def __init__(self, outer, _type):
    #                 super().__init__(label = f"Configure {_type}s")
    #                 self.outer = outer
    #                 self._type = _type
                    
    #             class TheView(nextcord.ui.View):
    #                 def __init__(self, outer, _type):
    #                     super().__init__(timeout = None)
    #                     self.outer = outer
    #                     self._type: str = _type
    #                     self._type_lower = self._type.lower()
                        
    #                     self.backBtn = nextcord.ui.Button(label = "Back")
    #                     self.backBtn.callback = self.backBtnCallback
    #                     self.add_item(self.backBtn)
                        
    #                     self.refreshBtn = nextcord.ui.Button(label = "Refresh")
    #                     self.refreshBtn.callback = self.refreshBtnCallback
    #                     self.add_item(self.refreshBtn)
                        
    #                 async def setup(self, interaction: Interaction):
    #                     embed = nextcord.Embed(title = f"Dashboard - Active Messages - {self._type}s",
    #                                            description = f"Please wait as we retrieve your active messages...",
    #                                            color = nextcord.Color.blue())
                        
    #                     main_message = await interaction.response.edit_message(embed = embed, view = self)
                        
                        
    #                     server = Server_DEP(interaction.guild.id)
                        
    #                     messages = server.messages.getAll(self._type)
                        
    #                     maxMessages = server.messages.maxOf(self._type)
                        
    #                     save = False
    #                     messagesFormatted = []
    #                     for index, message in enumerate(messages):
    #                         try:
    #                             # Get the Channel
    #                             discordChannel = await interaction.guild.fetch_channel(message.channel_id)
    #                             if not discordChannel: 
    #                                 raise(nextcord.errors.NotFound)
                                
    #                             # Get the Message
    #                             discordMessage = await discordChannel.fetch_message(message.message_id)
    #                             if not discordMessage: 
    #                                 raise(nextcord.errors.NotFound)
                                
    #                         except (nextcord.errors.NotFound, nextcord.errors.Forbidden):
    #                             server.messages.delete(message.message_id)
    #                             save = True
    #                             continue
                            
    #                         # Create the UI
    #                         title = discordMessage.embeds[0].title
    #                         persistent = " 🔒" if message.persistent else ""
                            
    #                         maxMessagesStr = (f"/{maxMessages}" if maxMessages else "")
    #                         messagesFormatted.append(f"{index + 1}{maxMessagesStr}) [{title}]({message.getLink(interaction.guild.id)}){persistent}")
                            
    #                     # Save if needed
    #                     if save: server.messages.save()
                            
    #                     if messagesFormatted == []:
    #                         messagesFormatted.append(f"You don't have any active {self._type_lower}s yet! Create one!")
                        
    #                     messagesFormatted_String = '\n'.join(messagesFormatted)
                        
    #                     persistentNotice = f"\n\nThe 🔒 symbol indicates that the message is persistent. To enable / disable persistency, go to the message, right click, go to `Apps → Edit → Prioritize / Deprioritize`"
    #                     if maxMessages == None: persistentNotice = ""
                        
    #                     embed = nextcord.Embed(title = f"Dashboard - Active Messages - {self._type}s",
    #                                            description = f"Manage your active {self._type_lower}s here.{persistentNotice}\n\n**Active {self._type}s**\n{messagesFormatted_String}",
    #                                            color = nextcord.Color.blue())
                        
    #                     await interaction.followup.edit_message(main_message.id, embed = embed)
                        
    #                 async def backBtnCallback(self, interaction: Interaction):
    #                     await self.outer.setup(interaction)
                            
    #                 async def refreshBtnCallback(self, interaction: Interaction):
    #                     # Reload and Recheck
    #                     await self.setup(interaction)
                    
    #             async def callback(self, interaction: Interaction):
    #                 await self.TheView(self.outer, self._type).setup(interaction)
                
    #         async def backBtnCallback(self, interaction: Interaction):
    #             await self.outer.setup(interaction)
            
    #     async def callback(self, interaction: Interaction):
    #         await self.ActiveMessagesView(self.outer).setup(interaction)
        
    # class ExtraFeaturesButton(nextcord.ui.Button):
    #     def __init__(self, outer):
    #         super().__init__(label = "Extra Features", style = nextcord.ButtonStyle.gray, row = 2)
    #         self.outer = outer
            
    #     class ExtraFeaturesButton(nextcord.ui.View):
    #         def __init__(self, outer, guildID):
    #             super().__init__(timeout = None)
    #             self.outer = outer
    #             self.server = Server_DEP(guildID)

    #             self.autoDeleteInvitesBtn = self.EnableDisableButton(self, "Delete Invites", self.server)
    #             self.add_item(self.autoDeleteInvitesBtn)
                
    #             self.getUpdatesBtn = self.EnableDisableButton(self, "Update Messages", self.server)
    #             self.add_item(self.getUpdatesBtn)
                
                
    #             self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
    #             self.backBtn.callback = self.backBtnCallback
    #             self.add_item(self.backBtn)
                
    #         async def setup(self, interaction: Interaction):
    #             for child in self.children: 
    #                 del child 
    #                 self.__init__(self.outer, interaction.guild.id)
                
    #             self.server = Server_DEP(interaction.guild.id)
                
    #             settings_value = f"""
    #             **{self.boolToString(self.server.delete_invites_enabled)} - Delete Invites**
    #             InfiniBot can automatically delete discord invites posted by members. (Does not affect Administrators)
                
    #             **{self.boolToString(self.server.get_updates_enabled)} - Update Messages**
    #             Get notified about brand-new updates to InfiniBot.
    #             """
                
    #             # On Mobile, extra spaces cause problems. We'll get rid of them here:
    #             settings_value = utils.standardize_str_indention(settings_value)
                
    #             embed = nextcord.Embed(title = "Dashboard - Extra Features", description = f"Choose a feature to enable / disable\n{settings_value}", color = nextcord.Color.blue())
    #             await interaction.response.edit_message(embed = embed, view = self)
             
    #         async def backBtnCallback(self, interaction: Interaction):
    #             await self.outer.setup(interaction)
                
    #         def boolToString(self, bool: bool):
    #             if bool:
    #                 return "✅"
    #             else:
    #                 return "❌"
                                    
    #         class EnableDisableButton(nextcord.ui.Button):
    #             def __init__(self, outer, title, server, row = 0):
    #                 super().__init__(label = title, style = nextcord.ButtonStyle.gray, row = row)
    #                 self.outer = outer
    #                 self.title = title
    #                 self.server = server
                    
    #             class ChooseView(nextcord.ui.View):
    #                 def __init__(self, outer, title, server):
    #                     super().__init__(timeout = None)
    #                     self.outer = outer
    #                     self.title = title
    #                     self.server: Server_DEP = server
                        
    #                     if self.findVariable(self.title, False):
    #                         self.choice = "Disable"
    #                     else:
    #                         self.choice = "Enable"
                        
    #                     self.cancelBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
    #                     self.cancelBtn.callback = self.cancelBtnCommand
    #                     self.add_item(self.cancelBtn)
                        
    #                     self.choiceBtn = nextcord.ui.Button(label = self.choice, style = nextcord.ButtonStyle.green)
    #                     self.choiceBtn.callback = self.choiceBtnCommand
    #                     self.add_item(self.choiceBtn)
                        
    #                 async def setup(self, interaction: Interaction):
    #                     embed = nextcord.Embed(title = f"Enable / Disable {self.title}", description = f"To {self.choice.lower()} {self.title}, click the button \"{self.choice}\"", color = nextcord.Color.blue())
    #                     await interaction.response.edit_message(embed = embed, view = self)
                        
    #                 async def cancelBtnCommand(self, interaction: Interaction):
    #                     await self.outer.setup(interaction)
                        
    #                 async def choiceBtnCommand(self, interaction: Interaction):
    #                     self.findVariable(self.title, True)
                        
    #                     self.server.saveData()
                        
    #                     await self.outer.setup(interaction)
                        
    #                 def findVariable(self, name, change: bool):
    #                     if name == "Delete Invites": 
    #                         if change: self.server.delete_invites_enabled = not self.server.delete_invites_enabled
    #                         return self.server.delete_invites_enabled
    #                     if name == "Update Messages":
    #                         if change: self.server.get_updates_enabled = not self.server.get_updates_enabled
    #                         return self.server.get_updates_enabled
                        
                    
    #                     print("ERROR: Button Name does not correspond with possible values in ChooseView.findVariable")
    #                     return None
                 
    #             async def callback(self, interaction: Interaction):
    #                 await self.ChooseView(self.outer, self.title, self.server).setup(interaction)
                       
    #     async def callback(self, interaction: Interaction):
    #         await self.ExtraFeaturesButton(self.outer, interaction.guild.id).setup(interaction)       

async def run_dashboard_command(interaction: Interaction):
    if await utils.user_has_config_permissions(interaction):
        view = Dashboard(interaction)
        await view.setup(interaction)