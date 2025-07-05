from nextcord import Interaction
import nextcord
from abc import ABC, abstractmethod

class OptionsButton(nextcord.ui.Button, ABC):
    def __init__(self, outer, interaction: Interaction, **kwargs):
        self.outer = outer
        self.interaction = interaction
        self._type = kwargs.get("_type")
        
        super().__init__(label=self.get_label(), style=nextcord.ButtonStyle.gray)

    @abstractmethod
    def get_label(self) -> str:
        """Return the label for the button."""
        pass

    @abstractmethod
    async def load(self, interaction: Interaction, data: dict) -> bool:
        """Load the button with the provided data and return whether it should be added to the view."""
        pass