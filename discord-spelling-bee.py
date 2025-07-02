import os
import json
import requests
from bs4 import BeautifulSoup
import dotenv
import discord
from discord.ext import tasks
import datetime
import random
from PIL import Image, ImageDraw, ImageFont

dotenv.load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set.")
UTC_TIME = os.getenv("UTC_TIME", "0")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

global serverData
if not os.path.exists("data/serverData.json"):
    os.makedirs("data", exist_ok=True)
    with open("data/serverData.json", "w") as f:
        json.dump({}, f)
serverData = json.load(open("data/serverData.json", "r"))

@bot.command(description="Set this channel as the Spelling Bee channel.")
async def set_channel(ctx):
    global serverData

    # Check if the server data file exists
    guildID = str(ctx.guild.id)
    if guildID not in serverData:
        serverData[guildID] = {}
    
    # Update Channel ID
    serverData[guildID]["channelID"] = ctx.channel.id
    with open("data/serverData.json", "w") as f:
        json.dump(serverData, f, indent=4)
    
    await ctx.respond("Channel set!", ephemeral=True)

@bot.command(description="Send today's Letters")
async def letters(ctx):
    file = discord.File("resources/todays_spelling_bee.png", filename="todays_spelling_bee.png")
    embed = discord.Embed(
        color=discord.Color.from_rgb(227, 204, 0)
    )
    embed.set_image(url="attachment://todays_spelling_bee.png")
    await ctx.respond(file=file, embed=embed)

@bot.command(description="Check today's Stats")
async def today(ctx):
    global serverData

    # Check if channel is correct
    guildID = str(ctx.guild.id)
    if guildID not in serverData or ctx.channel.id != serverData[guildID]['channelID']:
        return await ctx.respond("This command can only be used in the Spelling Bee channel.", ephemeral=True)
    
    # Get today's embed
    try:
        channel = bot.get_channel(int(serverData[guildID]['channelID']))
        if channel and 'messageID' in serverData[guildID]:
            messageToUpdate = await channel.fetch_message(serverData[guildID]['messageID'])
            embed = messageToUpdate.embeds[0]
            
            # Respond immediately to avoid timeout
            await ctx.respond("Creating new live stats message...", ephemeral=True)
            
            # Create new message with the embed
            newMessage = await ctx.followup.send(embed=embed)
            
            # Update the messageID to the new message
            serverData[guildID]['messageID'] = newMessage.id
            with open("data/serverData.json", "w") as f:
                json.dump(serverData, f, indent=4)
        else:
            await ctx.respond("No spelling bee game found for today. Use `/letters` to see today's letters.", ephemeral=True)
    except discord.NotFound:
        await ctx.respond("The original spelling bee message was not found. Use `/letters` to see today's letters.", ephemeral=True)
    except Exception as e:
        await ctx.respond("An error occurred while fetching today's stats.", ephemeral=True)

