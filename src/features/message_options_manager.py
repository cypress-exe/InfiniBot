import nextcord
from nextcord import Interaction

from config.server import Server

# TODO: WORK ON THIS

# class EditEmbed(nextcord.ui.View):s
#     def __init__(self, messageID: int):
#         super().__init__(timeout = None)
#         self.messageID = messageID
        
#     async def loadButtons(self, interaction: Interaction):
#         self.message = await interaction.channel.fetch_message(self.messageID)
#         self.server = Server_DEP(interaction.guild.id)
#         self.messageInfo = self.server.messages.get(self.messageID)
        
#         self.clear_items()
        
#         editTextBtn = self.editTextButton(self)
#         self.add_item(editTextBtn)
        
#         editColorBtn = self.editColorButton(self)
#         self.add_item(editColorBtn)
        
#         editPersistencyBtn = self.editPersistencyButton(self, self.messageInfo)
#         self.add_item(editPersistencyBtn)
        
#     async def setup(self, interaction: Interaction):
#         await self.loadButtons(interaction)
        
#         if not utils.enabled.ActiveMessages(guild_id = interaction.guild.id):
#             await disabled_feature_override(self, interaction)
#             return
        
#         mainEmbed = nextcord.Embed(title = "Edit Embed", description = "Edit the following embed's text and color.", color = nextcord.Color.yellow())
#         editEmbed = self.message.embeds[0]
#         embeds = [mainEmbed, editEmbed]
#         await interaction.response.edit_message(embeds = embeds, view = self)
  
#     class editTextButton(nextcord.ui.Button):
#         def __init__(self, outer):
#             super().__init__(label = "Edit Text", emoji = "✏️")
#             self.outer = outer;
        
#         class editTextModal(nextcord.ui.Modal):
#             def __init__(self, outer):
#                 super().__init__(title = "Edit Text")
#                 self.outer = outer;
                
#                 self.titleInput = nextcord.ui.TextInput(label = "Title", min_length = 1, max_length = 256, placeholder = "Title", default_value = outer.message.embeds[0].title)
#                 self.add_item(self.titleInput)
                
#                 self.descriptionInput = nextcord.ui.TextInput(label = "Description", min_length = 1, max_length = 4000, placeholder = "Description", default_value = outer.message.embeds[0].description, style = nextcord.TextInputStyle.paragraph)
#                 self.add_item(self.descriptionInput)
                
#             async def callback(self, interaction: Interaction):
#                 self.stop();
#                 beforeMessage = await interaction.channel.fetch_message(self.outer.message.id)
#                 await beforeMessage.edit(embed = nextcord.Embed(title = self.titleInput.value, description = self.descriptionInput.value, color = beforeMessage.embeds[0].color))
#                 await self.outer.setup(interaction);
                
#                 # Trigger Edit Log
#                 afterMessage = await interaction.channel.fetch_message(self.outer.message.id)
#                 await trigger_edit_log(interaction.guild, beforeMessage, afterMessage, user = interaction.user)
        
#         async def callback(self, interaction: Interaction):
#             await interaction.response.send_modal(self.editTextModal(self.outer))
        
#     class editColorButton(nextcord.ui.Button):
#         def __init__(self, outer):
#             super().__init__(label = "Edit Color", emoji = "🎨")
#             self.outer = outer
            
#         class editColorView(nextcord.ui.View):
#             def __init__(self, outer):
#                 super().__init__()
#                 self.outer = outer;
                
#                 options = ["Red", "Green", "Blue", "Yellow", "White", "Blurple", "Greyple", "Teal", "Purple", "Gold", "Magenta", "Fuchsia"]
                
#                 originalColor = get_string_from_discord_color(self.outer.message.embeds[0].color)        
#                 selectOptions = []
#                 for option in options:
#                     selectOptions.append(nextcord.SelectOption(label = option, value = option, default = (option == originalColor)))
                
#                 self.select = nextcord.ui.Select(placeholder = "Choose a color", options = selectOptions)
                
#                 self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.gray)
#                 self.backBtn.callback = self.backCallback

#                 self.button = nextcord.ui.Button(label = "Update Color", style = nextcord.ButtonStyle.blurple)
#                 self.button.callback = self.createCallback
                
#                 self.add_item(self.select)
#                 self.add_item(self.backBtn)
#                 self.add_item(self.button)
                
#             async def setup(self, interaction: Interaction):
#                 description = f"""Choose what color you would like the embed to be:
                
#                 **Colors Available**
#                 Red, Green, Blue, Yellow, White
#                 Blurple, Greyple, Teal, Purple
#                 Gold, Magenta, Fuchsia"""
                
                
#                 # On Mobile, extra spaces cause problems. We'll get rid of them here:
#                 description = standardize_str_indention(description)
    
#                 embed = nextcord.Embed(title = "Edit Color", description = description, color = nextcord.Color.yellow())
#                 await interaction.response.edit_message(embed = embed, view = self)
                    
#             async def createCallback(self, interaction: Interaction):
#                 if self.select.values == []: return
#                 self.selection = self.select.values[0]
#                 self.stop()
                
#                 message = await interaction.channel.fetch_message(self.outer.message.id)
#                 await message.edit(embed = nextcord.Embed(title = message.embeds[0].title, description = message.embeds[0].description, color = (get_discord_color_from_string(self.selection))))
#                 await self.outer.setup(interaction)
       
#             async def backCallback(self, interaction: Interaction):
#                 await self.outer.setup(interaction)
       
#         async def callback(self, interaction: Interaction):
#             await self.editColorView(self.outer).setup(interaction)
    
