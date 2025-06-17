-- Start of File db_build.sql ---

-- <IMPORTANT> =======================================================================================
-- Tags like #optimize are used to mark tables that get optimized for size.
-- This is done automatically by the src.db.optimize function.
-- These "comments" are not actually comments, but are used to mark the tables for optimization.
-- DO NOT REMOVE THEM. THEY ARE IMPORTANT FOR THE FUNCTIONALITY OF THE DATABASE.
-- </IMPORTANT> ======================================================================================

-- Simple tables are tables that are used to store simple data.
-- They have a default state for each variable which is set when a new table entry is created.
-- If they are marked with #optimize, then when all values for a server_id are equal to the default 
-- value, the entry is removed from the table to save space.

-- Integrated lists are tables that are used to store data that has two keys.
-- Can be queried more efficiently for two-keyed data.
-- They are abstracted into a dictionary in the src.core.db_manager.integrated_list class.
-- When instantiated under a src.config.server.Server, they are automatically created and managed,
-- filtered for the server_id and keyed by the secondary key.

-- Message logs are tables that are used to store messages for log messages.
-- They are handled by the src.config.stored_messages module.





-- START OF PROFILES
-- Create profanity_moderation_profile Table (simple table)
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

-- Create spam_moderation_profile Table (simple table)
CREATE TABLE IF NOT EXISTS spam_moderation_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    score_threshold INT DEFAULT 100,
    time_threshold_seconds INT DEFAULT 60,
    timeout_seconds INT DEFAULT 60,
    delete_invites BOOLEAN DEFAULT false
);

-- Create logging_profile Table (simple table)
CREATE TABLE IF NOT EXISTS logging_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}'
);

-- Create leveling_profile Table (simple table)
CREATE TABLE IF NOT EXISTS leveling_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    level_up_embed TEXT DEFAULT '{"title":"Congratulations, @displayname!","description":"Congrats @mention! You reached level [level]!", "color":"White"}',
    points_lost_per_day INT DEFAULT 0,
    max_points_per_message INT DEFAULT 40,
    exempt_channels TEXT DEFAULT '[]',
    allow_leveling_cards BOOLEAN DEFAULT true
);

-- Create join_message_profile Table (simple table)
CREATE TABLE IF NOT EXISTS join_message_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    embed TEXT DEFAULT '{"title":"@displayname just joined the server!","description":"Welcome to the server, @mention!", "color":"Blurple"}',
    allow_join_cards BOOLEAN DEFAULT true
);

-- Create leave_message_profile Table (simple table)
CREATE TABLE IF NOT EXISTS leave_message_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    embed TEXT DEFAULT '{"title":"@displayname just left the server.","description":"@mention left.", "color":"Blurple"}'
);

-- Create birthdays_profile Table (simple table)
CREATE TABLE IF NOT EXISTS birthdays_profile( -- #optimize
    server_id INT PRIMARY KEY,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    embed TEXT DEFAULT '{"title":"Happy Birthday, [realname]!","description":"@mention just turned [age]!", "color":"Gold"}',
    runtime TEXT DEFAULT '{"status": "UNSET", "value": null}'
)

-- Create infinibot_settings_profile Table (simple table)
CREATE TABLE IF NOT EXISTS infinibot_settings_profile( -- #optimize
    server_id INT PRIMARY KEY,
    delete_invites BOOLEAN DEFAULT false,
    get_updates BOOLEAN DEFAULT true,
    timezone TEXT DEFAULT '{"status": "UNSET", "value": null}'
)

-- Create member_profile Table (simple table)
CREATE TABLE IF NOT EXISTS member_profile( -- #optimize
    member_id INT PRIMARY KEY,
    level_up_card_enabled BOOLEAN DEFAULT false,
    join_card_enabled BOOLEAN DEFAULT false,
    level_up_card_embed TEXT DEFAULT '{"title":"Yum... Levels","description":"I am level [level]!","color":"Purple"}',
    join_card_embed TEXT DEFAULT '{"title":"About Me","description":"I am human","color":"Green"}',
    direct_messages_enabled BOOLEAN DEFAULT true
)


-- START of SIMPLE LISTS
-- Create join_to_create_vcs Table (simple table)
CREATE TABLE IF NOT EXISTS join_to_create_vcs( -- #optimize
    server_id INT PRIMARY KEY,
    channels TEXT DEFAULT '[]'
)

-- Create default_roles Table (simple table)
CREATE TABLE IF NOT EXISTS default_roles( -- #optimize
    server_id INT PRIMARY KEY,
    default_roles TEXT DEFAULT '[]'
)






-- START of INTEGRATED LISTS
-- Create moderation_strikes Table (integrated list table)
CREATE TABLE IF NOT EXISTS moderation_strikes(
    server_id INT, -- primary key
    member_id INT, -- secondary key
    strikes INT,
    last_strike DATETIME,
    PRIMARY KEY (server_id, member_id)
)

-- Create member_levels Table (integrated list table)
CREATE TABLE IF NOT EXISTS member_levels(
    server_id INT, -- primary key
    member_id INT, -- secondary key
    points INT,
    PRIMARY KEY (server_id, member_id)
)

-- Create level_rewards Table (integrated list table)
CREATE TABLE IF NOT EXISTS level_rewards(
    server_id INT, -- primary key
    role_id INT, -- secondary key
    level INT, -- "level" is technically an SQL keyword, but it doesn't seem to cause an issue here.
    PRIMARY KEY (server_id, role_id)
)

-- Create birthdays Table (integrated list table)
CREATE TABLE IF NOT EXISTS birthdays(
    server_id INT, -- primary key
    member_id INT, -- secondary key
    birth_date DATE,
    real_name TEXT,
    PRIMARY KEY (server_id, member_id)
)

-- Create autobans Table (integrated list table)
CREATE TABLE IF NOT EXISTS autobans(
    server_id INT, -- primary key
    member_id INT, -- secondary key
    member_name TEXT,
    PRIMARY KEY (server_id, member_id)
)


-- START of MESSAGE LOGS
-- Create managed_messages table (integrated list table)
CREATE TABLE IF NOT EXISTS managed_messages(
    server_id INT, -- primary key
    message_id INT, -- secondary key
    channel_id INT,
    author_id INT,
    message_type TEXT,
    json_data TEXT,
    PRIMARY KEY (server_id, message_id)
)


-- Create Message Logging table (Custom table managed by src.config.stored_messages)
-- This table is used to store messages for log messages.
CREATE TABLE IF NOT EXISTS messages ( 
    message_id INTEGER PRIMARY KEY,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_guild_time ON messages (guild_id, last_updated);