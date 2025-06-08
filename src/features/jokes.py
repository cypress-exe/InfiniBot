from nextcord import Interaction
import nextcord
import random
import json
import logging

from components import utils, ui_components
from components.ui_components import CustomModal, CustomView
from config.global_settings import get_configs
from config.member import Member

class Joke:
    def __init__(self, title, body, punchline):
        """
        Initialize a new Joke instance.

        :param title: The short, descriptive title of the joke
        :type title: str
        :param body: The main text of the joke
        :type body: str
        :param punchline: The punchline of the joke, or None if there is no punchline
        :type punchline: str or None
        :raises ValueError: If required parameters are missing or invalid
        """
        
        if not title or not body:
            raise ValueError("Title and body cannot be empty.")
        
        vars = [title, body, punchline]
        if any((not isinstance(var, str) and var is not None) for var in vars):
            raise ValueError("Title, body, and punchline must be strings.")

        self.title = title
        self.body = body
        self.punchline = punchline if punchline else None

    def __str__(self):        
        return f"Joke({', '.join(f'{k}={v}' for k, v in self.to_dict().items())})"
    
    def to_dict(self):
        """
        Converts the Joke instance into a dictionary.

        :return: A dictionary containing the joke title, body, and optional punchline
        :rtype: dict
        """
        values = {}
        for attr in ["title", "body", "punchline"]:
            value = getattr(self, attr)
            if value is not None:
                values[attr] = value

        return values
    
    def __dict__(self):
        return self.to_dict()
    
    def __hash__(self):
        return hash((self.title, self.body, self.punchline))
    
    def __eq__(self, value):
        if not isinstance(value, Joke):
            return False
        
        return (
            self.title == value.title and
            self.body == value.body and
            self.punchline == value.punchline
        )

