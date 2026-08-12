import asyncio
import os
import traceback
from pathlib import Path

import discord
import pymysql
import tomllib

from src import auth, config, download, help, present, start, status, stop
from src.util import get_permission, hasPermission, load_settings, send

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Login as {client.user}.")
    await main()


@client.event
async def on_message(message):
    # メッセージを処理
    if message.author.bot:
        return

    content = message.content
    if not content.startswith("!"):
        return

    command = content[1:].split()
    if len(command) < 1:
        await send.message("Invalid command format.", message)
        return

    action = command[0]

    if action == "perm":
        if len(command) < 2:
            perm = get_permission(message.author)
            await send.message(
                f"{message.author.display_name} の権限: {perm!s}", message
            )
            return
        name = command[1]
        member = discord.utils.find(
            lambda m: m.name == name or m.display_name == name, message.guild.members
        )
        if member is None:
            await send.message(f"ユーザー {name!r} が見つかりません。", message)
            return
        perm = get_permission(member)
        await send.message(f"{member.display_name} の権限: {perm!s}", message)
        return

    try:
        # everyone commands
        if action in ["status", "help"]:
            if action == "status":
                await status.main(command, message)
            elif action == "help":
                await help.main(command, message)
            return

        # staff commands
        if hasPermission(message.author, "staff") and action == "dl":
            await download.main(command, message)
            return

        # mod commands
        if hasPermission(message.author, "mod"):
            if action == "start":
                await start.main(command, message)
                return
            elif action == "stop":
                await stop.main(command, message)
                return
            elif action == "allow":
                await auth.allow(message, *command[1:])
                return
            elif action == "deny":
                await auth.deny(message, *command[1:])
                return
            elif action == "restart":
                await start.restart(message, *command[1:])
                return

        # admin commands
        if hasPermission(message.author, "admin"):
            if action == "startup":
                await config.default.main(command, message)
            if action == "present":
                await present.main(message)
                return

        await send.message("You do not have permission or the command is invalid.", message)

    except Exception as e:  # noqa
        tb = traceback.extract_tb(e.__traceback__)
        if tb:
            last = tb[-1]
            file_info = f'File "{last.filename}", line {last.lineno}'
        else:
            file_info = "No traceback info"
        await send.message(f"Error: {e!s}\n{file_info!s}", message)


def run_bot():
    token_file = Path("token.txt")
    if token_file.exists():
        client.run(token_file.read_text(encoding="utf-8").strip())
    else:
        print("Error: token.txt not found.")


async def main():
    """
    Check if the MySQL connection can be established and send a message.
    """
    settings = load_settings()
    mysql_toml_path = settings["paths"]["mysql_toml"]
    developer_channel_id = settings["channel_ids"]["developer"]
    developer_channnel = await client.fetch_channel(developer_channel_id)

    print(f"MySQL configuration path: {mysql_toml_path}")
    if not os.path.exists(mysql_toml_path):
        default_mysql_config = """host = "127.0.0.1"
user = ""
password = ""
database = ""
"""
        def write_default():
            with open(mysql_toml_path, "w", encoding="utf-8") as f:
                f.write(default_mysql_config)

        await asyncio.to_thread(write_default)
        print("mysql.toml が存在しなかったため、デフォルト設定で生成しました。")

    def load_config():
        with open(mysql_toml_path, "rb") as f:
            return tomllib.load(f)

    config = await asyncio.to_thread(load_config)

    config_message = "\n".join(
        [
            f"**{key}**: `{value}`" if key != "password" else "**password**: `****`"
            for key, value in config.items()
        ]
    )
    await send.message(
        f"**Loaded MySQL Configuration:**\n{config_message}", developer_channnel
    )

    try:
        connection = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            port=config.get("port", 3306),
        )
        connection.close()
        await send.message("MySQLに正常に接続できました。", developer_channnel)
    except pymysql.err.Error as e:
        await send.message(f"MySQL接続エラー: {e}", developer_channnel)


if __name__ == "__main__":
    token_file = Path("token.txt")
    if token_file.exists():
        client.run(token_file.read_text(encoding="utf-8").strip())
    else:
        print("Error: token.txt not found.")
