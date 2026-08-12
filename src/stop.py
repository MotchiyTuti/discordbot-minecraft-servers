import asyncio
import subprocess

from . import status
from .util import execute, send, settings, system_messages


async def server(message, server_name, status, command):
    if status == "waiting":
        await send.message(f"{server_name} is already stopped!", message)
        return
    backend_name = server_name + "_sv"
    close_command = "end" if "-p" in command else "stop"

    try:
        def check_session():
            return subprocess.run(
                f"tmux has-session -t {backend_name}",
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )

        check = await asyncio.to_thread(check_session)
        if check.returncode != 0:
            await send.message(
                f"No TMUX session named `{backend_name}` found. ({server_name} is not running)",
                message,
            )
            return

        execute(f'tmux send-keys -t {backend_name} "{close_command}" ENTER')
        execute(f"tmux kill-session -t {backend_name}")
        await send.message(f"{server_name} has been stopped!", message)
    except subprocess.CalledProcessError as e:
        await send.message(f"Failed to stop `{backend_name}`: {e}", message)
    except (subprocess.SubprocessError, OSError) as e:
        await send.message(
            f"An unexpected error occurred while closing `{backend_name}`: {e}", message
        )


async def all(message):
    try:
        def list_sessions():
            return subprocess.run(
                f"{settings['paths']['tmux_executable']} list-sessions -F '#S'",
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )

        result = await asyncio.to_thread(list_sessions)
        sessions = result.stdout.strip().split("\n")
        filtered_sessions = [s for s in sessions if s.endswith("_sv")]

        if not filtered_sessions:
            await send.message("No target TMUX sessions found.", message)
            return

        for session in filtered_sessions:
            await asyncio.to_thread(
                execute,
                f'{settings["paths"]["tmux_executable"]} send-keys -t {session} "stop" ENTER',
            )
            await asyncio.to_thread(
                execute,
                f'{settings["paths"]["tmux_executable"]} send-keys -t {session} "end" ENTER',
            )
            await asyncio.to_thread(
                execute, f"{settings['paths']['tmux_executable']} kill-session -t {session}"
            )

        await send.message(
            "All target TMUX sessions have been stopped and killed.", message
        )
    except (subprocess.SubprocessError, OSError) as e:
        await send.message(f"An error occurred while closing sessions: {e}", message)


async def main(command, message):
    if len(command) > 1 and command[1] == "all":
        await all(message)
    elif len(command) > 1:
        server_name = command[1]
        backend_name = server_name + "_sv"
        status_val = status.read(backend_name)
        if command[0] == "stop":
            await server(message, server_name, status_val, command)
    else:
        await send.message(
            system_messages.get("invalid_close", "Invalid command format for 'close'"),
            message,
        )
