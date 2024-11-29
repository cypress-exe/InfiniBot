from nextcord import AuditLogAction, Interaction, SlashOption
from nextcord.ext import commands
#from youtube_dl import YoutubeDL
# from yt_dlp import YoutubeDL
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
import copy

from custom_types import MISSING

from dashboard import Dashboard
from ui_components import SelectView, disabled_feature_override
from utils import standardize_dict_properties, standardize_str_indention, get_discord_color_from_string, get_string_from_discord_color
from global_settings import global_kill_status



# ----------------------------------------------------------- VERSION OF INFINIBOT---------------------------------------------------------

VERSION = 2.0

# ------------------------------------------------------------------------------------------------------------------------------------------






# IDs
dev_guilds = []
dev_ids = []
infinibot_guild_id = None
issue_report_channel_id = None
submission_channel_id = None
updates_channel_id = None
infinibot_updates_role_id = None

# Links
support_server_link = 'https://discord.gg/mWgJJ8ZqwR'
topgg_link = "https://top.gg/bot/991832387015159911"
topgg_vote_link = "https://top.gg/bot/991832387015159911/vote"
topgg_review_link = "https://top.gg/bot/991832387015159911#reviews"
invite_link = "https://discord.com/oauth2/authorize?client_id=991832387015159911&permissions=1374809222364&scope=bot"

