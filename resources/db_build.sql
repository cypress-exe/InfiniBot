-- Start of File db_build.sql ---

-- Create Profanity Moderation Table (server table)
CREATE TABLE IF NOT EXISTS profanity_moderation( -- #optimize
    id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    max_strikes INT DEFAULT 3,
    strike_expire_days INT DEFAULT 7,
    timeout_seconds INT DEFAULT 3600,
    custom_words TEXT DEFAULT '[]'
);

-- Create Spam Moderation Table (server table)
CREATE TABLE IF NOT EXISTS spam_moderation( -- #optimize
    id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    messages_threshold INT DEFAULT 5,
    timeout_seconds INT DEFAULT 60
);

-- Create Logging Table (server table)
CREATE TABLE IF NOT EXISTS logging( -- #optimize
    id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}'
);

-- Create Leveling Table (server table)
CREATE TABLE IF NOT EXISTS leveling( -- #optimize
    id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    level_up_embed TEXT DEFAULT '{"title":"Congratulations, @displayname!","description":"Congrats @member! You reached level [level]!"}',
    points_lost_per_day INT DEFAULT 5,
    exempt_channels TEXT DEFAULT '[]',
    allow_leveling_cards BOOL DEFAULT true
);

-- Create Level Rewards Table (integrated list table)
CREATE TABLE IF NOT EXISTS level_rewards(
    server_id INT,
    role_id INT,
    level_number INT,
    PRIMARY KEY (server_id, role_id)
)

-- Create Join Message Table (server table)
CREATE TABLE IF NOT EXISTS join_message( -- #optimize
    id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    embed TEXT DEFAULT '{"title":"@displayname just joined the server!","description":"Hello there, @member!"}',
    allow_join_cards BOOLEAN DEFAULT true
);

-- Create Leave Message Table (server table)
CREATE TABLE IF NOT EXISTS leave_message( -- #optimize
    id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    embed TEXT DEFAULT '{"title":"@displayname just left the server.","description":"@member left."}'
);

-- Create Birthdays Table (server table)
CREATE TABLE IF NOT EXISTS birthdays( -- #optimize
    id INT PRIMARY KEY,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    embed TEXT DEFAULT '{"title":"Happy Birthday, @realname!","description":"Hello there, @member!"}',
    birthdays_list TEXT DEFAULT '[]',
    runtime TEXT DEFAULT "8:00"
)

-- Create Join To Create VCS Table (server table)
CREATE TABLE IF NOT EXISTS join_to_create_vcs( -- #optimize
    id INT PRIMARY KEY,
    channels TEXT DEFAULT '[]'
)

-- Create Auto-Bans Table (integrated list table)
CREATE TABLE IF NOT EXISTS auto_bans( -- #optimize
    server_id INT,
    member_id INT,
    member_name TEXT,
    PRIMARY KEY (server_id, member_id)
)