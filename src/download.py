import asyncio
import zipfile
from pathlib import Path

import discord

from .util import send, settings


async def main(command, message):
    if len(command) < 2:
        await send.message("Please specify the message ID.", message)
        return

    message_id = command[1]
    try:
        target_message = await message.channel.fetch_message(int(message_id))
    except discord.NotFound:
        await send.message("The specified message could not be found.", message)
        return
    except discord.Forbidden:
        await send.message("You do not have permission to fetch the message.", message)
        return
    except ValueError:
        await send.message("Invalid message ID.", message)
        return

    download_dir = Path(settings["paths"]["download_dir"]) / str(message_id)
    download_dir.mkdir(parents=True, exist_ok=True)

    message_file = download_dir / "message.md"

    def write_message():
        with message_file.open("w", encoding="utf-8") as f:
            f.write("# Message Content\n\n")
            f.write(f"Sender: {target_message.author.display_name}\n")
            f.write(f"Content:\n{target_message.content}\n")

    await asyncio.to_thread(write_message)

    for attachment in target_message.attachments:
        file_path = download_dir / attachment.filename
        await attachment.save(file_path)

    zip_path = download_dir.with_suffix(".zip")

    def create_zip():
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in download_dir.iterdir():
                info = zipfile.ZipInfo(file.name)
                info.flag_bits |= 0x800  # Set UTF-8 flag
                with open(file, "rb") as f:
                    zipf.writestr(info, f.read())

    await asyncio.to_thread(create_zip)

    public_url = f"https://motchiy.f5.si/discord-downloads/{message_id}.zip"
    await send.message(f"Download link: {public_url}", message)

    for file in download_dir.iterdir():
        file.unlink()
    download_dir.rmdir()
