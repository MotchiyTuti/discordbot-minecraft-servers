import asyncio
from datetime import datetime, timezone

import pymysql
import tomllib

from src.util import future, get_user_input, send, settings


def update_or_insert_birthday_present(connection, name, birthday, amount, request):
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with connection.cursor() as cursor:
        check_sql = """
        SELECT amount, request FROM birthday_presents WHERE name = %s AND birthday = %s
        """
        cursor.execute(check_sql, (name, birthday))
        result = cursor.fetchone()

        if result:
            existing_amount, existing_request = result
            new_amount = existing_amount + amount
            new_request = (existing_request or "") + "\n" + (request or "")
            update_sql = """
            UPDATE birthday_presents
            SET amount = %s, request = %s, updated_at = %s
            WHERE name = %s AND birthday = %s
            """
            cursor.execute(
                update_sql,
                (new_amount, new_request.strip(), current_date, name, birthday),
            )
        else:
            insert_sql = """
            INSERT INTO birthday_presents (name, birthday, amount, request, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (name, birthday, amount, request, current_date))

        connection.commit()
        print("データベースが更新されました。")


def parse_command_input(content: str) -> dict[str, str]:
    parts = content.split()
    parsed_data = {}

    try:
        parsed_data["name"] = parts[0]
        parsed_data["birthday"] = parts[1]
        parsed_data["amount"] = parts[2]
        parsed_data["request"] = " ".join(parts[3:])
    except IndexError:
        raise ValueError(
            "入力形式が正しくありません。名前、誕生日、金額、リクエストの順で入力してください。"
        )

    return parsed_data


def calculate_next_birthday(birthday: str) -> str:
    birth_date = datetime.strptime(birthday, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    today = datetime.now(timezone.utc)

    next_birthday = birth_date.replace(year=today.year)

    if next_birthday < today:
        next_birthday = next_birthday.replace(year=today.year + 1)

    return next_birthday.strftime("%Y-%m-%d")


def normalize_birthday_format(birthday: str) -> str:
    birthday = birthday.replace("/", "-")

    if len(birthday) == 4 and birthday.isdigit():
        birthday = f"{birthday[:2]}-{birthday[2:]}"

    try:
        datetime.strptime(birthday, "%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(
            "誕生日の形式が正しくありません。MM-DD、MM/DD、またはMMDD形式で入力してください。"
        )

    return birthday


async def get_user_input_with_control(prompt: str, message, previous_value=None):
    while True:
        await send.message(
            f"{prompt}\n(入力を中断するには 'cancel' と入力してください。\n前の選択に戻るには 'back' と入力してください。)",
            message,
        )

        def check(m):
            return m.author == message.author and m.channel == message.channel

        try:
            bot = message._state._get_client()
            response = await bot.wait_for("message", check=check, timeout=60.0)
            content = response.content.strip()

            if content.lower() == "cancel":
                await send.message("操作を中断しました。", message)
                return None, "cancel"

            if content.lower() == "back":
                if previous_value is not None:
                    await send.message(f"前の選択に戻ります: {previous_value}", message)
                    return previous_value, "back"
                else:
                    await send.message("戻る選択肢がありません。", message)
                    continue

            return content, None

        except asyncio.TimeoutError:
            await send.message(
                "タイムアウトしました。もう一度やり直してください。", message
            )
            return None, "cancel"


async def main(message):
    mysql_toml_path = settings["paths"]["mysql_toml"]

    def load_config():
        with open(mysql_toml_path, "rb") as f:
            return tomllib.load(f)

    config = await asyncio.to_thread(load_config)

    command_content = message.content.strip()

    if command_content.startswith("!present"):
        command_args = command_content[len("!present") :].strip()

        if command_args:
            try:
                data = parse_command_input(command_args)
                name = data["name"]
                birthday = normalize_birthday_format(data["birthday"])
                amount = data["amount"]
                request = data["request"]
            except ValueError as e:
                await send.message(f"エラー: {e!s}", message)
                return
        else:
            name = await get_user_input("名前を入力してください：", message)
            if not name:
                return

            birthday = await get_user_input(
                "誕生日を MM-DD、MM/DD、または MMDD 形式で入力してください：", message
            )
            if not birthday:
                return

            try:
                birthday = normalize_birthday_format(birthday)
            except ValueError as e:
                await send.message(f"エラー: {e!s}", message)
                return

            amount = await get_user_input("金額を入力してください：", message)
            if not amount.isdigit():
                await send.message("金額は数字で入力してください。", message)
                return

            request = await get_user_input(
                "リクエスト内容を入力してください：", message
            )
            if not request:
                return

            amount = int(amount) if amount and amount.isdigit() else 0
            request = ""

        connection = pymysql.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            port=config.get("port", 3306),
        )

        try:
            update_or_insert_birthday_present(
                connection,
                name=name,
                birthday=future(birthday),
                amount=int(amount),
                request=request,
            )
        finally:
            connection.close()
        await send.message("データベースが正常に更新されました。", message)
        await send.message(
            f"名前: {name}, 誕生日: {birthday}, 金額: {amount}, リクエスト: {request}",
            message,
        )
