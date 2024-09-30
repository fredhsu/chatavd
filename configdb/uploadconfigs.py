import os
import dotenv
from os.path import isfile, join
from pathlib import Path
import libsql_experimental as libsql

url = dotenv.get_key("../.env", "TURSO_DATABASE_URL")
auth_token = dotenv.get_key("../.env", "TURSO_AUTH_TOKEN")
conn = libsql.connect(database=url, auth_token=auth_token)

# insert the text files into the database with the filename as the name
configs_path = Path("/home/fred/avd-example/single-dc-l3ls/intended/configs/")
config_files = [
    join(configs_path, f)
    for f in os.listdir(configs_path)
    if isfile(join(configs_path, f))
]
print(config_files)
for config_file in config_files:
    with open(config_file, "r") as f:
        hostname = Path(config_file).with_suffix("").name
        conn.execute(
            f"INSERT INTO configs (hostname, config) VALUES ('{hostname}', '{f.read()}')"
        )


conn.commit()

# CREATE TABLE IF NOT EXISTS users (
#     id INTEGER PRIMARY KEY,
#     name TEXT,
#     age INTEGER
# );
#
# INSERT INTO users (name, age) VALUES ('Alice', 25);
# INSERT INTO users (name, age) VALUES ('Bob', 30);
#
# SELECT * FROM users;
#
# UPDATE users SET age = 26 WHERE name = 'Alice';
#
# SELECT * FROM users;
