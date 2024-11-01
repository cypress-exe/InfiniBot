from nextcord import Interaction
import nextcord
import copy

# "Disabled Feature" override
async def disabled_feature_override(self: nextcord.ui.View, interaction: Interaction):
    """Overrides a page if the feature was disabled

    ------
    Parameters
    ------
    self: `nextcord.ui.View`
        The current view.
    interaction: `nextcord.Interaction`
        An interaction.
        
    Returns
    ------
        `None`
    """    
    # Only allow the back button
    for child in list(self.children):
        if isinstance(child, nextcord.ui.Button):
            if child.style == nextcord.ButtonStyle.danger or child.style == nextcord.ButtonStyle.red:
                child.label = "Back"
                continue;
            else:
                self.remove_item(child)
    
    # Replace with error
    embed = nextcord.Embed(title = "Disabled Feature", description = "This feature has been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red())
    try: await interaction.response.edit_message(embed = embed, view = self)
    except: await interaction.response.send_message(embed = embed, view = self, ephemeral=True)

class SelectView(nextcord.ui.View):
    """Creates a select view that has pages if needed.

    ------
    Parameters
    ------
    embed: `nextcord.Embed`
        The embed
    options: `list[nextcord.SelectOption]`
        Options of the Select
    returnCommand: `def(interaction, str | None)`
        Command to call when finished. Returns a value if the user selected something. Returns None if the user canceled.
        
    Optional Parameters
    ------
    placeholder: optional [`str`]
        Placeholder for the Select. Defaults to None.
    continueButtonLabel: optional [`str`]
        Continue Button Label. Defaults to "Continue".
    cancelButtonLabel: optional [`str`]
        Cancel Button Label. Defaults to "Cancel".
    preserveOrder: optional [`bool`]
        Preserves the order of options. Defaults to "False", where the options will be alphabetized.
        
    Raises
    ------
    `ValueError`
        If the arguments are incorrect.
        
    Setup
    ------
    Call `await ~setup(nextcord.Interaction)` to begin setup.
    """
        
    def __init__(self, embed: nextcord.Embed, 
                 options: list[nextcord.SelectOption], 
                 returnCommand, 
                 placeholder: str = None, 
                 continueButtonLabel = "Continue", 
                 cancelButtonLabel = "Cancel", 
                 preserveOrder = False):
        
        super().__init__()
        self.page = 0
        self.embed = embed
        self.options = options
        self.returnCommand = returnCommand
        
        # Confirm objects
        if self.options == None or self.options == []:
            raise ValueError(f"'options' must be a 'list' with one or more 'nextcord.SelectOption' items.")       
        if type(self.options) != list:
            raise ValueError(f"'options' must be of type 'list'. Recieved type '{type(self.options)}'")        
        for option in self.options:
            if type(option) != nextcord.SelectOption:
                raise ValueError(f"'options' must only contain 'nextcord.SelectOption' items. Countained 1+ '{type(option)}'")
            
        # Remove Unknowns
        if not self.embed.description: self.embed.description = ""
        confirmed_options = []
        for option in self.options:
            if option == None: continue
            if not isinstance(option, nextcord.SelectOption): continue
            if option.label == None: continue
            if option.value == None: continue
            confirmed_options.append(option)
        self.options = confirmed_options
        
        # Alphabetize options
        if not preserveOrder:
            # For some reason, this is how we have to do it to sort and get all "__" values at the top.
            self.options = sorted(self.options, key=lambda option: [not(isinstance(option.value, str) and option.value.startswith("__")), option.label.lower()])
        
        
        # Parse options into different pages
        self.selectOptions = [[]]
        xindex = 0
        yindex = 0
        for option in self.options:
            if yindex == 25:    # <--------------------------- Change the Threshold HERE!!!!
                # Create new page
                self.selectOptions.append([])
                xindex += 1
                yindex = 0
            # Add to current page
            self.selectOptions[xindex].append(option)
            yindex += 1
            
        del xindex, yindex
        
        # Add select menu
        self.Select = nextcord.ui.Select(options = [nextcord.SelectOption(label = "PLACEHOLDER!!!")], placeholder=placeholder)
        self.add_item(self.Select)
        
        # Add buttons
        self.backButton = nextcord.ui.Button(emoji = "◀️", style = nextcord.ButtonStyle.gray, row = 1, disabled = True)
        self.backButton.callback = self.back
        
        self.nextButton = nextcord.ui.Button(emoji = "▶️", style = nextcord.ButtonStyle.gray, row = 1)
        self.nextButton.callback = self.next
        
        if len(self.selectOptions) > 1: # If we need pages
            self.add_item(self.backButton)
            self.add_item(self.nextButton)
        
        self.cancelButton = nextcord.ui.Button(label = cancelButtonLabel, style = nextcord.ButtonStyle.danger, row = 2)
        self.cancelButton.callback = self.cancelButtonCallback
        self.add_item(self.cancelButton)
        
        self.continueButton = nextcord.ui.Button(label = continueButtonLabel, style = nextcord.ButtonStyle.blurple, row = 2)
        self.continueButton.callback = self.continueButtonCallback
        self.add_item(self.continueButton)
        
    async def setup(self, interaction):
        await self.setPage(interaction, 0)
        
    async def setPage(self, interaction: Interaction, page: int):
        if page >= len(self.selectOptions): raise IndexError("Page (int) was out of bounds of self.selectOptions (list[nextcord.SelectOption]).")
        
        embed = copy.copy(self.embed)
        if len(self.selectOptions) > 1: # If we don't need pages, don't bother the user with pages.
            embed.description += f"\n\n**Page {page + 1} of {len(self.selectOptions)}**\n{self.selectOptions[page][0].label} → {self.selectOptions[page][-1].label}"
        
        self.Select.options = self.selectOptions[page]

        if interaction != None: 
            await interaction.response.edit_message(embed = embed, view = self) 
            self.page = page
            return True
        
        return False
    
    
    async def back(self, interaction: Interaction):
        if self.page == 0: return
        
        #check to see if the back button *will* become unusable...
        self.backButton.disabled = False
        self.nextButton.disabled = False
        if self.page - 1 == 0: self.backButton.disabled = True
        else: self.nextButton.disabled = False
        
        #set the page
        await self.setPage(interaction, self.page - 1)
        
    async def next(self, interaction: Interaction):
        if self.page == (len(self.selectOptions) - 1): return
        
        #check to see if the next button *will* become unusable...
        self.backButton.disabled = False
        self.nextButton.disabled = False
        if self.page + 1 == (len(self.selectOptions) - 1): self.nextButton.disabled = True
        else: self.backButton.disabled = False
        
        #set the page
        await self.setPage(interaction, self.page + 1)
        
    
    async def cancelButtonCallback(self, interaction: Interaction):
        await self.returnCommand(interaction, None)
    
    async def continueButtonCallback(self, interaction: Interaction):
        if len(self.Select.values) == 0: return
        await self.returnCommand(interaction, self.Select.values[0])   
  