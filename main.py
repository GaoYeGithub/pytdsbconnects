import discord
import asyncio
import datetime
import tdsbconnects
import json
from getpass import getpass
import os

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def get_tdsb_data(username, password, date):
    async with tdsbconnects.TDSBConnects() as session:
        await session.login(username, password)
        info = await session.get_user_info()
        
        user_data = {
            "name": info.name,
            "role": str(info.roles[0]),
            "school": {
                "name": info.schools[0].name,
                "code": info.schools[0].code,
                "school_year": info.schools[0].school_year,
                "school_year_start": str(info.schools[0].school_year_start),
                "school_year_end": str(info.schools[0].school_year_end)
            }
        }

        timetable_date = datetime.datetime.strptime(date, "%Y-%m-%d")
        timetable = await info.schools[0].timetable(timetable_date)
        
        if timetable:
            user_data["timetable"] = {
                "day": timetable[0].course_cycle_day,
                "courses": []
            }
            for item in timetable:
                user_data["timetable"]["courses"].append({
                    "period": item.course_period,
                    "start": str(item.course_start),
                    "end": str(item.course_end),
                    "course_name": item.course_name,
                    "course_code": item.course_code,
                    "course_block": item.course_block,
                    "teacher_name": item.course_teacher_name,
                    "teacher_email": item.course_teacher_email
                })
        else:
            user_data["timetable"] = None

        with open("user_data.json", "w") as json_file:
            json.dump(user_data, json_file, indent=4)

        return user_data

@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!getinfo'):
        await message.channel.send("Please enter your TDSB username:")

        def check_username(msg):
            return msg.author == message.author and msg.channel == message.channel

        username_msg = await client.wait_for('message', check=check_username)
        username = username_msg.content

        await message.channel.send("Please enter your TDSB password:")

        def check_password(msg):
            return msg.author == message.author and msg.channel == message.channel

        password_msg = await client.wait_for('message', check=check_password)
        password = password_msg.content

        await message.channel.send("Please enter the date (YYYY-MM-DD) to get your timetable:")

        def check_date(msg):
            return msg.author == message.author and msg.channel == message.channel

        date_msg = await client.wait_for('message', check=check_date)
        date = date_msg.content

        await message.channel.send("Fetching your information...")

        try:
            user_data = await get_tdsb_data(username, password, date)
            await message.channel.send("Information fetched successfully! Here is your data:", file=discord.File("user_data.json"))
        except Exception as e:
            await message.channel.send(f"An error occurred: {str(e)}")

client.run(TOKEN)