# Global Variables
auto_deleted_message_time = None
nickname_changed = []
required_permissions = """
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


# LOAD IDS ==============================================================================================================================================================
def load_ids():
    global dev_guilds, dev_ids, infinibot_guild_id, issue_report_channel_id, submission_channel_id, updates_channel_id, infinibot_updates_role_id
    
    ids_file = None
    
    with open("./generated/configure/special_channel_ids.json") as file:
        ids_file = file.read()    

    json_file = json.loads(ids_file)
    
    dev_guilds = json_file["dev_guilds"]
    dev_ids = json_file["dev_ids"]
    infinibot_guild_id = json_file["infinibot_guild_id"]
    issue_report_channel_id = json_file["issue_report_channel_id"]
    submission_channel_id = json_file["submission_channel_id"]
    updates_channel_id = json_file["updates_channel_id"]
    infinibot_updates_role_id = json_file["infinibot_updates_role_id"]

load_ids()



# Server, Profile, and Dashboard general functions
class Strike:
    """TYPE Strike → Moderation Strikes → contains the member (nextcord.Member), member_id (int), strike (int), and last_strike (time → str).
    
    For initalization, either include the package, or call `setup`."""
    def __init__(self, guild: nextcord.Guild, package: str):
        if package:
            self.data = package.split("|||")
            self.guild = guild
            self.member: nextcord.Member = self.guild.get_member(int(self.data[0]))
            self.member_id: int = int(self.data[0])
            self.strike: int = int(self.data[1])
            self.last_strike: str = (self.data[2])
        else:
            self.data = None
            self.guild = guild
            self.member = None
            self.member_id = None
            self.strike = None
            self.last_strike = None
        
    def setup(self, member_id: int, strike: int, last_strike = None):
        self.member_id = int(member_id)
        self.member: nextcord.Member = self.guild.get_member(self.member_id)
        self.strike = int(strike)
        self.last_strike = (last_strike if last_strike else datetime.date.today())
    
    def set_strike(self, new_strike):
        self.strike = int(new_strike)
        self.last_strike = datetime.date.today()
        self.__format_strikes()
        
    def change_strike(self, quantity):
        self.strike = int(self.strike + quantity)
        self.last_strike = datetime.date.today()
        self.__format_strikes()
        
    def __format_strikes(self):
        if self.strike < 0: self.strike = 0.

class Birthday:
    '''TYPE Birthday → Birthdays → contains the member (nextcord.Member), member_id (int), date (time → str), and real_name (str | None)'''
    def __init__(self, guild: nextcord.Guild, package: str):
        self.data = package.split("|||")
        self.member: nextcord.Member = guild.get_member(int(self.data[0]))
        self.member_id = int(self.data[0])
        self.date: str = self.data[1]
        if len(self.data) == 3:
            self.real_name = self.data[2]
        else:
            self.real_name = None

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
        
        self.active = True
        '''Refers to whether or not InfiniBot has the correct permissions in the voice channel.'''
        
        #check Permissions
        if not (self.channel.permissions_for(guild.me).view_channel and self.channel.permissions_for(guild.me).connect and self.channel.permissions_for(guild.me).manage_channels):
            self.active = False

class StatsMessage:
    '''TYPE StatsMessage → Stats Message → contains the message_id(int | None), channel_id(int | None), and link (str | None).'''
    def __init__(self, guild: nextcord.Guild, package: typing.Union[str, None]):
        if package != None and package != None:
            self.data = package.split("/")
            self.guild = guild
            self.channel_id: int = int(self.data[0])
            self.message_id: int = int(self.data[1])
            self.link = f"https://discord.com/channels/{self.guild.id}/{self.channel_id}/{self.message_id}"
            self.active = True
        else:
            self.guild = guild
            self.channel_id = None
            self.message_id = None
            self.link = None
            self.active = False
        
    async def checkMessage(self):
        '''Finds the message and determins whether it exists.'''
        if self.channel_id == None or self.message_id == None:
            self.setValue(None)
            return False, None
        
        try:
            channel: nextcord.TextChannel = await self.guild.fetch_channel(self.channel_id)
            if channel is None: 
                self.setValue(None)
                return False, None
            
            message: nextcord.Message = await channel.fetch_message(self.message_id)
            if message is None: 
                self.setValue(None)
                return False, None
            
            return True, message
        except nextcord.NotFound:
            return False, None
    
    def setValue(self, message: nextcord.Message):
        '''Updates all values to reflect the attribute message'''
        if message == None:
            self.channel_id = None
            self.message_id = None
            self.link = None
            self.active = False
            return
        
        self.channel_id: int = message.channel.id
        self.message_id: int = message.id
        self.link = f"https://discord.com/channels/{self.guild.id}/{self.channel_id}/{self.message_id}"
    
    def saveValue(self):
        '''Returns how this variable should be saved.'''
        if self.channel_id == None or self.message_id == None:
            return None
        
        return str(self.channel_id) + "/" + str(self.message_id)

class Level:
    '''TYPE LEVEL → Leveling Level → contains the member (nextcord.Member), member_id (int), and score (int)'''
    def __init__(self, guild: nextcord.Guild, package: str):
        self.data = package.split("|||")
        self.member: nextcord.Member = guild.get_member(int(self.data[0]))
        self.member_id = int(self.data[0])
        self.score = int(self.data[1])
        
class LevelReward:
    '''TYPE Strike → Leveling Level Reward → contains the role (nextcord.Role), role_id (int), and level (int)'''
    def __init__(self, guild: nextcord.Guild, package: str):
        self.data = package.split("|||")
        self.role: nextcord.Role = guild.get_role(int(self.data[0]))
        self.role_id = int(self.data[0])
        self.level = int(self.data[1])

class AutoBan:
    '''TYPE AUTO-BAN → Auto-Bans → contains the member_name (str) and member_id (int)'''
    def __init__(self, package: str):
        self.data = package.split("|||")
        self.member_name: str = self.data[0]
        self.member_id = int(self.data[1])
        
    def saveValue(self):
        return f"{self.member_name}|||{self.member_id}"


class Levels:
    '''Manages Leveling System. Capable of loading and saving a member's levels and loading and saving level rewards. Should be instantiated through the class Server'''
    def __init__(self, guild: nextcord.Guild):
        self.guild = guild
        self.guild_id = str(guild.id)
        
        # Populate self.all_members
        need_to_save = False
        self.all_members: list[Level] = []
        for level in self.__getLevels():
            level_class = Level(self.guild, level)
            if True or level_class.member != None: self.all_members.append(level_class) # Disabled due to issue with InfiniBot restarting
            else: need_to_save = True
            
        if need_to_save: self.saveLevels()
        
        
        # Get rid of members with a level of 0
        need_to_save = False
        _allMembers = []
        for member in self.all_members:
            if member.score != 0: _allMembers.append(member) #if their score isn't 0, add them to the list
            if member.score == 0: need_to_save = True
                
        self.all_members = _allMembers
        if need_to_save: self.saveLevels()
        
        # Populate self.level_rewards
        need_to_save = False
        self.level_rewards: list[LevelReward] = []
        for level_reward in self.__getLevelRewards():
            levelRewardClass = LevelReward(self.guild, level_reward)
            if levelRewardClass.role != None: self.level_rewards.append(levelRewardClass)
            else: need_to_save = True

        if need_to_save: self.saveLevelRewards()
 
    def __getLevels(self):
        '''Returns a list each member's level (type LEVEL). Will add server if needed. Members with a level of 0 will be ommitted.'''
        all_levels = fileOperations.getAllLevels()

        for server in all_levels:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        newLevels = fileOperations.addServerToList(self.guild_id, all_levels, None)
        fileOperations.saveLevels(newLevels)

        return []

    def saveLevels(self):
        '''Saves any level changes made to this class.'''
        # Remove all unneccessary members (score 0)
        for member in list(self.all_members):
            if member.score <= 0: 
                self.all_members.remove(member)
        
        # Format
        levels_list = []
        for level in self.all_members:
            levels_list.append(str(level.member_id) + "|||" + str(level.score))

        levels_string = fileOperations.joinWithHyphens(levels_list)

        # Save
        all_levels = fileOperations.getAllLevels()
        all_levels = fileOperations.editServerInList(self.guild_id, all_levels, levels_string)
        fileOperations.saveLevels(all_levels)

    def memberExists(self, member_id):
        '''Returns a BOOL whether a member has a recorded level.'''
        member_id = int(member_id)
        for level in self.all_members:
            if level.member_id == member_id:
                return True

        return False

    def addMember(self, member_id, score = 0):
        '''Adds a member to leveling system with a default score of 0* (returns True). Supports when the member already exists (returns False).'''
        member_id = int(member_id)
        if self.memberExists(member_id): return False

        self.all_members.append(Level(self.guild, f"{str(member_id)}|||{str(score)}"))

        return True

    def getMember(self, member_id):
        '''Retrieves a member's level. Returns type LEVEL'''
        member_id = int(member_id)
        if self.memberExists(member_id):
            for level in self.all_members:
                if level.member_id == int(member_id):
                    return level
        else:
            # Create a temporary level for them to use.
            self.addMember(member_id)
            return self.getMember(member_id)

    def deleteMember(self, member_id):
        '''Delets a member from leveling system (returns True). Supports when the member doesn't exist (returns False).'''
        member_id = int(member_id)
        if self.memberExists(member_id):
            for level in self.all_members:
                if level.member_id == member_id:
                    self.all_members.pop(self.all_members.index(level))
                    return True
            
        return False


    def __getLevelRewards(self):
        '''Returns a list each level reward (type LEVELREWARD). Will add server if needed.'''
        all_level_rewards = fileOperations.getAllLevelRewards()

        for server in all_level_rewards:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        new_level_rewards = fileOperations.addServerToList(self.guild_id, all_level_rewards, None)
        fileOperations.saveLevelRewards(new_level_rewards)

        return []

    def saveLevelRewards(self):
        '''Saves any level reward changes made to this class.'''
        level_rewards_list = []
        for level_reward in self.level_rewards:
            level_rewards_list.append(str(level_reward.role.id) + "|||" + str(level_reward.level))

        level_reward_string = fileOperations.joinWithHyphens(level_rewards_list)
        all_level_rewards = fileOperations.getAllLevelRewards()

        list = fileOperations.editServerInList(self.guild_id, all_level_rewards, level_reward_string)

        fileOperations.saveLevelRewards(list)

    def levelRewardExists(self, role_id):
        '''Returns a BOOL whether a role has an associated level reward.'''
        for level_reward in self.level_rewards:
            if level_reward.role_id == role_id:
                return True

        return False

    def addLevelReward(self, role_id, level):
        '''Adds a level reward to leveling system (returns True). Supports when the level reward already exists (returns False).'''
        if self.levelRewardExists(role_id): return False

        self.level_rewards.append(LevelReward(self.guild, f"{str(role_id)}|||{str(level)}"))

        return True

    def getLevelReward(self, roleID):
        '''Retrieves a level reward. Returns type LEVELREWARD or NONE'''
        if self.levelRewardExists(roleID):
            for level_reward in self.level_rewards:
                if level_reward.role_id == int(roleID):
                    return level_reward

        else:
            return None

    def deleteLevelReward(self, roleID):
        '''Delets a level reward from leveling system (returns True). Supports when the level reward doesn't exist (returns False).'''
        if self.levelRewardExists(roleID):
            for level_reward in self.level_rewards:
                if level_reward.role_id == int(roleID):
                    self.level_rewards.pop(self.level_rewards.index(level_reward))
                    break
            
            return True
        else:
            return False

class Server_DEP:
    '''Main Infrastructure. Requires a guild_id, and you can access/save any saved data.'''
    def __init__(self, guild_id):
        self.guild_id = str(guild_id)

        self.guild = None

        for guild in bot.guilds:
            if guild.id == int(guild_id):
                self.guild = guild

        if self.guild != None:
            self.raw_data = self.__getData()
            self.profane_words = self.__getProfaneWords()
            self.__rawStrikes = self.__getStrikes()
            self.__rawBirthdays = self.__getBirthdays()
            self.__rawVCs = self.__getVCs()
            self.__rawBans = self.__getAutoBans()
        

            #handle data
            
            def loadChannel(channel):
                if channel == None: return None
                if channel == False: return False
                return bot.get_channel(channel)
            
            def loadChannels(channels):
                return [loadChannel(channel) for channel in channels if channel != None]
            
            def defaultRoles():
                result = []
                for role_id in self.raw_data['defaultRoles']:
                    role = self.guild.get_role(int(role_id))
                    if role != None: result.append(role)
                
                return result
            
            #KeyError
            self.version = float(self.raw_data['version'])
            self.profanity_moderation_enabled = self.raw_data['active']['profanityModeration']
            self.spam_moderation_enabled = self.raw_data['active']['spamModeration']
            self.logging_enabled = self.raw_data['active']['logging']
            self.leveling_enabled = self.raw_data['active']['leveling']
            self.delete_invites_enabled = self.raw_data['active']['deleteInvites']
            self.get_updates_enabled = self.raw_data['active']['getUpdates']
            
            self.admin_channel = loadChannel(self.raw_data['channels']['admin'])
            self.log_channel = loadChannel(self.raw_data['channels']['log'])
            self.join_channel = loadChannel(self.raw_data['channels']['join'])
            self.leave_channel = loadChannel(self.raw_data['channels']['leave'])
            self.leveling_channel = loadChannel(self.raw_data['channels']['leveling'])
            self.leveling_exempt_channels = loadChannels(self.raw_data['channels']['levelingExempt'])
            self.birthday_channel = loadChannel(self.raw_data['channels']['birthdays'])
            
            self.max_strikes = self.raw_data['moderation']['maxStrikes']
            self.profanity_timeout_time = self.raw_data['moderation']['profanityTimeoutTime']
            self.strike_expire_time = self.raw_data['moderation']['strikeExpireTime']
            self.spam_timeout_time = self.raw_data['moderation']['spamTimeoutTime']
            self.messages_threshold = self.raw_data['moderation']['messagesThreshold']
            
            self.join_message = self.raw_data['eventMessages']['joinMessage']
            self.leave_message = self.raw_data['eventMessages']['leaveMessage']
            
            self.points_lost_per_day = self.raw_data['leveling']['pointsLostPerDay']
            self.leveling_message = self.raw_data['leveling']['levelingMessage']
            
            self.allow_level_cards_bool = self.raw_data['allowCards']['level']
            self.allow_join_cards_bool = self.raw_data['allowCards']['join']
            
            self.default_roles = defaultRoles()
            self.stats_message = StatsMessage(self.guild, self.raw_data['statsMessage'])

            #handle strikes 
            self.strikes: list[Strike] = [Strike(self.guild, strike) for strike in self.__rawStrikes]

            #handle birthdays
            self.birthdays: list[Birthday] = [Birthday(self.guild, birthday) for birthday in self.__rawBirthdays]
            #self.birthdays = [birthday for birthday in self.birthdays if birthday != None and birthday.member != None] # Disabled due to issue with InfiniBot restarting
            #self.birthdays = sorted(self.birthdays, key = lambda x: (x.member.display_name))
            
            #handle levels
            self.levels = Levels(self.guild)
            
            #handle join-to-create-vcs
            self.VCs: list[JoinToCreateVC] = [JoinToCreateVC(self.guild, vc) for vc in self.__rawVCs if self.guild.get_channel(int(vc)) != None]
            
            #handle bans
            self.auto_bans: list[AutoBan] = [AutoBan(ban) for ban in self.__rawBans]
            self.auto_bans = sorted(self.auto_bans, key = lambda x: (x.member_name))
        
        #handle messages
        self.messages = Messages(self.guild_id)
        '''Not automatically initialized. Will be auto-initalized upon any changes.'''
        
        if self.guild == None:
            return None;

        
    def setAdminChannelID(self, id):
        '''Sets the Admin Channel via an ID instead of a channel. Returns TRUE if successful, or FALSE if Forbidden.'''
        try:
            self.admin_channel = bot.get_channel(int(id))
            return True
        except nextcord.errors.Forbidden:
            return False
        
    def setLogChannelID(self, id):
        '''Sets the Log Channel via an ID instead of a channel. Returns TRUE if successful, or FALSE if Forbidden.'''
        try:
            self.log_channel = bot.get_channel(int(id))
            return True
        except nextcord.errors.Forbidden:
            return False

    def setLevelingChannelID(self, id: (str | int)):
        '''Sets the Leveling Channel via an ID instead of a channel. Returns TRUE if successful, or FALSE if Forbidden.'''
        if type(id) != bool and id != None:
            try:
                self.leveling_channel = bot.get_channel(int(id))
                return True
            except nextcord.errors.Forbidden:
                return False
        else:
            self.leveling_channel = id
            return True
        
    def setJoinChannelID(self, id: (str | int)):
        '''Sets the Join Channel via an ID instead of a channel. Returns TRUE if successful, or FALSE if Forbidden.'''
        if type(id) != bool and id != None:
            try:
                self.join_channel = bot.get_channel(int(id))
                return True
            except nextcord.errors.Forbidden:
                return False
        else:
            self.join_channel = id
            return True
        
    def setLeaveChannelID(self, id: (str | int)):
        '''Sets the Leave Channel via an ID instead of a channel. Returns TRUE if successful, or FALSE if Forbidden.'''
        if type(id) != bool and id != None:
            try:
                self.leave_channel = bot.get_channel(int(id))
                return True
            except nextcord.errors.Forbidden:
                return False
        else:
            self.leave_channel = id
            return True
        
    def setBirthdayChannelID(self, id: (str | int)):
        '''Sets the Birthday Channel via an ID instead of a channel. Returns TRUE if successful, or FALSE if Forbidden.'''
        if type(id) != bool and id != None:
            try:
                self.birthday_channel = bot.get_channel(int(id))
                return True
            except nextcord.errors.Forbidden:
                return False
        else:
            self.birthday_channel = id
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
        self.messages.deleteAllAndSave()
    
   
         
    def __getData(self):
        '''Returns list of data.'''
        all_data = fileOperations.getAllData()
        
        # Backwards-Compatibility Translations
        aliases = {
            "banInvites": "deleteInvites"
        }
        
        for server in all_data:
            if server.split("———")[0] == self.guild_id:
                data: dict = json.loads(server.split("———")[1])        
                
                return standardize_dict_properties(fileOperations.DATADEFAULT, data, aliases = aliases)

        new_data = fileOperations.addServerToList(self.guild_id, all_data, json.dumps(fileOperations.DATADEFAULT))
        fileOperations.saveData(new_data)

        return fileOperations.DATADEFAULT

    def saveData(self):
        '''Saves any changes to Data made to this class'''
        
        def formatChannel(channel: nextcord.TextChannel):
            if channel == None: return None
            if channel == False: return False
            return channel.id
        
        def formatChannelList(channels):
            return [formatChannel(channel) for channel in channels]
        
        def formatDefaultRoles():
            return [role.id for role in self.default_roles]
            
        #be sure to change this in fileOperations.__init__() and server.__getData()
        dataRaw = {
            'version' : VERSION,
            'active': {
                'profanityModeration': self.profanity_moderation_enabled,
                'spamModeration': self.spam_moderation_enabled,
                'logging': self.logging_enabled,
                'leveling': self.leveling_enabled,
                'deleteInvites': self.delete_invites_enabled,
                'getUpdates': self.get_updates_enabled
            },
            'channels': {
                'admin': formatChannel(self.admin_channel),
                'log': formatChannel(self.log_channel),
                'join': formatChannel(self.join_channel),
                'leave': formatChannel(self.leave_channel),
                'leveling': formatChannel(self.leveling_channel),
                'levelingExempt': formatChannelList(self.leveling_exempt_channels),
                'birthdays': formatChannel(self.birthday_channel)
            },
            'moderation': {
                'maxStrikes': int(self.max_strikes),
                'profanityTimeoutTime': self.profanity_timeout_time,
                'strikeExpireTime': int(self.strike_expire_time),
                'spamTimeoutTime': self.spam_timeout_time,
                'messagesThreshold': int(self.messages_threshold)
            },
            'eventMessages': {
                'joinMessage': self.join_message,
                'leaveMessage': self.leave_message
            },
            'leveling': {
                'pointsLostPerDay': self.points_lost_per_day,
                'levelingMessage': self.leveling_message
            },
            'allowCards': {
                'level': self.allow_level_cards_bool,
                'join': self.allow_join_cards_bool
            },
            'defaultRoles': formatDefaultRoles(),
            'statsMessage': self.stats_message.saveValue()
        }
        
        #formatting data
        dataJson = json.dumps(dataRaw)
        allData = fileOperations.getAllData()

        list = fileOperations.editServerInList(self.guild_id, allData, dataJson)
        fileOperations.saveData(list)

    def deleteDataAndSave(self):
        '''Deletes any data files from server'''
        all_data = fileOperations.getAllData()

        list = fileOperations.deleteServerFromList(self.guild_id, all_data)

        fileOperations.saveData(list) 




    def __getProfaneWords(self):
        '''Returns list of Profane words.'''
        all_profane_words = fileOperations.getAllProfaneWords()

        for server in all_profane_words:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]
            
            
        #if it doesn't exist yet...
        new_profane_words = fileOperations.addServerToList(self.guild_id, all_profane_words, fileOperations.getDefaultProfaneWords())
        fileOperations.saveProfaneWords(new_profane_words)

        _returnInfo = fileOperations.getDefaultProfaneWords().split("———")
        return _returnInfo

    def saveProfaneWords(self):
        '''Saves any changes to Profane Words made to this class'''
        profane_words = self.profane_words
        all_profane_words = fileOperations.getAllProfaneWords()

        list = fileOperations.editServerInList(self.guild_id, all_profane_words, fileOperations.joinWithHyphens(profane_words))

        fileOperations.saveProfaneWords(list)

    def profaneWordExists(self, word):
        '''Returns bool if profane word exists on this server.'''
        for profane_word in self.profane_words:
            if profane_word == word:
                return True
        
        return False

    def addProfaneWord(self, word):
        '''Adds a profane word to this server (returns True). If it already existed, returns False.'''
        if self.profaneWordExists(word): return False
        
        self.profane_words.append(word)
        return True

    def deleteProfaneWord(self, word):
        '''Deletes a profane word from server (returns True). If Profane word didn't exist on this server, returns False.'''
        if self.profaneWordExists(word):
           self.profane_words.pop(self.profane_words.index(word)) 
           return True
        else:
            return False

    def deleteProfaneWordsAndSave(self):
        '''Deletes any Profane Words files from server'''
        all_profane_words = fileOperations.getAllProfaneWords()

        list = fileOperations.deleteServerFromList(self.guild_id, all_profane_words)

        fileOperations.saveProfaneWords(list) 





    def __getStrikes(self):
        '''Returns list of Strikes.'''
        all_strikes = fileOperations.getAllStrikes()

        for server in all_strikes:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        new_strikes = fileOperations.addServerToList(self.guild_id, all_strikes, None)
        fileOperations.saveStrikes(new_strikes)
        return []

    def saveStrikes(self):
        '''Saves any changes to Strikes made to this class'''
        # Remove any any records where strike = 0 and save to new format.
        strikes_list = []
        for strike in self.strikes:
            if strike.strike == 0: continue
            strikes_list.append(str(strike.member_id) + "|||" + str(strike.strike) + "|||" + str(strike.last_strike))

        strikes_string = fileOperations.joinWithHyphens(strikes_list)
        all_birthdays = fileOperations.getAllStrikes()

        list = fileOperations.editServerInList(self.guild_id, all_birthdays, strikes_string)

        fileOperations.saveStrikes(list)

    def strikeExists(self, member_id):
        '''Returns bool if member's strike exists on this server.'''
        for strike in self.strikes:
            if strike.member_id == int(member_id):
                return True

        return False

    def getStrike(self, member_id):
        '''Returns type STRIKE of a member'''
        if self.strikeExists(member_id):
            for strike in self.strikes:
                try:
                    if strike.member_id == int(member_id): return strike
                except Exception as e:
                    print("getStrike Exeption: " + str(e))
                    continue

        else:
            # Create a temporary strike for them to use.
            self.addStrike(member_id, 0)
            return self.getStrike(member_id)

    def addStrike(self, member_id, strike: int):
        '''Adds a member's strike to this server (returns True). If it already existed, returns False.'''
        if self.strikeExists(member_id): return False

        strike_object = Strike(self.guild, package = None)
        strike_object.setup(member_id = member_id, strike = strike)
        self.strikes.append(strike_object)
        return True

    def deleteStrike(self, memberID):
        '''Deletes a member's strike from server (returns True). If strike didn't exist for this member, returns False.'''
        if self.strikeExists(memberID):
            for strike in self.strikes:
                if strike.member_id == int(memberID):
                    self.strikes.pop(self.strikes.index(strike))
                    break
            return True

        else:
            return False

    def deleteStrikesAndSave(self):
        '''Deletes any Strike files from server'''
        all_strikes = fileOperations.getAllStrikes()

        list = fileOperations.deleteServerFromList(self.guild_id, all_strikes)

        fileOperations.saveStrikes(list) 






    def __getBirthdays(self):
        '''Returns list of Birthdays.'''
        all_birthdays = fileOperations.getAllBirthdays()

        for server in all_birthdays:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        new_birthdays = fileOperations.addServerToList(self.guild_id, all_birthdays, None)
        fileOperations.saveBirthdays(new_birthdays)

        return []

    def saveBirthdays(self):
        '''Saves any changes to Birthdays made to this class'''
        birthdays_list = []
        for birthday in self.birthdays:
            if birthday.real_name != None: 
                birthdays_list.append(str(birthday.member_id) + "|||" + birthday.date + "|||" + birthday.real_name)
            else: birthdays_list.append(str(birthday.member_id) + "|||" + birthday.date)

        birthdays_string = fileOperations.joinWithHyphens(birthdays_list)
        all_birthdays = fileOperations.getAllBirthdays()

        list = fileOperations.editServerInList(self.guild_id, all_birthdays, birthdays_string)

        fileOperations.saveBirthdays(list)

    def birthdayExists(self, member_id):
        '''Returns bool if member's birthday exists on this server.'''
        member_id = int(member_id)
        for birthday in self.birthdays:
            if birthday.member_id == member_id:
                return True

        return False

    def getBirthday(self, member_id):
        '''Returns type BIRTHDAY or NONE of a member'''
        member_id = int(member_id)
        if self.birthdayExists(member_id):
            for birthday in self.birthdays:
                if birthday.member_id == int(member_id):
                    return birthday

        else:
            return None

    def addBirthday(self, member_id, date, real_name = None):
        '''Adds a member's birthday to this server (returns True). If it already existed, returns False.'''
        if self.birthdayExists(member_id): return False

        if real_name != None: self.birthdays.append(Birthday(self.guild, f"{str(member_id)}|||{date}|||{real_name}"))
        else: self.birthdays.append(Birthday(self.guild, f"{str(member_id)}|||{date}"))

        return True

    def deleteBirthday(self, member_id):
        '''Deletes a member's birthday from server (returns True). If birthday didn't exist for this member, returns False.'''
        if self.birthdayExists(member_id):
            for birthday in self.birthdays:
                if birthday.member_id == int(member_id):
                    self.birthdays.pop(self.birthdays.index(birthday))
                    break
            
            return True
        else:
            return False

    def deleteBirthdaysAndSave(self):
        '''Deletes any Birthday files from server'''
        all_birthdays = fileOperations.getAllBirthdays()

        list = fileOperations.deleteServerFromList(self.guild_id, all_birthdays)

        fileOperations.saveBirthdays(list) 



    def saveLevels(self):
        '''Saves any level changes made to this class.'''
        self.levels.saveLevels()
        
    def deleteLevelsAndSave(self):
        '''Deletes any Level files from server'''
        all_levels = fileOperations.getAllLevels()

        list = fileOperations.deleteServerFromList(self.guild_id, all_levels)

        fileOperations.saveLevels(list) 

    def saveLevelRewards(self):
        '''Saves any level reward changes made to this class.'''
        self.levels.saveLevelRewards()
        
    def deleteLevelRewardsAndSave(self):
        '''Deletes any Level Reward files from server'''
        all_levels = fileOperations.getAllLevelRewards()

        list = fileOperations.deleteServerFromList(self.guild_id, all_levels)

        fileOperations.saveLevelRewards(list) 



    def __getVCs(self):
        '''Returns list of VCs.'''
        all_VCs = fileOperations.getAllVCs()

        for server in all_VCs:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        new_VCs = fileOperations.addServerToList(self.guild_id, all_VCs, None)
        fileOperations.saveVCs(new_VCs)

        return []

    def saveVCs(self):
        '''Saves any VC changes made to this class.'''
        VCs = [vc.id for vc in self.VCs] #will save the ids now
        
        all_VCs = fileOperations.getAllVCs()

        list = fileOperations.editServerInList(self.guild_id, all_VCs, fileOperations.joinWithHyphens(VCs))

        fileOperations.saveVCs(list)

    def VCExists(self, VC_ID):
        '''Returns bool if vc exists on this server as a join-to-create-vc.'''
        VC_ID = int(VC_ID)
        for Vc in self.VCs:
            if Vc.id == VC_ID:
                return True
        
        return False

    def deleteVCsAndSave(self):
        '''Deletes any VC files from server'''
        all_VCs = fileOperations.getAllVCs()

        list = fileOperations.deleteServerFromList(self.guild_id, all_VCs)

        fileOperations.saveVCs(list) 



    def __getAutoBans(self):
        '''Returns list of Auto-Bans.'''
        all_auto_bans = fileOperations.getAllAutoBans()

        for server in all_auto_bans:
            if server.split("———")[0] == self.guild_id:
                return server.split("———")[1:]

        new_auto_bans = fileOperations.addServerToList(self.guild_id, all_auto_bans, None)
        fileOperations.saveAutoBans(new_auto_bans)

        return []

    def saveAutoBans(self):
        '''Saves any Auto-Ban changes made to this class.'''
        auto_bans = [ban.saveValue() for ban in self.auto_bans]
        
        all_auto_bans = fileOperations.getAllAutoBans()

        list = fileOperations.editServerInList(self.guild_id, all_auto_bans, fileOperations.joinWithHyphens(auto_bans))

        fileOperations.saveAutoBans(list)

    def autoBanExists(self, member_id):
        '''Returns bool if memberID exists in this server as an auto-ban.'''
        member_id = int(member_id)
        for ban in self.auto_bans:
            if ban.member_id == member_id:
                return True
        
        return False

    def addAutoBan(self, member_name, member_id, replace = False):
        """
        Adds an auto-ban to this server (returns True). If it already existed, returns False.
        
        Optional Paramaters:
        --------------------
        replace: `bool` (False)
            Whether to replace if it already exists (returns True)
        """
        
        if self.autoBanExists(member_id):
            if replace:
                return self.replaceAutoBan(member_name, member_id)
            else:
                return False
        
        self.auto_bans.append(AutoBan(str(member_name) + "|||" + str(member_id)))
        return True
    
    def replaceAutoBan(self, member_name, member_id):
        '''Replaces an auto-ban in this server (returns True). If it didn't exist, returns False (doesn't add it).'''
        if self.autoBanExists(member_id):
            for auto_ban in self.auto_bans:
                if auto_ban.member_id == int(member_id):
                    self.auto_bans[self.auto_bans.index(auto_ban)] = AutoBan(str(member_name) + "|||" + str(member_id))
                    return True
                
            return False
        else:
            return False

    def deleteAutoBan(self, member_id):
        '''Deletes an auto-ban from server (returns True). If auto-ban didn't exist for this member, returns False.'''
        if self.autoBanExists(member_id):
            for auto_ban in self.auto_bans:
                if auto_ban.member_id == int(member_id):
                    self.auto_bans.remove(auto_ban)
                    break
            
            return True
        else:
            return False

    def deleteAutoBansAndSave(self):
        '''Deletes any Auto-Ban files from server'''
        all_bans = fileOperations.getAllAutoBans()

        list = fileOperations.deleteServerFromList(self.guild_id, all_bans)

        fileOperations.saveAutoBans(list) 


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
        return get_discord_color_from_string(self.color)

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
        self.dms_enabled = member['dms'] #bool
        self.level_card = Card(member['levelCard'])
        self.join_card = Card(member['joinCard'])
        
    def __getMember(self):
        '''Returns list of data for the member.'''
        allMembers = fileOperations.getAllMembers()
        
        #find THIS member
        for member in allMembers:
            #member = 123456789———JSON
            if member.split("———")[0] == self.member_id:
                data: dict = json.loads(member.split("———")[1])
                
                return standardize_dict_properties(self.DEFAULTS, data)
            
        #this means that the member does not exist in the records. We should return the defaults.
        return self.DEFAULTS
        
    def save(self):
        '''Saves any changes made to this class'''
        saveFile = dict(self.DEFAULTS)
        
        #set information
        saveFile['dms'] = self.dms_enabled
        saveFile['levelCard'] = self.level_card.saveValue()
        saveFile['joinCard'] = self.join_card.saveValue()
        
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
        self.message_data = {
            "Vote": {
                "list": [],
                "max_active_messages": None
            },
            "Reaction Role": {
                "list": [],
                "max_active_messages": None
            },
            "Embed": {
                "list": [],
                "max_active_messages": 20
            },
            "Role Message": {
                "list": [],
                "max_active_messages": None
            }
        }
        
        self.default_message_data = copy.deepcopy(self.message_data)
        self._initialized = False
        self.deleted = False

    def initialize(self):
        '''Initializes the Messages class by retrieving all active messages for this server.'''
        messages = self._getAllMessages()
        if messages is not None:
            for _type, data in self.message_data.items():
                data["list"] = messages.get(_type, [])
                # This code will save the data from messages and add it to self.message_data
                
        self._initialized = True;

    def _getAllMessages(self):
        '''Returns all the messages as a dictionary of message type and list of Message objects.'''
        allServers = fileOperations.getAllMessages()
        messageTypes = list(self.message_data.keys())

        # Find THIS server
        for server in allServers:
            if server.split("———")[0] == self.guild_id:
                # Correct Server
                if len(server.split("———")) == 1:
                    # No Data
                    return None

                package = {}
                serverMessageTypesSorted = server.split("———")[1].split("$")
                for index, messageType in enumerate(serverMessageTypesSorted):
                    # For each type of message, this loops once. You can get the type with messageTypes[index]
                    maxMessages = self.maxOf(messageTypes[index])
                    infinite = (maxMessages == None)
                    
                    messages = messageType.split("#") # messages stores all of the messages for the current type
                    for message in messages:
                        if message == "":
                            # No Data
                            continue

                        parts = message.split("|")
                        path = parts[0].split("/")
                        _type = messageTypes[index]
                        message_obj = Message(_type, int(path[0]), int(path[1]), int(parts[1]), True if infinite or parts[2] == "T" else False, parts[3:])
                        package.setdefault(_type, []).append(message_obj)
                        # Set default will create a key with a value of [] if the key does not exist. It will then return that empty list so that we can append to it.
                        # If it already does exist, then it returns the value that is already there. We then append to that list.
                        # Our changes that we have appended are then saved automatically in the list
                        
                return package

        # If the server does not exist, then we'll return None. If we later add something, THEN and only then will we save.
        return None

    def add(self, _type, channel_id, message_id, owner_id, persistent=False, parameters = []):
        '''Adds an active message to the server.
        Returns True if successful, False if the type is invalid.'''
        
        if not self._initialized:
            self.initialize();
        
        if _type not in self.message_data:
            # Type is invalid
            return False

        parameters = [str(x) for x in parameters] # Ensure that parameters are strings.
        _list: list = self.message_data[_type]["list"] # Get all the messages for our current type
        _list.insert(0, Message(_type, channel_id, message_id, owner_id, persistent, parameters)) # Insert our message

        # Delete a message if needed to maintain our maximum active messages count.
        max_active_messages = self.message_data[_type]["max_active_messages"]
        if max_active_messages != None and len(_list) > max_active_messages:
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
        
        for _type, data in self.message_data.items():
            _list: list[Message] = data["list"]
            for message in _list:
                if message.message_id == message_id:
                    # This is our message
                    _list.remove(message)
                    
                    # Also check if deletable
                    self.checkIfDeletable()
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
        
        removed_data = False
        for _type, data in self.message_data.items():
            _list: list[Message] = data["list"]
            for message in _list:
                if message.channel_id == channel_id:
                    # This is our channel
                    _list.remove(message)
                    removed_data = True
        
        if removed_data:
            # Check if deletable
            self.checkIfDeletable()
            return True
    
        return False

    def save(self):
        '''Saves all changes made to this class. Returns True if able to save, False if prohibited.'''     
            
        if self.deleted:
            return False
            
        if self.checkIfDeletable():
            return False
            
        serverData = []
        for _type, data in self.message_data.items():
            # For each type of message, this loop will run once.
            maxMessages = self.maxOf(_type)
            infinite = (maxMessages == None)
            
            _list: list[Message] = data["list"] # Get the data for this type
            allEncodedMessages = []
            for message in _list:
                if infinite:
                    persistent = ""
                else:
                    persistent = ("T" if message.persistent else "F")
                    
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
        
        return True

    def getAll(self, _type) -> list[Message]: 
        '''Returns the list of active messages of a specific type.
        Returns List if successful, None if the type is invalid.'''
        if not self._initialized:
            self.initialize();
            
        if _type not in self.message_data:
            # Type invalid
            return None;
        
        return self.message_data[_type]["list"]

    def get(self, message_id):
        '''Returns a Message with a specific channel and message_id.
        Returns Message if successful, None if message doesn't exist or error.'''
        if not self._initialized:
            self.initialize();
            
        try:
            message_id = int(message_id)
        except ValueError:
            return None;
        
        for _type, data in self.message_data.items():
            _list: list[Message] = data["list"]
            for message in _list:
                if message.message_id == message_id:
                    return message;
        return None;

    def countOf(self, _type) -> int:
        '''Returns the total amount of a type of active message that are currently cached (not the max amount). Returns None if type is invalid.'''
        all = self.getAll(_type)
        if all == None:
            return None
        
        return len(all)

    def maxOf(self, _type):
        '''Returns the max amount of a type of active message. None if infinite or invalid type.'''
        if _type not in self.message_data:
            # Type is invalid
            return None
        
        maxActiveMessages: int = self.message_data[_type]["max_active_messages"]
        return maxActiveMessages
        
    async def checkAll(self):
        '''Checks all active messages to see if any don't exist anymore'''
        if not self._initialized:
            self.initialize();
            
        guild = await bot.fetch_guild(self.guild_id)
        
        for _type, data in self.message_data.items():
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
        
        # Check if deletable
        self.checkIfDeletable()
      
    def checkIfDeletable(self):
        '''Checks if we need to be storing any Active Messages for the server. If not, data is deleted and returns True. Else returns False.'''
        if self.message_data == self.default_message_data:
            # The data is the same. Why store it?
            self.deleteAllAndSave()
            return True
        return False
                    
    def deleteAllAndSave(self):
        '''Deletes any Active Messages files from server'''
        allMessages = fileOperations.getAllMessages()

        list = fileOperations.deleteServerFromList(self.guild_id, allMessages)

        fileOperations.saveMessages(list)
        
        # Edit our deleted status
        self.deleted = True


#Buttons and UI






# CUSTOM views ==========================================================================================================================================================
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
        
        # We either need to refund a strike, or revoke a timeout.
        # If the user is at 0 strikes now, this tells us one of two things:
        # They were timed out
        # Or it's been so long that the strike has expired.
        
        server = Server_DEP(interaction.guild.id)
        strike_data = server.getStrike(member.id)
        if strike_data.strike != 0:
            # We'll just refund a strike.
            await giveStrike(guild.id, member.id, -1)
            
            embed.title += " - Marked As Incorrect"
            embed.color = nextcord.Color.dark_green()
            await interaction.response.edit_message(embed = embed, view=self)
            return
            
        else:
            # Uh, oh. We need to do some thinking...
            # Has it been past the time that the timeout would have been?
            current_time = datetime.datetime.now(datetime.timezone.utc)
            message_time = interaction.message.created_at
            timeout_time_seconds = humanfriendly.parse_timespan(server.profanity_timeout_time)
            delta_seconds = (current_time - message_time).seconds
            if delta_seconds <= timeout_time_seconds:
                # We can revoke the timeout
                await timeout(member = strike_data.member, time = "0s", reason = "Revoking Profanity Moderation Timeout")
                
                embed.title += " - Marked As Incorrect"
                embed.color = nextcord.Color.dark_green()
                await interaction.response.edit_message(embed = embed, view=self)
                return
            
            else:
                button.label = "No Available Actions"
                await interaction.response.edit_message(view=self)

                await interaction.followup.send(embed = nextcord.Embed(title = "No Available Actions", description = f"No actions available. Previous punishments have expired.", color =  nextcord.Color.red()), ephemeral = True)
                return

        

        
        
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
        ["Unable to find specifics", "Infinibot is unable to find any info regarding this message because of Discord's limitations.\n\nThe user probably deleted their own message."],
        ["Unable to find specifics", "Infinibot is unable to find the deleter because of Discord's limitations.\n\nThe user probably deleted their own message."]
    ]
  
  @nextcord.ui.button(label = 'Show More', style = nextcord.ButtonStyle.gray, custom_id = "show_more")
  async def event(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
    if button.label == "Show More":
        # Show more
        embed = interaction.message.embeds[0]
        code = embed.footer.text.split(" ")[-1]
        index = int(code) - 1
        
        info_embed = nextcord.Embed(title = "More Information", color = nextcord.Color.red())
        info_embed.add_field(name = self.possibleEmbeds[index][0], value = self.possibleEmbeds[index][1])
        
        # Change the Name of the button
        button.label = "Show Less"

        allEmbeds = interaction.message.embeds
        allEmbeds.append(info_embed)
    else:
        # Show less
        embed = interaction.message.embeds[0]
        
        # Change the Name of the button
        button.label = "Show More"
        
        allEmbeds = [embed]

    await interaction.response.edit_message(view=self, embeds = allEmbeds)
  
# Error "Why Administrator Privileges?" Button
class ErrorWhyAdminPrivilegesButton(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
    
    @nextcord.ui.button(label = "Why Administrator Privileges?", style = nextcord.ButtonStyle.gray, custom_id = "why_administrator_privileges")
    async def event(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        generalMessage = f"\n\n**Why Administrator Privileges?**\nSome of InfiniBot's features work best when it is able to view every channel and have all its required permissions in every channel. An alternative to Administrator is to give InfiniBot the following permissions in every channel:{required_permissions}"
        embed = interaction.message.embeds[0]
        embed.description += generalMessage
        
        button.disabled = True
        
        await interaction.response.edit_message(view = self, embed = embed)

# Role Message Button
class RoleMessageButton_Single(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
    
    class View(nextcord.ui.View):
        def __init__(self, user: nextcord.Member, message: nextcord.Message):
            super().__init__(timeout = None)
            self.message = message
            self.availableRoles = []
            
            userRoleIds = [role.id for role in user.roles if role.name != "@everyone"]
            
            optionSelected = False
            options = []
            for field in self.message.embeds[0].fields:
                description = "\n".join(field.value.split("\n")[:-1])
                roles = self.extract_ids(field.value.split("/n")[-1])
                self.add_available_roles(roles)
                
                # Check if the user has the roles
                selected = False
                for index, role in enumerate(roles):
                    if not int(role) in userRoleIds:
                        break
                    else:
                        if index == (len(roles) - 1): # If this is the last role to check
                            if not optionSelected:
                                selected = True
                                optionSelected = True
                            break
                
                options.append(nextcord.SelectOption(label = field.name, description = description, value = "|".join(roles), default = selected))
                
            self.select = nextcord.ui.Select(placeholder = "Choose a Role", min_values = 0, options = options)
            self.select.callback = self.selectCallback
            self.add_item(self.select)
                
        def extract_ids(self, input_string):
            pattern = r"<@&(\d+)>"
            matches = re.findall(pattern, input_string)
            return matches
            
        def add_available_roles(self, rolesList):
            for role in rolesList:
                if int(role) not in self.availableRoles:
                    self.availableRoles.append(int(role))
            
        async def setup(self, interaction: Interaction):
            await interaction.response.send_message(view = self, ephemeral = True)
            
        async def selectCallback(self, interaction: Interaction):
            selection = self.select.values
            selectedRoles = []
            for option in selection:
                for role in option.split("|"):
                    selectedRoles.append(int(role))
                    
            # Get the roles
            
            roles_add = []
            roles_remove = []
            for role in self.availableRoles:
                if role in selectedRoles:
                    roles_add.append(interaction.guild.get_role(int(role)))
                else:
                    roles_remove.append(interaction.guild.get_role(int(role)))
                    
            error = False
            try:
                await interaction.user.add_roles(*roles_add)
                await interaction.user.remove_roles(*roles_remove)
            except nextcord.errors.Forbidden:
                error = True
                
            embed = nextcord.Embed(title = "Modified Roles", color = nextcord.Color.green())
            if error: embed.description = "Warning: An error occurred with one or more roles. Please notify server admins."
            
            await interaction.response.edit_message(embed = embed, view = None, delete_after = 2.0)
    
    @nextcord.ui.button(label = "Get Role", style = nextcord.ButtonStyle.blurple, custom_id = "get_role")
    async def event(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        message = interaction.message
        await self.View(interaction.user, message).setup(interaction)

class RoleMessageButton_Multiple(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
    
    class View(nextcord.ui.View):
        def __init__(self, user: nextcord.Member, message: nextcord.Message):
            super().__init__(timeout = None)
            self.message = message
            self.availableRoles = []
            
            userRoleIds = [role.id for role in user.roles if role.name != "@everyone"]
            
            options = []
            for field in self.message.embeds[0].fields:
                description = "\n".join(field.value.split("\n")[:-1])
                roles = self.extract_ids(field.value.split("/n")[-1])
                self.add_available_roles(roles)
                
                # Check if the user has the roles
                selected = False
                for index, role in enumerate(roles):
                    if not int(role) in userRoleIds:
                        break
                    else:
                        if index == (len(roles) - 1): # If this is the last role to check
                            selected = True
                            break
                
                options.append(nextcord.SelectOption(label = field.name, description = description, value = "|".join(roles), default = selected))
                
            self.select = nextcord.ui.Select(placeholder = "Choose Roles", min_values = 0, max_values = len(options), options = options)
            self.select.callback = self.selectCallback
            self.add_item(self.select)
                
        def extract_ids(self, input_string):
            pattern = r"<@&(\d+)>"
            matches = re.findall(pattern, input_string)
            return matches
            
        def add_available_roles(self, rolesList):
            for role in rolesList:
                if int(role) not in self.availableRoles:
                    self.availableRoles.append(int(role))
            
        async def setup(self, interaction: Interaction):
            await interaction.response.send_message(view = self, ephemeral = True)
            
        async def selectCallback(self, interaction: Interaction):
            selection = self.select.values
            selectedRoles = []
            for option in selection:
                for role in option.split("|"):
                    selectedRoles.append(int(role))
                    
            # Get the roles
            
            roles_add = []
            roles_remove = []
            for role in self.availableRoles:
                if role in selectedRoles:
                    roles_add.append(interaction.guild.get_role(int(role)))
                else:
                    roles_remove.append(interaction.guild.get_role(int(role)))
                    
            error = False
            try:
                await interaction.user.add_roles(*roles_add)
                await interaction.user.remove_roles(*roles_remove)
            except nextcord.errors.Forbidden:
                error = True
                
            embed = nextcord.Embed(title = "Modified Roles", color = nextcord.Color.green())
            if error: embed.description = "Warning: An error occurred with one or more roles. Please notify server admins."
            
            await interaction.response.edit_message(embed = embed, view = None, delete_after = 2.0)
    
    @nextcord.ui.button(label = "Get Roles", style = nextcord.ButtonStyle.blurple, custom_id = "get_roles")
    async def event(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        message = interaction.message
        await self.View(interaction.user, message).setup(interaction)



class ReactionRoleView(nextcord.ui.View):
    def __init__(self, roles: list[nextcord.Role]):
        super().__init__()

        options = []
        # In case there are more than 25 roles, let's do this in reverse. We want the lowest roles to appear here, if nothing else.
        roles.reverse()
        for role in roles:
            if len(options) >= 25:
                # We can't add any more to this.
                break
            else:
                options.append(nextcord.SelectOption(label = role.name, value = role.name))
                
            
        self.selection = []
        
        if len(options) < 10:
            maxValues = len(options)
        else:
            maxValues = 10
        
        self.select = nextcord.ui.Select(placeholder = "Select Up to 10 Roles", options = options, max_values=maxValues)
        
        self.button = nextcord.ui.Button(label = "Create", style = nextcord.ButtonStyle.blurple)
        self.button.callback = self.createCallback
        
        self.add_item(self.select)
        self.add_item(self.button)
             
    async def createCallback(self, interaction: Interaction):
        self.selection = self.select.values
        if self.selection == []: return
        if self.selection == None: return
        
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
        if self.selection == []: return
        
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
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = support_server_link)
        self.add_item(supportServerBtn)

class InviteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        inviteBtn = nextcord.ui.Button(label = "Add to Your Server", style = nextcord.ButtonStyle.link, url = invite_link)
        self.add_item(inviteBtn)

class SupportAndInviteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = support_server_link)
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Add To Your Server", style = nextcord.ButtonStyle.link, url = invite_link)
        self.add_item(inviteBtn)

class SupportInviteAndTopGGVoteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = support_server_link)
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Invite", style = nextcord.ButtonStyle.link, url = invite_link)
        self.add_item(inviteBtn)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote for InfiniBot", style = nextcord.ButtonStyle.link, url = topgg_vote_link)
        self.add_item(topGGVoteBtn)
        
class SupportInviteAndTopGGReviewView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = support_server_link)
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Invite", style = nextcord.ButtonStyle.link, url = invite_link)
        self.add_item(inviteBtn)
        
        topGGReviewBtn = nextcord.ui.Button(label = "Leave a Review", style = nextcord.ButtonStyle.link, url = topgg_review_link)
        self.add_item(topGGReviewBtn)

class TopGGVoteView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote", style = nextcord.ButtonStyle.link, url = topgg_vote_link)
        self.add_item(topGGVoteBtn)
        
class TopGGAll(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        topGG = nextcord.ui.Button(label = "Visit on Top.GG", style = nextcord.ButtonStyle.link, url = topgg_link)
        self.add_item(topGG)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote for InfiniBot", style = nextcord.ButtonStyle.link, url = topgg_vote_link)
        self.add_item(topGGVoteBtn)
        
        topGGReviewBtn = nextcord.ui.Button(label = "Leave a Review", style = nextcord.ButtonStyle.link, url = topgg_review_link)
        self.add_item(topGGReviewBtn)

class SupportandPermissionsCheckView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = support_server_link)
        self.add_item(supportServerBtn)

        permissionsCheckBtn = nextcord.ui.Button(label = "Check Permissions", style = nextcord.ButtonStyle.gray)
        permissionsCheckBtn.callback = check_infinibot_permissions
        self.add_item(permissionsCheckBtn)
        
class SupportInviteTopGGVoteAndPermissionsCheckView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = support_server_link)
        self.add_item(supportServerBtn)
        
        inviteBtn = nextcord.ui.Button(label = "Invite", style = nextcord.ButtonStyle.link, url = invite_link)
        self.add_item(inviteBtn)
        
        topGGVoteBtn = nextcord.ui.Button(label = "Vote for InfiniBot", style = nextcord.ButtonStyle.link, url = topgg_vote_link)
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
            if guild.id == infinibot_guild_id: server = guild
        
        if server == None:
            print("ERROR: CANNOT FIND INFINIBOT SERVER!!!")
            self.stop()
            return
        
        embed = nextcord.Embed(title = "New Issue Report Submission:", description = f"Member: {self.member}\nMember ID: {self.member.id}\nServer: {interaction.guild.name}\nServer ID: {interaction.guild.id}", color = nextcord.Color.orange())
        embed.add_field(name = "Describe the Problem", value = self.problemTextInput.value)
        embed.add_field(name = "What Happened Before?", value = self.historyTextInput.value)
        if self.notesTextInput.value != "": embed.add_field(name = "Other notes:", value = self.notesTextInput.value)
        
        channel = server.get_channel(issue_report_channel_id)
        await channel.send(embed = embed)
        
        await interaction.response.send_message(embed = nextcord.Embed(title = "Issue Report Submitted", description = f"Join us at {support_server_link} or contact at infinibotassistance@gmail.com. and see if your issue will be added to https://discord.com/channels/1009127888483799110/1009136603064713309", color = nextcord.Color.green()), ephemeral=True, view = SupportView())
        
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
            if guild.id == infinibot_guild_id: server = guild
        
        if server == None:
            print("ERROR: CANNOT FIND INFINIBOT SERVER!!!")
            self.stop()
            return
        
        embed = nextcord.Embed(title = "New Idea Submission:", description = f"Member: {self.member}\nMember ID: {self.member.id}\nServer: {interaction.guild.name}\nServer ID: {interaction.guild.id}", color = nextcord.Color.green())
        embed.add_field(name = "How would it work?", value = self.ideaTextInput.value)
        embed.add_field(name = "What Happened Before?", value = self.howItWouldWorkTextInput.value)
        if self.notesTextInput.value != "": embed.add_field(name = "Other notes:", value = self.notesTextInput.value)
        
        channel = server.get_channel(submission_channel_id)
        await channel.send(embed = embed)
        
        await interaction.response.send_message(embed = nextcord.Embed(title = "Idea Submitted", description = f"Join us at {support_server_link} or contact at infinibotassistance@gmail.com. and see if your idea will be a reality! You can view our road map here: https://discord.com/channels/1009127888483799110/1009134131835322448", color = nextcord.Color.green()), ephemeral=True, view = SupportView())
 
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
    
        if not utils.enabled.Profile(guild_id = interaction.guild.id):
            await disabled_feature_override(self, interaction)
            return
    
        description = f"""Welcome to your InfiniBot Profile! Choose a setting:"""
        
        # On Mobile, extra spaces cause problems. We'll get rid of them here:
        description = standardize_str_indention(description)
        
        
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
                
                if member.level_card.enabled:
                    changeTextBtn = self.ChangeTextButton(self)
                    self.add_item(changeTextBtn)
                    
                    changeColorBtn = self.ChangeColorButton(self)
                    self.add_item(changeColorBtn)
                    
                enableDisableBtn = self.EnableDisableButton(self, member.level_card.enabled)
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
                enabledDescription = standardize_str_indention(enabledDescription)
                disabledDescription = standardize_str_indention(disabledDescription)
                
                
                member = Member(interaction.user.id)
                
                
                embed = nextcord.Embed(title = "Profile - Level-Up Card", description = (enabledDescription if member.level_card.enabled else disabledDescription), color = nextcord.Color.blurple())
                
                #get the card
                if member.level_card.enabled:
                    card = member.level_card.embed()
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
                        title = member.level_card.title
                        description = member.level_card.description
                        del member #we don't need it anymore
                        
                        self.titleTextInput = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, max_length = 256, default_value = title, placeholder = "Yum... Levels.")
                        self.add_item(self.titleTextInput)
                        
                        self.descriptionTextInput = nextcord.ui.TextInput(label = "Description ([level] = level)", style = nextcord.TextInputStyle.paragraph, max_length = 4000, default_value = description, placeholder = "Level [level]!")
                        self.add_item(self.descriptionTextInput)
                        
                    async def callback(self, interaction: Interaction):
                        title = self.titleTextInput.value
                        description = self.descriptionTextInput.value
                        
                        member = Member(interaction.user.id)
                        member.level_card.title = title
                        member.level_card.description = description
                        
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
                        description = standardize_str_indention(description)


                        embed = nextcord.Embed(title = "Profile - Level-Up Card - Change Color", description = description, color = nextcord.Color.blurple())
                        
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    async def updateBtnCallback(self, interaction: Interaction):
                        if len(self.select.values) != 1: 
                            await self.outer.setup(interaction)
                            return
                        
                        member = Member(interaction.user.id)
                        member.level_card.color = self.select.values[0]
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
                            member.level_card.enabled = not member.level_card.enabled
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
                
                if member.join_card.enabled:
                    changeTextBtn = self.ChangeTextButton(self)
                    self.add_item(changeTextBtn)
                    
                    changeColorBtn = self.ChangeColorButton(self)
                    self.add_item(changeColorBtn)
                    
                enableDisableBtn = self.EnableDisableButton(self, member.join_card.enabled)
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
                enabledDescription = standardize_str_indention(enabledDescription)
                disabledDescription = standardize_str_indention(disabledDescription)
                
                
                member = Member(interaction.user.id)
                
                
                embed = nextcord.Embed(title = "Profile - Join Card", description = (enabledDescription if member.join_card.enabled else disabledDescription), color = nextcord.Color.blurple())
                
                #get the card
                if member.join_card.enabled:
                    card = member.join_card.embed()
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
                        title = member.join_card.title
                        description = member.join_card.description
                        del member #we don't need it anymore
                        
                        self.titleTextInput = nextcord.ui.TextInput(label = "Title", style = nextcord.TextInputStyle.short, max_length = 256, default_value = title, placeholder = "About Me")
                        self.add_item(self.titleTextInput)
                        
                        self.descriptionTextInput = nextcord.ui.TextInput(label = "Description", style = nextcord.TextInputStyle.paragraph, max_length = 4000, default_value = description, placeholder = "I am human")
                        self.add_item(self.descriptionTextInput)
                        
                    async def callback(self, interaction: Interaction):
                        title = self.titleTextInput.value
                        description = self.descriptionTextInput.value
                        
                        member = Member(interaction.user.id)
                        member.join_card.title = title
                        member.join_card.description = description
                        
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
                        description = standardize_str_indention(description)


                        embed = nextcord.Embed(title = "Profile - Join Card - Change Color", description = description, color = nextcord.Color.blurple())
                        
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    async def updateBtnCallback(self, interaction: Interaction):
                        if len(self.select.values) != 1: 
                            await self.outer.setup(interaction)
                            return
                        
                        member = Member(interaction.user.id)
                        member.join_card.color = self.select.values[0]
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
                            member.join_card.enabled = not member.join_card.enabled
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
                
                {icon(member.dms_enabled)} Direct Messages Enabled"""
                
                # On Mobile, extra spaces cause problems. We'll get rid of them here:
                description = standardize_str_indention(description)
                
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
                        if member.dms_enabled: label = "Disable"
                        else: label = "Enable"
                        
                        button = nextcord.ui.Button(label = label, style = nextcord.ButtonStyle.green)
                        button.callback = self.callback
                        self.add_item(button)
                        
                    async def setup(self, interaction: Interaction):
                        member = Member(interaction.user.id)
                        
                        if member.dms_enabled: description = "To disable Direct Messages from InfiniBot, click the button \"Disable\"\n\nBy doing this, you will no longer recieve permission errors, birthday updates, or strike notices."
                        else: description = "To enable Direct Messages from InfiniBot, click the button \"Enable\"\n\nBy doing this, you will now recieve permission errors, birthday updates, and strike notices."
                        
                        embed = nextcord.Embed(title = "Profile - Settings - Direct Messages", description = description, color = nextcord.Color.blurple())
                        await interaction.response.edit_message(embed = embed, view = self)
                    
                    async def backBtnCallback(self, interaction: Interaction):
                        await self.outer.setup(interaction)
                    
                    async def callback(self, interaction: Interaction):
                        member = Member(interaction.user.id)
                        member.dms_enabled = not member.dms_enabled
                        
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
                        description = standardize_str_indention(description)
                        
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
    

