import requests


def format_uuid(uuid):
    """
    Format the UUID to include hyphens.

    Args:
        uuid (str): The raw UUID string without hyphens.

    Returns:
        str: The formatted UUID with hyphens.
    """
    return f"{uuid[:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}"


def get_uuid_from_name(player_name):
    """
    Fetch the UUID of a Minecraft player using their username.

    Args:
        player_name (str): The username of the Minecraft player.

    Returns:
        str: The UUID of the player if found, otherwise None.
    """
    url = f"https://api.mojang.com/users/profiles/minecraft/{player_name}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        raw_uuid = data.get("id")
        return format_uuid(raw_uuid)
    elif response.status_code == 204:
        print(f"Player '{player_name}' not found.")
        return None
    else:
        print(f"Error: Unable to fetch UUID. HTTP Status Code: {response.status_code}")
        return None


if __name__ == "__main__":
    player_name = input("Enter the Minecraft player name: ")
    uuid = get_uuid_from_name(player_name)

    if uuid:
        print(f"The UUID for player '{player_name}' is: {uuid}")
    else:
        print("Could not retrieve UUID.")
