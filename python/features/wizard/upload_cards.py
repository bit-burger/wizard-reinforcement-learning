import json
import os

from config import client

EMOJIS_FOLDER = './features/wizard/card_deck'  # Folder containing your PNG files
OUTPUT_JSON_FILE = './features/wizard/card_deck_info.json'
GUILD_IDS = [1292267820360400989, 1292267784889303060]  # Replace with your list of guild IDs


@client.event
async def ready():
    emoji_data = {}

    # emojis = guild.emojis
    # for emoji in emojis:
    #     try:
    #         await emoji.delete()
    #         print(f'Deleted emoji: {emoji.name}')
    #     except Exception as e:
    #         print(f'Failed to delete emoji {emoji.name}:', e)
    # Read all PNG files from the specified folder

    files = sorted([f for f in os.listdir(EMOJIS_FOLDER) if f.endswith('.png')])
    i = 0
    guild_id_index = 0
    for filename in files:
        i += 1
        if i > 50:
            i = 0
            guild_id_index += 1
        guild = await client.fetch_guild(GUILD_IDS[guild_id_index])
        emoji_name = os.path.splitext(filename)[0]  # Get the emoji name without extension
        file_path = os.path.join(EMOJIS_FOLDER, filename)  # Full path to the file
        try:
            # Upload the emoji
            with open(file_path, 'rb') as f:
                emoji = await guild.create_custom_emoji(name=emoji_name, image=f.read())
                print(f'Uploaded emoji: {emoji.name} with ID: {emoji.id} to guild {guild.name}')
                emoji_data[emoji_name] = str(emoji.id)  # Save emoji ID with the name as key
        except Exception as e:
            print(f'Failed to upload {filename} to guild {guild.name}:', e)

        # Save the emoji IDs to a JSON file for the current guild
    with open(OUTPUT_JSON_FILE, 'w') as json_file:
        json.dump(emoji_data, json_file, indent=2)