#     class editPersistencyButton(nextcord.ui.Button):
#         def __init__(self, outer, messageInfo: Message):
#             if messageInfo.persistent:
#                 text = "Deprioritize"
#                 icon = "🔓"
#             else:
#                 text = "Prioritize"
#                 icon = "🔒"
                
#             super().__init__(label = text, emoji = icon)
#             self.outer = outer
#             self.messageID = messageInfo.message_id
        
#         class warningView(nextcord.ui.View):
#             def __init__(self, outer, guildID: int, messageID: int):
#                 super().__init__(timeout = None)
#                 self.outer = outer
                
#                 self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger) 
#                 self.backBtn.callback = self.backBtnCallback
#                 self.add_item(self.backBtn)
                
#                 self.continueBtn = self.continueButton(self.outer, guildID, messageID)
#                 self.add_item(self.continueBtn)
                
#             async def setup(self, interaction: Interaction):
#                 messages = Messages(interaction.guild.id)
#                 max = messages.maxOf("Embed")
                
                
#                 embed = nextcord.Embed(title = "Edit Embed - Prioritize / Deprioritize", 
#                                        description = persistent_warning_description(_type = "embed", max = max, uses = ["rules", "onboarding information", "similar content"]), 
#                                        color = nextcord.Color.yellow())
                
#                 await interaction.response.edit_message(embed = embed, view = self)
                
#             async def backBtnCallback(self, interaction: Interaction):
#                 await self.outer.setup(interaction)
        
#             class continueButton(nextcord.ui.Button):
#                 def __init__(self, outer, guildID: int, messageID: int):
#                     self.server = Server_DEP(guildID)
#                     self.messageInfo = self.server.messages.get(messageID)
                    
#                     if self.messageInfo.persistent:
#                         text = "Deprioritize"
#                     else:
#                         text = "Prioritize"
                        
#                     super().__init__(label = text, style = nextcord.ButtonStyle.blurple)
#                     self.outer = outer
                    
#                 async def callback(self, interaction: Interaction):
#                     self.messageInfo.persistent = not self.messageInfo.persistent
#                     self.server.messages.save()
                    
#                     await self.outer.setup(interaction)
        
#         async def callback(self, interaction: Interaction):
#             await self.warningView(self.outer, interaction.guild.id, self.messageID).setup(interaction)
          
