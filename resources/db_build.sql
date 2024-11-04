-- Start of File db_build.sql ---



-- START OF PROFILES
-- Create profanity_moderation_profile Table (server table)
CREATE TABLE IF NOT EXISTS profanity_moderation_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    strike_system_active BOOLEAN DEFAULT true,
    max_strikes INT DEFAULT 3,
    strike_expiring_active BOOLEAN DEFAULT true,
    strike_expire_days INT DEFAULT 7,
    timeout_seconds INT DEFAULT 3600,
    filtered_words TEXT DEFAULT '[]'
);

-- Create spam_moderation_profile Table (server table)
CREATE TABLE IF NOT EXISTS spam_moderation_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    messages_threshold INT DEFAULT 5,
    timeout_seconds INT DEFAULT 60,
    delete_invites BOOLEAN DEFAULT false
);

-- Create logging_profile Table (server table)
CREATE TABLE IF NOT EXISTS logging_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}'
);

-- Create leveling_profile Table (server table)
CREATE TABLE IF NOT EXISTS leveling_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    level_up_embed TEXT DEFAULT '{"title":"Congratulations, @displayname!","description":"Congrats @member! You reached level [level]!"}',
    points_lost_per_day INT DEFAULT 5,
    exempt_channels TEXT DEFAULT '[]',
    allow_leveling_cards BOOLEAN DEFAULT true
);

-- Create join_message_profile Table (server table)
CREATE TABLE IF NOT EXISTS join_message_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    embed TEXT DEFAULT '{"title":"@displayname just joined the server!","description":"Welcome to the server, @member!"}',
    allow_join_cards BOOLEAN DEFAULT true
);

-- Create leave_message_profile Table (server table)
CREATE TABLE IF NOT EXISTS leave_message_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    embed TEXT DEFAULT '{"title":"@displayname just left the server.","description":"@member left."}'
);

-- Create birthdays_profile Table (server table)
CREATE TABLE IF NOT EXISTS birthdays_profile( -- #optimize
    server_id INT PRIMARY KEY,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    embed TEXT DEFAULT '{"title":"Happy Birthday, @realname!","description":"@member just turned @age!"}',
    runtime TEXT DEFAULT "8:00"
)

-- Create infinibot_settings_profile Table (server table)
CREATE TABLE IF NOT EXISTS infinibot_settings_profile( -- #optimize
    server_id INT PRIMARY KEY,
    get_updates BOOLEAN DEFAULT true
)


-- START of SIMPLE LISTS
-- Create join_to_create_vcs Table (server table)
CREATE TABLE IF NOT EXISTS join_to_create_vcs( -- #optimize
    server_id INT PRIMARY KEY,
    channels TEXT DEFAULT '[]'
)

-- Create default_roles Table (server table)
CREATE TABLE IF NOT EXISTS default_roles( -- #optimize
    server_id INT PRIMARY KEY,
    default_roles TEXT DEFAULT '[]'
)






-- START of INTEGRATED LISTS
-- Create moderation_strikes Table (integrated list table)
CREATE TABLE IF NOT EXISTS moderation_strikes(
    server_id INT,
    member_id INT,
    strikes INT,
    last_strike DATETIME,
    PRIMARY KEY (server_id, member_id)
)

-- Create level_rewards Table (integrated list table)
CREATE TABLE IF NOT EXISTS level_rewards(
    server_id INT,
    role_id INT,
    level INT,
    PRIMARY KEY (server_id, role_id)
)

-- Create birthdays Table (integrated list table)
CREATE TABLE IF NOT EXISTS birthdays(
    server_id INT,
    member_id INT,
    birth_date DATE,
    real_name TEXT,
    PRIMARY KEY (server_id, member_id)
)

-- Create auto_bans Table (integrated list table)
CREATE TABLE IF NOT EXISTS auto_bans(
    server_id INT,
    member_id INT,
    member_name TEXT,
    PRIMARY KEY (server_id, member_id)
)



-- START of MESSAGE LOGS
-- Create embeds table (integrated list table)
CREATE TABLE IF NOT EXISTS embeds(
    server_id INT,
    message_id INT,
    channel_id INT,
    author_id INT,
    PRIMARY KEY (server_id, message_id)
)

-- Create reaction_roles table (integrated list table)
CREATE TABLE IF NOT EXISTS reaction_roles(
    server_id INT,
    message_id INT,
    channel_id INT,
    author_id INT,
    PRIMARY KEY (server_id, message_id)
)

-- Create role_messages table (integrated list table)
CREATE TABLE IF NOT EXISTS role_messages(
    server_id INT,
    message_id INT,
    channel_id INT,
    author_id INT,
    PRIMARY KEY (server_id, message_id)
)