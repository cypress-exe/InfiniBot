from nextcord import AuditLogAction, Interaction, SlashOption
from nextcord.ext import commands
#from youtube_dl import YoutubeDL
from yt_dlp import YoutubeDL
from collections import defaultdict
from typing import List
import nextcord
import os
import datetime
import humanfriendly
import math
import asyncio
import random
import time
import Levenshtein
import typing
import json
import io
import mmap
import sys
import re








# ----------------------------------------------------------- VERSION OF INFINIBOT---------------------------------------------------------

VERSION = 2.0

# ------------------------------------------------------------------------------------------------------------------------------------------










# IDs
guildIDS = [968872260557488158, 995459530202808332]
developmentGuild = [968872260557488158, 995459530202808332]
developerID = [836701982425219072]
infinibotGuild = 1009127888483799110
issueReportChannel = 1012433924011597875
submissionChannel = 1009139174256935103
updatesChannel = 1009132479036276826
infinibotUpdatesRole = 1087605721060872262

# Links
supportServerLink = 'https://discord.gg/mWgJJ8ZqwR'
topggLink = "https://top.gg/bot/991832387015159911"
topggVoteLink = "https://top.gg/bot/991832387015159911/vote"
topggReviewLink = "https://top.gg/bot/991832387015159911#reviews"
inviteLink = "https://discord.com/oauth2/authorize?client_id=991832387015159911&permissions=1374809222364&scope=bot"

# Global Variables
autoDeletedMessageTime = None
nicknameChanged = []
requiredPermissions = """
\n**Text Channel Permissions**:
• View Channels
• Send Messages
• Embed Links
• Manage Roles
• Manage Channels
• Manage Messages
• Manage Nicknames
• View Audit Log
• Add Reactions
• Timeout Members
• Ban Members
• Read Message History

**Voice Channel Permissions**:
• Connect
• Move Members

→ Tip: Make sure that InfiniBot has all of these permissions in all of the channels in your server."""





# INIT BOT ==============================================================================================================================================================
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.reactions = True

bot = commands.Bot(intents = intents, allowed_mentions = nextcord.AllowedMentions(everyone = True), help_command=None)









# Files, Profile, and Dashboard general functions
def standardizeDictProperties(defaultDict: dict, objectDict: dict, aliases: dict = {}):
    """A recursive function that makes sure that the two dictionaries have the same properties.

    Args:
        defaultDict (dict): A dictionary containing all the properties and their default values
        objectDict (dict): The dictionary that will be edited
        aliases (dict) (optional): A dictionary of aliases (for backwards compatibility) (ex: {'old':'new'})
    Returns:
        dict: The object dictionary after having its properties standardized
    """


    # cloning defaultDict as returnDict
    returnDict = dict(defaultDict)
    
    # checking for aliases and changing the dictionary to account for them
    objectDict = {aliases.get(k, k): v for k, v in objectDict.items()}
    
    # for each key:
    for key in returnDict.keys():
        # for each key in returnDict
           
        if key in objectDict.keys():
            # the key was in our objectdict. Now we just have to set it.
            # We have to check this recursively if this is a dictionary, and set this to be the returned value from the recursive function.
            
            if type(objectDict[key]) == dict:
                # this is a dictionary. 
                # Now, we have to run this recursively to make sure that all values inside the dictionary are updated
                returnDict[key] = standardizeDictProperties(returnDict[key], objectDict[key], aliases = aliases)
            else:
                # this is not a dictionary. It's just a regular value
                # putting this value into returnDict
                returnDict[key] = objectDict[key]
        else:
            # the key was not in the objectDict, but it was in the defaultDict.
            # but, because the key was already added (as the default), we don't need to worry at all.
            # lower dictionaries that may be attached to this are also not a concern, seeing how it never existed on the objectDict, so the defaults are fine.
            continue
        
    return returnDict
    
def getDiscordColorFromString(color: str):
    if color == None or color == "": return nextcord.Color.default()
        
    if color == "Red": return nextcord.Color.red()
    if color == "Green": return nextcord.Color.green()
    if color == "Blue": return nextcord.Color.blue()
    if color == "Yellow": return nextcord.Color.yellow()
    if color == "White": return nextcord.Color.from_rgb(255, 255, 255) #white
    
    if color == "Blurple": return nextcord.Color.blurple()
    if color == "Greyple": return nextcord.Color.greyple()
    if color == "Teal": return nextcord.Color.teal()
    if color == "Purple": return nextcord.Color.purple()
    
    if color == "Gold": return nextcord.Color.gold()
    if color == "Magenta": return nextcord.Color.magenta()
    if color == "Fuchsia": return nextcord.Color.fuchsia()
    
    return nextcord.Color.default()

def getStringFromDiscordColor(color: nextcord.colour.Colour):
    if color == None or color == nextcord.Color.default(): return None
        
    if color == nextcord.Color.red(): return "Red"
    if color == nextcord.Color.green(): return "Green"
    if color == nextcord.Color.blue(): return "Blue"
    if color == nextcord.Color.yellow(): return "Yellow"
    if color == nextcord.Color.from_rgb(255, 255, 255): return "White"
    
    if color == nextcord.Color.blurple(): return "Blurple"
    if color == nextcord.Color.greyple(): return "Greyple"
    if color == nextcord.Color.teal(): return "Teal"
    if color ==nextcord.Color.purple(): return  "Purple"
    
    if color == nextcord.Color.gold(): return "Gold"
    if color == nextcord.Color.magenta(): return "Magenta"
    if color == nextcord.Color.fuchsia(): return "Fuchsia"
    
    return None

def standardizeStrIndention(string: str):
    # Split the string into lines
    lines = string.split('\n')

    # Remove the first level of indentation
    for i in range(len(lines)):
        lines[i] = lines[i].lstrip()

    # Iterate through each line and remove unneeded spaces based on the indentation level
    indent_level = 0
    for i in range(len(lines)):
        line = lines[i]
        if len(line) == 0:
            continue  # skip empty lines
        cur_indent_level = len(line) - len(line.lstrip())
        if cur_indent_level > indent_level:
            # Indentation level increased
            indent_level = cur_indent_level
        elif cur_indent_level < indent_level:
            # Indentation level decreased, go back to previous level
            indent_level = cur_indent_level
        # Remove the unneeded spaces
        lines[i] = " " * indent_level + line.lstrip()

    # Join the lines back into a string
    return('\n'.join(lines))



class FileOperations:
    '''Handles File Operations including loading, saving, and list manipulation'''
    def __init__(self):
        #be sure to change this in server.saveData() and server.__init__()
        self.DATADEFAULT = {
            'version' : VERSION,
            'active': {
                'profanityModeration': True,
                'spamModeration': True,
                'logging': True,
                'leveling': True,
                'deleteInvites': False,
                'getUpdates': True
            },
            'channels': {
                'admin': None,
                'log': None,
                'join': None,
                'leave': None,
                'leveling': None,
                'levelingExempt': []
            },
            'moderation': {
                'maxStrikes': 3,
                'profanityTimeoutTime': '2h',
                'strikeExpireTime': 7,
                'spamTimeoutTime': '1m',
                'messagesThreshold': 5
            },
            'eventMessages': {
                'joinMessage': 'Hello There, [member]!',
                'leaveMessage': '[member] left. They will be remembered.'
            },
            'leveling': {
                'pointsLostPerDay': 5,
                'levelingMessage': 'Congrats! You reached level [level]!'
            },
            'allowCards': {
                'level': True,
                'join': True
            },
            'defaultRoles': [],
            'statsMessage': None
        }
        
        #be sure to change this in main.savePersistentData() and main.__init__()
        self.PERSISTENTDATADEFAULT = {
            'login_response': {
                'guild': None,
                'channel': None
            }
        }

    def getPersistentData(self):
        '''Returns all PERSISTENT DATA in str form'''
        contents = ""
        if os.path.exists("./RequiredFiles/Persistent.txt"):
            with open("./RequiredFiles/Persistent.txt", "r") as file:
                contents = file.read()
            
        else:
            with open("./RequiredFiles/Persistent.txt", "w") as file:
                contents = json.dumps(self.PERSISTENTDATADEFAULT)
                file.write(json.dumps(self.PERSISTENTDATADEFAULT))
        
        return contents

    def getAllProfaneWords(self):
        '''Returns all Profane WORDS in list form (per server)'''
        contents = ""
        if os.path.exists("./Files/ProfaneWords.binary"):
            with open("./Files/ProfaneWords.binary", "rb") as file:
                contents = file.read().decode()
            
        else:
            with open("./Files/ProfaneWords.binary", "wb") as file:
                contents = ""
                file.write("".encode())
        
        return contents.split("\n")

    def getAllData(self):
        '''Returns all DATA in list form (per server)'''
        contents = ""
        if os.path.exists("./Files/Data.binary"):
            with open("./Files/Data.binary", "rb") as file:
                contents = file.read().decode()
        else:
            with open("./Files/Data.binary", "wb") as file:
                contents = ""
                file.write("".encode())
        
        return contents.split("\n")

    def getAllStrikes(self):
        '''Returns all STRIKES in list form (per server)'''
        contents = ""
        if os.path.exists("./Files/Strikes.binary"):
            with open("./Files/Strikes.binary", "rb") as file:
                contents = file.read().decode()
        else:
            with open("./Files/Strikes.binary", "wb") as file:
                contents = ""
                file.write("".encode())
        
        return contents.split("\n")

    def getAllBirthdays(self):
        '''Returns all BIRTHDAYS in list form (per server)'''
        contents = ""
        if os.path.exists("./Files/Birthdays.binary"):
            with open("./Files/Birthdays.binary", "rb") as file:
                contents = file.read().decode()
        else:
            with open("./Files/Birthdays.binary", "wb") as file:
                contents = ""
                file.write("".encode())
        
        return contents.split("\n")
    
    def getAllLevels(self):
        '''Returns all LEVELS in list form (per server)'''
        contents = ""
        if os.path.exists("./Files/Levels.binary"):
            with open("./Files/Levels.binary", "rb") as file:
                contents = file.read().decode()
        else:
            with open("./Files/Levels.binary", "wb") as file:
                contents = ""
                file.write("".encode())
        
        return contents.split("\n")
    
    def getAllLevelRewards(self):
        '''Returns all LEVEL REWARDS in list form (per server)'''
        contents = ""
        if os.path.exists("./Files/LevelRewards.binary"):
            with open("./Files/LevelRewards.binary", "rb") as file:
                contents = file.read().decode()
        else:
            with open("./Files/LevelRewards.binary", "wb") as file:
                contents = ""
                file.write("".encode())
        
        return contents.split("\n")

    def getAllVCs(self):
        '''Returns all VCs in list form (per server)'''
        contents = ""
        if os.path.exists("./Files/JoinToCreateVcs.binary"):
            with open("./Files/JoinToCreateVcs.binary", "rb") as file:
                contents = file.read().decode()
            
        else:
            with open("./Files/JoinToCreateVcs.binary", "wb") as file:
                contents = ""
                file.write("".encode())
        
        return contents.split("\n")
    
    def getAllMembers(self):
        '''Returns all MEMBERS in list form (per member)'''
        contents = ""
        if os.path.exists("./Files/Members.binary"):
            with open("./Files/Members.binary", "rb") as file:
                contents = file.read().decode()
            
        else:
            with open("./Files/Members.binary", "wb") as file:
                contents = ""
                file.write("".encode())
        
        return contents.split("\n")
    
    def getAllAutoBans(self):
        '''Returns all AUTO-BANS in list form (per server)'''
        contents = ""
        if os.path.exists("./Files/Bans.binary"):
            with open("./Files/Bans.binary", "rb") as file:
                contents = file.read().decode()
            
        else:
            with open("./Files/Bans.binary", "wb") as file:
                contents = ""
                file.write("".encode())
        
        return contents.split("\n")
    
    def getAllInvites(self):
        '''Returns invites (str) (per server)'''
        contents = ""
        if os.path.exists("./Files/Invites.binary"):
            with open("./Files/Invites.binary", "rb") as file:
                contents = file.read().decode()
            
        else:
            with open("./Files/Invites.binary", "wb") as file:
                contents = ""
                file.write("".encode())
        
        return contents.split("\n")

    def getAllMessages(self):
        '''Returns messages (raw list) (per server)'''
        contents = ""
        if os.path.exists("./Files/Messages.binary"):
            with open("./Files/Messages.binary", "rb") as file:
                contents = file.read().decode()
            
        else:
            with open("./Files/Messages.binary", "wb") as file:
                contents = ""
                file.write("".encode())
        
        return contents.split("\n")



    def addServerToList(self, guild_id, list, content):
        '''Can ONLY add servers/members to a list. If the server/member already exists, this function will return it without any edits.'''
        for server in list:
            if server.split("———")[0] == str(guild_id):
                return list
        
        if content != None: list.append(guild_id + "———" + content)
        else: list.append(guild_id)

        if list[0] == "": list.pop(0)

        return list

    def editServerInList(self, guild_id, list: list[str], content):
        '''Handles the adding and editing of a server/member in a list. *Takes out Spaces*'''
        #take out any empty spaces:
        optimizedList = []
        for server in list:
            if server.strip() != "": optimizedList.append(server)
            
            
        
        for server in optimizedList:
            if server.split("———")[0] == str(guild_id):
                if content != None: optimizedList[optimizedList.index(server)] = guild_id + "———" + content
                else: optimizedList[optimizedList.index(server)] = guild_id
                return optimizedList
            
        
        if content != None: optimizedList.append(guild_id + "———" + content)
        else: optimizedList.append(guild_id)

        if optimizedList[0] == "": optimizedList.pop(0)

        return optimizedList

    def deleteServerFromList(self, guild_id, list):
        '''Will delete ONE server/member from a list. Supports when the server/member is not inside the list.'''
        for server in list:
            if server.split("———")[0] == str(guild_id):
                list.pop(list.index(server))
                return list

        return list

    def joinWithHyphens(self, list: list):
        '''Takes a list and joins it with "———"'''
        list = [str(item) for item in list]
        if list == []:
            return None
        else:
            return "———".join(list)
            

    def savePersistentData(self, data):
        '''Saves a string of PERSISTENT DATA'''
        with open("./RequiredFiles/Persistent.txt", "w") as file:
            file.write(data)

    def saveData(self, list):
        '''Saves a list (per server) of DATA'''
        formatted = "\n".join(list)
        with open("./Files/Data.binary", "wb") as file:
            file.write(formatted.encode())

    def saveBirthdays(self, list):
        '''Saves a list (per server) of BIRTHDAYS'''
        formatted = "\n".join(list)
        with open("./Files/Birthdays.binary", "wb") as file:
            file.write(formatted.encode())

    def saveProfaneWords(self, list):
        '''Saves a list (per server) of Profane WORDS'''
        formatted = "\n".join(list)
        with open("./Files/ProfaneWords.binary", "wb") as file:
            file.write(formatted.encode())

    def saveStrikes(self, list):
        '''Saves a list (per server) of STRIKES'''
        formatted = "\n".join(list)
        with open("./Files/Strikes.binary", "wb") as file:
            file.write(formatted.encode())

    def saveLevels(self, list):
        '''Saves a list (per server) of LEVELS'''
        formatted = "\n".join(list)
        with open("./Files/Levels.binary", "wb") as file:
            file.write(formatted.encode())
            
    def saveLevelRewards(self, list):
        '''Saves a list (per server) of LEVEL REWARDS'''
        formatted = "\n".join(list)
        with open("./Files/LevelRewards.binary", "wb") as file:
            file.write(formatted.encode())

    def saveVCs(self, list):
        '''Saves a list (per server) of VCs'''
        formatted = "\n".join(list)
        with open("./Files/JoinToCreateVcs.binary", "wb") as file:
            file.write(formatted.encode())
            
    def saveMembers(self, list):
        '''Saves a list (per member) of MEMBERS'''
        formatted = "\n".join(list)
        with open("./Files/Members.binary", "wb") as file:
            file.write(formatted.encode())
            
    def saveAutoBans(self, list):
        '''Saves a list (per server) of AUTO-BANS'''
        formatted = "\n".join(list)
        with open("./Files/Bans.binary", "wb") as file:
            file.write(formatted.encode())
            
    def saveInvites(self, list):
        '''Saves a list (per server) of Invites'''
        formatted = "\n".join(list)
        with open("./Files/Invites.binary", "wb") as file:
            file.write(formatted.encode())

    def saveMessages(self, list):
        '''Saves a formatted list (per server) of Messages'''
        formatted = "\n".join(list)
        with open("./Files/Messages.binary", "wb") as file:
            file.write(formatted.encode())


    def getDefaultProfaneWords(self):
        '''Returns default Profane words in hyphenated form (apple———banana———orange)'''
        if os.path.exists("./RequiredFiles/ProfaneWordsDefault.binary"):
            with open("./RequiredFiles/ProfaneWordsDefault.binary", "rb") as file:
                return file.read().decode()
        else:
            print("Default Profane Words are MISSING! ---------------------------")
            exit()


fileOperations = FileOperations()


class Strike:
    '''TYPE Strike → Moderation Strikes → contains the member (nextcord.Member), memberID (int), strike (int), and lastStrike (time → str)'''
    def __init__(self, guild: nextcord.Guild, package: str):
        self.data = package.split("|||")
        self.member: nextcord.Member = guild.get_member(int(self.data[0]))
        self.memberID: int = int(self.data[0])
        self.strike: int = int(self.data[1])
        self.lastStrike: str = (self.data[2])

class Birthday:
    '''TYPE Birthday → Birthdays → contains the member (nextcord.Member), memberID (int), date (time → str), and realName (str | None)'''
    def __init__(self, guild: nextcord.Guild, package: str):
        self.data = package.split("|||")
        self.member: nextcord.Member = guild.get_member(int(self.data[0]))
        self.memberID = int(self.data[0])
        self.date: str = self.data[1]
        if len(self.data) == 3:
            self.realName = self.data[2]
        else:
            self.realName = None

class JoinToCreateVC:
    '''TYPE JoinToCreateVc → Join-to-create-vcs → contains the id (int) and channel (nextcord.VoiceChannel | None)'''
    def __init__(self, guild: nextcord.Guild, package: str, id: int = None):
        if id == None:
            self.data = package.split("|||")
            self.id: int = int(self.data[0])
        else:
            self.data = None
            self.id: int = int(id)
            
        self.channel: nextcord.VoiceChannel = guild.get_channel(self.id)
        
        #check Permissions
        if not (self.channel.permissions_for(guild.me).view_channel and self.channel.permissions_for(guild.me).connect and self.channel.permissions_for(guild.me).manage_channels):
            self.active = False
        else:
            self.active = True

class StatsMessage:
    '''TYPE StatsMessage → Stats Message → contains the messageID(int | None), channelID(int | None), and link (str | None).'''
    def __init__(self, guild: nextcord.Guild, package: typing.Union[str, None]):
        if package != None and package != None:
            self.data = package.split("/")
            self.guild = guild
            self.channelID: int = int(self.data[0])
            self.messageID: int = int(self.data[1])
            self.link = f"https://discord.com/channels/{self.guild.id}/{self.channelID}/{self.messageID}"
            self.active = True
        else:
            self.guild = guild
            self.channelID = None
            self.messageID = None
            self.link = None
            self.active = False
        
    async def checkMessage(self):
        '''Finds the message and determins whether it exists.'''
        if self.channelID == None or self.messageID == None:
            self.setValue(None)
            return False
        
        try:
            channel: nextcord.TextChannel = await self.guild.fetch_channel(self.channelID)
            if channel is None: 
                self.setValue(None)
                return False, None
            
            message: nextcord.Message = await channel.fetch_message(self.messageID)
            if message is None: 
                self.setValue(None)
                return False, None
            
            return True, message
        except nextcord.NotFound:
            return False, None
    
    def setValue(self, message: nextcord.Message):
        '''Updates all values to reflect the attribute message'''
        if message == None:
            self.channelID = None
            self.messageID = None
            self.link = None
            self.active = False
            return
        
        self.channelID: int = message.channel.id
        self.messageID: int = message.id
        self.link = f"https://discord.com/channels/{self.guild.id}/{self.channelID}/{self.messageID}"
    
    def saveValue(self):
        '''Returns how this variable should be saved.'''
        if self.channelID == None or self.messageID == None:
            return None
        
        return str(self.channelID) + "/" + str(self.messageID)

class Level:
    '''TYPE LEVEL → Leveling Level → contains the member (nextcord.Member), memberID (int), and score (int)'''
    def __init__(self, guild: nextcord.Guild, package: str):
        self.data = package.split("|||")
        self.member: nextcord.Member = guild.get_member(int(self.data[0]))
        self.memberID = int(self.data[0])
        self.score = int(self.data[1])
        
class LevelReward:
    '''TYPE Strike → Leveling Level Reward → contains the role (nextcord.Role), roleID (int), and level (int)'''
    def __init__(self, guild: nextcord.Guild, package: str):
        self.data = package.split("|||")
        self.role: nextcord.Role = guild.get_role(int(self.data[0]))
        self.roleID = int(self.data[0])
        self.level = int(self.data[1])

class AutoBan:
    '''TYPE AUTO-BAN → Auto-Bans → contains the memberName (str) and memberID (int)'''
    def __init__(self, package: str):
        self.data = package.split("|||")
        self.memberName: str = self.data[0]
        self.memberID = int(self.data[1])
        
    def saveValue(self):
        return f"{self.memberName}|||{self.memberID}"


class Levels:
    '''Manages Leveling System. Capable of loading and saving a member's levels and loading and saving level rewards. Should be instantiated through the class Server'''
    def __init__(self, guild: nextcord.Guild):
        self.guild = guild
        self.guild_id = str(guild.id)
        
        needToSave = False
        self.allMembers: list[Level] = []
        for level in self.__getLevels():
            levelClass = Level(self.guild, level)
            if levelClass.member != None: self.allMembers.append(levelClass)
            else: needToSave = True
            
        if needToSave: self.saveLevels()
        
        
        #get rid of members with a level of 0
        needToSave = False
        _allMembers = []
        for member in self.allMembers:
            if member.score != 0: _allMembers.append(member) #if their score isn't 0, add them to the list
            if member.score == 0: needToSave = True
                
        self.allMembers = _allMembers     
        if needToSave: self.saveLevels()
        
        
        needToSave = False
        self.levelRewards: list[LevelReward] = []
        for levelReward in self.__getLevelRewards():
            levelRewardClass = LevelReward(self.guild, levelReward)
            if levelRewardClass.role != None: self.levelRewards.append(levelRewardClass)
            else: needToSave = True

        if needToSave: self.saveLevelRewards()
 
    def __getLevels(self):
        '''Returns a list each member's level (type LEVEL). Will add server if needed. Members with a level of 0 will be ommitted.'''
        allLevels = fileOperations.getAllLevels()

        for server in allLevels:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        newLevels = fileOperations.addServerToList(self.guild_id, allLevels, None)
        fileOperations.saveLevels(newLevels)

        return []

    def saveLevels(self):
        '''Saves any level changes made to this class.'''
        levelsList = []
        for level in self.allMembers:
            levelsList.append(str(level.memberID) + "|||" + str(level.score))

        levelsString = fileOperations.joinWithHyphens(levelsList)
        allLevels = fileOperations.getAllLevels()

        list = fileOperations.editServerInList(self.guild_id, allLevels, levelsString)

        fileOperations.saveLevels(list)

    def memberExists(self, memberID):
        '''Returns a BOOL whether a member has a recorded level.'''
        memberID = int(memberID)
        for level in self.allMembers:
            if level.memberID == memberID:
                return True

        return False

    def addMember(self, memberID, score = 0):
        '''Adds a member to leveling system with a default score of 0* (returns True). Supports when the member already exists (returns False).'''
        memberID = int(memberID)
        if self.memberExists(memberID): return False

        self.allMembers.append(Level(self.guild, f"{str(memberID)}|||{str(score)}"))

        return True

    def getMember(self, memberID):
        '''Retrieves a member's level. Returns type LEVEL or NONE'''
        memberID = int(memberID)
        if self.memberExists(memberID):
            for level in self.allMembers:
                if level.memberID == int(memberID):
                    return level

        else:
            return None

    def deleteMember(self, memberID):
        '''Delets a member from leveling system (returns True). Supports when the member doesn't exist (returns False).'''
        memberID = int(memberID)
        if self.memberExists(memberID):
            for level in self.allMembers:
                if level.memberID == memberID:
                    self.allMembers.pop(self.allMembers.index(level))
                    return True
            
        return False


    def __getLevelRewards(self):
        '''Returns a list each level reward (type LEVELREWARD). Will add server if needed.'''
        allLevelRewards = fileOperations.getAllLevelRewards()

        for server in allLevelRewards:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        newLevelRewards = fileOperations.addServerToList(self.guild_id, allLevelRewards, None)
        fileOperations.saveLevelRewards(newLevelRewards)

        return []

    def saveLevelRewards(self):
        '''Saves any level reward changes made to this class.'''
        levelRewardsList = []
        for levelReward in self.levelRewards:
            levelRewardsList.append(str(levelReward.role.id) + "|||" + str(levelReward.level))

        levelRewardsString = fileOperations.joinWithHyphens(levelRewardsList)
        allLevelRewards = fileOperations.getAllLevelRewards()

        list = fileOperations.editServerInList(self.guild_id, allLevelRewards, levelRewardsString)

        fileOperations.saveLevelRewards(list)

    def levelRewardExists(self, roleID):
        '''Returns a BOOL whether a role has an associated level reward.'''
        for levelReward in self.levelRewards:
            if levelReward.roleID == roleID:
                return True

        return False

    def addLevelReward(self, roleID, level):
        '''Adds a level reward to leveling system (returns True). Supports when the level reward already exists (returns False).'''
        if self.levelRewardExists(roleID): return False

        self.levelRewards.append(LevelReward(self.guild, f"{str(roleID)}|||{str(level)}"))

        return True

    def getLevelReward(self, roleID):
        '''Retrieves a level reward. Returns type LEVELREWARD or NONE'''
        if self.levelRewardExists(roleID):
            for levelReward in self.levelRewards:
                if levelReward.roleID == int(roleID):
                    return levelReward

        else:
            return None

    def deleteLevelReward(self, roleID):
        '''Delets a level reward from leveling system (returns True). Supports when the level reward doesn't exist (returns False).'''
        if self.levelRewardExists(roleID):
            for levelReward in self.levelRewards:
                if levelReward.roleID == int(roleID):
                    self.levelRewards.pop(self.levelRewards.index(levelReward))
                    break
            
            return True
        else:
            return False

class Server:
    '''Main Infrastructure. Requires a guild_id, and you can access/save any saved data.'''
    def __init__(self, guild_id):
        self.guild_id = str(guild_id)

        self.guild = None

        for guild in bot.guilds:
            if guild.id == int(guild_id):
                self.guild = guild

        if self.guild != None:
            self.rawData = self.__getData()
            self.ProfaneWords = self.__getProfaneWords()
            self.__rawStrikes = self.__getStrikes()
            self.__rawBirthdays = self.__getBirthdays()
            self.__rawVCs = self.__getVCs()
            self.__rawBans = self.__getAutoBans()
            #self.invite = self.__getInvite()
        

            #handle data
            
            def loadChannel(channel):
                if channel == None:
                    return None
                return bot.get_channel(channel)
            
            def loadChannels(channels):
                return [loadChannel(channel) for channel in channels if channel != None]
            
            def defaultRoles():
                result = []
                for roleID in self.rawData['defaultRoles']:
                    role = self.guild.get_role(int(roleID))
                    if role != None: result.append(role)
                
                return result
            
            #KeyError
            self.version = float(self.rawData['version'])
            self.profanityBool = self.rawData['active']['profanityModeration']
            self.spamBool = self.rawData['active']['spamModeration']
            self.loggingBool = self.rawData['active']['logging']
            self.levelingBool = self.rawData['active']['leveling']
            self.deleteInvitesBool = self.rawData['active']['deleteInvites']
            self.getUpdates = self.rawData['active']['getUpdates']
            
            self.adminChannel = loadChannel(self.rawData['channels']['admin'])
            self.logChannel = loadChannel(self.rawData['channels']['log'])
            self.joinChannel = loadChannel(self.rawData['channels']['join'])
            self.leaveChannel = loadChannel(self.rawData['channels']['leave'])
            self.levelingChannel = loadChannel(self.rawData['channels']['leveling'])
            self.levelingExemptChannels = loadChannels(self.rawData['channels']['levelingExempt'])
            
            self.maxStrikes = self.rawData['moderation']['maxStrikes']
            self.profanityTimeoutTime = self.rawData['moderation']['profanityTimeoutTime']
            self.strikeExpireTime = self.rawData['moderation']['strikeExpireTime']
            self.spamTimeoutTime = self.rawData['moderation']['spamTimeoutTime']
            self.messagesThreshold = self.rawData['moderation']['messagesThreshold']
            
            self.joinMessage = self.rawData['eventMessages']['joinMessage']
            self.leaveMessage = self.rawData['eventMessages']['leaveMessage']
            
            self.pointsLostPerDay = self.rawData['leveling']['pointsLostPerDay']
            self.levelingMessage = self.rawData['leveling']['levelingMessage']
            
            self.allowLevelCardsBool = self.rawData['allowCards']['level']
            self.allowJoinCardsBool = self.rawData['allowCards']['join']
            
            self.defaultRoles = defaultRoles()
            self.statsMessage = StatsMessage(self.guild, self.rawData['statsMessage'])

            #handle strikes 
            self.strikes: list[Strike] = [Strike(self.guild, strike) for strike in self.__rawStrikes]

            #handle birthdays
            self.birthdays: list[Birthday] = [Birthday(self.guild, birthday) for birthday in self.__rawBirthdays]
            self.birthdays = [birthday for birthday in self.birthdays if birthday != None and birthday.member != None]
            self.birthdays = sorted(self.birthdays, key = lambda x: (x.member.display_name))
            
            #handle levels
            self.levels = Levels(self.guild)
            
            #handle join-to-create-vcs
            self.VCs: list[JoinToCreateVC] = [JoinToCreateVC(self.guild, vc) for vc in self.__rawVCs if self.guild.get_channel(int(vc)) != None]
            
            #handle bans
            self.autoBans: list[AutoBan] = [AutoBan(ban) for ban in self.__rawBans]
            self.autoBans = sorted(self.autoBans, key = lambda x: (x.memberName))
        
        #handle messages
        self.messages = Messages(self.guild_id)
        '''Not automatically initialized. Will be auto-initalized upon any changes.'''
        
        if self.guild == None:
            return None;

        
    def setAdminChannelID(self, id):
        '''Sets the Admin Channel via an ID instead of a channel. Returns TRUE if successful, or FALSE if Forbidden.'''
        try:
            self.adminChannel = bot.get_channel(int(id))
            return True
        except nextcord.errors.Forbidden:
            return False
        
    def setLogChannelID(self, id):
        '''Sets the Log Channel via an ID instead of a channel. Returns TRUE if successful, or FALSE if Forbidden.'''
        try:
            self.logChannel = bot.get_channel(int(id))
            return True
        except nextcord.errors.Forbidden:
            return False

    def setLevelingChannelID(self, id):
        '''Sets the Leveling Channel via an ID instead of a channel. Returns TRUE if successful, or FALSE if Forbidden.'''
        if id != None:
            try:
                self.levelingChannel = bot.get_channel(int(id))
                return True
            except nextcord.errors.Forbidden:
                return False
        else:
            self.levelingChannel = None
            return True
        
    def setJoinChannelID(self, id):
        '''Sets the Join Channel via an ID instead of a channel. Returns TRUE if successful, or FALSE if Forbidden.'''
        if id != None:
            try:
                self.joinChannel = bot.get_channel(int(id))
                return True
            except nextcord.errors.Forbidden:
                return False
        else:
            self.joinChannel = None
            return True
        
    def setLeaveChannelID(self, id):
        '''Sets the Leave Channel via an ID instead of a channel. Returns TRUE if successful, or FALSE if Forbidden.'''
        if id != None:
            try:
                self.leaveChannel = bot.get_channel(int(id))
                return True
            except nextcord.errors.Forbidden:
                return False
        else:
            self.leaveChannel = None
            return True


    def deleteServer(self):
        '''Deletes the server from all files on server.'''
        self.deleteDataAndSave()
        self.deleteProfaneWordsAndSave()
        self.deleteStrikesAndSave()
        self.deleteBirthdaysAndSave()
        self.deleteLevelsAndSave()
        self.deleteLevelRewardsAndSave()
        self.deleteVCsAndSave()
        self.deleteAutoBansAndSave()
        self.deleteInviteAndSave()
        self.messages.deleteAllAndSave()
    
   
         
    def __getData(self):
        '''Returns list of data.'''
        allData = fileOperations.getAllData()
        
        # Backwards-Compatibility Translations
        aliases = {
            "banInvites": "deleteInvites"
        }
        
        for server in allData:
            if server.split("———")[0] == self.guild_id:
                data: dict = json.loads(server.split("———")[1])        
                
                return standardizeDictProperties(fileOperations.DATADEFAULT, data, aliases = aliases)

        newData = fileOperations.addServerToList(self.guild_id, allData, json.dumps(fileOperations.DATADEFAULT))
        fileOperations.saveData(newData)

        return fileOperations.DATADEFAULT

    def saveData(self):
        '''Saves any changes to Data made to this class'''
        
        def formatChannel(channel: nextcord.TextChannel):
            if channel == None: return None
            return channel.id
        
        def formatChannelList(channels):
            return [formatChannel(channel) for channel in channels]
        
        def formatDefaultRoles():
            return [role.id for role in self.defaultRoles]
            
        #be sure to change this in fileOperations.__init__() and server.__getData()
        dataRaw = {
            'version' : VERSION,
            'active': {
                'profanityModeration': self.profanityBool,
                'spamModeration': self.spamBool,
                'logging': self.loggingBool,
                'leveling': self.levelingBool,
                'deleteInvites': self.deleteInvitesBool,
                'getUpdates': self.getUpdates
            },
            'channels': {
                'admin': formatChannel(self.adminChannel),
                'log': formatChannel(self.logChannel),
                'join': formatChannel(self.joinChannel),
                'leave': formatChannel(self.leaveChannel),
                'leveling': formatChannel(self.levelingChannel),
                'levelingExempt': formatChannelList(self.levelingExemptChannels)
            },
            'moderation': {
                'maxStrikes': int(self.maxStrikes),
                'profanityTimeoutTime': self.profanityTimeoutTime,
                'strikeExpireTime': int(self.strikeExpireTime),
                'spamTimeoutTime': self.spamTimeoutTime,
                'messagesThreshold': int(self.messagesThreshold)
            },
            'eventMessages': {
                'joinMessage': self.joinMessage,
                'leaveMessage': self.leaveMessage
            },
            'leveling': {
                'pointsLostPerDay': self.pointsLostPerDay,
                'levelingMessage': self.levelingMessage
            },
            'allowCards': {
                'level': self.allowLevelCardsBool,
                'join': self.allowJoinCardsBool
            },
            'defaultRoles': formatDefaultRoles(),
            'statsMessage': self.statsMessage.saveValue()
        }
        
        #formatting data
        dataJson = json.dumps(dataRaw)
        allData = fileOperations.getAllData()

        list = fileOperations.editServerInList(self.guild_id, allData, dataJson)
        fileOperations.saveData(list)

    def deleteDataAndSave(self):
        '''Deletes any data files from server'''
        allData = fileOperations.getAllData()

        list = fileOperations.deleteServerFromList(self.guild_id, allData)

        fileOperations.saveData(list) 




    def __getProfaneWords(self):
        '''Returns list of Profane words.'''
        allProfaneWords = fileOperations.getAllProfaneWords()

        for server in allProfaneWords:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]
            
            
        #if it doesn't exist yet...
        newProfaneWords = fileOperations.addServerToList(self.guild_id, allProfaneWords, fileOperations.getDefaultProfaneWords())
        fileOperations.saveProfaneWords(newProfaneWords)

        _returnInfo = fileOperations.getDefaultProfaneWords().split("———")
        return _returnInfo

    def saveProfaneWords(self):
        '''Saves any changes to Profane Words made to this class'''
        ProfaneWords = self.ProfaneWords
        allProfaneWords = fileOperations.getAllProfaneWords()

        list = fileOperations.editServerInList(self.guild_id, allProfaneWords, fileOperations.joinWithHyphens(ProfaneWords))

        fileOperations.saveProfaneWords(list)

    def ProfaneWordExists(self, word):
        '''Returns bool if Profane word exists on this server.'''
        for ProfaneWord in self.ProfaneWords:
            if ProfaneWord == word:
                return True
        
        return False

    def addProfaneWord(self, word):
        '''Adds a Profane word to this server (returns True). If it already existed, returns False.'''
        if self.ProfaneWordExists(word): return False
        
        self.ProfaneWords.append(word)
        return True

    def deleteProfaneWord(self, word):
        '''Deletes a Profane word from server (returns True). If Profane word didn't exist on this server, returns False.'''
        if self.ProfaneWordExists(word):
           self.ProfaneWords.pop(self.ProfaneWords.index(word)) 
           return True
        else:
            return False

    def deleteProfaneWordsAndSave(self):
        '''Deletes any Profane Words files from server'''
        allProfaneWords = fileOperations.getAllProfaneWords()

        list = fileOperations.deleteServerFromList(self.guild_id, allProfaneWords)

        fileOperations.saveProfaneWords(list) 





    def __getStrikes(self):
        '''Returns list of Strikes.'''
        allStrikes = fileOperations.getAllStrikes()

        for server in allStrikes:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        newStrikes = fileOperations.addServerToList(self.guild_id, allStrikes, None)
        fileOperations.saveStrikes(newStrikes)
        return []

    def saveStrikes(self):
        '''Saves any changes to Strikes made to this class'''
        strikesList = []
        for strike in self.strikes:
            strikesList.append(str(strike.memberID) + "|||" + str(strike.strike) + "|||" + str(strike.lastStrike))

        strikesString = fileOperations.joinWithHyphens(strikesList)
        allBirthdays = fileOperations.getAllStrikes()

        list = fileOperations.editServerInList(self.guild_id, allBirthdays, strikesString)

        fileOperations.saveStrikes(list)

    def strikeExists(self, memberID):
        '''Returns bool if member's strike exists on this server.'''
        for strike in self.strikes:
            if strike.memberID == int(memberID):
                return True

        return False

    def getStrike(self, memberID):
        '''Returns type STRIKE or NONE of a member'''
        if self.strikeExists(memberID):
            for strike in self.strikes:
                try:
                    if strike.memberID == int(memberID): return strike
                except Exception as e:
                    print("getStrike Exeption: " + str(e))
                    continue

        else:
            return None

    def addStrike(self, memberID, memberStrike):
        '''Adds a member's strike to this server (returns True). If it already existed, returns False.'''
        if self.strikeExists(memberID): return False

        self.strikes.append(Strike(self.guild, f"{str(memberID)}|||{str(memberStrike)}|||{str(datetime.date.today())}"))
        return True

    def deleteStrike(self, memberID):
        '''Deletes a member's strike from server (returns True). If strike didn't exist for this member, returns False.'''
        if self.strikeExists(memberID):
            for strike in self.strikes:
                if strike.memberID == int(memberID):
                    self.strikes.pop(self.strikes.index(strike))
                    break
            return True

        else:
            return False

    def deleteStrikesAndSave(self):
        '''Deletes any Strike files from server'''
        allStrikes = fileOperations.getAllStrikes()

        list = fileOperations.deleteServerFromList(self.guild_id, allStrikes)

        fileOperations.saveStrikes(list) 






    def __getBirthdays(self):
        '''Returns list of Birthdays.'''
        allBirthdays = fileOperations.getAllBirthdays()

        for server in allBirthdays:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        newBirthdays = fileOperations.addServerToList(self.guild_id, allBirthdays, None)
        fileOperations.saveBirthdays(newBirthdays)

        return []

    def saveBirthdays(self):
        '''Saves any changes to Birthdays made to this class'''
        birthdaysList = []
        for birthday in self.birthdays:
            if birthday.realName != None: 
                birthdaysList.append(str(birthday.memberID) + "|||" + birthday.date + "|||" + birthday.realName)
            else: birthdaysList.append(str(birthday.memberID) + "|||" + birthday.date)

        birthdaysString = fileOperations.joinWithHyphens(birthdaysList)
        allBirthdays = fileOperations.getAllBirthdays()

        list = fileOperations.editServerInList(self.guild_id, allBirthdays, birthdaysString)

        fileOperations.saveBirthdays(list)

    def birthdayExists(self, memberID):
        '''Returns bool if member's birthday exists on this server.'''
        memberID = int(memberID)
        for birthday in self.birthdays:
            if birthday.memberID == memberID:
                return True

        return False

    def getBirthday(self, memberID):
        '''Returns type BIRTHDAY or NONE of a member'''
        memberID = int(memberID)
        if self.birthdayExists(memberID):
            for birthday in self.birthdays:
                if birthday.memberID == int(memberID):
                    return birthday

        else:
            return None

    def addBirthday(self, memberID, date, realName = None):
        '''Adds a member's birthday to this server (returns True). If it already existed, returns False.'''
        if self.birthdayExists(memberID): return False

        if realName != None: self.birthdays.append(Birthday(self.guild, f"{str(memberID)}|||{date}|||{realName}"))
        else: self.birthdays.append(Birthday(self.guild, f"{str(memberID)}|||{date}"))

        return True

    def deleteBirthday(self, memberID):
        '''Deletes a member's birthday from server (returns True). If birthday didn't exist for this member, returns False.'''
        if self.birthdayExists(memberID):
            for birthday in self.birthdays:
                if birthday.memberID == int(memberID):
                    self.birthdays.pop(self.birthdays.index(birthday))
                    break
            
            return True
        else:
            return False

    def deleteBirthdaysAndSave(self):
        '''Deletes any Birthday files from server'''
        allBirthdays = fileOperations.getAllBirthdays()

        list = fileOperations.deleteServerFromList(self.guild_id, allBirthdays)

        fileOperations.saveBirthdays(list) 



    def saveLevels(self):
        '''Saves any level changes made to this class.'''
        self.levels.saveLevels()
        
    def deleteLevelsAndSave(self):
        '''Deletes any Level files from server'''
        allLevels = fileOperations.getAllLevels()

        list = fileOperations.deleteServerFromList(self.guild_id, allLevels)

        fileOperations.saveLevels(list) 

    def saveLevelRewards(self):
        '''Saves any level reward changes made to this class.'''
        self.levels.saveLevelRewards()
        
    def deleteLevelRewardsAndSave(self):
        '''Deletes any Level Reward files from server'''
        allLevels = fileOperations.getAllLevelRewards()

        list = fileOperations.deleteServerFromList(self.guild_id, allLevels)

        fileOperations.saveLevelRewards(list) 



    def __getVCs(self):
        '''Returns list of VCs.'''
        allVCs = fileOperations.getAllVCs()

        for server in allVCs:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        newVCs = fileOperations.addServerToList(self.guild_id, allVCs, None)
        fileOperations.saveVCs(newVCs)

        return []

    def saveVCs(self):
        '''Saves any VC changes made to this class.'''
        VCs = [vc.id for vc in self.VCs] #will save the ids now
        
        allVCs = fileOperations.getAllVCs()

        list = fileOperations.editServerInList(self.guild_id, allVCs, fileOperations.joinWithHyphens(VCs))

        fileOperations.saveVCs(list)

    def VCExists(self, VCID):
        '''Returns bool if vc exists on this server as a join-to-create-vc.'''
        VCID = int(VCID)
        for Vc in self.VCs:
            if Vc.id == VCID:
                return True
        
        return False

    def deleteVCsAndSave(self):
        '''Deletes any VC files from server'''
        allVCs = fileOperations.getAllVCs()

        list = fileOperations.deleteServerFromList(self.guild_id, allVCs)

        fileOperations.saveVCs(list) 



    def __getAutoBans(self):
        '''Returns list of Auto-Bans.'''
        allAutoBans = fileOperations.getAllAutoBans()

        for server in allAutoBans:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        newAutoBans = fileOperations.addServerToList(self.guild_id, allAutoBans, None)
        fileOperations.saveAutoBans(newAutoBans)

        return []

    def saveAutoBans(self):
        '''Saves any Auto-Ban changes made to this class.'''
        autoBans = [ban.saveValue() for ban in self.autoBans]
        
        allAutoBans = fileOperations.getAllAutoBans()

        list = fileOperations.editServerInList(self.guild_id, allAutoBans, fileOperations.joinWithHyphens(autoBans))

        fileOperations.saveAutoBans(list)

    def autoBanExists(self, memberID):
        '''Returns bool if memberID exists in this server as an auto-ban.'''
        memberID = int(memberID)
        for ban in self.autoBans:
            if ban.memberID == memberID:
                return True
        
        return False

    def addAutoBan(self, memberName, memberID, replace = False):
        """
        Adds an auto-ban to this server (returns True). If it already existed, returns False.
        
        Optional Paramaters:
        --------------------
        replace: `bool` (False)
            Whether to replace if it already exists (returns True)
        """
        
        if self.autoBanExists(memberID):
            if replace:
                return self.replaceAutoBan(memberName, memberID)
            else:
                return False
        
        self.autoBans.append(AutoBan(str(memberName) + "|||" + str(memberID)))
        return True
    
    def replaceAutoBan(self, memberName, memberID):
        '''Replaces an auto-ban in this server (returns True). If it didn't exist, returns False (doesn't add it).'''
        if self.autoBanExists(memberID):
            for autoBan in self.autoBans:
                if autoBan.memberID == int(memberID):
                    self.autoBans[self.autoBans.index(autoBan)] = AutoBan(str(memberName) + "|||" + str(memberID))
                    return True
                
            return False
        else:
            return False

    def deleteAutoBan(self, memberID):
        '''Deletes an auto-ban from server (returns True). If auto-ban didn't exist for this member, returns False.'''
        if self.autoBanExists(memberID):
            for autoBan in self.autoBans:
                if autoBan.memberID == int(memberID):
                    self.autoBans.remove(autoBan)
                    break
            
            return True
        else:
            return False

    def deleteAutoBansAndSave(self):
        '''Deletes any Auto-Ban files from server'''
        allBans = fileOperations.getAllAutoBans()

        list = fileOperations.deleteServerFromList(self.guild_id, allBans)

        fileOperations.saveAutoBans(list) 


    def __getInvite(self):
        '''Returns invite (str).'''
        allInvites = fileOperations.getAllInvites()

        for server in allInvites:
            if server.split("———")[0] == self.guild_id:
                data = "".join(server.split("———")[1:])
                if data == "":
                    return None
                return data

        newInvites = fileOperations.addServerToList(self.guild_id, allInvites, None)
        fileOperations.saveInvites(newInvites)

        return None

    def saveInvite(self):
        '''Saves the invite if changes were made to this class.'''       
        allInvites = fileOperations.getAllInvites()

        list = fileOperations.editServerInList(self.guild_id, allInvites, self.invite)

        fileOperations.saveInvites(list)

    def deleteInviteAndSave(self):
        '''Deletes Invite files from server'''
        allInvites = fileOperations.getAllInvites()

        list = fileOperations.deleteServerFromList(self.guild_id, allInvites)

        fileOperations.saveInvites(list) 

class Card:
    '''TYPE CARD → Cards → contains the card title (str | None), description (str | None), and color (str | None)'''
    def __init__(self, package: dict[str]):
        self.title = package['title']
        self.description = package['description']
        self.color = package['color']
        self.enabled = package['enabled']
    
    def saveValue(self):
        package = {
            'title': self.title,
            'description': self.description,
            'color': self.color,
            'enabled': self.enabled
        }
        
        return package

    def getDiscordColor(self):
        return getDiscordColorFromString(self.color)

    def embed(self):
        embed = nextcord.Embed(title = self.title, description = self.description, color = self.getDiscordColor())
        return embed

class Member:
    '''Manages Members. Requires a member_id, and you can access/save any saved data.'''
    def __init__(self, member_id):
        self.member_id = str(member_id)
        
        self.DEFAULTS = {
            'dms': True,
            'levelCard': {
                'title': 'Yum... Levels',
                'description': 'Level [level]!',
                'color': 'Purple',
                'enabled': False
            },
            'joinCard': {
                'title': 'About Me',
                'description': 'I am human',
                'color': 'Green',
                'enabled': False
            }
        }
        
        #store get the data for member
        member = self.__getMember()
        nextcord.Color.green()
        
        #store information
        self.dmsEnabledBool = member['dms'] #bool
        self.levelCard = Card(member['levelCard'])
        self.joinCard = Card(member['joinCard'])
        
        
        #in case we are still referencing level anywhere, let's keep it in
        self.level = 100 
        """DEPRICATED!!! DO NOT USE!!!"""
        
    def __getMember(self):
        '''Returns list of data for the member.'''
        allMembers = fileOperations.getAllMembers()
        
        #find THIS member
        for member in allMembers:
            #member = 123456789———JSON
            if member.split("———")[0] == self.member_id:
                data: dict = json.loads(member.split("———")[1])
                
                return standardizeDictProperties(self.DEFAULTS, data)
            
        #this means that the member does not exist in the records. We should return the defaults.
        return self.DEFAULTS
        
    def save(self):
        '''Saves any changes made to this class'''
        saveFile = dict(self.DEFAULTS)
        
        #set information
        saveFile['dms'] = self.dmsEnabledBool
        saveFile['levelCard'] = self.levelCard.saveValue()
        saveFile['joinCard'] = self.joinCard.saveValue()
        
        allMembers = fileOperations.getAllMembers()
        
        if saveFile == self.DEFAULTS:
            #because they are exactly what we assume them to be, we need to delete the member from the list to save space
            updatedList = fileOperations.deleteServerFromList(self.member_id, allMembers) #we aren't deleting a server, we're deleting a member. But, we can still use this function.
        else:
            #we DO need to save this member
            updatedList = fileOperations.editServerInList(self.member_id, allMembers, json.dumps(saveFile)) #we aren't editing a server, we're editing a member, But, we can still use this function.
            
        fileOperations.saveMembers(updatedList)
        
    def delete(self):
        '''Deletes the member from the members saved in InfiniBot (automatically saves)'''
        allMembers = fileOperations.getAllMembers()
        updatedList = fileOperations.deleteServerFromList(self.member_id, allMembers) #we aren't deleting a server, we're deleting a member. But, we can still use this function.
        fileOperations.saveMembers(updatedList)
        return None


class Message:
    '''Represents an active message'''
    def __init__(self, _type, channel_id, message_id, owner_id, persistent, parameters):
        self.type: str = _type
        self.channel_id: str = channel_id
        self.message_id: str = message_id
        self.owner_id: str = owner_id
        self.persistent: bool = persistent
        self.parameters: list[str] = parameters
        
    def getLink(self, guild_id: int):
        return f"https://discord.com/channels/{guild_id}/{self.channel_id}/{self.message_id}"

class Messages:
    '''Manages Messages Serverwide. Requires a server_id, and you can access/save any saved messages.'''
    def __init__(self, server_id):
        self.guild_id = server_id
        self.MESSAGE_DATA = {
            "Vote": {
                "list": [],
                "max_active_messages": 10
            },
            "Reaction Role": {
                "list": [],
                "max_active_messages": 10
            },
            "Embed": {
                "list": [],
                "max_active_messages": 20
            }
        }
        
        self._initialized = False

    def initialize(self):
        '''Initializes the Messages class by retrieving all active messages for this server.'''
        messages = self._getAllMessages()
        if messages is not None:
            for _type, data in self.MESSAGE_DATA.items():
                data["list"] = messages.get(_type, [])
                
        self._initialized = True;

    def _getAllMessages(self):
        '''Returns all the messages as a dictionary of message type and list of Message objects.'''
        allServers = fileOperations.getAllMessages()
        messageTypes = list(self.MESSAGE_DATA.keys())

        # Find THIS server
        for server in allServers:
            if server.split("———")[0] == self.guild_id:
                if len(server.split("———")) == 1:
                    return None

                package = {}
                serverMessageTypesSorted = server.split("———")[1].split("$")
                for messageType in serverMessageTypesSorted:
                    messages = messageType.split("#")
                    for message in messages:
                        if message == "":
                            continue

                        parts = message.split("|")
                        path = parts[0].split("/")
                        _type = messageTypes[serverMessageTypesSorted.index(messageType)]
                        message_obj = Message(_type, int(path[0]), int(path[1]), int(parts[1]), True if parts[2] == "T" else False, parts[3:])
                        package.setdefault(_type, []).append(message_obj)
                return package

        # Add the message to the records if it doesn't exist
        allServers = fileOperations.addServerToList(self.guild_id, allServers, None)
        fileOperations.saveMessages(allServers)
        return None

    def add(self, _type, channel_id, message_id, owner_id, persistent=False, parameters = []):
        '''Adds an active message to the server.
        Returns True if successful, False if the type is invalid.'''
        if not self._initialized:
            self.initialize();
        
        if _type not in self.MESSAGE_DATA:
            return False

        parameters = [str(x) for x in parameters]
        _list = self.MESSAGE_DATA[_type]["list"]
        _list.insert(0, Message(_type, channel_id, message_id, owner_id, persistent, parameters))

        max_active_messages = self.MESSAGE_DATA[_type]["max_active_messages"]

        if len(_list) > max_active_messages:
            # Remove some active messages
            num_persistent = sum(1 for message in _list if message.persistent)
            num_non_persistent = len(_list) - num_persistent
        
            num_to_remove = len(_list) - max_active_messages
            if num_non_persistent <= num_to_remove:
                # Remove all non-persistent messages if their count is less than or equal to the number to remove
                _list[:] = [message for message in _list if message.persistent]
            else:
                # Remove oldest non-persistent messages until the count reaches the required limit
                remove_indices = [index for index, message in enumerate(_list) if not message.persistent]
                remove_indices.reverse()  # Reverse the indices to start removing from the end
                remove_indices = remove_indices[:num_to_remove]
                for index in remove_indices:
                    _list.pop(index)

        return True

    def delete(self, message_id):
        '''Deletes a Message with a specific message_id
        Returns True if successful, False if message doesn't exist or error.'''
        if not self._initialized:
            self.initialize();
            
        try:
            message_id = int(message_id)
        except ValueError:
            return False
        
        for _type, data in self.MESSAGE_DATA.items():
            _list: list[Message] = data["list"]
            for message in _list:
                if message.message_id == message_id:
                    _list.remove(message)
                    return True
        return False

    def deleteAllFromChannel(self, channel_id):
        '''Deletes all Messages in a specific channel (requires channel_id)
        Returns True if successful, False if channel doesn't exist or error.'''
        if not self._initialized:
            self.initialize();
            
        try:
            channel_id = int(channel_id)
        except ValueError:
            return False
        
        for _type, data in self.MESSAGE_DATA.items():
            _list: list[Message] = data["list"]
            for message in _list:
                if message.channel_id == channel_id:
                    _list.remove(message)
                    return True
        return True

    def save(self):
        '''Saves all changes made to this class.'''     
            
        serverData = []
        for _type, data in self.MESSAGE_DATA.items():
            _list: list[Message] = data["list"]
            allEncodedMessages = []
            for message in _list:
                persistent = "T" if message.persistent else "F"
                if message.parameters != []:
                    parameters = "|" + "|".join(message.parameters)
                else: 
                    parameters = ""
                
                messageEncoded = f"{message.channel_id}/{message.message_id}|{message.owner_id}|{persistent}{parameters}"
                allEncodedMessages.append(messageEncoded)
                
            serverData.append("#".join(allEncodedMessages))

        serverCompiledData = "$".join(serverData)
        allServers = fileOperations.getAllMessages()
        finalData = fileOperations.editServerInList(self.guild_id, allServers, serverCompiledData)
        fileOperations.saveMessages(finalData)
        
        self.initialize()

    def getAll(self, _type) -> list[Message]: 
        '''Returns the list of active messages of a specific type.
        Returns List if successful, None if the type is invalid.'''
        if not self._initialized:
            self.initialize();
            
        if _type not in self.MESSAGE_DATA:
            return None;
        
        return self.MESSAGE_DATA[_type]["list"]

    def get(self, message_id):
        '''Returns a Message with a specific channel and message_id.
        Returns Message if successful, None if message doesn't exist or error.'''
        if not self._initialized:
            self.initialize();
            
        try:
            message_id = int(message_id)
        except ValueError:
            return None;
        
        for _type, data in self.MESSAGE_DATA.items():
            _list: list[Message] = data["list"]
            for message in _list:
                if message.message_id == message_id:
                    return message;
        return None;

    def countOf(self, _type) -> int:
        '''Returns the total amount of a type of active message that are currently cached (not the max amount)'''
        return len(self.getAll(_type))

    def maxOf(self, _type) -> int:
        '''Returns the max amount of a type of active message'''
        return self.MESSAGE_DATA[_type]["max_active_messages"]
        
    async def checkAll(self):
        '''Checks all active messages to see if any don't exist anymore'''
        if not self._initialized:
            self.initialize();
            
        guild = await bot.fetch_guild(self.guild_id)
        
        for _type, data in self.MESSAGE_DATA.items():
            _list: list[Message] = data["list"]
            for message in _list:
                try:
                    discordChannel = await guild.fetch_channel(message.channel_id)
                    if discordChannel:
                        discordMessage = await discordChannel.fetch_message(message.message_id)
                        if discordMessage:
                            # Message Exists
                            continue
                    else:
                        pass
                except:
                    pass
                    
                # Delete Message
                _list.remove(message)
                    
    def deleteAllAndSave(self):
        '''Deletes any Active Messages files from server'''
        allMessages = fileOperations.getAllMessages()

        list = fileOperations.deleteServerFromList(self.guild_id, allMessages)

        fileOperations.saveMessages(list)


class Main:
    '''Manages Persistent Data and other main functions'''
    def __init__(self):
        self.rawPersistentData = self.__getPersistentData()
        
        self.login_response_guildID = self.rawPersistentData['login_response']['guild']
        self.login_response_channelID = self.rawPersistentData['login_response']['channel']
    
    def __getPersistentData(self):
        rawData = fileOperations.getPersistentData()
        return standardizeDictProperties(fileOperations.PERSISTENTDATADEFAULT, json.loads(rawData))
    
    def savePersistentData(self):
        dataDict = {
            'login_response': {
                'guild': self.login_response_guildID,
                'channel': self.login_response_channelID
            }
        }
        
        dataToSave = standardizeDictProperties(fileOperations.PERSISTENTDATADEFAULT, dataDict)
        fileOperations.savePersistentData(json.dumps(dataToSave))
 
main = Main()       

#Buttons and UI


# CUSTOM VIEWS ==========================================================================================================================================================
# Strikes "Mark Incorrect" Button
class IncorrectButton(nextcord.ui.View):
  def __init__(self):
    super().__init__(timeout = None)
  
  @nextcord.ui.button(label = 'Mark As Incorrect', style = nextcord.ButtonStyle.blurple, custom_id = "mark_as_incorrect")
  async def event(self, button:nextcord.ui.Button, interaction: nextcord.Interaction):
    embed = interaction.message.embeds[0]
    id = embed.footer.text.split(" ")[-1]
    guild = interaction.guild
    member = guild.get_member(int(id))
    
    if member != None:
        button.label = "Marked as Incorrect"
        button.disabled = True

        await interaction.response.edit_message(view=self)

        strike = await giveStrike(guild.id, member.id, None, -1)

        await interaction.followup.send(embed = nextcord.Embed(title = "Strike Refunded", description = f"{interaction.user} refunded a strike to {member}\n\n{member} is now at {strike} strike(s).", color =  nextcord.Color.green()))
    else:
        button.label = "Member no longer exists"
        button.disabled = True
    
    self.stop()
    
# Deleted Message Logs "Show More" Button
class ShowMoreButton(nextcord.ui.View):
  def __init__(self):
    super().__init__(timeout = None)
    self.possibleEmbeds = [
        ["Possible Margin For Error", "Infinibot is relying on an educated guess regarding the deleter of this message. Thus, there *is* a margin for error (In testing, about 2%)."],
        ["Possible Margin For Error", "Because the message can not be retrieved, Infinibot is relying on an educated guess regarding the author and deleter of this message. Thus, there *is* a margin for error (In testing, about 6.5%)."],
        ["Unable to find specifics", "Infinibot is unable to find any info regarding this message because of Discord's limitations.\n\nThe user probably deleted thier own message."],
        ["Unable to find specifics", "Infinibot is unable to find the deleter because of Discord's limitations.\n\nThe user probably deleted thier own message."]
    ]
  
  @nextcord.ui.button(label = 'Show More', style = nextcord.ButtonStyle.gray, custom_id = "show_more")
  async def event(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
    embed = interaction.message.embeds[0]
    code = embed.footer.text.split(" ")[-1]
    index = int(code) - 1
    
    embed = nextcord.Embed(title = "More Information", color = nextcord.Color.red())
    embed.add_field(name = self.possibleEmbeds[index][0], value = self.possibleEmbeds[index][1])
    
    button.disabled = True

    allEmbeds = interaction.message.embeds
    allEmbeds.append(embed)

    await interaction.response.edit_message(view=self, embeds = allEmbeds)
    
    self.stop()
  
# Error "Why Administrator Privileges?" Button
class ErrorWhyAdminPrivilegesButton(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
    
    @nextcord.ui.button(label = "Why Administrator Privileges?", style = nextcord.ButtonStyle.gray, custom_id = "why_administrator_privileges")
    async def event(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        generalMessage = f"\n\n**Why Administrator Privileges?**\nSome of InfiniBot's features work best when it is able to view every channel and have all its required permissions in every channel. An alternative to Administrator is to give InfiniBot the following permissions in every channel:{requiredPermissions}"
        embed = interaction.message.embeds[0]
        embed.description += generalMessage
        
        button.disabled = True
        
        await interaction.response.edit_message(view = self, embed = embed)



class ReactionRoleView(nextcord.ui.View):
    def __init__(self, roles: list[nextcord.Role]):
        super().__init__()

        options = []
        for role in roles:
            options.append(nextcord.SelectOption(label = role.name))
            
        self.selection = None
        
        if len(roles) < 10:
            maxValues = len(roles)
        else:
            maxValues = 10
        
        self.select = nextcord.ui.Select(placeholder = "Select Up to 10 Roles", options = options, max_values=maxValues)
        
        self.button = nextcord.ui.Button(label = "Create", style = nextcord.ButtonStyle.blurple)
        self.button.callback = self.createCallback
        
        self.add_item(self.select)
        self.add_item(self.button)
             
    async def createCallback(self, interaction: Interaction):
        self.selection = self.select.values
        self.select.disabled = True
        self.button.disabled = True
        await interaction.response.edit_message(view = self)
        self.stop()
      
class EmbedColorView(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        
        options = ["Red", "Green", "Blue", "Yellow", "White", "Blurple", "Greyple", "Teal", "Purple", "Gold", "Magenta", "Fuchsia"]
                
        selectOptions = []
        for option in options:
            selectOptions.append(nextcord.SelectOption(label = option, value = option))
        
        self.select = nextcord.ui.Select(placeholder = "Choose a color", options = selectOptions)

        self.button = nextcord.ui.Button(label = "Create", style = nextcord.ButtonStyle.blurple)
        self.button.callback = self.createCallback
        
        self.add_item(self.select)
        self.add_item(self.button)
             
    async def createCallback(self, interaction: Interaction):
        self.selection = self.select.values[0]
        self.select.disabled = True
        self.button.disabled = True
        await interaction.response.edit_message(view = self)
        self.stop()
        
class JoinToCreateVCView(nextcord.ui.View):
    def __init__(self, vcs: list[list[str, bool]]):
        super().__init__()
        
        options = []
        for vc in vcs:
            options.append(nextcord.SelectOption(label = vc[0], default = vc[1]))
            
        self.selection = None
        
        if len(vcs) < 10: maxValues = len(vcs)
        else: maxValues = 10
        
        self.select = nextcord.ui.Select(placeholder = "Select Up to 5 Voice Channels", options = options, max_values = maxValues, min_values = 0)
        if maxValues == 0: self.select.disabled = True
        
        self.button = nextcord.ui.Button(label = "Confirm", style = nextcord.ButtonStyle.blurple)
        self.button.callback = self.continueCallback
        
        self.add_item(self.select)
        self.add_item(self.button)
        
        
    async def continueCallback(self, interaction: Interaction):
        self.selection = self.select.values
        self.select.disabled = True
        self.button.disabled = True
        await interaction.response.edit_message(view = self)
        self.stop()

class ConfirmationView(nextcord.ui.View):
    def __init__(self, yesBtnText = "Yes", noBtnText = "No"):
        super().__init__(timeout = None)
        
        self.choice = None
        
        self.noButton = nextcord.ui.Button(label = noBtnText, style = nextcord.ButtonStyle.red)
        self.noButton.callback = self.noButtonCallback
        self.add_item(self.noButton)
        
        self.yesButton = nextcord.ui.Button(label = yesBtnText, style = nextcord.ButtonStyle.green)
        self.yesButton.callback = self.yesButtonCallback
        self.add_item(self.yesButton)
        
    async def noButtonCallback(self, interaction: Interaction):
        self.noButton.disabled = True
        self.yesButton.disabled = True
        
        self.choice = False
        await interaction.response.edit_message(view = self)
        self.stop()
        
    async def yesButtonCallback(self, interaction: Interaction):
        self.noButton.disabled = True
        self.yesButton.disabled = True
        
        self.choice = True
        await interaction.response.edit_message(view = self)
        self.stop()



class SupportView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = supportServerLink)
        self.add_item(supportServerBtn)

class InviteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        inviteBtn = nextcord.ui.Button(label = "Add to Your Server", style = nextcord.ButtonStyle.link, url = inviteLink)
        self.add_item(inviteBtn)

class SupportAndInviteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = supportServerLink)
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Add To Your Server", style = nextcord.ButtonStyle.link, url = inviteLink)
        self.add_item(inviteBtn)

class SupportInviteAndTopGGVoteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = supportServerLink)
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Invite", style = nextcord.ButtonStyle.link, url = inviteLink)
        self.add_item(inviteBtn)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote for InfiniBot", style = nextcord.ButtonStyle.link, url = topggVoteLink)
        self.add_item(topGGVoteBtn)
        
class SupportInviteAndTopGGReviewView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = supportServerLink)
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Invite", style = nextcord.ButtonStyle.link, url = inviteLink)
        self.add_item(inviteBtn)
        
        topGGReviewBtn = nextcord.ui.Button(label = "Leave a Review", style = nextcord.ButtonStyle.link, url = topggReviewLink)
        self.add_item(topGGReviewBtn)

class TopGGVoteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote", style = nextcord.ButtonStyle.link, url = topggVoteLink)
        self.add_item(topGGVoteBtn)
        
class TopGGAll(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        topGG = nextcord.ui.Button(label = "Visit on Top.GG", style = nextcord.ButtonStyle.link, url = topggLink)
        self.add_item(topGG)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote for InfiniBot", style = nextcord.ButtonStyle.link, url = topggVoteLink)
        self.add_item(topGGVoteBtn)
        
        topGGReviewBtn = nextcord.ui.Button(label = "Leave a Review", style = nextcord.ButtonStyle.link, url = topggReviewLink)
        self.add_item(topGGReviewBtn)

class SupportandPermissionsCheckView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = supportServerLink)
        self.add_item(supportServerBtn)

        permissionsCheckBtn = nextcord.ui.Button(label = "Check Permissions", style = nextcord.ButtonStyle.gray)
        permissionsCheckBtn.callback = check_infinibot_permissions
        self.add_item(permissionsCheckBtn)
        
class SupportInviteTopGGVoteAndPermissionsCheckView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = supportServerLink)
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Invite", style = nextcord.ButtonStyle.link, url = inviteLink)
        self.add_item(inviteBtn)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote for InfiniBot", style = nextcord.ButtonStyle.link, url = topggVoteLink)
        self.add_item(topGGVoteBtn)
        
        permissionsCheckBtn = nextcord.ui.Button(label = "Check Permissions", style = nextcord.ButtonStyle.gray)
        permissionsCheckBtn.callback = check_infinibot_permissions
        self.add_item(permissionsCheckBtn)


# CUSTOM MODALS ==========================================================================================================================================================
class VotingModal(nextcord.ui.Modal):
    def __init__(self, interaction, type, options = None):
        super().__init__(title = "Create a Vote")
        self.interaction = interaction
        self.type = type
        self.options = options

        self.titleTextInput = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, placeholder = "What do we want to have for dinner?", required = True)
        self.descriptionTextInput = nextcord.ui.TextInput(label = "Description", style = nextcord.TextInputStyle.paragraph, placeholder = "Do we want Pizza or Steak?\nGive your vote below:", required = False)
        self.optionsTextInput = nextcord.ui.TextInput(label = "Options (Seperate with \", \") (Max: 10)", style = nextcord.TextInputStyle.short, placeholder = "Yes, No, Maybe", required = True)
        
        
        self.add_item(self.titleTextInput)
        self.add_item(self.descriptionTextInput)
        if self.type != "Custom": self.add_item(self.optionsTextInput)

    async def callback(self, interaction: Interaction):
        if self.type != "Custom":
            await createVote(self.interaction, self.titleTextInput.value, self.descriptionTextInput.value, self.optionsTextInput.value, self.type)
        else:
            await createVote(self.interaction, self.titleTextInput.value, self.descriptionTextInput.value, self.options, self.type)    
        
class ReactionRoleModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(title = "Create a Reaction Role")
        
        self.titleValue = None
        self.descriptionValue = None
        
        self.titleTextInput = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, placeholder = "Get access to the server", required = True)
        self.descriptionTextInput = nextcord.ui.TextInput(label = "Description", style = nextcord.TextInputStyle.paragraph, placeholder = "Grab your roles below:", required = False)
        
        self.add_item(self.titleTextInput)
        self.add_item(self.descriptionTextInput)

    async def callback(self, interaction: Interaction):
        self.titleValue = self.titleTextInput.value
        self.descriptionValue = self.descriptionTextInput.value
        self.stop()

class EmbedModal(nextcord.ui.Modal):        
    def __init__(self):
        super().__init__(title = "Create Embed")
   
        self.titleTextInput = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, required = True, max_length=256)
        self.descriptionTextInput = nextcord.ui.TextInput(label = "Description", style = nextcord.TextInputStyle.paragraph, required = True, max_length = 4000)
        
        
        self.add_item(self.titleTextInput)
        self.add_item(self.descriptionTextInput)

    async def callback(self, interaction: Interaction):
        self.titleValue = self.titleTextInput.value
        self.descriptionValue = self.descriptionTextInput.value  
        self.stop()
             
class AdminModal(nextcord.ui.Modal):        
    def __init__(self):
        super().__init__(title = "Send Message to All Guilds")
   
        self.titleTextInput = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, required = True)
        self.descriptionTextInput = nextcord.ui.TextInput(label = "Description", style = nextcord.TextInputStyle.paragraph, required = True)
        
        
        self.add_item(self.titleTextInput)
        self.add_item(self.descriptionTextInput)

    async def callback(self, interaction: Interaction):
        self.titleValue = self.titleTextInput.value
        self.descriptionValue = self.descriptionTextInput.value  
        self.stop()

class IssueReportModal(nextcord.ui.Modal):        
    def __init__(self, member: nextcord.Member):
        super().__init__(title = "Report An Issue")
        self.member = member

        self.problemTextInput = nextcord.ui.TextInput(label = "Describe The Problem", style = nextcord.TextInputStyle.paragraph, required = True, max_length=1024)
        self.historyTextInput = nextcord.ui.TextInput(label = "What Happened Before?", style = nextcord.TextInputStyle.paragraph, required = True, max_length=1024)
        self.notesTextInput = nextcord.ui.TextInput(label = "Other notes:", style = nextcord.TextInputStyle.paragraph, required = False, max_length=1024)
        
        self.add_item(self.problemTextInput)
        self.add_item(self.historyTextInput)
        self.add_item(self.notesTextInput)

    async def callback(self, interaction: Interaction): 
        server = None
        for guild in bot.guilds:
            if guild.id == infinibotGuild: server = guild
        
        if server == None:
            print("ERROR: CANNOT FIND INFINIBOT SERVER!!!")
            self.stop()
            return
        
        embed = nextcord.Embed(title = "New Issue Report Submission:", description = f"Member: {self.member}\nMember ID: {self.member.id}\nServer: {interaction.guild.name}\nServer ID: {interaction.guild.id}", color = nextcord.Color.orange())
        embed.add_field(name = "Describe the Problem", value = self.problemTextInput.value)
        embed.add_field(name = "What Happened Before?", value = self.historyTextInput.value)
        if self.notesTextInput.value != "": embed.add_field(name = "Other notes:", value = self.notesTextInput.value)
        
        channel = server.get_channel(issueReportChannel)
        await channel.send(embed = embed)
        
        await interaction.response.send_message(embed = nextcord.Embed(title = "Issue Report Submitted", description = f"Join us at {supportServerLink} or contact at infinibotassistance@gmail.com. and see if your issue will be added to https://discord.com/channels/1009127888483799110/1009136603064713309", color = nextcord.Color.green()), ephemeral=True, view = SupportView())
        
class IdeaReportModal(nextcord.ui.Modal):        
    def __init__(self, member: nextcord.Member):
        super().__init__(title = "Submit an Idea")
        self.member = member

        self.ideaTextInput = nextcord.ui.TextInput(label = "What's your idea?", style = nextcord.TextInputStyle.paragraph, required = True, max_length=1024)
        self.howItWouldWorkTextInput = nextcord.ui.TextInput(label = "How would it work?", style = nextcord.TextInputStyle.paragraph, required = True, max_length=1024)
        self.notesTextInput = nextcord.ui.TextInput(label = "Other notes:", style = nextcord.TextInputStyle.paragraph, required = False, max_length=1024)
        
        self.add_item(self.ideaTextInput)
        self.add_item(self.howItWouldWorkTextInput)
        self.add_item(self.notesTextInput)

    async def callback(self, interaction: Interaction): 
        server = None
        for guild in bot.guilds:
            if guild.id == infinibotGuild: server = guild
        
        if server == None:
            print("ERROR: CANNOT FIND INFINIBOT SERVER!!!")
            self.stop()
            return
        
        embed = nextcord.Embed(title = "New Idea Submission:", description = f"Member: {self.member}\nMember ID: {self.member.id}\nServer: {interaction.guild.name}\nServer ID: {interaction.guild.id}", color = nextcord.Color.green())
        embed.add_field(name = "How would it work?", value = self.ideaTextInput.value)
        embed.add_field(name = "What Happened Before?", value = self.howItWouldWorkTextInput.value)
        if self.notesTextInput.value != "": embed.add_field(name = "Other notes:", value = self.notesTextInput.value)
        
        channel = server.get_channel(submissionChannel)
        await channel.send(embed = embed)
        
        await interaction.response.send_message(embed = nextcord.Embed(title = "Idea Submitted", description = f"Join us at {supportServerLink} or contact at infinibotassistance@gmail.com. and see if your idea will be a reality! You can view our road map here: https://discord.com/channels/1009127888483799110/1009134131835322448", color = nextcord.Color.green()), ephemeral=True, view = SupportView())
 
class GeneralInputModal(nextcord.ui.Modal):
    def __init__(self, title, label, style = nextcord.TextInputStyle.short, max_length = 1024, required = True):
        super().__init__(title = title)
        
        self.response = None
        
        self.textInput = nextcord.ui.TextInput(label = label, style = style, max_length = max_length, required = required)
        
        self.add_item(self.textInput)
        
    async def callback(self, interaction: Interaction):
        self.response = self.textInput.value
        self.stop()


# COMPLICATED UI ==========================================================================================================================================================
class SelectView(nextcord.ui.View):
    def __init__(self, title: str, description: str, options: list[nextcord.SelectOption], returnCommand, embedColor: nextcord.Color = nextcord.Color.blue(), embedFields = [], placeholder: str = None, continueButtonLabel = "Continue", cancelButtonLabel = "Cancel", preserveOrder = False):
        """Creates a select view that has pages if needed.

        Args:
            title (str): Title of the Embed
            description (str): Description of the Embed
            options (list[nextcord.SelectOption]): Options of the Select
            returnCommand (def(str | None)): Command to call when finished.
            embedColor (nextcord.Color, optional): Color of the Embed. Defaults to nextcord.Color.blue().
            embedFields (list, optional): Fields of the Embed. Defaults to [].
            placeholder (str, optional): Placeholder for the Select. Defaults to None.
            continueButtonLabel (str, optional): Continue Button Label. Defaults to "Continue".
            cancelButtonLabel (str, optional): Cancel Button Label. Defaults to "Cancel".
            preserveOrder (bool, optional): Preserves the order of options. Defaults to "False", where the options will be alphabetized
        """
        
        super().__init__()
        self.page = 0
        self.title = title
        self.description = description
        self.options = options
        self.returnCommand = returnCommand
        self.embedColor = embedColor
        self.embedFields = embedFields
        
        #Confirm objects
        if self.options == None or self.options == []:
            raise ValueError(f"'options' must be a 'list' with one or more 'nextcord.SelectOption' items.")       
        if type(self.options) != list:
            raise ValueError(f"'options' must be of type 'list'. Recieved type '{type(self.options)}'")        
        for option in self.options:
            if type(option) != nextcord.SelectOption:
                raise ValueError(f"'options' must only contain 'nextcord.SelectOption' items. Countained 1+ '{type(option)}'")
        
        #Alphabetize options
        if not preserveOrder:
            self.options = sorted(self.options, key=lambda option: [option.value != "__NONE__", option.label.lower()])
        
        
        #parse options into different pages
        self.selectOptions = [[]]
        xindex = 0
        yindex = 0
        for option in self.options:
            if yindex == 25:    # <--------------------------- Change the Threshold HERE!!!!
                #create new page
                self.selectOptions.append([])
                xindex += 1
                yindex = 0
            #add to current page
            self.selectOptions[xindex].append(option)
            yindex += 1
            
        del xindex, yindex
        
        #add select menu
        self.Select = nextcord.ui.Select(options = [nextcord.SelectOption(label = "PLACEHOLDER!!!")], placeholder=placeholder)
        self.add_item(self.Select)
        
        #add buttons
        self.backButton = nextcord.ui.Button(emoji = "◀️", style = nextcord.ButtonStyle.gray, row = 1, disabled = True)
        self.backButton.callback = self.back
        
        self.nextButton = nextcord.ui.Button(emoji = "▶️", style = nextcord.ButtonStyle.gray, row = 1)
        self.nextButton.callback = self.next
        
        if len(self.selectOptions) > 1: #if we need pages
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
        
        if len(self.selectOptions) == 1: #if we don't need pages...
            self.embed = nextcord.Embed(title = self.title, description = self.description, color = self.embedColor)
        else:
            self.embed = nextcord.Embed(title = self.title, description = self.description + f"\n\n**Page {page + 1} of {len(self.selectOptions)}**\n{self.selectOptions[page][0].label} → {self.selectOptions[page][-1].label}", color = self.embedColor)
        
        for field in self.embedFields:
            self.embed.add_field(name = field.name, value = field.value, inline = field.inline)
            
            
            
        self.Select.options = self.selectOptions[page]

        if interaction != None: 
            await interaction.response.edit_message(embed = self.embed, view = self) 
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
    
    
class Dashboard(nextcord.ui.View):
    def __init__(self, interaction: Interaction):
        super().__init__(timeout = None)
        
        self.moderationBtn = self.ModerationButton(self)
        self.add_item(self.moderationBtn)
        
        self.loggingBtn = self.LoggingButton(self, interaction.guild.id)
        self.add_item(self.loggingBtn)
        
        self.levelingBtn = self.LevelingButton(self, interaction.guild.id)
        self.add_item(self.levelingBtn)
        
        self.joinLeaveMessagesBtn = self.JoinLeaveMessagesButton(self)
        self.add_item(self.joinLeaveMessagesBtn)
        
        self.birthdaysBtn = self.BirthdaysButton(self)
        self.add_item(self.birthdaysBtn)
        
        self.defaultRolesBtn = self.DefaultRolesButton(self)
        self.add_item(self.defaultRolesBtn)
        
        self.joinToCreateVCsButton = self.JoinToCreateVCsButton(self)
        self.add_item(self.joinToCreateVCsButton)
        
        self.bansButton = self.AutoBansButton(self)
        self.add_item(self.bansButton)
        
        self.activeMessagesBtn = self.ActiveMessagesButton(self)
        self.add_item(self.activeMessagesBtn)
        
        self.enableDisableBtn = self.EnableDisableButton(self)
        self.add_item(self.enableDisableBtn)

    async def setup(self, interaction: Interaction):
        for child in self.children: del child
        self.__init__(interaction)
        
        description = """Welcome to the InfiniBot Dashboard! Choose a feature to setup / edit:"""
        
        # On Mobile, extra spaces cause problems. We'll get rid of them here:
        description = standardizeStrIndention(description)
        
        embed = nextcord.Embed(title = "Dashboard", description = description, color = nextcord.Color.blue())
        try: await interaction.response.edit_message(embed = embed, view = self)
        except: await interaction.response.send_message(embed = embed, view = self, ephemeral=True)
              

    class ModerationButton(nextcord.ui.Button):
        def __init__(self, outer):
            
            super().__init__(label = "Moderation", style = nextcord.ButtonStyle.gray)
            self.outer = outer 
          
        class ModerationView(nextcord.ui.View):
            def __init__(self, outer, guild_id):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.ProfaneModerationBtn = self.ProfaneModerationButton(self, guild_id)
                self.add_item(self.ProfaneModerationBtn)
                
                self.spamModerationBtn = self.SpamModerationButton(self, guild_id)
                self.add_item(self.spamModerationBtn)
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1) 
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
            async def setup(self, interaction: Interaction):
                for child in self.children: 
                    del child
                    self.__init__(self.outer, interaction.guild_id)
                
                embed = nextcord.Embed(title = "Dashboard - Moderation", description = "Choose a feature to setup / edit.", color = nextcord.Color.blue())
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class ProfaneModerationButton(nextcord.ui.Button):
                def __init__(self, outer, guild_id):
                    server = Server(guild_id)
                    super().__init__(label = "Profanity", style = nextcord.ButtonStyle.gray, disabled = (not server.profanityBool))
                    del server
                    self.outer = outer
                    
                class ProfaneModerationView(nextcord.ui.View): #Moderation Window -----------------------------------------------------
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.wordsBtn = self.FilteredWordsButton(self)
                        self.add_item(self.wordsBtn)
                        
                        self.manageMembersBtn = self.ManageMembersButton(self)
                        self.add_item(self.manageMembersBtn)
                        
                        self.timeoutDurationBtn = self.TimeoutDurationButton(self)
                        self.add_item(self.timeoutDurationBtn)
                        
                        self.strikeExpireTimeBtn = self.StrikeExpireTimeButton(self)
                        self.add_item(self.strikeExpireTimeBtn)
                        
                        self.maxStrikesBtn = self.MaxStrikesButton(self)
                        self.add_item(self.maxStrikesBtn)
                        
                        self.adminChannelBtn = self.AdminChannelButton(self)
                        self.add_item(self.adminChannelBtn)
                        
                        
                        self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 3) 
                        self.backBtn.callback = self.backBtnCallback
                        self.add_item(self.backBtn)
                                    
                    async def setup(self, interaction: Interaction):
                        for child in self.children: 
                            del child 
                            self.__init__(self.outer)
                        
                        server = Server(interaction.guild.id)
                        if server.strikeExpireTime != None: strikeExpireTime =  str(server.strikeExpireTime) + " days"
                        else: strikeExpireTime = "Disabled"
                        if server.adminChannel: adminChannelName = server.adminChannel.mention
                        else: adminChannelName = "None"
                        
                        #warnings
                        if server.adminChannel == None: 
                            warning = "**WARNING!!! THE ADMIN CHANNEL IS NOT SET! MODERATION WILL NOT WORK AS EXPECTED!!!**"
                            self.adminChannelBtn.style = nextcord.ButtonStyle.blurple
                        else: 
                            warning = ""
                            self.adminChannelBtn.style = nextcord.ButtonStyle.gray
                        
                        embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity", description = f"{warning}\n\n**Settings**\nTimeout Duration: {server.profanityTimeoutTime}\nStrike Expire Time: {strikeExpireTime}\nMaximum Strikes: {server.maxStrikes}\nAdmin Channel: {adminChannelName}\n\n**Choose a feature to setup / edit.**", color = nextcord.Color.blue())
                        try: await interaction.response.edit_message(embed = embed, view = self)
                        except: await interaction.edit_original_message(embed = embed, view = self)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)

                    class FilteredWordsButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Filtered Words", style = nextcord.ButtonStyle.gray)
                            self.outer = outer           
                            
                        class FilteredWordsView(nextcord.ui.View): #Filtered Words Window -----------------------------------------------------
                            def __init__(self, outer):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                self.addWordBtn = self.AddWordButton(self)
                                self.add_item(self.addWordBtn)
                                
                                self.deleteWordBtn = self.DeleteWordButton(self)
                                self.add_item(self.deleteWordBtn)
                                
                                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                                self.backBtn.callback = self.backBtnCallback
                                self.add_item(self.backBtn)
                                
                            async def setup(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                
                                self.embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity - Filtered Words", description = "Moderation Word Settings\n\nThe following words are filtered by InfiniBot", color = nextcord.Color.blue())
                                ProfaneWords = server.ProfaneWords
                                if ProfaneWords == []: ProfaneWords.append("You don't have any filtered words set. Add some!")
                                else: ProfaneWords = sorted(ProfaneWords)
                                
                                self.embed.add_field(name = "Filtered Words", value = "||"+"\n".join(ProfaneWords)+"||")
                                
                                try: await interaction.response.edit_message(embed = self.embed, view = self)
                                except: await interaction.edit_original_message(embed = self.embed, view = self)
                                                           
                            async def backBtnCallback(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                                await interaction.edit_original_message(view = self.outer)
                                                                            
                            class AddWordButton(nextcord.ui.Button):
                                def __init__(self, outer):
                                    super().__init__(label = "Add Word", style = nextcord.ButtonStyle.gray)
                                    self.outer = outer
                                    
                                class getWordModal(nextcord.ui.Modal): #Add Word Modal -----------------------------------------------------
                                    def __init__(self, outer):
                                        super().__init__(title = "Add Word")
                                        self.outer = outer
                                        self.response = None
                                        
                                        self.input = nextcord.ui.TextInput(label = "Word to filter", style = nextcord.TextInputStyle.short, placeholder="Must have no suffixes. Ex: walking → walk, jumped → jump")
                                        self.add_item(self.input)
                                        
                                    async def callback(self, interaction: Interaction):
                                        response = addWord(self.input.value, interaction.guild.id)
                                        if response == True:
                                            self.response = self.input.value
                                            self.stop()
                                        else:
                                            await interaction.response.send_message(embed = response, ephemeral=True)
                                            self.stop()
                                        
                                async def callback(self, interaction: Interaction):
                                    modal = self.getWordModal(self)
                                    await interaction.response.send_modal(modal)
                                    await modal.wait()
                                    
                                    await self.outer.setup(interaction)
                                                                           
                            class DeleteWordButton(nextcord.ui.Button):
                                def __init__(self, outer):
                                    super().__init__(label = "Delete Word", style = nextcord.ButtonStyle.gray)
                                    self.outer = outer                     
                                        
                                async def callback(self, interaction: Interaction):
                                    server = Server(interaction.guild.id)
                                    ProfaneWords = [nextcord.SelectOption(label = x) for x in server.ProfaneWords]
                                    await SelectView(self.outer.embed.title, self.outer.embed.description, ProfaneWords, self.selectionCallback, embedColor = self.outer.embed.color, embedFields = self.outer.embed.fields, continueButtonLabel = "Delete").setup(interaction)
                                    
                                async def selectionCallback(self, interaction: Interaction, selection):
                                    if selection != None: deleteWord(selection, interaction.guild.id)
                                    await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction): #Filtered Words Button Callback ————————————————————————————————————————————————————————————
                            view = self.FilteredWordsView(self.outer)
                            await view.setup(interaction)
                            
                    class ManageMembersButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Manage Members", style = nextcord.ButtonStyle.gray)
                            self.outer = outer                 
                            
                        class ManageMembersView(nextcord.ui.View):#Strikes Window -----------------------------------------------------
                            def __init__(self, outer):
                                super().__init__(timeout=None)
                                self.outer = outer
                                
                                self.editStrikesBtn = self.EditStrikesButton(self)
                                self.add_item(self.editStrikesBtn)
                                
                                self.deleteAllStrikesBtn = self.DeleteAllStrikesButton(self)
                                self.add_item(self.deleteAllStrikesBtn)
                                
                                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                                self.backBtn.callback = self.backBtnCallback
                                self.add_item(self.backBtn)
                                
                            async def setup(self, interaction: Interaction):
                                self.dataSorted = self.getMembers(interaction, limit = 25)
                                
                                dataString = []
                                for index in self.dataSorted:
                                    dataString.append(index[0])

                                self.embed = nextcord.Embed(title = "Dashboard - Moderation - Profanity - Manage Members", color = nextcord.Color.blue())
                                self.embed.add_field(name = "Strike - Member", value = "\n".join(dataString), inline = True)
                                
                                await interaction.response.edit_message(embed = self.embed, view = self)
                            
                            def getMembers(self, interaction: Interaction, limit: str = None):
                                server = Server(interaction.guild_id)
                                
                                data = []
                                for member in interaction.guild.members:
                                    if limit != None and (len(data) + 1) > limit: 
                                        sortedMembers = sorted(data, key = lambda x: (x[0], x[1]), reverse = True)
                                        for data in sortedMembers:
                                            yield [f"{data[0]} - {data[1]}", data[2]]
                                        yield [f"{len(interaction.guild.members) - limit - 1} more. Use */get_strikes* to get a specific member's strike(s)", None]
                                        return
                                    
                                    if member.bot: continue
                                    
                                    strike = server.getStrike(member.id)
                                    if member.nick != None: Member = f"{member} ({member.nick})"
                                    else: Member = f"{member}"
                                    
                                    if type(strike) == Strike: data.append([strike.strike, Member, member.id])
                                    else: data.append([0, Member, member.id])
                                    
                                for data in sorted(data, key = lambda x: (x[0], x[1]), reverse = True):
                                    yield [f"{data[0]} - {data[1]}", data[2]]
                        
                            async def backBtnCallback(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                                await interaction.edit_original_message(view = self.outer)
                                
                            class EditStrikesButton(nextcord.ui.Button):
                                def __init__(self, outer):
                                    super().__init__(label = "Edit", style = nextcord.ButtonStyle.gray)
                                    self.outer = outer
                                    
                                class EditStrikesView(nextcord.ui.View):#Edit Strikes Window -----------------------------------------------------
                                    def __init__(self, outer, guild: nextcord.Guild, userSelection):
                                        super().__init__(timeout=None)
                                        self.outer = outer
                                        
                                        server = Server(guild.id)
                                        
                                        strikeSelectOptions: list[nextcord.SelectOption] = [nextcord.SelectOption(label = str(number)) for number in range(0, int(server.maxStrikes) + 1)]
                                        strikeSelectOptions.reverse()
                                        self.strikeSelect = nextcord.ui.Select(options = strikeSelectOptions, placeholder = "Choose a Strike")
                                        self.add_item(self.strikeSelect)
                                        
                                        self.cancelBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                                        self.cancelBtn.callback = self.cancelBtnCallback
                                        self.add_item(self.cancelBtn)
                                        
                                        self.confirmBtn = self.ConfirmButton(self.outer, self, userSelection)
                                        self.add_item(self.confirmBtn)
                                        
                                    async def setup(self, interaction: Interaction):
                                        Embed = self.outer.embed
                                        Embed.description = "Select a Strike"
                                        await interaction.response.edit_message(embed = Embed, view = self)
                                        
                                    async def cancelBtnCallback(self, interaction: Interaction):
                                        await self.outer.setup(interaction)
                                        
                                    class ConfirmButton(nextcord.ui.Button):
                                        def __init__(self, outer, parent, userSelection):
                                            super().__init__(label = "Confirm", style = nextcord.ButtonStyle.blurple)
                                            self.outer = outer
                                            self.parent = parent
                                            self.userSelection = userSelection
                                            
                                        async def callback(self, interaction: Interaction):
                                            member = self.userSelection
                                            strikes = self.parent.strikeSelect.values
                                            
                                            if strikes == []:
                                                return
                                            
                                            strike = int(strikes[0])
                                            
                                            server = Server(interaction.guild.id)
                                            discordMember = server.getStrike(member)
                                            if strike > 0:
                                                if discordMember != None: discordMember.strike = strike
                                                else: server.addStrike(member, strike)
                                                server.saveStrikes()
                                            else:
                                                if discordMember != None: 
                                                    server.deleteStrike(member)
                                                    server.saveStrikes()
                                                    
                                            await self.outer.setup(interaction)
                                                            
                                async def callback(self, interaction: Interaction):# Edit Strikes Callback and First Step ————————————————————————————————————————————————————————————
                                    #getting people
                                    memberSelectOptions = []
                                    for data in self.outer.getMembers(interaction):
                                        memberSelectOptions.append(nextcord.SelectOption(label = data[0], value = data[1]))
                                    
                                    await SelectView(self.outer.embed.title, "Select a Member", memberSelectOptions, self.callbackPart1, embedColor = self.outer.embed.color, embedFields = self.outer.embed.fields, placeholder = "Choose a Member", continueButtonLabel = "Next", preserveOrder = True).setup(interaction)
                                    
                                async def callbackPart1(self, interaction: Interaction, selection):
                                    if selection == None: #if they canceled
                                        await self.outer.setup(interaction)
                                    else:
                                        await self.EditStrikesView(self.outer, interaction.guild, selection).setup(interaction)
                                                        
                            class DeleteAllStrikesButton(nextcord.ui.Button):
                                def __init__(self, outer):
                                    super().__init__(label = "Clear", style = nextcord.ButtonStyle.gray)
                                    self.outer = outer
                                    
                                class DeleteAllStrikesView(nextcord.ui.View):
                                    def __init__(self, outer):
                                        super().__init__(timeout = None)
                                        self.outer = outer
                                        
                                        self.noBtn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
                                        self.noBtn.callback = self.noBtnCommand
                                        self.add_item(self.noBtn)
                                        
                                        self.yesBtn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
                                        self.yesBtn.callback = self.yesBtnCommand
                                        self.add_item(self.yesBtn)
                                        
                                    async def setup(self, interaction: Interaction):
                                        embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will reset all strikes in the server to 0.\nThis action cannot be undone.", color = nextcord.Color.blue())
                                        await interaction.response.edit_message(embed = embed, view = self)
                                        
                                    async def noBtnCommand(self, interaction: Interaction):
                                        await self.outer.setup(interaction)
                                        
                                    async def yesBtnCommand(self, interaction: Interaction):
                                        server = Server(interaction.guild.id)
                                        server.strikes = []
                                        server.saveStrikes()
                                        await self.outer.setup(interaction)
                                    
                                async def callback(self, interaction: Interaction):
                                    await self.DeleteAllStrikesView(self.outer).setup(interaction)
                            
                        async def callback(self, interaction: Interaction): # Strikes Callback ————————————————————————————————————————————————————————————
                            view = self.ManageMembersView(self.outer)
                            await view.setup(interaction)
                
                    class TimeoutDurationButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Timeout Duration", style = nextcord.ButtonStyle.gray, row = 1)
                            self.outer = outer
                            
                        class TimeoutDurationModal(nextcord.ui.Modal): #Timeout Duration Modal -----------------------------------------------------
                            def __init__(self, outer, guild_id):
                                super().__init__(title = "Timeout Duration")
                                self.outer = outer
                                server = Server(guild_id)
                                
                                self.input = nextcord.ui.TextInput(label = "Timeout Duration (Format: 5s, 10m, 1h, 2d)", default_value = server.profanityTimeoutTime, placeholder = "This Field is Required", max_length=10)
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                if self.input.value == "" or self.input.value == None:
                                    await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Timeout Time needs to be like this: 10s, 20s, 1m, 30m, 1h, 5h, 1d", color = nextcord.Color.red()), ephemeral=True)
                                    return
                                
                                try:
                                    humanfriendly.parse_timespan(self.input.value)
                                except:
                                    await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Timeout Time needs to be like this: 10s, 20s, 1m, 30m, 1h, 5h, 1d", color = nextcord.Color.red()), ephemeral=True)
                                    return
                                
                                server = Server(interaction.guild.id)
                                server.profanityTimeoutTime = self.input.value
                                server.saveData()
                                await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.TimeoutDurationModal(self.outer, interaction.guild.id))
                            
                    class StrikeExpireTimeButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Strike Expire Time", style = nextcord.ButtonStyle.gray, row  = 1)
                            self.outer = outer
                            
                        class StrikeExpireTimeModal(nextcord.ui.Modal): #Strike Expire Time Modal -----------------------------------------------------
                            def __init__(self, outer, guild_id):
                                super().__init__(title = "Strike Expire Time")
                                self.outer = outer
                                server = Server(guild_id)
                                
                                self.input = nextcord.ui.TextInput(label = "Strike Expire Time (Days) (Must be a number)", default_value = server.strikeExpireTime, placeholder = "Disable this feature", max_length=2, required = False)
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                if self.input.value != None:
                                    try:
                                        int(self.input.value)
                                    except:
                                        await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Strike Expire Time needs to be a number.", color = nextcord.Color.red()), ephemeral=True)
                                        return
                                
                                    server = Server(interaction.guild.id)
                                    server.strikeExpireTime = int(self.input.value)
                                else:
                                    server = Server(interaction.guild.id)
                                    server.strikeExpireTime = None
                                    
                                server.saveData()
                                await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.StrikeExpireTimeModal(self.outer, interaction.guild.id))
                            
                    class MaxStrikesButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Maximum Strikes", style = nextcord.ButtonStyle.gray, row  = 2)
                            self.outer = outer
                            
                        class MaxStrikesModal(nextcord.ui.Modal): #Max Strikes Modal -----------------------------------------------------
                            def __init__(self, outer, guild_id):
                                super().__init__(title = "Maximum Strikes")
                                self.outer = outer
                                server = Server(guild_id)
                                
                                self.input = nextcord.ui.TextInput(label = "Maximum Strikes (Must be a number)", default_value = server.maxStrikes, placeholder = "This Field is Required", max_length=2)
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                try:
                                    if int(self.input.value) > 25: raise Exception
                                except:
                                    await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Maximum Strikes needs to be a positive number below 26.", color = nextcord.Color.red()), ephemeral=True)
                                    return
                                
                                server = Server(interaction.guild.id)
                                server.maxStrikes = int(self.input.value)
                                server.saveData()
                                await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.MaxStrikesModal(self.outer, interaction.guild.id))
                            
                    class AdminChannelButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Admin Channel", style = nextcord.ButtonStyle.gray, row  = 2)
                            self.outer = outer
                                                
                        async def callback(self, interaction: Interaction):
                            server = Server(interaction.guild.id)
                                
                            selectOptions = []
                            for channel in interaction.guild.text_channels:
                                if channel.category != None: categoryName = channel.category.name
                                else: categoryName = None
                                #check permissions
                                if await checkTextChannelPermissions(channel, False):
                                    selectOptions.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.adminChannel != None and server.adminChannel.id == channel.id)))
                            
                            
                            await SelectView("Dashboard - Moderation - Profanity - Admin Channel", "Select a channel to send strike info to.\n\n**MAKE SURE THIS CHANNEL IS ONLY ACCESSABLE BY ADMINS**\nThis channel will allow members to mark strikes as incorrect. Thus, it should only be accessible by admins.\n\n**Don't See Your Channel?**\nCheck to make sure that InfiniBot has the permissions to view and send messages in your channel.", selectOptions, self.SelectViewCallback, continueButtonLabel = "Confirm").setup(interaction)
                            
                        async def SelectViewCallback(self, interaction: Interaction, selection):
                            if selection == None: 
                                await self.outer.setup(interaction)
                                return
                                
                            server = Server(interaction.guild.id)
                            if server.setAdminChannelID(selection):
                                server.saveData()
                                await self.outer.setup(interaction)
                                
                            #send a message to the new admin channel
                            await server.adminChannel.send(embed = nextcord.Embed(title = "Admin Channel Set", description = f"Strikes will now be logged in this channel.\n**IMPORTANT: MAKE SURE THAT THIS CHANNEL IS ONLY ACCESSABLE BY ADMINS!**\nThis channel will allow members to mark strikes as incorrect. Thus, you only want admins to see it.\n\nAction done by {interaction.user}", color =  nextcord.Color.green()), view = SupportAndInviteView())
                                     
                async def callback(self, interaction: Interaction):
                    view = self.ProfaneModerationView(self.outer)
                    await view.setup(interaction)
             
            class SpamModerationButton(nextcord.ui.Button):
                def __init__(self, outer, guild_id):
                    server = Server(guild_id)
                    super().__init__(label = "Spam", style = nextcord.ButtonStyle.gray, disabled = (not server.spamBool))
                    del server
                    self.outer = outer
                    
                class SpamModerationView(nextcord.ui.View):
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.timeoutDurationBtn = self.TimeoutDurationButton(self)
                        self.add_item(self.timeoutDurationBtn)
                        
                        self.messageThresholdBtn = self.MessagesThresholdButton(self)
                        self.add_item(self.messageThresholdBtn)
                        
                        self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1) 
                        self.backBtn.callback = self.backBtnCallback
                        self.add_item(self.backBtn)
                        
                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        embed = nextcord.Embed(title = "Dashboard - Moderation - Spam", description = f"This feature will not work for anyone with Administrator priveleges or a higher role than InfiniBot.\n\nTimeout Duration: {server.spamTimeoutTime}\nMessages Threshold: {server.messagesThreshold} messages\n\nChoose a feature to setup / edit.", color = nextcord.Color.blue())
                        
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                                                     
                    class TimeoutDurationButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Timeout Duration", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class TimeoutDurationModal(nextcord.ui.Modal): #Timeout Duration Modal -----------------------------------------------------
                            def __init__(self, outer, guild_id):
                                super().__init__(title = "Timeout Duration")
                                self.outer = outer
                                server = Server(guild_id)
                                
                                self.input = nextcord.ui.TextInput(label = "Timeout Duration (Format: 5s, 10m, 1h, 2d)", default_value = server.spamTimeoutTime, placeholder = "This Field is Required", max_length=10)
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                if self.input.value == "" or self.input.value == None:
                                    await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Timeout Time needs to be like this: 10s, 20s, 1m, 30m, 1h, 5h, 1d", color = nextcord.Color.red()), ephemeral=True)
                                    return
                                
                                try:
                                    humanfriendly.parse_timespan(self.input.value)
                                except:
                                    await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The Timeout Time needs to be like this: 10s, 20s, 1m, 30m, 1h, 5h, 1d", color = nextcord.Color.red()), ephemeral=True)
                                    return
                                
                                server = Server(interaction.guild.id)
                                server.spamTimeoutTime = self.input.value
                                server.saveData()
                                await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.TimeoutDurationModal(self.outer, interaction.guild.id))
                         
                    class MessagesThresholdButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Messages Threshold", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class MessagesThresholdModal(nextcord.ui.Modal): #Timeout Duration Modal -----------------------------------------------------
                            def __init__(self, outer, guild_id):
                                super().__init__(title = "Message Threshold")
                                self.outer = outer
                                server = Server(guild_id)
                                
                                self.input = nextcord.ui.TextInput(label = "Message Threshold (# of messages)", default_value = server.messagesThreshold, placeholder = "This Field is Required", max_length=2)
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                if self.input.value == "" or self.input.value == None:
                                    return
                                
                                try:
                                    int(self.input.value)
                                except:
                                    await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "You formatted that wrong. The messages threshold needs to be a number", color = nextcord.Color.red()), ephemeral=True)
                                    return
                                
                                server = Server(interaction.guild.id)
                                server.messagesThreshold = int(self.input.value)
                                server.saveData()
                                await self.outer.setup(interaction)
                                
                        async def callback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.MessagesThresholdModal(self.outer, interaction.guild.id))
                                                                      
                async def callback(self, interaction: Interaction):
                    view = self.SpamModerationView(self.outer)
                    await view.setup(interaction)
                                                                
        async def callback(self, interaction: Interaction): #Moderation Button Callback ————————————————————————————————————————————————————————————
            view = self.ModerationView(self.outer, interaction.guild.id)
            await view.setup(interaction)
            
    class LoggingButton(nextcord.ui.Button):
        def __init__(self, outer, guild_id):
            server = Server(guild_id)
            
            super().__init__(label = "Logging", style = nextcord.ButtonStyle.gray, disabled = (not server.loggingBool))
            del server
            self.outer = outer
            
        class LoggingView(nextcord.ui.View): #Logging Window -----------------------------------------------------
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
                self.logChannelBtn = self.LogChannelButton(self)
                self.add_item(self.logChannelBtn)
                
            async def setup(self, interaction: Interaction):
                for child in self.children: 
                    del child 
                    self.__init__(self.outer)
                
                server = Server(interaction.guild.id)
                if server.logChannel != None: logChannelName = server.logChannel.mention
                else: logChannelName = "None"
                
                #warnings
                if server.logChannel == None: 
                    warning = "**WARNING!!! THE LOG CHANNEL IS NOT SET! LOGGING WILL NOT WORK AS EXPECTED!!!**"
                    self.logChannelBtn.style = nextcord.ButtonStyle.blurple
                else: 
                    warning = ""
                    self.logChannelBtn.style = nextcord.ButtonStyle.gray
    
                embed = nextcord.Embed(title = "Dashboard - Logging", description = f"{warning}\n\n**Settings**\nLog Channel: {logChannelName}\n\n**Set / Edit the Log Channel below:**", color = nextcord.Color.blue())
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class LogChannelButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Log Channel", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
           
                async def callback(self, interaction: Interaction):
                    server = Server(interaction.guild.id)
                        
                    selectOptions = []
                    for channel in interaction.guild.text_channels:
                        if channel.category != None: categoryName = channel.category.name
                        else: categoryName = None
                        selectOptions.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.logChannel != None and server.logChannel.id == channel.id)))
                    
                    
                    await SelectView("Dashboard - Logging - Log Channel", "Select a channel to which to send logs\n\nNote: It is highly recommended that you set the notifications settings for this channel to \"nothing\".", selectOptions, self.SelectViewCallback, continueButtonLabel = "Confirm").setup(interaction)
                    
                async def SelectViewCallback(self, interaction: Interaction, selection):
                    if selection == None:
                        await self.outer.setup(interaction)
                        return
                    
                    server = Server(interaction.guild.id)
                    if server.setLogChannelID(selection):
                        server.saveData()
                    await self.outer.setup(interaction)
                    
                    await server.logChannel.send(embed = nextcord.Embed(title = "Log Channel Set", description = f"This channel will now be used for logging.\n\nNote: It is highly recommended that you set the notifications settings for this channel to \"nothing\".\n\nAction done by {interaction.user}", color =  nextcord.Color.green()), view = SupportAndInviteView())
            
        async def callback(self, interaction: Interaction):
            await self.LoggingView(self.outer).setup(interaction)

    class LevelingButton(nextcord.ui.Button):
        def __init__(self, outer, guild_id):
            server = Server(guild_id)
            
            super().__init__(label = "Leveling", style = nextcord.ButtonStyle.gray, disabled = (not server.levelingBool))
            del server
            self.outer = outer
            
        class LevelingView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.manageMembersBtn = self.ManageMembersButton(self)
                self.add_item(self.manageMembersBtn)
                
                self.levelRewardsBtn = self.LevelRewardsButton(self)
                self.add_item(self.levelRewardsBtn)
                
                self.levelingMessageBtn = self.LevelingMessageButton(self)
                self.add_item(self.levelingMessageBtn)
                
                self.levelingChannelBtn = self.LevelingChannelButton(self)
                self.add_item(self.levelingChannelBtn)
                
                self.pointsLostPerDayBtn = self.PointsLostPerDayButton(self)
                self.add_item(self.pointsLostPerDayBtn)
                
                self.exemptChannelsBtn = self.ExemptChannelsButton(self)
                self.add_item(self.exemptChannelsBtn)
                
                self.levelCardsBtn = self.LevelCardsButton(self)
                self.add_item(self.levelCardsBtn)
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 4)
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
            async def setup(self, interaction: Interaction):
                for child in self.children: 
                    del child 
                    self.__init__(self.outer)
                
                server = Server(interaction.guild.id)
                
                if server.levelingChannel != None: levelingChannelName = server.levelingChannel.mention
                else: levelingChannelName = "System Messages Channel"
                
                if server.pointsLostPerDay != None: pointsLostPerDay = server.pointsLostPerDay
                else: pointsLostPerDay = "DISABLED"
                
                if server.levelingMessage != None: levelingMessage = server.levelingMessage
                else: levelingMessage = "DISABLED"
                
                if server.allowLevelCardsBool: allowLevelCards = "Yes"
                else: allowLevelCards = "No"
                
                embed = nextcord.Embed(title = "Dashboard - Leveling", description = f"**Settings:**\nLeveling Channel: {levelingChannelName}\nPoints Lost Per Day: {pointsLostPerDay}\nAllow Level-Up Cards: {allowLevelCards}\nLevel Up Message:```{levelingMessage}```\n\n**Choose a feature to setup / edit**", color = nextcord.Color.blue())
                await interaction.response.edit_message(embed = embed, view = self)
             
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                
            class ManageMembersButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Manage Members", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class MembersView(nextcord.ui.View):#Members View Window -----------------------------------------------------
                    def __init__(self, outer):
                        super().__init__(timeout=None)
                        self.outer = outer
                        
                        self.editLevelBtn = self.EditLevelButton(self)
                        self.add_item(self.editLevelBtn)
                        
                        self.deleteAllLevelsBtn = self.DeleteAllLevelsButton(self)
                        self.add_item(self.deleteAllLevelsBtn)
                        
                        self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        self.backBtn.callback = self.backBtnCallback
                        self.add_item(self.backBtn)
                        
                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        if not await canLevel(interaction, server): return
                        
                        self.rankedMembers = []
                        
                        for member in interaction.guild.members: 
                            if member.bot: continue
                            Member = server.levels.getMember(member.id)
                            
                            if Member != None:
                                self.rankedMembers.append([member, Member.score])
                            else:
                                self.rankedMembers.append([member, 0])
                        
                        
                        #sort
                        self.rankedMembers = sorted(self.rankedMembers, key=lambda x: (-x[1], x[0].name))


                        self.embed = nextcord.Embed(title = "Dashboard - Leveling - Manage Members", color = nextcord.Color.blue())
                        
                        rank, lastScore = 1, 0
                        for member in self.rankedMembers: 
                            index = self.rankedMembers.index(member)
                            if index < 20:
                                level = getLevel(member[1])
                                if member[0].nick != None: memberName = f"{member[0]} ({member[0].nick})"
                                else: memberName = f"{member[0]}"
                                
                                if member[1] < lastScore:
                                    rank += 1
                                lastScore = member[1]
                            
                                self.embed.add_field(name = f"**#{rank} {memberName}**", value = f"Level: {str(level)}, Score: {str(member[1])}", inline = False)
                            else:
                                self.embed.add_field(name = f"+ {str(len(self.rankedMembers) - 20)} more", value = f"To see a specific member's level, type */level [member]*", inline = False)
                                break
                        
                        await interaction.response.edit_message(embed = self.embed, view = self)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        await interaction.edit_original_message(view = self.outer)
                        
                    class EditLevelButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Edit", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                                                        
                        class levelModal(nextcord.ui.Modal):
                            def __init__(self, outer, memberID, defaultLevel):
                                super().__init__(title = "Choose Level")
                                self.outer = outer
                                self.memberID = memberID

                                self.input = nextcord.ui.TextInput(label = "Choose a level. Must be a number", default_value=str(defaultLevel))
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                member = self.memberID
                                level = int(self.input.value)
                                
                                if member == None: return
                                
                                server = Server(interaction.guild.id)
                                discordMember = server.levels.getMember(member)
                                if level > 0:
                                    if discordMember != None: discordMember.score = getScore(level)
                                    else: server.levels.addMember(member, score = getScore(level))
                                    server.saveLevels()
                                else:
                                    if discordMember != None: 
                                        server.levels.deleteMember(member)
                                        server.saveLevels()
                                        
                                await self.outer.setup(interaction)
                                
                                #get the member
                                Member = None
                                for _member in interaction.guild.members:
                                    if _member.id == int(member):
                                        Member = _member
                                
                                #check their level rewards
                                await checkForLevelsAndLevelRewards(interaction.guild, Member, silent = True)  
                                                       
                        async def callback(self, interaction: Interaction):# Edit Levels Callback ————————————————————————————————————————————————————————————
                            memberSelectOptions:list[nextcord.SelectOption] = []
                            for data in self.outer.rankedMembers:
                                level = getLevel(data[1])
                                member = data[0]
                                if member.nick != None: memberName = f"{member} ({member.nick})"
                                else: memberName = f"{member}"
                            
                                memberSelectOptions.append(nextcord.SelectOption(label = f"{memberName} - Level {str(level)}, Score - {str(data[1])}", value = data[0].id))
                            
                            await SelectView(self.outer.embed.title, "Choose a Member", memberSelectOptions, self.selectViewCallback, embedFields = self.outer.embed.fields, continueButtonLabel = "Next", placeholder = "Choose", preserveOrder = True).setup(interaction)
                        
                        async def selectViewCallback(self, interaction: Interaction, selection):       
                            if selection == None:
                                await self.outer.setup(interaction)
                                return
                            
                            memberID = selection
                            server = Server(interaction.guild.id)
                            Member = server.levels.getMember(memberID)
                            if Member != None: score = Member.score
                            else: score = 0
                                    
                            await interaction.response.send_modal(self.levelModal(self.outer, selection, getLevel(score)))
                    
                    class DeleteAllLevelsButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Reset", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class DeleteAllLevelsView(nextcord.ui.View):
                            def __init__(self, outer):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                self.noBtn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
                                self.noBtn.callback = self.noBtnCommand
                                self.add_item(self.noBtn)
                                
                                self.yesBtn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
                                self.yesBtn.callback = self.yesBtnCommand
                                self.add_item(self.yesBtn)
                                
                            async def setup(self, interaction: Interaction):
                                embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will reset all levels in the server to 0.\nThis action cannot be undone.", color = nextcord.Color.blue())
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                            async def noBtnCommand(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                                
                            async def yesBtnCommand(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                server.levels.allMembers = []
                                server.saveLevels()
                                await self.outer.setup(interaction)
                            
                        async def callback(self, interaction: Interaction):
                            await self.DeleteAllLevelsView(self.outer).setup(interaction)
                    
                async def callback(self, interaction: Interaction): # Strikes Callback ————————————————————————————————————————————————————————————
                    view = self.MembersView(self.outer)
                    await view.setup(interaction)
            
            class LevelRewardsButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Level Rewards", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class LevelRewardsView(nextcord.ui.View): #Level Rewards Window -----------------------------------------------------
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.createLevelRewardBtn = self.CreateLevelRewardButton(self)
                        self.add_item(self.createLevelRewardBtn)
                        
                        self.deleteLevelRewardsBtn = self.DeleteLevelRewardButton(self)
                        self.add_item(self.deleteLevelRewardsBtn)
                        
                        self.deleteAllLevelRewardsBtn = self.DeleteAllLevelRewardsBtn(self)
                        self.add_item(self.deleteAllLevelRewardsBtn)
                        
                        self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        self.backBtn.callback = self.backBtnCallback
                        self.add_item(self.backBtn)
                        
                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        self.embed = nextcord.Embed(title = "Dashboard - Leveling - Level Rewards", color = nextcord.Color.blue())
                        
                        levelRewards = []
                        for levelReward in server.levels.levelRewards: 
                            if levelReward.role != None: #code should be obsolete. This is a security precaution
                                levelRewards.append(f"{levelReward.role.mention} - Level {levelReward.level}")
                                
                        if levelRewards == []: levelRewards.append("You don't have any level rewards set up. Create one!")
                        self.embed.add_field(name = "Level Rewards", value = "\n".join(levelRewards))
                        try: await interaction.response.edit_message(embed = self.embed, view = self)
                        except: await interaction.edit_original_message(embed = self.embed, view = self)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        await interaction.edit_original_message(view = self.outer)
                                                                   
                    class CreateLevelRewardButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Create", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                                               
                        async def callback(self, interaction: Interaction):
                            server = Server(interaction.guild.id)
                            allLevelRewardRoles = [levelReward.role for levelReward in server.levels.levelRewards]
                            
                            selectOptions = []
                            for role in interaction.guild.roles:
                                if role.name == "@everyone": continue
                                if not canAssignRole(role): continue
                                if role not in allLevelRewardRoles: selectOptions.append(nextcord.SelectOption(label = role.name, description = role.id, value = role.id))
                            
                            if selectOptions == []:
                                await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", description = "You've run out of roles to use! To fix this, either promote InfiniBot to the highest role, give InfiniBot Administrator, or add more roles to the server!", color = nextcord.Color.red()), ephemeral=True)             
                                        
                            else:
                                await SelectView(self.outer.embed.title, self.outer.embed.description, selectOptions, self.selectViewCallback, embedFields = self.outer.embed.fields, continueButtonLabel = "Next", placeholder = "Choose").setup(interaction)            
                            
                        async def selectViewCallback(self, interaction: Interaction, selection):
                            if selection == None: 
                                await self.outer.setup(interaction) 
                                return
                            
                            await interaction.response.send_modal(self.levelModal(self.outer, selection))
                                                
                        class levelModal(nextcord.ui.Modal):
                            def __init__(self, outer, selection):
                                super().__init__(title = "Choose Level")
                                self.outer = outer
                                self.selection = selection
                                
                                self.input = nextcord.ui.TextInput(label = "Level at which to reward this role (number)")
                                self.add_item(self.input)
                                
                            async def callback(self, interaction: Interaction):
                                role = self.selection
                                level = int(self.input.value)
                                
                                server = Server(interaction.guild.id)
                                server.levels.addLevelReward(role, level)
                                server.saveLevelRewards()
                                        
                                await self.outer.setup(interaction)
                                
                                discordRole = interaction.guild.get_role(int(role))
                                
                                await interaction.followup.send(embed = nextcord.Embed(title = "Level Reward Created", description = f"{discordRole.mention} is now assigned to level {str(level)}.\nNote: This will mean that this role will be revoked to anyone who is below level {str(level)}.", color = nextcord.Color.green()), ephemeral=True)                  

                                #update the level rewards for everyone
                                for member in interaction.guild.members:
                                    await checkForLevelsAndLevelRewards(interaction.guild, member, silent = True)
                    
                    class DeleteLevelRewardButton(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Delete", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class DeleteLevelRewardView(nextcord.ui.View): #Delete Level Reward Window -----------------------------------------------------
                            def __init__(self, outer, guild: nextcord.Guild):
                                super().__init__(timeout=None)
                                self.outer = outer
                                
                                self.cancelBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                                self.cancelBtn.callback = self.cancelBtnCallback
                                self.add_item(self.cancelBtn)
                                
                                self.confirmBtn = self.DeleteButton(self.outer, self, guild.id)
                                self.add_item(self.confirmBtn)
                                
                            async def setup(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                allLevelRewardRoles = [levelReward.role for levelReward in server.levels.levelRewards]
                                
                                selectOptions = [nextcord.SelectOption(label = role.name, description = role.id, value = role.id) for role in allLevelRewardRoles]
                                
                                if selectOptions != []:
                                    self.roleSelect = nextcord.ui.Select(options = selectOptions, placeholder = "Choose")
                                    self.add_item(self.roleSelect)
                                    await interaction.response.edit_message(view = self)
                                    
                                else:
                                    await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", description = "You don't have any level rewards set up!", color = nextcord.Color.red()), ephemeral=True)                     
                                                                                          
                            async def cancelBtnCallback(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                                                          
                        async def callback(self, interaction: Interaction):# Delete Level Reward Callback ————————————————————————————————————————————————————————————
                            server = Server(interaction.guild.id)
                            allLevelRewardRoles = [levelReward.role for levelReward in server.levels.levelRewards]
                            
                            selectOptions = [nextcord.SelectOption(label = role.name, description = role.id, value = role.id) for role in allLevelRewardRoles]
                            
                            if selectOptions == []:
                                await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", description = "You don't have any level rewards set up!", color = nextcord.Color.red()), ephemeral=True)                     
                            else:
                                await SelectView(self.outer.embed.title, self.outer.embed.description, selectOptions, self.selectViewCallback, embedFields = self.outer.embed.fields, continueButtonLabel = "Delete", placeholder = "Choose").setup(interaction)
                   
                        async def selectViewCallback(self, interaction: Interaction, selection):
                            if selection == None:
                                await self.outer.setup(interaction)
                                return
                            
                            server = Server(interaction.guild.id)
                            server.levels.deleteLevelReward(int(selection))
                            server.saveLevelRewards()
                            
                            await self.outer.setup(interaction)
                   
                    class DeleteAllLevelRewardsBtn(nextcord.ui.Button):
                        def __init__(self, outer):
                            super().__init__(label = "Delete All", style = nextcord.ButtonStyle.gray)
                            self.outer = outer
                            
                        class DeleteAllLevelsView(nextcord.ui.View):
                            def __init__(self, outer):
                                super().__init__(timeout = None)
                                self.outer = outer
                                
                                self.noBtn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
                                self.noBtn.callback = self.noBtnCommand
                                self.add_item(self.noBtn)
                                
                                self.yesBtn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
                                self.yesBtn.callback = self.yesBtnCommand
                                self.add_item(self.yesBtn)
                                
                            async def setup(self, interaction: Interaction):
                                embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will delete all level rewards in the server.\nThis action cannot be undone.", color = nextcord.Color.blue())
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                            async def noBtnCommand(self, interaction: Interaction):
                                await self.outer.setup(interaction)
                                
                            async def yesBtnCommand(self, interaction: Interaction):
                                server = Server(interaction.guild.id)
                                server.levels.levelRewards = []
                                server.saveLevelRewards()
                                await self.outer.setup(interaction)
                                
                            async def callback(self, interaction: Interaction):
                                await self.DeleteAllLevelsView(self.outer).setup(interaction)
                        
                        async def callback(self, interaction: Interaction):
                            await self.DeleteAllLevelsView(self.outer).setup(interaction)
                    
                async def callback(self, interaction: Interaction): #Filtered Words Button Callback ————————————————————————————————————————————————————————————
                    view = self.LevelRewardsView(self.outer)
                    await view.setup(interaction)           
                    
            class LevelingMessageButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Level Up Message", style = nextcord.ButtonStyle.gray, row  = 1)
                    self.outer = outer
                    
                class LevelingMessageModal(nextcord.ui.Modal): #Leveling Message Modal -----------------------------------------------------
                    def __init__(self, guild: nextcord.Guild, outer):
                        super().__init__(timeout = None, title = "Level Up Message")
                        self.outer = outer
                        
                        server = Server(guild.id)
                        
                        self.levelingMessageTextInput = nextcord.ui.TextInput(label = "Message ([level] = Level, BLANK = Disabled)", style = nextcord.TextInputStyle.paragraph, max_length=1024, default_value = server.levelingMessage, placeholder = "DISABLED", required = False)
                        self.add_item(self.levelingMessageTextInput)
                        
                    async def callback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        if self.levelingMessageTextInput.value != "":
                            server.levelingMessage = self.levelingMessageTextInput.value
                        else:
                            server.levelingMessage = None
                            
                        server.saveData()
                        
                        await self.outer.setup(interaction)
                                         
                async def callback(self, interaction: Interaction):
                    await interaction.response.send_modal(self.LevelingMessageModal(interaction.guild, self.outer))                                     
                    
            class LevelingChannelButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Leveling Channel", style = nextcord.ButtonStyle.gray, row = 1)
                    self.outer = outer
            
                async def callback(self, interaction: Interaction):
                    server = Server(interaction.guild.id)
                    selectOptions = [nextcord.SelectOption(label = "System Messages Channel", value = "__NONE__", description = "Display in system messages channel", default = (server.levelingChannel == None))]
                    for channel in interaction.guild.text_channels:
                        if channel.category != None: categoryName = channel.category.name
                        else: categoryName = None
                        selectOptions.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.levelingChannel != None and server.levelingChannel.id == channel.id)))
                        
                        
                    await SelectView("Dashboard - Leveling - Leveling Channel", "Select a channel to show level upgrades.", selectOptions, self.selectViewCallback).setup(interaction)

                async def selectViewCallback(self, interaction: Interaction, selection):
                    if selection == None:
                        await self.outer.setup(interaction)
                        return
                    
                    if selection == "__NONE__": value = None
                    else: value = selection
                    
                    server = Server(interaction.guild.id)
                    if server.setLevelingChannelID(value):
                        server.saveData()
                        await self.outer.setup(interaction)    

            class PointsLostPerDayButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Points Lost Per Day", style = nextcord.ButtonStyle.gray, row  = 2)
                    self.outer = outer
                    
                class PointsLostPerDayModal(nextcord.ui.Modal): #Leveling Message Modal -----------------------------------------------------
                    def __init__(self, guild: nextcord.Guild, outer):
                        super().__init__(timeout = None, title = "Points Lost Per Day")
                        self.outer = outer
                        
                        server = Server(guild.id)
                        
                        self.pointsLostPerDayTextInput = nextcord.ui.TextInput(label = "Points (must be a number, blank = DISABLED)", style = nextcord.TextInputStyle.short, max_length=3, default_value = server.pointsLostPerDay, required = False)
                        self.add_item(self.pointsLostPerDayTextInput)
                        
                    async def callback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        value: str = self.pointsLostPerDayTextInput.value
                        if not (value == None or value == ""):
                            if not value.isnumeric() or int(value) < 0:
                                await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "\"Points\" must be a number and cannot be negative.", color = nextcord.Color.red()), ephemeral = True)
                                return
                            server.pointsLostPerDay = int(value)
                            server.saveData()
                        
                            await self.outer.setup(interaction)
                            await interaction.followup.send(embed = nextcord.Embed(title = "Points Lost Per Day Set", description = f"Every day at midnight, everyone will loose {value} points.", color = nextcord.Color.green()), ephemeral = True)
                        
                        else:
                            server.pointsLostPerDay = None
                            server.saveData()
                        
                            await self.outer.setup(interaction)
                            await interaction.followup.send(embed = nextcord.Embed(title = "Points Lost Per Day Disabled", description = f"InfiniBot will not take points from anyone at midnight.", color = nextcord.Color.green()), ephemeral = True)
                            
                async def callback(self, interaction: Interaction):
                    await interaction.response.send_modal(self.PointsLostPerDayModal(interaction.guild, self.outer))       
                                          
            class ExemptChannelsButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Exempt Channels", style = nextcord.ButtonStyle.gray, row = 2)
                    self.outer = outer
                    
                class ExemptChannelsView(nextcord.ui.View):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(timeout = None)
                        self.outer = outer 
                        
                        addButton = self.AddButton(self, interaction)
                        self.add_item(addButton)
                        
                        deleteButton = self.DeleteButton(self, interaction)
                        self.add_item(deleteButton)
                        
                        self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        self.backBtn.callback = self.backBtnCallback
                        self.add_item(self.backBtn)
                                
                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        
                        channels = "\n".join([f"• {channel.mention}" for channel in server.levelingExemptChannels])
                        
                        if channels == "":
                            channels = "You don't have any exempt channels yet. Add one!"
                        
                        
                        description = f"**Select Channels that will not Grant Points when Messages are Sent**\n{channels}\n\n★ 20 Channels Maximum ★"
                        
                        embed = nextcord.Embed(title = "Dashboard - Leveling - Exempt Channels", description = description, color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def reload(self, interaction: Interaction):
                        self.__init__(self.outer, interaction)
                        await self.setup(interaction)
                    
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    class AddButton(nextcord.ui.Button):
                        def __init__(self, outer, interaction: Interaction):
                            server = Server(interaction.guild.id)
                            disabled = (len(server.levelingExemptChannels) == 20)
                            super().__init__(label = "Add Channel", style = nextcord.ButtonStyle.gray, disabled = disabled)
                            self.outer = outer
                                                    
                        async def callback(self, interaction: Interaction):
                            options = []
                            server = Server(interaction.guild.id)
                            alreadyAddedIds = [channel.id for channel in server.levelingExemptChannels]
                            for channel in interaction.guild.channels:
                                if type(channel) != nextcord.TextChannel and type(channel) != nextcord.VoiceChannel: continue
                                if channel.id in alreadyAddedIds: continue
                                options.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = channel.id))
                            
                            if len(options) == 0:
                                await interaction.response.send_message(embed = nextcord.Embed(title = "No More Channels", description = "You've ran out of channels to exempt. Create more channels, or give InfiniBot higher permissions to see more channels!", color = nextcord.Color.red()), ephemeral = True)
                                return
                            
                            selectView = SelectView("Dashboard - Leveling - Exempt Channels - Add", "Choose a channel to make exempt (messages won't grant points in this channel)", options, self.selectCallback, placeholder = "Choose a Channel", continueButtonLabel = "Add Channel")
                            await selectView.setup(interaction)
               
                        async def selectCallback(self, interaction: Interaction, choice):
                            if choice != None:
                                server = Server(interaction.guild.id)
                                server.levelingExemptChannels.append(interaction.guild.get_channel(int(choice)))
                                server.saveData()
                                
                            await self.outer.reload(interaction)
 
                    class DeleteButton(nextcord.ui.Button):
                        def __init__(self, outer, interaction: Interaction):
                            server = Server(interaction.guild.id)
                            disabled = (len(server.levelingExemptChannels) == 0)
                            super().__init__(label = "Delete Channel", style = nextcord.ButtonStyle.gray, disabled = disabled)
                            self.outer = outer
                                                    
                        async def callback(self, interaction: Interaction):
                            options = []
                            server = Server(interaction.guild.id)
                            for channel in server.levelingExemptChannels:
                                options.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = channel.id))
                            
                            selectView = SelectView("Dashboard - Leveling - Exempt Channels - Delete", "Choose a Channel", options, self.selectCallback, placeholder = "Choose a Channel", continueButtonLabel = "Delete Channel")
                            await selectView.setup(interaction)
               
                        async def selectCallback(self, interaction: Interaction, choice):
                            if choice != None:
                                server = Server(interaction.guild.id)
                                for channel in server.levelingExemptChannels:
                                    if channel.id == int(choice):
                                        server.levelingExemptChannels.remove(channel) #usually, you would never do this in a loop. However, because we are only doing it once, this still works.
                                        pass

                                server.saveData()
                                
                            await self.outer.reload(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.ExemptChannelsView(self.outer, interaction).setup(interaction)
       
            class LevelCardsButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Level-Up Cards", style = nextcord.ButtonStyle.gray, row = 3)
                    self.outer = outer
                    
                class LevelCardsView(nextcord.ui.View):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        server = Server(interaction.guild.id)
                        
                        if server.allowLevelCardsBool: buttonLabel = "Disable"
                        else: buttonLabel = "Enable"
                        
                        del server #we don't need it anymore
                        
                        
                        self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        self.backBtn.callback = self.backBtnCallback
                        self.add_item(self.backBtn)
                        
                        
                        self.mainBtn = nextcord.ui.Button(label = buttonLabel, style = nextcord.ButtonStyle.green)
                        self.mainBtn.callback = self.mainBtnCallback
                        self.add_item(self.mainBtn)
                        
                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        if server.allowLevelCardsBool: levelCards = "on"
                        else: levelCards = "off"
                
                        embed = nextcord.Embed(title = "Dashboard - Leveling - Level-Up Cards", description = f"Currently, level-up cards are turned {levelCards}.\n\n**What are level-up cards?**\nIf enabled, members can personalize their own level-up card which will be displayed after each level-up message.", color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    async def mainBtnCallback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        server.allowLevelCardsBool = not server.allowLevelCardsBool
                        
                        server.saveData()
                        
                        await self.outer.setup(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.LevelCardsView(self.outer, interaction).setup(interaction)
                 
        async def callback(self, interaction: Interaction):
            await self.LevelingView(self.outer).setup(interaction)

    class JoinLeaveMessagesButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Join / Leave Messages", style = nextcord.ButtonStyle.gray)
            self.outer = outer
            
        class JoinLeaveMessagesView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.joinMessageBtn = self.JoinMessageButton(self)
                self.add_item(self.joinMessageBtn)
                
                self.joinChannelBtn = self.JoinChannelButton(self)
                self.add_item(self.joinChannelBtn)
                
                self.leaveMessageBtn = self.LeaveMessageButton(self)
                self.add_item(self.leaveMessageBtn)
                
                self.leaveChannelBtn = self.LeaveChannelButton(self)
                self.add_item(self.leaveChannelBtn)
                
                self.joinCardsBtn = self.JoinCardsButton(self)
                self.add_item(self.joinCardsBtn)
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 3)
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
            async def setup(self, interaction: Interaction):
                for child in self.children: 
                    del child 
                    self.__init__(self.outer)

                server = Server(interaction.guild.id)
                
                if server.joinMessage != None: joinMessage = server.joinMessage
                else: joinMessage = "DISABLED"
                
                if server.leaveMessage != None: leaveMessage = server.leaveMessage
                else: leaveMessage = "DISABLED"
                
                if server.allowJoinCardsBool: joinCardsEnabled = "Yes"
                else: joinCardsEnabled = "No"
                
                if server.joinChannel != None: joinChannel = server.joinChannel.mention
                else: joinChannel = "System Messages Channel"
                
                if server.leaveChannel != None: leaveChannel = server.leaveChannel.mention
                else: leaveChannel = "System Messages Channel"
                
                embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages", description = f"**Settings:**\nJoin Messages Channel: {joinChannel}\nLeave Messages Channel: {leaveChannel}\n\nJoin Cards Enabled: {joinCardsEnabled}\n\nJoin Message:```{joinMessage}```Leave Message:```{leaveMessage}```\n\n**Choose a feature to setup / edit**", color = nextcord.Color.blue())
                await interaction.response.edit_message(embed = embed, view = self)
             
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
              
            class JoinMessageButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Join Message", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class JoinMessageModal(nextcord.ui.Modal): #Join Message Modal -----------------------------------------------------
                    def __init__(self, guild: nextcord.Guild, outer):
                        super().__init__(timeout = None, title = "Join Message")
                        self.outer = outer
                        
                        server = Server(guild.id)
                        if server.joinMessage != None: joinMessage = server.joinMessage
                        else: joinMessage = ""
                        self.joinMessageTextInput = nextcord.ui.TextInput(label = "Message ([member] = member, blank = DISABLED)", style = nextcord.TextInputStyle.paragraph, max_length=1024, default_value = joinMessage, placeholder = "DISABLED", required = False)
                        self.add_item(self.joinMessageTextInput)
                        
                    async def callback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        
                        if self.joinMessageTextInput.value != "": server.joinMessage = self.joinMessageTextInput.value
                        else: server.joinMessage = None
                        
                        server.saveData()
                        
                        await self.outer.setup(interaction)                     
                        
                async def callback(self, interaction: Interaction):
                    await interaction.response.send_modal(self.JoinMessageModal(interaction.guild, self.outer))                
                                
            class JoinChannelButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Join Message Channel", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                                     
                async def callback(self, interaction: Interaction):
                    server = Server(interaction.guild.id)
                        
                    selectOptions = [nextcord.SelectOption(label = "System Messages Channel", value = "__NONE__", description = "Display in system messages channel", default = (server.joinChannel == None))]
                    for channel in interaction.guild.text_channels:
                        if channel.category != None: categoryName = channel.category.name
                        else: categoryName = None
                        selectOptions.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.joinChannel != None and server.joinChannel.id == channel.id)))
                    
                    await SelectView("Dashboard - Join / Leave Messages - Join Messages Channel", "Select a channel to send join messages", selectOptions, self.SelectViewReturn, continueButtonLabel = "Confirm").setup(interaction)
                      
                async def SelectViewReturn(self, interaction: Interaction, selection):
                    if selection == None:
                        await self.outer.setup(interaction)
                        return
                    
                    if selection == "__NONE__": value = None
                    else: value = selection
                    
                    server = Server(interaction.guild.id)
                    if server.setJoinChannelID(value):
                        server.saveData()
                        await self.outer.setup(interaction)
                                      
            class LeaveMessageButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Leave Message", style = nextcord.ButtonStyle.gray, row = 1)
                    self.outer = outer
                    
                class leaveMessageModal(nextcord.ui.Modal): #Leave Message Modal -----------------------------------------------------
                    def __init__(self, guild: nextcord.Guild, outer):
                        super().__init__(timeout = None, title = "Leave Message")
                        self.outer = outer
                        
                        server = Server(guild.id)
                        if server.leaveMessage != None: leaveMessage = server.leaveMessage
                        else: leaveMessage = ""
                        self.leaveMessageTextInput = nextcord.ui.TextInput(label = "Message ([member] = member, blank = DISABLED)", style = nextcord.TextInputStyle.paragraph, max_length=1024, default_value = leaveMessage, placeholder = "DISABLED", required = False)
                        self.add_item(self.leaveMessageTextInput)
                        
                    async def callback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        if self.leaveMessageTextInput.value != "": server.leaveMessage = self.leaveMessageTextInput.value
                        else: server.leaveMessage = None
                        
                        server.saveData()
                        
                        await self.outer.setup(interaction)                       
                        
                async def callback(self, interaction: Interaction):
                    await interaction.response.send_modal(self.leaveMessageModal(interaction.guild, self.outer))                
                                
            class LeaveChannelButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Leave Message Channel", style = nextcord.ButtonStyle.gray, row = 1)
                    self.outer = outer
                    
                async def callback(self, interaction: Interaction):
                    server = Server(interaction.guild.id)
                        
                    selectOptions = [nextcord.SelectOption(label = "System Messages Channel", value = "__NONE__", description = "Display in system messages channel", default = (server.leaveChannel == None))]
                    for channel in interaction.guild.text_channels:
                        if channel.category != None: categoryName = channel.category.name
                        else: categoryName = None
                        selectOptions.append(nextcord.SelectOption(label = channel.name, value = channel.id, description = categoryName, default = (server.leaveChannel != None and server.leaveChannel.id == channel.id)))
                    
                    await SelectView("Dashboard - Join / Leave Messages - Leave Messages Channel", "Select a channel to send leave messages", selectOptions, self.SelectViewReturn, continueButtonLabel = "Confirm").setup(interaction)
                      
                async def SelectViewReturn(self, interaction: Interaction, selection):
                    if selection == None:
                        await self.outer.setup(interaction)
                        return
                    
                    if selection == "__NONE__": value = None
                    else: value = selection
                    
                    server = Server(interaction.guild.id)
                    if server.setLeaveChannelID(value):
                        server.saveData()
                        await self.outer.setup(interaction)
                                    
            class JoinCardsButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Join Cards", style = nextcord.ButtonStyle.gray, row = 2)
                    self.outer = outer
                    
                class JoinCardsView(nextcord.ui.View):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        server = Server(interaction.guild.id)
                        
                        if server.allowJoinCardsBool: buttonLabel = "Disable"
                        else: buttonLabel = "Enable"
                        
                        del server #we don't need it anymore
                        
                        
                        self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        self.backBtn.callback = self.backBtnCallback
                        self.add_item(self.backBtn)
                        
                        
                        self.mainBtn = nextcord.ui.Button(label = buttonLabel, style = nextcord.ButtonStyle.green)
                        self.mainBtn.callback = self.mainBtnCallback
                        self.add_item(self.mainBtn)
                        
                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        if server.allowJoinCardsBool: joinCards = "on"
                        else: joinCards = "off"
                
                        embed = nextcord.Embed(title = "Dashboard - Join / Leave Messages - Join Cards", description = f"Currently, join cards are turned {joinCards}.\n\n**What are join cards?**\nIf enabled, members can personalize their own join card which will be displayed after each join message.", color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    async def mainBtnCallback(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        server.allowJoinCardsBool = not server.allowJoinCardsBool
                        
                        server.saveData()
                        
                        await self.outer.setup(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.JoinCardsView(self.outer, interaction).setup(interaction)
                                      
        async def callback(self, interaction: Interaction):
            await self.JoinLeaveMessagesView(self.outer).setup(interaction)
    
    class BirthdaysButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Birthdays", style = nextcord.ButtonStyle.gray, row = 1)
            self.outer = outer 
            
        class BirthdaysView(nextcord.ui.View): #Birthdays Window -----------------------------------------------------
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.addBirthdayBtn = self.AddBirthdayButton(self)
                self.add_item(self.addBirthdayBtn)
                
                self.editBirthdayBtn = self.EditBirthdayButton(self)
                self.add_item(self.editBirthdayBtn)
                
                self.deleteBirthdayBtn = self.DeleteBirthdayButton(self)
                self.add_item(self.deleteBirthdayBtn)
                
                self.deleteAllBirthdayBtn = self.DeleteAllBirthdaysButton(self)
                self.add_item(self.deleteAllBirthdayBtn)
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 3) 
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                             
            async def setup(self, interaction: Interaction):
                for child in self.children: 
                    del child 
                    self.__init__(self.outer)
                
                server = Server(interaction.guild.id)
                
                birthdays = []
                for bday in server.birthdays:
                    try:
                        if bday.member == None:
                            server.deleteBirthday(bday.memberID)
                            server.saveBirthdays()
                            continue
                        
                        if bday.realName != None: birthdays.append(f"{bday.member.mention} ({str(bday.realName)}) - {bday.date}")
                        else: birthdays.append(f"{bday.member.mention} - {bday.date}")
                            
                    except Exception as err:
                        print("Birthdays View Error:", err)
                        
                if len(birthdays) == 0: birthdaysStr = "You don't have any birthdays. Create one!"
                else: birthdaysStr = "\n".join(birthdays)

                self.embed = nextcord.Embed(title = "Dashboard - Birthdays", description = f"**Birthdays**\n{birthdaysStr}\n\n**Use the buttons below to add/edit/delete.**", color = nextcord.Color.blue())
                try: await interaction.response.edit_message(embed = self.embed, view = self)
                except: await interaction.edit_original_message(embed = self.embed, view = self)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)               
              
            class AddBirthdayButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Add", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                async def callback(self, interaction: Interaction):# Edit Strikes Callback ————————————————————————————————————————————————————————————
                    server = Server(interaction.guild.id)
                        
                    memberSelectOptions = []
                    for member in interaction.guild.members:
                        if member.bot: continue
                        if not server.birthdayExists(member.id): memberSelectOptions.append(nextcord.SelectOption(label = f"{member}", description = member.nick, value = member.id))
                    
                    
                    if memberSelectOptions == []: 
                        await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Members", description = "Every member in your server already has a birthday! Go invite someone!", color = nextcord.Color.red()), ephemeral = True)
                        return
                    
                    await SelectView(self.outer.embed.title, self.outer.embed.description, memberSelectOptions, self.SelectViewReturn, embedFields = self.outer.embed.fields, placeholder = "Choose a Member", continueButtonLabel = "Next").setup(interaction)
                    
                async def SelectViewReturn(self, interaction: Interaction, selection):
                    if selection == None:
                        await self.outer.setup(interaction)
                        return
                    
                    await interaction.response.send_modal(self.InfoModal(self.outer, selection))          
                                    
                class InfoModal(nextcord.ui.Modal):            
                    def __init__(self, outer, memberID):
                        super().__init__(title = "Add Birthday", timeout = None)
                        self.outer = outer
                        self.memberID = memberID
                        
                        self.dateInput = nextcord.ui.TextInput(label = "Date (MM/DD/YYYY)", style = nextcord.TextInputStyle.short, max_length = 10, placeholder = "MM/DD/YYYY")
                        self.add_item(self.dateInput)
                        
                        self.realNameInput = nextcord.ui.TextInput(label = "Real Name (Optional)", style = nextcord.TextInputStyle.short, max_length=50, required = False)
                        self.add_item(self.realNameInput)
                        
                    async def callback(self, interaction: Interaction):
                        try:
                            datetime.datetime.strptime(self.dateInput.value, f"%m/%d/%Y")
                        except:
                            await interaction.response.send_message(embed = nextcord.Embed(title = "Invalid Format", description = "You formatted the date wrong. Try formating it like this: MM/DD/YYYY", color =  nextcord.Color.red()), ephemeral=True)
                            return
                        
                        server = Server(interaction.guild.id)
                        if self.realNameInput.value == "": server.addBirthday(self.memberID, self.dateInput.value)
                        else: server.addBirthday(self.memberID, self.dateInput.value, realName = self.realNameInput.value)
                        server.saveBirthdays()
                        
                        
                        await self.outer.setup(interaction)
          
            class EditBirthdayButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Edit", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                                                      
                async def callback(self, interaction: Interaction):# Edit Strikes Callback ————————————————————————————————————————————————————————————
                    server = Server(interaction.guild.id)
                        
                    memberSelectOptions = []
                    for member in interaction.guild.members:
                        if server.birthdayExists(member.id): memberSelectOptions.append(nextcord.SelectOption(label = f"{member}", description = member.nick, value = member.id))
                    
                    
                    if memberSelectOptions == []: 
                        await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Members", description = "No members in your server have birthdays. Add some!", color = nextcord.Color.red()), ephemeral = True)
                        return
                    
                    await SelectView(self.outer.embed.title, self.outer.embed.description, memberSelectOptions, self.SelectViewReturn, embedFields = self.outer.embed.fields, placeholder = "Choose a Member", continueButtonLabel = "Next").setup(interaction)
                    
                async def SelectViewReturn(self, interaction: Interaction, selection):
                    if selection == None:
                        await self.outer.setup(interaction)
                        return
                    
                    await interaction.response.send_modal(self.InfoModal(self.outer, selection, interaction.guild.id))          
                                    
                class InfoModal(nextcord.ui.Modal):            
                    def __init__(self, outer, memberID, guildID):
                        super().__init__(title = "Add Birthday", timeout = None)
                        self.outer = outer
                        self.memberID = memberID
                        
                        server = Server(guildID)
                        birthday = server.getBirthday(self.memberID)
                        
                        self.dateInput = nextcord.ui.TextInput(label = "Date (MM/DD/YYYY)", style = nextcord.TextInputStyle.short, max_length = 10, placeholder = "MM/DD/YYYY", default_value = birthday.date)
                        self.add_item(self.dateInput)
                        
                        self.realNameInput = nextcord.ui.TextInput(label = "Real Name (Optional)", style = nextcord.TextInputStyle.short, max_length=50, required = False, default_value = birthday.realName)
                        self.add_item(self.realNameInput)
                        
                    async def callback(self, interaction: Interaction):
                        try:
                            datetime.datetime.strptime(self.dateInput.value, f"%m/%d/%Y")
                        except:
                            await interaction.response.send_message(embed = nextcord.Embed(title = "Invalid Format", description = "You formatted the date wrong. Try formating it like this: MM/DD/YYYY", color =  nextcord.Color.red()), ephemeral=True)
                            return
                        
                        server = Server(interaction.guild.id)
                        birthday = server.getBirthday(self.memberID)
                        birthday.date = self.dateInput.value
                        
                        if self.realNameInput.value != "": birthday.realName = self.realNameInput.value
                        server.saveBirthdays()
                        
                        
                        await self.outer.setup(interaction)

            class DeleteBirthdayButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Delete", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                                      
                async def callback(self, interaction: Interaction):# Edit Strikes Callback ————————————————————————————————————————————————————————————
                    server = Server(interaction.guild.id)
                        
                    memberSelectOptions = []
                    for member in interaction.guild.members:
                        if server.birthdayExists(member.id): memberSelectOptions.append(nextcord.SelectOption(label = f"{member}", description = member.nick, value = member.id))
                    
                    
                    if memberSelectOptions == []: 
                        await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Members", description = "No members in your server have birthdays. Add some!", color = nextcord.Color.red()), ephemeral = True)
                        return
                    
                    await SelectView(self.outer.embed.title, self.outer.embed.description, memberSelectOptions, self.SelectViewReturn, embedFields = self.outer.embed.fields, placeholder = "Choose a Member", continueButtonLabel = "Delete").setup(interaction)
                    
                async def SelectViewReturn(self, interaction: Interaction, selection):
                    if selection == None:
                        await self.outer.setup(interaction)
                        return
                    
                    server = Server(interaction.guild.id)
                    server.deleteBirthday(selection)
                    server.saveBirthdays()
                    
                    await self.outer.setup(interaction)      
                                    
            class DeleteAllBirthdaysButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Delete All", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class DeleteAllStrikesView(nextcord.ui.View):
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.noBtn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger)
                        self.noBtn.callback = self.noBtnCommand
                        self.add_item(self.noBtn)
                        
                        self.yesBtn = nextcord.ui.Button(label = "Yes", style = nextcord.ButtonStyle.green)
                        self.yesBtn.callback = self.yesBtnCommand
                        self.add_item(self.yesBtn)
                        
                    async def setup(self, interaction: Interaction):
                        embed = nextcord.Embed(title = "Are you sure you want to do this?", description = "By choosing \"Yes\", you will delete all birthdays in the server.\nThis action cannot be undone.", color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def noBtnCommand(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    async def yesBtnCommand(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        server.birthdays = []
                        server.saveBirthdays()
                        await self.outer.setup(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.DeleteAllStrikesView(self.outer).setup(interaction)           
           
        async def callback(self, interaction: Interaction):
            view = self.BirthdaysView(self.outer)
            await view.setup(interaction)
    
    class DefaultRolesButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Default Roles", style = nextcord.ButtonStyle.gray, row = 1)
            self.outer = outer
    
        class DefaultRolesView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__(timeout=None)
                self.outer = outer
                
                self.cancelBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                self.cancelBtn.callback = self.cancelBtnCallback

                self.confirmBtn = self.NextButton(self.outer, self)
                
            async def setup(self, interaction: Interaction):
                for child in self.children: 
                    del child 
                    self.__init__(self.outer)
                
                embed = nextcord.Embed(title = "Dashboard - Default Roles", description = "Select the roles you would that InfiniBot will assign to any new members upon join.", color = nextcord.Color.blue())
                
                server = Server(interaction.guild.id)
                
                selectOptions = []
                for role in interaction.guild.roles:
                    if role.name == "@everyone": continue
                    if not canAssignRole(role): continue
                    if len(selectOptions) >= 25:
                        embed.description += "\n\nNote: Only the first 25 roles of your server can be set as default roles."
                        break
                        
                    selectOptions.append(nextcord.SelectOption(label = role.name, description = role.id, value = role.id, default = (role in server.defaultRoles)))
                
                if len(selectOptions) <= 5: maxOptions = len(selectOptions)
                else: maxOptions = 5
                
                if selectOptions != []:
                    self.roleSelect = nextcord.ui.Select(options = selectOptions, placeholder = "Choose", max_values = maxOptions, min_values = 0)
                    self.add_item(self.roleSelect)
                    self.add_item(self.cancelBtn)
                    self.add_item(self.confirmBtn)
                    await interaction.response.edit_message(embed = embed, view = self)
                    
                else:
                    await interaction.response.send_message(embed = nextcord.Embed(title = "No Available Roles", description = "You've run out of roles to use! To fix this, either promote InfiniBot to the highest role, give InfiniBot Administrator, or add more roles to the server!", color = nextcord.Color.red()), ephemeral=True)             
                                            
            async def cancelBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                
            class NextButton(nextcord.ui.Button):
                def __init__(self, outer, parent):
                    super().__init__(label = "Update", style = nextcord.ButtonStyle.blurple)
                    self.outer = outer     
                    self.parent = parent                 
                        
                async def callback(self, interaction: Interaction):
                    server = Server(interaction.guild.id)
                    
                    defaultRoles = []
                    for roleID in self.parent.roleSelect.values:
                        try: defaultRoles.append(interaction.guild.get_role(int(roleID)))
                        except: return
                    
                    
                    server.defaultRoles = defaultRoles
                    server.saveData()
                    
                    await self.outer.setup(interaction)
            
        async def callback(self, interaction: Interaction):
            await self.DefaultRolesView(self.outer).setup(interaction)    
    
    class JoinToCreateVCsButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Join-To-Create VCs", style = nextcord.ButtonStyle.gray, row = 1)
            self.outer = outer
                    
        class JoinToCreateVCsView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__(timeout=None)
                self.outer = outer
                
                #create buttons
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
                self.configureBtn = self.ConfigureButton(self)
                self.add_item(self.configureBtn)
                
            def getMessageEmbed(self, guild: nextcord.Guild):
                server = Server(guild.id)
                vcs = server.VCs
                del server
                    
                if len(vcs) > 0:
                    description = "**Join-To-Create VCs**\n" + "\n".join([f"• {item.channel.mention}" if item.active else f"• ⚠️ {item.channel.mention} ⚠️" for item in vcs])
                else:
                    description = "**Join-To-Create VCs**\nYou don't have any join-to-create VCs. Click Configure to make one!"
                    
                return nextcord.Embed(title = "Dashboard - Join-To-Create-VCs", description = f"You may select up to five voice channels that will have this feature.\n\n**What is it?**\nWhen a user joins one of these Voice Channels, they will be moved to a custom voice channel created just for them. When everyone leaves, the channel will be removed.\n\n{description}", color = nextcord.Color.blue())
        
            async def setup(self, interaction: Interaction):
                await interaction.response.edit_message(embed = self.getMessageEmbed(interaction.guild), view = self)
                    
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class ConfigureButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Configure", style = nextcord.ButtonStyle.blurple)
                    self.outer = outer
                    
                class ConfigureView(nextcord.ui.View):
                    def __init__(self, outer, guild: nextcord.Guild):
                        super().__init__(timeout=None)
                        self.outer = outer
                        
                        self.embed: nextcord.Embed = self.outer.getMessageEmbed(guild)
                        dontSeeYourChannelMessage = """\n\n**Having Issues?**
                        Make sure InfiniBot has the following permissions in your channel:
                        • View Channel
                        • Manage Channel
                        • Connect"""
                        dontSeeYourChannelMessage = standardizeStrIndention(dontSeeYourChannelMessage)
                        self.embed.description += dontSeeYourChannelMessage
                        
                        #get the vcs
                        accessableVCs = [vc for vc in guild.voice_channels if (vc.permissions_for(guild.me).view_channel and vc.permissions_for(guild.me).connect and vc.permissions_for(guild.me).manage_channels)]
                    
                        server = Server(guild.id)
                        vcs = [[vc, server.VCExists(vc.id)] for vc in accessableVCs]
                        
                        #Error message
                        if False in [vc.active for vc in server.VCs]:
                            self.embed.description += "\n\n**⚠️ There is a Problem with One or More of Your VCs ⚠️**\nMake sure that all join-to-create VCs have the following permissions:\n• View Channel\n• Manage Channel\n• Connect"
                        
                        del server

                        #create other buttons
                        self.addBtn = self.AddButton(self, guild, vcs)
                        self.add_item(self.addBtn)
                        
                        self.deleteBtn = self.DeleteButton(self, guild)
                        self.add_item(self.deleteBtn)
                        
                        self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        self.backBtn.callback = self.backBtnCallback
                        self.add_item(self.backBtn)
                        
                    async def setup(self, interaction: Interaction):
                        await interaction.response.edit_message(embed = self.embed, view = self)
                       
                    async def refresh(self, interaction: Interaction):
                        self.__init__(self.outer, interaction.guild)
                        await self.setup(interaction)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    class AddButton(nextcord.ui.Button):
                        def __init__(self, outer, guild: nextcord.Guild, vcs:list[nextcord.VoiceChannel, bool]):
                            self.outer = outer
                            self.vcs = vcs
                            
                            server = Server(guild.id)
                            
                            #choose enabled / disabled
                            if len(self.vcs) > 0 and len(server.VCs) < 5 and len([vc for vc in self.vcs if not vc[1]]) > 0: disabled = False
                            else: disabled = True
                            
                            #choose button style
                            server = Server(guild.id)
                            if len(server.VCs) == 0 and not disabled: style = nextcord.ButtonStyle.blurple
                            else: style = nextcord.ButtonStyle.gray
           
                            super().__init__(label = "Add Channel", style = style, disabled = disabled)
                                                     
                        async def callback(self, interaction: Interaction):
                            selectOptions = [nextcord.SelectOption(label = vc[0].name, value = vc[0].id, description = vc[0].category.name) for vc in [vc for vc in self.vcs if not vc[1]]]
                            
                            description = """Select a Voice Channel to be a Join-To-Create Voice Channel.
                                
                            **Don't See Your Channel?**
                            Make sure InfiniBot has the following permissions in your channel:
                            • View Channel
                            • Manage Channel
                            • Connect"""
                        
                            # On Mobile, extra spaces cause problems. We'll get rid of them here:
                            description = standardizeStrIndention(description)
                            
                            view = SelectView("Dashboard - Join-To-Create-VCs - Add Channel", 
                                              description, 
                                              options = selectOptions, 
                                              returnCommand = self.selectCallback, 
                                              continueButtonLabel = "Add", 
                                              preserveOrder = True, 
                                              placeholder = "Select a Voice Channel")
                            
                            await view.setup(interaction)
                            
                        async def selectCallback(self, interaction: Interaction, selection: str):
                            if selection == None: 
                                await self.outer.refresh(interaction) 
                                return
                            
                            server = Server(interaction.guild.id)
                            server.VCs.append(JoinToCreateVC(interaction.guild, None, id = selection))
                            server.saveVCs()
                            
                            await self.outer.refresh(interaction)
                            
                    class DeleteButton(nextcord.ui.Button):
                        def __init__(self, outer, guild: nextcord.Guild):
                            self.outer = outer
                            
                            server = Server(guild.id)
                            
                            #choose enabled / disabled
                            if len(server.VCs) > 0: disabled = False
                            else: disabled = True
           
                            super().__init__(label = "Delete Channel", style = nextcord.ButtonStyle.gray, disabled = disabled)
                                                        
                        async def callback(self, interaction: Interaction):
                            server = Server(interaction.guild.id)
                            selectOptions = [nextcord.SelectOption(label = vc.channel.name, value = vc.id, description = vc.channel.category.name) for vc in server.VCs]
                                        
                            description = """Select a Join-To-Create Voice Channel to no longer be a Join-To-Create Voice Channel."""
                        
                            # On Mobile, extra spaces cause problems. We'll get rid of them here:
                            description = standardizeStrIndention(description)
                            
                            view = SelectView("Dashboard - Join-To-Create-VCs - Add Channel", 
                                              description, 
                                              options = selectOptions, 
                                              returnCommand = self.selectCallback, 
                                              continueButtonLabel = "Delete", 
                                              preserveOrder = True, 
                                              placeholder = "Select a Voice Channel")
                            
                            await view.setup(interaction)
                            
                        async def selectCallback(self, interaction: Interaction, selection: str):
                            if selection == None: 
                                await self.outer.refresh(interaction)
                                return
                            
                            selection = int(selection)
                            
                            server = Server(interaction.guild.id)
                            
                            for vc in list(server.VCs):
                                if vc.id == selection:
                                    server.VCs.remove(vc)
                                    #we're not going to break to ensure that we delete every instance of this in case something glitched
                            
                            server.saveVCs()
                            
                            await self.outer.refresh(interaction)
                                        
                async def callback(self, interaction: Interaction):
                    await self.ConfigureView(self.outer, interaction.guild).setup(interaction)                      
        
        async def callback(self, interaction: Interaction):
            await self.JoinToCreateVCsView(self.outer).setup(interaction)

    class AutoBansButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Auto-Bans", style = nextcord.ButtonStyle.gray, row = 1)
            self.outer = outer
            
        class AutoBansView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__(timeout=None)
                self.outer = outer
                
                #create buttons
                self.addBtn = self.AddButton(self)
                self.add_item(self.addBtn)
                
                self.revokeBtn = self.RevokeButton(self)
                self.add_item(self.revokeBtn)
                                    
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                                                            
            async def setup(self, interaction: Interaction):
                if interaction.guild.me.guild_permissions.ban_members:
                    server = Server(interaction.guild.id)
                    
                    autoBans = []
                    for autoBan in server.autoBans:
                        autoBans.append(f"• {autoBan.memberName}  (ID: {autoBan.memberID})")
                        
                    if len(autoBans) > 0:
                        autoBansStr = "\n".join(autoBans)
                        autoBansStr = f"```{autoBansStr}```"
                        self.revokeBtn.disabled = False
                    else:
                        autoBansStr = "You don't have any auto-bans yet."
                        self.revokeBtn.disabled = True
                                        
                    description = f"""InfiniBot has the capability to ban members both in your server and after they leave.
                    ✯ You can even ban people who haven't even joined the server yet.
                    
                    **How?**
                    Just right click on a message or member, select \"Apps\" and click \"Ban Message Author\" or \"Ban Member\"                           
                    
                    **Ban Someone Before They Join the Server**
                    Click the "Add" button below, and follow the instructions. You will need the user's Discord ID.               
                    
                    **Revoking Auto-Bans**
                    Click the \"Revoke\" button to begin revoking auto-bans.
                    
                    
                    **Current Auto-Bans**
                    {autoBansStr}"""
                    
                    # On Mobile, extra spaces cause problems. We'll get rid of them here:
                    description = standardizeStrIndention(description)
                            

                else:
                    description = f"InfiniBot doesn't have the \"Ban Members\" permission. This feature requires this permission. Please give InfiniBot this permission, and then reload this page."
                    self.addBtn.disabled = True
                    self.revokeBtn.disabled = True
                    #disable all buttons
                
                embed = nextcord.Embed(title = "Dashboard - Auto-Bans", description = description, color = nextcord.Color.blue())
                await interaction.response.edit_message(embed = embed, view = self)
            
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class AddButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Add", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                                                
                class IDHelp(nextcord.ui.View):
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        self.backBtn.callback = self.backBtnCallback
                        self.add_item(self.backBtn)
                        
                        self.continueBtn = nextcord.ui.Button(label = "I've Copied the ID, Continue", style = nextcord.ButtonStyle.green)
                        self.continueBtn.callback = self.continueBtnCallback
                        self.add_item(self.continueBtn)
                        
                    async def setup(self, interaction: Interaction):
                        description = """In order to ban a member before they have joined, you need their Discord ID. To get this, follow these steps:
                    
                        **On Desktop**
                        • Go to Discord's Settings
                        • Scroll Down to "Advanced"
                        • Enable "Developer Mode"
                        • Exit Settings and Right click on the member whom you would like to auto-ban
                        • Click "Copy ID" (at the very bottom)
                        • Proceed
                        
                        **On Mobile**
                        • Go to Discord's Settings (by clicking your profile icon in the bottom right)
                        • Scroll Down to "Appearance"
                        • Enable "Developer Mode"
                        • Exit Settings and touch and hold on the member whom you would like to auto-ban
                        • Click the three dots in the top right of their profile 
                        • Click "Copy ID"
                        • Proceed
                        """
                        
                        # On Mobile, extra spaces cause problems. We'll get rid of them here:
                        description = standardizeStrIndention(description)

                        
                        embed = nextcord.Embed(title = "Dashboard - Auto-Bans - Add", description = description, color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    class AddModal(nextcord.ui.Modal):
                        def __init__(self, outer):
                            super().__init__(title = "Add Auto-Ban", timeout = None)
                            self.outer = outer
                            self.userName = None
                            self.id = None
                            
                            self.userNameInput = nextcord.ui.TextInput(label = "Discord Name (Not Critical)", placeholder = "BillyBob#1234", max_length = 64)
                            self.add_item(self.userNameInput)
                            
                            self.idInput = nextcord.ui.TextInput(label = "Discord ID (Paste It) (Critical)", placeholder = "12345678910", max_length = 30)
                            self.add_item(self.idInput)
                            
                        async def callback(self, interaction: Interaction): #saving
                            self.stop()
                            
                            userName = self.userNameInput.value
                            id = self.idInput.value
                            
                            embed = None
                            

                            for member in interaction.guild.members:
                                if member.id == int(id):
                                    embed = nextcord.Embed(title = "User Already In Server", description = f"InfiniBot won't add \"{userName} (ID: {id})\" as an auto-ban because they are already in this server ({member.mention}). You can ban them with the /ban command.", color = nextcord.Color.red())
                            
                            if interaction.guild.me.guild_permissions.ban_members == True:
                                async for ban in interaction.guild.bans():
                                    if ban.user.id == int(id):
                                        embed = nextcord.Embed(title = "User Already Banned", description = f"InfiniBot won't add \"{userName} (ID: {id})\" as an auto-ban because they are already banned in this server.", color = nextcord.Color.red())
                            
                            if embed == None:
                                #save data
                                server = Server(interaction.guild.id)
                                
                                server.addAutoBan(userName, id, replace = True)
                                server.saveAutoBans()
                                del server
                            
                            await self.outer.setup(interaction)
                            
                            if embed != None:
                                await interaction.followup.send(embed = embed, ephemeral = True)
                                                        
                    async def continueBtnCallback(self, interaction: Interaction):
                        await interaction.response.send_modal(self.AddModal(self.outer))
                                                
                async def callback(self, interaction: Interaction):              
                    await self.IDHelp(self.outer).setup(interaction)
            
            class RevokeButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Revoke", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                async def callback(self, interaction: Interaction):
                    server = Server(interaction.guild.id)
                    
                    autoBans = []
                    for autoBan in server.autoBans:
                        label = (f"{autoBan.memberName}")
                        autoBans.append(nextcord.SelectOption(label = label, description = f"ID: {autoBan.memberID}", value = autoBan.memberID))
                    
                    await SelectView(title = "Dashboard - Auto-Bans - Revoke", description = "To revoke an auto-ban, select the member, and click \"Revoke Auto-Ban\". They will then be able to join this server without being auto-banned.", options = autoBans, returnCommand = self.selectViewCallback, placeholder = "Select a Member", continueButtonLabel = "Revoke Auto-Ban").setup(interaction)
            
                async def selectViewCallback(self, interaction: Interaction, selection):
                    if selection != None:
                        server = Server(interaction.guild.id)
                        server.deleteAutoBan(selection)
                        server.saveAutoBans()
                    
                    await self.outer.setup(interaction)
            
        async def callback(self, interaction: Interaction):
            await self.AutoBansView(self.outer).setup(interaction)

    class ActiveMessagesButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Active Messages", row = 2)
            self.outer = outer
            
        class ActiveMessagesView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.voteBtn = self.OptionButton(self, "Vote")
                self.add_item(self.voteBtn)
                
                self.reactionRoleBtn = self.OptionButton(self, "Reaction Role")
                self.add_item(self.reactionRoleBtn)
                
                self.embedBtn = self.OptionButton(self, "Embed")
                self.add_item(self.embedBtn)
                
                self.backBtn = nextcord.ui.Button(label = "Back", row = 1)
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
            async def setup(self, interaction: Interaction):
                server = Server(interaction.guild.id)
                description = f"""InfiniBot caches every vote, reaction role, and embedded message posted on this server (using InfiniBot), enabling the ability to edit these messages. However, there is a maximum limit for each type of message. Please refer to the list below to manage your active messages.
                
                Votes ({server.messages.countOf("Vote")}/10)
                Reaction Roles ({server.messages.countOf("Reaction Role")}/10)
                Embeds ({server.messages.countOf("Embed")}/20)"""
                
                # On Mobile, extra spaces cause problems. We'll get rid of them here:
                description = standardizeStrIndention(description)
                
                embed = nextcord.Embed(title = "Dashboard - Active Messages", description = description, color = nextcord.Color.blue())
                await interaction.response.edit_message(embed = embed, view = self)
                
            class OptionButton(nextcord.ui.Button):
                def __init__(self, outer, _type):
                    super().__init__(label = f"Configure {_type}s")
                    self.outer = outer
                    self._type = _type
                    
                class TheView(nextcord.ui.View):
                    def __init__(self, outer, _type):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self._type = _type
                        
                        self.backBtn = nextcord.ui.Button(label = "Back")
                        self.backBtn.callback = self.backBtnCallback
                        self.add_item(self.backBtn)
                        
                        self.refreshBtn = nextcord.ui.Button(label = "Refresh")
                        self.refreshBtn.callback = self.refreshBtnCallback
                        self.add_item(self.refreshBtn)
                        
                    async def setup(self, interaction: Interaction):
                        server = Server(interaction.guild.id)
                        
                        messages = server.messages.getAll(self._type)
                        
                        maxMessages = server.messages.maxOf(self._type)
                        
                        messagesFormatted = []
                        save = False
                        for index, message in enumerate(messages):
                            # Get the Channel
                            discordChannel = await interaction.guild.fetch_channel(message.channel_id)
                            if not discordChannel: 
                                server.messages.delete(message.message_id)
                                save = True
                                continue
                            
                            # Get the Message
                            discordMessage = await discordChannel.fetch_message(message.message_id)
                            if not discordMessage: 
                                server.messages.delete(message.message_id)
                                save = True
                                continue
                            
                            # Create the UI
                            title = discordMessage.embeds[0].title
                            persistent = " 🔒" if message.persistent else ""
                            
                            messagesFormatted.append(f"{index + 1}/{maxMessages}) [{title}]({message.getLink(interaction.guild.id)}){persistent}")
                            
                        # Save if needed
                        server.messages.save()
                            
                        if messagesFormatted == []:
                            messagesFormatted.append(f"You don't have any active {self._type}s yet! Create one!")
                        
                        messagesFormatted_String = '\n'.join(messagesFormatted)
                        
                        embed = nextcord.Embed(title = f"Dashboard - Active Messages - {self._type}s",
                                               description = f"Mange your active {self._type}s here. The 🔒 symbol indicates that the message is persistent. \n\nTo enable / disable persistency, go to the message, right click, go to `Apps → Edit → Prioritize / Deprioritize`\n\n**Active {self._type}s**\n{messagesFormatted_String}",
                                               color = nextcord.Color.blue())
                        
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                            
                    async def refreshBtnCallback(self, interaction: Interaction):
                        await self.setup(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.TheView(self.outer, self._type).setup(interaction)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
        async def callback(self, interaction: Interaction):
            await self.ActiveMessagesView(self.outer).setup(interaction)
        
    class EnableDisableButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Enable / Disable Features", style = nextcord.ButtonStyle.gray, row = 2)
            self.outer = outer
            
        class EnableDisableView(nextcord.ui.View):
            def __init__(self, outer, guildID):
                super().__init__(timeout = None)
                self.outer = outer
                self.server = Server(guildID)
                
                self.profanityBtn = self.EnableDisableButton(self, "Profanity Moderation", self.server)
                self.add_item(self.profanityBtn)
                
                self.spamBtn = self.EnableDisableButton(self, "Spam Moderation", self.server)
                self.add_item(self.spamBtn)
                
                self.loggingBtn = self.EnableDisableButton(self, "Logging", self.server, row = 1)
                self.add_item(self.loggingBtn)
                
                self.levelingBtn = self.EnableDisableButton(self, "Leveling", self.server, row = 1)
                self.add_item(self.levelingBtn)
                
                self.autoDeleteInvitesBtn = self.EnableDisableButton(self, "Delete Invites", self.server, row = 1)
                self.add_item(self.autoDeleteInvitesBtn)
                
                self.getUpdatesBtn = self.EnableDisableButton(self, "Update Messages", self.server, row = 2)
                self.add_item(self.getUpdatesBtn)
                
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 3)
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
            async def setup(self, interaction: Interaction):
                for child in self.children: 
                    del child 
                    self.__init__(self.outer, interaction.guild.id)
                
                self.server = Server(interaction.guild.id)
                
                settingsValue = f"""
                {self.boolToString(self.server.profanityBool)} - Profanity Moderation
                {self.boolToString(self.server.spamBool)} - Spam Moderation
                {self.boolToString(self.server.loggingBool)} - Logging
                {self.boolToString(self.server.levelingBool)} - Leveling
                {self.boolToString(self.server.deleteInvitesBool)} - Delete Invites
                {self.boolToString(self.server.getUpdates)} - Update Messages
                """
                
                # On Mobile, extra spaces cause problems. We'll get rid of them here:
                settingsValue = standardizeStrIndention(settingsValue)
                
                embed = nextcord.Embed(title = "Dashboard - Enable / Disable Panel", description = f"Choose a feature to enable / disable", color = nextcord.Color.blue())
                embed.add_field(name = "Settings", value = settingsValue, inline = True)
                await interaction.response.edit_message(embed = embed, view = self)
             
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                
            def boolToString(self, bool: bool):
                if bool:
                    return "✅"
                else:
                    return "❌"
                                    
            class EnableDisableButton(nextcord.ui.Button):
                def __init__(self, outer, title, server, row = 0):
                    super().__init__(label = title, style = nextcord.ButtonStyle.gray, row = row)
                    self.outer = outer
                    self.title = title
                    self.server = server
                    
                class ChooseView(nextcord.ui.View):
                    def __init__(self, outer, title, server):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.title = title
                        self.server: Server = server
                        
                        if self.findVariable(self.title, False):
                            self.choice = "Disable"
                        else:
                            self.choice = "Enable"
                        
                        self.cancelBtn = nextcord.ui.Button(label = "Cancel", style = nextcord.ButtonStyle.danger)
                        self.cancelBtn.callback = self.cancelBtnCommand
                        self.add_item(self.cancelBtn)
                        
                        self.choiceBtn = nextcord.ui.Button(label = self.choice, style = nextcord.ButtonStyle.green)
                        self.choiceBtn.callback = self.choiceBtnCommand
                        self.add_item(self.choiceBtn)
                        
                    async def setup(self, interaction: Interaction):
                        embed = nextcord.Embed(title = f"Enable / Disable {self.title}", description = f"To {self.choice.lower()} {self.title}, click the button \"{self.choice}\"", color = nextcord.Color.blue())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def cancelBtnCommand(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    async def choiceBtnCommand(self, interaction: Interaction):
                        self.findVariable(self.title, True)
                        
                        self.server.saveData()
                        
                        await self.outer.setup(interaction)
                        
                    def findVariable(self, name, change: bool):
                        if name == "Profanity Moderation": 
                            if change: self.server.profanityBool = not self.server.profanityBool
                            return self.server.profanityBool
                        if name == "Spam Moderation": 
                            if change: self.server.spamBool = not self.server.spamBool
                            return self.server.spamBool
                        if name == "Logging": 
                            if change: self.server.loggingBool = not self.server.loggingBool
                            return self.server.loggingBool
                        if name == "Leveling": 
                            if change: self.server.levelingBool = not self.server.levelingBool
                            return self.server.levelingBool
                        if name == "Delete Invites": 
                            if change: self.server.deleteInvitesBool = not self.server.deleteInvitesBool
                            return self.server.deleteInvitesBool
                        if name == "Update Messages":
                            if change: self.server.getUpdates = not self.server.getUpdates
                            return self.server.getUpdates
                        
                    
                        print("ERROR: Button Name does not correspond with possible values in ChooseView.findVariable")
                        return None
                 
                async def callback(self, interaction: Interaction):
                    await self.ChooseView(self.outer, self.title, self.server).setup(interaction)
                       
        async def callback(self, interaction: Interaction):
            await self.EnableDisableView(self.outer, interaction.guild.id).setup(interaction)       


class Profile(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        levelCardButton = self.LevelCardButton(self)
        self.add_item(levelCardButton)
        
        joinCardButton = self.JoinCardButton(self)
        self.add_item(joinCardButton)
        
        settingsButton = self.SettingsButton(self)
        self.add_item(settingsButton)
        
    async def setup(self, interaction: Interaction):
        for child in self.children: del child
        self.__init__()
    
    
    
        description = f"""Welcome to your InfiniBot Profile! Choose a setting:"""
        
        # On Mobile, extra spaces cause problems. We'll get rid of them here:
        description = standardizeStrIndention(description)
        
        
        embed = nextcord.Embed(title = "Profile", description = description, color = nextcord.Color.blurple())
        try: await interaction.response.edit_message(embed = embed, view = self)
        except: await interaction.response.send_message(embed = embed, view = self, ephemeral=True)
   
    class LevelCardButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Level-Up Card", style = nextcord.ButtonStyle.gray)
            self.outer = outer
            
        class LevelCardView(nextcord.ui.View):
            def __init__(self, outer, interaction: Interaction):
                super().__init__(timeout = None)
                self.outer = outer
                
                member = Member(interaction.user.id)
                
                if member.levelCard.enabled:
                    changeTextBtn = self.ChangeTextButton(self)
                    self.add_item(changeTextBtn)
                    
                    changeColorBtn = self.ChangeColorButton(self)
                    self.add_item(changeColorBtn)
                    
                enableDisableBtn = self.EnableDisableButton(self, member.levelCard.enabled)
                self.add_item(enableDisableBtn)
                
                
                backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                backBtn.callback = self.backBtnCallback
                self.add_item(backBtn)
                
            async def setup(self, interaction: Interaction):
                enabledDescription = """**What is a level-up card?**
                Whenever you level-up with InfiniBot, your level-up message will contain this card:"""
                
                disabledDescription = """**What is a level-up card?**
                Whenever you level-up with InfiniBot, your level-up message can contain a personalizable card. Click "Enable" to begin!"""
                
                # On Mobile, extra spaces cause problems. We'll get rid of them here:
                enabledDescription = standardizeStrIndention(enabledDescription)
                disabledDescription = standardizeStrIndention(disabledDescription)
                
                
                member = Member(interaction.user.id)
                
                
                embed = nextcord.Embed(title = "Profile - Level-Up Card", description = (enabledDescription if member.levelCard.enabled else disabledDescription), color = nextcord.Color.blurple())
                
                #get the card
                if member.levelCard.enabled:
                    card = member.levelCard.embed()
                    embeds = [embed, card]
                else:
                    embeds = [embed]
                    
                del member #we don't need member anymore
                
                await interaction.response.edit_message(embeds = embeds, view = self)
               
            async def reload(self, interaction: Interaction):
                self.__init__(self.outer, interaction)
                await self.setup(interaction)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class ChangeTextButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Change Text", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class ChangeTextModal(nextcord.ui.Modal):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(title = "Level-Up Card", timeout = None)
                        self.outer = outer
                        
                        member = Member(interaction.user.id)
                        title = member.levelCard.title
                        description = member.levelCard.description
                        del member #we don't need it anymore
                        
                        self.titleTextInput = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, max_length = 256, default_value = title, placeholder = "Yum... Levels.")
                        self.add_item(self.titleTextInput)
                        
                        self.descriptionTextInput = nextcord.ui.TextInput(label = "Description ([level] = level)", style = nextcord.TextInputStyle.paragraph, max_length = 4000, default_value = description, placeholder = "Level [level]!")
                        self.add_item(self.descriptionTextInput)
                        
                    async def callback(self, interaction: Interaction):
                        title = self.titleTextInput.value
                        description = self.descriptionTextInput.value
                        
                        member = Member(interaction.user.id)
                        member.levelCard.title = title
                        member.levelCard.description = description
                        
                        member.save()
                        del member
                        
                        #send them back
                        await self.outer.setup(interaction)             
                    
                async def callback(self, interaction: Interaction):
                    await interaction.response.send_modal(self.ChangeTextModal(self.outer, interaction))
   
            class ChangeColorButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Change Color", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class ChangeColorView(nextcord.ui.View):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        options = ["Red", "Green", "Blue", "Yellow", "White", "Blurple", "Greyple", "Teal", "Purple", "Gold", "Magenta", "Fuchsia"]
                
                        selectOptions = []
                        for option in options:
                            selectOptions.append(nextcord.SelectOption(label = option, value = option))
                                
                        
                        self.select = nextcord.ui.Select(options = selectOptions, placeholder = "Select a Color")
                        self.add_item(self.select)
                        
                               
                        backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        backBtn.callback = self.backBtnCallback
                        self.add_item(backBtn)
                        
                        updateBtn = nextcord.ui.Button(label = "Update", style = nextcord.ButtonStyle.green, row = 1)
                        updateBtn.callback = self.updateBtnCallback
                        self.add_item(updateBtn)
                        
                    async def setup(self, interaction: Interaction):
                        description = f"""**Colors Available**
                        Red, Green, Blue, Yellow, White
                        Blurple, Greyple, Teal, Purple
                        Gold, Magenta, Fuchsia"""
                        
                        # On Mobile, extra spaces cause problems. We'll get rid of them here:
                        description = standardizeStrIndention(description)


                        embed = nextcord.Embed(title = "Profile - Level-Up Card - Change Color", description = description, color = nextcord.Color.blurple())
                        
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    async def updateBtnCallback(self, interaction: Interaction):
                        if len(self.select.values) != 1: 
                            await self.outer.setup(interaction)
                            return
                        
                        member = Member(interaction.user.id)
                        member.levelCard.color = self.select.values[0]
                        member.save()
                        del member #we don't need it anymore
                        
                        await self.outer.setup(interaction)
                                           
                async def callback(self, interaction: Interaction):
                    await self.ChangeColorView(self.outer, interaction).setup(interaction)
   
            class EnableDisableButton(nextcord.ui.Button):
                def __init__(self, outer, enabled):
                    self.enabled = ("Disable" if enabled else "Enable")
                    super().__init__(label = self.enabled, style = (nextcord.ButtonStyle.gray if enabled else nextcord.ButtonStyle.green))
                    self.outer = outer
                    
                class EnableDisableView(nextcord.ui.View):
                    def __init__(self, outer, enabled):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.enabled = enabled
                        
                        backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        backBtn.callback = self.backBtnCallback
                        self.add_item(backBtn)
                        
                        button = self.Button(self.outer, self.enabled)
                        self.add_item(button)          
                        
                    async def setup(self, interaction: Interaction):
                        embed = nextcord.Embed(title = f"Profile - Level-Up Card - {self.enabled}", description = "**What is a level-up card?**\nIf enabled, this personalizable level-up card will be displayed after each of your level-up messages. (As long as the server permits it)", color = nextcord.Color.blurple())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    class Button(nextcord.ui.Button):
                        def __init__(self, outer, label):
                            super().__init__(label = label, style = nextcord.ButtonStyle.green)
                            self.outer = outer
                            
                        async def callback(self, interaction: Interaction):
                            member = Member(interaction.user.id)
                            member.levelCard.enabled = not member.levelCard.enabled
                            member.save()
                            
                            await self.outer.reload(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.EnableDisableView(self.outer, self.enabled).setup(interaction)
   
        async def callback(self, interaction: Interaction):
            await self.LevelCardView(self.outer, interaction).setup(interaction)
      
    class JoinCardButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Join Card", style = nextcord.ButtonStyle.gray)
            self.outer = outer
            
        class JoinCardView(nextcord.ui.View):
            def __init__(self, outer, interaction: Interaction):
                super().__init__(timeout = None)
                self.outer = outer
                
                member = Member(interaction.user.id)
                
                if member.joinCard.enabled:
                    changeTextBtn = self.ChangeTextButton(self)
                    self.add_item(changeTextBtn)
                    
                    changeColorBtn = self.ChangeColorButton(self)
                    self.add_item(changeColorBtn)
                    
                enableDisableBtn = self.EnableDisableButton(self, member.joinCard.enabled)
                self.add_item(enableDisableBtn)
                
                
                backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                backBtn.callback = self.backBtnCallback
                self.add_item(backBtn)
                
            async def setup(self, interaction: Interaction):
                enabledDescription = """**What is a join card?**
                Whenever you join with InfiniBot, your join message will contain this card:"""
                
                disabledDescription = """**What is a join card?**
                Whenever you join with InfiniBot, your join message can contain a personalizable card. Click "Enable" to begin!"""
                
                # On Mobile, extra spaces cause problems. We'll get rid of them here:
                enabledDescription = standardizeStrIndention(enabledDescription)
                disabledDescription = standardizeStrIndention(disabledDescription)
                
                
                member = Member(interaction.user.id)
                
                
                embed = nextcord.Embed(title = "Profile - Join Card", description = (enabledDescription if member.joinCard.enabled else disabledDescription), color = nextcord.Color.blurple())
                
                #get the card
                if member.joinCard.enabled:
                    card = member.joinCard.embed()
                    embeds = [embed, card]
                else:
                    embeds = [embed]
                    
                del member #we don't need member anymore
                
                await interaction.response.edit_message(embeds = embeds, view = self)
               
            async def reload(self, interaction: Interaction):
                self.__init__(self.outer, interaction)
                await self.setup(interaction)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class ChangeTextButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Change Text", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class ChangeTextModal(nextcord.ui.Modal):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(title = "Join Card", timeout = None)
                        self.outer = outer
                        
                        member = Member(interaction.user.id)
                        title = member.joinCard.title
                        description = member.joinCard.description
                        del member #we don't need it anymore
                        
                        self.titleTextInput = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, max_length = 256, default_value = title, placeholder = "About Me")
                        self.add_item(self.titleTextInput)
                        
                        self.descriptionTextInput = nextcord.ui.TextInput(label = "Description", style = nextcord.TextInputStyle.paragraph, max_length = 4000, default_value = description, placeholder = "I am human")
                        self.add_item(self.descriptionTextInput)
                        
                    async def callback(self, interaction: Interaction):
                        title = self.titleTextInput.value
                        description = self.descriptionTextInput.value
                        
                        member = Member(interaction.user.id)
                        member.joinCard.title = title
                        member.joinCard.description = description
                        
                        member.save()
                        del member
                        
                        #send them back
                        await self.outer.setup(interaction)             
                    
                async def callback(self, interaction: Interaction):
                    await interaction.response.send_modal(self.ChangeTextModal(self.outer, interaction))
   
            class ChangeColorButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Change Color", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
                    
                class ChangeColorView(nextcord.ui.View):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        options = ["Red", "Green", "Blue", "Yellow", "White", "Blurple", "Greyple", "Teal", "Purple", "Gold", "Magenta", "Fuchsia"]
                
                        selectOptions = []
                        for option in options:
                            selectOptions.append(nextcord.SelectOption(label = option, value = option))
                                
                        
                        self.select = nextcord.ui.Select(options = selectOptions, placeholder = "Select a Color")
                        self.add_item(self.select)
                        
                               
                        backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                        backBtn.callback = self.backBtnCallback
                        self.add_item(backBtn)
                        
                        updateBtn = nextcord.ui.Button(label = "Update", style = nextcord.ButtonStyle.green, row = 1)
                        updateBtn.callback = self.updateBtnCallback
                        self.add_item(updateBtn)
                        
                    async def setup(self, interaction: Interaction):
                        description = f"""**Colors Available**
                        Red, Green, Blue, Yellow, White
                        Blurple, Greyple, Teal, Purple
                        Gold, Magenta, Fuchsia"""
                        
                        # On Mobile, extra spaces cause problems. We'll get rid of them here:
                        description = standardizeStrIndention(description)


                        embed = nextcord.Embed(title = "Profile - Join Card - Change Color", description = description, color = nextcord.Color.blurple())
                        
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    async def updateBtnCallback(self, interaction: Interaction):
                        if len(self.select.values) != 1: 
                            await self.outer.setup(interaction)
                            return
                        
                        member = Member(interaction.user.id)
                        member.joinCard.color = self.select.values[0]
                        member.save()
                        del member #we don't need it anymore
                        
                        await self.outer.setup(interaction)
                                           
                async def callback(self, interaction: Interaction):
                    await self.ChangeColorView(self.outer, interaction).setup(interaction)
   
            class EnableDisableButton(nextcord.ui.Button):
                def __init__(self, outer, enabled):
                    self.enabled = ("Disable" if enabled else "Enable")
                    super().__init__(label = self.enabled, style = (nextcord.ButtonStyle.gray if enabled else nextcord.ButtonStyle.green))
                    self.outer = outer
                    
                class EnableDisableView(nextcord.ui.View):
                    def __init__(self, outer, enabled):
                        super().__init__(timeout = None)
                        self.outer = outer
                        self.enabled = enabled
                        
                        backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        backBtn.callback = self.backBtnCallback
                        self.add_item(backBtn)
                        
                        button = self.Button(self.outer, self.enabled)
                        self.add_item(button)          
                        
                    async def setup(self, interaction: Interaction):
                        embed = nextcord.Embed(title = f"Profile - Join Card - {self.enabled}", description = "**What is a join card?**\nIf enabled, this personalizable join card will be attached to your join message every time you join a server with InfiniBot. (As long as the server permits it)", color = nextcord.Color.blurple())
                        await interaction.response.edit_message(embed = embed, view = self)
                        
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    class Button(nextcord.ui.Button):
                        def __init__(self, outer, label):
                            super().__init__(label = label, style = nextcord.ButtonStyle.green)
                            self.outer = outer
                            
                        async def callback(self, interaction: Interaction):
                            member = Member(interaction.user.id)
                            member.joinCard.enabled = not member.joinCard.enabled
                            member.save()
                            
                            await self.outer.reload(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.EnableDisableView(self.outer, self.enabled).setup(interaction)
   
        async def callback(self, interaction: Interaction):
            await self.JoinCardView(self.outer, interaction).setup(interaction)
    
    class SettingsButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Settings", style = nextcord.ButtonStyle.gray, row = 1)
            self.outer = outer
            
        class SettingsView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                dmsButton = self.DmsButton(self)
                self.add_item(dmsButton)
                
                dataButton = self.DataButton(self)
                self.add_item(dataButton)
                
                backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1)
                backBtn.callback = self.backBtnCallback
                self.add_item(backBtn)
            
            async def setup(self, interaction: Interaction):
                def icon(bool):
                    if bool:
                        return "✅"
                    return "❌"
                
                member = Member(interaction.user.id)
                
                description = f"""Configure InfiniBot to fit your needs.
                
                {icon(member.dmsEnabledBool)} Direct Messages Enabled"""
                
                # On Mobile, extra spaces cause problems. We'll get rid of them here:
                description = standardizeStrIndention(description)
                
                embed = nextcord.Embed(title = "Profile - Settings", description = description, color = nextcord.Color.blurple())
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
        
            class DmsButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Direct Messages", style = nextcord.ButtonStyle.gray)
                    self.outer = outer
        
                class DmsView(nextcord.ui.View):
                    def __init__(self, outer, interaction: Interaction):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        backBtn.callback = self.backBtnCallback
                        self.add_item(backBtn)
                        
                        
                        member = Member(interaction.user.id)
                        if member.dmsEnabledBool: label = "Disable"
                        else: label = "Enable"
                        
                        button = nextcord.ui.Button(label = label, style = nextcord.ButtonStyle.green)
                        button.callback = self.callback
                        self.add_item(button)
                        
                    async def setup(self, interaction: Interaction):
                        member = Member(interaction.user.id)
                        
                        if member.dmsEnabledBool: description = "To disable Direct Messages from InfiniBot, click the button \"Disable\"\n\nBy doing this, you will no longer recieve permission errors, birthday updates, or strike notices."
                        else: description = "To enable Direct Messages from InfiniBot, click the button \"Enable\"\n\nBy doing this, you will now recieve permission errors, birthday updates, and strike notices."
                        
                        embed = nextcord.Embed(title = "Profile - Settings - Direct Messages", description = description, color = nextcord.Color.blurple())
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    async def callback(self, interaction: Interaction):
                        member = Member(interaction.user.id)
                        member.dmsEnabledBool = not member.dmsEnabledBool
                        
                        member.save()
                        
                        await self.outer.setup(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.DmsView(self.outer, interaction).setup(interaction)
        
            class DataButton(nextcord.ui.Button):
                def __init__(self, outer):
                    super().__init__(label = "Delete My Data", style = nextcord.ButtonStyle.gray)
                    self.outer = outer       
                    
                class DataView(nextcord.ui.View):
                    def __init__(self, outer):
                        super().__init__(timeout = None)
                        self.outer = outer
                        
                        backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                        backBtn.callback = self.backBtnCallback
                        self.add_item(backBtn)
                        
                        button = nextcord.ui.Button(label = "Confirm", style = nextcord.ButtonStyle.green)
                        button.callback = self.callback
                        self.add_item(button)            
                    
                    async def setup(self, interaction: Interaction):
                        description = """By deleting your data, you will delete all your profile information associated with InfiniBot. This action is not reversable.
                        
                        This will not delete:
                        • Any message logs inside a server
                        • Any strikes, levels, etc in any server (you can delete these simply by leaving that server)
                        
                        Click "Confirm" to delete all your profile information.
                        """
                        
                        # On Mobile, extra spaces cause problems. We'll get rid of them here:
                        description = standardizeStrIndention(description)
                        
                        embed = nextcord.Embed(title = "Profile - Settings - Delete My Data", description = description, color = nextcord.Color.blurple())
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                        
                    async def callback(self, interaction: Interaction):
                        member = Member(interaction.user.id)
                        member.delete()
                        
                        await self.outer.setup(interaction)
                    
                async def callback(self, interaction: Interaction):
                    await self.DataView(self.outer).setup(interaction)           
        
        async def callback(self, interaction: Interaction):
            await self.SettingsView(self.outer).setup(interaction)
    

#Real Code (YAY) ------------------------------------------------------------------------------------------------------------------------------------------------


    
  
@bot.slash_command(name = "opt_into_dms", description = "Opt out of dm notifications from InfiniBot.")
async def opt_into_dms(interaction: Interaction):
    member = Member(interaction.user.id)
    
    if member.dmsEnabledBool == True: 
        await interaction.response.send_message(embed = nextcord.Embed(title = "Already opted into DMs", description = "You are already opted into dms.", color = nextcord.Color.blue()), ephemeral = True)
        return
    
    member.dmsEnabledBool = True
    member.save()
    
    embed = nextcord.Embed(title = "Opted Into DMs", description = f"You opted into DMs from InfiniBot. You will now recieve permission errors, birthday updates, or strike notices.", color = nextcord.Color.green())
    await interaction.response.send_message(embed = embed, ephemeral = True)
    
    dm = await interaction.user.create_dm()
    await dm.send(embed = embed)
    
@bot.slash_command(name = "opt_out_of_dms", description = "Opt out of dm notifications from InfiniBot.")
async def opt_out_of_dms(interaction: Interaction):
    member = Member(interaction.user.id)
    
    if member.dmsEnabledBool == False: 
        await interaction.response.send_message(embed = nextcord.Embed(title = "Already opted out of DMs", description = "You are already opted out of dms.", color = nextcord.Color.blue()), ephemeral = True)
        return
    
    member.dmsEnabledBool = False
    member.save()
    
    embed = nextcord.Embed(title = "Opted Out of DMs", description = f"You opted out of DMs from InfiniBot. You will no longer recieve permission errors, birthday updates, or strike notices. To re-opt-into this feature, use {opt_into_dms.get_mention()}", color = nextcord.Color.green())
    await interaction.response.send_message(embed = embed, ephemeral = True)
    
    dm = await interaction.user.create_dm()
    await dm.send(embed = embed)




viewsInitialized = False
@bot.event#------------------------------------------------------------------------
async def on_ready():
    global viewsInitialized
    
    await bot.wait_until_ready()
    
    if not viewsInitialized:
        bot.add_view(IncorrectButton())
        bot.add_view(ShowMoreButton())
        bot.add_view(ErrorWhyAdminPrivilegesButton())
        viewsInitialized = True
        
    print(f"Logged in as: {bot.user.name}")
    
    
    #login response stuff
    if (main.login_response_guildID != None and main.login_response_channelID != None):
        #get guild and channel
        guild = None
        for _guild in bot.guilds:
            if _guild.id == main.login_response_guildID:
                guild = _guild
                break
        
        if guild != None:
            channel = None
            for _channel in guild.channels:
                if _channel.id == main.login_response_channelID:
                    channel = _channel
                    break
            
            if channel != None:
                embed = nextcord.Embed(title = "InfiniBot Loaded", description = "InfiniBot has been completely loaded.", color = nextcord.Color.green())
                await channel.send(embed = embed)
        
        main.login_response_guildID = None
        main.login_response_channelID = None
        main.savePersistentData()
        
    if (main.login_response_guildID != None or main.login_response_channelID != None):
        main.login_response_guildID = None
        main.login_response_channelID = None
        main.savePersistentData()
    
    #run every minute
    await runEveryMinute()



   
       



@bot.slash_command(name = "view", description = "Requires Infinibot Mod", dm_permission=False)
async def view(interaction: Interaction):
    pass

@bot.slash_command(name = "set", description = "Requires Infinibot Mod", dm_permission=False)
async def set(interaction: Interaction):
    pass

@bot.slash_command(name = "create", description = "Requires Infinibot Mod", dm_permission=False)
async def create(interaction: Interaction):
    pass






#Manage Joining and Leaving: -----------------------------------------------------------------------------------------------------------------------------------------------------------------
@bot.event
async def on_guild_join(guild: nextcord.Guild):
    # Prepare a list of Embeds
    embeds = []
    
    # Greetings Embed --------------------------------------------------------------------------------------------
    join_message = f"""
    Hello! I am InfiniBot! Here's what you need to know:
    
    
    1) Assign the role \"Infinibot Mod\" to anyone and they will have access to exclusive admin-only features!
    
    2) Make sure that the Infinibot role is the highest role. If this requirement is not met, some features may not function as expected.
        → Alternatively, give InfiniBot Administrator  
    
    You're all set up! Type {dashboard.get_mention()} to get started or {help.get_mention()} for help.
    
    For any help or suggestions, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    join_message = standardizeStrIndention(join_message)
    
    greetingsEmbed = nextcord.Embed(title = "Greetings!", description = join_message, color = nextcord.Color.gold())
    embeds.append(greetingsEmbed)
    
    
    
    # Handle Permissions ------------------------------------------------------------------------------------------
    _globalPermissions, _channelPermissions = neededPermissions(guild)
    
    # Handle Global Permissions Embed Content
    if len(_globalPermissions) > 0:
        globalPermissionsStr = "\n".join([f"• {permission}" for permission in _globalPermissions])
        globalPermissionsEmbed = nextcord.Embed(title = "Wait! InfiniBot still needs some permissions!", description = f"InfiniBot is missing the following permissions:\n{globalPermissionsStr}\n\nAlternatively, give InfiniBot Administrator Priveleges.", color = nextcord.Color.red())
        embeds.append(globalPermissionsEmbed)
        
    # Handle Channel Permissions Embed Content
    if len(_channelPermissions) > 0:
        channelPermissionsEmbed = nextcord.Embed(title = "InfiniBot also needs some permissions in these channels:", color = nextcord.Color.red())
        for package in _channelPermissions:
            permissions = "\n".join([f"• {permission}" for permission in package[1]])
            channelPermissionsEmbed.add_field(name = str(package[0]), value = permissions)
        embeds.append(channelPermissionsEmbed)
        
    if not guild.me.guild_permissions.manage_roles and (getInfinibotModRoleId(guild) == None):
        infiniBotModEmbed = nextcord.Embed(title = "InfiniBot Mod Role Can't Generate", description = "Because InfiniBot does not have the \"Manage Roles\" permission, it can't create an important role called \"InfiniBot Mod\". Grant InfiniBot this permission, and the role should appear.", color = nextcord.Color.red())
        embeds.append(infiniBotModEmbed)
    
    # Send Embeds -------------------------------------------------------------------------------------------------
    channel = await getChannel(guild)
    view = SupportInviteTopGGVoteAndPermissionsCheckView()
    if channel != None: await channel.send(embeds = embeds, view=view)
    else: 
        try:
            dm = await guild.owner.create_dm()
            await dm.send(embeds = embeds, view=view)
        except Exception as err:
            print(err)
            return

@bot.event
async def on_guild_remove(guild: nextcord.Guild):
    server = Server(guild.id)
    server.deleteServer()
#Manage Joining and Leaving END: -------------------------------------------------------------------------------------------------------------------------------------------------------------






# ON MESSAGE =================================================================================================================================================================================
@bot.event
async def on_message(message: nextcord.Message):
    global guildsCheckingForRole
    
    if message == None: return
    
    # DM Commands ---------------------------------------------
    if message.guild == None: 
        if message.content.lower() == "clear":
            for message in await message.channel.history().flatten():
                if message.author.id == bot.application_id:
                    await message.delete()
                    
        elif message.content.lower() == "del":
            for message in await message.channel.history().flatten():
                if message.author.id == bot.application_id:
                    await message.delete()
                    return
                
        await adminCommands(message)    
        return
    
    
    # Regular Functionality
    server = Server(message.guild.id)
    await checkForExpiration(server)
    
    # Check for InfiniBot Mod Role Existence
    await checkForRole(message.guild)
    if message.guild.id in guildsCheckingForRole: guildsCheckingForRole.remove(message.guild.id)
    
    # Don't do any of this if this is a bot
    if message.author.bot:
        return

    # Profanity
    Profane = False
    if server.profanityBool:
        Profane = await punnishProfanity(server, message)
       

    # Other Things
    if not Profane:
        # Check Invites
        if server.deleteInvitesBool and not message.author.guild_permissions.administrator:
            if "discord.gg/" in message.content.lower(): await message.delete()
        # Check spam
        if server.spamBool and not message.author.guild_permissions.administrator:
            await checkSpam(message, server)
        # Give levels
        if server.levelingBool: await giveLevels(message)
        await adminCommands(message)


    # Continue with the Rest of the Bot Commands
    await bot.process_commands(message)








# RUN EVERY MINUTE ===========================================================================================================================================================================
dbl_token = ""
with open("./RequiredFiles/TOKEN.txt", "r") as file:
    dbl_token = file.read().split("\n")[1]
    
if dbl_token != "NONE":
    import topgg
    bot.topggpy = topgg.DBLClient(bot, dbl_token)

async def runEveryMinute():
    while True:
        currentTime = datetime.datetime.now()
        if currentTime.minute == 59: 
            if currentTime.hour != 23: 
                nextTime = f"{str(currentTime.day)}/{str(currentTime.month)}/{str(currentTime.year)} {str(currentTime.hour + 1)}:0:0"
            else: 
                nextTime = f"{str(currentTime.day + 1)}/{str(currentTime.month)}/{str(currentTime.year)} 0:0:0"

        else: 
            nextTime = f"{str(currentTime.day)}/{str(currentTime.month)}/{str(currentTime.year)} {str(currentTime.hour)}:{str(currentTime.minute + 1)}:0"

        nextTime = datetime.datetime.strptime(nextTime, f'%d/%m/%Y %H:%M:%S')

        deltaTime = nextTime - currentTime
        deltaTime = deltaTime.seconds
        if deltaTime == 0: deltaTime = 60

        #uncomment for telemetry
        #print("Current Time:", currentTime) # print("Next Time:", nextTime) print("Delta Time:", deltaTime)
        
        if dbl_token != "NONE":
            try:
                await bot.topggpy.post_guild_count(shard_count = bot.shard_count)
            except Exception as e:
                if type(e) == topgg.Unauthorized:
                    print("Unauthorized Token")
                else:
                    print(f"Failed to post server count\n{e.__class__.__name__}: {e}")
                    
                continue

        await asyncio.sleep(int(deltaTime))
        
        


        #actually check for birthdays
        if nextTime.hour == 8 and nextTime.minute == 0: #run at 8:00 AM every day
            await checkForBirthdays(nextTime, currentTime)
        
        if nextTime.hour == 0 and nextTime.minute == 1: #run at midnight + 1 (because [0 hours 0 minutes] is never reached for some reason)
            print("Checking Levels --------------------")
            allGuildIDs = [guild.id for guild in bot.guilds]
            for guild in bot.guilds:
                try:
                    if not guild.id in allGuildIDs: continue
                    
                    server = Server(guild.id)
                    if server == None or server.guild == None: continue
                    if server.levelingBool == False: continue
                    if server.pointsLostPerDay == None: continue
                    if server.pointsLostPerDay == 0: continue
                    
                    for level in server.levels.allMembers:
                        try:
                            level.score -= server.pointsLostPerDay
                            if level.score <= 0:
                                server.levels.deleteMember(level.memberID)
                        except Exception as err:
                            print(f"ERROR When checking levels (member): {err}")
                            continue
                    
                    server.saveLevels()
                    
                    for member in server.levels.allMembers:
                        await checkForLevelsAndLevelRewards(server.guild, member.member)
                    
                    del server
                    
                except Exception as err:
                    print(f"ERROR When checking levels (server): {err}")
                    continue
    







# GENERAL FUNCTIONS ==========================================================================================================================================================================
async def sendErrorMessageToOwner(guild: nextcord.Guild, permission, message = None, administrator = True, channel = None, guildPermission = False):
    """Sends an error message to the owner of the server via dm
    
    -----------------------
    NEEDS TO BE AWAITED
    
    Returns None
    
    -----------------------
    Args:
        guild (nextcord.Guild): the guild in which the error occured
        permission (str): the permission needed
        -----------------
    Optional Args:
        message (str): a custom message to send (the opt out info is appended to this). Defaults to None.
        administrator (bool): Whether to include info about giving InfiniBot adminstrator. Defaults to True.
        channel (str): the channel where the permission is needed. Defaults to None (meaning the message says "one or more channels").
        guildPermission (bool): whether the permission is a guild permission. If so, channel (↑) is overwritten. Defaults to False.
    """
    
    member = guild.owner
    
    if member == None: return
    memberSettings = Member(member.id)
    if not memberSettings.dmsEnabledBool: return
    
    if channel != None:
        channels = channel
    else:
        channels = "one or more channels"
        
    if guildPermission:
        inChannels = ""
    else:
        inChannels = f" in {channels}"
        
    
    
    if message == None:
        if permission != None: 
            embed = nextcord.Embed(title = f"Missing Permissions in in \"{guild.name}\" Server", description = f"InfiniBot is missing the **{permission}** permission{inChannels}.\n\nWe advise that you grant InfiniBot administrator privileges so that this is no longer a concern.\n\nTo opt out of dm notifications, use {opt_out_of_dms.get_mention()}", color = nextcord.Color.red())
        else:
            embed = nextcord.Embed(title = f"Missing Permissions in \"{guild.name}\" Server", description = f"InfiniBot is missing a permission{inChannels}.\n\nWe advise that you grant InfiniBot administrator privileges so that this is no longer a concern.\n\nTo opt out of dm notifications, use {opt_out_of_dms.get_mention()}", color = nextcord.Color.red())
    else:
        embed = nextcord.Embed(title = f"Missing Permissions in \"{guild.name}\" Server", description = f"{message}\n\nTo opt out of dm notifications, use {opt_out_of_dms.get_mention()}", color = nextcord.Color.red())

    embed.timestamp = datetime.datetime.now()

    try:
        dm = await member.create_dm()
        if administrator:
            await dm.send(embed = embed, view = ErrorWhyAdminPrivilegesButton())
        else:
            await dm.send(embed = embed)
    except:
        return

async def getChannel(guild: nextcord.Guild):
    if guild.system_channel: return guild.system_channel
    else:
        general = nextcord.utils.find(lambda x: x.name == 'general',  guild.text_channels)
        if await checkTextChannelPermissions(general, False):
            return general
        else: 
            welcome = nextcord.utils.find(lambda x: x.name == 'welcome',  guild.text_channels)
            if await checkTextChannelPermissions(welcome, False):
                return welcome
            else:
                greetings = nextcord.utils.find(lambda x: x.name == "greetings", guild.text_channels)
                if await checkTextChannelPermissions(greetings, False):
                    return greetings
                else: 
                    for channel in guild.text_channels:
                        if await checkTextChannelPermissions(channel, False):
                            return channel
                    await sendErrorMessageToOwner(guild, "Send Messages")
                    return None

guildsCheckingForRole = []
async def checkForRole(guild: nextcord.Guild):
    '''Check to see if InfiniBot Mod Role Exists. If not, create it.'''
    global guildsCheckingForRole
    
    roles = guild.roles
    for x in range(0, len(roles)): roles[x] = roles[x].name

    if not "Infinibot Mod" in roles:
        try:
            if not guild.id in guildsCheckingForRole:
                guildsCheckingForRole.append(guild.id)
                await guild.create_role(name = "Infinibot Mod")
                await asyncio.sleep(1)
                if guild.id in guildsCheckingForRole: guildsCheckingForRole.remove(guild.id)
            else: return
        except nextcord.errors.Forbidden:
            if guild.id in guildsCheckingForRole: guildsCheckingForRole.remove(guild.id)
            if guild.id == 33394969196219596: return #this is the top.gg guild id. I don't want them denying me because of dms
            await sendErrorMessageToOwner(guild, None, message = "InfiniBot is missing the **Manage Roles** permission which prevents it from creating the role *InfiniBot Mod*. Please give InfiniBot this permission.", administrator=False)

def getInfinibotModRoleId(guild: nextcord.Guild):
    roles = guild.roles

    for role in roles:
        if role.name == "Infinibot Mod":
            return role.id
    
    return None

def getInfinibotTopRoleId(guild: nextcord.Guild):
    return guild.me.top_role.id

def canAssignRole(role: nextcord.Role):
    if role.is_default(): return False
    if role.is_integration(): return False
    
    return role.is_assignable()   
    
async def hasRole(interaction: Interaction, message = True):
    if interaction.guild.owner == interaction.user: return True
    
    infinibotMod_role = nextcord.utils.get(interaction.guild.roles, name='Infinibot Mod')
    if infinibotMod_role in interaction.user.roles:
        return True

    if message: await interaction.response.send_message(embed = nextcord.Embed(title = "Missing Permissions", description = "You need to have the Infinibot Mod role to use this command.", color = nextcord.Color.red()), ephemeral = True)
    return False

async def checkIfTextChannel(interaction: Interaction):
    """Check to see if the channel that this slash command was used in was a text channel"""
    
    if type(interaction.channel) == nextcord.TextChannel:
        return True
    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = "You can't use that here!", description = "You can only use this command in text channels.", color = nextcord.Color.red()), ephemeral=True)
        return

def timedeltaToEnglish(td: datetime.timedelta):
    # Get the total number of seconds in the timedelta
    total_seconds = int(td.total_seconds())

    # Compute the number of hours, minutes, and seconds
    hours, seconds = divmod(total_seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    # Create a list of strings with the appropriate units
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    # Join the parts with commas and "and" as appropriate
    if len(parts) == 0:
        return "0 seconds"
    elif len(parts) == 1:
        return parts[0]
    else:
        return ", ".join(parts[:-1]) + f", and {parts[-1]}"

def lowerList(list: list[str]):
    newlist = []
    for x in list:
        newlist.append(x.lower())
    
    return newlist

async def checkTextChannelPermissions(channel: nextcord.TextChannel, autoWarn, customChannelName = None):
    if channel == None:
        return False
    
    if channel.guild == None:
        return False
    
    if channel.guild.me == None:
        return False
    
    channelName = (customChannelName if customChannelName else channel.name)
    
    if channel.permissions_for(channel.guild.me).view_channel:
        if channel.permissions_for(channel.guild.me).send_messages:
            if channel.permissions_for(channel.guild.me).embed_links:
                return True
            elif autoWarn:
                await sendErrorMessageToOwner(channel.guild, "Embed Links", channel = channelName, administrator = False)
        elif autoWarn:
            await sendErrorMessageToOwner(channel.guild, "Send Messages and/or Embed Links", channel = channelName, administrator = False)
    elif autoWarn:
        await sendErrorMessageToOwner(channel.guild, "View Channels", channel = channelName, administrator = False)

    return False



#Check Permissions
def neededPermissions(guild: nextcord.Guild):
    if guild.me.guild_permissions.administrator:
        return [], []
    
    guildPermissions = []
    
    if not guild.me.guild_permissions.view_channel:
        guildPermissions.append("View Channels")
    if not guild.me.guild_permissions.send_messages:
        guildPermissions.append("Send Messages")
    if not guild.me.guild_permissions.embed_links:
        guildPermissions.append("Embed Links")
    if not guild.me.guild_permissions.manage_roles:
        guildPermissions.append("Manage Roles")
    if not guild.me.guild_permissions.manage_channels:
        guildPermissions.append("Manage Channels")
    if not guild.me.guild_permissions.manage_messages:
        guildPermissions.append("Manage Messages")
    if not guild.me.guild_permissions.manage_nicknames:
        guildPermissions.append("Manage Nicknames")
    if not guild.me.guild_permissions.view_audit_log:
        guildPermissions.append("View Audit Log")
    if not guild.me.guild_permissions.attach_files:
        guildPermissions.append("Attach Files")
    if not guild.me.guild_permissions.add_reactions:
        guildPermissions.append("Add Reactions")
    if not guild.me.guild_permissions.moderate_members:
        guildPermissions.append("Timeout Members")
    if not guild.me.guild_permissions.ban_members:
        guildPermissions.append("Ban Members")
    if not guild.me.guild_permissions.read_message_history:
        guildPermissions.append("Read Message History")
    if not guild.me.guild_permissions.connect:
        guildPermissions.append("Connect (Voice)")
    if not guild.me.guild_permissions.move_members:
        guildPermissions.append("Move Members")
    
    channelPermissions = []
    for channel in guild.channels:
        _channelPermissions = []
        
        if type(channel) == nextcord.CategoryChannel: continue
        
        if not channel.permissions_for(guild.me).view_channel and ("View Channels" not in guildPermissions):
            _channelPermissions.append("View Channels")
        if not channel.permissions_for(guild.me).send_messages and ("Send Messages" not in guildPermissions):
            _channelPermissions.append("Send Messages")
        if not channel.permissions_for(guild.me).embed_links and ("Embed Links" not in guildPermissions):
            _channelPermissions.append("Embed Links")
        if not channel.permissions_for(guild.me).manage_channels and ("Manage Channels" not in guildPermissions):
            _channelPermissions.append("Manage Channels")
        if not channel.permissions_for(guild.me).manage_messages and ("Manage Messages" not in guildPermissions):
            _channelPermissions.append("Manage Messages")
        if not channel.permissions_for(guild.me).attach_files and ("Attach Files" not in guildPermissions):
            _channelPermissions.append("Attach Files")
        if not channel.permissions_for(guild.me).add_reactions and ("Add Reactions" not in guildPermissions):
            _channelPermissions.append("Add Reactions")
        if not channel.permissions_for(guild.me).read_message_history and ("Read Message History" not in guildPermissions):
            _channelPermissions.append("Read Message History")
        if type(channel) == nextcord.VoiceChannel:
            if not channel.permissions_for(guild.me).connect and ("Connect (Voice)" not in guildPermissions):
                _channelPermissions.append("Connect (Voice)")
            if not channel.permissions_for(guild.me).move_members and ("Move Members" not in guildPermissions):
                _channelPermissions.append("Move Members")
            
        if len(_channelPermissions) > 0:
            channelPermissions.append([channel, _channelPermissions])
        
    return guildPermissions, channelPermissions

@bot.slash_command(name = "check_infinibot_permissions", description = "Check InfiniBot's permissions to help diagnose issues.", dm_permission=False)
async def check_infinibot_permissions(interaction: Interaction):
    _guildPermissions, _channelPermissions = neededPermissions(interaction.guild)
    
    # Return if everything is good
    if len(_guildPermissions) == 0 and len(_channelPermissions) == 0:
        embed = nextcord.Embed(title = "InfiniBot Permission Report", description = f"InfiniBot has every permission it needs! Nice work!", color = nextcord.Color.blue())
        await interaction.response.send_message(embed = embed, ephemeral=True, view = SupportandPermissionsCheckView())
        return

    # Guild Permissions
    if len(_guildPermissions) > 0:
        guildPermissions = ""
        for permission in _guildPermissions:
            guildPermissions += f"\n• {permission}"
        guildPermissionsSection = f"\n\n**Server Permissions** (Give the InfiniBot role these permissions):\n{guildPermissions}"
    else: guildPermissionsSection = ""
        
    # Channel Permissions
    if len(_channelPermissions) > 0:
        channelPermissions = ""
        for channel in _channelPermissions:
            channelPermissions += f"\n**{channel[0]}** ({channel[0].mention})"
            for permission in channel[1]:
                channelPermissions += f"\n• {permission}"
            channelPermissions += "\n"
        channelPermissionsSection = f"\n\n**Channel Permissions** (Give the InfiniBot role these permissions in each channel):\n\nNote: These permissions are in order of importance. Grant the first one, and the others may be granted automatically.\n{channelPermissions}"
    else: channelPermissionsSection = ""
        
    # Advice  
    advice = ""
    if len(_guildPermissions) + len(_channelPermissions) > 5:
        advice = "```Alternatively to the options below, you could give InfiniBot Administrator```\n\n"
    
    # Sending The Embed
    embed = nextcord.Embed(title = "InfiniBot Permission Report", description = f"{advice}InfiniBot is missing the following permissions:{guildPermissionsSection}{channelPermissionsSection}", color = nextcord.Color.blue())
    await interaction.response.send_message(embed = embed, ephemeral=True, view = SupportandPermissionsCheckView())

@bot.event
async def on_guild_role_update(before: nextcord.Role, after: nextcord.Role):
    await asyncio.sleep(3) #wait 3 seconds to let stuff sink in
    
    guild = after.guild
    #it *could* have been us... Let's just double check some things now...
    await checkForRole(guild)






# Dashboard and Profile
@bot.slash_command(name = "dashboard", description = "Configure InfiniBot (Requires Infinibot Mod)", dm_permission=False)
async def dashboard(interaction: Interaction):
    if await hasRole(interaction):
        view = Dashboard(interaction)
        await view.setup(interaction)
    
@bot.slash_command(name = "profile", description = "Configure Your Profile In InfiniBot")
async def profile(interaction: Interaction):
    view = Profile()
    await view.setup(interaction)







#Moderation Bot Functionality --------------------------------------------------------------------------------------------------------------
async def timeout(member: nextcord.Member, time: str, reason = None):
    try:
        time = humanfriendly.parse_timespan(time)
        await member.edit(timeout=nextcord.utils.utcnow()+datetime.timedelta(seconds=time), reason = reason)
        return True
    except Exception as error:
        return error

async def giveStrike(guild_id, userID, channel: nextcord.TextChannel, factor: int):
    server = Server(guild_id)

    userStrike = server.getStrike(userID)
    
    if factor == 1: #handle adding a strike
        if userStrike == None: #they are at strike 0
            server.addStrike(userID, 1)
            server.saveStrikes()
            return 1
        
        elif userStrike.strike < int(server.maxStrikes):
            userStrike.strike = userStrike.strike + 1
            userStrike.lastStrike = datetime.date.today()
            server.saveStrikes()
            return userStrike.strike
        
        else:
            #user needs to be timed out...          
            if not channel.permissions_for(channel.guild.me).moderate_members:
                await sendErrorMessageToOwner(channel.guild, "Timeout Members", guildPermission = True)
                return
            
            response = await timeout(userStrike.member, server.profanityTimeoutTime, reason = f"Profanity Moderation: User exceeded strike limit of {server.maxStrikes}.")
                
            if response == True: 
                if channel != None: 
                    await channel.send(embed = nextcord.Embed(title = "Timeout Given", description = f"{userStrike.member} is now timed out for {server.profanityTimeoutTime}", color = nextcord.Color.dark_red()))
                    server.deleteStrike(userStrike.memberID)
                    server.saveStrikes()
                    return 0
                else:
                    return userStrike.strike

            else: 
                if isinstance(response, nextcord.errors.Forbidden):
                    await channel.send(embed = nextcord.Embed(title = "Timeout Error", description = f"Failed to timeout {userStrike.member} for {server.profanityTimeoutTime}. \n\nError: Member is of a higher rank than InfiniBot", color = nextcord.Color.red()))
                else:
                    await channel.send(embed = nextcord.Embed(title = "Timeout Error", description = f"Failed to timeout {userStrike.member} for {server.profanityTimeoutTime}. \n\nError: {response}", color = nextcord.Color.red()))
                return userStrike.strike
        
    else:
        if userStrike != None:
            if userStrike.strike == 1:
                server.deleteStrike(userID)
                server.saveStrikes()
                return 0
            else:
                userStrike.strike -= 1
                userStrike.lastStrike = datetime.date.today()
                server.saveStrikes()
                return userStrike.strike
                
        else:
            return 0

async def checkForExpiration(server: Server):
    '''Check All Strikes in the Server for Expiration'''
    if server.strikeExpireTime == None or server.strikeExpireTime == 0: return
    
    for strike in server.strikes:
        try:
            referenceDate = datetime.datetime.strptime(strike.lastStrike, f"%Y-%m-%d")
            currentDate = datetime.datetime.today()
            
            dayDelta = (currentDate - referenceDate).days

            if int(dayDelta) >= int(server.strikeExpireTime):
                compensate = int(math.floor(int(dayDelta) / int(server.strikeExpireTime)))

                for x in range(0, compensate):
                    await giveStrike(server.guild_id, strike.memberID, None, -1) #remove a strike
        except Exception as err:
            print("Error when checking for expiration: " + str(err))

def checkProfanity(messageSplit, database):
    messageSplit = lowerList(messageSplit)
    database = lowerList(database)

    for word in messageSplit:
        if word == "he'll": continue
        word = ''.join(filter(str.isalnum, word))
        for dbWord in database:
            if word == dbWord: return word
            if word == dbWord + "s": return word
            if word == dbWord + "er": return word
            if word == dbWord + "ers": return word
            if word == dbWord + "ing": return word
            if word == dbWord + "ed": return word
            if word == dbWord + "y": return word
            if word == dbWord + "or": return word
            if word == dbWord + "ness": return word
            if word == dbWord + "tion": return word
            if word == dbWord + "sion": return word
            if word == dbWord + "ship": return word
            if word == dbWord + "ment": return word
            if word == "mother" + dbWord: return word
            if word == "mother" + dbWord + "er": return word
            if word == "mother" + dbWord + "ers": return word
            if word == dbWord: return word
            
    return None

def removeSymbols(string):
    return re.sub(r'\W+', '', string)

def checkRepeatedWordsPercentage(text, threshold=0.7):
    words = re.findall(r'\w+', text.lower())  # Convert text to lowercase and extract words
    counts = defaultdict(lambda: 0)  # Dictionary to store word counts
    
    # Remove symbols from the words
    words = [removeSymbols(word) for word in words]

    # Iterate over the words and count their occurrences
    lastWords = []
    for word in words:
        if word not in lastWords:
            counts[word] += 0.5
        else:
            counts[word] += 1
        lastWords.insert(0, word)
        if len(lastWords) >= 5:
            lastWords.pop(3)
        
    # Calculate the total number of words and the number of repeated words
    totalWords = len(words)
    if totalWords == 0: return False
    repeatedWords = sum(count for count in counts.values() if count > 0.5)

    # Calculate the percentage of repeated words
    repeatedPercentage = repeatedWords / totalWords

    # Check if the percentage exceeds the threshold
    return repeatedPercentage >= threshold

def compareAttachments(attachments1: List[nextcord.Attachment], attachments2: List[nextcord.Attachment]):
        # quick optimizations
        if not attachments1 or not attachments2:
            return False
        if attachments1 == attachments2:
            return True

        for attachment1 in attachments1:
            for attachment2 in attachments2:
                if (
                    attachment1.url == attachment2.url
                    or (
                        attachment1.filename == attachment2.filename
                        and attachment1.width == attachment2.width
                        and attachment1.height == attachment2.height
                        and attachment1.size == attachment2.size
                    )
                ):
                    return True
        return False

async def checkNickname(guild: nextcord.Guild, update: nextcord.Member):
    """Check to ensure that the edited nickname is in compliance with moderation"""
    
    member = guild.get_member(update.id)
    nickname = update.nick
    
    server = Server(guild.id)

    nicknameSplit = nickname.split(" ")
    result = checkProfanity(nicknameSplit, server.ProfaneWords)
    if result != None:
        channel = await getChannel(guild)
        if channel == None: return
        strikes = await giveStrike(guild.id, member.id, channel, 1)
        await channel.send(embed = nextcord.Embed(title = "Profanity Detected", description = f"{member} was flagged thier nickname of \"{nickname}\"\n\n{member} is now at {strikes} strike(s)", color = nextcord.Color.dark_red()))

        if server.adminChannel == None:
            return
        else:
            view = IncorrectButton()
            embed =  nextcord.Embed(title = "Profanity Detected", description = f"{member} was flagged thier nickname of \"{nickname}\"\n\n{member} is now at {strikes} strike(s)", color = nextcord.Color.dark_red())
            embed.set_footer(text = f"Member ID: {str(member.id)}")
            await server.adminChannel.send(view = view, embed = embed)

            await view.wait()

            await giveStrike(guild.id, member.id, None, -1)
            
async def canModerate(interaction: Interaction, server: Server):
    """Runs a check whether moderation is active. NOT SILENT!"""
    if server.profanityBool:
        return True
    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Moderation Tools Disabled", description = "Moderation has been turned off. type \"/enable moderation\" to turn it back on.", color = nextcord.Color.red()), ephemeral = True)
        return False

async def punnishProfanity(server: Server, message: nextcord.Message):
    global autoDeletedMessageTime
    
    if not server.profanityBool: return
    if message.channel.is_nsfw(): return
    if message.author == message.guild.owner: return
    
    msg = message.content.lower()
    messageSplit = msg.split(" ")

    if len(msg) == 0 or msg[0] == "/":
        await bot.process_commands(message)
        return
    
    result = checkProfanity(messageSplit, server.ProfaneWords)
    if result != None:
        #if they are in violation and need to be punnished...
        strikes = await giveStrike(message.guild.id, message.author.id, message.channel, 1)
        
        #dm them (if they want)
        memberSettings = Member(message.author.id)
        if memberSettings.dmsEnabledBool:
            try:
                dm = await message.author.create_dm()
                if strikes == 0:
                    embed = nextcord.Embed(title = "Profanity Log", description = f"You were flagged for saying \"{result}\" in \"{message.content}\" in \"{message.guild.name}\". You are now timed out for {server.profanityTimeoutTime}.\n\nTo opt out of dm notifications, use {opt_out_of_dms.get_mention()}", color = nextcord.Color.red(), timestamp = datetime.datetime.now())
                    await dm.send(embed = embed)
                else:
                    embed = nextcord.Embed(title = "Profanity Log", description = f"You were flagged for saying \"{result}\" in \"{message.content}\" in \"{message.guild.name}\". You are now at strike {strikes}.\n\nTo opt out of dm notifications, use {opt_out_of_dms.get_mention()}", color = nextcord.Color.red(), timestamp = datetime.datetime.now())
                    await dm.send(embed = embed)
            except:
                pass #the user has dms turned off. It's not a big deal, they just don't get notified.
        
        #Send message in channel where bad word was sent.
        if await checkTextChannelPermissions(message.channel, True):
            embed = nextcord.Embed(title = "Profanity Detected", description = f"{message.author.mention} was flagged for saying a Profane word. The message was automatically deleted.\n\n{message.author.mention} is now at {strikes} strike(s)\n\nContact a server admin for more info.", color = nextcord.Color.dark_red(), timestamp = datetime.datetime.now())
            await message.channel.send(embed = embed, view = InviteView())
        
        #Send message to admin channel (if enabled)
        if server.adminChannel != None:
            if server.adminChannel and await checkTextChannelPermissions(server.adminChannel, True, customChannelName = f"Admin Channel (#{server.adminChannel.name})"):
                view = IncorrectButton()

                embed = nextcord.Embed(title = "Profanity Detected", description = f"{message.author} was flagged for saying \"{result}\" in \"{message.content}\".\n\nThis message was automatically deleted.\n\n{message.author} is now at {strikes} strike(s)", color = nextcord.Color.dark_red(), timestamp = datetime.datetime.now())
                embed.set_footer(text = f"Member ID: {str(message.author.id)}")
                
                await server.adminChannel.send(view = view, embed = embed)

            
        #delete the message
        autoDeletedMessageTime = datetime.datetime.utcnow()
        
        try:
            await message.delete()
        except nextcord.errors.Forbidden:
            await sendErrorMessageToOwner(message.guild, "Manage Messages")

async def checkSpam(message: nextcord.Message, server: Server):
    MAX_MESSAGES_TO_CHECK = 11    # The MAXIMUM messages InfiniBot will try to check for spam
    MESSAGE_CHARS_TO_CHECK_REPETITION = 140    # A message requires these many characters before it is checked for repetition

    # If Spam is Enabled
    if not server.spamBool: return
    
    # Check if we can view the audit log
    if not message.guild.me.guild_permissions.view_audit_log:
        await sendErrorMessageToOwner(message.guild, "View Audit Log", channel=message.channel.name)
        return

    # Configure limit (the most messages that we're willing to check)
    if server.messagesThreshold < MAX_MESSAGES_TO_CHECK:
        limit = server.messagesThreshold + 1 # Add one because of the existing message
    else:
        limit = MAX_MESSAGES_TO_CHECK
        
    

    # Get previous messages
    previousMessages = await message.channel.history(limit=limit).flatten()
    
    # Loop through each previous message and test it
    duplicateMessages = []
    for _message in previousMessages:
        # Check word count percentage
        if _message.content and len(_message.content) >= MESSAGE_CHARS_TO_CHECK_REPETITION and checkRepeatedWordsPercentage(_message.content):
            duplicateMessages.append(_message)
            break
        
        # Check message content and attachments
        if _message.content == message.content or compareAttachments(_message.attachments, message.attachments):
            timeNow = datetime.datetime.utcnow() - datetime.timedelta(seconds = 2 * server.messagesThreshold) # ======= Time Threshold =========
            timeNow = timeNow.replace(tzinfo=datetime.timezone.utc)  # Make timeNow offset-aware
            
            # If the message is within the time threshold window, add that message.
            if _message.created_at >= timeNow:
                duplicateMessages.append(_message)
            else:
                # If this message was outside of the time window, previous messages will also be, so this loop can stop
                break


    # Punnish the member (if needed)
    if len(duplicateMessages) >= server.messagesThreshold:
        try:
            # Time them out
            await timeout(message.author, server.spamTimeoutTime, reason=f"Spam Moderation: User exceeded spam message limit of {server.messagesThreshold}.")
            
            # Send them a message (if they want it)
            if Member(message.author.id).dmsEnabledBool:
                dm = await message.author.create_dm()
                await dm.send(
                    embed=nextcord.Embed(
                        title="Spam Timeout",
                        description=f"You were flagged for spamming in \"{message.guild.name}\". You have been timed out for {server.spamTimeoutTime}.\n\nPlease contact the admins if you think this is a mistake.",
                        color=nextcord.Color.red(),
                    )
                )
        except nextcord.errors.Forbidden:
            await sendErrorMessageToOwner(message.guild, "Timeout Members", guildPermission=True)

# At refatoring time, remove these and integrate with dashboard
def addWord(word: str, guild_id):
    server = Server(guild_id)
    
    if word.lower() in lowerList(server.ProfaneWords):
        return nextcord.Embed(title = "Word Already Exists", description = f"The word \"{word}\" already exists in the database.", color = nextcord.Color.red())

    if "———" in word:
        return nextcord.Embed(title = "Word Cannot Contain Unique Case", description = f"Your word cannot contain \"———\" as it is reserved for other uses", color = nextcord.Color.red())

    #add word
    server.ProfaneWords.append(word.lower())

    server.saveProfaneWords()

    return True
def deleteWord(word: str, guild_id):
    server = Server(guild_id) 
    server.ProfaneWords.pop(server.ProfaneWords.index(word))
    server.saveProfaneWords()

@set.subcommand(name = "strikes", description = "Set any user's strikes (requires Infinibot Mod)")
async def setstrikescommand(interaction: Interaction, member: nextcord.Member, strike: str = SlashOption(description = "\"+1\" adds a strike, \"-1\" subtracts a strike. Or, input a number to overide strike count.")):
    if await hasRole(interaction):
        try:
            int(strike)
        except TypeError:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "Strikes must be a number", color = nextcord.Color.red()), ephemeral = True)
            return

        if strike == "-1":
            for x in range(0, int(strike[1:])):
                await giveStrike(interaction.guild_id, member.id, None, -1)
                await interaction.response.send_message(embed = nextcord.Embed(title = "Strikes Modified", description = f"{interaction.user} decreased {member}'s strikes by {strike}.", color = nextcord.Color.green()))
                return

        if strike == "+1":
            for x in range(0, int(strike[1:])):
                await giveStrike(interaction.guild_id, member.id, None, 1)
                await interaction.response.send_message(embed = nextcord.Embed(title = "Strikes Modified", description = f"{interaction.user} increased {member}'s strikes by {strike}.", color = nextcord.Color.green()))
                return
            
            
        server = Server(interaction.guild.id)
        if not await canModerate(interaction, server): return
        
        thierStrike = server.getStrike(member.id)
        
        if thierStrike != None:
            if int(strike) != 0: server.getStrike(member.id).strike = int(strike)
            else: server.deleteStrike(member.id)
        else:
            server.addStrike(member.id, strike)
        
        server.saveStrikes()

        await interaction.response.send_message(embed = nextcord.Embed(title = "Strikes Modified", description = f"{interaction.user} changed {member}'s strikes to {strike}.", color = nextcord.Color.green()))

@bot.slash_command(name = "my_strikes", description = "Get your strikes", dm_permission=False)
async def mystrikes(interaction: Interaction):
    server = Server(interaction.guild.id)
    if not await canModerate(interaction, server): return

    thierStrike = server.getStrike(interaction.user.id)
    if thierStrike != None:
        await interaction.response.send_message(embed = nextcord.Embed(title = f"Strikes - {interaction.user}", description = f"You are at {str(thierStrike.strike)} strike(s)", color =  nextcord.Color.blue()))
    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = f"Strikes - {interaction.user}", description = f"You are at 0 strike(s)", color =  nextcord.Color.blue()))

@bot.slash_command(name = "view_strikes", description = "View another member's strikes", dm_permission=False)
async def viewstrikes(interaction: Interaction, member: nextcord.Member):
    server = Server(interaction.guild.id)
    if not await canModerate(interaction, server): return

    thierStrike = server.getStrike(member.id)
    if thierStrike != None:
        await interaction.response.send_message(embed = nextcord.Embed(title = f"Strikes - {member}", description = f"{member} is at {str(thierStrike.strike)} strike(s).\n\nAction done by {interaction.user}", color =  nextcord.Color.blue()))
    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = f"Strikes - {member}", description = f"{member} is at 0 strikes.\n\nAction done by {interaction.user}", color =  nextcord.Color.blue()))

@set.subcommand(name = "admin_channel", description = "Use this channel to log strikes. Channel should only be viewable by admins. (requires Infinibot Mod)")
async def setAdminChannel(interaction: Interaction):
   if await hasRole(interaction) and await checkIfTextChannel(interaction):
        server = Server(interaction.guild.id)

        server.adminChannel = interaction.channel
        server.saveData()


        await interaction.response.send_message(embed = nextcord.Embed(title = "Admin Channel Set", description = f"Strikes will now be logged in this channel.\n**IMPORTANT: MAKE SURE THAT THIS CHANNEL IS ONLY ACCESSABLE BY ADMINS!**\nThis channel will allow members to mark strikes as incorrect. Thus, you only want admins to see it.\n\nAction done by {interaction.user}", color =  nextcord.Color.green()), view = SupportAndInviteView())
#END OF MODERATION BOT FUNCTIONALITY -----------------------------------------------------------------------------------------------------------------------------------------------------






#Music Bot Functionality ----------------------------------------------------------------------------------------------------------------------
class Music:
    def __init__(self, audioURL: str , title: str, videoURL:str , vc):
        self.audioURL = audioURL
        self.title = title
        self.videoURL = videoURL
        self.vc = vc


class Queue:
    def __init__(self, serverID: int, playing: bool, paused: bool, vc: nextcord.voice_client, volume: int):
        self.serverID = serverID
        self.playing = playing
        self.paused = paused
        self.vc = vc
        self.volume = volume
        self.loop = False
        self.queue: list[Music] = []
    
    def addSong(self, audioURL:str , title: str, videoURL:str , vc):
        self.queue.append(Music(audioURL, title, videoURL, vc))

    def deleteSong(self, index: int):
        self.queue.pop(index)


class MusicQueue:
    def __init__(self):
        self.queue: list[Queue] = []

    def addServer(self, serverID: int):
        self.queue.append(Queue(serverID, False, False, None, 100))
        return self.getData(serverID)

    def deleteServer(self, serverID: int):
        index = None
        for x in range(0, len(self.queue)):
            if self.queue[x].serverID == serverID:
                index = x
                break

        if not index == None:
            self.queue.pop(index)
            return True
        return False

    def getData(self, serverID: int):
        index = None
        for x in range(0, len(self.queue)):
            if self.queue[x].serverID == serverID:
                index = x
                break

        if index == None:
            return musicQueue.addServer(serverID)

        return self.queue[x]
        

musicQueue = MusicQueue()

#add Server: musicQueue.addServer(serverID: int) returns the server's data
#delete Server: musicQueue.deleteServer(serverID: int) #returns True if it was deleted, returns false if it didn't exist in the first place
#get Server's data: musicQueue.getData(serverID: int)
#add Song: musicQueue.getData(serverID: int).addSong(audioURL: str, title: str, videoURL: str, vc)
#delete Song: musicQueue.getData(serverID: int).deleteSong(index: int)

#get playing?: musicQueue.playing returns True or False
#get paused?: musicQueue.paused returns True or False
#get voice client: musicQueue.vc returns nextcord.voice_client/play 
#get volume: musicQueue.volume returns int
#get a song's audio URL: musicQueue.getData(serverID: int).queue[slot: int].audioURL returns str
#get a song's title: musicQueue.getData(serverID: int).queue[slot: int].titleURL returns str
#get a song's video URL: musicQueue.getData(serverID: int).queue[slot: int].videoURL returns str
#get a song's vc: musicQueue.getData(serverID: int).queue[slot: int].vc returns vc (of any type)

YDLP_OPTIONS = {'format':'bestaudio/best', 'noplaylist':'True', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}



async def canPlayMusic(interaction: Interaction, server: Server):
    if server.musicBool:
        return True
    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Music Tools Disabled", description = "Music has been turned off. type \"/enable music\" to turn it back on.", color = nextcord.Color.red()), ephemeral = True)
        return False


def search_yt(item):
    global YDLP_OPTIONS

    with YoutubeDL(YDLP_OPTIONS) as ydlp:
        try:
            info = ydlp.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
        except Exception as exc:
            print (exc)
            return False

    return {'source' : info['url'], 'title' : info['title'], 'video' : info['webpage_url']}

async def stopVC(serverData: Queue, vc: nextcord.VoiceClient):
    await vc.disconnect()
    musicQueue.deleteServer(serverData.serverID)

async def play_next(interaction: nextcord.Interaction):
    serverData = musicQueue.getData(interaction.guild_id)
    
    if not serverData.loop:
        serverData.deleteSong(0)
        
    if len(serverData.queue) > 0:
        vc = serverData.queue[0].vc
        if len(vc.members) == 1:
            if vc.members[0].id == bot.application_id:
                await stopVC(serverData, serverData.vc)
                return
        elif len(vc.members) == 0:
            await stopVC(serverData, serverData.vc)
            return
    else:
        await stopVC(serverData, serverData.vc)
        return

    await play_music(interaction)

async def play_music(interaction: nextcord.Interaction):
    serverData = musicQueue.getData(interaction.guild_id)
    vc = serverData.vc

    if len(serverData.queue) > 0: #if there is something in the queue
        if vc is None or not vc.is_connected(): #if we need to connect to a vc
            try:
                vc = await serverData.queue[0].vc.connect()
            except nextcord.errors.Forbidden:
                await sendErrorMessageToOwner(interaction.guild, "Voice Connect and/or Speak")
                return

            if vc is None:
                serverData.playing = False
                serverData.paused = False
                await vc.disconnect()
                return

            serverData.vc = vc

        else:
            try:
                await vc.move_to(serverData.queue[0].vc)
            except nextcord.errors.Forbidden:
                await sendErrorMessageToOwner(interaction.guild, "Voice Connect and/or Speak")
                return
            else:
                pass

        m_url = serverData.queue[0].audioURL

        serverData.playing = True
        serverData.paused = False
        vc.play(nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(m_url, **FFMPEG_OPTIONS, executable = "./ffmpeg.exe")), after = lambda e: play_next(interaction)) # executable="/home/tasty-pie/Desktop/Infinibot/ffmpeg.exe"
        vc.source.volume = serverData.volume

    else:
        serverData.playing = False
        serverData.paused = False
        try:
            await vc.disconnect()
        except:
            return

#@bot.slash_command(name = "play", description = "Play any song from YouTube", dm_permission=False)
async def play(interaction: Interaction, music: str = SlashOption(description = "Can be a url or a search query")):
    server = Server(interaction.guild.id)
    if not await canPlayMusic(interaction, server): return
    
    #check search query for prohibited key-words
    checkForNSFW = True
    if checkForNSFW:
        prohibitedWords = ["nude", "naked", "breast", "sex"]
        for word in prohibitedWords:
            if word in music:
                await interaction.response.send_message(embed = nextcord.Embed(title = "Prohibited Search Query", description = "InfiniBot will not play that search query due to NSFW possibility", color = nextcord.Color.red()), ephemeral = True)
                return
    
    serverData = musicQueue.getData(interaction.guild_id)

    await interaction.response.defer()

    if interaction.user.voice is None: #if the user is not in a voice channel
        await interaction.followup.send(embed = nextcord.Embed(title = "Can't connect to your voice channel", description = "This command requires the user to be connected to a voice channel", color = nextcord.Color.red()), ephemeral = True)
        return
    
    if not(interaction.user.voice.channel.permissions_for(interaction.guild.me).connect and interaction.user.voice.channel.permissions_for(interaction.guild.me).speak):
        await interaction.followup.send(embed = nextcord.Embed(title = "Missing Permissions", description = "This command requires InfiniBot to have both **Voice Connect** and **Voice Speak** permissions.", color = nextcord.Color.red()), ephemeral = True)
        await sendErrorMessageToOwner(interaction.guild, "Voice Connect and/or Speak", channel = f"#{interaction.user.voice.channel.name}")
        return

    if serverData.paused:
        serverData.playing = True
        serverData.paused = False
        serverData.queue[0].vc.resume()

    
    music = search_yt(music)
    if music == False:
        embed = nextcord.Embed(title = "Could not Download Song", description = "Incorrect Format / Keyword", color = nextcord.Color.red())
        embed.add_field(name = "Possible Reasons", value = "1. The keywords you used failed to yield a search result. Try a different keyword.\n2. The search result yielded a live stream result. You cannot play a live stream.\n3. The video is age-restricted.")
        await interaction.followup.send(embed = embed, ephemeral = True)
        return

    print(music)
    voice_channel = interaction.user.voice.channel

    serverData.addSong(music['source'], music['title'], music['video'], voice_channel)
    if serverData.playing:
        embed = nextcord.Embed(title = "Music Added to Queue", description = f"Action done by {interaction.user}", color = nextcord.Color.green())
        embed.add_field(name = music['title'], value = music['video'])
        await interaction.followup.send(embed = embed, view = InviteView())

    else:
        embed = nextcord.Embed(title = "Playing Music", description = f"Action done by {interaction.user}", color = nextcord.Color.green())
        embed.add_field(name = music['title'], value = music['video'])
        await interaction.followup.send(embed = embed, view = InviteView())
        

        await play_music(interaction)

#@bot.slash_command(name = "skip", description="Skip the current song", dm_permission=False)
async def skip(interaction: Interaction):
    server = Server(interaction.guild.id)
    if not await canPlayMusic(interaction, server): return
    
    serverData = musicQueue.getData(interaction.guild_id)
    vc = serverData.vc

    if vc != None and vc:
        vc.stop()
        serverData.playing = True
        serverData.paused = False
        serverData.loop = False
        if len(serverData.queue) > 1:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Song Skipped", description = f"Action done by {interaction.user}", color = nextcord.Color.yellow()))
        else:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Song Skipped. No Music Left in Queue.", description = f"Action done by {interaction.user}", color = nextcord.Color.yellow()))
            await stopVC(serverData, serverData.vc)

    else:
        serverData.playing = False
        serverData.paused = False
        await interaction.response.send_message(embed = nextcord.Embed(title = "No Music Playing", description = "Cannot skip when no music is playing", color = nextcord.Color.red()), ephemeral = True)

#@bot.slash_command(name = "leave", description = "Leave the current voice channel and clear queue", dm_permission=False)
async def leave(interaction: Interaction):
    server = Server(interaction.guild.id)
    if not await canPlayMusic(interaction, server): return
    
    serverData = musicQueue.getData(interaction.guild_id)

    if serverData.vc == None:
        await interaction.response.send_message(embed = nextcord.Embed(title = "No Music in Queue", description = "Type /play [music] to play something", color = nextcord.Color.red()), ephemeral = True)
        return

    await stopVC(serverData, serverData.vc)
    await interaction.response.send_message(embed = nextcord.Embed(title = "Left voice channel", description = f"Action done by {interaction.user}", color = nextcord.Color.orange()))

#@bot.slash_command(name = "stop", description = "Leave the current voice channel and clear queue", dm_permission=False)
async def stop(interaction: Interaction):
    await leave(interaction)

#@bot.slash_command(name = "clear", description = "Clears all music in queue except for the current song", dm_permission=False)
async def clear(interaction: Interaction):
    server = Server(interaction.guild.id)
    if not await canPlayMusic(interaction, server): return
    
    serverData = musicQueue.getData(interaction.guild_id)

    if serverData.vc == None:
        await interaction.response.send_message(embed = nextcord.Embed(title = "No Music in Queue", description = "Type /play [music] to play something", color = nextcord.Color.red()), ephemeral = True)
        return
    
    for x in range(1, len(serverData.queue)):
        serverData.deleteSong(1) #index is one because after we delete a song, the next songs shift up, so by always deleting one, we delete all the songs exept for song [0]

    await interaction.response.send_message(embed = nextcord.Embed(title = "Queue Cleared", description = f"Action done by {interaction.user}", color = nextcord.Color.orange()))

#@bot.slash_command(name = "queue", description = "Display the current queue", dm_permission=False)
async def queue(interaction: Interaction):
    server = Server(interaction.guild.id)
    if not await canPlayMusic(interaction, server): return
    
    serverData = musicQueue.getData(interaction.guild_id)

    queueString = ""

    for i in range(0, len(serverData.queue)):
        if i > 9:
            queueString += f"+{len(serverData.queue) - 10} more"
            break
        
        if i == 0 and serverData.loop: queueString += f"1. {serverData.queue[i].title} (Looped)\n"
        else: queueString += f"{str(i + 1)}. {serverData.queue[i].title}\n"

    if queueString == "":
        await interaction.response.send_message(embed = nextcord.Embed(title = "No Music in Queue", description = "Type /play [music] to play something", color = nextcord.Color.red()), ephemeral = True)
        return
        
    await interaction.response.send_message(embed = nextcord.Embed(title = "Music Queue", description = queueString, color = nextcord.Color.blue()))

#@bot.slash_command(name = "pause", description = "Pause the current song", dm_permission=False)
async def pause(interaction: Interaction):
    server = Server(interaction.guild.id)
    if not await canPlayMusic(interaction, server): return
    
    serverData = musicQueue.getData(interaction.guild_id)

    if serverData.paused == False and serverData.playing == True:
        serverData.playing = False
        serverData.paused = True
        serverData.vc.pause()
        await interaction.response.send_message(embed = nextcord.Embed(title = "Paused Current Song and Queue", description = f"Action done by {interaction.user}", color = nextcord.Color.green()))

    elif serverData.paused == True:
        serverData.playing = True
        serverData.paused = False
        serverData.vc.resume()
        await interaction.response.send_message(embed = nextcord.Embed(title = "Resumed Current Song and Queue", description = f"Action done by {interaction.user}", color = nextcord.Color.green()))

    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = "No music playing", description = "Type /play [music] to play something", color = nextcord.Color.red()), ephemeral = True)

#@bot.slash_command(name = "resume", description = "Resume the current song", dm_permission=False)
async def resume(interaction: Interaction):
    server = Server(interaction.guild.id)
    if not await canPlayMusic(interaction, server): return
    
    serverData = musicQueue.getData(interaction.guild_id)

    if serverData.paused == True:
        serverData.playing = True
        serverData.paused = False
        serverData.vc.resume()
        await interaction.response.send_message(embed = nextcord.Embed(title = "Resumed Current Song and Queue", description = f"Action done by {interaction.user}", color = nextcord.Color.green()))

    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = "No music playing", description = "Type /play [music] to play something", color = nextcord.Color.red()), ephemeral = True)

#@bot.slash_command(name = "volume", description = "Get the volume or set the volume to any number between 0 and 100", dm_permission=False)
async def volume(interaction: Interaction, volume: int = SlashOption(description = "Must be a number between 0 and 100", required = False)):
    server = Server(interaction.guild.id)
    if not await canPlayMusic(interaction, server): return
    
    if volume == None:
        serverData = musicQueue.getData(interaction.guild_id)

        if serverData.vc == None: 
            await interaction.response.send_message(embed = nextcord.Embed(title = "No music is playing", description = "Type /play [music] to play something", color = nextcord.Color.red()), ephemeral = True)
            return
        
        await interaction.response.send_message(embed = nextcord.Embed(title = f"Volume at {int(serverData.vc.source.volume * 100)}%", description = "To change, type /volume [0-100]", color = nextcord.Color.blue()))
        return
    else:
        serverData = musicQueue.getData(interaction.guild_id)

        if serverData.vc == None: 
            await interaction.response.send_message(embed = nextcord.Embed(title = "No music is playing", description = "Type /play [music] to play something", color = nextcord.Color.red()), ephemeral = True)
            return

        if int(volume) > 100 or int(volume) < 0:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Improper Format", description = "Volume must be between 0 and 100", color = nextcord.Color.red()), ephemeral = True)
            return
        
        formattedVolume = int(volume) / 100 

        if not (serverData.vc == None): 
            serverData.vc.source.volume = formattedVolume

        serverData.volume = formattedVolume

        await interaction.response.send_message(embed = nextcord.Embed(title = f"Volume Set to {volume}%", description = f"Action done by {interaction.user}", color = nextcord.Color.green()))

#@bot.slash_command(name = "loop", description = "Loop / un-loop the current song", dm_permission=False)
async def loop(interaction: Interaction):
    server = Server(interaction.guild.id)
    if not await canPlayMusic(interaction, server): return

    serverData = musicQueue.getData(interaction.guild_id)

    if serverData.loop == False:
        serverData.loop = True
        await interaction.response.send_message(embed = nextcord.Embed(title = "Looped Current Song", description = f"Action done by {interaction.user}", color = nextcord.Color.green()))

    else:
        serverData.loop = False
        await interaction.response.send_message(embed = nextcord.Embed(title = "Un-Looped Current Song", description = f"Action done by {interaction.user}", color = nextcord.Color.dark_green()))
#Music Bot Functionality END ---------------------------------------------------------------------------------------------------------------







#Start of Voting Bot Functionality: ------------------------------------------------------------------------------------------------------------------------------------------------------
VOTETYPES = ["Letters", "Numbers", "Custom"]
@create.subcommand(name = "vote", description = "Automatically create a vote.")
async def voteCommand(interaction: Interaction, type: str = SlashOption(choices = ["Letters", "Numbers"])):
    modal = VotingModal(interaction, type)
        
    await interaction.response.send_modal(modal)
       
@create.subcommand(name = "custom_vote", description = "Automatically create a vote that you can customize with emojis.")
async def customVoteCommand(interaction: Interaction, options: str = SlashOption(description = "Format: \"😄 = Yes, 😢 = No\"")):   
    optionsSplit = options.split(",")
    optionsSplit = [option.strip() for option in optionsSplit]
    
    if len(optionsSplit) > 10:
        await interaction.followup.send(embed = nextcord.Embed(title = "Too Many Arguments", description = "You can't have more than 10 voting options.", color = nextcord.Color.red()), ephemeral=True)
        return
    
    emojis = []
    for option in optionsSplit:
        try:
            if len(option.split("=")) < 2:
                await interaction.response.send_message(embed = nextcord.Embed(title = "You Formatted that Wrong", description = "\"Options\" needs to be formatted like this:\n\nEmoji = Option, Emoji = Option, Emoji = Option, Etc\n\n😄 = Yes, 😢 = No", color = nextcord.Color.red()), ephemeral=True)
                return
            emoji = option.split("=")[0].strip()
            if emoji in emojis:
                await interaction.response.send_message(embed = nextcord.Embed(title = "You can't use the same emoji twice", description = "Every emoji has to be unique.", color = nextcord.Color.red()), ephemeral=True)
                return
            
            emojis.append(option.split("=")[0].strip())
            
        except:
            await interaction.response.send_message(embed = nextcord.Embed(title = "You Formatted that Wrong", description = "\"Options\" needs to be formatted like this:\n\nEmoji = Option, Emoji = Option, Emoji = Option, Etc\n\n😄 = Yes, 😢 = No", color = nextcord.Color.red()), ephemeral=True)
            return
     
    modal = VotingModal(interaction, "Custom", options = options)
    await interaction.response.send_modal(modal)
          
async def createVote(interaction: Interaction, title: str, message: str, options: str, _type: str):   
    optionsSplit = options.split(",")
    optionsSplit = [option.strip() for option in optionsSplit]

    if len(optionsSplit) > 10:
        await interaction.followup.send(embed = nextcord.Embed(title = "Too Many Arguments", description = "You can't have more than 10 voting options.", color = nextcord.Color.red()), ephemeral=True)
        return

    reactionsFormatted = ""
    addedOptions_Emojis = []
    addedOptions_Asci = [] #expendable after the following loop

    counter = 1
    for option in optionsSplit:
        if _type == "Letters":
            if not option[0].lower() in addedOptions_Asci: #if we have not already used this reaction
                letter = option[0]
                reaction = asci_to_emoji(letter)
                reactionsFormatted += "\n" + reaction + " " + option
                addedOptions_Asci.append(letter.lower())
                addedOptions_Emojis.append(reaction)
                counter += 1
            else:
                letter = getNextOpenLetter(addedOptions_Asci)
                reaction = asci_to_emoji(letter)
                reactionsFormatted += "\n" + reaction + " " + option
                addedOptions_Asci.append(letter.lower())
                addedOptions_Emojis.append(reaction)
                counter += 1      
                
        elif _type == "Numbers":
            letter = option[0]
            reaction = asci_to_emoji(counter)
            reactionsFormatted += "\n" + reaction + " " + option
            addedOptions_Asci.append(letter.lower())
            addedOptions_Emojis.append(reaction)
            counter += 1
        
        else:
            stripped = option.split("=")
            emoji = stripped[0].strip()
            word = "=".join(stripped[1:]).strip()
            reactionsFormatted += "\n" + emoji + " " + word
            addedOptions_Emojis.append(emoji)  


    embed = nextcord.Embed(title = title, description = message, color =  nextcord.Color.magenta())
    embed.add_field(name = "Options", value = reactionsFormatted, inline = False)

    partialMessage = await interaction.followup.send(embed = embed, wait = True)
    

    
    voteMessage = partialMessage
    for reaction in addedOptions_Emojis:
        try:
            await voteMessage.add_reaction(emoji = reaction)
        except nextcord.errors.Forbidden:
            await interaction.followup.send(embed = nextcord.Embed(title = "Emoji Error", description = f"InfiniBot is unable to apply the emoji: {reaction}. If the emoji *is* valid, check that InfiniBot has the permission \"Add Reactions\".", color = nextcord.Color.red()))
            await sendErrorMessageToOwner(interaction.guild, "Add Reactions")
            break
        
    #finally, add the vote to our active messages for future editing
    server = Server(interaction.guild.id);
    server.messages.add("Vote", interaction.channel.id, partialMessage.id, interaction.user.id)
    server.messages.save()

def asci_to_emoji(letter):
    letter = str(letter)
    letter = letter.lower()

    if letter == "a": return "🇦"
    if letter == "b": return "🇧"
    if letter == "c": return "🇨"
    if letter == "d": return "🇩"
    if letter == "e": return "🇪"
    if letter == "f": return "🇫"
    if letter == "g": return "🇬"
    if letter == "h": return "🇭"
    if letter == "i": return "🇮"
    if letter == "j": return "🇯"
    if letter == "k": return "🇰"
    if letter == "l": return "🇱"
    if letter == "m": return "🇲"
    if letter == "n": return "🇳"
    if letter == "o": return "🇴"
    if letter == "p": return "🇵"
    if letter == "q": return "🇶"
    if letter == "r": return "🇷"
    if letter == "s": return "🇸"
    if letter == "t": return "🇹"
    if letter == "u": return "🇺"
    if letter == "v": return "🇻"
    if letter == "w": return "🇼"
    if letter == "x": return "🇽"
    if letter == "y": return "🇾"
    if letter == "z": return "🇿"
    if letter == "1": return "1️⃣"
    if letter == "2": return "2️⃣"
    if letter == "3": return "3️⃣"
    if letter == "4": return "4️⃣"
    if letter == "5": return "5️⃣"
    if letter == "6": return "6️⃣"
    if letter == "7": return "7️⃣"
    if letter == "8": return "8️⃣"
    if letter == "9": return "9️⃣"
    if letter == "0": return "0️⃣"

    return "🇿"

def getNextOpenLetter(list):
    if not ("a" in list): return "a"
    if not ("b" in list): return "b"
    if not ("c" in list): return "c"
    if not ("d" in list): return "d"
    if not ("e" in list): return "e"
    if not ("f" in list): return "f"
    if not ("g" in list): return "g"
    if not ("h" in list): return "h"
    if not ("i" in list): return "i"
    if not ("j" in list): return "j"
    if not ("k" in list): return "k"
    if not ("l" in list): return "l"
    if not ("m" in list): return "m"
    if not ("n" in list): return "n"
    if not ("o" in list): return "o"
    if not ("p" in list): return "p"
    if not ("q" in list): return "q"
    if not ("r" in list): return "r"
    if not ("s" in list): return "s"
    if not ("t" in list): return "t"
    if not ("u" in list): return "u"
    if not ("v" in list): return "v"
    if not ("w" in list): return "w"
    if not ("x" in list): return "x"
    if not ("y" in list): return "y"
    if not ("z" in list): return "z"
    if not ("1" in list): return "1"
    if not ("2" in list): return "2"
    if not ("3" in list): return "3"
    if not ("4" in list): return "4"
    if not ("5" in list): return "5"
    if not ("6" in list): return "6"
    if not ("7" in list): return "7"
    if not ("8" in list): return "8"
    if not ("9" in list): return "9"
    if not ("0" in list): return "0"
#END of Voting Bot Functionality: ------------------------------------------------------------------------------------------------------------------------------------------------------






#Start of reaction bot functionality: ----------------------------------------------------------------------------------------------------------------------------------------------------
REACTIONROLETYPES = ["Letters", "Numbers", "Custom"]
@create.subcommand(name = "reaction_role", description = "Create a message that will allow users to add/remove roles from themselves. (Requires Infinibot Mod)")
async def reactionRoleCommand(interaction: Interaction, type: str = SlashOption(choices = ["Letters", "Numbers"]), mentionRoles: bool = SlashOption(name = "mention_roles", description = "Mention the roles with @mention", required = False, default = True)):
    if await hasRole(interaction):
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(embed = nextcord.Embed(title = "InfiniBot Missing Permissions", description = "InfiniBot needs the \"Manage Roles\" permission in order to use this command. Grant InfiniBot this permission and try again.", color = nextcord.Color.red()), ephemeral = True)
            return
        
        #Send Modal
        modal = ReactionRoleModal()
            
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        #Proccess Modal
        title = modal.titleValue
        description = modal.descriptionValue
        
        #Prepare Selection
        rolesAllowed = []
        
        for role in interaction.guild.roles:
            if role.name == "@everyone": continue
            if canAssignRole(role): rolesAllowed.append(role)
            
        if len(rolesAllowed) == 0:
            await interaction.followup.send(embed = nextcord.Embed(title = "No Roles", description = "InfiniBot can't find any roles that it is able to assign. Make sure that your server has roles and that InfiniBot is the highest role on the server.", color = nextcord.Color.red()), ephemeral = True)
            return;
                    
        #Send Selection View
        view = ReactionRoleView(rolesAllowed)
        await interaction.followup.send(embed = nextcord.Embed(title = "Choose the roles you would like to include.", description = "**Don't see your role?**\nIf a role is equal to or higher than InfiniBot's highest role, InfiniBot cannot grant that role to anyone. Fix this by making InfiniBot the highest role on the server.", color = nextcord.Color.blurple()), view = view, ephemeral=True)

        await view.wait()
        
        #Finish Proccessing...
        await createReactionRole(interaction, title, description, view.selection, type, mentionRoles)
    
@create.subcommand(name = "custom_reaction_role", description = "Automatically create a vote that you can customize with emojis.")
async def customReactionRoleCommand(interaction: Interaction, options: str = SlashOption(description = "Format: \"👍 = @Member, 🥸 = @Gamer\""), mentionRoles: bool = SlashOption(name = "mention_roles", description = "Mention the roles with @mention", required = False, default = True)):   
    if await hasRole(interaction):
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(embed = nextcord.Embed(title = "InfiniBot Missing Permissions", description = "InfiniBot needs the \"Manage Roles\" permission in order to use this command. Grant InfiniBot this permission and try again.", color = nextcord.Color.red()), ephemeral = True)
            return
        
        optionsSplit = options.split(",")
        optionsSplit = [option.strip() for option in optionsSplit]
        
        if len(optionsSplit) > 10:
            await interaction.followup.send(embed = nextcord.Embed(title = "Too Many Arguments", description = "You can't have more than 10 voting options.", color = nextcord.Color.red()), ephemeral=True)
            return
        
        emojis = []
        rolesID = []
        for option in optionsSplit:
            try:
                if len(option.split("=")) < 2:
                    await interaction.response.send_message(embed = nextcord.Embed(title = "You Formatted that Wrong", description = "\"Options\" needs to be formatted like this:\n\nEmoji = @Role, Emoji = @Role, Emoji = @Role, Etc\n\n👍 = @Member, 🥸 = @Gamer", color = nextcord.Color.red()), ephemeral=True)
                    return
                
                emoji = option.split("=")[0].strip()
                if emoji in emojis:
                    await interaction.response.send_message(embed = nextcord.Embed(title = "You can't use the same emoji twice", description = "Every emoji has to be unique.", color = nextcord.Color.red()), ephemeral=True)
                    return
                
                roleID = int(option.split("=")[1][4:-1].strip())
                role = [role for role in interaction.guild.roles if role.id == roleID][0]
                if roleID in rolesID:
                    await interaction.response.send_message(embed = nextcord.Embed(title = "You can't use the same role twice", description = "Every role has to be unique.", color = nextcord.Color.red()), ephemeral=True)
                    return
                if not roleID in [role.id for role in interaction.guild.roles]:
                    await interaction.response.send_message(embed = nextcord.Embed(title = "Role Doesn't Exist", description = f"The role \"{role.name}\" doesn't exist.", color = nextcord.Color.red()), ephemeral=True)
                    return
                if not canAssignRole(role):
                    await interaction.response.send_message(embed = nextcord.Embed(title = "Error", description = f"Infinibot does not have a high enough role to assign/remove {role.name}. To fix this, promote the role \"Infinibot\" to the highest role on the server or give InfiniBot Administrator.", color = nextcord.Color.red()))
                
                emojis.append(emoji)
                rolesID.append(role.id)
                
            except Exception:
                await interaction.response.send_message(embed = nextcord.Embed(title = "You Formatted that Wrong", description = "\"Options\" needs to be formatted like this:\n\nEmoji = @Role, Emoji = @Role, Emoji = @Role, Etc\n\n👍 = @Member, 🥸 = @Gamer", color = nextcord.Color.red()), ephemeral=True)
                return
        
        modal = ReactionRoleModal()
        await interaction.response.send_modal(modal)
        
        await modal.wait()
        
        await createReactionRole(interaction, modal.titleValue, modal.descriptionValue, [option.strip() for option in options.split(",")], "Custom", mentionRoles)

def reactionRoleOptionsFormatter(_type: str, roles: list[nextcord.Role], emojis: list[str], mentionRoles: bool):
    reactionsFormatted = "" # Returned
    addedOptions_Emojis = [] # Returned
    addedOptions_Asci = []
    
    count = 1
    for role in roles:
        if _type == "Letters":
            if not role.name[0].lower() in addedOptions_Asci: #if we have not already used this reaction
                letter = role.name[0]
                reaction = asci_to_emoji(letter)
                reactionsFormatted += "\n" + reaction + " " + (role.mention if mentionRoles else role.name)
                addedOptions_Asci.append(letter.lower())
                addedOptions_Emojis.append(reaction)
            else:
                letter = getNextOpenLetter(addedOptions_Asci)
                reaction = asci_to_emoji(letter)
                reactionsFormatted += "\n" + reaction + " " + (role.mention if mentionRoles else role.name)
                addedOptions_Asci.append(letter.lower())
                addedOptions_Emojis.append(reaction)
        elif _type == "Numbers":
            letter = role.name[0]
            reaction = asci_to_emoji(count)
            reactionsFormatted += "\n" + reaction + " " + (role.mention if mentionRoles else role.name)
            addedOptions_Asci.append(letter.lower())
            addedOptions_Emojis.append(reaction)
            count += 1
        else:
            index = roles.index(role)
            emoji = emojis[index].strip()
            reactionsFormatted += "\n" + emoji + " " + (role.mention if mentionRoles else role.name)
            addedOptions_Emojis.append(emoji)
            
    return reactionsFormatted, addedOptions_Emojis

async def createReactionRole(interaction: Interaction, title: str, message: str, rolesStr: list[str], _type: str, mentionRoles: bool):  
    # Decode roles and emojis
    if _type != "Custom":
        roles: list[nextcord.Role] = [role for roleName in rolesStr for role in interaction.guild.roles if role.name == roleName]
        emojis = None
    else:
        newRolesStr = [int(role.split("=")[1][4:-1].strip()) for role in rolesStr]
        roles: list[nextcord.Role] = [role for roleID in newRolesStr for role in interaction.guild.roles if role.id == roleID]
        emojis: list[str] = [emoji.split("=")[0] for emoji in rolesStr]
    
    # Ensure that these roles are grantable
    for role in roles:
        if role.position >= interaction.guild.me.top_role.position:
            infinibotRole = interaction.guild.get_role(getInfinibotTopRoleId(interaction.guild))
            await interaction.followup.send(embed = nextcord.Embed(title = "Infinibot cannot grant a permission", description = f"{role.mention} is equal to or above the role {infinibotRole.mention}. Therefore, it cannot grant the role to any member.", color = nextcord.Color.red()), ephemeral=True)
            return
    
    # Ensure that this is idiot proof
    if len(roles) == 0:
        await interaction.followup.send(embed = nextcord.Embed(title = "No Roles", description = "You need to have at least one role.", color =  nextcord.Color.red()), ephemeral = True)
        return
    
    # Format the options
    optionsFormatted, addedReactions_Emojis = reactionRoleOptionsFormatter(_type, roles, emojis, mentionRoles)

    # Post message
    embed = nextcord.Embed(title = title, description = message, color =  nextcord.Color.teal())
    embed.add_field(name = "React for the following roles", value = optionsFormatted, inline = False)

    partialMessage = await interaction.followup.send(embed = embed, wait = True)

    # Add Reactions
    reactionRoleMessage = partialMessage
    for reaction in addedReactions_Emojis:
        try:
            await reactionRoleMessage.add_reaction(emoji = reaction)
        except nextcord.errors.Forbidden or nextcord.errors.HTTPException:
            try:
                await interaction.followup.send(embed = nextcord.Embed(title = "Emoji Error", description = f"InfiniBot is unable to apply the emoji: {reaction}. If the emoji *is* valid, check that InfiniBot has the permission \"Add Reactions\".", color = nextcord.Color.red()))
            except nextcord.errors.Forbidden:
                await sendErrorMessageToOwner(interaction.guild, "Add Reactions")
            break
    
    # Add the Reaction Role to Active Messages for Future Editing
    server = Server(interaction.guild.id);
    try: parameters = [REACTIONROLETYPES.index(_type), ("1" if mentionRoles else "0")]
    except ValueError: parameters = []
    server.messages.add("Reaction Role", interaction.channel.id, partialMessage.id, interaction.user.id, parameters = parameters)
    server.messages.save()
    
@bot.event
async def on_raw_reaction_add(payload: nextcord.RawReactionActionEvent):
    emoji = payload.emoji

    # Get the guild
    guild = None
    for Guild in bot.guilds:
        if Guild.id == payload.guild_id:
            guild = Guild
    if guild == None: return

    # Get the user
    user = guild.get_member(payload.user_id)
    if user == None: return

    # Get the message
    try:
        message = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
    except nextcord.errors.Forbidden:
        return
    except AttributeError:
        return
    
    # Declare some functions
    def getRole(string: str):
        pattern = r"^(<@&)(.*)>$"  # Regular expression pattern with a capturing group
        match = re.search(pattern, string)
        if match:
            id = int(match.group(2))
            role = nextcord.utils.get(guild.roles, id = id)
        else:
            role = nextcord.utils.get(guild.roles, name = string)
        return role
    
    async def sendNoRoleError():
        await message.channel.send(embed = nextcord.Embed(title = "Role Not Found", description = f"Infinibot cannot find one or more of those roles. Check to make sure all roles still exist.", color = nextcord.Color.red()), reference = message)
    
    async def sendNoPermissionsError(role: nextcord.Role, user: nextcord.Member):
        try:
            await message.channel.send(embed = nextcord.Embed(title = "Missing Permissions", description = f"Infinibot does not have a high enough role to assign/remove {role.mention} to/from {user.mention}. To fix this, promote the role \"Infinibot\" to the highest role on the server or give InfiniBot administrator privileges.", color = nextcord.Color.red()), reference = message)
        except nextcord.errors.Forbidden:
            await sendErrorMessageToOwner(guild, None, message = f"Infinibot does not have a high enough role to assign/remove {role.name} (id: {role.id}) to/from {user} (id: {user.id}). To fix this, promote the role \"Infinibot\" to the highest role on the server or give InfiniBot administrator privileges.")

    # If it was our message and it was not a bot reacting,
    if message.author.id == bot.application_id and not user.bot:
        if message.embeds:
            # Check to see if this is actually a reaction role
            server = Server(guild.id)
            messageInfo = server.messages.get(message.id)
            if messageInfo and messageInfo.type == "Reaction Role": # This message IS a reaction role
                del server, messageInfo # Don't need them
                
                # Can we manage roles? If not, there's not point to any of this
                if not message.channel.permissions_for(guild.me).manage_roles:
                    await sendErrorMessageToOwner(guild, "Manage Roles", guildPermission = True)
                    return
                
                # Get all options
                info = message.embeds[0].fields[0].value
                info = info.split("\n")
                
                # For each option
                for line in info:
                    lineSplit = line.split(" ")
                    if str(lineSplit[0]) == str(emoji): # Ensure that this is a real option
                        # Get the discord role
                        discordRole = getRole(" ".join(lineSplit[1:]))
                        if discordRole: # If it exists
                            # Check the user's roles
                            userRole = nextcord.utils.get(user.roles, id = discordRole.id)
                            # Give / Take the role
                            try:
                                if userRole:
                                    await user.remove_roles(discordRole)
                                else:
                                    await user.add_roles(discordRole)
                            except nextcord.errors.Forbidden:
                                # No permissions. Send an error
                                await sendNoPermissionsError(discordRole, user)
                            
                            # Remove their reaction
                            await message.remove_reaction(emoji, user)
                        else:
                            # If the discord role does not exist, send an error
                            await sendNoRoleError()
                            # Try to remove their reaction. If we can't, it's fine
                            try:
                                await message.remove_reaction(emoji, user)
                            except nextcord.errors.Forbidden:
                                pass
                            return
#END of reaction bot functionality: ------------------------------------------------------------------------------------------------------------------------------------------------------





#Start of join/leave messages functionality: ----------------------------------------------------------------------------------------------------------------------------------------------
guildsBanning = []
@bot.event
async def on_member_join(member: nextcord.Member):
    global guildsBanning
    
    server = Server(member.guild.id)
    
    #banning------------------------------------------------------------
    if server.autoBanExists(member.id):
        server.deleteAutoBan(member.id)
        server.saveAutoBans()
        if member.guild.me.guild_permissions.ban_members:
            try:
                #add server to guildsBanning list to prevent a leave message from appearing.
                if not (member.guild.id in [guild[0] for guild in guildsBanning]): guildsBanning.append([member.guild.id, datetime.datetime.now()])
                
                await member.ban(delete_message_seconds = 0, reason = "This member was already scheduled to be banned by InfiniBot.")
                
                return
            
            except nextcord.errors.Forbidden:
                #take this guild out of guildsBanning
                for guild in guildsBanning:
                    if guild[0] == member.guild.id:
                        guildsBanning.remove(guild)
                        break
                
                await sendErrorMessageToOwner(member.guild, "Ban Members")
        else:
            await sendErrorMessageToOwner(member.guild, "Ban Members")
    
    #give them levels --------------------------------------------------------------
    server.levels.addMember(member.id)

    #welcome them -----------------------------------------------------------------
    joinMessage: str = server.joinMessage
    if joinMessage != None: #if we don't have a join message, what's the point?
        if server.joinChannel != None: #set the join channel (if none, then it is the system channel)
            channel = server.joinChannel
        else:
            if member.guild.system_channel != None:
                channel = member.guild.system_channel
            else:
                channel = None #if we set channel to none here, all other processes will be jumped
        
        #double check permissions
        if channel and not await checkTextChannelPermissions(channel, True, customChannelName = f"Join Message Channel (#{channel.name})"): #double check permissions
            channel = None
            
            
        if channel != None:
            joinMessageFormatted = joinMessage.replace("[member]", member.mention)
            
            embed = nextcord.Embed(title = f"{member} just joined the server!", description = joinMessageFormatted, color =  nextcord.Color.gold(), timestamp = datetime.datetime.now())
            embeds = [embed]
            
            #card (if necessary)
            if server.allowJoinCardsBool:
                memberData = Member(member.id)
                if memberData.joinCard.enabled:
                    card = memberData.joinCard.embed()
                    embeds.append(card)
            
            
            await channel.send(embeds = embeds)
    
    #give them roles --------------------------------------------------------------
    for role in server.defaultRoles:
        await member.add_roles(role)
        
    #update stats --------------------------------------------------------------------
    if server.statsMessage.active:
        async def exceptionFunction():
            await sendErrorMessageToOwner(member.guild, None, message = "InfiniBot cannot access the Server Statistics message anymore to edit it. The message has been deactivated. Use /setup_stats to activate another.", administrator = False)
            server.statsMessage.setValue(None)
            server.saveData()
            
        try:
            bool, message = await server.statsMessage.checkMessage()
            if message != None:
                await message.edit(embed = getStatsMessage(message.guild))
            else:
                await exceptionFunction()
        except nextcord.errors.Forbidden or TypeError or ValueError:
            await exceptionFunction()
            
@bot.event
async def on_member_remove(member: nextcord.Member):
    global guildsBanning
    
    if member == None: return
    if member.guild == None: return
    if member.guild.id == None: return
    
    server = Server(member.guild.id)
    if server.guild == None: return

    #if this member was auto-banned, then we don't want to trigger a leave message. This should be silent.
    #Check to make sure that the above condition is not true.
    for guild in guildsBanning:
        if guild[0] == member.guild.id:
            #we are in there. Is the timing correct?
            if (datetime.datetime.now() - guild[1]).seconds <= 3:
                #this is real. We need to clear this guild from guildsBanning.
                guildsBanning.remove(guild)
                
                #make sure to trigger the log
                await memberRemove(member.guild, member)
                return
            else:
                #this is not within our time-frame. Thus, it will never be used. Let's remove it.
                guildsBanning.remove(guild)
                #also, we found our guild now. Our job in this loop is done.
                break
            
            
            
    #say farewell to them: --------------------------------------------------------------------------------
    leaveMessage: str = server.leaveMessage
    if leaveMessage != None: #if we don't have a leave message, what's the point?
        if server.leaveChannel != None: #set the leave channel (if none, then it is the system channel)
            channel = server.leaveChannel
        else:
            if member.guild.system_channel != None:
                channel = member.guild.system_channel
            else:
                channel = None #if we set channel to none here, all other processes will be jumped
        
        #double check permissions
        if channel and not await checkTextChannelPermissions(channel, True, customChannelName = f"Leave Message Channel (#{channel.name})"): #double check permissions
            channel = None
            
            
        if channel != None:
            leaveMessageFormatted = leaveMessage.replace("[member]", member.mention)
            
            embed = nextcord.Embed(title = f"{member} just left the server.", description = leaveMessageFormatted, color =  nextcord.Color.gold(), timestamp = datetime.datetime.now())
            await channel.send(embed = embed)
            
            
            
    #update stats: ---------------------------------------------------------------------------------------------
    if server.statsMessage.active:
        async def exceptionFunction():
            await sendErrorMessageToOwner(member.guild, None, message = "InfiniBot cannot access the Server Statistics message anymore to edit it. The message has been deactivated. Use /setup_stats to activate another.", administrator = False)
            server.statsMessage.setValue(None)
            server.saveData()
            
        try:
            bool, message = await server.statsMessage.checkMessage()
            if message != None:
                await message.edit(embed = getStatsMessage(message.guild))
            else:
                await exceptionFunction()
        except nextcord.errors.Forbidden or TypeError or ValueError:
            await exceptionFunction()

    await memberRemove(member.guild, member)
#END of join/leave messages functionality: ---------------------------------------------------------------------------------------------------------------------------------------------







#Start of birthday messages functionality: ---------------------------------------------------------------------------------------------------------------------------------------------
async def checkForBirthdays(nextTime, currentTime):
    print("checking birthdays -----------------------------------------------")
    #check for birthdays
    birthdays_allServers = fileOperations.getAllBirthdays()
    for server in birthdays_allServers:
        try:
            serverSplit = server.split("———")
            for member in serverSplit[1:]:
                try:
                    memberSplit = member.split("|||")
                    birthdayTime = datetime.datetime.strptime(memberSplit[1], f"%m/%d/%Y")
                    #uncomment for telemetry
                    #print("memberSplit:", memberSplit) print("Day Delta:", abs(birthdayTime.day - nextTime.day)) print("Month Delta:", abs(birthdayTime.month - nextTime.month))
                    if birthdayTime.day == nextTime.day and birthdayTime.month == nextTime.month: #if it is thier birthday
                        Server = None
                        for guild in bot.guilds:
                            if guild.id == int(serverSplit[0]):
                                Server = guild

                        if Server == None: break

                        _member = await bot.fetch_user(memberSplit[0])
                        #uncomment for telemetry
                        #print("bot guilds:", bot.guilds) print("Server Data:", Server) print("Server Members:", Server.members) print("_member:", _member)
                        if _member == None: continue

                        year = currentTime.year - birthdayTime.year


                        dm = await _member.create_dm()
                        
                        memberSettings = Member(_member.id)
                        
                        
                        channel = await getChannel(Server)
                        if channel == None: break
                        if len(memberSplit) == 2:
                            await channel.send(embed = nextcord.Embed(title = f"Happy Birthday {_member.name}!", description = f"{_member.mention} just turned {year}! Congratulations!", color =  nextcord.Color.gold()))
                            if memberSettings.dmsEnabledBool: await dm.send(embed = nextcord.Embed(title = f"Happy Birthday {_member.name}!", description = f"You just turned {year}! Congratulations!\n\nTo opt out of dm notifications, use {opt_out_of_dms.get_mention()}", color =  nextcord.Color.gold()))
                        else:
                            await channel.send(embed = nextcord.Embed(title = f"Happy Birthday {memberSplit[2]}!", description = f"{_member.mention} just turned {year}! Congratulations!", color =  nextcord.Color.gold()))
                            if memberSettings.dmsEnabledBool: await dm.send(embed = nextcord.Embed(title = f"Happy Birthday {memberSplit[2]}!", description = f"You just turned {year}! Congratulations!\n\nTo opt out of dm notifications, use {opt_out_of_dms.get_mention()}", color =  nextcord.Color.gold()))
                except Exception as err:
                    print("Checking Birthdays Member Exception: " + str(err))
                    continue
                
        except Exception as err:
            print("Checking Birthdays Server Exception: " + str(err))
            continue

@view.subcommand(name = "birthdays", description = "View all of the saved birthdays")
async def view_birthdays(interaction: Interaction):
    server = Server(interaction.guild.id)
    embed = nextcord.Embed(title = "Birthdays", color =  nextcord.Color.blue())
    
    birthdays = []
    for birthday in server.birthdays:
        try:
            if birthday.member == None:
                server.deleteBirthday(birthday.memberID)
                server.saveBirthdays()
                continue
            
            if birthday.realName != None: birthdays.append(f"{birthday.member.mention} ({str(birthday.realName)}) - {birthday.date}")
            else: birthdays.append(f"{birthday.member.mention} - {birthday.date}")
                
        except Exception as err:
            print("Birthdays View Error:", err)

    if len(server.birthdays) == 0:
        embed.description = f"No birthdays yet. Go to \"{dashboard.get_mention()} → Birthdays → Add\" to add one!"
    else:
        embed.description = "\n".join(birthdays)

    await interaction.response.send_message(embed = embed, view = InviteView())
#END of birthday messages functionality: -----------------------------------------------------------------------------------------------------------------------------------------------





#Start of purge channels functionality: --------------------------------------------------------------------------------------------------------------------------------------------------
purging = []     
@bot.slash_command(name = "purge", description = "Purge any channel (requires manage messages permission and Infinibot Mod)", dm_permission=False)
async def purge(interaction: Interaction, amount: str = SlashOption(description="The amount of messages you want to delete. \"All\" purges the whole channel")):
    global purging
    
    if interaction.user.guild_permissions.manage_messages == False:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Permission Error", description = "You do not have the \"manage messages\" permission which is required to use this command.", color =  nextcord.Color.red()), ephemeral=True)
        return


    if await hasRole(interaction):
        if amount.lower() == "all":
            await interaction.response.defer()
            
            if not interaction.channel.permissions_for(interaction.guild.me).manage_channels:
                await interaction.followup.send(embed = nextcord.Embed(title = "Permission Error", description = "InfiniBot needs to have the Manage Channels permission in this channel to use this command.", color = nextcord.Color.red()), ephemeral = True)
                return
            
            #create a channel, and move it to where it should
            newChannel: nextcord.TextChannel = await interaction.channel.clone(reason = "Purging Channel")
            await newChannel.edit(position = interaction.channel.position + 1, reason = "Purging Channel")
            
            server = Server(interaction.guild.id)
            #check for if the channel is connected to anything. And if so, replace it:
            
            def getID(channel):
                if channel == None: return None
                else: return channel.id
                 
            if interaction.channel.id == getID(server.adminChannel): server.adminChannel = newChannel
            if interaction.channel.id == getID(server.logChannel): server.logChannel = newChannel
            if interaction.channel.id == getID(server.levelingChannel): server.levelingChannel = newChannel
            if interaction.channel.id == getID(server.joinChannel): server.joinChannel = newChannel
            if interaction.channel.id == getID(server.leaveChannel): server.leaveChannel = newChannel
            if interaction.channel.id in [getID(channel) for channel in server.levelingExemptChannels]:
                server.levelingExemptChannels.remove(interaction.channel)
                server.levelingExemptChannels.append(newChannel)
            
            server.saveData()
            
            #delete old channel
            await interaction.channel.delete(reason = "Purging Channel")
            
            
            await newChannel.send(embed = nextcord.Embed(title = "Purged Messages", description = f"{interaction.user} has instantly purged {newChannel.mention} of all messages", color =  nextcord.Color.orange()), view = InviteView())
            return

        try:
            int(amount)
        except TypeError:
            interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "\"Amount\" needs to be a number", color =  nextcord.Color.red()), ephemeral = True)
            return

        await interaction.response.defer()
        
        if not str(interaction.guild_id) in purging:
            purging.append(str(interaction.guild_id))

        deleted = await interaction.channel.purge(limit = int(amount) + 1)

        await asyncio.sleep(1)

        if str(interaction.guild_id) in purging:
            purging.pop(purging.index(str(interaction.guild_id)))

        await interaction.channel.send(embed = nextcord.Embed(title = "Purged Messages", description = f"{interaction.user} has purged {interaction.channel.mention} of {str(len(deleted) - 1)} messages", color =  nextcord.Color.orange()), view = InviteView())
#END of purge channels functionality: ----------------------------------------------------------------------------------------------------------------------------------------------------






#Start of logging bot functionality: -----------------------------------------------------------------------------------------------------------------------------------------------------
def shouldLog(guild_id):
    server = Server(guild_id)

    if server.loggingBool == True:
        if server.logChannel == None:
            return False, None
        else:
            return True, server.logChannel
    else:
        return False, None

@set.subcommand(name = "log_channel", description = "Use this channel for logging. Channel should only be viewable by admins. (requires Infinibot Mod)")
async def setLogChannel(interaction: Interaction):
   if await hasRole(interaction) and await checkIfTextChannel(interaction):
        server = Server(interaction.guild.id)

        server.logChannel = interaction.channel
        server.saveData()


        await interaction.response.send_message(embed = nextcord.Embed(title = "Log Channel Set", description = f"This channel will now be used for logging.\n\nNote: It is highly recommended that you set the notifications settings for this channel to \"nothing\".\n\nAction done by {interaction.user}", color =  nextcord.Color.green()), view = SupportAndInviteView())
          
@bot.event
async def on_raw_message_edit(payload: nextcord.RawMessageUpdateEvent):
    #find the guild
    guild = None
    for _guild in bot.guilds:
        if _guild.id == payload.guild_id:
            guild = _guild
            break
    if guild == None: return
    
    #see if we should even be doing this
    ShouldLog, logChannel = shouldLog(guild.id)

    #find the channel
    channel = None
    for channel in guild.channels:
        if channel.id == payload.channel_id:
            channel = channel
            break
    if channel == None: return
    
    if not channel.permissions_for(guild.me).read_message_history:
        await sendErrorMessageToOwner(guild, "View Message History", channel = f"one or more channels (including #{channel.name})")
        return
    
    #if we have it, grab the before message
    beforeMessage = payload.cached_message
    
    #find the message
    afterMessage = None
    try:
        history = await channel.history().flatten()
        for message in history:
            if history.index(message) > 500: return
            if int(message.id) == int(payload.message_id):
                afterMessage: nextcord.Message = message
                break
    except:
        return
            
    if afterMessage == None: return
    
    #punish profanity (if any)
    await punnishProfanity(Server(guild.id), afterMessage)
    
    #test for false-positives
    if not ShouldLog: return
    if afterMessage.author.bot == True: return
    if afterMessage.content == "": return
    if beforeMessage != None and beforeMessage.content == "": return
    if beforeMessage != None and afterMessage.content == beforeMessage.content: return
    
    #UI Log
    await trigger_edit_log(guild, beforeMessage, afterMessage, logChannel = logChannel)
 
async def trigger_edit_log(guild: nextcord.Guild, beforeMessage: nextcord.Message, afterMessage: nextcord.Message, user: nextcord.Member = None, logChannel: nextcord.TextChannel = None):
    if not user: user = afterMessage.author
    if not logChannel:
        server = Server(guild.id)
        logChannel = server.logChannel
        if not logChannel or not server.loggingBool:
            return;
    
    url = afterMessage.jump_url

    Embed = nextcord.Embed(title = "Message Edited", description = f"Edited by: {user}", color = nextcord.Color.yellow(), timestamp = datetime.datetime.now())
    
    # Format messages if they're embeds
    if len(beforeMessage.embeds) != 0:
        beforeMessage = f"**Title:** {beforeMessage.embeds[0].title}\n**Description:** {beforeMessage.embeds[0].description}"
    else:
        beforeMessage = beforeMessage.content
    if len(afterMessage.embeds) != 0:
        afterMessage = f"**Title:** {afterMessage.embeds[0].title}\n**Description:** {afterMessage.embeds[0].description}"
    else:
        afterMessage = afterMessage.system_content
    
    if beforeMessage != None:
        originalMessage = beforeMessage
        if len(originalMessage) > 1024:
            originalMessage = "*Too long to display*"
            
        Embed.add_field(name = "Original Message", value = originalMessage, inline = True)
     
    editedMessage = afterMessage
    if len(editedMessage) > 1024:
        editedMessage = "*Too long to display*"
    Embed.add_field(name = "Edited Message", value = editedMessage, inline = True)
    
    Embed.add_field(name = "More", value = f"[Go to Message]({url})", inline = False)

    if logChannel and await checkTextChannelPermissions(logChannel, True, customChannelName = f"Log Message Channel (#{logChannel.name})"): 
        await logChannel.send(embed = Embed)
    
async def file_computation(file: nextcord.Attachment):
    #disclaimer: I truthfully have no idea how this bit of the code works. I mean, I have *some* idea, but chatgpt wrote it, so...
    try:
        file_bytes = await file.read()
        
        with mmap.mmap(-1, len(file_bytes), access=mmap.ACCESS_WRITE) as mem:
            mem.write(file_bytes)
            mem.seek(0)
            file_data = bytes(mem)
            
        file = nextcord.File(io.BytesIO(file_data), file.filename, description=file.description, spoiler=file.is_spoiler())
        return file
    except:
        return None
    
async def files_computation(deleted_message: nextcord.Message, log_channel: nextcord.TextChannel, log_message: nextcord.Message):
    #disclaimer: I truthfully have no idea how this bit of the code works. I mean, I have *some* idea, but chatgpt wrote it, so...
    # Create tasks for each attachment
    tasks = []
    for attachment in deleted_message.attachments:
        tasks.append(asyncio.create_task(file_computation(attachment)))
    
    # Wait for all tasks to complete asynchronously
    completed_tasks = await asyncio.gather(*tasks)
    
    # Collect the files from the completed tasks
    files = [task_result for task_result in completed_tasks if task_result is not None]
    
        
    if len(files) > 0:
        await log_channel.send(files = files, reference = log_message)
    else:
        await log_channel.send(embed = nextcord.Embed(title = "Error", description = "There was a problem when retrieving these files. They have been lost to the void.", color = nextcord.Color.red()), reference = log_message)
 
@bot.event
async def on_raw_message_delete(payload: nextcord.RawMessageDeleteEvent):
    global autoDeletedMessageTime, purging

    time.sleep(1) #we need this time delay for some other features

    if autoDeletedMessageTime != None: #see if this is InfiniBot's doing
        if ((datetime.datetime.utcnow() - autoDeletedMessageTime).seconds <= 5):
            return
    
    #find the message (CSI Time!)
    message = None
    guild = None
    for _guild in bot.guilds:
        if _guild.id == payload.guild_id:
            guild = _guild
            break
    if guild == None: return

    channel = None
    for _channel in guild.channels:
        if _channel.id == payload.channel_id:
            channel = _channel
            break
    
    if channel == None: return

    message = payload.cached_message
    #we got the message!!! (Or at least information about it)
    
    # Remove the message if we're storing it
    server = Server(guild.id)
    server.messages.delete(payload.message_id)
    server.messages.save()
    del server

    if str(guild.id) in purging: return #again, check to see if this is InfiniBot's doing
    
    #gather more data and eliminate cases -----------------------------------------------------------------------------------------------------------------------------
    logBool, logChannel = shouldLog(guild.id)
    if logBool:
        if logChannel == None: return #we can't do anything
        
        #get more information about the message with Audit Logs
        try:
            entry = list(await guild.audit_logs(limit=1, action=nextcord.AuditLogAction.message_delete).flatten())[0]
        except nextcord.errors.Forbidden:
            await sendErrorMessageToOwner(guild, "View Audit Log", guildPermission = True)
            return
        except IndexError:
            return
        except Exception as e:
            print("on_raw_message_delete:")
            print(e)
            return
        
        #log whether or not the audit log is fresh enough to be accurate (within 5 seconds)
        freshAuditLog = (entry.created_at.month == datetime.datetime.utcnow().month and entry.created_at.day == datetime.datetime.utcnow().day and entry.created_at.hour == datetime.datetime.utcnow().hour and ((datetime.datetime.utcnow().minute - entry.created_at.minute) <= 5))
        
        #we prioritize the author of the message if we know it, but if we don't we use this
        if not message: user = entry.target
        else: user = message.author
        #set the deleter (because we didn't know that before)
        deleter = entry.user
        
        #eliminate whether InfiniBot is the author / deleter (only do this if we're sure that the audit log is fresh)
        if user.id == bot.application_id and freshAuditLog: return
        if deleter.id == bot.application_id and freshAuditLog: return
            
        
        #send log information!!! -------------------------------------------------------------------------------------------------------------------------------------------
        embed = nextcord.Embed(title = "Message Deleted", color = nextcord.Color.red(), timestamp = datetime.datetime.now())
        embeds = []
        code = 1
        
        #embed description and code
        if freshAuditLog: 
            embed.description = f"{deleter} deleted {user}'s message from {channel.mention}"
            if message:
                code = 1
            else:
                code = 2
        else:
            if not message:
                embed.description = f"A message was deleted from {channel.mention}"
                code = 3
            else:
                embed.description = f"{message.author}'s message was deleted from {channel.mention}"
                code = 4
                
        
        #message content
        if message: 
            if message.content != "": embed.add_field(name = "Message", value = message.content)
        else: 
            embed.add_field(name = "Message", value = "The message cannot be retrieved. This is due to the message being deleted too long after creation. This is a Discord limitation.", inline = False)
        
        #attached Embeds
        if message and message.embeds != []:
            attachedMessage = "Attached below"
            if len(message.embeds) > 9:
                attachedMessage = f"9/{len(message.embeds)} are attached below"
                
            embed.add_field(name = "Embeds", value = f"This message contained one or more embeds. ({attachedMessage})", inline = False)
            embeds = message.embeds
            
        #attached Files
        if message and message.attachments != []:              
            embed.add_field(name = "Files", value = f"This message contained one or more files. (Attached Below)\n→ Please wait as InfiniBot processes these files and Discord uploads them", inline = False)
            
            
        #the footer
        embed.set_footer(text = f"Message ID: {payload.message_id}\nCode: {code}")
        
        #double check that the embed is fine in terms of character size
        if len(embed.fields) > 0:
            for field in embed.fields:
                if len(field.value) > 1024:
                    field.value = "Message is too long!!! Discord won't display it."

        #actually send the embed
        view = ShowMoreButton()
        if logChannel and await checkTextChannelPermissions(logChannel, True, customChannelName = f"Log Message Channel (#{logChannel.name})"): 
            logMessage = await logChannel.send(view = view, embeds = ([embed] + (embeds[0:8] if len(embeds) >= 10 else embeds)))
            if message and message.attachments != []:
                await files_computation(message, logChannel, logMessage)

@bot.event
async def on_guild_channel_delete(channel: nextcord.abc.GuildChannel):
    server = Server(channel.guild.id)
    server.messages.deleteAllFromChannel(channel.id)
    server.messages.save()

@bot.event
async def on_member_update(before: nextcord.Member, after: nextcord.Member):
    global nicknameChanged
    
    if before.nick != after.nick and not after.guild.id in nicknameChanged:
        ShouldLog, logChannel = shouldLog(after.guild.id)
        if ShouldLog:

            entry = list(await after.guild.audit_logs(limit=1).flatten())[0]
            user = entry.user

            embed = nextcord.Embed(title = "Nickname Changed", description = f"{user} changed {after}'s nickname.", color = nextcord.Color.blue(), timestamp = datetime.datetime.now())

            if before.nick != None: embed.add_field(name = "Before", value = before.nick, inline = True)
            else: embed.add_field(name = "Before", value = "None", inline = True)

            if after.nick != None: embed.add_field(name = "After", value = after.nick, inline = True)
            else: embed.add_field(name = "After", value = "None", inline = True)
            
            if logChannel and await checkTextChannelPermissions(logChannel, True, customChannelName = f"Log Message Channel (#{logChannel.name})"): 
                await logChannel.send(embed = embed)
            
            
        if after.nick != None: await checkNickname(after.guild, after)

    if before.roles != after.roles:
        ShouldLog, logChannel = shouldLog(after.guild.id)
        if ShouldLog:

            addedRoles = []
            for afterRole in after.roles:
                for beforeRole in before.roles:
                    foundRole = False
                    if beforeRole == afterRole:
                        foundRole = True
                        break

                if foundRole == False:
                    addedRoles.append(afterRole.mention)
                    
                    if after.guild.premium_subscriber_role != None: 
                        if afterRole.id == after.guild.premium_subscriber_role.id: return
            
            deletedRoles = []
            for beforeRole in before.roles:
                for afterRole in after.roles:
                    foundRole = False
                    if beforeRole == afterRole:
                        foundRole = True
                        break
                
                if foundRole == False:
                    deletedRoles.append(beforeRole.mention)
            try:
                entry = list(await after.guild.audit_logs(limit=1).flatten())[0]
            except nextcord.errors.Forbidden:
                return
                
            user = entry.user

            embed = nextcord.Embed(title = "Roles Modified", description = f"{user} modified {after}'s roles.", color = nextcord.Color.blue(), timestamp = datetime.datetime.now())

            if len(addedRoles) > 0:
                embed.add_field(name = "Added", value = "\n".join(addedRoles), inline = True)

            if len(deletedRoles) > 0:
                embed.add_field(name = "Removed", value = "\n".join(deletedRoles), inline = False)

            if logChannel and await checkTextChannelPermissions(logChannel, True, customChannelName = f"Log Message Channel (#{logChannel.name})"): 
                await logChannel.send(embed = embed)
            
    if before.communication_disabled_until != after.communication_disabled_until:
        ShouldLog, logChannel = shouldLog(after.guild.id)
        if ShouldLog:
            entry = list(await after.guild.audit_logs(limit=1).flatten())[0]
            user = entry.user
                
            if before.communication_disabled_until == None: #if they weren't timed out before
                #get the seconds
                timeoutTime: datetime.timedelta = after.communication_disabled_until - datetime.datetime.now(datetime.timezone.utc)
                
                #round to the nearest second
                roundedTimeoutTime = datetime.timedelta(seconds=round(timeoutTime.total_seconds() / 60) * 60)
                
                #display
                embed = nextcord.Embed(title = "Member Timed-Out", description = f"{user} timed out {after} for {timedeltaToEnglish(roundedTimeoutTime)}", color = nextcord.Color.orange(), timestamp = datetime.datetime.now())
                if entry.reason != None:
                    embed.add_field(name = "Reason", value = entry.reason)
                
                if logChannel and await checkTextChannelPermissions(logChannel, True, customChannelName = f"Log Message Channel (#{logChannel.name})"): 
                    await logChannel.send(embed = embed)
                
            elif after.communication_disabled_until == None: #their timeout was removed manually
                embed = nextcord.Embed(title = "Timeout Revoked", description = f"{user} revoked {after}'s timeout", color = nextcord.Color.orange(), timestamp = datetime.datetime.now())
                
                if logChannel and await checkTextChannelPermissions(logChannel, True, customChannelName = f"Log Message Channel (#{logChannel.name})"): 
                    await logChannel.send(embed = embed)

async def memberRemove(guild: nextcord.Guild, member: nextcord.Member):
    if guild == None: return
    if guild.unavailable: return
    if guild.me == None: return
    
    if not guild.me.guild_permissions.view_audit_log:
        await sendErrorMessageToOwner(guild, "View Audit Log", guildPermission = True)
        return
    
    auditLogEntries = await guild.audit_logs(limit=1).flatten()
    if len(auditLogEntries) == 0: return
    
    entry = list(auditLogEntries)[0]
    user = entry.user 
    reason = entry.reason

    ShouldLog, channel = shouldLog(guild.id)
    if ShouldLog:

        if entry.action == AuditLogAction.kick:
            embed = nextcord.Embed(title = "Member Kicked", description = f"{user} kicked {member}.", color = nextcord.Color.red(), timestamp = datetime.datetime.now())
            embed.add_field(name = "Reason", value = f"{reason}", inline = False)
            
        elif entry.action == AuditLogAction.ban:
            embed = nextcord.Embed(title = "Member Banned", description = f"{user} banned {member}.", color = nextcord.Color.dark_red(), timestamp = datetime.datetime.now())
            embed.add_field(name = "Reason", value = f"{reason}", inline = False)
            
        else:
            return
        
        if channel and await checkTextChannelPermissions(channel, True, customChannelName = f"Log Message Channel (#{channel.name})"):
            await channel.send(embed = embed)
#END of logging bot functionality: -------------------------------------------------------------------------------------------------------------------------------------------------------






#Join-to-create VC: -------------------------------------------------------------------------------------------------------------------------------------------------------------------     
@bot.event
async def on_voice_state_update(member: nextcord.Member, before: nextcord.VoiceState, after: nextcord.VoiceState):
    if before.channel == None and after.channel == None: return
    if after.channel != None:
        server = Server(member.guild.id)
        if after.channel.id in [vc.id for vc in server.VCs]:
            #double check that we have permissions
            for vc in server.VCs:
                if vc.id == after.channel.id:
                    if not vc.active:
                        return
                    break
            
            try:
                vc = await after.channel.category.create_voice_channel(name = f"{member.name} Vc")
            except nextcord.errors.Forbidden:
                await sendErrorMessageToOwner(member.guild, "Manage Channels", guildPermission = True)
                return
            try:
                await member.move_to(vc)
            except nextcord.errors.Forbidden:
                await sendErrorMessageToOwner(member.guild, "Move Members")
                return
            
    if before.channel != None:
        if before.channel.members == []:
            try:
                channelNameSplit = before.channel.name.split(" ")
                memberName = " ".join(channelNameSplit[:-1])
                if memberName in [member.name for member in member.guild.members] and channelNameSplit[-1] == "Vc":
                    #double check that we can view the channel
                    if not before.channel.permissions_for(member.guild.me).view_channel:
                        await sendErrorMessageToOwner(member.guild, "View Channels", channel = f"#{before.channel.name}")
                        return
                    
                    await before.channel.delete()
            except nextcord.errors.Forbidden:
                if before.channel.permissions_for(member.guild.me).manage_channels == False:
                    await sendErrorMessageToOwner(member.guild, "Manage Channels", guildPermission = True)
                if before.channel.permissions_for(member.guild.me).connect == False:
                    await sendErrorMessageToOwner(member.guild, "Connect", guildPermission = True)
                return
#Join-to-create vc END: --------------------------------------------------------------------------------------------------------------------------------------------------------------





#Leveling: ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def getLevel(score: int):
    score /= 10
    if score == 0: return 0
    return(math.floor(score ** 0.65)) #levels are calculated by x^0.65

def getScore(level: int):
    if level == 0: return 0
    
    score = level**(1/0.65)
    score *= 10
    score = math.floor(score)
    
    for _ in range(0, 100):
        if getLevel(score) == level:
            return score
        elif getLevel(score) > level:
            score -= 1
        else:
            score += 1
    
    return(score) #levels are calculated by x^0.65

def setScoreOfMember(server: Server, member_id, score):
    if score != 0: #if we are not reseting thier score
        memberLevel = server.levels.getMember(member_id)
        
        if memberLevel != None: memberLevel.score = score #if they already had a score
        else: server.levels.addMember(member_id, score = score) #else, create one
    else:
        server.levels.deleteMember(member_id)
            
    server.saveLevels()

async def canLevel(interaction: Interaction, server: Server):
    """Determins whether or not leveling is enabled for the server. NOT SILENT!"""
    if server.levelingBool:
        return True
    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Leveling Disabled", description = "Leveling has been turned off. type \"/enable leveling\" to turn it back on.", color = nextcord.Color.red()), ephemeral = True)
        return False

async def giveLevels(message: nextcord.Message):
    """Manages the distribution of points (and also levels and level rewards, but indirect). Simply requires a message."""
    MAX_POINTS_PER_MESSAGE = 40 # Messages are capped at these amount of points
    
    
    member = message.author
    if member.id == bot.application_id: return

    channel = message.channel
    
    server = Server(message.guild.id)
    if message.channel.id in [channel.id for channel in server.levelingExemptChannels]: return
    
    lastFiveMessages = channel.history(limit = 6) #it is 6 because this includes the message just sent.
    
    count = 0
    async for _message in lastFiveMessages:
        if count == 0: 
            count += 1 
            continue
        if _message.content == None or _message.content == "": 
            continue
        if Levenshtein.distance(message.content, _message.content) < 3:
            return
        
        count += 1

    words = message.content.split(" ")
    totalPoints = 0
    for word in words:
        for _ in word: totalPoints += 1
        
    totalPoints /= 10
    roundedPoints = round(totalPoints)
    
    if roundedPoints > MAX_POINTS_PER_MESSAGE:
        roundedPoints = MAX_POINTS_PER_MESSAGE
    
    memberLevel = server.levels.getMember(member.id)
    if memberLevel != None:
        originalLevel = getLevel(memberLevel.score)
        memberLevel.score += roundedPoints
    else:
        originalLevel = 0
        server.levels.addMember(member.id, roundedPoints)
        memberLevel = server.levels.getMember(member.id)
        
    nowLevel = getLevel(memberLevel.score)
    server.saveLevels()
    
    if originalLevel != nowLevel:
        await checkForLevelsAndLevelRewards(message.guild, message.author, levelup_announce = True)
  
async def checkForLevelsAndLevelRewards(guild: nextcord.Guild, member: nextcord.Member, levelup_announce: bool = False, silent = False):
    """Handles the distribution of levels and level rewards"""
    server = Server(guild.id)
    memberLevel = server.levels.getMember(member.id)
    if memberLevel != None:
        score = memberLevel.score
        level = getLevel(score)
    else:
        score = 0
        level = 0
    
    
    memberOptions = Member(member.id)
    
    
    #level-up messages
    if levelup_announce and (not silent) and (server.levelingMessage != None):
        message = server.levelingMessage.replace("[level]", str(level))
        embed = nextcord.Embed(title = f"Congratulations, {member}!", description = message, color = nextcord.Color.from_rgb(235, 235, 235))
        embeds = [embed]
        
        #get the card (if needed)
        if server.allowLevelCardsBool:
            memberData = Member(member.id)
            if memberData.levelCard.enabled:
                card = memberData.levelCard.embed()
                card.description = card.description.replace("[level]", str(level))
                embeds.append(card)
        
        
        if server.levelingChannel != None:
            await server.levelingChannel.send(embeds = embeds) #white-ish
        else:
            channel = await getChannel(guild)
            if channel != None: await channel.send(embeds = embeds) #white-ish
    
    #level-reward messages
    for levelReward in server.levels.levelRewards:
        if levelReward.level <= level:
            #we need to give them this role.
            if not levelReward.role in member.roles:
                try:
                    await member.add_roles(levelReward.role)
                except nextcord.errors.Forbidden:
                    await sendErrorMessageToOwner(guild, "Manage Roles", guildPermission = True)
                    return
                
                try:    
                    if server.levelingChannel != None and (not silent): await server.levelingChannel.send(embed = nextcord.Embed(title = f"Role Granted to {member}", description = f"{member.mention} has been granted the role of {levelReward.role.mention} as a result of reaching level {str(levelReward.level)}!", color = nextcord.Color.purple()))
                    else: 
                        channel = await getChannel(guild)
                        if channel != None and (not silent): await channel.send(embed = nextcord.Embed(title = f"Role Granted to {member}", description = f"{member.mention} has been granted the role of {levelReward.role.mention} as a result of reaching level {str(levelReward.level)}!", color = nextcord.Color.purple()))
                    
                    if memberOptions.dmsEnabledBool and (not silent): await member.send(embed = nextcord.Embed(title = f"Congratulations! You reached level {str(levelReward.level)} in \"{guild.name}\"!", description = f"As a result, you were granted the role of \"{levelReward.role.name}\". Keep your levels up, or else you will loose it!\n\nTo opt out of dm notifications, use {opt_out_of_dms.get_mention()}", color = nextcord.Color.purple()))
                except nextcord.errors.Forbidden:
                    await sendErrorMessageToOwner(guild, "Send Messages")
                    return
                
        else:
            #we need to take the role
            if levelReward.role in member.roles:
                try:
                    await member.remove_roles(levelReward.role)
                except nextcord.errors.Forbidden:
                    await sendErrorMessageToOwner(guild, "Manage Roles", guildPermission = True)
                    return
                
                try:
                    if server.levelingChannel != None and (not silent): await server.levelingChannel.send(embed = nextcord.Embed(title = f"Role Revoked from {member}", description = f"{member.mention} has been revoked the role of {levelReward.role.mention} as a result of loosing level {str(levelReward.level)}", color = nextcord.Color.dark_purple()))
                    else:
                        channel = await getChannel(guild) 
                        if channel != None and (not silent): channel.send(embed = nextcord.Embed(title = f"Role Revoked from {member}", description = f"{member.mention} has been revoked the role of {levelReward.role.mention} as a result of loosing level {str(levelReward.level)}", color = nextcord.Color.dark_purple()))
                    
                    if memberOptions.dmsEnabledBool and (not silent): await member.send(embed = nextcord.Embed(title = f"Oh, no! You lost a level and are now at level {str(levelReward.level)} in \"{guild.name}\"!", description = f"As a result, the role of \"{levelReward.role.name}\" has been revoked. Bring your levels back up, and win back your role!\n\nTo opt out of dm notifications, use {opt_out_of_dms.get_mention()}", color = nextcord.Color.dark_purple()))
                except nextcord.errors.Forbidden:
                    await sendErrorMessageToOwner(guild, "Send Messages")
                    return
  

@bot.slash_command(name = "leaderboard", description = "Get your level and the level of everyone on the server.", dm_permission=False)
async def leaderboard(interaction: Interaction):
    server = Server(interaction.guild.id)
    if not await canLevel(interaction, server): return
    
    rankedMembers = []
    
    for member in interaction.guild.members: 
        if member.bot: continue
        Member = server.levels.getMember(member.id)
        if Member != None:
            rankedMembers.append([member, Member.score])
        else:
            rankedMembers.append([member, 0])
    
    #sort
    rankedMembers = sorted(rankedMembers, key=lambda x: (-x[1], x[0].name))
    
    
    embed = nextcord.Embed(title = "Leaderboard", color = nextcord.Color.blue())
    
    rank, lastScore = 1, 0
    for member in rankedMembers: 
        #check if score is above 0
        if int(member[1]) == 0:
            continue
        
        index = rankedMembers.index(member)
        if index < 20:
            level = getLevel(member[1])
            if member[0].nick != None: memberName = f"{member[0]} ({member[0].nick})"
            else: memberName = f"{member[0]}"
            
            if member[1] < lastScore:
                rank += 1
            lastScore = member[1]
        
            embed.add_field(name = f"**#{rank} {memberName}**", value = f"Level: {str(level)}, Score: {str(member[1])}", inline = False)
        else:
            embed.add_field(name = f"+ {str(len(rankedMembers) - 20)} more", value = f"To see a specific member's level, type */level [member]*", inline = False)
            break
    
    
    #incase there is nothing
    if len(embed.fields) == 0:
        embed.description = "No one has scored any leveling points. Startup a conversation!"
    
    
    
    await interaction.response.send_message(embed = embed, view = InviteView())
    
@bot.slash_command(name = "my_level", description = "Get your level", dm_permission=False)
async def myLevel(interaction: Interaction):
    server = Server(interaction.guild.id)
    if not await canLevel(interaction, server): return
    
    Member = server.levels.getMember(interaction.user.id)
    if Member != None:
        score = Member.score
    else:
        score = 0
        
    level = getLevel(score)
    
    await interaction.response.send_message(embed = nextcord.Embed(title = "Your level", description = f"{interaction.user.mention} is at level {str(level)} (score: {str(score)})", color = nextcord.Color.blue()), view = InviteView())

@view.subcommand("levels", description = "Know how many points you need to reach any level")
async def levelsView(interaction: Interaction, level: int):
    response = ""
    if level >= 0:
        response = f"To get to level {str(level)}, you need a score of at least {str(getScore(level))}."
        
        await interaction.response.send_message(embed = nextcord.Embed(title = f"Level {str(level)}", description = response, color = nextcord.Color.blue()))
        
    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "\"Level\" cannot be negative", color = nextcord.Color.red()), ephemeral=True)

@set.subcommand(name = "level", description = "Set levels for any individual (Requires Infinibot Mod)")
async def setLevel(interaction: Interaction, member: nextcord.Member, level: int):
    if await hasRole(interaction):
        if level < 0:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "\"Level\" needs to be positive.", color = nextcord.Color.red()), ephemeral=True)
            return
        
        score = getScore(level)
        
        server = Server(interaction.guild.id)
        Member = server.levels.getMember(member.id)
        if Member != None: beforeScore = Member.score
        else: beforeScore = 0
        
        setScoreOfMember(server, member.id, score)    
        
        await interaction.response.send_message(embed = nextcord.Embed(title = "Levels Changed", description = f"{interaction.user} changed {member}'s level to {str(level)} (score: {str(score)})", color = nextcord.Color.green()))
        
        if getLevel(beforeScore) != level: await checkForLevelsAndLevelRewards(interaction.guild, member)

@set.subcommand(name = "score", description = "Set a score for any individual (Requires Infinibot Mod)")
async def setScore(interaction: Interaction, member: nextcord.Member, score: int):
    if await hasRole(interaction):
        if score < 0:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "\"Score\" needs to be positive.", color = nextcord.Color.red()), ephemeral=True)
            return
        
        server = Server(interaction.guild.id)
        Member = server.levels.getMember(member.id)
        if Member != None: beforeScore = Member.score
        else: beforeScore = 0
        
        setScoreOfMember(server, member.id, score)
        
        level = getLevel(score)
        
        await interaction.response.send_message(embed = nextcord.Embed(title = "Levels Changed", description = f"{interaction.user} changed {member}'s score to {str(score)} (level: {str(level)})", color = nextcord.Color.green()))
        
        if getLevel(beforeScore) != level: await checkForLevelsAndLevelRewards(interaction.guild, member)

#Leveling END: ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





#Stats: --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
statsInvalidMessage = nextcord.Embed(title = "Invalid Server Statistics", description = f"You can only have one server statistics message at once. Use /setup_stats to reactivate another link.", color = nextcord.Color.red())
def getStatsMessage(guild: nextcord.Guild):
    statsMessageEmbed = nextcord.Embed(title = "Server Statistics", description = f"Total Members: {guild.member_count}\nTotal Bots: {len(guild.bots)}", color = nextcord.Color.gold())
    return statsMessageEmbed

@bot.slash_command(name = "setup_stats", description = "Creates a stats message which will auto-update. (Requires InfiniBot Mod)", dm_permission = False, force_global = True)
async def setupStats(interaction: Interaction):
    global statsInvalidMessage
    if await hasRole(interaction):
        server = Server(interaction.guild.id)
        if await server.statsMessage.checkMessage():
            #they already have a stats message. We should double check that they want to continue.
            embed = nextcord.Embed(title = "Statistics Message Already Exists", description = f"Each server can only have one statistics message.\n\nCurrently, there is already a [statistics message]({server.statsMessage.link}). Would you like to replace it?", color = nextcord.Color.blue())

            view = ConfirmationView()
            await interaction.response.send_message(embed = embed, view = view, ephemeral = True)
            await view.wait()
            
            if view.choice == False:
                return
            
            #they agree to override
            #first, change the existing one....
            try:
                bool, message = await server.statsMessage.checkMessage()
                await message.edit(embed = statsInvalidMessage)
            except nextcord.errors.Forbidden:
                pass
            
            #next, add new one...
            statsMessage = getStatsMessage(interaction.guild)
            
            if not await checkTextChannelPermissions(interaction.channel, True):
                return
            
            message = await interaction.channel.send(embed = statsMessage)
            
            server.statsMessage.setValue(message)
            server.saveData()
            
        
        else:
            #they do not have a stats message.
            statsMessage = getStatsMessage(interaction.guild)
            
            if not await checkTextChannelPermissions(interaction.channel, True):
                return
            
            message = await interaction.channel.send(embed = statsMessage)
            
            server.statsMessage.setValue(message)
            server.saveData()
            
            await interaction.response.send_message(embed = nextcord.Embed(title = "How it works: Server Statistics", description = "This message will update every time someone joins / leaves the server. There can only be one of these, so if you run this command again, this one will become inactive.", color = nextcord.Color.blue()), ephemeral = True)
#Stats END: ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





#Bans: ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@bot.message_command(name = "Ban Message Author", dm_permission = False)
async def messageCommandBanMember(interaction: Interaction, message: nextcord.Message):
    await banMemberAction(interaction, message.author)
    
@bot.user_command(name = "Ban Member", dm_permission = False)
async def messageCommandBanMember(interaction: Interaction, member: nextcord.Member):
    await banMemberAction(interaction, member)
    
async def banMemberAction(interaction: Interaction, member: nextcord.Member):
    #double check that the user can ban members
    if interaction.user.guild_permissions.ban_members: #user can ban members
        if interaction.guild.me.guild_permissions.ban_members: #InfiniBot can ban members
            if interaction.user.id != member.id: #user not banning themself
                if member in interaction.guild.members: skipFurtherChecks = False
                else: skipFurtherChecks = True
                if skipFurtherChecks or (interaction.user.top_role.position > member.top_role.position): #user = higher rank than member
                    if skipFurtherChecks or (bot.application_id != member.id): #member is not InfiniBot
                        if skipFurtherChecks or (interaction.guild.me.top_role.position > member.top_role.position): #InfiniBot = higher rank than member
                            #check with them if this is truly what they want.
                            view = ConfirmationView(yesBtnText = "Yes, Ban", noBtnText = "No, Cancel")
                            
                            if interaction.guild.get_member(member.id) is not None:
                                #if member is in server
                                description = f"Are you sure that you want to ban {member.mention}?\n\nThis means that they will be kicked and not be able to re-join this server unless they are un-baned.\n\nNo messages will be deleted."
                            else:
                                #if member is not in the server
                                description = f"Are you sure that you want to ban \"{member}\"?\n\nThis means that they will not be able to join this server unless they are un-baned.\n\nNo messages will be deleted."
                            
                            
                            embed = nextcord.Embed(title = "Confirm Ban?", description = description, color = nextcord.Color.orange())
                            await interaction.response.send_message(embed = embed, view = view, ephemeral = True)
                            await view.wait()
                            
                            #read choice
                            if view.choice == False:
                                return
                            else:
                                try:
                                    await interaction.guild.ban(user = member, reason = f"{interaction.user} requested that this user be banned.", delete_message_seconds = 0)
                                except Exception as error:
                                    print(f"Error When Banning Member: {error}")
                                    await interaction.followup.send(embed = nextcord.Embed(title = "An Unknown Error Occured", description = "An unknown error occured while performing this action.", color = nextcord.Color.red()), ephemeral = True)
                                    return
                                
                                await interaction.followup.send(embed = nextcord.Embed(title = "Member Banned", description = f"{member} has been banned.", color = nextcord.Color.green()), ephemeral = True)
                        else:
                            await interaction.response.send_message(embed = nextcord.Embed(title = "InfiniBot Missing Rank", description = "InfiniBot needs a higher rank.\n\nInfiniBot cannot ban a member with the same/higher role as itself.", color = nextcord.Color.red()), ephemeral = True)
                    else:
                        await interaction.response.send_message(embed = nextcord.Embed(title = "InfiniBot Self-Ban", description = "InfiniBot cannot ban itself.", color = nextcord.Color.red()), ephemeral = True)
                else:
                    await interaction.response.send_message(embed = nextcord.Embed(title = "Missing Rank", description = "You cannot ban a member with the same/higher role.", color = nextcord.Color.red()), ephemeral = True)
            else:
                await interaction.response.send_message(embed = nextcord.Embed(title = "Self-Ban", description = "You cannot ban yourself.", color = nextcord.Color.red()), ephemeral = True)
        else:
            await interaction.response.send_message(embed = nextcord.Embed(title = "InfiniBot Missing Permissions", description = "InfiniBot needs the \"Ban Members\" permission to use this command.", color = nextcord.Color.red()), ephemeral = True)
    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Missing Permissions", description = "You need the \"Ban Members\" permission to use this command.", color = nextcord.Color.red()), ephemeral = True)
#Bans END: -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------







#Editing Messages: --------------------------------------------------------------------------------------------------------------------------------------------------------------------     
class EditEmbed(nextcord.ui.View):
    def __init__(self, messageID: int):
        super().__init__(timeout = None)
        self.messageID = messageID
        
    async def loadButtons(self, interaction: Interaction):
        self.message = await interaction.channel.fetch_message(self.messageID)
        self.server = Server(interaction.guild.id)
        self.messageInfo = self.server.messages.get(self.messageID)
        
        self.clear_items()
        
        editTextBtn = self.editTextButton(self)
        self.add_item(editTextBtn)
        
        editColorBtn = self.editColorButton(self)
        self.add_item(editColorBtn)
        
        editPersistencyBtn = self.editPersistencyButton(self, self.messageInfo)
        self.add_item(editPersistencyBtn)
        
    async def setup(self, interaction: Interaction):
        await self.loadButtons(interaction)
        
        mainEmbed = nextcord.Embed(title = "Edit Embed", description = "Edit the following embed's text and color.", color = nextcord.Color.yellow())
        editEmbed = self.message.embeds[0]
        embeds = [mainEmbed, editEmbed]
        try:
            await interaction.response.edit_message(embeds = embeds, view = self)
        except:
            await interaction.response.send_message(embeds = embeds, view = self, ephemeral = True)
  
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
                await beforeMessage.edit(embed = nextcord.Embed(title = self.titleInput.value, description = self.descriptionInput.value, color = beforeMessage.embeds[0].color))
                await self.outer.setup(interaction);
                
                # Trigger Edit Log
                afterMessage = await interaction.channel.fetch_message(self.outer.message.id)
                await trigger_edit_log(interaction.guild, beforeMessage, afterMessage, user = interaction.user)
        
        async def callback(self, interaction: Interaction):
            await interaction.response.send_modal(self.editTextModal(self.outer))
        
    class editColorButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Edit Color", emoji = "🎨")
            self.outer = outer
            
        class editColorView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__()
                self.outer = outer;
                
                options = ["Red", "Green", "Blue", "Yellow", "White", "Blurple", "Greyple", "Teal", "Purple", "Gold", "Magenta", "Fuchsia"]
                
                originalColor = getStringFromDiscordColor(self.outer.message.embeds[0].color)        
                selectOptions = []
                for option in options:
                    selectOptions.append(nextcord.SelectOption(label = option, value = option, default = (option == originalColor)))
                
                self.select = nextcord.ui.Select(placeholder = "Choose a color", options = selectOptions)
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.gray)
                self.backBtn.callback = self.backCallback

                self.button = nextcord.ui.Button(label = "Update Color", style = nextcord.ButtonStyle.blurple)
                self.button.callback = self.createCallback
                
                self.add_item(self.select)
                self.add_item(self.backBtn)
                self.add_item(self.button)
                
            async def setup(self, interaction: Interaction):
                description = f"""Choose what color you would like the embed to be:
                
                **Colors Available**
                Red, Green, Blue, Yellow, White
                Blurple, Greyple, Teal, Purple
                Gold, Magenta, Fuchsia"""
                
                
                # On Mobile, extra spaces cause problems. We'll get rid of them here:
                description = standardizeStrIndention(description)
    
                embed = nextcord.Embed(title = "Edit Color", description = description, color = nextcord.Color.yellow())
                await interaction.response.edit_message(embed = embed, view = self)
                    
            async def createCallback(self, interaction: Interaction):
                if self.select.values == []: return
                self.selection = self.select.values[0]
                self.stop()
                
                message = await interaction.channel.fetch_message(self.outer.message.id)
                await message.edit(embed = nextcord.Embed(title = message.embeds[0].title, description = message.embeds[0].description, color = (getDiscordColorFromString(self.selection))))
                await self.outer.setup(interaction)
       
            async def backCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
       
        async def callback(self, interaction: Interaction):
            await self.editColorView(self.outer).setup(interaction)
    
    class editPersistencyButton(nextcord.ui.Button):
        def __init__(self, outer, messageInfo: Message):
            if messageInfo.persistent:
                text = "Deprioritize"
                icon = "🔓"
            else:
                text = "Prioritize"
                icon = "🔒"
                
            super().__init__(label = text, emoji = icon)
            self.outer = outer
            self.messageID = messageInfo.message_id
        
        class warningView(nextcord.ui.View):
            def __init__(self, outer, guildID: int, messageID: int):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger) 
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
                self.continueBtn = self.continueButton(self.outer, guildID, messageID)
                self.add_item(self.continueBtn)
                
            async def setup(self, interaction: Interaction):
                embed = nextcord.Embed(title = "Edit Embed - Prioritize / Deprioritize", 
                                       description = "InfiniBot, similar to all free software, has its limitations. Regrettably, we are unable to continuously cache every embed ever created in our systems. Consequently, each server is allocated a maximum of 20 active (cached) embeds. As a result, there may come a point when this embed can no longer be edited.\n\n**What is Prioritizing?**\nPrioritizing ensures that this particular embed remains active indefinitely, enabling it to be edited well into the future. However, this comes at the expense of one of the server's active embed slots (20). This feature is particularly useful for embeds such as rules, onboarding information, and similar content.", 
                                       color = nextcord.Color.yellow())
                
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
        
            class continueButton(nextcord.ui.Button):
                def __init__(self, outer, guildID: int, messageID: int):
                    self.server = Server(guildID)
                    self.messageInfo = self.server.messages.get(messageID)
                    
                    if self.messageInfo.persistent:
                        text = "Deprioritize"
                    else:
                        text = "Prioritize"
                        
                    super().__init__(label = text, style = nextcord.ButtonStyle.blurple)
                    self.outer = outer
                    
                async def callback(self, interaction: Interaction):
                    self.messageInfo.persistent = not self.messageInfo.persistent
                    self.server.messages.save()
                    
                    await self.outer.setup(interaction)
        
        async def callback(self, interaction: Interaction):
            await self.warningView(self.outer, interaction.guild.id, self.messageID).setup(interaction)
   
class EditVote(nextcord.ui.View):
    def __init__(self, messageID: int):
        super().__init__(timeout = None)
        self.messageID = messageID
        
    async def loadButtons(self, interaction: Interaction):
        self.message = await interaction.channel.fetch_message(self.messageID)
        self.server = Server(interaction.guild.id)
        self.messageInfo = self.server.messages.get(self.messageID)
        
        self.clear_items()
        
        editTextBtn = self.editTextButton(self)
        self.add_item(editTextBtn)
        
        closeVoteBtn = self.closeVote(self, self.message.id)
        self.add_item(closeVoteBtn)
        
        editPersistencyBtn = self.editPersistencyButton(self, self.messageInfo)
        self.add_item(editPersistencyBtn)
        
    async def setup(self, interaction: Interaction):
        await self.loadButtons(interaction)
        
        mainEmbed = nextcord.Embed(title = "Edit Vote", description = "Edit the text of the following vote or close the vote.", color = nextcord.Color.yellow())
        editEmbed = self.message.embeds[0]
        embeds = [mainEmbed, editEmbed]
        try:
            await interaction.response.edit_message(embeds = embeds, view = self)
        except:
            await interaction.response.send_message(embeds = embeds, view = self, ephemeral = True)
  
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
        
    class closeVote(nextcord.ui.Button):
        def __init__(self, outer, messageID):
            super().__init__(label = "Close Vote", emoji = "🏁")
            self.outer = outer
            self.messageID = messageID
            
        class closeVoteView(nextcord.ui.View):
            def __init__(self, outer, messageID):
                super().__init__(timeout = None)
                self.outer = outer
                self.messageID = messageID
                
                self.backBtn = nextcord.ui.Button(label = "No", style = nextcord.ButtonStyle.danger) 
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
                self.continueBtn = self.continueButton(self, self.messageID)
                self.add_item(self.continueBtn)
                
            async def setup(self, interaction: Interaction):
                embed = nextcord.Embed(title = "Edit Vote - Close Vote",
                                       description = "Are you sure you want to close this vote? This will disable the vote forever and no one will be able to add, remove, or change results.",
                                       color = nextcord.Color.yellow())
                
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def disableAll(self, interaction: Interaction):
                embed = nextcord.Embed(title = "Vote Closed",
                                       description = "The vote was successfully closed.",
                                       color = nextcord.Color.green())
                
                await interaction.response.edit_message(embed = embed, view = None)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            class continueButton(nextcord.ui.Button):
                def __init__(self, outer, messageID: int):
                    super().__init__(label = "Yes", style = nextcord.ButtonStyle.green)
                    self.outer = outer
                    self.messageID = messageID
                    
                async def callback(self, interaction: Interaction):
                    message = await interaction.channel.fetch_message(self.messageID)
                    
                    # Finalize the embed ----------------------------------------------------------------
                    embed = nextcord.Embed(title = message.embeds[0].title,
                                           description = message.embeds[0].description,
                                           color = message.embeds[0].color)
                    # Get results
                    results = []
                    allReactions = message.reactions
                    for option in message.embeds[0].fields[0].value.splitlines():
                        parts = option.split(" ")
                        emoji = parts[0]
                        optionName = parts[1]
                        
                        optionCount = 0
                        for reaction in allReactions:
                            if reaction.emoji == emoji:
                                optionCount = reaction.count
                        
                        if optionCount == 0:
                            continue
                        
                        # Remove one because one of the reactions is InfiniBot's
                        optionCount -= 1
                        
                        results.append([optionName, optionCount])
                        
                    # Sort results
                    sortedResults = sorted(results, key=lambda x: (-x[1], x[0]))  
                    
                    # Create result interface
                    formattedResults = []
                    lastScore = 0
                    index = 0
                    for result in sortedResults:
                        if lastScore != result[1]:
                            index += 1;
                            
                        formattedResults.append("{}) {} — {} Vote{}".format(index, result[0], result[1], "s" if result[1] != 1 else ""))
                        lastScore = result[1]
                        
                    embed.add_field(name = "Final Results", value = "\n".join(formattedResults))
                    
                    # Edit the message ----------------------------------------------------------------
                    await message.edit(embed = embed)
                    await message.clear_reactions()
                    
                    # Remove the message from cache ----------------------------------------------------------------
                    server = Server(interaction.guild.id)
                    server.messages.delete(self.messageID)
                    server.messages.save()
                    
                    await self.outer.disableAll(interaction)
            
        async def callback(self, interaction: Interaction):
            await self.closeVoteView(self.outer, self.messageID).setup(interaction)
        
    class editPersistencyButton(nextcord.ui.Button):
        def __init__(self, outer, messageInfo: Message):
            if messageInfo.persistent:
                text = "Deprioritize"
                icon = "🔓"
            else:
                text = "Prioritize"
                icon = "🔒"
                
            super().__init__(label = text, emoji = icon)
            self.outer = outer
            self.messageID = messageInfo.message_id
        
        class warningView(nextcord.ui.View):
            def __init__(self, outer, guildID: int, messageID: int):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger) 
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
                self.continueBtn = self.continueButton(self.outer, guildID, messageID)
                self.add_item(self.continueBtn)
                
            async def setup(self, interaction: Interaction):
                embed = nextcord.Embed(title = "Edit Vote - Prioritize / Deprioritize", 
                                       description = "InfiniBot, similar to all free software, has its limitations. Regrettably, we are unable to continuously cache every vote ever created in our systems. Consequently, each server is allocated a maximum of 10 active (cached) votes. As a result, there may come a point when this vote can no longer be edited.\n\n**What is Prioritizing?**\nPrioritizing ensures that this particular vote remains active indefinitely, enabling it to be edited well into the future. However, this comes at the expense of one of the server's active vote slots (10). This feature is particularly useful for votes such as long-term poles and similar content.", 
                                       color = nextcord.Color.yellow())
                
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
        
            class continueButton(nextcord.ui.Button):
                def __init__(self, outer, guildID: int, messageID: int):
                    self.server = Server(guildID)
                    self.messageInfo = self.server.messages.get(messageID)
                    
                    if self.messageInfo.persistent:
                        text = "Deprioritize"
                    else:
                        text = "Prioritize"
                        
                    super().__init__(label = text, style = nextcord.ButtonStyle.blurple)
                    self.outer = outer
                    
                async def callback(self, interaction: Interaction):
                    self.messageInfo.persistent = not self.messageInfo.persistent
                    self.server.messages.save()
                    
                    await self.outer.setup(interaction)
        
        async def callback(self, interaction: Interaction):
            await self.warningView(self.outer, interaction.guild.id, self.messageID).setup(interaction)

class EditReactionRole(nextcord.ui.View):
    def __init__(self, messageID: int):
        super().__init__(timeout = None)
        self.messageID = messageID
        
    async def loadButtons(self, interaction: Interaction):
        self.message = await interaction.channel.fetch_message(self.messageID)
        self.server = Server(interaction.guild.id)
        self.messageInfo = self.server.messages.get(self.messageID)
        
        self.clear_items()
        
        editTextBtn = self.editTextButton(self)
        self.add_item(editTextBtn)
        
        editOptionsBtn = self.editOptionsButton(self, self.messageInfo)
        self.add_item(editOptionsBtn)
        
        editPersistencyBtn = self.editPersistencyButton(self, self.messageInfo)
        self.add_item(editPersistencyBtn)
        
    async def setup(self, interaction: Interaction):
        await self.loadButtons(interaction)
        
        mainEmbed = nextcord.Embed(title = "Edit Reaction Role", description = "Edit the following reaction role's text and options.", color = nextcord.Color.yellow())
        editEmbed = self.message.embeds[0]
        embeds = [mainEmbed, editEmbed]
        try:
            await interaction.response.edit_message(embeds = embeds, view = self)
        except:
            await interaction.response.send_message(embeds = embeds, view = self, ephemeral = True)
  
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
                                emoji = asci_to_emoji(firstLetter)
                                addedOptions_Asci.append(firstLetter)
                            else:
                                nextOpenLetter = getNextOpenLetter(firstLetter)
                                emoji = asci_to_emoji(nextOpenLetter)
                                addedOptions_Asci.append(nextOpenLetter)
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
                    
                    await SelectView("Edit Reaction Role - Edit Options - Add Role", "Add a Role to your Reaction Role.\n\n**Don't See Your Role?**\nMake sure InfiniBot has permission to assign it (higher role or administrator).", selectOptions, self.SelectViewCallback, continueButtonLabel = "Add Role", preserveOrder = True).setup(interaction)
                    
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
                    
                    await SelectView("Edit Reaction Role - Edit Options - Delete Role", "Delete a Role from your Reaction Role.", selectOptions, self.SelectViewCallback, continueButtonLabel = "Delete Role", preserveOrder = True).setup(interaction)
                    
                async def SelectViewCallback(self, interaction: Interaction, selection):
                    if selection == None: 
                        await self.outer.setup(interaction)
                        return
                    
                    await self.outer.addOrRemoveOption(interaction, None, None, index = int(selection))
                           
        async def callback(self, interaction: Interaction):
            await self.editOptionsView(self.outer, self.messageInfo).setup(interaction)
        
    class editPersistencyButton(nextcord.ui.Button):
        def __init__(self, outer, messageInfo: Message):
            if messageInfo.persistent:
                text = "Deprioritize"
                icon = "🔓"
            else:
                text = "Prioritize"
                icon = "🔒"
                
            super().__init__(label = text, emoji = icon)
            self.outer = outer
            self.messageID = messageInfo.message_id
        
        class warningView(nextcord.ui.View):
            def __init__(self, outer, guildID: int, messageID: int):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger) 
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
                self.continueBtn = self.continueButton(self.outer, guildID, messageID)
                self.add_item(self.continueBtn)
                
            async def setup(self, interaction: Interaction):
                embed = nextcord.Embed(title = "Edit Vote - Prioritize / Deprioritize", 
                                       description = "InfiniBot, similar to all free software, has its limitations. Regrettably, we are unable to continuously cache every reaction role ever created in our systems. Consequently, each server is allocated a maximum of 10 active (cached) reaction roles. As a result, there may come a point when this reaction role can no longer be edited.\n\n**What is Prioritizing?**\nPrioritizing ensures that this particular reaction role remains active indefinitely, enabling it to be edited well into the future. However, this comes at the expense of one of the server's active reaction role slots (10). This feature is particularly useful for reaction roles for server roles, verification roles, and similar content.", 
                                       color = nextcord.Color.yellow())
                
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
        
            class continueButton(nextcord.ui.Button):
                def __init__(self, outer, guildID: int, messageID: int):
                    self.server = Server(guildID)
                    self.messageInfo = self.server.messages.get(messageID)
                    
                    if self.messageInfo.persistent:
                        text = "Deprioritize"
                    else:
                        text = "Prioritize"
                        
                    super().__init__(label = text, style = nextcord.ButtonStyle.blurple)
                    self.outer = outer
                    
                async def callback(self, interaction: Interaction):
                    self.messageInfo.persistent = not self.messageInfo.persistent
                    self.server.messages.save()
                    
                    await self.outer.setup(interaction)
        
        async def callback(self, interaction: Interaction):
            await self.warningView(self.outer, interaction.guild.id, self.messageID).setup(interaction)


@bot.message_command(name = "Edit", dm_permission = False)
async def editMessageCommand(interaction: Interaction, message: nextcord.Message):
    #check to see if it's InfiniBot's message
    if message.author.id != bot.application_id:
        embed = nextcord.Embed(title = "This Action is not Supported", description = "This command only works on select messages by InfiniBot.", color = nextcord.Color.red())
        await interaction.response.send_message(embed = embed, ephemeral = True)
        return
    
    server = Server(interaction.guild.id);
    server.messages.initialize();
    messageInfo = server.messages.get(message.id);
    if messageInfo == None:
        embed = nextcord.Embed(title = "This Action is not Supported", description = "This command only works on select messages by InfiniBot that are still cached.\n\nFor future messages that support this feature, be sure to make them persistent if you want this feature forever.", color = nextcord.Color.red())
        await interaction.response.send_message(embed = embed, ephemeral = True)
        return
    
    if interaction.user != interaction.guild.owner and interaction.user.id != messageInfo.owner_id:
        embed = nextcord.Embed(title = "Permission Denied", description = "This command can only be used if you are the owner of the message and/or server.", color = nextcord.Color.red())
        await interaction.response.send_message(embed = embed, ephemeral = True)
        return
    
    # All checks have been completed. Let's begin sectioning off the actual code:
    if messageInfo.type == "Embed":
        await EditEmbed(message.id).setup(interaction)
    elif messageInfo.type == "Vote":
        await EditVote(message.id).setup(interaction)
    elif messageInfo.type == "Reaction Role":
        await EditReactionRole(message.id).setup(interaction)
#Editing Messages END: ----------------------------------------------------------------------------------------------------------------------------------------------------------------




#Other Features: -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
@bot.slash_command(name = "motivational_statement", description = "Get, uh, a motivational statement", dm_permission=False)
async def emotionalSupport(interaction: Interaction):
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

    embed = nextcord.Embed(title = "Motivational Statement", description = messages[random.randint(0, len(messages) - 1)], color =  nextcord.Color.blue())
    embed.set_footer(text = "Disclaimer: This is obviously not real motivational advice. For real advice, seek the help of a licenced professional.")

    await interaction.response.send_message(embed = embed)

@bot.slash_command(name = "change_nick", description = "Change the nickname of any user. (Requires a higher role, and manage nicknames permission)", dm_permission=False)
async def change_nick(interaction: Interaction, member: nextcord.Member, nickname: str = SlashOption(description = "List a nickname. \"CLEAR\" will clear an existing nickname.")):
    global nicknameChanged
    
    if not interaction.user.guild_permissions.manage_nicknames:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Permission Error", description = "You do not have the \"manage nicknames\" permission which is required to use this command.", color =  nextcord.Color.red()), ephemeral=True)
        return
    if interaction.user.top_role.position <= member.top_role.position and interaction.user.id != member.id and interaction.user.id != interaction.guild.owner.id:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Permission Error", description = f"You do not have a higher role than {member}.", color =  nextcord.Color.red()), ephemeral=True)
        return
    if not interaction.channel.permissions_for(interaction.guild.me).manage_nicknames:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Permission Error", description = "InfiniBot needs the Manage Nicknames permission for this action.", color =  nextcord.Color.red()), ephemeral=True)
        return
    
    if not interaction.guild_id in nicknameChanged:
        nicknameChanged.append(interaction.guild_id)
    
    beforeNick = member.nick
    
    try:
        if nickname != "CLEAR":
            await member.edit(nick = nickname)    
            await interaction.response.send_message(embed = nextcord.Embed(title = "Nickname Changed", description = f"{interaction.user} changed {member}'s nickname to {nickname}", color =  nextcord.Color.green()))
        else:
            await member.edit(nick = None)
            await interaction.response.send_message(embed = nextcord.Embed(title = "Nickname Changed", description = f"{interaction.user} cleared {member}'s nickname", color =  nextcord.Color.green()))
    
        should_log, channel = shouldLog(interaction.guild.id)
        if channel != None and should_log:
            embed = nextcord.Embed(title = "Nickname Changed", description = f"{interaction.user} changed {member}'s nickname.", color = nextcord.Color.blue())

            if beforeNick != None: embed.add_field(name = "Before", value = beforeNick, inline = True)
            else: embed.add_field(name = "Before", value = "None", inline = True)

            if member.nick != None: embed.add_field(name = "After", value = member.nick, inline = True)
            else: embed.add_field(name = "After", value = "None", inline = True)

            await channel.send(embed = embed)
    
    
    
    except:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Permission Error", description = "Infinibot does not have a high enough role to do this for you.", color =  nextcord.Color.red()), ephemeral=True)


    await asyncio.sleep(1)
    if interaction.guild.id in nicknameChanged:
        nicknameChanged.pop(nicknameChanged.index(interaction.guild.id))

@set.subcommand(name = "default_role", description = "Set a default role that will be given to anyone who joins the server. (Requires Infinibot Mod)")
async def defaultRole(interaction: Interaction, role: nextcord.Role = SlashOption(description = "Leave blank to disable this feature.", required=False)):
    if await hasRole(interaction):
        if role != None:
            botMember: nextcord.Member = await interaction.guild.fetch_member(bot.application_id)
            if role.position >= botMember.top_role.position:
                infinibotRole = interaction.guild.get_role(getInfinibotTopRoleId(interaction.guild))
                await interaction.response.send_message(embed = nextcord.Embed(title = "Infinibot cannot grant this permission", description = f"{role.mention} is equal to or above the role {infinibotRole.mention}. Therefore, it cannot grant the role to any member.", color = nextcord.Color.red()), ephemeral=True)
                return
        
        server = Server(interaction.guild.id)
        if role != None: server.defaultRoles = role
        else: server.defaultRoles = []
        server.saveData()
        
        if role != None: await interaction.response.send_message(embed = nextcord.Embed(title = "Default Role Set", description = f"Any member who joins this server will get the role {role.mention}.\nAction done by {interaction.user}", color = nextcord.Color.green()))
        else: await interaction.response.send_message(embed = nextcord.Embed(title = "Default Role Disabled", description = f"Any member who joins this server will not recieve any role automatically by Infinibot\nAction done by {interaction.user}.", color = nextcord.Color.green()))

@create.subcommand(name = "embed", description = "Create a beautiful embed!")
async def createEmbed(interaction: Interaction, role: nextcord.Role = SlashOption(description = "Role to Ping", required = False)):
    #handle the pinging
    content = ""
    if role != None:
        if interaction.guild.me.guild_permissions.mention_everyone or role.mentionable:
            content = role.mention
        else:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Can't Ping that Role", description = "InfiniBot can't ping that role. Either *allow anyone to @mention this role*, or give InfiniBot permission to *mention @everyone, @here, and All Roles*.", color = nextcord.Color.red()), ephemeral = True)
            return
        
    #create the modal
    modal = EmbedModal()
    await interaction.response.send_modal(modal)
    await modal.wait()
    
    embedTitle = modal.titleValue
    embedDescription = modal.descriptionValue
    
    #now we get the color
    def icon(levelRequirement, level):
        if level >= levelRequirement:
            return "✅"
        return "❌"

    description = f"""Choose what color you would like the embed to be:
    
    **Colors Available**
    Red, Green, Blue, Yellow, White
    Blurple, Greyple, Teal, Purple
    Gold, Magenta, Fuchsia"""
    
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    
    
    embed = nextcord.Embed(title = "Choose a Color", description = description, color = nextcord.Color.blue())
    view = EmbedColorView()
    
    await interaction.followup.send(embed = embed, view = view, ephemeral=True)
    
    await view.wait()
    
    color = view.selection
    
    
    #now, we have to process the color into something that our code can read:
    discordColor = getDiscordColorFromString(color)
    
    #noway, we just displ the embed!
    embed = nextcord.Embed(title = embedTitle, description = embedDescription, color = discordColor)
    interaction_response = await interaction.followup.send(content = content, embed = embed, wait = True)
    
    #finally, add the embed to our active messages for future editing
    server = Server(interaction.guild.id);
    server.messages.add("Embed", interaction.channel.id, interaction_response.id, interaction.user.id)
    server.messages.save()
#Other Features END: ------------------------------------------------------------------------------------------------------------------------------------------------------------------




#Submitting Stuff: ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@bot.slash_command(name = "report_issue", description = "Report an issue", dm_permission=False)
async def reportIssue(interaction: Interaction):
    issueReportModal = IssueReportModal(interaction.user)
    await interaction.response.send_modal(issueReportModal)
    
@bot.slash_command(name = "submit_idea", description = "Submit an idea for a future update!", dm_permission=False)
async def submitIdea(interaction: Interaction):
    ideaReportModal = IdeaReportModal(interaction.user)
    await interaction.response.send_modal(ideaReportModal)
#Submitting Stuff END: -----------------------------------------------------------------------------------------------------------------------------------------------------------------------





#Help: --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@bot.slash_command(name = "help", description = "Help with the InfiniBot.")
async def help(interaction: Interaction):
    description = f"""For help with InfiniBot, use one of the following commands:
    
    • /help profanity_moderation
    • /help spam_moderation
    • /help voting
    • /help reaction_roles
    • /help join_and_leave_messages
    • /help birthdays
    • /help logging
    • /help leveling
    • /help infinibot_mod
    • /help join_to_create_vcs
    • /help stats
    • /help auto_bans
    • /help other
    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "Help", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral=True, view = SupportAndInviteView())

@help.subcommand(name = "moderation_profanity", description = "Help with the Admin Channel, Strikes, Infinibot Mod, Flagged/Profane Words, and more.")
async def profanityModerationHelp(interaction: Interaction):
    description = f"""Out of the box, profanity moderation is *mostly* set up. The only thing left to do is to set up the \"Admin Channel\". To do this, go to `/dashboard → Moderation → Profanity → Admin Channel` and select a secure channel that only admins can see.
    
    **What is the Admin Channel?**
        • Whenever a member says a flagged word, their message will be automatically deleted, and they will recieve a strike. All strikes will be reported to the Admin Channel where admins can look over the strike and decide whether it was legitimate.
        • In this channel, you can mark any strikes as incorrect, and the member who recieved the strike will have it refunded. In addition, you will be able to see the original message that was automatically deleted.
            → Note: Make sure the channel has application commands enabled and InfiniBot has access to it!
        
    **What happens when you get a strike?**
        • One strike on its own is not dangerous. However, they can build up. Once you reach the server's __maximum strikes__ (to find, go to `/dashboard → Moderation → Profanity`), you will be timed out for the server's __timeout duration__ (to find, go to `/dashboard → Moderation → Profanity`).
        • Once you serve your timeout, you will be back at 0 strikes.
    
        • In some servers, another way to clear strikes is by waiting. Once the \"strike expire time\" has passed (to find, go to `/dashboard → Moderation → Profanity`), you will be refunded one strike.
    
    **It says I need Infinibot Mod?**
        • Some features are locked down so that only admins can use them. If you are an admin, go ahead and assign yourself the role Infinibot Mod (which should have been automatically created by InfiniBot). Once you have this role, you will have full access to InfiniBot and its features.
    
    **How do I add/delete a flagged/Profane word?**
        • Go to `/dashboard → Moderation → Profanity → Filtered Words`. In here, you can add, delete, and view all the words InfiniBot will filter.
            → Note: InfiniBot will also listen for variations of these words.
        
    **Don't want it?**
        • Don't think profanity moderation is what your server needs? That's fine! You can turn it off by going to `/dashboard → Enable/Disable Features → Profanity Moderation`, and selecting "Disable"
    
    **Extra Commands**
        • `/view_strikes` allows you to see another member's strikes. (This works without Infinibot Mod)
        • `/my_strikes` allows you to see your own strikes. (This works without Infinibot Mod)
        • `/dashboard → Moderation → Profanity` allows you to configure specific features in Profanity Moderation.
        • `/dashboard → Moderation → Profanity → Manage Members` allows you to view and configure strikes.
    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "How profanity moderation works with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())
    
@help.subcommand(name = "moderation_spam", description = "Help with spam moderation")
async def spamModerationHelp(interaction: Interaction):
    description = f"""Out of the box, spam moderation is all set up! However, you can configure it for your needs!
    
    **Settings**
        • You can adjust certain features to better fit your server. Here's how:
            → Go to `/dashboard → Moderation → Spam`
            → You can configure the timeout duration of the penalty when a member spams too much (Click on Timeout Duration)
            → You can also configure the messages threshold (the number of messages until the member recieves a timeout). (Click on Messages Threshold)
    
    **Don't want it?**
        • Don't think you need spam moderation? That's fine! You can turn it off by going to `/dashboard → Enable/Disable Features → Spam Moderation`, and selecting "Disable"
    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "How spam moderation works with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())
    
#@help.subcommand(name = "music", description = "Help with playing music")
async def musicHelp(interaction: Interaction):
    description = f"""InfiniBot contains a built-in music feature! Go ahead and give it a try!
    
    **How to use it**
        1) First, join any voice channel that InfiniBot can access.
        2) Go to any text channel that allows application commands (and that InfiniBot can access) and type `/play [music]`
        3) InfiniBot should join your voice channel and start playing music!
            → Note: If InfiniBot is already playing music somewhere else on the server, your song will be added to the queue, and InfiniBot will come to that channel once it is your time.
        
    **What's the queue?**
        • If two or more songs are requested, InfiniBot will start up a queue. Once one song ends, the next song will begin. You can skip a song by typing `/skip`, or stop the bot by typing `/stop` or `/leave`.
    
    **What can I play?**
        • InfiniBot is capable of searching YouTube for any song that you like. Type `/play` and describe your song as if you were looking it up. You can search via words or a YouTube url.
            → Note: InfiniBot *cannot* play livestreams, playlists, or anything like that.
    
    **Don't want it?**
        • Running a server that doesn't need Music? That's fine! You can turn it off by going to `/dashboard → Enable/Disable Features → Music`, and selecting "Disable"
    
    **Extra Commands**
        • `/pause` will pause the song and queue.
        • `/resume` will resume the song and queue.
        • `/clear` will clear the queue, but the current song will keep playing
        • `/queue` will let you see what's playing, and what's coming up next.
        • `/volume` will let you set the volume server-wide (remember that you can always do this for yourself by right-clicking on InfiniBot, and changing the User Volume)
        • `/loop` will let you loop your favorite song and not have to type the command for it over and over.
       
    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """

    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    
    embed = nextcord.Embed(title = "How to use music with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())  

@help.subcommand(name = "voting", description = "Help with creating votes")
async def votingHelp(interaction: Interaction):
    description = f"""Voting has always been hard in Discord. InfiniBot makes it less painful.
    
    **How to use it**
        • Type `/create vote` and select either "Letters" or "Numbers". Your choice will be the symbols for the votes.
        • Now, run the command, and you should see a window pop up. Fill in the title, description, and the options.
            → Tip: Remember that the options must be formatted with a comma and a space in between (ex: ", ").
        • Finally, click Submit.
    
    **What did it do?**
        • If all went well, it should have created a couple of reactions that others can react to.
        • If these reactions did NOT appear, check InfiniBot's permissions and make sure that it can add reactions (check the channel permissions too!)
        
    **What do the letters mean?**
        • If you chose "Letters" when creating the vote, each option will be the first letter of every choice (if the letter was already used, it will default to "A", then "B", etc.)
    
    **Custom Votes**
        • Custom votes are a little trickier, but you can customize the reactions. Here's how to do it.
        • Type `/create custom_vote` and in the options format it like this: "Emoji = Option, Emoji = Option, Emoji = Option, etc"
             → example: "😄 = Yes, 😢 = No"
        • From there, run the command, and choose the Title and Description.
        
    **Edit Votes**
        • To edit your vote, right click on the message, and go to `Apps → Edit → Edit Text`. Here you can edit the text of your vote
        
    **Close Votes**
        • To close your vote, right click on the message, and go to `Apps → Edit → Close Vote`. This will disable your vote and finalize the results.
        
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "How to use InfiniBot to help you create votes!", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())

@help.subcommand(name = "reaction_roles", description = "Help with creating reaction roles")
async def reactionRolesHelp(interaction: Interaction):
    description = f"""Set up reaction roles to allow members to give themselves roles!
    
    **How to use it**
        • Type `/create reaction_role` and select either "Letters" or "Numbers". Your choice will be the symbols for the reactions.
        • Now, run the command, and you should see a window pop up. Fill in the title and description.
        • Click Submit, and you should see a new message with a dropdown box. Go ahead and select all the roles you would like the reaction role to give.
        • Finally, click Create, and you should see your reaction role come to life!
    
    **What did it do?**
        • If all went well, it should have created a couple of reactions that others can react to.
        • If these reactions did NOT appear, check InfiniBot's permissions and make sure that it can add reactions (check the channel permissions too!)
        
    **What do the letters mean?**
        • If you chose "Letters" when creating the reaction role, each option will be the first letter of every choice (if the letter was already used, it will default to "A", then "B", etc.)
        
    **Whenever I react to one, my reaction is taken away. Why?**
        • If you react to one of the reactions, you should be given the corresponding role. Then, your reaction will be removed via the bot. If you would like to get rid of this role, just react to that same letter again, and that role will be removed from you.
    
    **I didn't get the role. Why?**
        • If you reacted for the role but did not recieve the role, there could be a couple of reasons:
            1) The role you are wanting is equal to or higher than InfiniBot's highest role, so it cannot grant this role to you.
            2) InfiniBot does not have permission to manage roles. Go ahead and give InfiniBot this permission and see if things work for you.
        • If these don't fix the problem, submit a question / issue at {supportServerLink}.
        
    **Custom Reaction Roles**
        • Custom reaction roles are a little trickier, but you can customize the reactions. Here's how to do it.
        • Type `/create custom_reaction_role` and in the options format it like this: "Emoji = @role, Emoji = @role, Emoji = @role, etc"
            → example: "👍 = @Member, 🥸 = @Gamer"
        • From there, run the command, and choose the Title and Description.
            → Note: The role select menu will not show seeing how you already selected the roles when you declared the emojis.
            
    **Edit Reaction Roles**
        • To edit your reaction role, right click, and go to `Apps → Edit`. From here, you can edit the text and options of the reaction role.
        
    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "How to set up reaction roles with InfiniBot!", description = description, color = nextcord.Color.greyple())
    
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView()) 

@help.subcommand(name = "join_and_leave_messages", description = "Help with join / leave messages")
async def joinLeaveMessagesHelp(interaction: Interaction):
    description = f"""Want to greet your members? Go ahead and set up join / leave messages!
    
    **How to set a join / leave message**
        • Go to `/dashboard → Join / Leave Messages`. In here, select either "Join Message" or "Leave Message" and write your message! If you want to reference the member who joined, include "[member]" in your message.
        • After running this command, InfiniBot will greet and say farewell to members however you would like!
        
    **Don't want it?**
        • Don't need this feature? That's fine! You can turn it off by going to `/dashboard → Join / Leave Messages` and editing the "Join Message" and "Leave Message" to be blank.
    
    **Extra Commands**
        • `/dashboard → Join / Leave Messages → Join Message Channel` allows you to configure where the join message will be sent.
        • `/dashboard → Join / Leave Messages → Leave Message Channel` allows you to configure where the leave message will be sent.
       
    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "How to set up join and leave messages with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())  

@help.subcommand(name = "birthdays", description = "Help with birthdays")
async def birthdaysHelp(interaction: Interaction):
    description = f"""Never forget a birthday again and let InfiniBot do all the work!
    
    **How to add a birthday**
        • Go to `/dashboard → Birthdays → Add` and choose the member, click next, and then enter the date of thier birthday. This MUST be formatted as month, day, year (MM/DD/YYYY).
        • If you know it, you can even include thier real name!
        • Now, on thier birthday at 8:00 AM MDT, they will be wished a happy birthday on the server and via a dm!
        
    **Editing and Deleting**
        • You can go to `/dashboard → Birthdays` and use both "Edit" and "Delete" incase you made a mistake, or don't want InfiniBot to celebrate their birthday anymore.
        
    **Extra Commands**
        • `/dashboard → Birthdays → Delete All` will delete all the birthdays in the server.
    
    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "How to set up birthdays with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())  

@help.subcommand(name = "logging", description = "Help with logging.")
async def loggingHelp(interaction: Interaction):
    description = f"""Ever find it annoying how members can edit or delete thier message and leave you with no proof? With logging enabled, you will never have to worry about this again.
    
    **What is the Log Channel?**
        • Whenever a log is created, it has to go somewhere! Creating a private channel specifically for logs is highly encouraged. Go to `/dashboard → Logging → Log Channel` and choose a channel to automatically be used for logging.
            → Note: Make sure the channel has application commands enabled and InfiniBot has access to it!
            → Tip: Go ahead and turn notifications to "Nothing" for this channel, as it will constently be logging.
    
    **What will it log?**
        • InfiniBot will log the following:
            → Deleted Messages
            → Edited Messages
            → Nickname Changes
            → Role Changes
            → Kicks
            → Bans
        
    **There is a *slight* limitation**
        • Discord has a slight limitation regarding deleted messages. Therefore, in some senarios, the logs may not include the actual message, and/or author/deleter. By clicking "More Information", more information will be presented about the specific situation.
        
    **Don't want it?**
        • Don't feel like logging suits your needs? That's fine! You can turn it off by going to `/dashboard → Enable/Disable Features → Logging`, and selecting "Disable"

    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "How logging works with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())

@help.subcommand(name = "leveling", description = "Help with leveling and level rewards.")
async def levelingHelp(interaction: Interaction):
    description = f"""Enjoy a leveling system for your members and keep your server active!
    
    By default, everything is already set up for leveling! Whenever members type in text channels, InfiniBot will give them points to level up. But, even though this is cool, you can do more with it!
    
    **Set up Level Rewards**
        • Create specific roles for once members reach a certain level. For example, you could create a member-plus role with the ability to add custom emojis to the server, and you could use that as a level reward. Here's how to set that up:
        • Go to `/dashboard → Leveling → Level Rewards → Create` and select the role you would like to assign. Then, choose a level. Now, once members reach that level, they can get that role, but if they loose that level, they will loose the role.
            → Tip: Don't choose too high of a level. Levels are calculated via the equation 0.1x^0.65, so each level will make the next harder and harder to get to.
            → Warning: If you link a role to a level reward, anyone who does not meet that level will have that role automatically taken from them once thier level updates, so be careful.
    
    **How are points given?**
        • Points are given via every character in a message. The longer the message, the more points. However, you can't spam a long message, as InfiniBot will check to make sure that the message is not spamed.
        • Levels are calculed by 0.1x^0.65, so it's exponential. In English, the more levels you have, the harder it is to get to the next one.
        
    **How do I loose points?**
        • Every day at midnight MDT, every member will loose a certain amount of points from thier score. This is not thier levels, but thier points. Overtime, this can add up and it can take your levels, so be careful!
        • The amount of points lost per day can be changed via `/dashboard → Leveling → Points Lost Per Day`. The default is 2 per day.
        
    **Don't want it?**
        • Think that it doesn't work for you? That's fine! You can turn it off by going to `/dashboard → Enable/Disable Features → Leveling`, and selecting "Disable"
        
    **Extra Commands**
        • `/leaderboard` allows you to see where you rank with the rest of the server.
        • `/set level` allows you to set the level of any member on the server via a slash command (you can also do this within the dashboard).
        • `/set score` allows you to set the score of any member on the server via a slash command (you can also do this within the dashboard).
        • `/dashboard → Leveling → Leveling Channel` lets you set a channel to be the announcement place for level ups / level rewards.
        • `/dashboard → Leveling → Level Up Message` allows you to change what message will be sent when someone levels up.
        • `/view levels [level]` lets you calculate the score requirement for each level.
        • `/dashboard → Leveling → Manage Members → Reset` will set everyone in the server back to level 0.
    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "Set up leveling with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())

@help.subcommand(name = "other", description = "Help with other features.")
async def otherHelp(interaction: Interaction):
    description = f"""InfiniBot has a lot of useful features, but some were a bit miscellaneous. Below are those features.
    
    **Purging Channels**
        • To purge a channel, type `/purge [all]` and the whole channel should be deleted
            → Note: for big channels, `/purge [all]` is much more efficient than deleting messages one with the following option.
        • Another way to purge a channel is to use `/dashboard [100]` and InfiniBot will purge the channel of 100 messages.
            → Tip: You can use any number — 100 was an example.
    
    **Motivational Statement**
        • Type `/motivational_statement` and get, uh, a motivational statement — if you squint.
        
    **Change Nickname**
        • Type`/change_nick [member] [new nickname]` and be able to change a member's nickname via a command.
            → Tip: For bigger servers, it might not be worth your time to scroll though the members list. Therefore, you can use a command instead.
        
    **Default Roles**
        • A default roles are roles that will be given to anyone who joins the server. To set this up, go to `/dashboard → Default Roles` and choose up to 5 roles. Now, any time a member joins the server, they will be greeted with those roles.
       
    **Delete Invites**
        • If you are managing a large server and don't want people advertising thier servers, you can enable this feature. Go to `/dashboard → Enable / Disable Features → Delete Invites` and select "Enable". InfiniBot will now delete any message that includes an invite.
            → Note: If you have the permission "Administrator", you are immune to this.
        
    **Check InfiniBot's Permissions**
        • It's always a good idea to check InfiniBot's permissions to make sure that it has everything it needs. To do this, simply use `/check_infinibot_permissions` and give InfiniBot the permissions it wants.
        
    **DM Commands**
        • If you feel like your dm from InfiniBot is getting a little cluttered, there's a simple fix to that!
        • Typing `del` in InfiniBot's dm channel will have InfiniBot delete the last message it sent to you.
        • Typing `clear` in InfiniBot's dm will have InfiniBot delete all the messages it sent to you.
        • You can also opt in and out of dm notifications using `/opt_into_dms` and `/opt_out_of_dms`.
    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "Other commands with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView()) 

@help.subcommand(name = "infinibot_mod", description = "Help with Infinibot Mod.")
async def infinibotMod(interaction: Interaction):
    description = f"""**It says I need Infinibot Mod?**
        • Some features are locked down so that only admins can use them. If you are an admin, go ahead and assign yourself the role Infinibot Mod (which should have been automatically created by InfiniBot). Once you have this role, you will have full access to InfiniBot and its features.
    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "InfiniBot Mod", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView()) 

@help.subcommand(name = "join_to_create_vcs", description = "Help with Join To Create Voice Channels")
async def joinToCreateVoiceChannelsHelp(interaction: Interaction):
    description = f"""Want to have a voice channel for everyone in the server but not feel cluttered? Join To Create Voice Channels are the way to go.
    
    **How to set up a Join-To-Create Voice Channel**
        • Go to `/dashboard → Join-To-Create VCs → Configure → Add`.  
        • Select your channel and click "Add".
            → Tip: Don't see your voice channel? Check to make sure that InfiniBot has the permissions to view it.
        
    **What did it do?**
        • Now, you can join that voice channel, and it will move you to a new voice channel with your name on it! Once everyone leaves, the channel will be deleted.
    
    **Disable this feature on a voice channel**
        • To disable this feature on any voice channel, go to `/dashboard → Join-To-Create VCs → Configure → Delete` and select the voice channel.
        • Click "Delete"
       
    
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "How to set up join-to-create vcs with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())  
    
@help.subcommand(name = "stats", description = "Help with Server Statistics messages")
async def statsHelp(interaction: Interaction):
    description = f"""Want to know how many people are in your server? Use server statistics to always keep track.
    
    **How to set up a Server Statistics message**
        • Use `/setup_stats` in the channel where you want to have the Statistics message.
            → Tip: Every time a member joins or leaves the server, this message will update.
        
    **Why can't I create another?**
        • Because these are updated constantly, InfiniBot currently can only keep track of one. Therefore, you can only have one of these messages. If you want to move the message, just run the command somewhere else (although it will deactivate the first message).
           
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "How to set up statistics messages with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())  
       
@help.subcommand(name = "auto_bans", description = "Help with Auto Bans")
async def autoBansHelp(interaction: Interaction):
    description = f"""Banning is a powerful tool, however, Discord limits you in some cases. With InfiniBot, you can ban members even before and after they join your server.  
        
    **How to Auto-Ban a Member (Never Joined your Server)**
        ★ Make sure InfiniBot has the "Ban Members" permission.
        • Go to `/dashboard → Auto-Bans → Add` and follow the instructions.
        • Once you finish, they will be auto-banned the second they join this server.   
        
    **How to Revoke an Auto-Ban**
        ★ Make sure InfiniBot has the "Ban Members" permission.
        • Go to `/dashboard → Auto-Bans → Revoke` and select any member to revoke their auto-ban.
        • Click "Revoke Auto-Ban"
        
    **How to Ban a Member (still in the server or after they have left)**
        ★ Make sure both you and InfiniBot have the "Ban Members" permission.
        • Right click on the member or message, select "Apps", and click ether "Ban Member" or "Ban Message Author".
        • Click "Yes, ban" on the message that will appear.
        • The member is now banned from this server.
    
           
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "How to set up auto-bans with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView()) 
   
@help.subcommand(name = "embeds", description = "Help with Embeds")
async def embedsHelp(interaction: Interaction):
    description = f"""Discord's default messages *can* look really good. But sometimes, the default message just doesn't cut it. For that, use embeds!
        
    **How to Create an Embed**
        • Type `/create embed` and choose your title, text, and color.
        
    **How to Edit an Embed**
        • Go to the embed, and right click. Go to `Apps → Edit`
        • From here, you can edit the embed's title, description, and color
         
    For more help, join us at {supportServerLink} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardizeStrIndention(description)
    
    embed = nextcord.Embed(title = "How to use embeds with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView()) 
    
 
#Help END: ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------






@bot.slash_command("admin", guild_ids = developmentGuild)
async def admin(interaction: Interaction):
    pass

@admin.subcommand(name = "send_message_to_all_guilds", description = "Only usable by bot owner.")
async def sendMessageToAllGuilds(interaction: Interaction):
    modal = AdminModal()
    await interaction.response.send_modal(modal)
    
    await modal.wait()
    
    title = modal.titleValue
    description = modal.descriptionValue
    
    
    if interaction.user.id in developerID:

        embed = nextcord.Embed(title = title, description = description, color = nextcord.Color.gold())

        for guild in bot.guilds:
            try:
                # If the server wants updates
                server = Server(guild.id)
                if not server.getUpdates:
                    continue
                
                # Find a channel
                general = nextcord.utils.find(lambda x: x.name == 'general',  guild.text_channels)
                if general: await general.send(embed = embed, view = SupportAndInviteView())
                else: 
                    channel = await getChannel(guild)
                    if channel != None: 
                        # Send message
                        await channel.send(embed = embed, view = SupportAndInviteView())
                print(f"Message sent to server: {guild.name}, id: {guild.id}")
                
                # Do some special stuff if it's the InfiniBot server
                if guild.id == infinibotGuild:
                    channel = guild.get_channel(updatesChannel)
                    role = guild.get_role(infinibotUpdatesRole)
                    await channel.send(content = role.mention, embed = embed, view = SupportAndInviteView())
                    print(f"Message sent to InfiniBot Server Updates Area")
                        
                
            except:
                await sendErrorMessageToOwner(guild, "Send Messages")
                continue

        await interaction.followup.send(embeds = [nextcord.Embed(title = "Success", description = "Message was sent to all guilds. The message is attached below."), embed])



    else:
        await interaction.followup.send(embed = nextcord.Embed(title = "User Error", description = "You do not have access to this command", color = nextcord.Color.red()), ephemeral = True)

@admin.subcommand(name = "get_all_guilds", description = "Only usable by bot owner.")
async def getAllGuilds(interaction: Interaction):
    await interaction.response.defer()
    
    membercount = 0
    if interaction.user.id in developerID:

        formattedGuilds = ""
        number = 1
        for guild in bot.guilds:
            server = Server(guild.id)
            bots = len(guild.bots)
            formattedGuilds += f"{number}) Name: {guild.name}, ID: {guild.id}, Member Count: `{guild.member_count}`, Bot Count: `{bots}`\n"
            del server
            
            number += 1
            membercount += guild.member_count
            
        maxChar = 4000
        formattedGuilds = [formattedGuilds[i:i+maxChar] for i in range(0, len(formattedGuilds), maxChar)]
        for x in formattedGuilds:
            embed = nextcord.Embed(title = "Guilds:", description = x, color = nextcord.Color.gold())
            await interaction.followup.send(embed = embed)

    else:
        await interaction.followup.send(embed = nextcord.Embed(title = "User Error", description = "You do not have access to this command", color = nextcord.Color.red()), ephemeral = True)
        
async def adminCommands(message: nextcord.Message):
    global guildsCheckingForRole, purging
    messageContent = message.content.lower()
    messageContentList = messageContent.split(" ")
    
    
    #get admins
    with open("./RequiredFiles/AdminIDS.txt", "r") as file:
        admins = file.read().split("\n")
        
    allAdmins = []
    levelOneAdmins = [] #others whom I trust
    levelTwoAdmins = [] #support staff
    levelThreeAdmins = [] #total control
    
    for admin in admins:
        if admin == "": continue
        parts = admin.split("|||")
        id = int(parts[0])
        level = int(parts[1])
        allAdmins.append([id, level])
        if level == 1:
            levelOneAdmins.append(id)
        if level == 2:
            levelOneAdmins.append(id)
            levelTwoAdmins.append(id)
        if level == 3:
            levelOneAdmins.append(id)
            levelTwoAdmins.append(id)
            levelThreeAdmins.append(id)
        
    #commands
    
    # Level 1 ----------------------------------------------------------------------
    
    if messageContent == "-help" and message.author.id in levelOneAdmins: #-help
        description = """
        ### **Level 1**
        • `-stats`: display InfiniBot satistics
        
        ### **Level 2**
        • `-info`: display info about a server or owner of a server that uses InfiniBot
        • `-resetServerConfigurations`: reset a server's configurations and set them back to default
        • `-checkActiveMessages`: check a server's active messages to make sure that they all exist
        • `-InfiniBotModHelp`: give a help message to those who need help with InfiniBotMod
        
        ### **Level 3**
        • `-refresh`: refresh InfiniBot
        • `-restart`: restart InfiniBot
        • `-addAdmin`: add an admin
        • `-editAdmin`: edit an admin
        • `-deleteAdmin`: delete an admin"""
        
        # On Mobile, extra spaces cause problems. We'll get rid of them here:
        description = standardizeStrIndention(description)
        
        embed = nextcord.Embed(title = "Help Commands for Admins", description = description, color = nextcord.Color.blue())
        await message.channel.send(embed = embed)
    
    if messageContent == "-stats" and message.author.id in levelOneAdmins: #-stats
        membercount = 0
        servercount = 0
        
        print(f"Guilds requested by: {message.author}")
        for guild in bot.guilds:
            servercount += 1
            membercount += guild.member_count

        embed = nextcord.Embed(title = "Server Stats:", description = f"Server Count: {str(servercount)}\nTotal Members: {str(membercount)}\n\n*A watched pot never boils*", color = nextcord.Color.blue())
        await message.channel.send(embed = embed, view = TopGGVoteView())
        return
        
    # Level 2 ----------------------------------------------------------------------
        
    if messageContentList[0] == "-info" and message.author.id in levelTwoAdmins:
        if not (len(messageContentList) > 1 and messageContentList[1].isdigit()):
            embed = nextcord.Embed(title = "Incorrect Format", description = f"Format like this: `-info [serverID or ownerID]`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return
        
        id = int(messageContentList[1])
        
        #test server ids and owner ids simultaniously:
        guilds:list[nextcord.Guild] = []
        for _guild in bot.guilds:
            if _guild.id == id or _guild.owner.id == id:
                #add it
                guilds.append(_guild)
                
        if len(guilds) == 0:
            embed = nextcord.Embed(title = "Server or Owner Could Not Be Found", description = "Make sure you are formatting correctly: `-info [serverID or ownerID]`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return
                
        #we should have them all. We now need to display them:
        for guild in guilds:
            server = Server(guild.id)
            description = f"""Owner: {guild.owner} ({guild.owner.id})
            Members: {len(guild.members)}
            Bots: {len(guild.bots)}
            
            **Configurations:**
            {server.rawData}"""
            
            # On Mobile, extra spaces cause problems. We'll get rid of them here:
            description = standardizeStrIndention(description)
            
            embed = nextcord.Embed(title = f"Server: {guild.name} ({guild.id})", description = description, color = nextcord.Color.blue())
            await message.channel.send(embed = embed)
            print(f"{message.author} requested info about the server {guild.name} ({guild.id})")
            
    if messageContentList[0] == "-resetserverconfigurations" and message.author.id in levelTwoAdmins:
        if not (len(messageContentList) > 1 and messageContentList[1].isdigit()):
            embed = nextcord.Embed(title = "Incorrect Format", description = f"Format like this: `-resetserverconfigurations [serverID]`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return
        
        id = int(messageContentList[1])
        
        #test server id
        server = Server(id)
                
        if server.guild == None:
            embed = nextcord.Embed(title = "Server Could Not Be Found", description = "Make sure you are formatting correctly: `-resetserverconfigurations [serverID]`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return
                
        #we should have it. Now we just need to delete the server.
        server.deleteServer()
        
        #display it
        embed = nextcord.Embed(title = "Server Configurations Reset", description = f"The configurations for the server {server.guild.name} ({server.guild.id}) have been reset to defaults.", color = nextcord.Color.green())
        await message.channel.send(embed = embed)
        print(f"{message.author} reset configurations in the server {guild.name} ({guild.id})")
        
    if messageContentList[0] == "-checkactivemessages" and message.author.id in levelTwoAdmins:
        if not (len(messageContentList) > 1 and messageContentList[1].isdigit()):
            embed = nextcord.Embed(title = "Incorrect Format", description = f"Format like this: `-checkActiveMessages [serverID]`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return
        
        id = int(messageContentList[1])
        
        #test server id
        server = Server(id)
                
        if server.guild == None:
            embed = nextcord.Embed(title = "Server Could Not Be Found", description = "Make sure you are formatting correctly: `-checkActiveMessages [serverID]`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return
                
        #we should have it. Now we just need to check the active messages
        await server.messages.checkAll()
        server.messages.save()
        
        #display it
        embed = nextcord.Embed(title = "Server Active Messages Checked", description = f"The active messages for the server {server.guild.name} ({server.guild.id}) have been checked. All active messages exist.", color = nextcord.Color.green())
        await message.channel.send(embed = embed)
        print(f"{message.author} checked active messages in the server {server.guild.name} ({server.guild.id})")
            
    #server help commands
    if messageContent == "-infinibotmodhelp" and message.author.id in levelTwoAdmins:
        description = f"""**It says I need Infinibot Mod?**
        • Some features are locked down so that only admins can use them. If you are an admin, go ahead and assign yourself the role Infinibot Mod (which should have been automatically created by InfiniBot). Once you have this role, you will have full access to InfiniBot and its features.
        
        • If this role does not appear, try one of these two things:
            → Make sure that InfiniBot has the Manage Roles permission
            → Create a role named "Infinibot Mod" (exact same spelling) with no permissions"""
            
        # On Mobile, extra spaces cause problems. We'll get rid of them here:
        description = standardizeStrIndention(description)
        
        await message.channel.send(embed = nextcord.Embed(title = "InfiniBot Mod Help", description = description, color = nextcord.Color.blurple()))
     
    # Level 3 ----------------------------------------------------------------------   
    
    if messageContent == "-refresh" and message.author.id in levelThreeAdmins: #-reset
        guildsCheckingForRole = []
        purging = []

        embed = nextcord.Embed(title = "Infinibot Refreshed", description = "GuildsCheckingForRole and Purging has been reset.", color = nextcord.Color.green())
        await message.channel.send(embed = embed)
        print(f"{message.author} refeshed InfiniBot")
        
    if messageContent == "-restart" and message.author.id in levelThreeAdmins:
        embed = nextcord.Embed(title = "InfiniBot Restarting", description = "InfiniBot is restarting.", color = nextcord.Color.green())
        await message.channel.send(embed = embed)
        
        print(f"{message.author} requested InfiniBot to be restarted. Restarting...")
        
        main.login_response_guildID = message.guild.id
        main.login_response_channelID = message.channel.id
        main.savePersistentData()
        
        python = sys.executable
        os.execl(python, python, * sys.argv)   
        
    if messageContentList[0] == "-addadmin" and message.author.id in levelThreeAdmins: #-addAdmin
        if len(messageContentList) > 2 and messageContentList[1].isdigit() and messageContentList[2].isdigit():
            userID = messageContentList[1]
            userLevel = int(messageContentList[2])
            if 0 < userLevel <= 3: #if level is within 1-3
                if not int(userID) in [admin[0] for admin in allAdmins]:
                    #everything is correct
                    with open("./RequiredFiles/AdminIDS.txt", "a") as file:
                        file.write(f"\n{userID}|||{userLevel}")
                        
                    embed = nextcord.Embed(title = "Admin Added", description = f"\"{userID}\" added as an admin (level {userLevel})", color = nextcord.Color.green())
                    await message.channel.send(embed = embed)
                    return 
                else:
                    embed = nextcord.Embed(title = "Already Admin", description = f"\"{userID}\" is already an admin.", color = nextcord.Color.red())
                    await message.channel.send(embed = embed)
                    return 
            else:
                embed = nextcord.Embed(title = "Incorrect Level", description = f"Level can only be between 1 and 3.", color = nextcord.Color.red())
                await message.channel.send(embed = embed)
                return 
        else:
            embed = nextcord.Embed(title = "Incorrect Format", description = f"Format like this: `-addAdmin 12345678912345689 [1-3]`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return

    if messageContentList[0] == "-editadmin" and message.author.id in levelThreeAdmins: #-editAdmin
        if len(messageContentList) > 2 and messageContentList[1].isdigit() and messageContentList[2].isdigit():
            userID = int(messageContentList[1])
            userLevel = int(messageContentList[2])
            if 0 < userLevel <= 3: #if level is within 1-3
                if userID in [admin[0] for admin in allAdmins]:
                    #everything is correct
                    with open("./RequiredFiles/AdminIDS.txt", "r") as file:
                        admins = file.read().split("\n")
                    
                    changed = False
                    for admin in admins:
                        parts = admin.split("|||")
                        id = int(parts[0])
                        if id == userID:
                            #we need to change the level
                            admins[admins.index(admin)] = f"{id}|||{userLevel}"
                            changed = True
                            break
                    
                    if not changed:
                        embed = nextcord.Embed(title = "Error", description = f"The admin was not edited for some reason.", color = nextcord.Color.red())
                        await message.channel.send(embed = embed)
                        return 
                    
                    with open("./RequiredFiles/AdminIDS.txt", "w") as file:
                        file.write("\n".join(admins))
                         
                    embed = nextcord.Embed(title = "Admin Edited", description = f"\"{userID}\" was edited to be of level {userLevel}", color = nextcord.Color.green())
                    await message.channel.send(embed = embed)
                    return 
                else:
                    embed = nextcord.Embed(title = "Not Admin", description = f"\"{userID}\" is not an admin.", color = nextcord.Color.red())
                    await message.channel.send(embed = embed)
                    return 
            else:
                embed = nextcord.Embed(title = "Incorrect Level", description = f"Level can only be between 1 and 3.", color = nextcord.Color.red())
                await message.channel.send(embed = embed)
                return 
        else:
            embed = nextcord.Embed(title = "Incorrect Format", description = f"Format like this: `-editAdmin 12345678912345689 [1-3]`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return

    if messageContentList[0] == "-deleteadmin" and message.author.id in levelThreeAdmins: #-deleteAdmin
        if len(messageContentList) > 1 and messageContentList[1].isdigit():
            userID = int(messageContentList[1])
            if userID in [admin[0] for admin in allAdmins]:
                #everything is correct
                with open("./RequiredFiles/AdminIDS.txt", "r") as file:
                    admins = file.read().split("\n")
                
                changed = False
                newAdmins = []
                for admin in admins:
                    parts = admin.split("|||")
                    id = int(parts[0])
                    if id == userID:
                        #we need to delete this admin.
                        #We do this by not adding it to the new Admins.
                        changed = True
                    else:
                        newAdmins.append(admin)
                
                if not changed:
                    embed = nextcord.Embed(title = "Error", description = f"The admin was not deleted for some reason.", color = nextcord.Color.red())
                    await message.channel.send(embed = embed)
                    return 
                
                with open("./RequiredFiles/AdminIDS.txt", "w") as file:
                    file.write("\n".join(newAdmins))
                        
                embed = nextcord.Embed(title = "Admin Deleted", description = f"\"{userID}\" was deleted as an admin.", color = nextcord.Color.green())
                await message.channel.send(embed = embed)
                return 
            else:
                embed = nextcord.Embed(title = "Not Admin", description = f"\"{userID}\" is not an admin.", color = nextcord.Color.red())
                await message.channel.send(embed = embed)
                return 
        else:
            embed = nextcord.Embed(title = "Incorrect Format", description = f"Format like this: `-deleteAdmin 12345678912345689`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return


















token = ""
with open("./RequiredFiles/TOKEN.txt", "r") as file:
    token = file.read().split("\n")[0]
    
    
bot.run(token)


#Infinibot: https://discord.com/api/oauth2/authorize?client_id=991832387015159911&permissions=8&scope=bot%20applications.commands

#Infinibot Testing: https://discord.com/api/oauth2/authorize?client_id=1005942420476796958&permissions=8&scope=bot%20applications.commands
#Infinibot Testing TopGG Invite: https://discord.com/api/oauth2/authorize?client_id=1005942420476796958&permissions=242736287296&scope=bot