class EditReactionRole(nextcord.ui.View):
    def __init__(self, messageID: int):
        super().__init__(timeout = None)
        self.messageID = messageID
        
    async def loadButtons(self, interaction: Interaction):
        self.message = await interaction.channel.fetch_message(self.messageID)
        self.server = Server(interaction.guild.id)
        self.message_info = self.server.messages.get(self.messageID)
        
        self.clear_items()
        
        editTextBtn = self.editTextButton(self)
        self.add_item(editTextBtn)
        
        editOptionsBtn = self.editOptionsButton(self, self.message_info)
        self.add_item(editOptionsBtn)
        
    async def setup(self, interaction: Interaction):
        await self.loadButtons(interaction)
        
        if not utils.enabled.ActiveMessages(guild_id = interaction.guild.id):
            await disabled_feature_override(self, interaction)
            return
        
        mainEmbed = nextcord.Embed(title = "Edit Reaction Role", description = "Edit the following reaction role's text and options.", color = nextcord.Color.yellow())
        editEmbed = self.message.embeds[0]
        embeds = [mainEmbed, editEmbed]
        await interaction.response.edit_message(embeds = embeds, view = self)
  
    class editTextButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Edit Text", emoji = "✏️")
            self.outer = outer;
        
        class editTextModal(nextcord.ui.Modal):
            def __init__(self, outer):
                super().__init__(title = "Edit Text")
                self.outer = outer;
                
                self.titleInput = nextcord.ui.TextInput(label = "Title", min_length = 1, max_length = 256, placeholder = "Title", default_value = outer.message.embeds[0].title)
                self.add_item(self.titleInput)
                
                self.descriptionInput = nextcord.ui.TextInput(label = "Description", min_length = 1, max_length = 4000, placeholder = "Description", default_value = outer.message.embeds[0].description, style = nextcord.TextInputStyle.paragraph)
                self.add_item(self.descriptionInput)
                
            async def callback(self, interaction: Interaction):
                self.stop();
                beforeMessage = await interaction.channel.fetch_message(self.outer.message.id)
                
                embed = nextcord.Embed(title = self.titleInput.value, description = self.descriptionInput.value, color = beforeMessage.embeds[0].color)
                for field in beforeMessage.embeds[0].fields:
                    embed.add_field(name = field.name, value = field.value, inline = field.inline)
                    
                await beforeMessage.edit(embed = embed)
                await self.outer.setup(interaction);
                
                # Trigger Edit Log
                afterMessage = await interaction.channel.fetch_message(self.outer.message.id)
                await trigger_edit_log(interaction.guild, beforeMessage, afterMessage, user = interaction.user)
        
        async def callback(self, interaction: Interaction):
            await interaction.response.send_modal(self.editTextModal(self.outer))
  
    class editOptionsButton(nextcord.ui.Button):
        def __init__(self, outer, messageInfo: Message):
            super().__init__(label = "Edit Options", emoji = "🎚️")
            self.outer = outer;
            self.messageInfo = messageInfo
        
        class editOptionsView(nextcord.ui.View):
            def __init__(self, outer, messageInfo: Message):
                super().__init__(timeout = None)
                self.outer = outer
                self.messageInfo = messageInfo
                self.addedReactions_Emojis = []
                self.addedRoles_IDs = []
                self.addedOptions_noFormat = []
                self.messageID = None
                
                self.addBtn = self.addButton(self, self.messageInfo)
                self.add_item(self.addBtn)
                
                self.deleteBtn = self.deleteButton(self, self.messageInfo)
                self.add_item(self.deleteBtn)
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.gray, row = 1) 
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
            async def setup(self, interaction: Interaction):             
                # Get the message
                channel = await interaction.guild.fetch_channel(self.messageInfo.channel_id)
                message = await channel.fetch_message(self.messageInfo.message_id)       
                            
                # Get all options
                options = message.embeds[0].fields[0].value.split("\n")
                self.optionsFormatted, problem = self.formatOptions(interaction.guild, options)
                
                # Create UI
                embed = nextcord.Embed(title = "Edit Reaction Role - Edit Options",
                                       description = "Add, Manage, and Delete Options.",
                                       color = nextcord.Color.yellow())
                
                embed.add_field(name = "Roles", value = "\n".join(self.optionsFormatted))
                
                # Help Messages
                if problem:
                    embed.add_field(name = "⚠️ Issue With One or More Roles ⚠️", value = "One or more of your roles no longer exist.", inline = False)
                    
                    
                # ============================================ OTHER SETUP ============================================
                
                
                #Prepare Available Roles
                self.availableRoles = []
                
                for role in interaction.guild.roles:
                    if role.name == "@everyone": continue
                    if role.id in self.addedRoles_IDs: continue
                    if canAssignRole(role): self.availableRoles.append(role)
                    
                
                # Check Buttons and their Availability
                if len(self.optionsFormatted) >= 10 and len(self.availableRoles) > 0:
                    self.addBtn.disabled = True
                else:
                    self.addBtn.disabled = False
                    
                if len(self.optionsFormatted) <= 1:
                    self.deleteBtn.disabled = True
                else:
                    self.deleteBtn.disabled = False
                    
                    
                # Edit the message
                try:
                    message = await interaction.response.edit_message(embed = embed, view = self)
                    self.messageID = message.id
                except:
                    await interaction.followup.edit_message(message_id = self.messageID, embed = embed, view = self)

            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
           
            def getRole(self, guild: nextcord.Guild, string: str):
                pattern = r"^(<@&)(.*)>$"  # "<@&...>"
                match = re.search(pattern, string)
                if match:
                    id = int(match.group(2))
                    role = nextcord.utils.get(guild.roles, id = id)
                elif string.isdigit():
                    role = nextcord.utils.get(guild.roles, id = int(string))
                else:
                    role = nextcord.utils.get(guild.roles, name = string)
                    
                return role
           
            def formatOptions(self, guild: nextcord.Guild, lines: list[str], packetToModify = None, displayErrors = True):
                self.addedRoles_IDs = []
                self.addedReactions_Emojis = []
                self.addedOptions_noFormat = []
                
                returnList = []
                problem = False
                
                _type = self.messageInfo.parameters[0]
                mentionRoles = (True if self.messageInfo.parameters[1] == "1" else False)
                
                # Inject another role if we are modifying a role. If we are deleting the role, well, we actually have it twice and ignore it twice.
                if packetToModify:
                    if packetToModify[0] == None: packetToModify[0] = "🚫"
                    lines.append(f"{packetToModify[0]} {packetToModify[1]}")

                addedOptions_Asci = []
                number = 1
                ignoreExtraPacket = False
                for index, line in enumerate(lines):
                    lineSplit = line.split(" ") # Emoji, Role
                    rawRoleName = " ".join(lineSplit[1:])
                    role: nextcord.Role = self.getRole(guild, rawRoleName)
                    
                    # Do some modification checks
                    if packetToModify:
                        if role and packetToModify[1] and role.id == int(packetToModify[1]): # If the ids match
                            if ignoreExtraPacket:
                                continue
                            if index != (len(lines) - 1): # If this is not the last item in the list
                                ignoreExtraPacket = True
                                continue
                    
                    # Manage the apparent name of the role
                    if role:
                        name = (role.mention if mentionRoles else role.name)
                        firstLetter = role.name[0].lower()
                        nonFormattedName = role.name
                    else:
                        if not displayErrors: continue
                        name = f"⚠️ {rawRoleName} ⚠️"
                        nonFormattedName = f"⚠️ {rawRoleName} ⚠️"
                        firstLetter = None
                        problem = True
                    
                    if firstLetter:
                        if _type == "0":
                            # Letter Reaction Role
                            if not firstLetter in addedOptions_Asci: # If this letter has not already been used as a reaction
                                emoji, letter_used = asci_to_emoji(firstLetter, fallback_letter = getNextOpenLetter(addedOptions_Asci))
                                addedOptions_Asci.append(letter_used)
                            else:
                                nextOpenLetter = getNextOpenLetter(addedOptions_Asci)
                                emoji, letter_used = asci_to_emoji(nextOpenLetter)
                                addedOptions_Asci.append(letter_used)
                        elif _type == "1":
                            # Number Reaction Role
                            emoji = asci_to_emoji(number)
                            number += 1
                        else:
                            # Custom Reaction Role
                            emoji = lineSplit[0]
                    else:
                        emoji = "❌"
                        
                    
                    self.addedRoles_IDs.append(role.id if role else None)
                    self.addedReactions_Emojis.append(emoji)
                    self.addedOptions_noFormat.append(f"{emoji} {nonFormattedName}")
                    returnList.append(f"{emoji} {name}")
                    
                return returnList, problem

            async def addOrRemoveOption(self, interaction: Interaction, emoji, roleID, index = None):
                # Get the message
                channel = await interaction.guild.fetch_channel(self.messageInfo.channel_id)
                message = await channel.fetch_message(self.messageInfo.message_id)
                            
                # Get all options
                options = message.embeds[0].fields[0].value.split("\n")
                
                # (Add some helping code for deleting)
                if index is not None:
                    emoji = self.addedReactions_Emojis[index]
                    roleID = self.addedRoles_IDs[index]
                
                # Continue getting the options
                optionsFormatted, problem = self.formatOptions(interaction.guild, options, packetToModify = [emoji, roleID], displayErrors = False)
                
                
                # Get new embed
                newEmbed = nextcord.Embed(title = message.embeds[0].title, description = message.embeds[0].description, color = message.embeds[0].color)
                newEmbed.add_field(name = "React for the following roles", value = "\n".join(optionsFormatted), inline = False)
                
                # Update embed
                await message.edit(embed = newEmbed)
                
                # Go back
                await self.setup(interaction)
                
                # Update Reactions
                await message.clear_reactions()
                addedEmojiUses = 0
                for index, reaction in enumerate(self.addedReactions_Emojis):
                    if reaction == emoji:
                        addedEmojiUses += 1
                        if addedEmojiUses >= 2:
                            # If this is the emoji that we're using now and this isn't the last thing,
                            # We messed up. We gotta remove this guy
                            await self.addOrRemoveOption(interaction, emoji, roleID)
                            await interaction.followup.send(embed = nextcord.Embed(title = "Can't Use the Same Emoji", description = "Every Emoji has to be unique. Try again.", color = nextcord.Color.red()), ephemeral = True)
                            return
                    try:
                        await message.add_reaction(emoji = reaction)
                    except (nextcord.errors.Forbidden, nextcord.errors.HTTPException):
                        try:
                            await interaction.followup.send(embed = nextcord.Embed(title = "Emoji Error", description = f"InfiniBot is unable to apply the emoji: \"{reaction}\". If the emoji *is* valid, check that InfiniBot has the permission \"Add Reactions\".", color = nextcord.Color.red()), ephemeral = True)
                        except nextcord.errors.Forbidden:
                            await sendErrorMessageToOwner(interaction.guild, "Add Reactions")
                        await self.addOrRemoveOption(interaction, reaction, self.addedRoles_IDs[index])
                     
            class addButton(nextcord.ui.Button):
                def __init__(self, outer, messageInfo: Message):
                    super().__init__(label = "Add Role")
                    self.outer = outer
                    self.messageInfo = messageInfo
                    
                async def callback(self, interaction: Interaction):                     
                    selectOptions = []
                    availableRoles: list[nextcord.Role] = self.outer.availableRoles
                    for role in availableRoles:
                        selectOptions.append(nextcord.SelectOption(label = role.name, value = role.id, description = role.id))
                    
                    embed = nextcord.Embed(title = "Edit Reaction Role - Edit Options - Add Role", description = "Add a Role to your Reaction Role.\n\n**Don't See Your Role?**\nMake sure InfiniBot has permission to assign it (higher role or administrator).", color = nextcord.Color.yellow())
                    await SelectView(embed, selectOptions, self.SelectViewCallback, continueButtonLabel = "Add Role", preserveOrder = True).setup(interaction)
                    
                async def SelectViewCallback(self, interaction: Interaction, selection):
                    if selection == None: 
                        await self.outer.setup(interaction)
                        return
                    
                    if self.messageInfo.parameters[0] == "2": # If this is a custom reaction role,
                        await self.emojiSelectView(self.outer, selection).setup(interaction)
                        return;
                    
                    await self.outer.addOrRemoveOption(interaction, None, selection)
                    
                class emojiSelectView(nextcord.ui.View):
                    def __init__(self, outer, selection):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.selection = selection
                        
                        backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        backBtn.callback = self.backBtnCallback
                        self.add_item(backBtn)
                        
                        nextBtn = nextcord.ui.Button(label = "Next", style = nextcord.ButtonStyle.blurple)
                        nextBtn.callback = self.nextBtnCallback
                        self.add_item(nextBtn)
                        
                    async def setup(self, interaction: Interaction):
                        embed = nextcord.Embed(title = "Edit Reaction Role - Edit Options - Add Role", description = "Because this is a custom reaction role, InfiniBot requires an emoji. Therefore, you need to get an emoji into your clipboard (unless you're fancy and know unicode.)\n\n**How?**\nGo to a channel that you don't care about (or InfiniBot's dms) and select the emoji you want. Then, send it, and copy what you sent. Now, come back and click \"Next\".", color = nextcord.Color.yellow())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    async def nextBtnCallback(self, interaction: Interaction):
                        await interaction.response.send_modal(self.emojiSelectModal(self.outer, self.selection))
                   
                    class emojiSelectModal(nextcord.ui.Modal):
                        def __init__(self, outer, selection):
                            super().__init__(title = "Emoji Selection")
                            self.outer = outer
                            self.selection = selection
                            
                            self.emojiTextInput = nextcord.ui.TextInput(label = "Paste the emoji for this option.", max_length = 100)     
                            self.add_item(self.emojiTextInput)
                            
                        async def callback(self, interaction: Interaction):
                            await self.outer.addOrRemoveOption(interaction, self.emojiTextInput.value, self.selection)
                              
            class deleteButton(nextcord.ui.Button):
                def __init__(self, outer, messageInfo: Message):
                    super().__init__(label = "Delete Role")
                    self.outer = outer
                    self.messageInfo = messageInfo
                    
                async def callback(self, interaction: Interaction):                     
                    selectOptions = []
                    
                    for index, option in enumerate(self.outer.addedOptions_noFormat):
                        selectOptions.append(nextcord.SelectOption(label = option, value = index))
                    
                    embed = nextcord.Embed(title = "Edit Reaction Role - Edit Options - Delete Role", description = "Delete a Role from your Reaction Role.", color = nextcord.Color.yellow())
                    await SelectView(embed, selectOptions, self.SelectViewCallback, continueButtonLabel = "Delete Role", preserveOrder = True).setup(interaction)
                    
                async def SelectViewCallback(self, interaction: Interaction, selection):
                    if selection == None: 
                        await self.outer.setup(interaction)
                        return
                    
                    await self.outer.addOrRemoveOption(interaction, None, None, index = int(selection))
                           
        async def callback(self, interaction: Interaction):
            await self.editOptionsView(self.outer, self.messageInfo).setup(interaction)
        
