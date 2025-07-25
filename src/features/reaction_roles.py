import re
import nextcord
from nextcord import Interaction
import logging
import json

from config.server import Server
from components import ui_components, utils 

class ReactionRoleModal(ui_components.CustomModal):
    def __init__(self):
        super().__init__(title = "Create a Reaction Role")
        
        self.title_value = None
        self.description_value = None
        
        self.title_text_input = nextcord.ui.TextInput(label="Title", style=nextcord.TextInputStyle.short, placeholder="Get access to the server", required=True)
        self.description_text_input = nextcord.ui.TextInput(label="Description", style=nextcord.TextInputStyle.paragraph, max_length=4000,
                                                            placeholder="Grab your roles below:", required=False)
        
        self.add_item(self.title_text_input)
        self.add_item(self.description_text_input)

    async def callback(self, interaction: Interaction):
        self.title_value = self.title_text_input.value
        self.description_value = self.description_text_input.value
        self.stop()

class ReactionRoleView(ui_components.CustomView):
    def __init__(self, roles: list[nextcord.Role]):
        super().__init__()

        options = []
        # In case there are more than 25 roles, do this in reverse. Ensure that at least the lowest roles appear here, if nothing else.
        roles.reverse()
        for role in roles:
            if len(options) >= 25:
                # Discord has a limit of 25 options. Can't add any more.
                break
            else:
                options.append(nextcord.SelectOption(label=role.name, value=role.name))
            
        self.selection = []
        
        if len(options) < 10:
            max_values = len(options)
        else:
            max_values = 10
        
        self.select = nextcord.ui.Select(placeholder="Select Up to 10 Roles", options=options, max_values=max_values)
        
        self.button = nextcord.ui.Button(label="Create", style=nextcord.ButtonStyle.blurple)
        self.button.callback = self.create_callback
        
        self.add_item(self.select)
        self.add_item(self.button)
             
    async def create_callback(self, interaction: Interaction):
        self.selection = self.select.values
        if self.selection == []: return
        if self.selection == None: return
        
        # Disable the buttons now
        self.select.disabled = True
        self.button.disabled = True

        # Edit the message to show the disabled buttons, with autodelete on
        await interaction.response.edit_message(view=self, delete_after=1.0)
        self.stop()