class JokeManager:
    def __init__(self, file_path="generated/files/jokes.json"):
        """
        Inits the JokeManager with a path to the JSON file storing jokes.

        :param file_path: The path to the jokes file
        :type file_path: str
        :return: None
        """
        self.jokes:list[Joke] = []
        self.file_path = file_path

        self.load_jokes()

    def load_jokes(self):
        """
        Loads jokes from the JSON file at self.file_path into the jokes list.

        :param: :none:
        :return: :none:
        :raises Exception: If an error occurs while reading or parsing the JSON file
        """
        logging.debug("Loading jokes...")
        
        # Clear jokes
        self.jokes = []

        try:
            jokes = {}
            with open(self.file_path, "r") as f:
                jokes = json.load(f)

            for joke in jokes["jokes"]:
                self.jokes.append(Joke(
                    title=joke["title"],
                    body=joke["body"],
                    punchline=joke["punchline"] if "punchline" in joke else None
                ))
        except Exception as e:
            logging.error(f"Failed to load jokes: {e}", exc_info=True)
    
    def save_jokes(self):
        """
        Saves the jokes list to the JSON file at the configured path.

        :param: :string: This method does not consume any new string argument.
        :return: :none:
        :raises Exception: If writing to the JSON file fails.
        """
        logging.debug("Saving jokes...")

        if self.jokes is None or len(self.jokes) == 0:
            # Jokes might have gotten corrupted. Don't override all jokes with an empty list.
            logging.error("Tried to save jokes, but jokes was None or empty. Skipping due to safety reasons. Jokes: " + str(self.jokes))
            return
        try:
            with open(self.file_path, "w") as f:
                json.dump({"jokes": [joke.to_dict() for joke in self.jokes]}, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save jokes: {e}", exc_info=True)

    def add_joke(self, joke:Joke):
        """
        This snippet checks for duplicate jokes, logs the addition, and appends the joke to the manager.

        :param joke: The Joke object to be added
        :return: None  
        """
        if joke in self.jokes:
            logging.warning("Joke already exists. Skipping.")
            return
        
        logging.info(f"Adding joke: {joke}")
        self.jokes.append(joke)

        self.save_jokes()


def _get_infinibot_support_server():
    """
    Retrieves the InfiniBot support server guild object.
    
    :return: The Discord guild object for the InfiniBot support server, or None if not found or inaccessible
    :rtype: nextcord.Guild or None
    """
    from core.bot import get_bot

    bot = get_bot()

    infinibot_guild_id = get_configs()['support-server']['support-server-id']

    try:
        if guild := bot.get_guild(infinibot_guild_id):
            return guild
    except nextcord.errors.Forbidden:
        # This means the bot doesn't have access to the server
        # This is likely due to the bot being removed from the server
        # or the bot being banned from the server
        pass
            
    logging.error("ERROR: CANNOT FIND INFINIBOT SERVER!!!")
    return None

def _format_joke_submission_embed(joke: Joke, member: nextcord.Member, supplementary_info=None):
    """
    Formats a Nextcord Embed object for a joke submission, including member and server information.
    
    :param joke: The joke object containing the title, body, and optional punchline
    :type joke: Joke
    :param member: The Discord member who submitted the joke. Can be None if supplementary_info is provided
    :type member: nextcord.Member
    :param supplementary_info: A dictionary containing fallback information such as 'member', 'member_id', 'server', and 'server_id' if the member object is not available
    :type supplementary_info: dict, optional
    :return: An embed object representing the joke submission, including member/server details and joke content
    :rtype: nextcord.Embed
    :raises ValueError: If neither member nor supplementary_info is provided, indicating insufficient information to format the embed
    """
    if not supplementary_info and not member:
        logging.error("Cannot format joke submission embed without member or supplementary info.")
        raise ValueError("Cannot format joke submission embed without member or supplementary info.")
    
    def safe_get(obj, attr, fallback_obj, fallback_attr):
        """
        Safely retrieves an attribute from an object, with optional fallback.
        
        :param obj: The primary object to retrieve the attribute from.
        :param attr: The name of the attribute to retrieve from `obj`. If None, `obj` itself is returned.
        :type attr: str or None
        :param fallback_obj: The fallback object to retrieve the fallback attribute from if the primary value is None.
        :param fallback_attr: The name of the attribute to retrieve from `fallback_obj` if the primary value is None.
        :type fallback_attr: str
        :return: The value of `obj.attr` if it exists and is not None; otherwise, the value of `fallback_obj.fallback_attr` if provided; otherwise, None.
        """
        
        value = None
        
        # Get value from primary object
        if obj:
            if attr is not None:
                value = getattr(obj, attr)
            else:
                value = obj
    
        # Use fallback if value is None and both fallback parameters are provided
        if value is None:
            return fallback_obj[fallback_attr]
    
        return value
    
    guild = member.guild if member else None
        
    embed = nextcord.Embed(
        title="New Joke Submission:",
        description=(
            f"Member: {safe_get(member, None, supplementary_info, 'member')}\n"
            f"Member ID: {safe_get(member, 'id', supplementary_info, 'member_id')}\n"
            f"Server: {safe_get(guild, None, supplementary_info, 'server')}\n"
            f"Server ID: {safe_get(guild, 'id', supplementary_info, 'server_id')}\n"
        ),
        color=nextcord.Color.dark_green()
    )
    embed.add_field(name="Title", value=joke.title)
    embed.add_field(name="Joke", value=joke.body)
    if joke.punchline: embed.add_field(name="Punchline", value=joke.punchline)

    return embed


def _extract_info_from_joke_submission_embed(embed: nextcord.Embed):
    """
    Extracts joke information and supplementary data from a joke submission embed.
    
    :param embed: The Discord embed containing the joke submission information
    :type embed: nextcord.Embed
    :return: A tuple containing the extracted Joke object and a dictionary of supplementary information (member_id, server_id, member, server)
    :rtype: tuple[Joke, dict]
    """
    title = None
    body = None
    punchline = None

    for field in embed.fields:
        if field.name == "Title":
            title = field.value
        elif field.name == "Joke" or field.name == "Body":
            body = field.value
        elif field.name == "Punchline":
            punchline = field.value

    joke = Joke(
        title=title,
        body=body,
        punchline=punchline
    )

    objects_to_extract = {
        "Member ID:": "member_id",
        "Server ID:": "server_id",
        "Member:": "member",
        "Server:": "server"
    }

    extracted_values = {}
    for key in objects_to_extract:
        if key in embed.description:
            value = embed.description.split(key)[1].split("\n")[0].strip()
            extracted_values[objects_to_extract[key]] = value

    return joke, extracted_values

def _get_member_in_support_server(member_id: int):
    """
    Retrieves a Discord member from the InfiniBot support server by their ID.
    
    :param member_id: The Discord user ID to search for in the support server
    :type member_id: int
    :return: The Discord member object if found in the support server, or None if not found or server inaccessible
    :rtype: nextcord.Member or None
    """
    if isinstance(member_id, str) and not member_id.isdigit():
        logging.error(f"Member ID is not a digit: {member_id}")
        return None

    support_server = _get_infinibot_support_server()
    if not support_server: return None

    return support_server.get_member(int(member_id))

class JokeView(CustomView):
    def __init__(self):
        super().__init__(timeout=None)

        if utils.feature_is_active(feature="joke_submissions"):
            self.button = nextcord.ui.Button(
                label="Submit a Joke",
                custom_id="submit_a_joke"
            )
            self.button.callback = self.submit_joke_callback
            self.add_item(self.button)

    class SubmitJokeModal(CustomModal):
        def __init__(self):
            super().__init__(title="Submit a Joke", timeout=None)

            self.joke_title = nextcord.ui.TextInput(
                label="Title",
                placeholder="The Chicken and the Road",
                max_length=100
            )
            self.add_item(self.joke_title)

            self.joke_body = nextcord.ui.TextInput(
                label="Joke",
                placeholder="Why did the chicken cross the road?",
                style=nextcord.TextInputStyle.paragraph,
                max_length=500
            )
            self.add_item(self.joke_body)

            self.joke_punchline = nextcord.ui.TextInput(
                label="Punchline",
                placeholder="To get to the other side! (Optional. Leave blank if not applicable)",
                style=nextcord.TextInputStyle.paragraph,
                max_length=500,
                required=False
            )
            self.add_item(self.joke_punchline)

        async def callback(self, interaction: Interaction):
            # Try to post a message to the submission channel on the InfiniBot Support Server
            server = _get_infinibot_support_server()
            if server is None: self.stop()

            # Get the submission channel ID
            submission_channel_id = get_configs()['support-server']['submission-channel-id']
            if submission_channel_id is None or submission_channel_id == 0:
                logging.error("Joke submission channel ID is None. Cannot send joke submission.")
                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="Joke Submission Failed",
                        description=(
                            "Joke submission channel ID is None. "
                            "Please contact the developers of InfiniBot to fix this issue."
                        ),
                        color=nextcord.Color.red()
                    ),
                    ephemeral=True
                )

            embed = _format_joke_submission_embed(
                Joke(
                    title=self.joke_title.value,
                    body=self.joke_body.value,
                    punchline=self.joke_punchline.value
                ),
                interaction.user
            )

            channel = server.get_channel(submission_channel_id)
            await channel.send(embed=embed, view=JokeVerificationView())

            # Inform the user that it was sent
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Submission Sent",
                    description=(
                        "Your submission was sent! Join our support server, and we'll dm you regarding your submission's status."
                    ),
                    color=nextcord.Color.green()
                ),
                ephemeral=True,
                view=ui_components.SupportView()
            )

    async def submit_joke_callback(self, interaction: Interaction):
        if not utils.feature_is_active(feature="joke_submissions"):
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="Joke Submissions Disabled",
                    description=(
                        "Joke Submissions have been disabled by the developers of InfiniBot. "
                        "This is likely due to an critical instability with it right now. "
                        "It will be re-enabled shortly after the issue has been resolved."
                    ),
                    color=nextcord.Color.red()
                ),
                ephemeral=True
            )
            return

        await interaction.response.send_modal(self.SubmitJokeModal())