# class EditRoleMessage(nextcord.ui.View):
#     def __init__(self, messageID: int):
#         super().__init__(timeout = None)
#         self.messageID = messageID
        
#         self.title = None
#         self.description = None
#         self.color = None
#         self.options: list[list[list[int], str, str]] = []
        
#     class EditTextButton(nextcord.ui.Button):
#         def __init__(self, outer):
#             super().__init__(label = "Edit Text", emoji = "✏️")
#             self.outer = outer;
        
#         class EditTextModal(nextcord.ui.Modal):
#             def __init__(self, outer):
#                 super().__init__(title = "Edit Text")
#                 self.outer = outer;
                
#                 self.titleInput = nextcord.ui.TextInput(label = "Title", min_length = 1, max_length = 256, placeholder = "Title", default_value = outer.title)
#                 self.add_item(self.titleInput)
                
#                 self.descriptionInput = nextcord.ui.TextInput(label = "Description", min_length = 1, max_length = 4000, placeholder = "Description", default_value = outer.description, style = nextcord.TextInputStyle.paragraph, required = False)
#                 self.add_item(self.descriptionInput)
                
#             async def callback(self, interaction: Interaction):
#                 self.stop();
#                 self.outer.title = self.titleInput.value
#                 self.outer.description = self.descriptionInput.value
                
