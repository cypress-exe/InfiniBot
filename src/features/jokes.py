from nextcord import Interaction
import nextcord
import random
import os
import json
import logging

from components import utils

class Joke:
    def __init__(self, title, body, punchline):
        self.title = title
        self.body = body
        self.punchline = punchline

    def __str__(self):
        return (
            f"Title: {self.title}\n"
            f"Body: {self.body}\n"
            f"Punchline: {self.punchline}"
        )
    
    def __dict__(self):
        return {
            "title": self.title,
            "body": self.body,
            "punchline": self.punchline
        }
    
    def __hash__(self):
        return hash((self.title, self.body, self.punchline))

class JokeManager:
    def __init__(self, file_path="generated/files/jokes.json"):
        self.jokes:list[Joke] = []
        self.file_path = file_path

        self.load_jokes()

    def load_jokes(self):
        logging.debug("Loading jokes...")
        
        # Clear jokes
        self.jokes = []

        try:
            jokes = {}
            with open(self.file_path, "r") as f:
                jokes = json.load(f)

            for joke in jokes["jokes"]:
                self.jokes.append(Joke(
                    title = joke["title"], 
                    body = joke["body"], 
                    punchline = joke["punchline"] if "punchline" in joke else None
                ))
        except Exception as e:
            logging.error(f"Failed to load jokes: {e}", exc_info=True)
    
    def save_jokes(self):
        logging.debug("Saving jokes...")

        if self.jokes is None or len(self.jokes) == 0:
            # Jokes might have gotten corrupted. Don't override all jokes with an empty list.
            logging.warning("Tried to save jokes, but jokes was None or empty. Skipping due to safety reasons. Jokes: " + str(self.jokes))
            return

        try:
            with open(self.file_path, "w") as f:
                json.dump({"jokes": [joke.__dict__ for joke in self.jokes]}, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save jokes: {e}", exc_info=True)

    def add_joke(self, joke:Joke):
        logging.info(f"Adding joke: {joke}")
        self.jokes.append(joke)

        self.save_jokes()


async def run_joke_command(interaction: Interaction):
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
    
    embed = nextcord.Embed(
        title=joke.title,
        description=f"{joke.body}\n\n{f'Answer: ||{joke.punchline}||' if joke.punchline else ''}",
        color=nextcord.Color.magenta()
    )
    
    await interaction.response.send_message(embed=embed)