class JokeVerificationView(CustomView):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label="Deny", custom_id="deny_joke")
    async def deny(self, button: nextcord.ui.Button, interaction: Interaction):
        class Modal(CustomModal):
            def __init__(self, message: nextcord.Message):
                super().__init__(title="Reason to Deny", timeout=None)
                self.message = message
                
                # Get the member ID
                _, extraction_info = _extract_info_from_joke_submission_embed(message.embeds[0])
                self.member_id = extraction_info["member_id"]

                # Get the member
                member = _get_member_in_support_server(self.member_id)

                self.reason = nextcord.ui.TextInput(
                    label=f"Reason. {"WARNING: WILL SEND TO THE SUBMITTER" if member else ""}",
                    placeholder="Your joke submission was denied because...",
                    default_value="Your joke submission was denied because ",
                    style=nextcord.TextInputStyle.paragraph
                )
                self.add_item(self.reason)

            async def callback(self, interaction: Interaction):
                reason = self.reason.value

                class ConfirmView(CustomView):
                    def __init__(self, message: nextcord.Message, reason: str, member: nextcord.Member | None):
                        super().__init__(timeout=None)
                        self.message = message
                        self.reason = reason
                        self.member = member

                    @nextcord.ui.button(label="Cancel")
                    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
                        await interaction.response.edit_message(delete_after=0.0)

                    @nextcord.ui.button(label="Confirm")
                    async def confirm(self, button: nextcord.ui.Button, interaction: Interaction):
                        # Send Confirmation
                        embeds = self.message.embeds
                        embeds.append(
                            nextcord.Embed(
                                title="Submission Denied",
                                description=(
                                    f"{interaction.user} denied this submission.\n\n"
                                    f"Reason: {self.reason}\n\n"
                                    f"Submission owner was {'**not**' if not self.member else ''} sent a dm."
                                ),
                                color=nextcord.Color.red()
                            )
                        )
                        await interaction.response.edit_message(delete_after=0.0)
                        await self.message.edit(embeds=embeds, view=None)

                        # Try to dm
                        if not self.member:
                            return

                        dm = await self.member.create_dm()

                        member_settings = Member(self.member.id)
                        if member_settings.direct_messages_enabled:
                            # Get joke
                            joke, _ = _extract_info_from_joke_submission_embed(self.message.embeds[0])
                            await dm.send(
                                embeds=[
                                    nextcord.Embed(
                                        title="Joke Submission Denied",
                                        description=(
                                            f"Your joke submission has been denied by {interaction.user}. "
                                            "The joke you submitted has been attached below.\n\n"
                                            f"Reason: {self.reason}\n\n"
                                            "If you believe this to be a mistake, contact the moderator in the #support channel of the InfiniBot Support Server."
                                            ),
                                        color=nextcord.Color.red()
                                    ),
                                    _format_joke_embed(joke)
                                ]
                            )

                        # Remove the message
                        await interaction.response.edit_message(delete_after=0.0)

                # Get confirmation that we will be able to dm the user
                more_info = "\n\nThis will **not** send the submitter a dm."
                member = None
                if _get_infinibot_support_server():
                    member = _get_member_in_support_server(self.member_id)
                    if member:
                        # Overwrite the message to say that the user WILL be sent a dm
                        more_info = "\n\nBoth your reason and your username will be sent to the submitter via dm."

                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="Confirm Deny",
                        description=(
                            "Are you sure you want to deny this joke submission? "
                            "This will not be reversable."
                            f"{more_info}"
                        ),
                        color=nextcord.Color.blue()
                    ),
                    ephemeral=True,
                    view=ConfirmView(self.message, reason, member)
                )

        modal = Modal(interaction.message)
        await interaction.response.send_modal(modal)

    @nextcord.ui.button(label="Verify", custom_id="verify_joke")
    async def verify(self, button: nextcord.ui.Button, interaction: Interaction):
        class Modal(CustomModal):
            def __init__(self, message: nextcord.Message):
                super().__init__(title="Finalize Joke", timeout=None)
                self.message = message

                joke, extracted_info = _extract_info_from_joke_submission_embed(message.embeds[0])
                self.member_id = extracted_info["member_id"]

                self.joke_title = nextcord.ui.TextInput(
                    label="Title",
                    placeholder="The Chicken and the Road",
                    default_value=joke.title,
                    max_length=100
                )
                self.add_item(self.joke_title)

                self.joke_body = nextcord.ui.TextInput(
                    label="Joke",
                    placeholder="Why did the chicken cross the road?",
                    default_value=joke.body,
                    style=nextcord.TextInputStyle.paragraph,
                    max_length=500
                )
                self.add_item(self.joke_body)

                self.joke_punchline = nextcord.ui.TextInput(
                    label="Punchline",
                    placeholder="To get to the other side! (Optional. Leave blank if not applicable)",
                    default_value=joke.punchline,
                    style=nextcord.TextInputStyle.paragraph,
                    max_length=500,
                    required=False
                )
                self.add_item(self.joke_punchline)

            async def callback(self, interaction: Interaction):
                title = self.joke_title.value
                body = self.joke_body.value
                punchline = self.joke_punchline.value

                class ConfirmView(CustomView):
                    def __init__(
                        self,
                        message: nextcord.Message,
                        joke_title: str,
                        joke_body: str,
                        joke_punchline: str,
                        member_id: int,
                        member: nextcord.Member | None
                    ):
                        super().__init__(timeout=None)
                        self.message = message
                        self.joke_title = joke_title
                        self.joke_body = joke_body
                        self.joke_punchline = joke_punchline
                        self.member_id = member_id
                        self.member = member

                    @nextcord.ui.button(label="Cancel")
                    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
                        await interaction.response.edit_message(delete_after=0.0)

                    @nextcord.ui.button(label="Confirm")
                    async def confirm(self, button: nextcord.ui.Button, interaction: Interaction):
                        
                        joke = Joke(
                            title=self.joke_title,
                            body=self.joke_body,
                            punchline=self.joke_punchline
                        )

                        # Add the joke to jokes.json
                        joke_manager = JokeManager()
                        joke_manager.add_joke(joke)
                        joke_manager.save_jokes()

                        # Retrieve submission info from original message
                        _, extraction_info = _extract_info_from_joke_submission_embed(self.message.embeds[0])

                        # Send Confirmation
                        joke_embed = _format_joke_submission_embed(joke, None, supplementary_info=extraction_info)
                        embeds = [joke_embed]
                        embeds.append(
                            nextcord.Embed(
                                title="Submission Verified",
                                description=(
                                    f"{interaction.user} verified this submission.\n\n"
                                    f"A dm was {'not' if not self.member else ''} sent to the submitter."
                                ),
                                color=nextcord.Color.green()
                            )
                        )
                        await interaction.response.edit_message(delete_after=0.0)
                        await self.message.edit(embeds=embeds, view=None)


                        # Try to dm
                        if not self.member:
                            return

                        dm = await self.member.create_dm()

                        member_settings = Member(self.member.id)
                        if member_settings.direct_messages_enabled:
                            await dm.send(
                                embeds=[
                                    nextcord.Embed(
                                        title="Joke Submission Verified",
                                        description=(
                                            "Your joke submission has been verified! "
                                            "The joke you submitted has been attached below."
                                        ),
                                        color=nextcord.Color.green()
                                    ),
                                    _format_joke_embed(joke)
                                ]
                            )

                # Get confirmation that we will be able to dm the user
                more_info = "This will **not** send the submitter a dm."
                member = None
                if _get_infinibot_support_server():
                    member = _get_member_in_support_server(self.member_id)
                    if member: more_info = "This will send the submitter a dm."

                await interaction.response.send_message(
                    embed=nextcord.Embed(
                        title="Confirm Verify",
                        description=(
                            "Are you sure you want to verify this joke submission (applying any changes you made)? "
                            "This will not be reversable.\n\n"
                            f"{more_info}"
                        ),
                        color=nextcord.Color.blue()
                    ),
                    ephemeral=True,
                    view=ConfirmView(
                        interaction.message,
                        title,
                        body,
                        punchline,
                        self.member_id,
                        member
                    )
                )

        modal = Modal(interaction.message)
        await interaction.response.send_modal(modal)
        