#                 await self.outer.setup(interaction)
        
#         async def callback(self, interaction: Interaction):
#             await interaction.response.send_modal(self.EditTextModal(self.outer))
        
#     class EditColorButton(nextcord.ui.Button):
#         def __init__(self, outer):
#             super().__init__(label = "Edit Color", emoji = "🎨")
#             self.outer = outer
            
#         class EditColorView(nextcord.ui.View):
#             def __init__(self, outer):
#                 super().__init__()
#                 self.outer = outer;
                
#                 options = ["Red", "Green", "Blue", "Yellow", "White", "Blurple", "Greyple", "Teal", "Purple", "Gold", "Magenta", "Fuchsia"]
                
#                 originalColor = get_string_from_discord_color(self.outer.color)        
#                 selectOptions = []
#                 for option in options:
#                     selectOptions.append(nextcord.SelectOption(label = option, value = option, default = (option == originalColor)))
                
#                 self.select = nextcord.ui.Select(placeholder = "Choose a color", options = selectOptions)
                
#                 self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.gray)
#                 self.backBtn.callback = self.backCallback

#                 self.button = nextcord.ui.Button(label = "Update Color", style = nextcord.ButtonStyle.blurple)
#                 self.button.callback = self.createCallback
                
#                 self.add_item(self.select)
#                 self.add_item(self.backBtn)
#                 self.add_item(self.button)
                
#             async def setup(self, interaction: Interaction):
#                 description = f"""Choose what color you would like the role message to be:
                
#                 **Colors Available**
#                 Red, Green, Blue, Yellow, White
#                 Blurple, Greyple, Teal, Purple
#                 Gold, Magenta, Fuchsia"""
                
                
#                 # On Mobile, extra spaces cause problems. We'll get rid of them here:
#                 description = standardize_str_indention(description)
    
#                 embed = nextcord.Embed(title = "Edit Role Message - Edit Color", description = description, color = nextcord.Color.yellow())
#                 await interaction.response.edit_message(embed = embed, view = self)
                    
#             async def createCallback(self, interaction: Interaction):
#                 if self.select.values == []: return
#                 self.selection = self.select.values[0]
#                 self.stop()
                
#                 self.outer.color = get_discord_color_from_string(self.selection)
                
#                 await self.outer.setup(interaction)
    
#             async def backCallback(self, interaction: Interaction):
#                 await self.outer.setup(interaction)
    
#         async def callback(self, interaction: Interaction):
#             await self.EditColorView(self.outer).setup(interaction)
        
#     class AddBtn(nextcord.ui.Button):
#         def __init__(self, outer, options):
#             super().__init__(label = "Add Option", style = nextcord.ButtonStyle.gray, disabled = (len(options) >= 25), emoji = "🔨")
                
#             self.outer = outer
#             self.options = options
            
#         class AddView(nextcord.ui.View):
#             def __init__(self, outer, options, index = None):
#                 super().__init__(timeout = None)
#                 self.outer = outer
#                 self.options = options
#                 self.index = index
                
#                 if self.index == None:
#                     self.title = None
#                     self.description = None
#                     self.roles: list[int] = []
#                     self.editing = False
#                 else:
#                     self.title = self.options[index][1]
#                     self.description = self.options[index][2]
#                     self.roles: list[int] = self.options[index][0]
#                     self.editing = True
                    