class Onboarding(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        self.dropdown_options = [
            ["Profanity Moderation", "Automatically moderate your server for profanity."],
            ["Spam Moderation", "Help keep spam to a minimum."],
            ["Leveling", "Encourage activity as members compete for levels."],
            ["Message and Action Logging", "Track deleted and edited messages, and server modifications."],
            ["Join / Leave Messages", "Welcome / bid farewell with customized messages."],
            ["Birthdays", "Celebrate birthdays with personalized messages."],
            ["Default Roles", "Automatically assign roles to new members."],
            ["Join-To-Create VCs", "Allow members to create custom voice channels."]
        ]
        
        formatted_options = [nextcord.SelectOption(label = option[0], description = option[1]) for option in self.dropdown_options]
        self.dropdown = nextcord.ui.Select(placeholder = "Select Features", min_values = 0, max_values = len(formatted_options), options = formatted_options)
        self.add_item(self.dropdown)
        
        self.cancelBtn = self.cancelButton(self)
        self.add_item(self.cancelBtn)
        
        self.nextBtn = self.nextButton(self)
        self.add_item(self.nextBtn)
        
    async def setup(self, interaction: Interaction):
        for child in self.children: del child
        self.__init__()
        
        embed = nextcord.Embed(title = "Welcome to InfiniBot!", 
                               description = "Hello there!\n\nThank you for giving InfiniBot a try! Let's kick off your journey. Below, you'll find a convenient drop-down menu showcasing a variety of features that InfiniBot can set up for your server. \n\nTake your time to choose the ones that best suit your preferences. Once you've made your selections, simply click the \"Next\" button to proceed. Happy customizing!",
                               color = nextcord.Color.fuchsia())
        
        try: await interaction.response.edit_message(embed = embed, view = self)
        except: await interaction.response.send_message(embed = embed, view = self, ephemeral=True)
    
    class cancelButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Cancel", style = nextcord.ButtonStyle.danger, row = 1)
            self.outer = outer
            
        class cancelView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.gobackBtn = nextcord.ui.Button(label = "Go Back")
                self.gobackBtn.callback = self.gobackBtn_callback
                self.add_item(self.gobackBtn)
                
            async def setup(self, interaction: Interaction):
                embed = nextcord.Embed(title = "Canceling Onboarding Process", description = "To get back to this onboarding process, type `/onboarding`.", color = nextcord.Color.red())
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def gobackBtn_callback(self, interaction: Interaction):
                # Put us back to where we were at the start.
                self.outer.__init__()
                await self.outer.setup(interaction)
            
        async def callback(self, interaction: Interaction):          
            await self.cancelView(self.outer).setup(interaction)
    
    # This button gives a screen talking about the onboarding setup proccess. Then it jumps to the onboarding walkthrough class.
    class nextButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Next", style = nextcord.ButtonStyle.blurple)
            self.outer = outer
            
        class onboardingInfoView(nextcord.ui.View):
            def __init__(self, outer, order: list):
                super().__init__(timeout = None)
                self.outer = outer
                self.order = order
                
                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                self.back_btn.callback = self.backBtnCallback
                self.add_item(self.back_btn)
                
                self.start_btn = nextcord.ui.Button(label = "Start", style = nextcord.ButtonStyle.blurple)
                self.start_btn.callback = self.startBtnCallback
                self.add_item(self.start_btn)              
                
            async def setup(self, interaction: Interaction):
                description = """
                Next, configure each selected feature.

                You'll be directed to the dashboard for step-by-step instructions on setup. 

                Click "Next" after configuring each feature."""
                description = standardize_str_indention(description)
                
                embed = nextcord.Embed(title = "Onboarding Setup",
                                       description = description,
                                       color = nextcord.Color.fuchsia())
                
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                
            async def startBtnCallback(self, interaction: Interaction):
                await self.outer.onboardingWalkthrough(self.order, self.setup).start(interaction)
            
        async def callback(self, interaction: Interaction):
            selected_options = self.outer.dropdown.values
        
            if selected_options == []: return
            
            # Re-order the options
            ordered_list = []
            for option in [option[0] for option in self.outer.dropdown_options]:
                if option in selected_options:
                    ordered_list.append(option)
            
            await self.onboardingInfoView(self.outer, ordered_list).setup(interaction)
           
    class onboardingWalkthrough:
        def __init__(self, order: list, previous):
            self.order = order
            self.previous = previous
            
            self.current = order[0]
            self.objective = None
            self.next_objective = None
            self.onboarding_embed = None
            self.last_objective_bool = False
            
        async def start(self, interaction: Interaction):
            self.update_objectives()
            
            if self.current == "Profanity Moderation":
                await self.profanity_moderation(interaction)
                return
            
            if self.current == "Spam Moderation":
                await self.spam_moderation(interaction)
                return
            
            if self.current == "Leveling":
                await self.leveling(interaction)
                return
            
            if self.current == "Message and Action Logging":
                await self.logging(interaction)
                return
            
            if self.current == "Join / Leave Messages":
                await self.joinLeaveMessages(interaction)
                return
            
            if self.current == "Birthdays":
                await self.birthdays(interaction)
                return
            
            if self.current == "Default Roles":
                await self.defaultRoles(interaction)
                return
        
            if self.current == "Join-To-Create VCs":
                await self.joinToCreateVCs(interaction)
                return
            
        async def previous_item(self, interaction: Interaction):
            index = self.order.index(self.current)
            
            # Check if we are able to
            if index == 0:
                await self.previous(interaction)
            else:
                self.current = self.order[index - 1]
                await self.start(interaction)
            
        async def next_item(self, interaction: Interaction):
            index = self.order.index(self.current)
            
            # Check if we are able to
            if index == (len(self.order) - 1):
                await self.finished(interaction)
            else:
                self.current = self.order[index + 1]
                await self.start(interaction)
                
        def update_objectives(self):
            index = self.order.index(self.current)
            
            self.objective = f"configure {self.current}"
            
            if index == (len(self.order) - 1):
                self.next_objective = "Finish"
                self.last_objective_bool = True
            else:
                self.next_objective = f"Setup {self.order[index + 1]}"
                self.last_objective_bool = False
                
            self.onboarding_embed = nextcord.Embed(title = f"Click \"Next\" to {self.next_objective}",
                                   description = f"Alternatively, {self.objective}.",
                                   color = nextcord.Color.fuchsia())
                              
        async def finished(self, interaction: Interaction):
            await self.finishedView(self).setup(interaction)
        
        def remap_view_buttons(self, view: nextcord.ui.View):
            # Remove back (and next) button(s)
            # Also remove disable buttons (if they're there)
            for child in list(view.children):
                if isinstance(child, nextcord.ui.Button):
                    if child.label == "Back" or child.label == "Cancel":
                        view.remove_item(child)
                    if child.label == "Next" or child.label == "Finish":
                        view.remove_item(child)
                    if "Disable" in child.label:
                        view.remove_item(child)
                        
            # Add new buttons
            backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 4)
            backBtn.callback = self.previous_item
            view.add_item(backBtn)
            
            nextBtn = nextcord.ui.Button(label = ("Finish" if self.last_objective_bool else "Next"), style = nextcord.ButtonStyle.green, row = 4)
            nextBtn.callback = self.next_item
            view.add_item(nextBtn)
            
            return view
   
        # Some dashboard features may want to go all the way back. This function is for that
        async def setup(self, interaction: Interaction):
            await self.previous_item(interaction)
            return
        
        
        async def profanity_moderation(self, interaction: Interaction):
            # Enable the feature
            server = Server_DEP(interaction.guild.id)
            server.profanity_moderation_enabled = True
            server.saveData()
            del server
            
            view = Dashboard.ModerationButton.ModerationView.ProfaneModerationButton.ProfaneModerationView(outer = self, guild_id = interaction.guild.id, onboarding_modifier = self.remap_view_buttons, onboarding_embed = self.onboarding_embed)
            await view.setup(interaction)
            
        async def spam_moderation(self, interaction: Interaction):
            # Enable the feature
            server = Server_DEP(interaction.guild.id)
            server.spam_moderation_enabled = True
            server.saveData()
            del server
        
            view = Dashboard.ModerationButton.ModerationView.SpamModerationButton.SpamModerationView(outer = self, onboarding_modifier = self.remap_view_buttons, onboarding_embed = self.onboarding_embed)
            await view.setup(interaction)
            
        async def leveling(self, interaction: Interaction):
            # Enable the feature
            server = Server_DEP(interaction.guild.id)
            server.leveling_enabled = True
            server.saveData()
            del server
        
            view = Dashboard.LevelingButton.LevelingView(outer = self, onboarding_modifier = self.remap_view_buttons, onboarding_embed = self.onboarding_embed)
            await view.setup(interaction)
            
        async def logging(self, interaction: Interaction):
            # Enable the feature
            server = Server_DEP(interaction.guild.id)
            server.logging_enabled = True
            server.saveData()
            del server
        
            view = Dashboard.LoggingButton.LoggingView(outer = self, onboarding_modifier = self.remap_view_buttons, onboarding_embed = self.onboarding_embed)
            await view.setup(interaction)
            
        async def joinLeaveMessages(self, interaction: Interaction):
            # Enable the feature
            server = Server_DEP(interaction.guild.id)
            if server.join_channel == False: server.join_channel = None
            if server.leave_channel == False: server.leave_channel = None
            server.saveData()
            del server
            
            view = Dashboard.JoinLeaveMessagesButton.JoinLeaveMessagesView(outer = self, onboarding_modifier = self.remap_view_buttons, onboarding_embed = self.onboarding_embed)
            await view.setup(interaction)
            
        async def birthdays(self, interaction: Interaction):
            view = Dashboard.BirthdaysButton.BirthdaysView(outer = self, onboarding_modifier = self.remap_view_buttons, onboarding_embed = self.onboarding_embed)
            await view.setup(interaction)
            
        async def defaultRoles(self, interaction: Interaction):
            view = Dashboard.DefaultRolesButton.DefaultRolesView(outer = self, onboarding_modifier = self.remap_view_buttons, onboarding_embed = self.onboarding_embed)
            await view.setup(interaction)

        async def joinToCreateVCs(self, interaction: Interaction):
            view = Dashboard.JoinToCreateVCsButton.JoinToCreateVCsView(outer = self, onboarding_modifier = self.remap_view_buttons, onboarding_embed = self.onboarding_embed)
            await view.setup(interaction)

        class finishedView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                self.back_btn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger)
                self.back_btn.callback = self.backBtnCallback
                self.add_item(self.back_btn)
                
                supportServerBtn = nextcord.ui.Button(label = "Support Server", style = nextcord.ButtonStyle.link, url = support_server_link)
                self.add_item(supportServerBtn)
                
            async def setup(self, interaction: Interaction):
                description = """
                Congratulations! InfiniBot is now set up for your server.

                For additional features, type `/dashboard` to explore all InfiniBot offers. If you need to change anything you've done today, this is your place to go.

                Questions? Join our support server for assistance.

                Thanks for using InfiniBot!
                """
                
                embed = nextcord.Embed(title = "Onboarding - Completed",
                                       description = standardize_str_indention(description), color = nextcord.Color.fuchsia())
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.start(interaction)

#Real Code (YAY) ------------------------------------------------------------------------------------------------------------------------------------------------






    
  
@bot.slash_command(name = "opt_into_dms", description = "Opt in for dm notifications from InfiniBot.")
async def opt_into_dms(interaction: Interaction):
    member = Member(interaction.user.id)
    
    if member.dms_enabled == True: 
        await interaction.response.send_message(embed = nextcord.Embed(title = "Already opted into DMs", description = "You are already opted into dms.", color = nextcord.Color.blue()), ephemeral = True)
        return
    
    member.dms_enabled = True
    member.save()
    
    embed = nextcord.Embed(title = "Opted Into DMs", description = f"You opted into DMs from InfiniBot. You will now recieve permission errors, birthday updates, or strike notices.", color = nextcord.Color.green())
    await interaction.response.send_message(embed = embed, ephemeral = True)
    
    dm = await interaction.user.create_dm()
    await dm.send(embed = embed)
    
@bot.slash_command(name = "opt_out_of_dms", description = "Opt out of dm notifications from InfiniBot.")
async def opt_out_of_dms(interaction: Interaction):
    member = Member(interaction.user.id)
    
    if member.dms_enabled == False: 
        await interaction.response.send_message(embed = nextcord.Embed(title = "Already opted out of DMs", description = "You are already opted out of dms.", color = nextcord.Color.blue()), ephemeral = True)
        return
    
    member.dms_enabled = False
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
        bot.add_view(RoleMessageButton_Single())
        bot.add_view(RoleMessageButton_Multiple())
        bot.add_view(JokeView())
        bot.add_view(JokeVerificationView())
        viewsInitialized = True
        
    print(f"Logged in as: {bot.user.name}")
    
    
    #login response stuff
    if (global_kill_status.login_response_guildID != None and global_kill_status.login_response_channelID != None):
        #get guild and channel
        guild = None
        for _guild in bot.guilds:
            if _guild.id == global_kill_status.login_response_guildID:
                guild = _guild
                break
        
        if guild != None:
            channel = None
            for _channel in guild.channels:
                if _channel.id == global_kill_status.login_response_channelID:
                    channel = _channel
                    break
            
            if channel != None:
                embed = nextcord.Embed(title = "InfiniBot Loaded", description = "InfiniBot has been completely loaded.", color = nextcord.Color.green())
                await channel.send(embed = embed)
        
        global_kill_status.login_response_guildID = None
        global_kill_status.login_response_channelID = None
        global_kill_status.savePersistentData()
        
    if (global_kill_status.login_response_guildID != None or global_kill_status.login_response_channelID != None):
        global_kill_status.login_response_guildID = None
        global_kill_status.login_response_channelID = None
        global_kill_status.savePersistentData()
    
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
    
    You're all set up! Type {onboarding.get_mention()} to get started.
    
    For any help or suggestions, join us at {support_server_link} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    join_message = standardize_str_indention(join_message)
    
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
    server = Server_DEP(guild.id)
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
    server = Server_DEP(message.guild.id)
    await checkForExpiration(server)
    
    # Check for InfiniBot Mod Role Existence
    await checkForRole(message.guild)
    if message.guild.id in guildsCheckingForRole: guildsCheckingForRole.remove(message.guild.id)
    
    # Don't do any of this if this is a bot
    if message.author.bot:
        return

    # Profanity
    Profane = False
    if utils.enabled.ProfanityModeration(server = server):
        Profane = await checkProfanity(server, message)
       

    # Other Things
    if not Profane:
        # Check Invites
        if server.delete_invites_enabled and not message.author.guild_permissions.administrator:
            if "discord.gg/" in message.content.lower(): await message.delete()
        # Check spam
        if utils.enabled.SpamModeration(server = server) and not message.author.guild_permissions.administrator:
            await checkSpam(message, server)
        # Give levels
        if utils.enabled.Leveling(server = server): await giveLevels(message)
        await adminCommands(message)


    # Continue with the Rest of the Bot Commands
    await bot.process_commands(message)








# RUN EVERY MINUTE ===========================================================================================================================================================================
dbl_token = ""
with open("./generated/configure/TOKEN.txt", "r") as file:
    dbl_token = file.read().split("\n")[1]
    
if dbl_token.lower() != "none":
    import topgg
    bot.topggpy = topgg.DBLClient(bot, dbl_token)

runEveryMinute_isRunning = False
async def runEveryMinute():
    global runEveryMinute_isRunning
    
    # Ensure only one instance
    if runEveryMinute_isRunning:
        return
    
    # Update the variable
    runEveryMinute_isRunning = True
    
    # Run the code
    while True:
        currentTimeRaw = datetime.datetime.now()
        currentTime = datetime.datetime(year = currentTimeRaw.year, month = currentTimeRaw.month, day = currentTimeRaw.day, hour = currentTimeRaw.hour, minute = currentTimeRaw.minute, second = currentTimeRaw.second)
        nextTime = currentTime.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
        deltaTime = int((nextTime - currentTime).total_seconds())

        # Uncomment for telemetry
        #print("Current Time:", currentTime); print("Next Time:", nextTime); print("Delta Time:", deltaTime, "seconds"); print("====================================")
        
        # Wait
        await asyncio.sleep(deltaTime)
        
        # Post server count every hour
        if nextTime.minute == 0:
            if dbl_token != "NONE":
                try:
                    await bot.topggpy.post_guild_count(shard_count = bot.shard_count)
                except Exception as e:
                    if type(e) == topgg.Unauthorized:
                        print("Unauthorized Token")
                    else:
                        print(f"Failed to post server count\n{e.__class__.__name__}: {e}")
                        
                    continue

        # Check for Birthays
        if nextTime.hour == 8 and nextTime.minute == 0: # Run at 8:00 AM every day
            await checkForBirthdays()
        
        # Check for levels
        if nextTime.hour == 0 and nextTime.minute == 1: # Run at midnight + 1
            await checkLevels()
    







# GENERAL FUNCTIONS ==========================================================================================================================================================================
async def sendErrorMessageToOwner(guild: nextcord.Guild, permission, message = None, administrator = True, channel = None, guild_permission = False):
    """|coro|
    
    Sends an error message to the owner of the server via dm

    ------
    Parameters
    ------
    guild: `nextcord.Guild` 
        The guild in which the error occured.
    permission: `str`
        The permission needed.

    Optional Parameters
    ------
    message: `str`
        A custom message to send (the opt out info is appended to this). Defaults to None.
    administrator: `bool`
        Whether to include info about giving InfiniBot adminstrator. Defaults to True.
    channel: `str`
        The channel where the permission is needed. Defaults to None (meaning the message says "one or more channels").
    guild_permission: `bool`
        Whether the permission is a guild permission. If so, channel (↑) is overwritten. Defaults to False.

    Returns
    ------
        `None`
    """
    
    if not guild: return
    
    member = guild.owner
    
    if member == None: return
    member_settings = Member(member.id)
    if not member_settings.dms_enabled: return
    
    if channel != None:
        channels = channel
    else:
        channels = "one or more channels"
        
    if guild_permission:
        inChannels = ""
    else:
        inChannels = f" in {channels}"
        
    
    
    if message == None:
        if permission != None: 
            embed = nextcord.Embed(title = f"Missing Permissions in in \"{guild.name}\" Server", description = f"InfiniBot is missing the **{permission}** permission{inChannels}.\n\nWe advise that you grant InfiniBot administrator privileges so that this is no longer a concern.", color = nextcord.Color.red())
        else:
            embed = nextcord.Embed(title = f"Missing Permissions in \"{guild.name}\" Server", description = f"InfiniBot is missing a permission{inChannels}.\n\nWe advise that you grant InfiniBot administrator privileges so that this is no longer a concern.", color = nextcord.Color.red())
    else:
        embed = nextcord.Embed(title = f"Missing Permissions in \"{guild.name}\" Server", description = f"{message}", color = nextcord.Color.red())

    embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
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
    """|coro|
    
    Get a text channel that InfiniBot can send messages and embeds in.
    
    ------
    Parameters
    ------
    guild: `nextcord.Guild`
        The guild in which to check.
    
    Returns
    ------
    Optional [`Nextcord.TextChannel`]
        Returns a `Text Channel` if found, else returns `None`.
    """
    
    if not guild or guild.unavailable: return None
    
    if guild.system_channel: 
        if await checkTextChannelPermissions(guild.system_channel, True, custom_channel_name = f"System Channel ({guild.system_channel.name})"):
            return guild.system_channel
        else:
            return None
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
    """|coro|
    
    Check to see if InfiniBot Mod role exists. If not, create it.

    ------
    Parameters
    ------
    guild: `nextcord.Guild`
        The guild in which to check.
        
    Returns
    ------
    `bool`
        True if the role was created. False if it already existed, another script was running, or failed.
    """
    
    global guildsCheckingForRole
    
    if not guild: return False
    
    roles = guild.roles
    for x in range(0, len(roles)): roles[x] = roles[x].name

    if not "Infinibot Mod" in roles:
        try:
            if not guild.id in guildsCheckingForRole:
                guildsCheckingForRole.append(guild.id)
                await guild.create_role(name = "Infinibot Mod")
                await asyncio.sleep(1)
                if guild.id in guildsCheckingForRole: guildsCheckingForRole.remove(guild.id)
                return True
            else: return False
        except nextcord.errors.Forbidden:
            if guild.id in guildsCheckingForRole: guildsCheckingForRole.remove(guild.id)
            if guild.id == 33394969196219596: return False #this is the top.gg guild id. I don't want them denying me because of dms
            await sendErrorMessageToOwner(guild, None, message = "InfiniBot is missing the **Manage Roles** permission which prevents it from creating the role *InfiniBot Mod*. Please give InfiniBot this permission.", administrator=False)
            return False
    else:
        return False
            
def getInfinibotModRoleId(guild: nextcord.Guild):
    """Get the InfiniBot Mod role's id.

    ------
    Parameters
    ------
    guild: `nextcord.Guild`
        The guild to check.

    Returns
    ------
    optional [`int`] 
        If the role is found, returns the role's id. Otherwise, returns `None`.
    """
    if guild and not guild.unavailable:
        roles = guild.roles

        for role in roles:
            if role.name == "Infinibot Mod":
                return role.id
    
    return None

def getInfinibotTopRole(guild: nextcord.Guild):
    """Returns InfiniBot's top role.

    ------
    Parameters
    ------
    guild: `nextcord.Guild`
        The guild to check for InfiniBot's role.

    Returns
    ------
    optional [`nextcord.Role`]
        If applicable, returns InfiniBot's top role. Otherwise, returns `None`.
    """    
    if guild and not guild.unavailable:
        return guild.me.top_role
    else:
        return None

def canAssignRole(role: nextcord.Role):
    """Determins if InfiniBot can assign a role

    ------
    Parameters
    ------
    role: `nextcord.Role`
        The role to check for

    Returns
    ------
    `bool`
        True if assignable, False if not.
    """    
    if role.is_default(): return False
    if role.is_integration(): return False
    
    return role.is_assignable()   
    
async def hasRole(interaction: Interaction, notify = True):
    """|coro|
    
    Determins if an interaction can be continued if it is protected by InfiniBot Mod.

    ------
    Parameters
    ------
    interaction: `nextcord.Interaction`
        The interaction.
        
    Optional Parameters
    ------
    notify: optional [`bool`]
        Whether to notify the user if they fail. Defaults to True.

    Returns
    ------
    `bool`
        Whether or not the interaction can continue.
    """
    
    if interaction.guild.owner == interaction.user: return True
    
    infinibotMod_role = nextcord.utils.get(interaction.guild.roles, name='Infinibot Mod')
    if infinibotMod_role in interaction.user.roles:
        return True

    if notify: await interaction.response.send_message(embed = nextcord.Embed(title = "Missing Permissions", description = "You need to have the Infinibot Mod role to use this command.\n\nType `/help infinibot_mod` for more information.", color = nextcord.Color.red()), ephemeral = True)
    return False

async def checkIfTextChannel(interaction: Interaction):
    """|coro|
    
    Check to see if the channel that this `Interaction` was used in was a `Text Channel`.
    Notifies the user if this was not a `Text Channel`. Recommened to immediately return if this function returns False.

    ------
    Parameters
    ------
    interaction: `nextcord.Interaction`
        The interaction.

    Returns
    ------
    `bool`
        Whether or not this is a text channel.
    """    
    
    if type(interaction.channel) == nextcord.TextChannel:
        return True
    else:
        await interaction.response.send_message(embed = nextcord.Embed(title = "You can't use that here!", description = "You can only use this command in text channels.", color = nextcord.Color.red()), ephemeral=True)
        return False

def timedeltaToEnglish(td: datetime.timedelta):
    """Convert a time delta to English.

    ------
    Parameters
    ------
    td: `datetime.timedelta`
        A time delta.

    Returns
    ------
    `str`
        The time delta in English.
    """    
    
    # Get the total number of seconds in the timedelta
    total_seconds = int(td.total_seconds())

    # Compute the number of hours, minutes, and seconds
    hours, seconds = divmod(total_seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    # Create a list of strings with the appropriate units
    parts: list[str] = []
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

async def checkTextChannelPermissions(channel: nextcord.TextChannel, autoWarn: bool, custom_channel_name: str = None):
    """|coro|
    
    Ensure that InfiniBot has permissions to send messages and embeds in a channel.

    ------
    Parameters
    ------
    channel: `nextcord.TextChannel`
        The channel to check.
    autoWarn: `bool`
        Whether or not to warn the guild's owner if InfiniBot does NOT have the required permissions.
        
    Optional Parameters
    ------
    custom_channel_name: optional [`str`]
        If warning the owner, custom_channel_name specifies a specific name for the channel instead of the default channel name. Defaults to None.

    Returns
    ------
    `bool`
        Whether or not InfiniBot has permissions to send messages and embeds in the channel.
    """    
    
    if channel == None:
        return False
    
    if channel.guild == None:
        return False
    
    if channel.guild.me == None:
        return False
    
    channelName = (custom_channel_name if custom_channel_name else channel.name)
    
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

def getName(member: nextcord.Member):
    if member.discriminator != "0":
        return str(member)
    else:
        return member.name

def formatNewlinesForUser(string: str):
    '''Formats a string so that "\\n" turns into an actual new line.'''
    if not isinstance(string, str):
        return string
    
    return string.replace("\\n", "\n")

def formatNewlinesForComputer(string: str):
    '''Formats a string so that actual new lines just turn into "\\n"'''
    if not isinstance(string, str):
        return string
    
    return string.replace("\n", "\\n")







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






# Dashboard, Profile, and Onboarding
@bot.slash_command(name = "dashboard", description = "Configure InfiniBot (Requires Infinibot Mod)", dm_permission=False)
async def dashboard(interaction: Interaction):
    if await hasRole(interaction):
        view = Dashboard(interaction)
        await view.setup(interaction)
    
@bot.slash_command(name = "profile", description = "Configure Your Profile In InfiniBot")
async def profile(interaction: Interaction):
    view = Profile()
    await view.setup(interaction)

@bot.slash_command(name = "onboarding", description = "Configure InfiniBot for the first time (Requires InfiniBot Mod)")
async def onboarding(interaction: Interaction):
    if await hasRole(interaction):
        view = Onboarding()
        await view.setup(interaction)





#Moderation Bot Functionality --------------------------------------------------------------------------------------------------------------
# General
async def canModerate(interaction: Interaction, server: Server_DEP):
    """Runs a check whether moderation is active. NOT SILENT!"""
    if utils.enabled.ProfanityModeration(server = server):
        return True
    else:
        if not global_kill_status.global_kill_profanity_moderation:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Moderation Tools Disabled", description = "Moderation has been turned off. Type \"/enable moderation\" to turn it back on.", color = nextcord.Color.red()), ephemeral = True)
            return False
        else:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Moderation Tools Disabled", description = "Moderation has been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
            return False


# Profanity Moderation -------------------------------
async def timeout(member: nextcord.Member, time: str, reason: str = None):
    """|coro|
    
    Handles the timing out of a member.

    ------
    Parameters
    ------
    member: `nextcord.Member`
        The member to time out.
    time: `str`
        The timeout time. Must be in `humanfriendly` format.
        
    Optional Parameters
    ------
    reason: optional [`str`]
        The reason that appears in the audit log. Defaults to None.

    Returns
    ------
    optional [`True` | `Exception`]
        True if the timeout was successful, `Exception` if there was an issue.
    """    
    try:
        time = humanfriendly.parse_timespan(time)
        if time == 0.0: 
            await member.edit(timeout=None, reason = reason)
        else:
            await member.edit(timeout=nextcord.utils.utcnow()+datetime.timedelta(seconds=time), reason = reason)
        
        return True
    except Exception as error:
        return error

# Add or remove strikes, grant timeouts
async def giveStrike(guild_id, userID, amount: int, server = None, strike_data = None):
    """|coro|
    
    Handle giving or taking a strike to/from a member.
    
    Note: This will grant timeouts.

    ------
    Parameters
    ------
    guild_id : `int`
        The guild id that you are in.
    userID : `int`
        The id of the user to give/take a strike to/from.
    amount : `int`
        Positive or negative number of strikes to give/take.
        
    Returns
    ------
    `int`
        The user's strikes now.
    """
    # Get the current user's strikes
    server = Server_DEP(guild_id)
    strike_data = server.getStrike(userID)
    
    # Add or Remove the strike
    if amount != 0:
        strike_data.change_strike(amount)
        server.saveStrikes()
        
    # Check if they should be timed out
    if (strike_data.strike >= server.max_strikes) and (strike_data.strike != 0) and (amount > 0):
        # They are beyond the strike limit
        # And they are above 0
        # And we were adding strikes (as opposed to removing them)
        # YES. PUNNISH THEM!
        
        # Check Permissions        
        if not server.guild.me.guild_permissions.moderate_members:
            await sendErrorMessageToOwner(server.guild, "Timeout Members", guild_permission = True)
            return strike_data.strike
        
        # Time them out.
        reason = (f"Profanity Moderation: User exceeded strike limit of {server.max_strikes}." if (server.max_strikes != 0) else "Profanity Moderation")
        response = await timeout(strike_data.member, server.profanity_timeout_time, reason = reason)
            
        if response == True:
            # The user was successfully timed out. Let's remove that strike now.
            strike_data.set_strike(0)
            server.saveStrikes()
        
        else:
            if isinstance(response, nextcord.errors.Forbidden):
                await server.admin_channel.send(embed = nextcord.Embed(title = "Timeout Error", description = f"Failed to timeout {strike_data.member} for {server.profanity_timeout_time}. \n\nError: Member is of a higher rank than InfiniBot", color = nextcord.Color.red()))
            else:
                await server.admin_channel.send(embed = nextcord.Embed(title = "Timeout Error", description = f"Failed to timeout {strike_data.member} for {server.profanity_timeout_time}. \n\nError: {response}", color = nextcord.Color.red()))
        

    return strike_data.strike

# Check a server for strike expirations and rectify them
async def checkForExpiration(server: Server_DEP):
    '''Check All Strikes in the Server for Expiration'''
    if not utils.enabled.ProfanityModeration(server = server): return
    if server.strike_expire_time == None or server.strike_expire_time == 0: return
    if server.max_strikes == 0: return
    
    for strike in server.strikes:
        try:
            referenceDate = datetime.datetime.strptime(strike.last_strike, f"%Y-%m-%d")
            currentDate = datetime.datetime.today()
            
            dayDelta = (currentDate - referenceDate).days

            if int(dayDelta) >= int(server.strike_expire_time):
                compensate = int(math.floor(int(dayDelta) / int(server.strike_expire_time)))
                await giveStrike(server.guild_id, strike.member_id, 0 - compensate)
                
        except Exception as err:
            print("Error when checking for expiration: " + str(err))