@tasks.loop(time=datetime.time(hour=int(UTC_TIME)), reconnect=False)
async def start_games():
    global serverData

    # Fetch Spelling Bee data
    print("Fetching Spelling Bee data...")
    response = requests.get("https://www.nytimes.com/puzzles/spelling-bee")
    soup = BeautifulSoup(response.text, "html.parser")
    gameData = json.loads(soup.find('div', class_='pz-game-screen').find('script').contents[0].replace('window.gameData = ',''))['today']

    # Calculate total points
    totalPoints = 0
    for answer in gameData['answers']:
        if len(answer) == 4:
            totalPoints += 1
        else:
            totalPoints += len(answer)
    totalPoints += 7 * len(gameData['pangrams'])
    gameData['totalPoints'] = totalPoints
    with open("data/spelling_bee_data.json", "w") as f:
        json.dump(gameData, f, indent=4, ensure_ascii=False)

    # Generate game image
    img = Image.open("resources/spbee.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("resources/helvmn.ttf", 80)
    positions = [(284, 114), (440, 205), (440, 386), (284, 478), (128, 386), (128, 205)]
    random.shuffle(positions)
    for i, letter in enumerate(gameData['outerLetters']):
        pos = positions[i]
        draw.text(pos, letter.upper(), font=font, fill=(0, 0, 0), anchor="mm", stroke_width=2)
    draw.text((284, 296), gameData['centerLetter'].upper(), font=font, fill=(0, 0, 0), anchor="mm", stroke_width=2)
    img.save("resources/todays_spelling_bee.png")

    # Format the game data
    embed = discord.Embed(
        title="**Today's Spelling Bee**",
        description=f"*{gameData['displayWeekday']}, {gameData['displayDate']}*",
        color=discord.Color.from_rgb(227, 204, 0)
    )
    embed.set_thumbnail(url="https://static01.nyt.com/images/2020/03/23/crosswords/spelling-bee-logo-nytgames-hi-res/spelling-bee-logo-nytgames-hi-res-smallSquare252-v4.png")
    embed.add_field(name="Letters", value=f":regional_indicator_{gameData['centerLetter']}:, {', '.join(gameData['outerLetters'])}", inline=False)
    embed.add_field(name="Words:", value=f"0/{len(gameData['answers'])}", inline=True)
    embed.add_field(name="Pangrams:", value=f"0/{len(gameData['pangrams'])}", inline=True)
    embed.add_field(name="Points:", value=f"0/{totalPoints}", inline=True)
    embed.add_field(name="Scores:", value="*No scores yet.*", inline=False)
    embed.set_image(url="attachment://todays_spelling_bee.png")

    # Load server data
    remove = []
    for guildID, data in serverData.items():
        channelID = data["channelID"]
        channel = bot.get_channel(int(channelID))
        # Send game data to chanel
        if channel:
            # Create a new file object for each channel
            file = discord.File("resources/todays_spelling_bee.png", filename="todays_spelling_bee.png")
            message = await channel.send(file=file, embed=embed)
            data["messageID"] = message.id
            data["foundWords"] = []
            data["userScores"] = {}
            data["pangrams"] = 0
            data["points"] = 0
        else:
            remove.append(guildID)
    
    # Remove channels that are no longer accessible
    for guildID in remove:
        del serverData[guildID]
    
    # Save updated server data
    with open("data/serverData.json", "w") as f:
        json.dump(serverData, f, indent=4)
    print("Spelling Bee data fetched and sent to channels.")

@bot.event
async def on_message(message):
    global serverData

    if message.author == bot.user:
        return
    
    # Load server data
    guildID = str(message.guild.id)
    if guildID not in serverData or message.channel.id != serverData[guildID]['channelID']:
        return
    
    # Check if the message is a valid word
    word = message.content.strip().lower()
    with open("data/spelling_bee_data.json", "r") as f:
        gameData = json.load(f)
    if word not in gameData['answers']:
        return
    if word in serverData[guildID]['foundWords']:
        await message.add_reaction("⚠️")
        return
    
    # Process word
    serverData[guildID]['foundWords'].append(word)
    points = len(word) if len(word) > 4 else 1
    if word in gameData['pangrams']:
        points += 7
        serverData[guildID]['pangrams'] += 1
        await message.add_reaction("👑")
    else:
        await message.add_reaction("✅")
    serverData[guildID]['points'] += points

    # Update user scores
    userID = str(message.author.id)
    if userID not in serverData[guildID]['userScores']:
        serverData[guildID]['userScores'][userID] = 0
    serverData[guildID]['userScores'][userID] += points

    # Update message embed
    channel = bot.get_channel(int(serverData[guildID]['channelID']))
    if channel:
        messageToUpdate = await channel.fetch_message(serverData[guildID]['messageID'])
        embed = messageToUpdate.embeds[0]
        embed.set_field_at(1, name="Words:", value=f"{len(serverData[guildID]['foundWords'])}/{len(gameData['answers'])}", inline=True)
        embed.set_field_at(2, name="Pangrams:", value=f"{serverData[guildID]['pangrams']}/{len(gameData['pangrams'])}", inline=True)
        embed.set_field_at(3, name="Points:", value=f"{serverData[guildID]['points']}/{gameData['totalPoints']}", inline=True)

        scoreList = sorted(serverData[guildID]['userScores'].items(), key=lambda x: x[1], reverse=True)
        scoreText = "\n".join([f"{i+1}. <@{userID}>: {data} points" for i, (userID, data) in enumerate(scoreList)])
        embed.set_field_at(4, name="Scores:", value=scoreText, inline=False)

        await messageToUpdate.edit(embed=embed)
    
    # Save updated server data
    with open("data/serverData.json", "w") as f:
        json.dump(serverData, f, indent=4)

@bot.event
async def on_ready():
    print("Online!")
    start_games.start()
bot.run(DISCORD_TOKEN)