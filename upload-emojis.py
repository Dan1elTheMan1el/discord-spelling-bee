import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import json

# Check if data directory exists
if not os.path.exists("data"):
    os.makedirs("data")

# Load emoji IDs from file if it exists
if os.path.exists("data/emoji_IDs.json"):
    with open("data/emoji_IDs.json", "r") as f:
        emoji_IDs = json.load(f)
else:
    emoji_IDs = {}

print(emoji_IDs)

# Create undetected Chrome driver (handles anti-detection automatically)
driver = uc.Chrome()
driver.get("https://discord.com/developers/applications")
print("Log in and navigate to your application's emojis page.")

while not driver.current_url.endswith("emojis"):
    pass  # Wait for user to navigate to emojis page
time.sleep(2)

for letter in "abcdefghijklmnopqrstuvwxyz":
    for col in ["mid", "out"]:
        emoji_upload = driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
        emoji_upload.send_keys(os.path.abspath(f"emojis/{col}_{letter}.png"))

        time.sleep(2)

        first_row = driver.find_element(By.CSS_SELECTOR, '.rowWrapper-2RxnWO.row-2ndVB-')
        emoji_name_input = first_row.find_element(By.CSS_SELECTOR, '.emojiNameInputTextbox-1H3B1T input')
        emoji_name = emoji_name_input.get_attribute('value')
        emoji_id_element = first_row.find_element(By.CSS_SELECTOR, '.cellId--lByq3')
        emoji_id = emoji_id_element.text

        print(f"Emoji Name: {emoji_name}")
        print(f"Emoji ID: {emoji_id}")

        # Store in the emoji_IDs dictionary
        emoji_IDs[emoji_name] = emoji_id

# Save emoji IDs to a file
with open("data/emoji_IDs.json", "w") as f:
    json.dump(emoji_IDs, f, indent=4)