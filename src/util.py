import asyncio
import os
import random
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import discord
import tomllib
from tomlkit import dumps, parse, table


def execute(command):
    # シェルコマンドを実行
    subprocess.run(command, shell=True, check=True)


def load_system_messages() -> dict[str, Any]:
    try:
        p = Path("message.toml")
        if not p.exists():
            return {}
        with p.open("rb") as f:
            message_toml = tomllib.load(f)
        return message_toml.get("system", {})
    except (OSError, tomllib.TOMLDecodeError):
        return {}


system_messages = load_system_messages()


def get_permission(member):
    roles_order = ["admin", "mod", "staff", "everyone"]
    member_roles = {role.name for role in getattr(member, "roles", [])}
    for role in roles_order:
        if role in member_roles:
            return role
    return "everyone"


def hasPermission(member, required_role):
    roles_order = ["everyone", "staff", "mod", "admin"]
    member_role = get_permission(member)
    try:
        member_idx = roles_order.index(member_role)
        required_idx = roles_order.index(required_role)
        return member_idx >= required_idx
    except ValueError:
        return False


class send:
    @staticmethod
    async def message(content: str, message) -> None:
        content = "\n" + content

        print(content)
        if message is None:
            return

        target_send = None

        if isinstance(message, discord.Message):
            target_send = message.channel.send

        elif isinstance(message, discord.Interaction):
            if not message.response.is_done():
                target_send = message.response.send_message
            else:
                target_send = message.followup.send

        elif hasattr(message, "send"):
            target_send = message.send

        if target_send is None:
            print("No valid target to send message.")
            return

        MAX_LEN = 2000
        try:
            for i in range(0, len(content), MAX_LEN):
                chunk = content[i : i + MAX_LEN]
                await target_send(chunk)
        except discord.HTTPException as e:
            print(f"Failed to send message: {e}")


def select_option(items):
    options = [x for x in items if x.startswith("--")]
    args = [x for x in items if not x.startswith("--")]
    return options, args


def random_path():
    chars = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        dirname = "".join(random.choices(chars, k=8))
        full_path = os.path.join("output", dirname)
        if not os.path.exists(full_path):
            return dirname


def create_empty_toml(path: Path):
    empty_data = table()
    with path.open("w", encoding="utf-8") as f:
        f.write(dumps(empty_data))


def unwrap_toml(value):
    if isinstance(value, dict):
        return {k: unwrap_toml(v) for k, v in value.items()}
    if isinstance(value, list):
        return [unwrap_toml(v) for v in value]
    return value


class load_settings:
    _instance = None

    def __new__(cls, settings_path: str = "settings.toml"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load(settings_path)
        return cls._instance

    def _load(self, settings_path: str):
        path = Path(settings_path)
        if not path.exists():
            raise FileNotFoundError(f"{settings_path} not found.")

        with path.open("r", encoding="utf-8") as f:
            data = parse(f.read())

        self._settings: dict[str, Any] = unwrap_toml(data)

    # -----------------------------
    # 追加：辞書アクセスを可能にする
    # -----------------------------
    def __getitem__(self, key: str) -> Any:
        return self._settings[key]

    # 任意キーを安全に取得
    def get(self, *keys, default=None):
        data = self._settings
        for key in keys:
            if key not in data:
                return default
            data = data[key]
        return data

    # -----------------------------
    # 値取得メソッド
    # -----------------------------
    def server_base_dir(self) -> str:
        return self._settings["paths"]["server_base_dir"]

    def servers_file(self) -> str:
        return self._settings["paths"]["servers_file"]

    def download_dir(self) -> str:
        return self._settings["paths"]["download_dir"]

    def message_toml(self) -> str:
        return self._settings["paths"]["message_toml"]

    def log_file(self) -> str:
        return self._settings["paths"]["log_file"]

    def tmux_executable(self) -> str:
        return self._settings["paths"]["tmux_executable"]

    def mysql_toml(self) -> str:
        return self._settings["paths"]["mysql_toml"]

    def developer_channel_id(self) -> int:
        return self._settings["channel_ids"]["developer"]


settings = load_settings()  # グローバルインスタンス

# -----------------------------
# ここで設定読み込み部分終了
# -----------------------------


async def get_user_input(prompt: str, message: discord.Message) -> str:
    await send.message(prompt, message)

    def check(m):
        return m.author == message.author and m.channel == message.channel

    try:
        bot = message._state._get_client()
        response = await bot.wait_for("message", check=check, timeout=60.0)
        return response.content
    except asyncio.TimeoutError:
        await send.message(
            "タイムアウトしました。もう一度やり直してください。", message
        )
        return ""


def future(mm_dd: str) -> str:
    today = datetime.now(timezone.utc).date()
    month, day = map(int, mm_dd.split("-"))
    target = date(today.year, month, day)
    if target <= today:
        target = date(today.year + 1, month, day)
    return target.strftime("%Y-%m-%d")


def past(mm_dd: str) -> str:
    today = datetime.now(timezone.utc).date()
    month, day = map(int, mm_dd.split("-"))
    target = date(today.year, month, day)
    if target >= today:
        target = date(today.year - 1, month, day)
    return target.strftime("%Y-%m-%d")