# Check edge-cases for profanity given a string and database of words
def isProfanity(message_split: list[str], database: list[str]):
    message_split = [x.lower() for x in message_split]
    database = [x.lower() for x in database]

    for word in message_split:
        if word == "he'll": continue
        word = ''.join(filter(str.isalnum, word))
        for db_word in database:
            if word == db_word: return word
            if word == db_word + "s": return word
            if word == db_word + "er": return word
            if word == db_word + "ers": return word
            if word == db_word + "ing": return word
            if word == db_word + "ed": return word
            if word == db_word + "y": return word
            if word == db_word + "or": return word
            if word == db_word + "ness": return word
            if word == db_word + "tion": return word
            if word == db_word + "sion": return word
            if word == db_word + "ship": return word
            if word == db_word + "ment": return word
            if word == "mother" + db_word: return word
            if word == "mother" + db_word + "er": return word
            if word == "mother" + db_word + "ers": return word
            if word == db_word: return word
            
    return None

# Confirm that a nickname is not in violation of profanity
async def checkNickname(guild: nextcord.Guild, before: nextcord.Member, after: nextcord.Member):
    """Check to ensure that the edited nickname is in compliance with moderation"""
    
    member = after
    nickname = after.nick
    
    if member.guild_permissions.administrator: return
    
    server = Server_DEP(guild.id)
    
    if not utils.enabled.ProfanityModeration(server = server): return

    nicknameSplit = nickname.split(" ")
    result = isProfanity(nicknameSplit, server.profane_words)
    if result != None:
        # They are in violation. Let's try to change their nickname back
        try:
            await member.edit(nick = before.nick)
        except nextcord.errors.Forbidden:
            await sendErrorMessageToOwner(guild = guild, permission = "Manage Nicknames", guild_permission = True, )
        
        # Give them a strike (or timeout)
        strikes = await giveStrike(guild.id, member.id, 1)
        
        # DM them
        if strikes == 0: strikes_info = f"\n\nYou were timed out for {server.profanity_timeout_time}"
        else: strikes_info = f"\n\nYou are now at strike {strikes} / {server.max_strikes}"
        
        embed = nextcord.Embed(title = "Profanity Detected", description = f"You were flagged for your nickname.\n\n**Server**: {guild.name}\n**Nickname:** {nickname}{strikes_info}", color = nextcord.Color.dark_red())
        embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
        await member.send(embed = embed)

        # Send a message to the admin channel
        if server.admin_channel == None:
            return
        else:
            view = IncorrectButton()
            if strikes == 0: strikes_info = f"\n\n{member.mention} was timed out for {server.profanity_timeout_time} and is now at strike {strikes}."
            else: strikes_info = f"\n\n{member.mention} is now at strike {strikes} / {server.max_strikes}"
            embed =  nextcord.Embed(title = "Profanity Detected", description = f"{member.mention} was flagged for their nickname of \"{nickname}\".{strikes_info}", color = nextcord.Color.dark_red())
            embed.set_footer(text = f"Member ID: {str(member.id)}")
            await server.admin_channel.send(view = view, embed = embed)

# RAN FOR EVERY MESSAGE. Ties profanity moderation together
async def checkProfanity(server: Server_DEP, message: nextcord.Message):
    global auto_deleted_message_time
    
    # Checks
    if not utils.enabled.ProfanityModeration(server = server): return
    if message.channel.type != nextcord.ChannelType.stage_voice and message.channel.is_nsfw(): return
    # Sometimes, the member is not a member of the guild for some reason. Let's rule that out.
    if not isinstance(message.author, nextcord.Member): return
    if message.author.guild_permissions.administrator: return
    
    # Message Content
    msg = message.content.lower()
    message_split = msg.split(" ")

    # Ignore if the message is nothing, or if it is actually just a slash command
    if len(msg) == 0 or msg[0] == "/":
        await bot.process_commands(message)
        return
    
    # Check for profanity -------------------------------------------------------------------
    result = isProfanity(message_split, server.profane_words)
    if result != None:
        #if they are in violation and need to be punnished...
        # Give them a strike (and perhaps a timeout)
        strikes = await giveStrike(message.guild.id, message.author.id, 1)
        
        # DM them (if they want)
        memberSettings = Member(message.author.id)
        if memberSettings.dms_enabled:
            try:
                dm = await message.author.create_dm()
                
                # Check if they were timed out, or if it's just a strike
                if strikes == 0:
                    # They were timed out. Tell them.
                    embed = nextcord.Embed(title = "Profanity Log", description = f"You were flagged for profanity.\n\n**Server:** {message.guild.name}\n**Word:** {result}\n**Message:** {message.content}\n\nYou were timed out for {server.profanity_timeout_time}.", color = nextcord.Color.red(), timestamp = datetime.datetime.now())
                    embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
                    await dm.send(embed = embed)
                    
                else:
                    # It was just a strike. Tell them.
                    embed = nextcord.Embed(title = "Profanity Log", description = f"You were flagged for profanity.\n\n**Server:** {message.guild.name}\n**Word:** {result}\n**Message:** {message.content}\n\nYou are now at strike {strikes} / {server.max_strikes}.", color = nextcord.Color.red(), timestamp = datetime.datetime.now())
                    embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
                    await dm.send(embed = embed)
                    
            except:
                pass #the user has dms turned off. It's not a big deal, they just don't get notified.
        
        # Send message in channel where bad word was sent.
        if await checkTextChannelPermissions(message.channel, True):
            embed = nextcord.Embed(title = "Profanity Detected", description = f"{message.author.mention} was flagged for profanity. The message was automatically deleted.\n\nContact a server admin for more info.", color = nextcord.Color.dark_red())
            await message.channel.send(embed = embed, view = InviteView(), delete_after = 10.0)
        
        # Send message to admin channel (if enabled)
        if server.admin_channel != None:
            if server.admin_channel and await checkTextChannelPermissions(server.admin_channel, True, custom_channel_name = f"Admin Channel (#{server.admin_channel.name})"):
                view = IncorrectButton()

                timeout_message = (f" was timed out for {server.profanity_timeout_time} and" if (strikes == 0 and server.max_strikes != 0) else "")
                strikes_message = (f"{message.author.mention}{timeout_message} is now at strike {strikes} / {server.max_strikes}." if server.max_strikes != 0 else "")
                
                embed = nextcord.Embed(title = "Profanity Detected", description = f"{message.author.mention} was flagged for profanity.\n\n**Word:** {result}\n**Message:** {message.content}\n\**Channel**: {message.channel.mention}n\nThis message was automatically deleted.\n\n{strikes_message}", color = nextcord.Color.dark_red(), timestamp = datetime.datetime.now())
                embed.set_footer(text = f"Member ID: {str(message.author.id)}")
                
                await server.admin_channel.send(view = view, embed = embed)

            
        # Delete the message
        auto_deleted_message_time = datetime.datetime.now(datetime.timezone.utc)
        
        try:
            await message.delete()
        except nextcord.errors.Forbidden:
            await sendErrorMessageToOwner(message.guild, "Manage Messages", channel = message.channel.name)


# Spam Moderation -------------------------------
# Checks for repeated words given a string
def checkRepeatedWordsPercentage(text, threshold=0.7):
    words = re.findall(r'\w+', text.lower())  # Convert text to lowercase and extract words
    counts = defaultdict(lambda: 0)  # Dictionary to store word counts
    
    # Remove symbols from the words
    words = [re.sub(r'\W+', '', word) for word in words]

    # Iterate over the words and count their occurrences
    last_words = []
    for word in words:
        if word not in last_words:
            counts[word] += 0.5
        else:
            counts[word] += 1
        last_words.insert(0, word)
        if len(last_words) >= 5:
            last_words.pop(3)
        
    # Calculate the total number of words and the number of repeated words
    total_words = len(words)
    if total_words == 0: return False
    repeated_words = sum(count for count in counts.values() if count > 0.5)

    # Calculate the percentage of repeated words
    repeated_percentage = repeated_words / total_words

    # Check if the percentage exceeds the threshold
    return repeated_percentage >= threshold

# Compares attatchments given two attachments
def compareAttachments(attachments_1: List[nextcord.Attachment], attachments_2: List[nextcord.Attachment]):
        # quick optimizations
        if not attachments_1 or not attachments_2:
            return False
        if attachments_1 == attachments_2:
            return True

        for attachment_1 in attachments_1:
            for attachment_2 in attachments_2:
                if (
                    attachment_1.url == attachment_2.url
                    or (
                        attachment_1.filename == attachment_2.filename
                        and attachment_1.width == attachment_2.width
                        and attachment_1.height == attachment_2.height
                        and attachment_1.size == attachment_2.size
                    )
                ):
                    return True
        return False

# RAN FOR EVERY MESSAGE. Ties spam moderation together
async def checkSpam(message: nextcord.Message, server: Server_DEP):
    MAX_MESSAGES_TO_CHECK = 11    # The MAXIMUM messages InfiniBot will try to check for spam
    MESSAGE_CHARS_TO_CHECK_REPETITION = 140    # A message requires these many characters before it is checked for repetition

    # If Spam is Enabled
    if not utils.enabled.SpamModeration(server = server): return
    
    # Checks
    if message.author.guild_permissions.administrator: return
    
    # Check if we can view the audit log
    if not message.guild.me.guild_permissions.view_audit_log:
        await sendErrorMessageToOwner(message.guild, "View Audit Log", channel=message.channel.name)
        return

    # Configure limit (the most messages that we're willing to check)
    if server.messages_threshold < MAX_MESSAGES_TO_CHECK:
        limit = server.messages_threshold + 1 # Add one because of the existing message
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
            timeNow = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds = 2 * server.messages_threshold) # ======= Time Threshold =========
            timeNow = timeNow.replace(tzinfo=datetime.timezone.utc)  # Make timeNow offset-aware
            
            # If the message is within the time threshold window, add that message.
            if _message.created_at >= timeNow:
                duplicateMessages.append(_message)
            else:
                # If this message was outside of the time window, previous messages will also be, so this loop can stop
                break


    # Punnish the member (if needed)
    if len(duplicateMessages) >= server.messages_threshold:
        try:
            # Time them out
            await timeout(message.author, server.spam_timeout_time, reason=f"Spam Moderation: User exceeded spam message limit of {server.messages_threshold}.")
            
            # Send them a message (if they want it)
            if Member(message.author.id).dms_enabled:
                dm = await message.author.create_dm()
                await dm.send(
                    embed=nextcord.Embed(
                        title="Spam Timeout",
                        description=f"You were flagged for spamming in \"{message.guild.name}\". You have been timed out for {server.spam_timeout_time}.\n\nPlease contact the admins if you think this is a mistake.",
                        color=nextcord.Color.red(),
                    )
                )
        except nextcord.errors.Forbidden:
            await sendErrorMessageToOwner(message.guild, "Timeout Members", guild_permission=True)


# Commands -------------------------------
@bot.slash_command(name = "my_strikes", description = "View your strikes", dm_permission=False)
async def mystrikes(interaction: Interaction):
    server = Server_DEP(interaction.guild.id)
    if not await canModerate(interaction, server): return

    theirStrike = server.getStrike(interaction.user.id)
    await interaction.response.send_message(embed = nextcord.Embed(title = f"Strikes - {interaction.user}", description = f"You are at {str(theirStrike.strike)} strike(s)", color =  nextcord.Color.blue()))

@bot.slash_command(name = "view_strikes", description = "View another member's strikes. (Requires Infinibot Mod)", dm_permission=False)
async def viewstrikes(interaction: Interaction, member: nextcord.Member):
    if await hasRole(interaction):
        server = Server_DEP(interaction.guild.id)
        if not await canModerate(interaction, server): return

        theirStrike = server.getStrike(member.id)
        await interaction.response.send_message(embed = nextcord.Embed(title = f"Strikes - {member}", description = f"{member} is at {str(theirStrike.strike)} strike(s).\n\nAction done by {interaction.user}", color =  nextcord.Color.blue()))

@set.subcommand(name = "admin_channel", description = "Use this channel to log strikes. Channel should only be viewable by admins. (Requires Infinibot Mod)")
async def setAdminChannel(interaction: Interaction):
   if await hasRole(interaction) and await checkIfTextChannel(interaction):
        server = Server_DEP(interaction.guild.id)

        server.admin_channel = interaction.channel
        server.saveData()


        await interaction.response.send_message(embed = nextcord.Embed(title = "Admin Channel Set", description = f"Strikes will now be logged in this channel.\n**IMPORTANT: MAKE SURE THAT THIS CHANNEL IS ONLY ACCESSABLE BY ADMINS!**\nThis channel will allow members to mark strikes as incorrect. Thus, you only want admins to see it.\n\nAction done by {interaction.user}", color =  nextcord.Color.green()), view = SupportAndInviteView())
#END OF MODERATION BOT FUNCTIONALITY -----------------------------------------------------------------------------------------------------------------------------------------------------






