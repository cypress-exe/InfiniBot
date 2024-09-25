-- Start of File db_build.sql ---

-- Create profanity_moderation_profile Table (server table)
CREATE TABLE IF NOT EXISTS profanity_moderation_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    max_strikes INT DEFAULT 3,
    strike_expire_days INT DEFAULT 7,
    timeout_seconds INT DEFAULT 3600,
    custom_words TEXT DEFAULT '[]'
);

-- Create spam_moderation_profile Table (server table)
CREATE TABLE IF NOT EXISTS spam_moderation_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    messages_threshold INT DEFAULT 5,
    timeout_seconds INT DEFAULT 60
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
    allow_leveling_cards BOOL DEFAULT true
);

-- Create level_rewards Table (integrated list table)
CREATE TABLE IF NOT EXISTS level_rewards(
    server_id INT,
    role_id INT,
    level_number INT,
    PRIMARY KEY (server_id, role_id)
)

-- Create join_message_profile Table (server table)
CREATE TABLE IF NOT EXISTS join_message_profile( -- #optimize
    server_id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    embed TEXT DEFAULT '{"title":"@displayname just joined the server!","description":"Hello there, @member!"}',
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
    embed TEXT DEFAULT '{"title":"Happy Birthday, @realname!","description":"Hello there, @member!"}',
    runtime TEXT DEFAULT "8:00"
)

-- Create birthdays Table (integrated list table)
CREATE TABLE IF NOT EXISTS birthdays( -- #optimize
    server_id INT,
    member_id INT,
    birth_date DATE,
    real_name TEXT,
    PRIMARY KEY (server_id, member_id)
)

-- Create join_to_create_vcs Table (server table)
CREATE TABLE IF NOT EXISTS join_to_create_vcs( -- #optimize
    server_id INT PRIMARY KEY,
    channels TEXT DEFAULT '[]'
)

-- Create auto_bans Table (integrated list table)
CREATE TABLE IF NOT EXISTS auto_bans( -- #optimize
    server_id INT,
    member_id INT,
    member_name TEXT,
    PRIMARY KEY (server_id, member_id)
)