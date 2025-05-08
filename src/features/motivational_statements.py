from nextcord import Interaction
import nextcord
import random

from components import utils


async def run_motivational_statement(interaction: Interaction):
    if not utils.feature_is_active(guild_id=interaction.guild.id, feature="motivational_statements"):
        embed = nextcord.Embed(
            title="Motivational Statements Disabled",
            description="Motivational Statements have been disabled by the developers of InfiniBot. \
            This is likely due to an critical instability with it right now. It will be re-enabled \
            shortly after the issue has been resolved.",
            color=nextcord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    messages = [
        "Don't stress over something today; it will be worse tomorrow.",
        "Time to leave the past behind and start over in life; your existence didn't mean anything anyway.",
        "If you think life is horrible right now, you're wrong. It will always get worse count on it.",
        "Keep working. Though you will never find success, your family might remember your meaningless life.",
        "If you fail to find success over and over, give up. You're not good enough to do it anyway, and you never will be.",
        "The cookies you were looking foreward to all day burned to a crisp.",
        "Are others really talking about you behind your back? Yes. Yes they are.",
        "You lie awake at night thinking about how much of a disapointment you are."
    ]

    embed = nextcord.Embed(
        title="Motivational Statement",
        description=messages[random.randint(0, len(messages) - 1)],
        color=nextcord.Color.blue()
    )
    embed.set_footer(text="Disclaimer: This is obviously not real motivational advice. For real advice, seek the help of a licenced professional.")

    await interaction.response.send_message(embed=embed)