#                 # Make roles all ints
#                 self.roles = [int(role) for role in self.roles]
                
#                 changeTextBtn = nextcord.ui.Button(label = "Change Text")
#                 changeTextBtn.callback = self.changeTextBtnCallback
#                 self.add_item(changeTextBtn)
                
#                 self.addRoleBtn = nextcord.ui.Button(label = "Add Role")
#                 self.addRoleBtn.callback = self.addRoleBtnCallback
#                 self.add_item(self.addRoleBtn)
                
#                 self.removeRoleBtn = nextcord.ui.Button(label = "Remove Role")
#                 self.removeRoleBtn.callback = self.removeRoleBtnCallback
#                 self.add_item(self.removeRoleBtn)
                
#                 self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = (2 if len(self.outer.options) <= 1 else 1))
#                 self.backBtn.callback = self.backBtnCallback
#                 # Only add if this is not the first option
#                 if len(self.outer.options) > 0:
#                     self.add_item(self.backBtn)
                
#                 self.finishBtn = nextcord.ui.Button(label = ("Finish" if not self.editing else "Save"), style = nextcord.ButtonStyle.blurple, row = 1)
#                 self.finishBtn.callback = self.finishBtnCallback
#                 self.add_item(self.finishBtn)
                
#             async def validateData(self, interaction: Interaction):
#                 """Make sure you refresh the view after running this"""
#                 self.addableRoles = []
#                 for role in interaction.guild.roles:
#                     if role.name == "@everyone": continue
#                     if role.id in self.roles: continue
#                     if canAssignRole(role):
#                         self.addableRoles.append(nextcord.SelectOption(label = role.name, value = role.id))
                        
#                 self.removableRoles = []
#                 for role in self.roles:
#                     discordRole = interaction.guild.get_role(role)
#                     if discordRole:
#                         self.removableRoles.append(nextcord.SelectOption(label = discordRole.name, value = role))
#                     else:
#                         self.removableRoles.append(nextcord.SelectOption(label = "~ Deleted Role ~", value = role, emoji = "⚠️"))
                    
#                 # Validate buttons
#                 self.addRoleBtn.disabled = len(self.addableRoles) == 0
#                 self.removeRoleBtn.disabled = len(self.removableRoles) <= 1
                
#             async def setup(self, interaction: Interaction):
#                 # Validate Data
#                 await self.validateData(interaction)
                
#                 if len(self.roles) == 0 and not self.editing:
#                     # Send the user past this view.
#                     await self.addRoleBtnCallback(interaction)
#                 else:
#                     if not self.editing:
#                         embed = nextcord.Embed(title = "Edit Role Message - Add Option", description = "You have the option to add more roles or make changes to the text. Here is a mockup of what this option will look like:", color = nextcord.Color.yellow())
#                     else:
#                         embed = nextcord.Embed(title = "Edit Role Message - Edit Option", description = "You have the option to add more roles or make changes to the text. Here is a mockup of what this option will look like:", color = nextcord.Color.yellow())
                    
#                     self.outer.addField(embed, [self.roles, self.title, self.description])
                    
#                     await interaction.response.edit_message(embed = embed, view = self)
                    
#             async def addRoleBtnCallback(self, interaction: Interaction):
#                 # Update Information
#                 await self.validateData(interaction)
#                 if self.addRoleBtn.disabled:
#                     await self.setup(interaction)
#                     return
                
#                 # Have 2 embeds. One for the first visit, and another for a re-visit
#                 if len(self.roles) == 0:
#                     embed = nextcord.Embed(title = "Role Message Creation Wizard - Add Option", description = "Please select a role. This choice will be added as one of the options.\n\n**Unable to find a role?**\nIf you are unable to find a role, please ensure that InfiniBot has the necessary permissions to assign roles, such as managing messages and having a higher rank.", color = nextcord.Color.green())
#                 else:
#                     embed = nextcord.Embed(title = "Role Message Creation Wizard - Add Option - Add Role", description = "Select a role to be granted when the user chooses this option.\n\n**Unable to find a role?**\nIf you are unable to find a role, please ensure that InfiniBot has the necessary permissions to assign roles, such as managing messages and having a higher rank.", color = nextcord.Color.green())
#                 await SelectView(embed = embed, options = self.addableRoles, returnCommand = self.addRoleBtnSelectViewCallback, placeholder = "Choose a Role", continueButtonLabel = "Use Role").setup(interaction)
                
#             async def addRoleBtnSelectViewCallback(self, interaction: Interaction, value: str):
#                 if value == None:
#                     # User canceled. Return them to us.
#                     # Unless they actually came from the original view. If so, let's send them back to that.
#                     if self.roles == []:
#                         await self.outer.setup(interaction)
#                         return
#                     else:
#                         await self.setup(interaction)
#                         return
                    
#                 if value.isdigit():
#                     self.roles.append(int(value))
                
#                 # Send them to the modal, or just back home
#                 if self.title == None:
#                     await interaction.response.send_modal(self.OptionTitleAndDescriptionModal(self))
#                 else:
#                     await self.setup(interaction)
                
#             class OptionTitleAndDescriptionModal(nextcord.ui.Modal):
#                 def __init__(self, outer):
#                     super().__init__(title = "Option Settings", timeout = None)
#                     self.outer = outer

#                     if self.outer.title == None:
#                         self.titleInput = nextcord.ui.TextInput(label = "Please provide a name for that option", max_length = 100)
#                     else:
#                         self.titleInput = nextcord.ui.TextInput(label = "Option Name", max_length = 100, default_value = self.outer.title)
#                     self.add_item(self.titleInput)
                    
