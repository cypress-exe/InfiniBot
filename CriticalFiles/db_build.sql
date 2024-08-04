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
    message_title TEXT DEFAULT 'Congratulations, @member!',
    message_description TEXT DEFAULT 'Congrats! You reached level [level]!',
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
    message_title TEXT DEFAULT '@member just joined the server!',
    message_description TEXT DEFAULT 'Hello there, @member!',
    allow_join_cards BOOLEAN DEFAULT true
);

-- Create Leave Message Table (server table)
CREATE TABLE IF NOT EXISTS leave_message( -- #optimize
    id INT PRIMARY KEY,
    active BOOLEAN DEFAULT false,
    channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    message_title TEXT DEFAULT '@member just left the server.',
    message_description TEXT DEFAULT '@member left.'
);