def _format_joke_embed(joke: Joke):
    """
    Formats a Discord embed for displaying a joke with title, body, and optional spoiler-tagged punchline.
    
    :param joke: The joke object to format into an embed
    :type joke: Joke
    :return: A formatted Discord embed containing the joke information
    :rtype: nextcord.Embed
    """
    embed = nextcord.Embed(
        title=joke.title,
        description=(
            f"{joke.body}\n\n"
            f"{f'Reveal Punchline: ||{joke.punchline}||' if joke.punchline else ''}"
        ),
        color=nextcord.Color.magenta()
    )
    return embed

async def run_joke_command(interaction: Interaction):
    """
    Executes the joke command by selecting a random joke and displaying it to the user.
    
    :param interaction: The Discord interaction object containing the command context
    :type interaction: nextcord.Interaction
    :return: Sends a response message directly to the interaction
    :rtype: None
    """
    if not utils.feature_is_active(guild=interaction.guild, feature="jokes"):
        await interaction.response.send_message(
            embed=nextcord.Embed(
                title="Jokes Disabled",
                description=(
                    "Jokes have been disabled by the developers of InfiniBot. "
                    "This is likely due to an critical instability with it right now. "
                    "It will be re-enabled shortly after the issue has been resolved."
                ),
                color=nextcord.Color.red()
            ),
            ephemeral=True
        )
        return
    
    all_jokes = JokeManager().jokes
    
    joke = random.choice(all_jokes)

    if joke is None: 
        logging.error("Joke is None")
        return
    
    embed = _format_joke_embed(joke)
    
    await interaction.response.send_message(embed=embed, view=JokeView())