#Music Bot Functionality ----------------------------------------------------------------------------------------------------------------------
if False:
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



    async def canPlayMusic(interaction: Interaction, server: Server_DEP):
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

    @bot.slash_command(name = "play", description = "Play any song from YouTube", dm_permission=False)
    async def play(interaction: Interaction, music: str = SlashOption(description = "Can be a url or a search query")):
        server = Server_DEP(interaction.guild.id)
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

    @bot.slash_command(name = "skip", description="Skip the current song", dm_permission=False)
    async def skip(interaction: Interaction):
        server = Server_DEP(interaction.guild.id)
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

    @bot.slash_command(name = "leave", description = "Leave the current voice channel and clear queue", dm_permission=False)
    async def leave(interaction: Interaction):
        server = Server_DEP(interaction.guild.id)
        if not await canPlayMusic(interaction, server): return
        
        serverData = musicQueue.getData(interaction.guild_id)

        if serverData.vc == None:
            await interaction.response.send_message(embed = nextcord.Embed(title = "No Music in Queue", description = "Type /play [music] to play something", color = nextcord.Color.red()), ephemeral = True)
            return

        await stopVC(serverData, serverData.vc)
        await interaction.response.send_message(embed = nextcord.Embed(title = "Left voice channel", description = f"Action done by {interaction.user}", color = nextcord.Color.orange()))

    @bot.slash_command(name = "stop", description = "Leave the current voice channel and clear queue", dm_permission=False)
    async def stop(interaction: Interaction):
        await leave(interaction)

    @bot.slash_command(name = "clear", description = "Clears all music in queue except for the current song", dm_permission=False)
    async def clear(interaction: Interaction):
        server = Server_DEP(interaction.guild.id)
        if not await canPlayMusic(interaction, server): return
        
        serverData = musicQueue.getData(interaction.guild_id)

        if serverData.vc == None:
            await interaction.response.send_message(embed = nextcord.Embed(title = "No Music in Queue", description = "Type /play [music] to play something", color = nextcord.Color.red()), ephemeral = True)
            return
        
        for x in range(1, len(serverData.queue)):
            serverData.deleteSong(1) #index is one because after we delete a song, the next songs shift up, so by always deleting one, we delete all the songs exept for song [0]

        await interaction.response.send_message(embed = nextcord.Embed(title = "Queue Cleared", description = f"Action done by {interaction.user}", color = nextcord.Color.orange()))

    @bot.slash_command(name = "queue", description = "Display the current queue", dm_permission=False)
    async def queue(interaction: Interaction):
        server = Server_DEP(interaction.guild.id)
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

    @bot.slash_command(name = "pause", description = "Pause the current song", dm_permission=False)
    async def pause(interaction: Interaction):
        server = Server_DEP(interaction.guild.id)
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

    @bot.slash_command(name = "resume", description = "Resume the current song", dm_permission=False)
    async def resume(interaction: Interaction):
        server = Server_DEP(interaction.guild.id)
        if not await canPlayMusic(interaction, server): return
        
        serverData = musicQueue.getData(interaction.guild_id)

        if serverData.paused == True:
            serverData.playing = True
            serverData.paused = False
            serverData.vc.resume()
            await interaction.response.send_message(embed = nextcord.Embed(title = "Resumed Current Song and Queue", description = f"Action done by {interaction.user}", color = nextcord.Color.green()))

        else:
            await interaction.response.send_message(embed = nextcord.Embed(title = "No music playing", description = "Type /play [music] to play something", color = nextcord.Color.red()), ephemeral = True)

    @bot.slash_command(name = "volume", description = "Get the volume or set the volume to any number between 0 and 100", dm_permission=False)
    async def volume(interaction: Interaction, volume: int = SlashOption(description = "Must be a number between 0 and 100", required = False)):
        server = Server_DEP(interaction.guild.id)
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

    @bot.slash_command(name = "loop", description = "Loop / un-loop the current song", dm_permission=False)
    async def loop(interaction: Interaction):
        server = Server_DEP(interaction.guild.id)
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
    if not utils.enabled.Votes(guild_id = interaction.guild.id):
        await interaction.response.send_message(embed = nextcord.Embed(title = "Votes Disabled", description = "Votes have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
        return
        
    modal = VotingModal(interaction, type)
        
    await interaction.response.send_modal(modal)
       
@create.subcommand(name = "custom_vote", description = "Automatically create a vote that you can customize with emojis.")
async def customVoteCommand(interaction: Interaction, options: str = SlashOption(description = "Format: \"😄 = Yes, 😢 = No\"")):
    if not utils.enabled.Votes(guild_id = interaction.guild.id):
        await interaction.response.send_message(embed = nextcord.Embed(title = "Votes Disabled", description = "Votes have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
        return
    
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
                reaction, letter_used = asci_to_emoji(letter, fallback_letter = getNextOpenLetter(addedOptions_Asci))
                reactionsFormatted += "\n" + reaction + " " + option
                addedOptions_Asci.append(letter_used.lower())
                addedOptions_Emojis.append(reaction)
            else:
                letter = getNextOpenLetter(addedOptions_Asci)
                reaction, letter_used = asci_to_emoji(letter)
                reactionsFormatted += "\n" + reaction + " " + option
                addedOptions_Asci.append(letter_used.lower())
                addedOptions_Emojis.append(reaction) 
                
        elif _type == "Numbers":
            letter = option[0]
            reaction, letter_used = asci_to_emoji(counter)
            reactionsFormatted += "\n" + reaction + " " + option
            addedOptions_Asci.append(letter_used.lower())
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
    server = Server_DEP(interaction.guild.id);
    server.messages.add("Vote", interaction.channel.id, partialMessage.id, interaction.user.id)
    server.messages.save()

def asci_to_emoji(letter, fallback_letter = "1"):
    letter = str(letter)
    letter = letter.lower()

    if letter == "a": return "🇦", "a"
    if letter == "b": return "🇧", "b"
    if letter == "c": return "🇨", "c"
    if letter == "d": return "🇩", "d"
    if letter == "e": return "🇪", "e"
    if letter == "f": return "🇫", "f"
    if letter == "g": return "🇬", "g"
    if letter == "h": return "🇭", "h"
    if letter == "i": return "🇮", "i"
    if letter == "j": return "🇯", "j"
    if letter == "k": return "🇰", "k"
    if letter == "l": return "🇱", "l"
    if letter == "m": return "🇲", "m"
    if letter == "n": return "🇳", "n"
    if letter == "o": return "🇴", "o"
    if letter == "p": return "🇵", "p"
    if letter == "q": return "🇶", "q"
    if letter == "r": return "🇷", "r"
    if letter == "s": return "🇸", "s"
    if letter == "t": return "🇹", "t"
    if letter == "u": return "🇺", "u"
    if letter == "v": return "🇻", "v"
    if letter == "w": return "🇼", "w"
    if letter == "x": return "🇽", "x"
    if letter == "y": return "🇾", "y"
    if letter == "z": return "🇿", "z"
    if letter == "1": return "1️⃣", "1"
    if letter == "2": return "2️⃣", "2"
    if letter == "3": return "3️⃣", "3"
    if letter == "4": return "4️⃣", "4"
    if letter == "5": return "5️⃣", "5"
    if letter == "6": return "6️⃣", "6"
    if letter == "7": return "7️⃣", "7"
    if letter == "8": return "8️⃣", "8"
    if letter == "9": return "9️⃣", "9"
    if letter == "0": return "0️⃣", "0"

    return asci_to_emoji(fallback_letter)

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
@create.subcommand(name = "reaction_role", description = "Legacy: Create a message allowing users to add/remove roles by themselves. (Requires Infinibot Mod)")
async def reactionRoleCommand(interaction: Interaction, type: str = SlashOption(choices = ["Letters", "Numbers"]), mentionRoles: bool = SlashOption(name = "mention_roles", description = "Mention the roles with @mention", required = False, default = True)):
    if await hasRole(interaction):
        if not utils.enabled.ReactionRoles(guild_id = interaction.guild.id):
            await interaction.response.send_message(embed = nextcord.Embed(title = "Reaction Roles Disabled", description = "Reaction Roles have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
            return
        
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
    
@create.subcommand(name = "custom_reaction_role", description = "Legacy: Create a reaction role with customized emojis. (Requires Infinibot Mod)")
async def customReactionRoleCommand(interaction: Interaction, options: str = SlashOption(description = "Format: \"👍 = @Member, 🥸 = @Gamer\""), mentionRoles: bool = SlashOption(name = "mention_roles", description = "Mention the roles with @mention", required = False, default = True)):   
    if await hasRole(interaction):
        if not utils.enabled.ReactionRoles(guild_id = interaction.guild.id):
            await interaction.response.send_message(embed = nextcord.Embed(title = "Reaction Roles Disabled", description = "Reaction Roles have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
            return
        
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
                reaction, letter_used = asci_to_emoji(letter, fallback_letter = getNextOpenLetter(addedOptions_Asci))
                reactionsFormatted += "\n" + reaction + " " + (role.mention if mentionRoles else role.name)
                addedOptions_Asci.append(letter_used.lower())
                addedOptions_Emojis.append(reaction)
            else:
                letter = getNextOpenLetter(addedOptions_Asci)
                reaction, letter_used = asci_to_emoji(letter)
                reactionsFormatted += "\n" + reaction + " " + (role.mention if mentionRoles else role.name)
                addedOptions_Asci.append(letter_used.lower())
                addedOptions_Emojis.append(reaction)
        elif _type == "Numbers":
            letter = role.name[0]
            reaction, letter_used = asci_to_emoji(count)
            reactionsFormatted += "\n" + reaction + " " + (role.mention if mentionRoles else role.name)
            addedOptions_Asci.append(letter_used.lower())
            addedOptions_Emojis.append(reaction)
            count += 1
        else:
            index = roles.index(role)
            emoji = emojis[index].strip()
            reactionsFormatted += "\n" + emoji + " " + (role.mention if mentionRoles else role.name)
            addedOptions_Emojis.append(emoji)
            
    return reactionsFormatted, addedOptions_Emojis

async def createReactionRole(interaction: Interaction, title: str, message: str, rolesStr: list[str], _type: str, mentionRoles: bool):
    if not interaction.guild: 
        print("Guild is \"not\" for some reason: createReactionRole")
        return
    if interaction.guild == None:
        print("Guild is equal to None for some reason: createReactionRole")
        return
      
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
            infinibotRole = getInfinibotTopRole(interaction.guild)
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
    server = Server_DEP(interaction.guild.id);
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
            if len(message.embeds[0].fields) >= 1 and message.embeds[0].fields[0].name.lower().startswith("react"): # This message IS a reaction role
                # Can we manage roles? If not, there's not point to any of this
                if not message.channel.permissions_for(guild.me).manage_roles:
                    await sendErrorMessageToOwner(guild, "Manage Roles", guild_permission = True)
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






#Start of role messages functionality: ----------------------------------------------------------------------------------------------------------------------------------------
class RoleMessageSetup(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        nevermindBtn = self.NevermindButton(self)
        self.add_item(nevermindBtn)
        
        getStartedBtn = self.GetStartedButton()
        self.add_item(getStartedBtn)
        
    async def setup(self, interaction: Interaction):
        if utils.enabled.RoleMessages(guild_id = interaction.guild.id):
            embed = nextcord.Embed(title = "Role Message Creation Wizard", description = "We will guide you through the process of creating a custom message that enables users to assign themselves roles.\n★ Unlike reaction roles, this method utilizes a modern interface.\n\n**Click on \"Get Started\" to initiate the process!**", color = nextcord.Color.green())
            await interaction.response.send_message(embed = embed, view = self, ephemeral = True)
        else:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Role Messages Disabled", description = "Role Messages have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
        
    class NevermindButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Nevermind", style = nextcord.ButtonStyle.gray)
            self.outer = outer
            
        async def callback(self, interaction: Interaction):
            for child in self.outer.children:
                if isinstance(child, nextcord.ui.Button):
                    child.disabled = True
                    
            await interaction.response.edit_message(view = self.outer)
        
    class GetStartedButton(nextcord.ui.Button):
        def __init__(self):
            super().__init__(label = "Get Started", style = nextcord.ButtonStyle.blurple)
            
        class Modal(nextcord.ui.Modal):
            def __init__(self):
                super().__init__(title = "Role Message Creation Wizard", timeout = None)
                
                self.titleInput = nextcord.ui.TextInput(label = "To begin, please add a Title", max_length = "256")
                self.add_item(self.titleInput)
                
                self.descriptionInput = nextcord.ui.TextInput(label = "And then a Description (if you want)", style = nextcord.TextInputStyle.paragraph, required = False)
                self.add_item(self.descriptionInput)
                
            class RoleSelectWizardView(nextcord.ui.View):
                def __init__(self, title, description):
                    super().__init__(timeout = None)
                    self.title = title
                    self.description = description
                    self.color = nextcord.Color.teal()
                    self.options: list[list[list[int], str, str]] = []
                    
                    editTextBtn = self.EditTextButton(self)
                    self.add_item(editTextBtn)
                    
                    editColorBtn = self.EditColorButton(self)
                    self.add_item(editColorBtn)
                    
                    # Also known as "next" on the first time
                    self.addBtn = self.AddBtn(self, self.options)
                    self.add_item(self.addBtn)
                    
                    self.editBtn = self.EditBtn(self, self.options)
                    
                    self.removeBtn = self.RemoveBtn(self, self.options)
                    
                    self.finishBtn = self.FinishBtn(self)
                    
                class EditTextButton(nextcord.ui.Button):
                    def __init__(self, outer):
                        super().__init__(label = "Edit Text", emoji = "✏️")
                        self.outer = outer;
                    
                    class EditTextModal(nextcord.ui.Modal):
                        def __init__(self, outer):
                            super().__init__(title = "Edit Text")
                            self.outer = outer;
                            
                            self.titleInput = nextcord.ui.TextInput(label = "Title", min_length = 1, max_length = 256, placeholder = "Title", default_value = outer.title)
                            self.add_item(self.titleInput)
                            
                            self.descriptionInput = nextcord.ui.TextInput(label = "Description", min_length = 1, max_length = 4000, placeholder = "Description", default_value = outer.description, style = nextcord.TextInputStyle.paragraph, required = False)
                            self.add_item(self.descriptionInput)
                            
                        async def callback(self, interaction: Interaction):
                            self.stop();
                            self.outer.title = self.titleInput.value
                            self.outer.description = self.descriptionInput.value
                            
                            await self.outer.setup(interaction)
                    
                    async def callback(self, interaction: Interaction):
                        await interaction.response.send_modal(self.EditTextModal(self.outer))
                    
                class EditColorButton(nextcord.ui.Button):
                    def __init__(self, outer):
                        super().__init__(label = "Edit Color", emoji = "🎨")
                        self.outer = outer
                        
                    class EditColorView(nextcord.ui.View):
                        def __init__(self, outer):
                            super().__init__()
                            self.outer = outer;
                            
                            options = ["Red", "Green", "Blue", "Yellow", "White", "Blurple", "Greyple", "Teal", "Purple", "Gold", "Magenta", "Fuchsia"]
                            
                            originalColor = get_string_from_discord_color(self.outer.color)        
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
                            description = f"""Choose what color you would like the role message to be:
                            
                            **Colors Available**
                            Red, Green, Blue, Yellow, White
                            Blurple, Greyple, Teal, Purple
                            Gold, Magenta, Fuchsia"""
                            
                            
                            # On Mobile, extra spaces cause problems. We'll get rid of them here:
                            description = standardize_str_indention(description)
                
                            embed = nextcord.Embed(title = "Role Message Creation Wizard - Edit Color", description = description, color = nextcord.Color.green())
                            await interaction.response.edit_message(embed = embed, view = self)
                                
                        async def createCallback(self, interaction: Interaction):
                            if self.select.values == []: return
                            self.selection = self.select.values[0]
                            self.stop()
                            
                            self.outer.color = get_discord_color_from_string(self.selection)
                            
                            await self.outer.setup(interaction)
                
                        async def backCallback(self, interaction: Interaction):
                            await self.outer.setup(interaction)
                
                    async def callback(self, interaction: Interaction):
                        await self.EditColorView(self.outer).setup(interaction)
                    
                class AddBtn(nextcord.ui.Button):
                    def __init__(self, outer, options):
                        if options == []:    
                            super().__init__(label = "Next", style = nextcord.ButtonStyle.blurple)
                        else:
                            super().__init__(label = "Add Option", style = nextcord.ButtonStyle.gray, disabled = (len(options) >= 25), emoji = "🔨")
                            
                        self.outer = outer
                        self.options = options
                        
                    class AddView(nextcord.ui.View):
                        def __init__(self, outer, options, index = None):
                            super().__init__(timeout = None)
                            self.outer = outer
                            self.options = options
                            self.index = index
                            
                            if self.index == None:
                                self.title = None
                                self.description = None
                                self.roles: list[int] = []
                                self.editing = False
                            else:
                                self.title = self.options[index][1]
                                self.description = self.options[index][2]
                                self.roles: list[int] = self.options[index][0]
                                self.editing = True
                    
                            # Make roles all ints
                            self.roles = [int(role) for role in self.roles]
                            
                            changeTextBtn = nextcord.ui.Button(label = "Change Text")
                            changeTextBtn.callback = self.changeTextBtnCallback
                            self.add_item(changeTextBtn)
                            
                            self.addRoleBtn = nextcord.ui.Button(label = "Add Role")
                            self.addRoleBtn.callback = self.addRoleBtnCallback
                            self.add_item(self.addRoleBtn)
                            
                            self.removeRoleBtn = nextcord.ui.Button(label = "Remove Role")
                            self.removeRoleBtn.callback = self.removeRoleBtnCallback
                            self.add_item(self.removeRoleBtn)
                            
                            self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = (2 if len(self.outer.options) <= 1 else 1))
                            self.backBtn.callback = self.backBtnCallback
                            # Only add if this is not the first option
                            if len(self.outer.options) > 0:
                                self.add_item(self.backBtn)
                            
                            self.finishBtn = nextcord.ui.Button(label = ("Finish" if not self.editing else "Save"), style = nextcord.ButtonStyle.blurple, row = 1)
                            self.finishBtn.callback = self.finishBtnCallback
                            self.add_item(self.finishBtn)
                            
                        async def validateData(self, interaction: Interaction):
                            """Make sure you refresh the view after running this"""
                            self.addableRoles = []
                            for role in interaction.guild.roles:
                                if role.name == "@everyone": continue
                                if role.id in self.roles: continue
                                if canAssignRole(role):
                                    self.addableRoles.append(nextcord.SelectOption(label = role.name, value = role.id))
                                    
                            self.removableRoles = []
                            for role in self.roles:
                                discordRole = interaction.guild.get_role(role)
                                if discordRole:
                                    self.removableRoles.append(nextcord.SelectOption(label = discordRole.name, value = role))
                                else:
                                    self.removableRoles.append(nextcord.SelectOption(label = "~ Deleted Role ~", value = role, emoji = "⚠️"))
                                
                            # Validate buttons
                            self.addRoleBtn.disabled = len(self.addableRoles) == 0
                            self.removeRoleBtn.disabled = len(self.removableRoles) <= 1
                            
                        async def setup(self, interaction: Interaction):
                            # Validate Data
                            await self.validateData(interaction)
                            
                            if len(self.roles) == 0 and not self.editing:
                                # Send the user past this view.
                                await self.addRoleBtnCallback(interaction)
                            else:
                                if not self.editing:
                                    embed = nextcord.Embed(title = "Role Message Creation Wizard - Add Option", description = "You have the option to add more roles or make changes to the text. Here is a mockup of what this option will look like:", color = nextcord.Color.green())
                                else:
                                    embed = nextcord.Embed(title = "Role Message Creation Wizard - Edit Option", description = "You have the option to add more roles or make changes to the text. Here is a mockup of what this option will look like:", color = nextcord.Color.green())
                                
                                self.outer.addField(embed, [self.roles, self.title, self.description])
                                
                                await interaction.response.edit_message(embed = embed, view = self)
                                
                        async def addRoleBtnCallback(self, interaction: Interaction):
                            # Update Information
                            await self.validateData(interaction)
                            if self.addRoleBtn.disabled:
                                await self.setup(interaction)
                                return
                            
                            # Have 2 embeds. One for the first visit, and another for a re-visit
                            if len(self.roles) == 0:
                                embed = nextcord.Embed(title = "Role Message Creation Wizard - Add Option", description = "Please select a role. This choice will be added as one of the options.\n\n**Unable to find a role?**\nIf you are unable to find a role, please ensure that InfiniBot has the necessary permissions to assign roles, such as managing messages and having a higher rank.", color = nextcord.Color.green())
                            else:
                                embed = nextcord.Embed(title = "Role Message Creation Wizard - Add Option - Add Role", description = "Select a role to be granted when the user chooses this option.\n\n**Unable to find a role?**\nIf you are unable to find a role, please ensure that InfiniBot has the necessary permissions to assign roles, such as managing messages and having a higher rank.", color = nextcord.Color.green())
                            await SelectView(embed = embed, options = self.addableRoles, returnCommand = self.addRoleBtnSelectViewCallback, placeholder = "Choose a Role", continueButtonLabel = "Use Role").setup(interaction)
                            
                        async def addRoleBtnSelectViewCallback(self, interaction: Interaction, value: str):
                            if value == None:
                                # User canceled. Return them to us.
                                # Unless they actually came from the original view. If so, let's send them back to that.
                                if self.roles == []:
                                    await self.outer.setup(interaction)
                                    return
                                else:
                                    await self.setup(interaction)
                                    return
                                
                            if value.isdigit():
                                self.roles.append(int(value))
                            
                            # Send them to the modal, or just back home
                            if self.title == None:
                                await interaction.response.send_modal(self.OptionTitleAndDescriptionModal(self))
                            else:
                                await self.setup(interaction)
                            
                        class OptionTitleAndDescriptionModal(nextcord.ui.Modal):
                            def __init__(self, outer):
                                super().__init__(title = "Option Settings", timeout = None)
                                self.outer = outer

                                if self.outer.title == None:
                                    self.titleInput = nextcord.ui.TextInput(label = "Please provide a name for that option", max_length = 100)
                                else:
                                    self.titleInput = nextcord.ui.TextInput(label = "Option Name", max_length = 100, default_value = self.outer.title)
                                self.add_item(self.titleInput)
                                
                                if self.outer.description == None:
                                    self.descriptionInput = nextcord.ui.TextInput(label = "Add a description (optional)", max_length = 100, required = False)
                                else:
                                    self.descriptionInput = nextcord.ui.TextInput(label = "Description (optional)", max_length = 100, required = False, default_value = self.outer.description)
                                self.add_item(self.descriptionInput)
                                
                            async def callback(self, interaction: Interaction):
                                self.outer.title = self.titleInput.value
                                self.outer.description = self.descriptionInput.value
                                
                                await self.outer.setup(interaction)
                                              
                        async def changeTextBtnCallback(self, interaction: Interaction):
                            await interaction.response.send_modal(self.OptionTitleAndDescriptionModal(self))
                        
                        async def removeRoleBtnCallback(self, interaction: Interaction): 
                            # Update Information
                            await self.validateData(interaction)
                            if self.removeRoleBtn.disabled:
                                await self.setup(interaction)
                                return
                            
                            embed = nextcord.Embed(title = "Role Message Creation Wizard - Add Option - Remove Role", description = "Choose a role to be removed from this option.", color = nextcord.Color.green())
                            await SelectView(embed = embed, options = self.removableRoles, returnCommand = self.removeRoleBtnSelectViewCallback, placeholder = "Choose a Role", continueButtonLabel = "Remove Role").setup(interaction)
                            
                        async def removeRoleBtnSelectViewCallback(self, interaction: Interaction, value: str):
                            if value == None:
                                await self.setup(interaction)
                                return
                                
                            if value.isdigit() and int(value) in self.roles:
                                self.roles.remove(int(value))
                            
                            await self.setup(interaction)
                          
                        async def backBtnCallback(self, interaction: Interaction):
                            await self.outer.setup(interaction)
                                                                      
                        async def finishBtnCallback(self, interaction: Interaction):
                            if not self.editing:
                                # Add data to self.outer.options in the form of list[list[int], str, str]
                                self.outer.options.append([self.roles, self.title, self.description])
                            else:
                                self.outer.options[self.index] = [self.roles, self.title, self.description]
                            
                            await self.outer.setup(interaction)
                                         
                    async def callback(self, interaction: Interaction):
                        await self.AddView(self.outer, self.options).setup(interaction)
                
                class EditBtn(nextcord.ui.Button):
                    def __init__(self, outer, options):
                        super().__init__(label = "Edit Option", emoji = "⚙️")
                        self.outer = outer
                        self.options: list[list[list[int], str, str]] = options
                        
                    async def callback(self, interaction: Interaction):
                        # Get the options
                        selectOptions = []
                        for index, option in enumerate(self.options):
                            selectOptions.append(nextcord.SelectOption(label = option[1], description = option[2], value = index))
                        
                        embed = nextcord.Embed(title = "Role Message Creation Wizard - Edit Option", description = "Choose an option to edit", color = nextcord.Color.green())
                        await SelectView(embed = embed, options = selectOptions, returnCommand = self.selectViewCallback, continueButtonLabel = "Edit", preserveOrder = True).setup(interaction)
                    
                    async def selectViewCallback(self, interaction, selection):
                        if selection == None:
                            await self.outer.setup(interaction)
                            return
                            
                        # Send them to the editing
                        await self.outer.AddBtn.AddView(self.outer, self.options, index = int(selection)).setup(interaction)
      
                class RemoveBtn(nextcord.ui.Button):
                    def __init__(self, outer, options):
                        super().__init__(label = "Remove Option", disabled = (len(options) <= 1), emoji = "🚫")
                        self.outer = outer
                        self.options: list[list[list[int], str, str]] = options
                        
                    async def callback(self, interaction: Interaction):
                        # Get the options
                        selectOptions = []
                        for index, option in enumerate(self.options):
                            selectOptions.append(nextcord.SelectOption(label = option[1], description = option[2], value = index))
                        
                        embed = nextcord.Embed(title = "Edit Role Message - Remove Option", description = "Choose an option to remove", color = nextcord.Color.yellow())
                        await SelectView(embed = embed, options = selectOptions, returnCommand = self.selectViewCallback, continueButtonLabel = "Remove", preserveOrder = True).setup(interaction)
                    
                    async def selectViewCallback(self, interaction, selection):
                        if selection == None:
                            await self.outer.setup(interaction)
                            return
                            
                        self.outer.options.pop(int(selection))
                        
                        await self.outer.setup(interaction)
  
                class FinishBtn(nextcord.ui.Button):
                    def __init__(self, outer):
                        super().__init__(label = "Finish", style = nextcord.ButtonStyle.blurple, row = 1, emoji = "🏁")
                        self.outer = outer
                        
                    class MultiOrSingleSelectView(nextcord.ui.View):
                        def __init__(self, outer):
                            super().__init__(timeout = None)
                            self.outer = outer
                            
                            options = [nextcord.SelectOption(label = "Single", description = "Members can only select one option", value = "Single"),
                                            nextcord.SelectOption(label = "Multiple", description = "Members can select multiple options.", value = "Multiple")]
                            self.select = nextcord.ui.Select(options = options, placeholder = "Choose a Mode")
                            self.add_item(self.select)
                            
                            self.createBtn = nextcord.ui.Button(label = "Create Role Select", style = nextcord.ButtonStyle.blurple)
                            self.createBtn.callback = self.createBtnCallback
                            self.add_item(self.createBtn)
                            
                        async def setup(self, interaction: Interaction):
                            embed = nextcord.Embed(title = "Role Message Creation Wizard - Finish", description = "Finally, decide whether you want members to have the option to select multiple choices or just one.", color = nextcord.Color.green())
                            await interaction.response.edit_message(embed = embed, view = self)
                        
                        async def createBtnCallback(self, interaction: Interaction):
                            values = self.select.values
                            if values == []:
                                return
                            
                            value = values[0]
                            
                            if value == "Single":
                                view = RoleMessageButton_Single()
                            else:
                                view = RoleMessageButton_Multiple()
                            
                            # Create Role Select
                            
                            roleMessageEmbed = self.outer.createEmbed(self.outer.title, self.outer.description, self.outer.color, self.outer.options)
                    
                            await self.outer.disableView(interaction)
                            
                            message = await interaction.channel.send(embed = roleMessageEmbed, view = view)
                            
                            # Catalog Message
                            server = Server_DEP(interaction.guild.id)
                            server.messages.add("Role Message", message.channel.id, message.id, interaction.user.id)
                            server.messages.save()
                        
                    async def callback(self, interaction: Interaction):
                        await self.MultiOrSingleSelectView(self.outer).setup(interaction)
            
                async def setup(self, interaction: Interaction):
                    self.validateButtons()
                    
                    # Create two embeds depending on whether this is the first time
                    if len(self.options) == 0:
                        embed = nextcord.Embed(title = "Role Message Creation Wizard", description = "Excellent work! Your message is below. If you are satisfied with it, click on \"Next\".\n\nAlternatively, you can make edits to the text and color.", color = nextcord.Color.green())
                    else:
                        embed = nextcord.Embed(title = "Role Message Creation Wizard", description = "Excellent work! Your message is below. If you are satisfied with it, click on \"Finish\".\n\nAlternatively, you can make edits to the text, color, and options.", color = nextcord.Color.green())
                    
                    # Create a mockup of the embed
                    roleMessageEmbed = self.createEmbed(self.title, self.description, self.color, self.options)
                    
                    await interaction.response.edit_message(embeds = [embed, roleMessageEmbed], view = self)
                    
                def validateButtons(self):
                    """Be sure to update the view after running this"""
                    if len(self.options) > 0:
                        self.addBtn.__init__(self, self.options)
                        if self.editBtn not in self.children:
                            self.add_item(self.editBtn)
                        if self.removeBtn not in self.children:
                            self.add_item(self.removeBtn)
                        if self.finishBtn not in self.children:
                            self.add_item(self.finishBtn)
                    
                def createEmbed(self, title, description, color, options):
                    embed = nextcord.Embed(title = title, description = description, color = color)
                    for option in options:
                        self.addField(embed, option)

                    return embed
                        
                def addField(self, embed: nextcord.Embed, optionInfo):
                    mentions = [f"<@&{role}>" for role in optionInfo[0]]
                    if len(mentions) > 1:
                        mentions[-1] = f"and {mentions[-1]}"
                    roles = ", ".join(mentions)
                        
                    title = optionInfo[1]
                    description = optionInfo[2]
                    
                    spacer = ("\n" if description != "" else "")
                    
                    embed.add_field(name = title, value = f"{description}{spacer}> Grants {roles}", inline = False)
                
                async def disableView(self, interaction: Interaction):
                    for child in self.children:
                        if isinstance(child, nextcord.ui.Button):
                            child.disabled = True
                            
                    await interaction.response.edit_message(view = self, delete_after = 1.0)
                                     
            async def callback(self, interaction: Interaction):
                await self.RoleSelectWizardView(self.titleInput.value, self.descriptionInput.value).setup(interaction)
            
        async def callback(self, interaction: Interaction):
            await interaction.response.send_modal(self.Modal())
      
@create.subcommand(name = "role_message", description = "Create a message allowing users to add/remove roles by themselves. (Requires Infinibot Mod)")
async def roleMessageCommand(interaction: Interaction):
    if await hasRole(interaction):
        await RoleMessageSetup().setup(interaction)
#End of role messages functionality: ----------------------------------------------------------------------------------------------------------------------------------------






#Start of join/leave messages functionality: ----------------------------------------------------------------------------------------------------------------------------------------------
guildsBanning = []
@bot.event
async def on_member_join(member: nextcord.Member):
    global guildsBanning
    
    server = Server_DEP(member.guild.id)
    
    #banning------------------------------------------------------------
    if utils.enabled.AutoBans(server = server) and server.autoBanExists(member.id):
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
    joinMessage: str = server.join_message
    if utils.enabled.JoinLeaveMessages(server = server) and joinMessage != None and server.join_channel != False: #if we don't have a join message, what's the point?
        if server.join_channel != None: #set the join channel (if none, then it is the system channel)
            channel = server.join_channel
        else:
            if member.guild.system_channel != None:
                channel = member.guild.system_channel
            else:
                channel = None #if we set channel to none here, all other processes will be jumped
        
        #double check permissions
        if channel and not await checkTextChannelPermissions(channel, True, custom_channel_name = f"Join Message Channel (#{channel.name})"): #double check permissions
            channel = None
            
            
        if channel != None:
            joinMessageFormatted = joinMessage.replace("[member]", member.mention)
            
            embed = nextcord.Embed(title = f"{member} just joined the server!", description = joinMessageFormatted, color =  nextcord.Color.gold(), timestamp = datetime.datetime.now())
            embeds = [embed]
            
            #card (if necessary)
            if server.allow_join_cards_bool:
                memberData = Member(member.id)
                if memberData.join_card.enabled:
                    card = memberData.join_card.embed()
                    embeds.append(card)
            
            
            await channel.send(embeds = embeds)
    
    #give them roles --------------------------------------------------------------
    if utils.enabled.DefaultRoles(server = server):
        for role in server.default_roles:
            await member.add_roles(role)
        
    #update stats --------------------------------------------------------------------
    if server.stats_message.active:
        async def exceptionFunction():
            await sendErrorMessageToOwner(member.guild, None, message = "InfiniBot cannot access the Server Statistics message anymore to edit it. The message has been deactivated. Use /setup_stats to activate another.", administrator = False)
            server.stats_message.setValue(None)
            server.saveData()
            
        try:
            bool, message = await server.stats_message.checkMessage()
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
    
    server = Server_DEP(member.guild.id)
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
    leaveMessage: str = server.leave_message
    if utils.enabled.JoinLeaveMessages(server = server) and leaveMessage != None and server.leave_channel != False: #if we don't have a leave message, what's the point?
        if server.leave_channel != None: #set the leave channel (if none, then it is the system channel)
            channel = server.leave_channel
        else:
            if member.guild.system_channel != None:
                channel = member.guild.system_channel
            else:
                channel = None #if we set channel to none here, all other processes will be jumped
        
        #double check permissions
        if channel and not await checkTextChannelPermissions(channel, True, custom_channel_name = f"Leave Message Channel (#{channel.name})"): #double check permissions
            channel = None
            
            
        if channel != None:
            leaveMessageFormatted = leaveMessage.replace("[member]", member.mention)
            
            embed = nextcord.Embed(title = f"{member} just left the server.", description = leaveMessageFormatted, color =  nextcord.Color.gold(), timestamp = datetime.datetime.now())
            await channel.send(embed = embed)
            
            
            
    #update stats: ---------------------------------------------------------------------------------------------
    if server.stats_message.active:
        async def exceptionFunction():
            await sendErrorMessageToOwner(member.guild, None, message = "InfiniBot cannot access the Server Statistics message anymore to edit it. The message has been deactivated. Use /setup_stats to activate another.", administrator = False)
            server.stats_message.setValue(None)
            server.saveData()
            
        try:
            bool, message = await server.stats_message.checkMessage()
            if message != None:
                await message.edit(embed = getStatsMessage(message.guild))
            else:
                await exceptionFunction()
        except nextcord.errors.Forbidden or TypeError or ValueError:
            await exceptionFunction()

    await memberRemove(member.guild, member)
#END of join/leave messages functionality: ---------------------------------------------------------------------------------------------------------------------------------------------







#Start of birthday messages functionality: ---------------------------------------------------------------------------------------------------------------------------------------------
async def checkForBirthdays():
    print("checking birthdays -----------------------------------------------")
    current_time = datetime.datetime.now()
    
    #check for birthdays
    if global_kill_status.global_kill_birthdays: return
    
    # Loop through guilds
    for guild in bot.guilds:
        server = Server_DEP(guild.id)
        
        if server == None: continue
        if server.guild == None: continue
        
        # Loop through birthdays in each guild
        for birthday in server.birthdays:
            # Decode birthday time
            birthday_time = datetime.datetime.strptime(birthday.date, f"%m/%d/%Y")
                    
            if birthday_time.day == current_time.day and birthday_time.month == current_time.month: #if it is their birthday
                # If the member is none for some reason, just skip
                if birthday.member == None: continue
                
                # Calculate their age
                age = current_time.year - birthday_time.year
                
                # Embeds
                name = (birthday.real_name if birthday.real_name else birthday.member.name)
                
                server_embed = nextcord.Embed(title = f"Happy Birthday {name}!", description = f"{birthday.member.mention} just turned {age}! Congratulations!", color =  nextcord.Color.gold())
                dm_embed = nextcord.Embed(title = f"Happy Birthday {name}!", description = f"You just turned {age}! Congratulations!", color =  nextcord.Color.gold())
                dm_embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
                
                # Send to server
                birthday_channel = server.birthday_channel
                if birthday_channel: await birthday_channel.send(embed = server_embed)
                
                # DM
                memberSettings = Member(birthday.member_id)
                if memberSettings.dms_enabled: await birthday.member.send(embed = dm_embed)

@view.subcommand(name = "birthdays", description = "View all of the saved birthdays")
async def view_birthdays(interaction: Interaction):
    server = Server_DEP(interaction.guild.id)
    embed = nextcord.Embed(title = "Birthdays", color =  nextcord.Color.blue())
    
    birthdays = []
    for birthday in server.birthdays:
        try:
            if False or birthday.member == None: # Disabled due to issue with InfiniBot restarting 
                server.deleteBirthday(birthday.memberID)
                server.saveBirthdays()
                continue
            
            if birthday.real_name != None: birthdays.append(f"{birthday.member.mention} ({str(birthday.real_name)}) - {birthday.date}")
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
        if not utils.enabled.Purging(guild_id = interaction.guild.id):
            await interaction.response.send_message(embed = nextcord.Embed(title = "Purging Disabled", description = "Purging has been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
            return;
        
        if amount.lower() == "all":
            # Purging all messages
            await interaction.response.defer()
            
            if not interaction.channel.permissions_for(interaction.guild.me).manage_channels:
                await interaction.followup.send(embed = nextcord.Embed(title = "Permission Error", description = "InfiniBot needs to have the Manage Channels permission in this channel to use this command.", color = nextcord.Color.red()), ephemeral = True)
                return
            
            #create a channel, and move it to where it should
            try:
                newChannel: nextcord.TextChannel = await interaction.channel.clone(reason = "Purging Channel")
                await newChannel.edit(position = interaction.channel.position + 1, reason = "Purging Channel")
            except nextcord.errors.Forbidden:
                await interaction.followup.send(embed = nextcord.Embed(title = "Unknown Error", description = "An unknown error occurred when purging the channel. Please double check InfiniBot's permissions and try again.\n\nNote: It is possible that InfiniBot cloned this channel. You may want to double check.", color = nextcord.Color.red()), ephemeral = True)
                return
            
            server = Server_DEP(interaction.guild.id)
            #check for if the channel is connected to anything. And if so, replace it:
            
            def getID(channel: nextcord.TextChannel):
                if channel == None: return None
                else: return channel.id
                 
            if interaction.channel.id == getID(server.admin_channel): server.admin_channel = newChannel
            if interaction.channel.id == getID(server.log_channel): server.log_channel = newChannel
            if interaction.channel.id == getID(server.leveling_channel): server.leveling_channel = newChannel
            if interaction.channel.id == getID(server.join_channel): server.join_channel = newChannel
            if interaction.channel.id == getID(server.leave_channel): server.leave_channel = newChannel
            if interaction.channel.id in [getID(channel) for channel in server.leveling_exempt_channels]:
                server.leveling_exempt_channels.remove(interaction.channel)
                server.leveling_exempt_channels.append(newChannel)
            
            server.saveData()
            
            #delete old channel
            try:
                await interaction.channel.delete(reason = "Purging Channel")
            except nextcord.errors.Forbidden:
                await interaction.followup.send(embed = nextcord.Embed(title = "Unknown Error", description = "An unknown error occurred when purging the channel. Please double check InfiniBot's permissions and try again.\n\nNote: It is possible that InfiniBot cloned this channel. You may want to double check.", color = nextcord.Color.red()), ephemeral = True)
                return
            
            await newChannel.send(embed = nextcord.Embed(title = "Purged Messages", description = f"{interaction.user} has instantly purged {newChannel.mention} of all messages", color =  nextcord.Color.orange()), view = InviteView())
        
        else:
            # Purging a specified amount of messages
            try:
                int(amount)
            except TypeError:
                interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "\"Amount\" needs to be a number", color =  nextcord.Color.red()), ephemeral = True)
                return

            await interaction.response.defer()
            
            if not str(interaction.guild_id) in purging:
                purging.append(str(interaction.guild_id))

            deleted = []

            try:
                deleted = await interaction.channel.purge(limit = int(amount) + 1)
            except nextcord.errors.NotFound:
                # We reached the end of all the messages that we can purge.
                pass
            except Exception as e:
                # Remove it from the purging list
                if str(interaction.guild_id) in purging:
                    purging.pop(purging.index(str(interaction.guild_id)))
                    
                # Throw error
                await interaction.response.send_message(embed = nextcord.Embed(title = "Unknown Error", description = "An unknown error occurred when purging. Please double check InfiniBot's permissions and try again.", color = nextcord.Color.red()), ephemeral = True)
                
                # Log error
                print(e)
                return

            await asyncio.sleep(1)

            if str(interaction.guild_id) in purging:
                purging.pop(purging.index(str(interaction.guild_id)))

            await interaction.channel.send(embed = nextcord.Embed(title = "Purged Messages", description = f"{interaction.user} has purged {interaction.channel.mention} of {str(len(deleted) - 1)} messages", color =  nextcord.Color.orange()), view = InviteView())
#END of purge channels functionality: ----------------------------------------------------------------------------------------------------------------------------------------------------






#Start of logging bot functionality: -----------------------------------------------------------------------------------------------------------------------------------------------------
def shouldLog(guild_id):
    server = Server_DEP(guild_id)
    
    if not utils.enabled.Logging(server = server):
        return False, None

    if server.log_channel == None:
        return False, None
    else:
        return True, server.log_channel

@set.subcommand(name = "log_channel", description = "Use this channel for logging. Channel should only be viewable by admins. (Requires Infinibot Mod)")
async def setLogChannel(interaction: Interaction):
   if await hasRole(interaction) and await checkIfTextChannel(interaction):
        server = Server_DEP(interaction.guild.id)

        server.log_channel = interaction.channel
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
    await checkProfanity(Server_DEP(guild.id), afterMessage)
    
    #test for false-positives
    if not ShouldLog: return
    if afterMessage.author.bot == True: return
    if afterMessage.content == "": return
    if beforeMessage != None and beforeMessage.content == "": return
    if beforeMessage != None and afterMessage.content == beforeMessage.content: return
    
    #UI Log
    await trigger_edit_log(guild, beforeMessage, afterMessage, logChannel = logChannel)
 
async def trigger_edit_log(guild: nextcord.Guild, originalMessage: nextcord.Message, editedMessage: nextcord.Message, user: nextcord.Member = None, logChannel: nextcord.TextChannel = None):
    if not user: user = editedMessage.author
    if not logChannel:
        server = Server_DEP(guild.id)
        logChannel = server.log_channel
        if not logChannel or not server.logging_enabled:
            return;
    
    # Avatar
    avatar_url = user.display_avatar.url
    # Field name, Link name, content
    content_tasks = []
    # Added or Deleted, embed
    embed_tasks = []

    # Create an embed to edit
    Embed = nextcord.Embed(title = "Message Edited", description = editedMessage.channel.mention, color = nextcord.Color.yellow(), timestamp = datetime.datetime.now(), url = editedMessage.jump_url)
    
    # Check that the original message is still cached
    if not originalMessage:
        # The message is no longer retrievable
        if logChannel and await checkTextChannelPermissions(logChannel, True, custom_channel_name = f"Log Message Channel (#{logChannel.name})"):
            # Configure the embed
            Embed.add_field(name = "Contents Unretrievable", value = "The original message is unretrievable because the message was created too long ago.")
            
            # Add the extra stuff in the message
            Embed.set_author(name = getName(user), icon_url = avatar_url)
            
            # Send the message
            await logChannel.send(embed = Embed)
        return
    
    
    # Compare Contents
    if originalMessage.content != editedMessage.content:
        if len(originalMessage.content) <= 1024:
            Embed.add_field(name = "Original Message", value = originalMessage.content)
        elif len(originalMessage.content) > 2000:
            Embed.add_field(name = "Original Message", value = "Message too long. Please wait...")
            content_tasks.append(["Original Message", "View Original Message (Truncated)", originalMessage.content[:1999]])
        else:
            Embed.add_field(name = "Original Message", value = "Message too long. Please wait...")
            content_tasks.append(["Original Message", "View Original Message", originalMessage.content])
            
        if len(editedMessage.content) <= 1024:
            Embed.add_field(name = "Edited Message", value = editedMessage.content)
        elif len(editedMessage.content) > 2000:
            Embed.add_field(name = "Edited Message", value = "Message too long. Please wait...")
            content_tasks.append(["Edited Message", "View Edited Message (Truncated)", editedMessage.content[:1999]])
        else:
            Embed.add_field(name = "Edited Message", value = "Message too long. Please wait...")
            content_tasks.append(["Edited Message", "View Edited Message", editedMessage.content])
            
            
    # Compare embeds
    if (len(originalMessage.embeds) > 0) or (len(editedMessage.embeds)) > 0:
        deletedEmbeds = []
        for originalEmbed in originalMessage.embeds:
            counterpart_exists = False
            for editedEmbed in editedMessage.embeds:
                if originalEmbed == editedEmbed:
                    counterpart_exists = True
                    break
                
            if not counterpart_exists:
                # They deleted or edited this embed
                deletedEmbeds.append(originalEmbed)
                
        addedEmbeds = []
        for editedEmbed in editedMessage.embeds:
            counterpart_exists = False
            for originalEmbed in originalMessage.embeds:
                if editedEmbed == originalEmbed:
                    counterpart_exists = True
                    break
                
            if not counterpart_exists:
                # They added or edited this embed
                addedEmbeds.append(editedEmbed)
                
        if deletedEmbeds == [] and addedEmbeds == []:
            # They didn't do anything to the embeds
            pass
        else:
            # They DID do something to the embeds.
            Embed.add_field(name = "Embed(s)", value = "One or more embeds were modified. Here's a list of modifications:\n\nPlease Wait...\n\nNote: Edited embeds will appear as them being deleted then added.", inline = False)
            
            # Loop through embeds
            for embed in deletedEmbeds:
                embed_tasks.append(["Deleted", embed])
            
            for embed in addedEmbeds:
                embed_tasks.append(["Added", embed])
                
    
    # Add the extra stuff in the message
    Embed.set_author(name = getName(user), icon_url = avatar_url)
                
    # Send Message
    message = None
    if logChannel and await checkTextChannelPermissions(logChannel, True, custom_channel_name = f"Log Message Channel (#{logChannel.name})"):
        message = await logChannel.send(embed = Embed)
    
    # Do the other stuff after sending the message
    if message: # We want to make sure that the message was even sent
        if content_tasks == [] and embed_tasks == []: return
        
        completed_content_tasks = []
        for task in content_tasks:
            content_message = await logChannel.send(content = task[2], reference = message)
            completed_content_tasks.append([task[0], task[1], content_message.jump_url])
            
        completed_embed_tasks = []
        for task in embed_tasks:
            embed_message = await logChannel.send(embed = task[1], reference = message)
            completed_embed_tasks.append([task[0], task[1].title, embed_message.jump_url])
            
        # We've sent the other messages. Time to circle back and edit our old message to include the just sent links
        fields = Embed.fields
        
        # Clear the old fields
        Embed.clear_fields()
        
        # Update the fields and re-add them
        completed_content_tasks_field_names = [task[0] for task in completed_content_tasks]
        for field in fields:
            if field.name in completed_content_tasks_field_names:
                # This is where our content info will go (it could be an original message or an edited message)
                index = completed_content_tasks_field_names.index(field.name)
                Embed.add_field(name = completed_content_tasks[index][0], value = f"[{completed_content_tasks[index][1]}]({completed_content_tasks[index][2]})", inline = field.inline)
                continue

            if field.name == "Embed(s)":
                # This is where our embed info will go
                links = []
                for task in completed_embed_tasks:
                    links.append(f"• **{task[0]}** [{task[1]}]({task[2]})")
                    
                content = field.value
                content = content.replace("Please Wait...", "\n".join(links))
                Embed.add_field(name = field.name, value = content, inline = field.inline)
                continue
            
            # The field was not a task, but we should still replace it
            Embed.add_field(name = field.name, value = field.value, inline = field.inline)
                
        # Finally, update the old message to have the new embed
        await message.edit(embed = Embed)
    
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
    global auto_deleted_message_time, purging

    time.sleep(1) #we need this time delay for some other features

    if auto_deleted_message_time != None: #see if this is InfiniBot's doing
        if ((datetime.datetime.now(datetime.timezone.utc) - auto_deleted_message_time).seconds <= 5):
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
    server = Server_DEP(guild.id)
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
            await sendErrorMessageToOwner(guild, "View Audit Log", guild_permission = True)
            return
        except IndexError:
            entry = None
        except Exception as e:
            print("on_raw_message_delete:")
            print(e)
            return
        
        #log whether or not the audit log is fresh enough to be accurate (within 5 seconds)
        if entry:
            freshAuditLog = (entry.created_at.month == datetime.datetime.now(datetime.timezone.utc).month and entry.created_at.day == datetime.datetime.now(datetime.timezone.utc).day and entry.created_at.hour == datetime.datetime.now(datetime.timezone.utc).hour and ((datetime.datetime.now(datetime.timezone.utc).minute - entry.created_at.minute) <= 5))
        else:
            freshAuditLog = False
        
        if entry and freshAuditLog:
            #we prioritize the author of the message if we know it, but if we don't we use this
            if not message: user = entry.target
            else: user = message.author
            #set the deleter (because we didn't know that before)
            deleter = entry.user
        else:
            # The user probably just deleted their own message. We'll go with that theory.
            # We don't actually need any of this information to exist then
            if not message: user = None
            deleter = None
        
        #eliminate whether InfiniBot is the author / deleter (only do this if we're sure that the audit log is fresh)
        if freshAuditLog and user.id == bot.application_id: return
        if freshAuditLog and deleter.id == bot.application_id: return
            
        
        #send log information!!! -------------------------------------------------------------------------------------------------------------------------------------------
        embed = nextcord.Embed(title = "Message Deleted", color = nextcord.Color.red(), timestamp = datetime.datetime.now())
        embeds = []
        code = 1
        
        #embed description and code
        if freshAuditLog:
            if deleter.id != user.id:
                embed.description = f"{deleter.mention} deleted {user.mention}'s message from {channel.mention}"
            else:
                embed.description = f"{deleter.mention} deleted their message from {channel.mention}"
                
            if message:
                code = 1
            else:
                code = 2
        else:
            if not message:
                embed.description = f"A message was deleted from {channel.mention}"
                code = 3
            else:
                embed.description = f"{message.author.mention}'s message was deleted from {channel.mention}"
                code = 4
                
        
        #message content
        if message: 
            if message.content != "": 
                if len(message.content) <= 1024: 
                    embed.add_field(name = "Message", value = message.content)
                else:
                    embed.add_field(name = "Message", value = "Message is too long! Discord won't display it.")
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
          
        # The Profile
        if deleter:
            embed.set_author(name = getName(deleter), icon_url = deleter.display_avatar.url)  
            
        #the footer
        embed.set_footer(text = f"Message ID: {payload.message_id}\nCode: {code}")

        #actually send the embed
        view = ShowMoreButton()
        if logChannel and await checkTextChannelPermissions(logChannel, True, custom_channel_name = f"Log Message Channel (#{logChannel.name})"): 
            logMessage = await logChannel.send(view = view, embeds = ([embed] + (embeds[0:8] if len(embeds) >= 10 else embeds)))
            if message and message.attachments != []:
                await files_computation(message, logChannel, logMessage)

@bot.event
async def on_guild_channel_delete(channel: nextcord.abc.GuildChannel):
    server = Server_DEP(channel.guild.id)
    server.messages.deleteAllFromChannel(channel.id)
    server.messages.save()

@bot.event
async def on_member_update(before: nextcord.Member, after: nextcord.Member):
    global nickname_changed
    
    if before.nick != after.nick and not after.guild.id in nickname_changed:
        ShouldLog, logChannel = shouldLog(after.guild.id)
        if ShouldLog:

            entry = list(await after.guild.audit_logs(limit=1).flatten())[0]
            user = entry.user

            embed = nextcord.Embed(title = "Nickname Changed", description = f"{user} changed {after}'s nickname.", color = nextcord.Color.blue(), timestamp = datetime.datetime.now())

            if before.nick != None: embed.add_field(name = "Before", value = before.nick, inline = True)
            else: embed.add_field(name = "Before", value = "None", inline = True)

            if after.nick != None: embed.add_field(name = "After", value = after.nick, inline = True)
            else: embed.add_field(name = "After", value = "None", inline = True)
            
            if logChannel and await checkTextChannelPermissions(logChannel, True, custom_channel_name = f"Log Message Channel (#{logChannel.name})"): 
                await logChannel.send(embed = embed)
            
            
        if after.nick != None: await checkNickname(after.guild, before, after)

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

            if logChannel and await checkTextChannelPermissions(logChannel, True, custom_channel_name = f"Log Message Channel (#{logChannel.name})"): 
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
                
                if logChannel and await checkTextChannelPermissions(logChannel, True, custom_channel_name = f"Log Message Channel (#{logChannel.name})"): 
                    await logChannel.send(embed = embed)
                
            elif after.communication_disabled_until == None: #their timeout was removed manually
                embed = nextcord.Embed(title = "Timeout Revoked", description = f"{user} revoked {after}'s timeout", color = nextcord.Color.orange(), timestamp = datetime.datetime.now())
                
                if logChannel and await checkTextChannelPermissions(logChannel, True, custom_channel_name = f"Log Message Channel (#{logChannel.name})"): 
                    await logChannel.send(embed = embed)

async def memberRemove(guild: nextcord.Guild, member: nextcord.Member):
    if guild == None: return
    if guild.unavailable: return
    if guild.me == None: return
    
    if not guild.me.guild_permissions.view_audit_log:
        await sendErrorMessageToOwner(guild, "View Audit Log", guild_permission = True)
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
        
        if channel and await checkTextChannelPermissions(channel, True, custom_channel_name = f"Log Message Channel (#{channel.name})"):
            await channel.send(embed = embed)
#END of logging bot functionality: -------------------------------------------------------------------------------------------------------------------------------------------------------






#Join-to-create VC: -------------------------------------------------------------------------------------------------------------------------------------------------------------------     
@bot.event
async def on_voice_state_update(member: nextcord.Member, before: nextcord.VoiceState, after: nextcord.VoiceState):
    if not utils.enabled.JoinToCreateVCs(guild_id = member.guild.id):
        return
    
    if before.channel == None and after.channel == None: return
    if after.channel != None:
        server = Server_DEP(member.guild.id)
        if after.channel.id in [vc.id for vc in server.VCs]:
            #double check that we have permissions
            for vc in server.VCs:
                if vc.id == after.channel.id:
                    if not vc.active:
                        return
                    break
                
            category = after.channel.category if after.channel.category else member.guild
            
            try:
                vc = await category.create_voice_channel(name = f"{member.name} Vc")
            except nextcord.errors.Forbidden:
                await sendErrorMessageToOwner(member.guild, "Manage Channels", guild_permission = True)
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
                    await sendErrorMessageToOwner(member.guild, "Manage Channels", guild_permission = True)
                if before.channel.permissions_for(member.guild.me).connect == False:
                    await sendErrorMessageToOwner(member.guild, "Connect", guild_permission = True)
                return
#Join-to-create vc END: --------------------------------------------------------------------------------------------------------------------------------------------------------------





#Leveling: ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
async def checkLevels():
    print("Checking Levels --------------------")
    if not global_kill_status.global_kill_leveling:
        all_guild_IDs = [guild.id for guild in bot.guilds]
        for guild in bot.guilds:
            try:
                if not guild.id in all_guild_IDs: continue
                
                server = Server_DEP(guild.id)
                
                # Checks
                if server == None or server.guild == None: continue
                if server.leveling_enabled == False: continue
                if server.points_lost_per_day == None: continue
                if server.points_lost_per_day == 0: continue
                
                # Go through each member and edit
                for level in server.levels.all_members:
                    try:
                        # Remove the points
                        level.score -= server.points_lost_per_day
                    except Exception as err:
                        print(f"ERROR When checking levels (member): {err}")
                        continue
                
                server.saveLevels()
                
                for member in server.levels.all_members:
                    await checkForLevelsAndLevelRewards(server.guild, member.member)
                
                del server
                
            except Exception as err:
                print(f"ERROR When checking levels (server): {err}")
                continue

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

def setScoreOfMember(server: Server_DEP, member_id, score):
    memberLevel = server.levels.getMember(member_id)
    memberLevel.score = score        
    server.saveLevels()

async def canLevel(interaction: Interaction, server: Server_DEP):
    """Determins whether or not leveling is enabled for the server. NOT SILENT!"""
    if utils.enabled.Leveling(server = server):
        return True
    else:
        if not global_kill_status.global_kill_leveling:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Leveling Disabled", description = "Leveling has been turned off. type \"/enable leveling\" to turn it back on.", color = nextcord.Color.red()), ephemeral = True)
            return False
        else:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Leveling Disabled", description = "Leveling has been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
            return False

async def giveLevels(message: nextcord.Message):
    """Manages the distribution of points (and also levels and level rewards, but indirect). Simply requires a message."""
    MAX_POINTS_PER_MESSAGE = 40 # Messages are capped at these amount of points
    
    
    member = message.author
    if member.id == bot.application_id: return

    channel = message.channel
    
    server = Server_DEP(message.guild.id)
    if message.channel.id in [channel.id for channel in server.leveling_exempt_channels]: return
    
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
    total_points = 0
    for word in words:
        for _ in word: total_points += 1
        
    total_points /= 10
    roundedPoints = round(total_points)
    
    if roundedPoints > MAX_POINTS_PER_MESSAGE:
        roundedPoints = MAX_POINTS_PER_MESSAGE
    
    member_level = server.levels.getMember(member.id)
    originalLevel = getLevel(member_level.score)
    member_level.score += roundedPoints
        
    nowLevel = getLevel(member_level.score)
    server.saveLevels()
    
    if originalLevel != nowLevel:
        await checkForLevelsAndLevelRewards(message.guild, message.author, levelup_announce = True)
  
async def checkForLevelsAndLevelRewards(guild: nextcord.Guild, member: nextcord.Member, levelup_announce: bool = False, silent = False):
    """Handles the distribution of levels and level rewards"""
    server = Server_DEP(guild.id)
    member_level = server.levels.getMember(member.id)
    score = member_level.score
    level = getLevel(score)
    
    
    member_options = Member(member.id)
    
    
    #level-up messages
    if levelup_announce and (not silent) and (server.leveling_message != None) and (server.leveling_channel != False):
        message = server.leveling_message.replace("[level]", str(level))
        embed = nextcord.Embed(title = f"Congratulations, {member.display_name}!", description = message, color = nextcord.Color.from_rgb(235, 235, 235)) #white-ish
        embeds = [embed]
        
        #get the card (if needed)
        if server.allow_level_cards_bool:
            memberData = Member(member.id)
            if memberData.level_card.enabled:
                card = memberData.level_card.embed()
                card.description = card.description.replace("[level]", str(level))
                embeds.append(card)
        
        
        if server.leveling_channel != None:
            await server.leveling_channel.send(embeds = embeds) 
        else:
            channel = await getChannel(guild)
            if channel != None: await channel.send(embeds = embeds)
    
    # Level-Reward messages
    for level_reward in server.levels.level_rewards:
        if level_reward.level <= level:
            # We need to give them this role.
            if not level_reward.role in member.roles:
                try:
                    await member.add_roles(level_reward.role)
                except nextcord.errors.Forbidden:
                    await sendErrorMessageToOwner(guild, "Manage Roles", guild_permission = True)
                    return
                
                # Send a notifications
                if not silent:
                    # DM Them
                    if member_options.dms_enabled:
                        embed = nextcord.Embed(title = f"Congratulations! You leveled up in {guild.name}!", description = f"As a result, you were granted {level_reward.role.name}. Keep your levels up, or else you will loose it!", color = nextcord.Color.purple())
                        embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
                        try:
                            await member.send(embed = embed)
                        except nextcord.errors.Forbidden:
                            # DMs are disabled
                            pass
                
        else:
            # We need to take the role
            if level_reward.role in member.roles:
                try:
                    await member.remove_roles(level_reward.role)
                except nextcord.errors.Forbidden:
                    await sendErrorMessageToOwner(guild, "Manage Roles", guild_permission = True)
                    return
                
                # Send a notifications
                if not silent:
                    # DM Them
                    if member_options.dms_enabled:
                        embed = nextcord.Embed(title = f"Oh, no! You lost a level in {guild.name}!", description = f"As a result, {level_reward.role.name} has been revoked. Bring your levels back up, and win back your role!", color = nextcord.Color.purple())
                        embed.set_footer(text = "To opt out of dm notifications, use /opt_out_of_dms")
                        try:
                            await member.send(embed = embed)
                        except nextcord.errors.Forbidden:
                            # DMs are disabled
                            pass
  

@bot.slash_command(name = "leaderboard", description = "Get your level and the level of everyone on the server.", dm_permission=False)
async def leaderboard(interaction: Interaction):
    server = Server_DEP(interaction.guild.id)
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
    server = Server_DEP(interaction.guild.id)
    if not await canLevel(interaction, server): return
    
    Member = server.levels.getMember(interaction.user.id)
    if Member != None:
        score = Member.score
    else:
        score = 0
        
    level = getLevel(score)
    
    await interaction.response.send_message(embed = nextcord.Embed(title = "Your level", description = f"{interaction.user.mention} is at level {str(level)} (score: {str(score)})", color = nextcord.Color.blue()), view = InviteView())

@set.subcommand(name = "level", description = "Set levels for any individual (Requires Infinibot Mod)")
async def setLevel(interaction: Interaction, member: nextcord.Member, level: int):
    if await hasRole(interaction):
        if level < 0:
            await interaction.response.send_message(embed = nextcord.Embed(title = "Format Error", description = "\"Level\" needs to be positive.", color = nextcord.Color.red()), ephemeral=True)
            return
        
        score = getScore(level)
        
        server = Server_DEP(interaction.guild.id)
        Member = server.levels.getMember(member.id)
        if Member != None: beforeScore = Member.score
        else: beforeScore = 0
        
        setScoreOfMember(server, member.id, score)    
        
        await interaction.response.send_message(embed = nextcord.Embed(title = "Levels Changed", description = f"{interaction.user} changed {member}'s level to {str(level)} (score: {str(score)})", color = nextcord.Color.green()))
        
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
        server = Server_DEP(interaction.guild.id)
        exists, message = await server.stats_message.checkMessage()
        if exists:
            #they already have a stats message. We should double check that they want to continue.
            embed = nextcord.Embed(title = "Statistics Message Already Exists", description = f"Each server can only have one statistics message.\n\nCurrently, there is already a [statistics message]({server.stats_message.link}). Would you like to replace it?", color = nextcord.Color.blue())

            view = ConfirmationView()
            await interaction.response.send_message(embed = embed, view = view, ephemeral = True)
            await view.wait()
            
            if view.choice == False:
                return
            
            #they agree to override
            #first, change the existing one....
            try:
                await message.edit(embed = statsInvalidMessage)
            except nextcord.errors.Forbidden:
                pass
            
            #next, add new one...
            statsMessage = getStatsMessage(interaction.guild)
            
            if not await checkTextChannelPermissions(interaction.channel, False):
                await interaction.followup.send(embed = nextcord.Embed(title = "Unable to Post Messages", description = "InfiniBot is unable to post messages in this channel. Please resolve this issue and try again.", color = nextcord.Color.red()), ephemeral = True)
                return
            
            message = await interaction.channel.send(embed = statsMessage)
            
            server.stats_message.setValue(message)
            server.saveData()
            
        
        else:
            #they do not have a stats message.
            statsMessage = getStatsMessage(interaction.guild)
            
            if not await checkTextChannelPermissions(interaction.channel, False):
                await interaction.followup.send(embed = nextcord.Embed(title = "Unable to Post Messages", description = "InfiniBot is unable to post messages in this channel. Please resolve this issue and try again.", color = nextcord.Color.red()), ephemeral = True)
                return
            
            message = await interaction.channel.send(embed = statsMessage)
            
            server.stats_message.setValue(message)
            server.saveData()
            
            await interaction.response.send_message(embed = nextcord.Embed(title = "How it works: Server Statistics", description = "This message will update every time someone joins / leaves the server. There can only be one of these, so if you run this command again, this one will become inactive.", color = nextcord.Color.blue()), ephemeral = True)
#Stats END: ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# Jokes: --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class JokeView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
        if utils.enabled.JokeSubmissions(guild_id = 123546798): # the result of bad code
            self.button = nextcord.ui.Button(label = "Submit a Joke", custom_id = "submit_a_joke")
            self.button.callback = self.submit_a_joke_callback
            self.add_item(self.button)
        
    class SubmitAJokeModal(nextcord.ui.Modal):
        def __init__(self):
            super().__init__(title = "Submit a Joke", timeout = None)
            
            self.joke_title = nextcord.ui.TextInput(label = "Title", placeholder = "The Chicken and the Road", max_length = 100)
            self.add_item(self.joke_title)
            
            self.joke_description = nextcord.ui.TextInput(label = "Joke", placeholder = "Why did the chicken cross the road?", style = nextcord.TextInputStyle.paragraph, max_length = 500)
            self.add_item(self.joke_description)
            
            self.joke_answer = nextcord.ui.TextInput(label = "Answer", placeholder = "To get to the other side!", style = nextcord.TextInputStyle.paragraph, max_length = 500, required = False)
            self.add_item(self.joke_answer)
            
        async def callback(self, interaction: Interaction):
            # Try to post a message to the submission channel on the InfiniBot Support Server
            server = None
            for guild in bot.guilds:
                if guild.id == infinibot_guild_id: server = guild
            
            if server == None:
                print("ERROR: CANNOT FIND INFINIBOT SERVER!!!")
                self.stop()
                return
            
            embed = nextcord.Embed(title = "New Joke Submission:", description = f"Member: {interaction.user}\nMember ID: {interaction.user.id}\nServer: {interaction.guild.name}\nServer ID: {interaction.guild.id}", color = nextcord.Color.dark_green())
            embed.add_field(name = "Title", value = self.joke_title.value)
            embed.add_field(name = "Joke", value = self.joke_description.value)
            if self.joke_answer.value: embed.add_field(name = "Answer", value = self.joke_answer.value)
            
            channel = server.get_channel(submission_channel_id)
            await channel.send(embed = embed, view = JokeVerificationView())
            
            # Inform the user that it was sent
            await interaction.response.send_message(embed = nextcord.Embed(title = "Submission Sent", description = "Your submission was sent! Join our support server, and we'll dm you regarding your submission's status.", color = nextcord.Color.green()), ephemeral = True, view = SupportView())
                   
    async def submit_a_joke_callback(self, interaction: Interaction):
        if not utils.enabled.JokeSubmissions(guild_id = interaction.guild.id):
            await interaction.response.send_message(embed = nextcord.Embed(title = "Joke Submissions Disabled", description = "Joke Submissions have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
            return
        
        await interaction.response.send_modal(self.SubmitAJokeModal())
        
class JokeVerificationView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        
    @nextcord.ui.button(label = "Deny", custom_id = "deny_joke")
    async def deny(self, button: nextcord.ui.Button, interaction: Interaction):
        class Modal(nextcord.ui.Modal):
            def __init__(self, message):
                super().__init__(title = "Reason to Deny", timeout = None)
                self.message = message
                
                # Get the member ID 
                self.member_id = None
                for line in self.message.embeds[0].description.splitlines():
                    if line.startswith("Member ID:"):
                        id = line[len("Member ID: "):]
                        if id.isdigit():
                            self.member_id = int(id)
                            break
                
                self.reason = nextcord.ui.TextInput(label = "Reason. This will be sent to the submitter.", placeholder = "Your joke submission was denied because ...", style = nextcord.TextInputStyle.paragraph)
                self.add_item(self.reason)
                
            async def callback(self, interaction: Interaction):
                reason = self.reason.value
                
                class ConfirmView(nextcord.ui.View):
                    def __init__(self, message: nextcord.Message, reason):
                        super().__init__(timeout = None)
                        self.message = message
                        self.reason = reason
                            
                    @nextcord.ui.button(label = "Cancel")
                    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
                        await interaction.response.edit_message(delete_after=0.0)
                        
                    @nextcord.ui.button(label = "Confirm")
                    async def confirm(self, button: nextcord.ui.Button, interaction: Interaction):
                        # Let's add it
                        title = None
                        description = None
                        answer = None
                        for field in self.message.embeds[0].fields:
                            if field.name == "Title":
                                title = field.value
                            elif field.name == "Joke":
                                description = field.value
                            elif field.name == "Answer":
                                answer = field.value
                        
                        # Send Confirmation
                        embeds = self.message.embeds
                        embeds.append(nextcord.Embed(title = "Submission Denied", description = f"{interaction.user} denied this submission.\n\nReason: {self.reason}", color = nextcord.Color.red()))
                        await self.message.edit(embeds = embeds, view = None)
                        
                        # Try to dm
                        support_server = bot.get_guild(infinibot_guild_id)
                        if not support_server:
                            print("ERROR: CANNOT FIND INFINIBOT SERVER!!!")
                            return
                        
                        member = support_server.get_member(self.member_id)
                        if not member:
                            return
                        
                        dm = await member.create_dm()
                        
                        memberSettings = Member(member.id)
                        if memberSettings.dms_enabled:
                            await dm.send(embeds = [nextcord.Embed(title = "Joke Submission Denied", description = f"Your joke submission has been denied by {interaction.user}. The joke you submitted has been attached below.\n\nReason: {self.reason}\n\nIf you believe this to be a mistake, contact the moderator in the #support channel of the InfiniBot Support Server.", color = nextcord.Color.red()),
                                              nextcord.Embed(title = title, description = f"{description}\n\n{f'Answer: ||{answer}||' if answer else ''}", color = nextcord.Color.fuchsia())])
                        
                        # Remove the message
                        await interaction.response.edit_message(delete_after=0.0)
                   
                # Get confirmation that we will be able to dm the user
                try:
                    support_server = bot.get_guild(infinibot_guild_id)
                except nextcord.errors.Forbidden:
                    print("ERROR: CANNOT FIND INFINIBOT SERVER!!!")
                    return
                
                member = support_server.get_member(self.member_id)
                if not member:
                    moreInfo = "\n\nThis will **not** send the submitter a dm."
                else:
                    moreInfo = "\n\nBoth your reason and your username will be sent to the submitter via dm."
                        
                await interaction.response.send_message(embed = nextcord.Embed(title = "Confirm Deny", description = f"Are you sure you want to deny this joke submission? This will not be reversable.{moreInfo}", color = nextcord.Color.blue()), ephemeral = True, view = ConfirmView(self.message, reason))
                                            
        modal = Modal(interaction.message)
        await interaction.response.send_modal(modal)
        
    @nextcord.ui.button(label = "Verify", custom_id = "verify_joke")
    async def verify(self, button: nextcord.ui.Button, interaction: Interaction):
        class Modal(nextcord.ui.Modal):
            def __init__(self, message: nextcord.Message):
                super().__init__(title = "Finalize Joke", timeout = None)
                self.message = message
                
                # Get the message contents
                joke_title = None
                joke_description = None
                joke_answer = None
                for field in self.message.embeds[0].fields:
                    if field.name == "Title":
                        joke_title = field.value
                    elif field.name == "Joke":
                        joke_description = field.value
                    elif field.name == "Answer":
                        joke_answer = field.value
                       
                # Get the member ID 
                self.member_id = None
                for line in self.message.embeds[0].description.splitlines():
                    if line.startswith("Member ID:"):
                        id = line[len("Member ID: "):]
                        if id.isdigit():
                            self.member_id = int(id)
                            break
                        
                
                self.joke_title = nextcord.ui.TextInput(label = "Title", placeholder = "The Chicken and the Road", default_value = joke_title, max_length = 100)
                self.add_item(self.joke_title)
                
                self.joke_description = nextcord.ui.TextInput(label = "Joke", placeholder = "Why did the chicken cross the road?", default_value = joke_description, style = nextcord.TextInputStyle.paragraph, max_length = 500)
                self.add_item(self.joke_description)
                
                self.joke_answer = nextcord.ui.TextInput(label = "Answer", placeholder = "To get to the other side!", default_value = joke_answer, style = nextcord.TextInputStyle.paragraph, max_length = 500, required = False)
                self.add_item(self.joke_answer)
                
            async def callback(self, interaction: Interaction):
                title = self.joke_title.value
                description = self.joke_description.value
                answer = self.joke_answer.value
                
                # Fix new lines
                description = formatNewlinesForComputer(description)
                answer = formatNewlinesForComputer(answer)
                
                class ConfirmView(nextcord.ui.View):
                    def __init__(self, message: nextcord.Message, joke_title: str, joke_description: str, joke_answer: str, member_id: int):
                        super().__init__(timeout = None)
                        self.message = message
                        self.joke_title = joke_title
                        self.joke_description = joke_description
                        self.joke_answer = joke_answer
                        self.member_id = member_id
                            
                    @nextcord.ui.button(label = "Cancel")
                    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
                        await interaction.response.edit_message(delete_after=0.0)
                        
                    @nextcord.ui.button(label = "Confirm")
                    async def confirm(self, button: nextcord.ui.Button, interaction: Interaction):
                        # Let's add it                                          
                        if self.joke_answer: joke = "~".join([self.joke_title, self.joke_description, self.joke_answer])
                        else: joke = "~".join([self.joke_title, self.joke_description])
                        
                        all_jokes = fileOperations.getAllJokes()
                        all_jokes.append(joke)
                        fileOperations.saveJokes(all_jokes)
                        
                        # Send Confirmation
                        joke_embed = self.message.embeds[0]
                        joke_embed.clear_fields()
                        joke_embed.add_field(name = "Title", value = self.joke_title)
                        joke_embed.add_field(name = "Joke", value = formatNewlinesForUser(self.joke_description))
                        joke_embed.add_field(name = "Answer", value = formatNewlinesForUser(self.joke_answer))
                        embeds = [joke_embed]
                        embeds.append(nextcord.Embed(title = "Submission Verified", description = f"{interaction.user} verified this submission.", color = nextcord.Color.green()))
                        await self.message.edit(embeds = embeds, view = None)
                        
                        # Try to dm
                        try:
                            support_server = bot.get_guild(infinibot_guild_id)
                        except nextcord.errors.Forbidden:
                            print("ERROR: CANNOT FIND INFINIBOT SERVER!!!")
                            return
                        
                        member = support_server.get_member(self.member_id)
                        if not member:
                            return
                        
                        dm = await member.create_dm()
                        
                        memberSettings = Member(member.id)
                        if memberSettings.dms_enabled:
                            await dm.send(embeds = [nextcord.Embed(title = "Joke Submission Verified", description = f"Your joke submission has been verified! The joke you submitted has been attached below.", color = nextcord.Color.green()),
                                                nextcord.Embed(title = self.joke_title, description = f"{formatNewlinesForUser(self.joke_description)}\n\n{f'Answer: ||{formatNewlinesForUser(self.joke_answer)}||' if self.joke_answer else ''}", color = nextcord.Color.fuchsia())])
                        
                        # Remove the message
                        await interaction.response.edit_message(delete_after=0.0)
                
                
                # Get confirmation that we will be able to dm the user
                try:
                    support_server = bot.get_guild(infinibot_guild_id)
                except nextcord.errors.Forbidden:
                    print("ERROR: CANNOT FIND INFINIBOT SERVER!!!")
                    return
                
                member = support_server.get_member(self.member_id)
                if not member:
                    moreInfo = "\n\nThis will **not** send the submitter a dm."
                else:
                    moreInfo = "\n\nThis will send the submitter a dm."
                
                
                await interaction.response.send_message(embed = nextcord.Embed(title = "Confirm Verify", description = f"Are you sure you want to verify this joke submission (applying any changes you made)? This will not be reversable.{moreInfo}", color = nextcord.Color.blue()), ephemeral = True, view = ConfirmView(interaction.message, title, description, answer, self.member_id))            
               
        modal = Modal(interaction.message)
        await interaction.response.send_modal(modal)
        
@bot.slash_command(name = "joke", description = "Get a joke")
async def jokeCommand(interaction: Interaction):
    if not utils.enabled.Jokes(guild = interaction.guild):
        await interaction.response.send_message(embed = nextcord.Embed(title = "Jokes Disabled", description = "Jokes have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
        return
    
    all_jokes = fileOperations.getAllJokes()
    
    joke = ""
    
    for _ in range(0, 100):
        id = random.randint(0, len(all_jokes) - 1)
        
        joke = all_jokes[id]
        
        if joke != "":
            break
    
    if joke == "":
        return
    
    joke_parts = joke.split("~")
    
    await interaction.response.send_message(embed = nextcord.Embed(title = joke_parts[0], description = f"{formatNewlinesForUser(joke_parts[1])}\n\n{f'Answer: ||{formatNewlinesForUser(joke_parts[2])}||' if len(joke_parts) == 3 else ''}", color = nextcord.Color.fuchsia()), view = JokeView())
# Jokes END: ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



# Message and User Dropdowns
class MessageCommandOptionsView(nextcord.ui.View):
    def __init__(self, interaction: Interaction, message: nextcord.Message, hasRole: bool):
        super().__init__(timeout = None)
        self.interaction = interaction
        self.message = message
        self.hasRole = hasRole
        
        self.thisMessage_id = None
        
        # Add buttons
        self.DeleteDMButton(self, interaction, message)
        self.EditButton(self, interaction, message)
        self.BanButton(self, interaction, message)
        
    async def setup(self, interaction: Interaction):
        embed = nextcord.Embed(title = "Message Options", description = "Syncing Data. Please Wait...", color = nextcord.Color.blue())
        message = await interaction.response.send_message(embed = embed, ephemeral = True)
        full_message = await message.fetch()
        
        if len(self.children) == 0:
            description = "Hmmm. You don't have any options for this message."
            color = nextcord.Color.red()
        else:
            description = "This message supports the options below:"
            color = nextcord.Color.blue()
        
        embed = nextcord.Embed(title = "Message Options", description = description, color = color)
        
        self.thisMessage_id = await interaction.followup.edit_message(full_message.id, embed = embed, view = self)
        
    async def disableAll(self, interaction: Interaction):
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                child.disabled = True
        
        try:
            self.thisMessage_id = await interaction.response.edit_message(view = self, delete_after = 0.0)
        except nextcord.errors.InteractionResponded:
            await interaction.followup.edit_message(self.thisMessage_id.id, view = self, delete_after = 0.0)
        
    class DeleteDMButton(nextcord.ui.Button):
        def __init__(self, outer, interaction: Interaction, message: nextcord.Message):
            super().__init__(label = "Delete Message")
            
            self.outer = outer
            self.interaction = interaction
            self.message = message
            
            # Check Message Compatibility
            if not interaction.guild and message.author.id == bot.application_id:
                self.outer.add_item(self)
                
        async def callback(self, interaction: Interaction):
            await self.message.delete()
            await self.outer.disableAll(interaction)

    class EditButton(nextcord.ui.Button):
        def __init__(self, outer, interaction: Interaction, message: nextcord.Message):
            super().__init__(label = "Edit Message")
            
            self.outer = outer
            self.interaction = interaction
            self.message = message
            
            # Check Message Compatibility
            if not interaction.guild: return
            server = Server_DEP(interaction.guild.id);
            server.messages.initialize();
            self.messageInfo = server.messages.get(message.id);
            
            if (interaction.guild and message.author == interaction.guild.me
                and self.messageInfo and interaction.user.id == self.messageInfo.owner_id):
                self.outer.add_item(self)
                
        async def callback(self, interaction: Interaction):
            if self.messageInfo.type == "Embed":
                await EditEmbed(self.message.id).setup(interaction)
            elif self.messageInfo.type == "Vote":
                await EditVote(self.message.id).setup(interaction)
            elif self.messageInfo.type == "Reaction Role":
                await EditReactionRole(self.message.id).setup(interaction)
            elif self.messageInfo.type == "Role Message":
                await EditRoleMessage(self.message.id).setup(interaction)

    class BanButton(nextcord.ui.Button):
        def __init__(self, outer, interaction: Interaction, message: nextcord.Message):
            super().__init__(label = "Ban Message Author")
            
            self.outer = outer
            self.interaction = interaction
            self.message = message
            
            # Check Message Compatibility
            if not interaction.guild: return
            enabled = False
            if (interaction.user.guild_permissions.ban_members and interaction.guild.me.guild_permissions.ban_members
                and interaction.user.id != self.message.author.id):
                # We have basic permissions to ban
                if (self.message.author in interaction.guild.members):
                    if (bot.application_id != self.message.author.id and interaction.guild.me.top_role.position > self.message.author.top_role.position):
                        enabled = True
                else:
                    enabled = True
            
            if enabled:
                self.outer.add_item(self)
                
        class BanView(nextcord.ui.View):
            def __init__(self, outer, message: nextcord.Message):
                super().__init__(timeout = None)
                self.outer = outer
                self.message = message
                

                noBtn = nextcord.ui.Button(label = "No, Cancel", style = nextcord.ButtonStyle.danger)
                noBtn.callback = self.noBtnCallback
                self.add_item(noBtn)

                yesBtn = nextcord.ui.Button(label = "Yes, Ban", style = nextcord.ButtonStyle.green)
                yesBtn.callback = self.yesBtnCallback
                self.add_item(yesBtn)
                
            async def setup(self, interaction: Interaction):
                if not utils.enabled.AutoBans(guild_id = interaction.guild.id):
                    await disabled_feature_override(self, interaction)
                    return
                
                if self.message.author in interaction.guild.members:
                    #if member is in server
                    description = f"Are you sure that you want to ban {self.message.author.mention}?\n\nThis means that they will be kicked and not be able to re-join this server unless they are un-baned.\n\nNo messages will be deleted."
                else:
                    #if member is not in the server
                    description = f"Are you sure that you want to ban \"{self.message.author}\"?\n\nThis means that they will not be able to join this server unless they are un-baned.\n\nNo messages will be deleted."
                embed = nextcord.Embed(title = "Confirm Ban?", description = description, color = nextcord.Color.orange())
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def noBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                
            async def yesBtnCallback(self, interaction: Interaction):
                try:
                    await interaction.guild.ban(user = self.message.author, reason = f"{interaction.user} requested that this user be banned.", delete_message_seconds = 0)
                    await self.outer.disableAll(interaction)
                except Exception as error:
                    print(f"Error When Banning Member: {error}")
                    await self.outer.setup(interaction)
                    await interaction.followup.send(embed = nextcord.Embed(title = "An Unknown Error Occured", description = "An unknown error occured while performing this action.", color = nextcord.Color.red()), ephemeral = True)
                    
        async def callback(self, interaction: Interaction):
            await self.BanView(self.outer, self.message).setup(interaction)

@bot.message_command(name = "Options", dm_permission = True)
async def messageCommandOptions(interaction: Interaction, message: nextcord.Message):
    _hasRole = (await hasRole(interaction, notify = False) if interaction.guild else True)
    await MessageCommandOptionsView(interaction, message, _hasRole).setup(interaction)






#Bans: ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@bot.user_command(name = "Ban Member", dm_permission = False)
async def messageCommandBanMember(interaction: Interaction, member: nextcord.Member):
    if not utils.enabled.AutoBans(guild_id = interaction.guild.id):
        await interaction.response.send_message(embed = nextcord.Embed(title = "Banning Disabled", description = "Banning has been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
        return;
    
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
def persistent_warning_description(_type: str, max: str, uses: list):
    if not isinstance(_type, str):
        raise ValueError("Type must be a string!")
    if not (isinstance(max, str) or isinstance(max, int)):
        raise ValueError("Max must be an int or a string!")
    if not isinstance(uses, list) or uses == []:
        raise ValueError("Uses must be a list with content!")
    
    _type = _type.lower()
    max = str(max)
    
    # Add "and"
    uses[-1] = f"and {uses[-1]}"
    # Tie it together
    uses_str = ", ".join(uses)
    
    return (f"InfiniBot, similar to all free software, has its limitations. Regrettably, we are unable to continuously cache every {_type} ever created in our systems. Consequently, each server is allocated a maximum of {max} active (cached) {_type}s. As a result, there may come a point when this {_type} can no longer be edited.\n\n**What is Prioritizing?**\nPrioritizing ensures that this particular {_type} remains active indefinitely, enabling it to be edited well into the future. However, this comes at the expense of one of the server's active {_type} slots ({max}). This feature is particularly useful for {_type}s such as {uses_str}.") 

class EditEmbed(nextcord.ui.View):
    def __init__(self, messageID: int):
        super().__init__(timeout = None)
        self.messageID = messageID
        
    async def loadButtons(self, interaction: Interaction):
        self.message = await interaction.channel.fetch_message(self.messageID)
        self.server = Server_DEP(interaction.guild.id)
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
        
        if not utils.enabled.ActiveMessages(guild_id = interaction.guild.id):
            await disabled_feature_override(self, interaction)
            return
        
        mainEmbed = nextcord.Embed(title = "Edit Embed", description = "Edit the following embed's text and color.", color = nextcord.Color.yellow())
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
                
                originalColor = get_string_from_discord_color(self.outer.message.embeds[0].color)        
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
                description = standardize_str_indention(description)
    
                embed = nextcord.Embed(title = "Edit Color", description = description, color = nextcord.Color.yellow())
                await interaction.response.edit_message(embed = embed, view = self)
                    
            async def createCallback(self, interaction: Interaction):
                if self.select.values == []: return
                self.selection = self.select.values[0]
                self.stop()
                
                message = await interaction.channel.fetch_message(self.outer.message.id)
                await message.edit(embed = nextcord.Embed(title = message.embeds[0].title, description = message.embeds[0].description, color = (get_discord_color_from_string(self.selection))))
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
                messages = Messages(interaction.guild.id)
                max = messages.maxOf("Embed")
                
                
                embed = nextcord.Embed(title = "Edit Embed - Prioritize / Deprioritize", 
                                       description = persistent_warning_description(_type = "embed", max = max, uses = ["rules", "onboarding information", "similar content"]), 
                                       color = nextcord.Color.yellow())
                
                await interaction.response.edit_message(embed = embed, view = self)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
        
            class continueButton(nextcord.ui.Button):
                def __init__(self, outer, guildID: int, messageID: int):
                    self.server = Server_DEP(guildID)
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
        self.server = Server_DEP(interaction.guild.id)
        self.messageInfo = self.server.messages.get(self.messageID)
        
        self.clear_items()
        
        editTextBtn = self.editTextButton(self)
        self.add_item(editTextBtn)
        
        closeVoteBtn = self.closeVote(self, self.message.id)
        self.add_item(closeVoteBtn)
        
    async def setup(self, interaction: Interaction):
        await self.loadButtons(interaction)
        
        if not utils.enabled.ActiveMessages(guild_id = interaction.guild.id):
            await disabled_feature_override(self, interaction)
            return
        
        mainEmbed = nextcord.Embed(title = "Edit Vote", description = "Edit the text of the following vote or close the vote.", color = nextcord.Color.yellow())
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
                    server = Server_DEP(interaction.guild.id)
                    server.messages.delete(self.messageID)
                    server.messages.save()
                    
                    await self.outer.disableAll(interaction)
            
        async def callback(self, interaction: Interaction):
            await self.closeVoteView(self.outer, self.messageID).setup(interaction)
        
class EditReactionRole(nextcord.ui.View):
    def __init__(self, messageID: int):
        super().__init__(timeout = None)
        self.messageID = messageID
        
    async def loadButtons(self, interaction: Interaction):
        self.message = await interaction.channel.fetch_message(self.messageID)
        self.server = Server_DEP(interaction.guild.id)
        self.messageInfo = self.server.messages.get(self.messageID)
        
        self.clear_items()
        
        editTextBtn = self.editTextButton(self)
        self.add_item(editTextBtn)
        
        editOptionsBtn = self.editOptionsButton(self, self.messageInfo)
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
        
class EditRoleMessage(nextcord.ui.View):
    def __init__(self, messageID: int):
        super().__init__(timeout = None)
        self.messageID = messageID
        
        self.title = None
        self.description = None
        self.color = None
        self.options: list[list[list[int], str, str]] = []
        
    class EditTextButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Edit Text", emoji = "✏️")
            self.outer = outer;
        
        class EditTextModal(nextcord.ui.Modal):
            def __init__(self, outer):
                super().__init__(title = "Edit Text")
                self.outer = outer;
                
                self.titleInput = nextcord.ui.TextInput(label = "Title", min_length = 1, max_length = 256, placeholder = "Title", default_value = outer.title)
                self.add_item(self.titleInput)
                
                self.descriptionInput = nextcord.ui.TextInput(label = "Description", min_length = 1, max_length = 4000, placeholder = "Description", default_value = outer.description, style = nextcord.TextInputStyle.paragraph, required = False)
                self.add_item(self.descriptionInput)
                
            async def callback(self, interaction: Interaction):
                self.stop();
                self.outer.title = self.titleInput.value
                self.outer.description = self.descriptionInput.value
                
                await self.outer.setup(interaction)
        
        async def callback(self, interaction: Interaction):
            await interaction.response.send_modal(self.EditTextModal(self.outer))
        
    class EditColorButton(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Edit Color", emoji = "🎨")
            self.outer = outer
            
        class EditColorView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__()
                self.outer = outer;
                
                options = ["Red", "Green", "Blue", "Yellow", "White", "Blurple", "Greyple", "Teal", "Purple", "Gold", "Magenta", "Fuchsia"]
                
                originalColor = get_string_from_discord_color(self.outer.color)        
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
                description = f"""Choose what color you would like the role message to be:
                
                **Colors Available**
                Red, Green, Blue, Yellow, White
                Blurple, Greyple, Teal, Purple
                Gold, Magenta, Fuchsia"""
                
                
                # On Mobile, extra spaces cause problems. We'll get rid of them here:
                description = standardize_str_indention(description)
    
                embed = nextcord.Embed(title = "Edit Role Message - Edit Color", description = description, color = nextcord.Color.yellow())
                await interaction.response.edit_message(embed = embed, view = self)
                    
            async def createCallback(self, interaction: Interaction):
                if self.select.values == []: return
                self.selection = self.select.values[0]
                self.stop()
                
                self.outer.color = get_discord_color_from_string(self.selection)
                
                await self.outer.setup(interaction)
    
            async def backCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
    
        async def callback(self, interaction: Interaction):
            await self.EditColorView(self.outer).setup(interaction)
        
    class AddBtn(nextcord.ui.Button):
        def __init__(self, outer, options):
            super().__init__(label = "Add Option", style = nextcord.ButtonStyle.gray, disabled = (len(options) >= 25), emoji = "🔨")
                
            self.outer = outer
            self.options = options
            
        class AddView(nextcord.ui.View):
            def __init__(self, outer, options, index = None):
                super().__init__(timeout = None)
                self.outer = outer
                self.options = options
                self.index = index
                
                if self.index == None:
                    self.title = None
                    self.description = None
                    self.roles: list[int] = []
                    self.editing = False
                else:
                    self.title = self.options[index][1]
                    self.description = self.options[index][2]
                    self.roles: list[int] = self.options[index][0]
                    self.editing = True
                    
                # Make roles all ints
                self.roles = [int(role) for role in self.roles]
                
                changeTextBtn = nextcord.ui.Button(label = "Change Text")
                changeTextBtn.callback = self.changeTextBtnCallback
                self.add_item(changeTextBtn)
                
                self.addRoleBtn = nextcord.ui.Button(label = "Add Role")
                self.addRoleBtn.callback = self.addRoleBtnCallback
                self.add_item(self.addRoleBtn)
                
                self.removeRoleBtn = nextcord.ui.Button(label = "Remove Role")
                self.removeRoleBtn.callback = self.removeRoleBtnCallback
                self.add_item(self.removeRoleBtn)
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = (2 if len(self.outer.options) <= 1 else 1))
                self.backBtn.callback = self.backBtnCallback
                # Only add if this is not the first option
                if len(self.outer.options) > 0:
                    self.add_item(self.backBtn)
                
                self.finishBtn = nextcord.ui.Button(label = ("Finish" if not self.editing else "Save"), style = nextcord.ButtonStyle.blurple, row = 1)
                self.finishBtn.callback = self.finishBtnCallback
                self.add_item(self.finishBtn)
                
            async def validateData(self, interaction: Interaction):
                """Make sure you refresh the view after running this"""
                self.addableRoles = []
                for role in interaction.guild.roles:
                    if role.name == "@everyone": continue
                    if role.id in self.roles: continue
                    if canAssignRole(role):
                        self.addableRoles.append(nextcord.SelectOption(label = role.name, value = role.id))
                        
                self.removableRoles = []
                for role in self.roles:
                    discordRole = interaction.guild.get_role(role)
                    if discordRole:
                        self.removableRoles.append(nextcord.SelectOption(label = discordRole.name, value = role))
                    else:
                        self.removableRoles.append(nextcord.SelectOption(label = "~ Deleted Role ~", value = role, emoji = "⚠️"))
                    
                # Validate buttons
                self.addRoleBtn.disabled = len(self.addableRoles) == 0
                self.removeRoleBtn.disabled = len(self.removableRoles) <= 1
                
            async def setup(self, interaction: Interaction):
                # Validate Data
                await self.validateData(interaction)
                
                if len(self.roles) == 0 and not self.editing:
                    # Send the user past this view.
                    await self.addRoleBtnCallback(interaction)
                else:
                    if not self.editing:
                        embed = nextcord.Embed(title = "Edit Role Message - Add Option", description = "You have the option to add more roles or make changes to the text. Here is a mockup of what this option will look like:", color = nextcord.Color.yellow())
                    else:
                        embed = nextcord.Embed(title = "Edit Role Message - Edit Option", description = "You have the option to add more roles or make changes to the text. Here is a mockup of what this option will look like:", color = nextcord.Color.yellow())
                    
                    self.outer.addField(embed, [self.roles, self.title, self.description])
                    
                    await interaction.response.edit_message(embed = embed, view = self)
                    
            async def addRoleBtnCallback(self, interaction: Interaction):
                # Update Information
                await self.validateData(interaction)
                if self.addRoleBtn.disabled:
                    await self.setup(interaction)
                    return
                
                # Have 2 embeds. One for the first visit, and another for a re-visit
                if len(self.roles) == 0:
                    embed = nextcord.Embed(title = "Role Message Creation Wizard - Add Option", description = "Please select a role. This choice will be added as one of the options.\n\n**Unable to find a role?**\nIf you are unable to find a role, please ensure that InfiniBot has the necessary permissions to assign roles, such as managing messages and having a higher rank.", color = nextcord.Color.green())
                else:
                    embed = nextcord.Embed(title = "Role Message Creation Wizard - Add Option - Add Role", description = "Select a role to be granted when the user chooses this option.\n\n**Unable to find a role?**\nIf you are unable to find a role, please ensure that InfiniBot has the necessary permissions to assign roles, such as managing messages and having a higher rank.", color = nextcord.Color.green())
                await SelectView(embed = embed, options = self.addableRoles, returnCommand = self.addRoleBtnSelectViewCallback, placeholder = "Choose a Role", continueButtonLabel = "Use Role").setup(interaction)
                
            async def addRoleBtnSelectViewCallback(self, interaction: Interaction, value: str):
                if value == None:
                    # User canceled. Return them to us.
                    # Unless they actually came from the original view. If so, let's send them back to that.
                    if self.roles == []:
                        await self.outer.setup(interaction)
                        return
                    else:
                        await self.setup(interaction)
                        return
                    
                if value.isdigit():
                    self.roles.append(int(value))
                
                # Send them to the modal, or just back home
                if self.title == None:
                    await interaction.response.send_modal(self.OptionTitleAndDescriptionModal(self))
                else:
                    await self.setup(interaction)
                
            class OptionTitleAndDescriptionModal(nextcord.ui.Modal):
                def __init__(self, outer):
                    super().__init__(title = "Option Settings", timeout = None)
                    self.outer = outer

                    if self.outer.title == None:
                        self.titleInput = nextcord.ui.TextInput(label = "Please provide a name for that option", max_length = 100)
                    else:
                        self.titleInput = nextcord.ui.TextInput(label = "Option Name", max_length = 100, default_value = self.outer.title)
                    self.add_item(self.titleInput)
                    
                    if self.outer.description == None:
                        self.descriptionInput = nextcord.ui.TextInput(label = "Add a description (optional)", max_length = 100, required = False)
                    else:
                        self.descriptionInput = nextcord.ui.TextInput(label = "Description (optional)", max_length = 100, required = False, default_value = self.outer.description)
                    self.add_item(self.descriptionInput)
                    
                async def callback(self, interaction: Interaction):
                    self.outer.title = self.titleInput.value
                    self.outer.description = self.descriptionInput.value
                    
                    await self.outer.setup(interaction)
                                    
            async def changeTextBtnCallback(self, interaction: Interaction):
                await interaction.response.send_modal(self.OptionTitleAndDescriptionModal(self))
            
            async def removeRoleBtnCallback(self, interaction: Interaction): 
                # Update Information
                await self.validateData(interaction)
                if self.removeRoleBtn.disabled:
                    await self.setup(interaction)
                    return
                
                embed = nextcord.Embed(title = "Role Message Creation Wizard - Add Option - Remove Role", description = "Choose a role to be removed from this option.", color = nextcord.Color.green())
                await SelectView(embed = embed, options = self.removableRoles, returnCommand = self.removeRoleBtnSelectViewCallback, placeholder = "Choose a Role", continueButtonLabel = "Remove Role").setup(interaction)
                
            async def removeRoleBtnSelectViewCallback(self, interaction: Interaction, value: str):
                if value == None:
                    await self.setup(interaction)
                    return
                    
                if value.isdigit() and int(value) in self.roles:
                    self.roles.remove(int(value))
                
                await self.setup(interaction)
                
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
                            
            async def finishBtnCallback(self, interaction: Interaction):
                if not self.editing:
                    # Add data to self.outer.options in the form of list[list[int], str, str]
                    self.outer.options.append([self.roles, self.title, self.description])
                else:
                    self.outer.options[self.index] = [self.roles, self.title, self.description]
                
                await self.outer.setup(interaction)
                                
        async def callback(self, interaction: Interaction):
            await self.AddView(self.outer, self.options).setup(interaction)
    
    class EditBtn(nextcord.ui.Button):
        def __init__(self, outer, options):
            super().__init__(label = "Edit Option", emoji = "⚙️")
            self.outer = outer
            self.options: list[list[list[int], str, str]] = options
            
        async def callback(self, interaction: Interaction):
            # Get the options
            selectOptions = []
            for index, option in enumerate(self.options):
                selectOptions.append(nextcord.SelectOption(label = option[1], description = option[2], value = index))
            
            embed = nextcord.Embed(title = "Edit Role Message - Edit Option", description = "Choose an option to edit", color = nextcord.Color.yellow())
            await SelectView(embed = embed, options = selectOptions, returnCommand = self.selectViewCallback, continueButtonLabel = "Edit", preserveOrder = True).setup(interaction)
        
        async def selectViewCallback(self, interaction, selection):
            if selection == None:
                await self.outer.setup(interaction)
                return
                
            # Send them to the editing
            await self.outer.AddBtn.AddView(self.outer, self.options, index = int(selection)).setup(interaction)
     
    class RemoveBtn(nextcord.ui.Button):
        def __init__(self, outer, options):
            super().__init__(label = "Remove Option", disabled = (len(options) <= 1), emoji = "🚫")
            self.outer = outer
            self.options: list[list[list[int], str, str]] = options
            
        async def callback(self, interaction: Interaction):
            # Get the options
            selectOptions = []
            for index, option in enumerate(self.options):
                selectOptions.append(nextcord.SelectOption(label = option[1], description = option[2], value = index))
            
            embed = nextcord.Embed(title = "Edit Role Message - Remove Option", description = "Choose an option to remove", color = nextcord.Color.yellow())
            await SelectView(embed = embed, options = selectOptions, returnCommand = self.selectViewCallback, continueButtonLabel = "Remove", preserveOrder = True).setup(interaction)
        
        async def selectViewCallback(self, interaction, selection):
            if selection == None:
                await self.outer.setup(interaction)
                return
                
            self.outer.options.pop(int(selection))
            
            await self.outer.setup(interaction)
        
    class EditModeBtn(nextcord.ui.Button):
        def __init__(self, outer):
            super().__init__(label = "Change Mode", row = 1, emoji = "🎚️")
            self.outer = outer
            
        class MultiOrSingleSelectView(nextcord.ui.View):
            def __init__(self, outer):
                super().__init__(timeout = None)
                self.outer = outer
                
                options = [nextcord.SelectOption(label = "Single", description = "Members can only select one option", value = "Single", default = (self.outer.mode == "Single")),
                            nextcord.SelectOption(label = "Multiple", description = "Members can select multiple options.", value = "Multiple", default = (self.outer.mode == "Multiple"))]
                
                self.select = nextcord.ui.Select(options = options, placeholder = "Choose a Mode")
                self.add_item(self.select)
                
                self.backBtn = nextcord.ui.Button(label = "Back", style = nextcord.ButtonStyle.danger, row = 1) 
                self.backBtn.callback = self.backBtnCallback
                self.add_item(self.backBtn)
                
                self.createBtn = nextcord.ui.Button(label = "Change Mode", style = nextcord.ButtonStyle.blurple)
                self.createBtn.callback = self.createBtnCallback
                self.add_item(self.createBtn)
                
            async def setup(self, interaction: Interaction):
                embed = nextcord.Embed(title = "Edit Role Message - Change Mode", description = "Decide whether you want members to have the option to select multiple choices or just one.", color = nextcord.Color.yellow())
                await interaction.response.edit_message(embed = embed, view = self)
            
            async def backBtnCallback(self, interaction: Interaction):
                await self.outer.setup(interaction)
            
            async def createBtnCallback(self, interaction: Interaction):
                values = self.select.values
                if values == []:
                    return
                
                value = values[0]
                
                self.outer.mode = value
                
                await self.outer.setup(interaction)
            
        async def callback(self, interaction: Interaction):
            await self.MultiOrSingleSelectView(self.outer).setup(interaction)
       
    async def load(self, interaction: Interaction):
        self.message = await interaction.channel.fetch_message(self.messageID)
        self.server = Server_DEP(interaction.guild.id)
        self.messageInfo = self.server.messages.get(self.messageID)
        
        if self.title == None and self.description == None and self.color == None and self.options == []:
            self.title = self.message.embeds[0].title
            self.description = self.message.embeds[0].description
            self.color = self.message.embeds[0].color
            
            # Get options
            self.options = []
            for field in self.message.embeds[0].fields:
                name = field.name
                description = "\n".join(field.value.split("\n")[:-1])
                roles = self.extract_ids(field.value.split("\n")[-1])
                self.options.append([roles, name, description])
                
                
            # Get Mode
            self.mode = "Multiple"
            for component in self.message.components:
                if isinstance(component, nextcord.components.ActionRow):
                    for item in component.children:
                        if isinstance(item, nextcord.components.Button):
                            if item.custom_id == "get_roles":
                                self.mode = "Multiple"
                                break
                            elif item.custom_id == "get_role":
                                self.mode = "Single"
                                break
            self.currentMode = self.mode
            
        self.clear_items()
            
        # Load buttons   
        editTextBtn = self.EditTextButton(self)
        self.add_item(editTextBtn)
        
        editColorBtn = self.EditColorButton(self)
        self.add_item(editColorBtn)
        
        self.addBtn = self.AddBtn(self, self.options)
        self.add_item(self.addBtn)
        
        self.editBtn = self.EditBtn(self, self.options)
        self.add_item(self.editBtn)
        
        self.removeBtn = self.RemoveBtn(self, self.options)
        self.add_item(self.removeBtn)
        
        editModeBtn = self.EditModeBtn(self)
        self.add_item(editModeBtn)
        
        self.confirmBtn = nextcord.ui.Button(label = "Confirm Edits", style = nextcord.ButtonStyle.blurple, row = 1)
        self.confirmBtn.callback = self.confirmBtnCallback
        self.add_item(self.confirmBtn)
        
    async def setup(self, interaction: Interaction):
        await self.load(interaction)
        
        embed = nextcord.Embed(title = "Edit Role Message", description = "Edit your role message by making to the text, color, and options. Once finished, click on \"Confirm Edits\"", color = nextcord.Color.yellow())
        
        # Create a mockup of the embed
        roleMessageEmbed = self.createEmbed(self.title, self.description, self.color, self.options)
        
        embeds = [embed, roleMessageEmbed]
        
        # Give warning about mode if needed
        if self.mode != self.currentMode:
            warningEmbed = nextcord.Embed(title = "Warning: Mode Not Saved", description = "Be sure to Confirm Edits to save your mode.", color = nextcord.Color.red())
            embeds.append(warningEmbed)
        
        await interaction.response.edit_message(embeds = embeds, view = self)
        
    def createEmbed(self, title, description, color, options):
        embed = nextcord.Embed(title = title, description = description, color = color)
        for option in options:
            self.addField(embed, option)

        return embed
            
    def addField(self, embed: nextcord.Embed, optionInfo):
        mentions = [f"<@&{role}>" for role in optionInfo[0]]
        if len(mentions) > 1:
            mentions[-1] = f"and {mentions[-1]}"
        roles = ", ".join(mentions)
            
        title = optionInfo[1]
        description = optionInfo[2]
        
        spacer = ("\n" if description != "" else "")
        
        embed.add_field(name = title, value = f"{description}{spacer}> Grants {roles}", inline = False)
    
    def extract_ids(self, input_string):
        pattern = r"<@&(\d+)>"
        matches = re.findall(pattern, input_string)
        return matches
    
    async def disableView(self, interaction: Interaction):
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                child.disabled = True
                
        await interaction.response.edit_message(view = self, delete_after = 1.0)
    
    async def confirmBtnCallback(self, interaction: Interaction):
        roleMessageEmbed = self.createEmbed(self.title, self.description, self.color, self.options)
        
        await self.disableView(interaction)
        
        if self.mode == "Single":
            view = RoleMessageButton_Single()
        else:
            view = RoleMessageButton_Multiple()
        
        await self.message.edit(embed = roleMessageEmbed, view = view)
                            
    async def callback(self, interaction: Interaction):
        await self.RoleSelectWizardView(self.titleInput.value, self.descriptionInput.value).setup(interaction)
#Editing Messages END: ----------------------------------------------------------------------------------------------------------------------------------------------------------------




#Other Features: -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
@bot.slash_command(name = "motivational_statement", description = "Get, uh, a motivational statement", dm_permission=False)
async def motivationalStatement(interaction: Interaction):
    if not utils.enabled.MotivationalStatement(guild_id = interaction.guild.id):
        await interaction.response.send_message(embed = nextcord.Embed(title = "Motivational Statements Disabled", description = "Motivational Statements have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
        return;
    
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
    global nickname_changed
    
    if not interaction.user.guild_permissions.manage_nicknames:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Permission Error", description = "You do not have the \"manage nicknames\" permission which is required to use this command.", color =  nextcord.Color.red()), ephemeral=True)
        return
    if interaction.user.top_role.position <= member.top_role.position and interaction.user.id != member.id and interaction.user.id != interaction.guild.owner.id:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Permission Error", description = f"You do not have a higher role than {member}.", color =  nextcord.Color.red()), ephemeral=True)
        return
    if not interaction.channel.permissions_for(interaction.guild.me).manage_nicknames:
        await interaction.response.send_message(embed = nextcord.Embed(title = "Permission Error", description = "InfiniBot needs the Manage Nicknames permission for this action.", color =  nextcord.Color.red()), ephemeral=True)
        return
    
    if not interaction.guild_id in nickname_changed:
        nickname_changed.append(interaction.guild_id)
    
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
    if interaction.guild.id in nickname_changed:
        nickname_changed.pop(nickname_changed.index(interaction.guild.id))

#@set.subcommand(name = "default_role", description = "Set a default role that will be given to anyone who joins the server. (Requires Infinibot Mod)")
async def defaultRole(interaction: Interaction, role: nextcord.Role = SlashOption(description = "Leave blank to disable this feature.", required=False)):
    if not utils.enabled.DefaultRoles(guild_id = interaction.guild.id):
        await interaction.response.send_message(embed = nextcord.Embed(title = "Default Roles Disabled", description = "Default Roles have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
        return;
    
    if await hasRole(interaction):
        if role != None:
            botMember: nextcord.Member = await interaction.guild.fetch_member(bot.application_id)
            if role.position >= botMember.top_role.position:
                infinibotRole = getInfinibotTopRole(interaction.guild)
                await interaction.response.send_message(embed = nextcord.Embed(title = "Infinibot cannot grant this permission", description = f"{role.mention} is equal to or above the role {infinibotRole.mention}. Therefore, it cannot grant the role to any member.", color = nextcord.Color.red()), ephemeral=True)
                return
        
        server = Server_DEP(interaction.guild.id)
        if role != None: server.default_roles = role
        else: server.default_roles = []
        server.saveData()
        
        if role != None: await interaction.response.send_message(embed = nextcord.Embed(title = "Default Role Set", description = f"Any member who joins this server will get the role {role.mention}.\nAction done by {interaction.user}", color = nextcord.Color.green()))
        else: await interaction.response.send_message(embed = nextcord.Embed(title = "Default Role Disabled", description = f"Any member who joins this server will not recieve any role automatically by Infinibot\nAction done by {interaction.user}.", color = nextcord.Color.green()))

@create.subcommand(name = "embed", description = "Create a beautiful embed!")
async def createEmbed(interaction: Interaction, role: nextcord.Role = SlashOption(description = "Role to Ping", required = False)):
    if not utils.enabled.Embeds(guild_id = interaction.guild.id):
        await interaction.response.send_message(embed = nextcord.Embed(title = "Embeds Disabled", description = "Embeds have been disabled by the developers of InfiniBot. This is likely due to an critical instability with it right now. It will be re-enabled shortly after the issue has been resolved.", color = nextcord.Color.red()), ephemeral = True)
        return;
    
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
    description = standardize_str_indention(description)
    
    
    
    embed = nextcord.Embed(title = "Choose a Color", description = description, color = nextcord.Color.blue())
    view = EmbedColorView()
    
    await interaction.followup.send(embed = embed, view = view, ephemeral=True)
    
    await view.wait()
    
    color = view.selection
    
    
    #now, we have to process the color into something that our code can read:
    discordColor = get_discord_color_from_string(color)
    
    #noway, we just displ the embed!
    embed = nextcord.Embed(title = embedTitle, description = embedDescription, color = discordColor)
    interaction_response = await interaction.followup.send(content = content, embed = embed, wait = True)
    
    #finally, add the embed to our active messages for future editing
    server = Server_DEP(interaction.guild.id);
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
    description = f"""For help with InfiniBot, use `/help` followed by what you need help with.
    
    • Discord's autocomplete feature can be useful.
    
    For more help, join us at {support_server_link} or contact at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Help", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral=True, view = SupportAndInviteView())

@help.subcommand(name = "moderation_profanity", description = "Help with the Admin Channel, Strikes, Infinibot Mod, Flagged/Profane Words, and more.")
async def profanityModerationHelp(interaction: Interaction):
    description = f"""
    Out of the box, profanity moderation is mostly set up. To complete the setup, visit `/dashboard → Moderation → Profanity` and enable the feature.

    **Admin Channel Overview:**
    - When a member uses flagged words, their message is automatically deleted, and they receive a strike.
    - All strikes are reported to the Admin Channel, where admins can review and decide on their legitimacy.
        - Note: Ensure InfiniBot can view the channel and send messages.

    **Strike Handling:**
    - Admins can mark strikes as incorrect in the Admin Channel, refunding them to the member.
    - Admins can also view the original message that was automatically deleted.

    **Understanding Strikes:**
    - A single strike is not dangerous, but they can accumulate.
    - Upon reaching the server's maximum strikes (configured at `/dashboard → Moderation → Profanity`), a timed-out duration is applied.
    - After serving the timeout, the member resets to 0 strikes.

    **Strike Expire Time:**
    - In some servers, strikes can be cleared by waiting for the "strike expire time" (configured at `/dashboard → Moderation → Profanity`), which refunds one strike.

    **Managing Filtered Words:**
    - Add, delete, and view filtered words at `/dashboard → Moderation → Profanity → Filtered Words`.
        - Note: InfiniBot also detects variations of these words.

    **Disabling Profanity Moderation:**
    - If profanity moderation isn't suitable for your server, turn it off at `/dashboard → Moderation → Profanity → Disable Profanity Moderation`.

    **Extra Commands:**
    - `/view_strikes`: View another member's strikes. (Works without Infinibot Mod)
    - `/my_strikes`: View your own strikes. (Works without Infinibot Mod)
    - `/dashboard → Moderation → Profanity`: Configure specific features in Profanity Moderation.
    - `/dashboard → Moderation → Profanity → Manage Members`: View and configure strikes.

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Fine-Tune Profanity Moderation for Your Server", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())
    
@help.subcommand(name = "moderation_spam", description = "Help with spam moderation")
async def spamModerationHelp(interaction: Interaction):
    description = f"""Out of the box, spam moderation is pre-configured for your convenience. To activate it, head to `/dashboard → Moderation → Spam`.

    **Settings Customization:**
    Tailor spam moderation to suit your server's needs by adjusting specific features:
    - Navigate to `/dashboard → Moderation → Spam`.
    - Configure the timeout duration for the penalty when a member exceeds the spam threshold (Click on Timeout Duration).
    - Adjust the messages threshold (the number of messages triggering a timeout) to better align with your server's dynamics (Click on Messages Threshold).

    **Disabling Spam Moderation:**
    - If spam moderation isn't required, you can easily disable it at `/dashboard → Moderation → Spam → Disable Spam Moderation`.

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Streamline Your Server with Spam Moderation", description = description, color = nextcord.Color.greyple())
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
       
    
    For more help, join us at {support_server_link} or contact at infinibotassistance@gmail.com.
    """

    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    
    embed = nextcord.Embed(title = "How to use music with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())  

@help.subcommand(name = "voting", description = "Help with creating votes")
async def votingHelp(interaction: Interaction):
    description = f"""Voting in Discord made easy with InfiniBot.

    **Creating a Vote:**
    - Type `/create vote` and choose either "Letters" or "Numbers" as symbols for the votes.
    - Run the command, and a window will appear. Fill in the title, description, and options.
        - Tip: Ensure options are formatted with a comma and a space in between (e.g., ", ").
    - Click Submit.

    **Vote Reactions:**
    - If successful, reactions will be created for others to participate.
    - If reactions don't appear, check InfiniBot's permissions and ensure it can add reactions (also check channel permissions).

    **Letter Representation:**
    - If "Letters" was chosen, each option will be represented by the first letter of the choice. If the letter is already used, it defaults to "A," then "B," and so on.

    **Custom Votes:**
    - For custom votes, type `/create custom_vote` and format options like "Emoji = Option, Emoji = Option, Emoji = Option, etc."
    - Example: "😄 = Yes, 😢 = No"
    - Run the command, and choose the Title and Description.

    **Editing Votes:**
    - To edit a vote, right-click on the message, go to `Apps → Options → Edit → Edit Text`. Here, you can modify the vote text.
        - Tip: If the Edit option isn't visible, check that the message is from InfiniBot, is a vote, and is still an active message.

    **Closing Votes:**
    - To close a vote, right-click on the message, go to `Apps → Options → Edit → Close Vote`. This disables the vote and finalizes the results.
        - Tip: If the Edit option isn't visible, check that the message is from InfiniBot, is a vote, and is still an active message.

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Simplify Voting with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())

@help.subcommand(name = "reaction_roles", description = "Help with creating reaction roles")
async def reactionRolesHelp(interaction: Interaction):
    description = f"""
    **Note:** A new and improved version of reaction roles has been released. Type `/help role_messages` to learn more!

    **How to Use It:**
    - Type `/create reaction_role` and choose "Letters" or "Numbers" as symbols for reactions.
    - Run the command and a window will pop up. Fill in the title and description.
    - Click Submit, and a new message with a dropdown box will appear. Select the roles you want the reaction role to give.
    - Finally, click Create to see your reaction role come to life!

    **Reaction Role Details:**
    - If successful, reactions will be created for others to interact with.
    - If reactions don't appear, check InfiniBot's permissions, ensuring it can add reactions (also check channel permissions).

    **Letter Representation:**
    - If "Letters" was chosen, each option will be represented by the first letter of the choice. If the letter is already used, it defaults to "A," then "B," and so on.

    **Understanding Reaction Removal:**
    - When you react, you'll be given the corresponding role, and your reaction will be removed. To remove the role, react to the same letter again.

    **Troubleshooting Role Acquisition:**
    - If you didn't get the role after reacting, consider the following:
    1. The desired role may be equal to or higher than InfiniBot's highest role.
    2. Ensure InfiniBot has the "Manage Roles" permission.

    **Custom Reaction Roles:**
    - For custom reaction roles, type `/create custom_reaction_role` and format options like "Emoji = @role, Emoji = @role, Emoji = @role, etc."
    - Example: "👍 = @Member, 🥸 = @Gamer"

    **Editing Reaction Roles:**
    - To edit your reaction role, right-click, and go to `Apps → Options → Edit`. Edit the text and options.
        - Tip: If the Edit option isn't visible, check that the message is from InfiniBot, is a reaction role, and is still an active message.

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Set Up Reaction Roles with InfiniBot", description = description, color = nextcord.Color.greyple())
    
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView()) 

@help.subcommand(name = "role_messages", description = "Help with creating role messages")
async def roleMessagesHelp(interaction: Interaction):
    description = f"""Role messages allow members to assign themselves roles using a modern interface.
    
    **How to Use:**
    - Type `/create role_message` and choose "Get Started." You'll then be prompted to input the title of the role message and an optional description.
    - Afterward, you can edit your text or change the color. If you're satisfied, proceed to add roles by clicking "Next."
    - Creating an option involves choosing a role, providing a name, and an optional description for that option.
    - Customize the text or add/remove roles for the option. A single option can grant multiple roles.
    - Click "Finish" to reach a screen where you can edit every part of your role message, including adding, editing, or deleting more options.
    - Click "Finish" again, and choose whether the role message allows users to select a single option or multiple options.
    - Lastly, click "Create Role Message" to bring your role message to life!

    **Functionality:**
    - Members can click the button below the role message to be prompted to select available options.

    **Troubleshooting:**
    - If members encounter an error, they'll receive a prompt to report the issue to a server admin.
    - To resolve, check InfiniBot's "Manage Roles" permission and ensure InfiniBot has a higher role than any assigned roles.
    - If issues persist, submit a question/issue in our [support server]({support_server_link}).

    **Editing Role Messages:**
    - Right-click on the message and go to `Apps → Options → Edit` to modify the text, options, and mode of the role message.
        - Tip: If the Edit option is missing, confirm the message is from InfiniBot, is a role message, and is still active.

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Setting Up Role Messages:", description = description, color = nextcord.Color.greyple())
    
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView()) 

@help.subcommand(name = "join_and_leave_messages", description = "Help with join / leave messages")
async def joinLeaveMessagesHelp(interaction: Interaction):
    description = f"""
    **Setting up Join/Leave Messages:**
    - Navigate to `/dashboard → Join/Leave Messages`. Choose either "Join Message" or "Leave Message" and craft your desired message. To reference the joining member, include "[member]" in your message.
    - Now, InfiniBot will warmly welcome and bid farewell to members according to your preferences.

    **Disabling Join and Leave Messages**
    - If you don't need this feature, you can disable it by going to `/dashboard → Join/Leave Messages` and clearing the "Join Message" and "Leave Message" fields.

    **Additional Commands:**
    - Use `/dashboard → Join/Leave Messages → Join Message Channel` to specify where the join message will be sent.
    - Employ `/dashboard → Join/Leave Messages → Leave Message Channel` to configure the destination for leave messages.

    For further assistance, join us at {support_server_link} or reach out to us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Greet Your Members with Join/Leave Messages", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())  

@help.subcommand(name = "birthdays", description = "Help with birthdays")
async def birthdaysHelp(interaction: Interaction):
    description = f"""
    **Adding a Birthday:**
    - Visit `/dashboard → Birthdays → Add`. Select the member, proceed to the next step, and enter their birthday, formatted as month, day, year (MM/DD/YYYY).
    - Optionally, include their real name if you have it.
    - On their birthday at 8:00 AM MDT, InfiniBot will automatically extend birthday wishes on the server and through a direct message!

    **Editing and Deleting:**
    - Navigate to `/dashboard → Birthdays` to use both "Edit" and "Delete" in case of errors or if you no longer want InfiniBot to celebrate a particular birthday.

    **Additional Commands:**
    - Use `/dashboard → Birthdays → Delete All` to clear all birthdays in the server.

    For additional assistance, join us at {support_server_link} or reach out to us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Never Miss a Birthday Again with InfiniBot", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())  

@help.subcommand(name = "logging", description = "Help with logging.")
async def loggingHelp(interaction: Interaction):
    description = f"""Enable logging by going to `/dashboard → Logging`.

    **Log Channel Setup:**
    - Create a private channel dedicated to logs by going to `/dashboard → Logging → Log Channel`. Choose a channel for automatic logging.
    - Note: Ensure the chosen channel has application commands enabled, and InfiniBot has access to it.
        - Tip: Set channel notifications to "Nothing" as it will be consistently logging.

    **What Gets Logged:**
    - InfiniBot will log message deletions, edits, and server changes.

    **Slight Limitation:**
    - Discord has a minor limitation with deleted messages. As a result, logs may not always include the whole story. Click "More Information" on the message for specifics.

    **Not Interested in Logging?**
    - If logging doesn't suit your needs, turn it off at `/dashboard → Logging → Disable Logging`.

    For additional assistance, join us at {support_server_link} or reach out to us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Never Lose Track with Message Logging!", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())

@help.subcommand(name = "leveling", description = "Help with leveling and level rewards.")
async def levelingHelp(interaction: Interaction):
    description = f"""
    InfiniBot has a built-in system for leveling in your server. Enable it by going to `/dashboard → Leveling`.

    **Setting up Level Rewards:**
    - Create specific roles as rewards for reaching certain levels. Go to `/dashboard → Leveling → Level Rewards → Create`, choose the role, and set the corresponding level.
        - Tip: Avoid choosing excessively high levels; levels are calculated exponentially using the equation 0.1x^0.65, making each subsequent level harder to achieve.
    - Warning: Linking a role to a level reward will automatically remove the role from members who don't meet the level requirement.

    **Earning Points:**
    - Points are awarded based on the length of messages. Longer messages earn more points. Anti-spam measures are in place to ensure fair distribution.

    **Losing Points:**
    - Every day at midnight MDT, members lose a set amount of points. Adjust this amount at `/dashboard → Leveling → Points Lost Per Day`. Default is 2 points per day.

    **Disabling Leveling:**
    - If the leveling system doesn't suit your server, disable it at `/dashboard → Leveling → Disable Leveling`.

    **Extra Commands:**
    - `/leaderboard`: Check your rank within the server.
    - `/set level`: Set the level of any member via slash command.
    - `/dashboard → Leveling → Notification Channel`: Set a channel for level up and reward announcements.
    - `/dashboard → Leveling → Level Up Message`: Customize the message sent when someone levels up.
    - `/dashboard → Leveling → Manage Members → Reset`: Reset everyone in the server to level 0.

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Elevate Your Server with the Leveling System", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())

@help.subcommand(name = "other", description = "Help with other features.")
async def otherHelp(interaction: Interaction):
    description = f"""Explore some of InfiniBot's diverse features that don't fit into specific categories:

    **Purging Channels:**
    - To purge a channel, use `/purge all` to efficiently delete the entire channel's history.
    - Note: For large channels, `/purge all` is more efficient than deleting messages individually.
    - Alternatively, use `/purge #` to purge the channel of the last # messages.

    **Motivational Statement:**
    - Generate a motivational statement with `/motivational_statement` (if you squint).

    **Change Nickname:**
    - Modify a member's nickname with `/change_nick [member] [new nickname]` via a command.
        - Tip: Useful for larger servers where scrolling through the members list may be time-consuming.

    **Default Roles:**
    - Set default roles for new members at `/dashboard → Default Roles`. Up to 5 roles can be assigned to greet new members.

    **Delete Invites:**
    - Manage server invites by enabling this feature at `/dashboard → Enable/Disable Features → Delete Invites`.
        - Note: Users with the "Administrator" permission are immune to this feature.

    **Check InfiniBot's Permissions:**
    - Ensure InfiniBot has the necessary permissions by using `/check_infinibot_permissions`.

    **DM Commands:**
    - Right-click on any DM from InfiniBot, go to `Options → Delete Message` to remove a specific message.
    - Typing `del` in InfiniBot's DM channel deletes the last message sent to you.
    - Typing `clear` in InfiniBot's DM deletes all messages sent to you.
    - Opt in/out of DM notifications with `/opt_into_dms` and `/opt_out_of_dms`.

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Miscellaneous Features Overview", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView()) 

@help.subcommand(name = "infinibot_mod", description = "Help with Infinibot Mod.")
async def infinibotMod(interaction: Interaction):
    description = f"""Some features are restricted to administrators for enhanced control. If you are an admin, follow these steps:

    - Assign yourself the role "Infinibot Mod," which InfiniBot should have automatically created.
    - With the "Infinibot Mod" role, you'll gain complete access to InfiniBot and its features.

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "It says I need Infinibot Mod?", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView()) 

@help.subcommand(name = "join_to_create_vcs", description = "Help with Join To Create Voice Channels")
async def joinToCreateVoiceChannelsHelp(interaction: Interaction):
    description = f"""
    **Setting up Join-To-Create Voice Channel:**
    - Navigate to `/dashboard → Join-To-Create VCs → Configure → Add`.
    - Select your desired channel and click "Add."
        - Tip: If you don't see your voice channel, ensure InfiniBot has the necessary permissions to view it.

    **How it Works:**
    - Join the configured voice channel, and InfiniBot will create a personalized voice channel for you. Once everyone leaves, the channel automatically gets deleted.

    **Disabling the Feature:**
    - To disable Join-To-Create on a voice channel, go to `/dashboard → Join-To-Create VCs → Configure → Delete`.
    - Select the voice channel and click "Delete."

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Enjoy Clean and Convenient Voice Channels with Join-To-Create", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())  
    
@help.subcommand(name = "stats", description = "Help with Server Statistics messages")
async def statsHelp(interaction: Interaction):
    description = f"""
    **Setting up a Server Statistics Message:**
    - Execute `/setup_stats` in the desired channel where you want the Statistics message.
        - Tip: This message automatically updates every time a member joins or leaves the server.

    **Limitations on Multiple Messages:**
    - InfiniBot can only keep track of one Statistics message at a time since they are constantly updated.
    - If you want to move the message, simply run the command elsewhere, but it will deactivate the original message.

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Stay Informed with Server Statistics", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView())  
       
@help.subcommand(name = "auto_bans", description = "Help with Auto Bans")
async def autoBansHelp(interaction: Interaction):
    description = f"""
    **Auto-Banning a Member (Before Joining):**
    - Ensure InfiniBot has the "Ban Members" permission.
    - Visit `/dashboard → Auto-Bans → Add` and follow the instructions.
    - Once configured, members will be auto-banned the moment they join your server.

    **Revoking an Auto-Ban:**
    - Make sure InfiniBot has the "Ban Members" permission.
    - Access `/dashboard → Auto-Bans → Revoke` and select a member to revoke their auto-ban.
    - Click "Revoke Auto-Ban."

    **Banning a Member (In or After Leaving the Server):**
    - Confirm both you and InfiniBot have the "Ban Members" permission.
    - Right-click on the member or message, choose "Apps," and select either "Ban Member" or "Options → Ban Message Author."
        - Tip: If "Ban Message Author" is not visible, ensure both you and InfiniBot have permission to ban the user.
    - Click "Yes, ban" on the confirmation message.
    - The member is now banned from the server.

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Empower Your Moderation with InfiniBot's Ban Features", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView()) 
   
@help.subcommand(name = "embeds", description = "Help with Embeds")
async def embedsHelp(interaction: Interaction):
    description = f"""
    Discord's default messages are sleek, but when you need that extra flair, turn to embeds!

    **Creating an Embed:**
    - Type `/create embed` and select your title, text, and color.

    **Editing an Embed:**
    - Right-click on the embed, go to `Apps → Options → Edit`.
    - Modify the embed's title, description, and color as needed.

    For additional assistance, join us at {support_server_link} or contact us at infinibotassistance@gmail.com.
    """
    
    # On Mobile, extra spaces cause problems. We'll get rid of them here:
    description = standardize_str_indention(description)
    
    embed = nextcord.Embed(title = "Elevate Your Messages with Embeds", description = description, color = nextcord.Color.greyple())
    await interaction.response.send_message(embed = embed, ephemeral = True, view = SupportAndInviteView()) 
    
 
#Help END: ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------






@bot.slash_command("admin", guild_ids = dev_guilds)
async def admin(interaction: Interaction):
    pass

@admin.subcommand(name = "send_message_to_all_guilds", description = "Only usable by bot owner.")
async def sendMessageToAllGuilds(interaction: Interaction):
    modal = AdminModal()
    await interaction.response.send_modal(modal)
    
    await modal.wait()
    
    title = modal.titleValue
    description = modal.descriptionValue
    
    
    if interaction.user.id in dev_ids:

        embed = nextcord.Embed(title = title, description = description, color = nextcord.Color.gold())

        for guild in bot.guilds:
            try:
                # Do some special stuff if it's the InfiniBot server
                if guild.id == infinibot_guild_id:
                    channel = guild.get_channel(updates_channel_id)
                    role = guild.get_role(infinibot_updates_role_id)
                    await channel.send(content = role.mention, embed = embed, view = SupportAndInviteView())
                    print(f"Message sent to InfiniBot Server Updates Area")
                    
                else:
                    # If the server wants updates
                    server = Server_DEP(guild.id)
                    if not server.get_updates_enabled:
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
    if interaction.user.id in dev_ids:

        formattedGuilds = ""
        number = 1
        for guild in bot.guilds:
            server = Server_DEP(guild.id)
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
    with open("./CriticalFiles/AdminIDS.txt", "r") as file:
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
        • `-ping`: display InfiniBot latency diagnosis
        
        ### **Level 2**
        • `-info`: display info about a server or owner of a server that uses InfiniBot
        • `-resetServerConfigurations`: reset a server's configurations and set them back to default
        • `-checkActiveMessages`: check a server's active messages to make sure that they all exist
        • `-InfiniBotModHelp`: give a help message to those who need help with InfiniBotMod
        
        ### **Level 3**
        • `-refresh`: refresh InfiniBot
        • `-restart`: restart InfiniBot
        • `-globalKill`: globaly kill any feature of InfiniBot. Use `-globalKill help` for a list of use cases.
        • `-addAdmin`: add an admin
        • `-editAdmin`: edit an admin
        • `-deleteAdmin`: delete an admin"""
        
        # On Mobile, extra spaces cause problems. We'll get rid of them here:
        description = standardize_str_indention(description)
        
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
        
    if messageContent == "-ping" and message.author.id in levelOneAdmins:
        start_time = time.time()
        response_message = await message.channel.send(embed = nextcord.Embed(title = "InfiniBot Diagnosis Ping", description = "Pinging...", color = nextcord.Color.blue()))
        end_time = time.time()

        latency = (end_time - start_time) * 1000
        await response_message.edit(embed = nextcord.Embed(title = "InfiniBot Diagnosis Ping", description = f"InfiniBot pinged with a high-priority diagnosis ping. \n\nLatency: {latency:.2f} ms.", color = nextcord.Color.blue()))
        
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
            server = Server_DEP(guild.id)
            
            joined_at = guild.me.joined_at.replace(tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)
            duration = now - joined_at
            
            description = f"""Owner: {guild.owner} ({guild.owner.id})
            Members: {len(guild.members)}
            Bots: {len(guild.bots)}
            
            **Configurations:**
            {server.raw_data}
            
            **Time In Server**: {duration.days} days"""
            
            # On Mobile, extra spaces cause problems. We'll get rid of them here:
            description = standardize_str_indention(description)
            
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
        server = Server_DEP(id)
                
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
        server = Server_DEP(id)
                
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
        description = standardize_str_indention(description)
        
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
        
        global_kill_status.login_response_guildID = message.guild.id
        global_kill_status.login_response_channelID = message.channel.id
        global_kill_status.savePersistentData()
        
        python = sys.executable
        os.execl(python, python, * sys.argv)   
        
    if messageContentList[0] == "-globalkill" and message.author.id in levelThreeAdmins:
        if len(messageContentList) <= 1:
            await message.channel.send(embed = nextcord.Embed(title = "Incorrect Format", description = "Please include argument(s). Use the `-globalKill help` command for a list of arguments.", color = nextcord.Color.red()))
            return
        
        argument = messageContentList[1]
        
        commands = {
            'profanity_moderation': lambda value: setattr(global_kill_status, 'global_kill_profanity_moderation', value),
            'spam_moderation': lambda value: setattr(global_kill_status, 'global_kill_spam_moderation', value),
            'logging': lambda value: setattr(global_kill_status, 'global_kill_logging', value),
            'leveling': lambda value: setattr(global_kill_status, 'global_kill_leveling', value),
            'level_rewards': lambda value: setattr(global_kill_status, 'global_kill_level_rewards', value),
            'join_leave_messages': lambda value: setattr(global_kill_status, 'global_kill_join_leave_messages', value),
            'birthdays': lambda value: setattr(global_kill_status, 'global_kill_birthdays', value),
            'default_roles': lambda value: setattr(global_kill_status, 'global_kill_default_roles', value),
            'join_to_create_vcs': lambda value: setattr(global_kill_status, 'global_kill_join_to_create_vcs', value),
            'auto_bans': lambda value: setattr(global_kill_status, 'global_kill_auto_bans', value),
            'active_messages': lambda value: setattr(global_kill_status, 'global_kill_active_messages', value),
            'votes': lambda value: setattr(global_kill_status, 'global_kill_votes', value),
            'reaction_roles': lambda value: setattr(global_kill_status, 'global_kill_reaction_roles', value),
            'embeds': lambda value: setattr(global_kill_status, 'global_kill_embeds', value),
            'role_messages': lambda value: setattr(global_kill_status, 'global_kill_role_messages', value),
            'purging': lambda value: setattr(global_kill_status, 'global_kill_purging', value),
            'motivational_statements': lambda value: setattr(global_kill_status, 'global_kill_motivational_statements', value),
            'jokes': lambda value: setattr(global_kill_status, 'global_kill_jokes', value),
            'joke_submissions': lambda value: setattr(global_kill_status, 'global_kill_joke_submissions', value),
            'dashboard': lambda value: setattr(global_kill_status, 'global_kill_dashboard', value),
            'profile': lambda value: setattr(global_kill_status, 'global_kill_profile', value),
        }

        
        if argument.lower()  == "help":
            commandsString = "-globalKill "+"\n-globalKill ".join(commands.keys())
            
            embed = nextcord.Embed(title = "Global Kill Commands", description = f"### ONLY USE THESE COMMANDS FOR EMERGENCIES!!! THIS GOES INTO EFFECT GLOBALLY ACROSS ALL GUILDS INSTANTLY!!!\n\n{commandsString}", color = nextcord.Color.blue())
            await message.channel.send(embed = embed)
            return
        
        else:
            if argument.lower() in commands.keys():
                if len(messageContentList) >= 3:
                    action = None
                    if messageContentList[2].lower() == "kill":
                        action = True
                    elif messageContentList[2].lower() == "revive":
                        action = False
                    else:
                        await message.channel.send(embed = nextcord.Embed(title = "Invalid Argument", description = "Specify whether to `kill` or `revive`.", color = nextcord.Color.red()))
                        return
                    
                    commands[argument.lower()](action)
                    global_kill_status.savePersistentData()
                    global_kill_status.reload()
                    
                    # Description. Yeah, it's a mess, but it works and has perfect English.
                    description = f"{argument[0].capitalize()}{argument[1:].replace('_', ' ')} successfully {messageContentList[2]}{'e' if messageContentList[2].lower() == 'kill' else ''}d."
                    await message.channel.send(embed = nextcord.Embed(title = "Success", description = description, color = nextcord.Color.green()))
                    return
                
                else:
                    await message.channel.send(embed = nextcord.Embed(title = "Invalid Argument", description = "Specify whether to `kill` or `revive`.", color = nextcord.Color.red()))
                    return
            else:
                await message.channel.send(embed = nextcord.Embed(title = "Invalid Argument", description = "Use the `-globalKill help` command for a list of arguments.", color = nextcord.Color.red()))
                return
        
    if messageContentList[0] == "-addadmin" and message.author.id in levelThreeAdmins: #-addAdmin
        if len(messageContentList) > 2 and messageContentList[1].isdigit() and messageContentList[2].isdigit():
            userID = messageContentList[1]
            userLevel = int(messageContentList[2])
            if 0 < userLevel <= 3: #if level is within 1-3
                if not int(userID) in [admin[0] for admin in allAdmins]:
                    #everything is correct
                    with open("./CriticalFiles/AdminIDS.txt", "a") as file:
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
                    with open("./CriticalFiles/AdminIDS.txt", "r") as file:
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
                    
                    with open("./CriticalFiles/AdminIDS.txt", "w") as file:
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
                with open("./CriticalFiles/AdminIDS.txt", "r") as file:
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
                
                with open("./CriticalFiles/AdminIDS.txt", "w") as file:
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
with open("./generated/configure/TOKEN.txt", "r") as file:
    token = file.read().split("\n")[0]
    
    
bot.run(token)


#Infinibot: https://discord.com/api/oauth2/authorize?client_id=991832387015159911&permissions=8&scope=bot%20applications.commands

#Infinibot Testing: https://discord.com/api/oauth2/authorize?client_id=1005942420476796958&permissions=8&scope=bot%20applications.commands
#Infinibot Testing TopGG Invite: https://discord.com/api/oauth2/authorize?client_id=1005942420476796958&permissions=242736287296&scope=bot