#                     if self.outer.description == None:
#                         self.descriptionInput = nextcord.ui.TextInput(label = "Add a description (optional)", max_length = 100, required = False)
#                     else:
#                         self.descriptionInput = nextcord.ui.TextInput(label = "Description (optional)", max_length = 100, required = False, default_value = self.outer.description)
#                     self.add_item(self.descriptionInput)
                    
#                 async def callback(self, interaction: Interaction):
#                     self.outer.title = self.titleInput.value
#                     self.outer.description = self.descriptionInput.value
                    
#                     await self.outer.setup(interaction)
                                    
#             async def changeTextBtnCallback(self, interaction: Interaction):
#                 await interaction.response.send_modal(self.OptionTitleAndDescriptionModal(self))
            
#             async def removeRoleBtnCallback(self, interaction: Interaction): 
#                 # Update Information
#                 await self.validateData(interaction)
#                 if self.removeRoleBtn.disabled:
#                     await self.setup(interaction)
#                     return
                
#                 embed = nextcord.Embed(title = "Role Message Creation Wizard - Add Option - Remove Role", description = "Choose a role to be removed from this option.", color = nextcord.Color.green())
#                 await SelectView(embed = embed, options = self.removableRoles, returnCommand = self.removeRoleBtnSelectViewCallback, placeholder = "Choose a Role", continueButtonLabel = "Remove Role").setup(interaction)
                
#             async def removeRoleBtnSelectViewCallback(self, interaction: Interaction, value: str):
#                 if value == None:
#                     await self.setup(interaction)
#                     return
                    
#                 if value.isdigit() and int(value) in self.roles:
#                     self.roles.remove(int(value))
                
#                 await self.setup(interaction)
                
#             async def backBtnCallback(self, interaction: Interaction):
#                 await self.outer.setup(interaction)
                            
#             async def finishBtnCallback(self, interaction: Interaction):
#                 if not self.editing:
#                     # Add data to self.outer.options in the form of list[list[int], str, str]
#                     self.outer.options.append([self.roles, self.title, self.description])
#                 else:
#                     self.outer.options[self.index] = [self.roles, self.title, self.description]
                
#                 await self.outer.setup(interaction)
                                
#         async def callback(self, interaction: Interaction):
#             await self.AddView(self.outer, self.options).setup(interaction)
    
#     class EditBtn(nextcord.ui.Button):
#         def __init__(self, outer, options):
#             super().__init__(label = "Edit Option", emoji = "⚙️")
#             self.outer = outer
#             self.options: list[list[list[int], str, str]] = options
            
#         async def callback(self, interaction: Interaction):
#             # Get the options
#             selectOptions = []
#             for index, option in enumerate(self.options):
#                 selectOptions.append(nextcord.SelectOption(label = option[1], description = option[2], value = index))
            
#             embed = nextcord.Embed(title = "Edit Role Message - Edit Option", description = "Choose an option to edit", color = nextcord.Color.yellow())
#             await SelectView(embed = embed, options = selectOptions, returnCommand = self.selectViewCallback, continueButtonLabel = "Edit", preserveOrder = True).setup(interaction)
        
#         async def selectViewCallback(self, interaction, selection):
#             if selection == None:
#                 await self.outer.setup(interaction)
#                 return
                
#             # Send them to the editing
#             await self.outer.AddBtn.AddView(self.outer, self.options, index = int(selection)).setup(interaction)
     
#     class RemoveBtn(nextcord.ui.Button):
#         def __init__(self, outer, options):
#             super().__init__(label = "Remove Option", disabled = (len(options) <= 1), emoji = "🚫")
#             self.outer = outer
#             self.options: list[list[list[int], str, str]] = options
            
#         async def callback(self, interaction: Interaction):
#             # Get the options
#             selectOptions = []
#             for index, option in enumerate(self.options):
#                 selectOptions.append(nextcord.SelectOption(label = option[1], description = option[2], value = index))
            
#             embed = nextcord.Embed(title = "Edit Role Message - Remove Option", description = "Choose an option to remove", color = nextcord.Color.yellow())
#             await SelectView(embed = embed, options = selectOptions, returnCommand = self.selectViewCallback, continueButtonLabel = "Remove", preserveOrder = True).setup(interaction)
        
#         async def selectViewCallback(self, interaction, selection):
#             if selection == None:
#                 await self.outer.setup(interaction)
#                 return
                
#             self.outer.options.pop(int(selection))
            
#             await self.outer.setup(interaction)
        
#     class EditModeBtn(nextcord.ui.Button):
#         def __init__(self, outer):
#             super().__init__(label = "Change Mode", row = 1, emoji = "🎚️")
#             self.outer = outer
            
#         class MultiOrSingleSelectView(nextcord.ui.View):
#             def __init__(self, outer):
#                 super().__init__(timeout = None)
#                 self.outer = outer
                
#                 options = [nextcord.SelectOption(label = "Single", description = "Members can only select one option", value = "Single", default = (self.outer.mode == "Single")),
#                             nextcord.SelectOption(label = "Multiple", description = "Members can select multiple options.", value = "Multiple", default = (self.outer.mode == "Multiple"))]
                
#                 self.select = nextcord.ui.Select(options = options, placeholder = "Choose a Mode")
#                 self.add_item(self.select)
                
#                 self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1) 
#                 self.backBtn.callback = self.backBtnCallback
#                 self.add_item(self.backBtn)
                
#                 self.createBtn = nextcord.ui.Button(label = "Change Mode", style = nextcord.ButtonStyle.blurple)
#                 self.createBtn.callback = self.createBtnCallback
#                 self.add_item(self.createBtn)
                
