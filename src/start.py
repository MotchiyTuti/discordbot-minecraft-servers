import asyncio
from pathlib import Path

from tomlkit import parse, table

from . import status as status_module
from .util import create_empty_toml, execute, send, settings, system_messages


def unwrap_toml(item):
    if item is None:
        return {}
    if hasattr(item, "unwrap"):
        return item.unwrap()
    if isinstance(item, dict):
        return item
    return item


def load_servers():
    servers_file = Path(settings["paths"]["servers_file"])
    if servers_file.exists():
        with servers_file.open("r", encoding="utf-8") as f:
            return parse(f.read())
    else:
        create_empty_toml(servers_file)
        return table()


async def run_shell(message, server_name):
    base = settings["paths"]["server_base_dir"]
    backend_name = f"{server_name}_sv"
    run_sh = Path(f"{base}/{backend_name}/run.sh")

    if run_sh.exists():
        execute(f'tmux send-keys -t {backend_name} "bash run.sh" ENTER')
        await send.message(f"Opening {server_name} with run.sh", message)
        return True

    return False


async def server(message, server_name, status_val):
    servers = load_servers()
    backend_name = f"{server_name}_sv"

    # tomlkit → dict
    server_info = unwrap_toml(servers.get(server_name))
    java_version = server_info.get("java_version", "")

    if status_val == "running":
        await send.message(f"{server_name} is already running!", message)
        return

    base = settings["paths"]["server_base_dir"]

    execute(f"tmux new -s {backend_name} -d")
    execute(f'tmux send-keys -t {backend_name} "cd {base}/{backend_name}" ENTER')

    used_run_sh = await run_shell(message, server_name)

    if not used_run_sh:
        await send.message("Opening with jarFile", message)

        if server_name != "proxy":
            execute(
                f'tmux send-keys -t {backend_name} "java{java_version} -jar *.jar nogui" ENTER'
            )
            await asyncio.sleep(2)

            output = await status_module.tmux_output(backend_name)
            if output and "Automatic saving is now disabled" in output:
                await send.message(
                    f"save-off was successfully executed for {server_name}", message
                )
        else:
            execute(
                f'tmux send-keys -t {backend_name} "java{java_version} -jar *.jar" ENTER'
            )

    await send.message(f"{server_name} has been started!", message)


async def all(message):
    servers_file = Path(settings["paths"]["servers_file"])
    if not servers_file.exists():
        await send.message("servers.toml not found. Please add servers to it.", message)
        return

    servers = load_servers()
    if not servers:
        await send.message("No servers found in servers.toml.", message)
        return

    base = settings["paths"]["server_base_dir"]

    for server_name in servers:
        backend_name = f"{server_name}_sv"
        server_info = unwrap_toml(servers.get(server_name))
        java_version = server_info.get("java_version", "")
        status_val = status_module.read(backend_name)

        if status_val == "running":
            await send.message(f"{server_name} is already running!", message)
            continue

        execute(f"tmux new -s {backend_name} -d")
        execute(f'tmux send-keys -t {backend_name} "cd {base}/{backend_name}" ENTER')

        used_run_sh = await run_shell(message, server_name)

        if not used_run_sh:
            await send.message(f"Opening {server_name} with jarFile", message)

            if server_name != "proxy":
                execute(
                    f'tmux send-keys -t {backend_name} "java{java_version} -jar *.jar nogui" ENTER'
                )
            else:
                execute(
                    f'tmux send-keys -t {backend_name} "java{java_version} -jar *.jar" ENTER'
                )

        await send.message(f"{server_name} has been started!", message)

    await send.message("All servers from servers.toml have been started.", message)


async def restart(message, server_name):
    if server_name == "all":
        servers = load_servers()

        if not servers:
            await send.message("servers.toml にサーバーがありません。", message)
            return

        for name in servers:
            backend_name = f"{name}_sv"
            status_val = status_module.read(backend_name)

            if status_val == "running":
                execute(f'tmux send-keys -t {backend_name} "stop" ENTER')
                await asyncio.sleep(3)
                execute(f"tmux kill-session -t {backend_name}")
            await server(message, name, "stopped")

        await send.message("すべてのサーバーを再起動しました。", message)
        return

    backend_name = f"{server_name}_sv"
    status_val = status_module.read(backend_name)

    if status_val == "running":
        execute(f'tmux send-keys -t {backend_name} "stop" ENTER')
        await asyncio.sleep(3)
        execute(f"tmux kill-session -t {backend_name}")

    await server(message, server_name, "stopped")


async def main(command, message):
    if len(command) > 1 and command[1] == "all":
        await all(message)
        return

    if len(command) > 1:
        server_name = command[1]

        if command[0] == "start":
            backend_name = f"{server_name}_sv"
            status_val = status_module.read(backend_name)
            await server(message, server_name, status_val)
            return

        if command[0] == "restart":
            await restart(message, server_name)
            return

    await send.message(
        system_messages.get("invalid_open", "Invalid command format for 'open'"),
        message,
    )
