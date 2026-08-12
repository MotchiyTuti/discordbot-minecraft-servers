import asyncio
import os

import tomllib

from .util import send


async def command(message, command=None):
    roles = {role.name for role in message.author.roles}
    is_admin = roles & {"admin", "mod", "staff"}

    toml_path = os.path.join(os.path.dirname(__file__), "../message.toml")

    def load_toml():
        with open(toml_path, "rb") as f:
            return tomllib.load(f)

    toml_data = await asyncio.to_thread(load_toml)
    help_table = toml_data.get("help", {})

    if command:
        help_text = help_table.get(
            command, f"No detailed help available for `{command}`."
        )
    else:
        if is_admin:
            help_text = help_table.get("admin_list", "")
        else:
            help_text = help_table.get("user_list", "")

    await send.message(help_text, message)


async def main(command_args, message):
    if len(command_args) > 1:
        await command(message, command_args[1])
    else:
        await command(message)