#             async def setup(self, interaction: Interaction):
#                 embed = nextcord.Embed(title = "Edit Role Message - Change Mode", description = "Decide whether you want members to have the option to select multiple choices or just one.", color = nextcord.Color.yellow())
#                 await interaction.response.edit_message(embed = embed, view = self)
            
#             async def backBtnCallback(self, interaction: Interaction):
#                 await self.outer.setup(interaction)
            
#             async def createBtnCallback(self, interaction: Interaction):
#                 values = self.select.values
#                 if values == []:
#                     return
                
#                 value = values[0]
                
#                 self.outer.mode = value
                
#                 await self.outer.setup(interaction)
            
#         async def callback(self, interaction: Interaction):
#             await self.MultiOrSingleSelectView(self.outer).setup(interaction)
       
#     async def load(self, interaction: Interaction):
#         self.message = await interaction.channel.fetch_message(self.messageID)
#         self.server = Server_DEP(interaction.guild.id)
#         self.messageInfo = self.server.messages.get(self.messageID)
        
#         if self.title == None and self.description == None and self.color == None and self.options == []:
#             self.title = self.message.embeds[0].title
#             self.description = self.message.embeds[0].description
#             self.color = self.message.embeds[0].color
            
#             # Get options
#             self.options = []
#             for field in self.message.embeds[0].fields:
#                 name = field.name
#                 description = "\n".join(field.value.split("\n")[:-1])
#                 roles = self.extract_ids(field.value.split("\n")[-1])
#                 self.options.append([roles, name, description])
                
                
#             # Get Mode
#             self.mode = "Multiple"
#             for component in self.message.components:
#                 if isinstance(component, nextcord.components.ActionRow):
#                     for item in component.children:
#                         if isinstance(item, nextcord.components.Button):
#                             if item.custom_id == "get_roles":
#                                 self.mode = "Multiple"
#                                 break
#                             elif item.custom_id == "get_role":
#                                 self.mode = "Single"
#                                 break
#             self.currentMode = self.mode
            
#         self.clear_items()
            
#         # Load buttons   
#         editTextBtn = self.EditTextButton(self)
#         self.add_item(editTextBtn)
        
#         editColorBtn = self.EditColorButton(self)
#         self.add_item(editColorBtn)
        
#         self.addBtn = self.AddBtn(self, self.options)
#         self.add_item(self.addBtn)
        
#         self.editBtn = self.EditBtn(self, self.options)
#         self.add_item(self.editBtn)
        
#         self.removeBtn = self.RemoveBtn(self, self.options)
#         self.add_item(self.removeBtn)
        
#         editModeBtn = self.EditModeBtn(self)
#         self.add_item(editModeBtn)
        
#         self.confirmBtn = nextcord.ui.Button(label = "Confirm Edits", style = nextcord.ButtonStyle.blurple, row = 1)
#         self.confirmBtn.callback = self.confirmBtnCallback
#         self.add_item(self.confirmBtn)
        
#     async def setup(self, interaction: Interaction):
#         await self.load(interaction)
        
#         embed = nextcord.Embed(title = "Edit Role Message", description = "Edit your role message by making to the text, color, and options. Once finished, click on \"Confirm Edits\"", color = nextcord.Color.yellow())
        
#         # Create a mockup of the embed
#         roleMessageEmbed = self.createEmbed(self.title, self.description, self.color, self.options)
        
#         embeds = [embed, roleMessageEmbed]
        
#         # Give warning about mode if needed
#         if self.mode != self.currentMode:
#             warningEmbed = nextcord.Embed(title = "Warning: Mode Not Saved", description = "Be sure to Confirm Edits to save your mode.", color = nextcord.Color.red())
#             embeds.append(warningEmbed)
        
#         await interaction.response.edit_message(embeds = embeds, view = self)
        
#     def createEmbed(self, title, description, color, options):
#         embed = nextcord.Embed(title = title, description = description, color = color)
#         for option in options:
#             self.addField(embed, option)

#         return embed
            
#     def addField(self, embed: nextcord.Embed, optionInfo):
#         mentions = [f"<@&{role}>" for role in optionInfo[0]]
#         if len(mentions) > 1:
#             mentions[-1] = f"and {mentions[-1]}"
#         roles = ", ".join(mentions)
            
#         title = optionInfo[1]
#         description = optionInfo[2]
        
#         spacer = ("\n" if description != "" else "")
        
#         embed.add_field(name = title, value = f"{description}{spacer}> Grants {roles}", inline = False)
    
#     def extract_ids(self, input_string):
#         pattern = r"<@&(\d+)>"
#         matches = re.findall(pattern, input_string)
#         return matches
    
#     async def disableView(self, interaction: Interaction):
#         for child in self.children:
#             if isinstance(child, nextcord.ui.Button):
#                 child.disabled = True
                
#         await interaction.response.edit_message(view = self, delete_after = 1.0)
    
#     async def confirmBtnCallback(self, interaction: Interaction):
#         roleMessageEmbed = self.createEmbed(self.title, self.description, self.color, self.options)
        
#         await self.disableView(interaction)
        
#         if self.mode == "Single":
#             view = RoleMessageButton_Single()
#         else:
#             view = RoleMessageButton_Multiple()
        
#         await self.message.edit(embed = roleMessageEmbed, view = view)
                            
#     async def callback(self, interaction: Interaction):
#         await self.RoleSelectWizardView(self.titleInput.value, self.descriptionInput.value).setup(interaction)
