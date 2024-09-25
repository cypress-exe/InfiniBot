-- Start of File test_db_build.sql ---

-- DO NOT USE IN PRODUCTION --

CREATE TABLE IF NOT EXISTS table_1( -- #optimize
    primary_key INT PRIMARY KEY,
    example_bool BOOLEAN DEFAULT false,
    example_channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    example_integer INT DEFAULT 3,
    example_list TEXT DEFAULT '[]'
);


CREATE TABLE IF NOT EXISTS table_2(
    primary_key_1 INT,
    primary_key_2 INT,
    example_integer INT,
    example_bool BOOLEAN DEFAULT false,
    PRIMARY KEY (primary_key_1, primary_key_2)
)

CREATE TABLE IF NOT EXISTS table_3( -- #optimize
    primary_key INT PRIMARY KEY,
    example_bool BOOLEAN DEFAULT false,
    example_channel TEXT DEFAULT '{"status": "UNSET", "value": null}',
    example_integer INT DEFAULT 3,
    example_list TEXT DEFAULT '[]'
);