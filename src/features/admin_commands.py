import datetime

import nextcord

from config.file_manager import JSONFile

async def check_and_run_admin_commands(message: nextcord.Message):
    return # TODO
    message_content = message.content.lower()
    message_content_list = message_content.split(" ")
    
    
    #get admins
    admins = JSONFile("./CriticalFiles/AdminIDS.txt").read()
        
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
    
    if message_content == "-help" and message.author.id in levelOneAdmins: #-help
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
    
    if message_content == "-stats" and message.author.id in levelOneAdmins: #-stats
        membercount = 0
        servercount = 0
        
        print(f"Guilds requested by: {message.author}")
        for guild in bot.guilds:
            servercount += 1
            membercount += guild.member_count

        embed = nextcord.Embed(title = "Server Stats:", description = f"Server Count: {str(servercount)}\nTotal Members: {str(membercount)}\n\n*A watched pot never boils*", color = nextcord.Color.blue())
        await message.channel.send(embed = embed, view = TopGGVoteView())
        return
        
    if message_content == "-ping" and message.author.id in levelOneAdmins:
        start_time = time.time()
        response_message = await message.channel.send(embed = nextcord.Embed(title = "InfiniBot Diagnosis Ping", description = "Pinging...", color = nextcord.Color.blue()))
        end_time = time.time()

        latency = (end_time - start_time) * 1000
        await response_message.edit(embed = nextcord.Embed(title = "InfiniBot Diagnosis Ping", description = f"InfiniBot pinged with a high-priority diagnosis ping. \n\nLatency: {latency:.2f} ms.", color = nextcord.Color.blue()))
        
    # Level 2 ----------------------------------------------------------------------
        
    if message_content_list[0] == "-info" and message.author.id in levelTwoAdmins:
        if not (len(message_content_list) > 1 and message_content_list[1].isdigit()):
            embed = nextcord.Embed(title = "Incorrect Format", description = f"Format like this: `-info [serverID or ownerID]`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return
        
        id = int(message_content_list[1])
        
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
            
    if message_content_list[0] == "-resetserverconfigurations" and message.author.id in levelTwoAdmins:
        if not (len(message_content_list) > 1 and message_content_list[1].isdigit()):
            embed = nextcord.Embed(title = "Incorrect Format", description = f"Format like this: `-resetserverconfigurations [serverID]`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return
        
        id = int(message_content_list[1])
        
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
        
    if message_content_list[0] == "-checkactivemessages" and message.author.id in levelTwoAdmins:
        if not (len(message_content_list) > 1 and message_content_list[1].isdigit()):
            embed = nextcord.Embed(title = "Incorrect Format", description = f"Format like this: `-checkActiveMessages [serverID]`", color = nextcord.Color.red())
            await message.channel.send(embed = embed)
            return
        
        id = int(message_content_list[1])
        
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
    if message_content == "-infinibotmodhelp" and message.author.id in levelTwoAdmins:
        description = f"""**It says I need Infinibot Mod?**
        • Some features are locked down so that only admins can use them. If you are an admin, go ahead and assign yourself the role Infinibot Mod (which should have been automatically created by InfiniBot). Once you have this role, you will have full access to InfiniBot and its features.
        
        • If this role does not appear, try one of these two things:
            → Make sure that InfiniBot has the Manage Roles permission
            → Create a role named "Infinibot Mod" (exact same spelling) with no permissions"""
            
        # On Mobile, extra spaces cause problems. We'll get rid of them here:
        description = standardize_str_indention(description)
        
        await message.channel.send(embed = nextcord.Embed(title = "InfiniBot Mod Help", description = description, color = nextcord.Color.blurple()))
     
    # Level 3 ----------------------------------------------------------------------   
    
    if message_content == "-refresh" and message.author.id in levelThreeAdmins: #-reset
        guildsCheckingForRole = []
        purging = []

        embed = nextcord.Embed(title = "Infinibot Refreshed", description = "GuildsCheckingForRole and Purging has been reset.", color = nextcord.Color.green())
        await message.channel.send(embed = embed)
        print(f"{message.author} refeshed InfiniBot")
        
    if message_content == "-restart" and message.author.id in levelThreeAdmins:
        embed = nextcord.Embed(title = "InfiniBot Restarting", description = "InfiniBot is restarting.", color = nextcord.Color.green())
        await message.channel.send(embed = embed)
        
        print(f"{message.author} requested InfiniBot to be restarted. Restarting...")
        
        global_kill_status.login_response_guildID = message.guild.id
        global_kill_status.login_response_channelID = message.channel.id
        global_kill_status.savePersistentData()
        
        python = sys.executable
        os.execl(python, python, * sys.argv)   
        
    if message_content_list[0] == "-globalkill" and message.author.id in levelThreeAdmins:
        if len(message_content_list) <= 1:
            await message.channel.send(embed = nextcord.Embed(title = "Incorrect Format", description = "Please include argument(s). Use the `-globalKill help` command for a list of arguments.", color = nextcord.Color.red()))
            return
        
        argument = message_content_list[1]
        
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
                if len(message_content_list) >= 3:
                    action = None
                    if message_content_list[2].lower() == "kill":
                        action = True
                    elif message_content_list[2].lower() == "revive":
                        action = False
                    else:
                        await message.channel.send(embed = nextcord.Embed(title = "Invalid Argument", description = "Specify whether to `kill` or `revive`.", color = nextcord.Color.red()))
                        return
                    
                    commands[argument.lower()](action)
                    global_kill_status.savePersistentData()
                    global_kill_status.reload()
                    
                    # Description. Yeah, it's a mess, but it works and has perfect English.
                    description = f"{argument[0].capitalize()}{argument[1:].replace('_', ' ')} successfully {message_content_list[2]}{'e' if message_content_list[2].lower() == 'kill' else ''}d."
                    await message.channel.send(embed = nextcord.Embed(title = "Success", description = description, color = nextcord.Color.green()))
                    return
                
                else:
                    await message.channel.send(embed = nextcord.Embed(title = "Invalid Argument", description = "Specify whether to `kill` or `revive`.", color = nextcord.Color.red()))
                    return
            else:
                await message.channel.send(embed = nextcord.Embed(title = "Invalid Argument", description = "Use the `-globalKill help` command for a list of arguments.", color = nextcord.Color.red()))
                return
        
    if message_content_list[0] == "-addadmin" and message.author.id in levelThreeAdmins: #-addAdmin
        if len(message_content_list) > 2 and message_content_list[1].isdigit() and message_content_list[2].isdigit():
            userID = message_content_list[1]
            userLevel = int(message_content_list[2])
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

    if message_content_list[0] == "-editadmin" and message.author.id in levelThreeAdmins: #-editAdmin
        if len(message_content_list) > 2 and message_content_list[1].isdigit() and message_content_list[2].isdigit():
            userID = int(message_content_list[1])
            userLevel = int(message_content_list[2])
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

    if message_content_list[0] == "-deleteadmin" and message.author.id in levelThreeAdmins: #-deleteAdmin
        if len(message_content_list) > 1 and message_content_list[1].isdigit():
            userID = int(message_content_list[1])
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