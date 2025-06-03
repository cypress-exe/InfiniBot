import nextcord

from config.member import Member

async def check_and_run_dm_commands(bot: nextcord.Client, message: nextcord.Message) -> None:
    """
    |coro|

    Runs a specified command for DMs
    
    :param bot: The bot client
    :type bot: nextcord.Client
    :param message: The message to check
    :type message: nextcord.Message
    :return: None
    :rtype: None
    """
    if message.author.id == bot.application_id: return

    if message.content.lower() == "clear-last": # Clear last message
        async for message in message.channel.history(limit=10):
            if message.author.id == bot.application_id:
                await message.delete()
                break

        embed = nextcord.Embed(title = "Cleared Last Message", description="Last message has been cleared.", color = nextcord.Color.green())
        await message.channel.send(embed = embed, delete_after = 3)

async def run_opt_out_of_dms_command(interaction: nextcord.Interaction) -> None:
    """
    |coro|

    Runs the opt-out of DMs command
    
    :param interaction: The interaction object
    :type interaction: nextcord.Interaction
    :return: None
    :rtype: None
    """
    
    member = Member(interaction.user.id)
    
    if not member.direct_messages_enabled: 
        embed = nextcord.Embed(
            title="Already opted out of DMs", 
            description="You are already opted out of dms.", 
            color=nextcord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    member.direct_messages_enabled = False
    
    embed = nextcord.Embed(
        title="Opted Out of DMs", 
        description=f"You opted out of DMs from InfiniBot. You will no longer recieve permission errors, birthday updates, or strike notices. To re-opt-into this feature, use `/opt-into-dms`", 
        color=nextcord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

async def run_opt_into_dms_command(interaction: nextcord.Interaction) -> None:
    """
    |coro|

    Runs the opt-into DMs command
    
    :param interaction: The interaction object
    :type interaction: nextcord.Interaction
    :return: None
    :rtype: None
    """
    
    member = Member(interaction.user.id)
    
    if member.direct_messages_enabled: 
        embed = nextcord.Embed(
            title="Already opted into DMs", 
            description="You are already opted into dms.", 
            color=nextcord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    member.direct_messages_enabled = True
    
    embed = nextcord.Embed(
        title="Opted Into DMs", 
        description=f"You opted into DMs from InfiniBot. You will now recieve permission errors, birthday updates, and strike notices. To re-opt-out of this feature, use `/opt-out-of-dms`", 
        color=nextcord.Color.green()
    )
    await interaction.response.send_message(embed=embed)