REACTION_ROLES_DISABLED_MESSAGE = nextcord.Embed(title="Reaction Roles Disabled", description="Reaction Roles have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color=nextcord.Color.red())
MISSING_PERMISSIONS_MESSAGE = nextcord.Embed(title="InfiniBot Missing Permissions", description="InfiniBot needs the \"Manage Roles\" permission in order to use this command. Grant InfiniBot this permission and try again.\n\nFor more information: [Check our documentation](https://cypress-exe.github.io/InfiniBot/docs/roles/reaction-roles/)", color=nextcord.Color.red())

REACTIONROLETYPES = ["Letters", "Numbers", "Custom"]
async def run_reaction_role_command(interaction: Interaction, type: str, mention_roles: bool):
    if not await utils.user_has_config_permissions(interaction):
        return
    
    if not utils.feature_is_active(guild = interaction.guild, feature = "reaction_roles"):
        await interaction.response.send_message(embed=REACTION_ROLES_DISABLED_MESSAGE, ephemeral=True)
        return
    
    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message(embed=MISSING_PERMISSIONS_MESSAGE, ephemeral=True)
        return
    
    # Send Modal
    modal = ReactionRoleModal()
        
    await interaction.response.send_modal(modal)
    await modal.wait()
    
    # Proccess Modal
    reaction_role_title = modal.title_value
    reaction_role_description = modal.description_value
    
    # Prepare Selection
    roles_allowed = []
    
    for role in interaction.guild.roles:
        if role.name == "@everyone": continue
        if utils.role_assignable_by_infinibot(role): roles_allowed.append(role)
        
    if len(roles_allowed) == 0:
        description = """
        InfiniBot can't find any roles that it is able to assign. Make sure that your server has roles and that InfiniBot is the highest role on the server.
        """
        description = utils.standardize_str_indention(description)
        await interaction.followup.send(embed=nextcord.Embed(title="No Roles", description=description, color=nextcord.Color.red()), ephemeral=True)
        return
                
    # Send Selection View
    view = ReactionRoleView(roles_allowed)
    description = """
    **Don't see your role?**
    If a role is equal to or higher than InfiniBot's highest role, InfiniBot cannot grant that role to anyone. Fix this by making InfiniBot the highest role on the server.
    
    For more information on reaction roles: [Check our documentation](https://cypress-exe.github.io/InfiniBot/docs/roles/reaction-roles/)
    """
    description = utils.standardize_str_indention(description)
    await interaction.followup.send(embed=nextcord.Embed(title="Choose the roles you would like to include.", description=description, color=nextcord.Color.blurple()), view=view, ephemeral=True)

    await view.wait()
    
    # Finish Proccessing...
    await create_reaction_role(interaction, reaction_role_title, reaction_role_description, view.selection, type, mention_roles)
    
async def run_custom_reaction_role_command(interaction: Interaction, options: str, mention_roles: bool):
    if await utils.user_has_config_permissions(interaction):
        if not utils.feature_is_active(guild = interaction.guild, feature = "reaction_roles"):
            await interaction.response.send_message(embed = REACTION_ROLES_DISABLED_MESSAGE, ephemeral=True)
            return
        
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(embed = MISSING_PERMISSIONS_MESSAGE, ephemeral=True)
            return
        
        options_split = [option.strip() for option in options.split(",")]
        
        if len(options_split) > 10:
            await interaction.followup.send(embed = nextcord.Embed(title="Too Many Arguments", description="You can't have more than 10 role options.", color=nextcord.Color.red()), ephemeral=True)
            return
        
        emojis = []
        role_IDs = []
        for option in options_split:
            try:
                if len(option.split("=")) < 2:
                    raise Exception # Trigger the error message at end of try block
                
                emoji = option.split("=")[0].strip()
                if emoji in emojis:
                    await interaction.response.send_message(embed = nextcord.Embed(title="Error: You can't use the same emoji twice", 
                                                                                   description="Every emoji has to be unique.", color=nextcord.Color.red()), ephemeral=True)
                    return
                
                role_ID = int(option.split("=")[1][4:-1].strip())
                role = [role for role in interaction.guild.roles if role.id == role_ID][0]
                if role_ID in role_IDs:
                    await interaction.response.send_message(embed = nextcord.Embed(title="Error: You can't use the same role twice", description="Every role has to be unique.", 
                                                                                   color=nextcord.Color.red()), ephemeral=True)
                    return
                if not role_ID in [role.id for role in interaction.guild.roles]:
                    await interaction.response.send_message(embed = nextcord.Embed(title="Error: Role Doesn't Exist", description=f"The role \"{role.name}\" doesn't exist.", 
                                                                                   color=nextcord.Color.red()), ephemeral=True)
                    return
                if not utils.role_assignable_by_infinibot(role):
                    await interaction.response.send_message(embed = nextcord.Embed(title="Error: Missing Permissions", 
                                                                                   description=f"Infinibot does not have a high enough role to assign/remove {role.mention}. To fix this, promote the role \"Infinibot\" to the highest role on the server or give InfiniBot Administrator.", 
                                                                                   color=nextcord.Color.red()))
                
                emojis.append(emoji)
                role_IDs.append(role.id)
                
            except Exception:
                description = utils.standardize_str_indention("""
                \"Options\" needs to be formatted like this:
                                                                
                `Emoji = @Role, Emoji = @Role, Emoji = @Role, Etc`                  
                `👍 = @Member, 🥸 = @Gamer`
                
                For more information: [Check our documentation](https://cypress-exe.github.io/InfiniBot/docs/roles/reaction-roles/)
                """)
                await interaction.response.send_message(embed = nextcord.Embed(title="Woops... You Formatted that Wrong", description=description, 
                                                                                color=nextcord.Color.red()), ephemeral=True)
                return
        
        modal = ReactionRoleModal()
        await interaction.response.send_modal(modal)
        
        await modal.wait()
        
        await create_reaction_role(interaction, modal.title_value, modal.description_value, [option.strip() for option in options.split(",")], "Custom", mention_roles)

def reaction_role_options_formatter(_type: str, roles: list[nextcord.Role], emojis: list[str], mention_roles: bool):
    reactions_formatted = "" # Returned
    added_options__emojis = [] # Returned
    added_options__asci = []
    
    count = 1
    for role in roles:
        if _type == "Letters":
            if not role.name[0].lower() in added_options__asci: #if we have not already used this reaction
                letter = role.name[0]
                reaction, letter_used = utils.asci_to_emoji(letter, fallback_letter = utils.get_next_open_letter(added_options__asci))
                reactions_formatted += "\n" + reaction + " " + (role.mention if mention_roles else role.name)
                added_options__asci.append(letter_used.lower())
                added_options__emojis.append(reaction)
            else:
                letter = utils.get_next_open_letter(added_options__asci)
                reaction, letter_used = utils.asci_to_emoji(letter)
                reactions_formatted += "\n" + reaction + " " + (role.mention if mention_roles else role.name)
                added_options__asci.append(letter_used.lower())
                added_options__emojis.append(reaction)
        elif _type == "Numbers":
            letter = role.name[0]
            reaction, letter_used = utils.asci_to_emoji(count)
            reactions_formatted += "\n" + reaction + " " + (role.mention if mention_roles else role.name)
            added_options__asci.append(letter_used.lower())
            added_options__emojis.append(reaction)
            count += 1
        else:
            index = roles.index(role)
            emoji = emojis[index].strip()
            reactions_formatted += "\n" + emoji + " " + (role.mention if mention_roles else role.name)
            added_options__emojis.append(emoji)
            
    return reactions_formatted, added_options__emojis

async def create_reaction_role(interaction: Interaction, title: str, message: str, roles_str: list[str], _type: str, mention_roles: bool):
    if not interaction.guild or interaction.guild == None: 
        logging.error("interaction.guild is equal to None. Unexpected behavior.")
        return

    # Check for Manage Roles permission
    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.followup.send(embed=MISSING_PERMISSIONS_MESSAGE, ephemeral=True)
        return
      
    # Decode roles and emojis
    if _type != "Custom":
        roles: list[nextcord.Role] = [role for role_name in roles_str for role in interaction.guild.roles if role.name == role_name]
        emojis = None
    else:
        new_roles_str = [int(role.split("=")[1][4:-1].strip()) for role in roles_str]
        roles: list[nextcord.Role] = [role for role_ID in new_roles_str for role in interaction.guild.roles if role.id == role_ID]
        emojis: list[str] = [emoji.split("=")[0] for emoji in roles_str]
    
    # Ensure that these roles are grantable
    for role in roles:
        if role.position >= interaction.guild.me.top_role.position:
            infinibot_role = utils.get_infinibot_top_role(interaction.guild)
            await interaction.followup.send(embed = nextcord.Embed(title="Infinibot cannot grant a permission", 
                                                                   description=f"{role.mention} is equal to or above the role {infinibot_role.mention}. Therefore, it cannot grant the role to any member.", 
                                                                   color=nextcord.Color.red()), ephemeral=True)
            return
    
    # Ensure that at least one role is selected
    if len(roles) == 0:
        await interaction.followup.send(embed=nextcord.Embed(title="No Roles", description="You need to have at least one role.\n\nFor more information: [Check our documentation](https://cypress-exe.github.io/InfiniBot/docs/roles/reaction-roles/)", color=nextcord.Color.red()), ephemeral=True)
        return
    
    # Format the options
    options_formatted, added_reactions__emojis = reaction_role_options_formatter(_type, roles, emojis, mention_roles)

    # Post message
    embed = nextcord.Embed(title=title, description=message, color=nextcord.Color.teal())
    embed = utils.apply_generic_replacements(embed, None, interaction.guild)
    embed.add_field(name = "React for the following roles", value=options_formatted, inline=False)

    partial_message = await interaction.followup.send(embed=embed, wait=True)

    # Add Reactions
    reaction_role_message = partial_message
    for reaction in added_reactions__emojis:
        try:
            await reaction_role_message.add_reaction(emoji = reaction)
        except (nextcord.errors.Forbidden, nextcord.errors.HTTPException):
            try:
                await interaction.followup.send(
                    embed=nextcord.Embed(
                        title="Emoji Error",
                        description=(
                            f"InfiniBot is unable to apply the emoji: {reaction}. "
                            f"If the emoji *is* valid, check that InfiniBot has the permission \"Add Reactions\".\n\n"
                            f"Alternatively, if the emoji is an external emoji, InfiniBot can't use it. "
                            f"Be sure to add it to the server's emojis for InfiniBot to use it."
                        ),
                        color=nextcord.Color.red()
                    )
                )
            except nextcord.errors.Forbidden:
                await utils.send_error_message_to_server_owner(interaction.guild, "Add Reactions")
            break
    
    # Add the Reaction Role to Active Messages for Future Editing
    server = Server(interaction.guild.id)
    data = {
        "v": 1, # Version
        "type": REACTIONROLETYPES.index(_type),
        "mention_roles": (1 if mention_roles else 0),
    }
    server.managed_messages.add(
        message_id = partial_message.id,
        channel_id = interaction.channel.id,
        author_id = interaction.user.id,
        message_type = "reaction_role",
        json_data = json.dumps(data)
    )
    
async def run_raw_reaction_add(payload: nextcord.RawReactionActionEvent, bot: nextcord.Client):
    emoji = payload.emoji

    # Commented out. Here's why:
    #
    #    Back when InfiniBot started, reaction roles were not necessarily stored in the database indefinitely.
    #    All modern reaction roles are stored, but uncommenting this block of code would break the really old
    #    reaction roles that were created before database storage was implemented. It's unfortunate, because 
    #    it would be nice to have this check, but it's not worth breaking old reaction roles.
    #
    # <code>
    # # Check if the message is a reaction role message
    # server = Server(payload.guild_id)
    # if not payload.message_id in server.managed_messages:
    #     logging.debug(f"Reaction role message not found for message ID {payload.message_id} in guild {payload.guild_id}. Ignoring reaction.")
    #     return
    # </code>

    # Get the guild
    guild = None
    for _guild in bot.guilds:
        if _guild.id == payload.guild_id:
            guild = _guild
    if guild == None: return

    if not guild.chunked:
        await guild.chunk()

    if not guild.me:
        return

    # Get the user
    user = await utils.get_member(guild, payload.user_id)
    if user is None:
        # If the user is not in the server, we can't do anything
        logging.warning(f"User {payload.user_id} not found in guild {guild.id}. Ignoring reaction.")
        return

    # Get the message
    channel = await utils.get_channel(payload.channel_id)
    if channel is None: 
        return  # If the channel doesn't exist, we can't do anything
    message = await utils.get_message(channel, payload.message_id)
    if message is None: 
        return  # Message doesn't exist or was recently not found

    # Declare some functions
    def get_role(string: str):
        pattern = r"^(<@&)(.*)>$"  # Regular expression pattern with a capturing group
        match = re.search(pattern, string)
        if match:
            role_id = int(match.group(2)) # Role ID
            role = nextcord.utils.get(guild.roles, id=role_id)
        else:
            role = nextcord.utils.get(guild.roles, name=string)
        return role
    
    async def send_no_role_error():
        await message.channel.send(embed = nextcord.Embed(title="Role Not Found", description=f"Infinibot cannot find one or more of those roles. Check to make sure all roles still exist.", color=nextcord.Color.red()), reference=message)
    
    async def send_no_permissions_error(role: nextcord.Role, user: nextcord.Member):
        try:
            await message.channel.send(embed = nextcord.Embed(title="Missing Permissions", description=f"Infinibot does not have a high enough role to assign/remove {role.mention} to/from {user.mention}. To fix this, promote the role \"Infinibot\" to the highest role on the server or give InfiniBot administrator privileges.", color=nextcord.Color.red()), reference=message)
        except nextcord.errors.Forbidden:
            await utils.send_error_message_to_server_owner(guild, None, message=f"Infinibot does not have a high enough role to assign/remove {role.name} (id: {role.id}) to/from {user} (id: {user.id}). To fix this, promote the role \"Infinibot\" to the highest role on the server or give InfiniBot administrator privileges.")

    action = None

    # If it was our message and it was not a bot reacting,
    if message.author.id == bot.application_id and not user.bot:
        if message.embeds:
            # Check to see if this is actually a reaction role
            if len(message.embeds[0].fields) >= 1 and message.embeds[0].fields[0].name.lower().startswith("react"): # This message IS a reaction role
                # Get all options
                info = message.embeds[0].fields[0].value
                info = info.split("\n")
                
                # For each option
                for line in info:
                    line_split = line.split(" ")
                    if str(line_split[0]) == str(emoji): # Ensure that this is a real option
                        # Get the discord role
                        discord_role = get_role(" ".join(line_split[1:]))
                        if discord_role: # If it exists
                            # Check the user's roles
                            user_role = nextcord.utils.get(user.roles, id=discord_role.id)
                            # Give / Take the role
                            try:
                                if user_role:
                                    await user.remove_roles(discord_role)
                                    action = "removed"
                                else:
                                    await user.add_roles(discord_role)
                                    action = "added"
                            except nextcord.errors.Forbidden:
                                # No permissions. Send an error
                                await send_no_permissions_error(discord_role, user)
                            
                            # Remove their reaction
                            await message.remove_reaction(emoji, user)
                        else:
                            # If the discord role does not exist, send an error
                            await send_no_role_error()
                            # Try to remove their reaction. If we can't, it's fine
                            try:
                                await message.remove_reaction(emoji, user)
                            except nextcord.errors.Forbidden:
                                pass
                            return
    
    # Send embed notifying the user of the action
    if action:
        embed = nextcord.Embed(
            title = "🔄  Role Updated",
            description = f"Your roles have been updated in **{guild.name}**",
            color = nextcord.Color.green() if action == "added" else nextcord.Color.orange()
        )

        if action == "added":
            embed.add_field(
                name = "✅  Role Added", 
                value = f"You now have the **{discord_role.name}** role.", 
                inline=False
            )
        elif action == "removed":
            embed.add_field(
                name = "❌  Role Removed", 
                value = f"The **{discord_role.name}** role has been removed from you.", 
                inline=False
            )

        embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
        embed.set_footer(text="Your reaction was automatically removed by InfiniBot. React again to toggle this role.")

        view = ui_components.CustomView()
        view.add_item(nextcord.ui.Button(
            label="Go to Reaction Role",
            style=nextcord.ButtonStyle.link,
            url=f"https://discord.com/channels/{guild.id}/{message.channel.id}/{message.id}"
        ))

        # Note: This DM does not respect the user's DM settings. This is because the user has explicitly
        # interacted with the bot, so in this case, their settings are overridden.
        try:
            await user.send(embed=embed, view=view)
        except (nextcord.errors.Forbidden, nextcord.errors.HTTPException):
            # If the user has DMs disabled, we can't send them a message.
            return
