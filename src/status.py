import asyncio
import subprocess

from .util import send, settings, system_messages


async def read(server_name):
    try:
        def run_cmd():
            return subprocess.run(
                f"{settings['paths']['tmux_executable']} list-sessions -F '#S'",
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )

        result = await asyncio.to_thread(run_cmd)
        sessions = result.stdout.strip().split("\n")
        sessions = [s for s in sessions if s]
        filtered_sessions = [s for s in sessions if s.endswith("_sv")]
        if server_name in filtered_sessions:
            return "running"  # サーバーが実行中
        else:
            return "waiting"  # サーバーが実行されていない
    except (subprocess.SubprocessError, OSError):
        return None


async def tmux_output(session_name, lines=10):
    # TMUXセッションの最新出力を取得
    try:
        def run_cmd():
            return subprocess.run(
                f"tmux capture-pane -pt {session_name} -S -{lines}",
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )

        result = await asyncio.to_thread(run_cmd)
        return result.stdout
    except (subprocess.SubprocessError, OSError):
        return None


async def server(message, server_name, status_val):
    if status_val:
        await send.message(f"{server_name} is {status_val}", message)
    else:
        await send.message(f"Status file for {server_name} not found.", message)


async def list(message):
    try:
        def run_cmd():
            return subprocess.run(
                f"{settings['paths']['tmux_executable']} list-sessions -F '#S'",
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )

        result = await asyncio.to_thread(run_cmd)
        sessions = result.stdout.strip().split("\n")
        sessions = [s for s in sessions if s]
        filtered = [s for s in sessions if s.endswith("_sv")]
        display_names = [s[:-3] for s in filtered]

        if display_names:
            await send.message(
                "Currently running servers: " + ", ".join(display_names), message
            )
        else:
            await send.message("No servers are currently running.", message)
    except (subprocess.SubprocessError, OSError) as e:
        await send.message(
            f"An error occurred while listing tmux sessions: {e}", message
        )


async def main(command, message):
    if len(command) > 1 and command[1] == "ls":
        await list(message)
    elif len(command) > 1:
        server_name = command[1]
        backend_name = server_name + "_sv"
        status_val = await read(backend_name)
        await server(message, server_name, status_val)
    else:
        await send.message(
            system_messages.get(
                "invalid_status", "Invalid command format for 'status'"
            ),
            message,
        )
